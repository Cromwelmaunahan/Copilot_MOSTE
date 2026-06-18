"""Loading and statistical analysis of a basictype folder of ``.eff`` files."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import config
from .eff_parser import TestParam, WaferData, parse_eff_file, wafer_number_from_name

log = logging.getLogger(__name__)


@dataclass
class WaferTestStats:
    """Per-wafer statistics for one test number."""

    wafer_number: int
    n: int
    mean: float | None
    std: float | None
    cpk: float | None
    values: np.ndarray


@dataclass
class TestSummary:
    """Everything needed to render one test-number slide."""

    number: int
    name: str
    unit: str
    lsl: float | None
    usl: float | None
    per_wafer: list[WaferTestStats] = field(default_factory=list)

    @property
    def overall_mean(self) -> float | None:
        allv = np.concatenate([w.values for w in self.per_wafer if w.values.size]) \
            if any(w.values.size for w in self.per_wafer) else np.empty(0)
        return float(allv.mean()) if allv.size else None


@dataclass
class WaferYield:
    wafer_number: int
    total: int
    passed: int

    @property
    def yield_pct(self) -> float:
        return 100.0 * self.passed / self.total if self.total else 0.0


@dataclass
class BasicTypeDataset:
    """Parsed + analysed data for one basictype folder."""

    basictype: str
    folder: Path
    wafers: list[WaferData]
    p_code: str
    vf_code: str
    test_numbers: list[int]
    skipped_files: list[tuple[str, str]] = field(default_factory=list)

    @property
    def wafer_numbers(self) -> list[int]:
        return [w.wafer_number for w in self.wafers]


def compute_cpk(
    mean: float, std: float, lsl: float | None, usl: float | None
) -> float | None:
    """Process capability index. Handles single-sided limits; guards std == 0."""
    if std is None or std <= 0 or np.isnan(std):
        return None
    terms: list[float] = []
    if usl is not None:
        terms.append((usl - mean) / (3.0 * std))
    if lsl is not None:
        terms.append((mean - lsl) / (3.0 * std))
    if not terms:
        return None
    return float(min(terms))


def _wafer_test_stats(
    wafer: WaferData, param: TestParam
) -> WaferTestStats:
    values = wafer.values(param.number)
    if values.size:
        mean = float(values.mean())
        std = float(values.std(ddof=1)) if values.size > 1 else 0.0
        cpk = compute_cpk(mean, std, param.lsl, param.usl)
    else:
        mean = std = cpk = None
    return WaferTestStats(
        wafer_number=wafer.wafer_number,
        n=int(values.size),
        mean=mean,
        std=std,
        cpk=cpk,
        values=values,
    )


def load_basictype(basictype: str, *, root: Path | None = None) -> BasicTypeDataset:
    """Parse every ``.eff`` file in a basictype folder and return the dataset."""
    root = root or config.DATA_ROOT
    folder = root / basictype
    if not folder.is_dir():
        raise FileNotFoundError(f"Basictype folder not found: {folder}")

    eff_files = sorted(folder.glob("*.eff"))
    if not eff_files:
        raise FileNotFoundError(f"No .eff files found in {folder}")

    wafers: list[WaferData] = []
    skipped: list[tuple[str, str]] = []
    for path in eff_files:
        if wafer_number_from_name(path) is None:
            skipped.append((path.name, "no wafernumN_ prefix"))
            continue
        try:
            wafers.append(
                parse_eff_file(
                    path,
                    test_min=config.TEST_NUMBER_MIN,
                    test_max=config.TEST_NUMBER_MAX,
                )
            )
        except Exception as exc:  # noqa: BLE001 - keep going on bad files
            log.warning("Skipping %s: %s", path.name, exc)
            skipped.append((path.name, str(exc)))

    if not wafers:
        raise ValueError(f"No readable .eff files in {folder}")

    wafers.sort(key=lambda w: w.wafer_number)

    # Union of test numbers across wafers, preserving numeric order.
    test_numbers = sorted({n for w in wafers for n in w.params})

    p_code = basictype
    vf_code = _derive_vf_code(wafers)

    return BasicTypeDataset(
        basictype=basictype,
        folder=folder,
        wafers=wafers,
        p_code=p_code,
        vf_code=vf_code,
        test_numbers=test_numbers,
        skipped_files=skipped,
    )


def _derive_vf_code(wafers: list[WaferData]) -> str:
    """VF code from the ``Wafer`` data field (e.g. VF524022), falling back to filename."""
    from .eff_parser import COL_WAFER

    for wafer in wafers:
        if COL_WAFER in wafer.df.columns and len(wafer.df):
            val = wafer.df[COL_WAFER].dropna()
            if len(val):
                text = str(val.iloc[0]).strip()
                if text:
                    return text
    # Fallback: look for a VFxxxxxx token in the filename.
    import re

    for wafer in wafers:
        match = re.search(r"(VF\d+)", wafer.path.name)
        if match:
            return match.group(1)
    return "VFXXXXXX"


def get_test_param(dataset: BasicTypeDataset, number: int) -> TestParam | None:
    for wafer in dataset.wafers:
        if number in wafer.params:
            return wafer.params[number]
    return None


def summarize_test(dataset: BasicTypeDataset, number: int) -> TestSummary:
    param = get_test_param(dataset, number)
    if param is None:
        raise KeyError(f"Test number {number} not present in dataset")
    per_wafer = [_wafer_test_stats(w, param) for w in dataset.wafers]
    return TestSummary(
        number=param.number,
        name=param.name,
        unit=param.unit,
        lsl=param.lsl,
        usl=param.usl,
        per_wafer=per_wafer,
    )


def compute_yields(dataset: BasicTypeDataset) -> list[WaferYield]:
    out: list[WaferYield] = []
    for wafer in dataset.wafers:
        total = wafer.die_count
        passed = wafer.pass_count(config.PASS_HBIN)
        out.append(WaferYield(wafer.wafer_number, total, passed))
    return out


def hbin_pareto(dataset: BasicTypeDataset, *, fails_only: bool = True) -> list[tuple[int, int]]:
    """Aggregate HBIN counts across all wafers, sorted descending by count."""
    from .eff_parser import COL_HBIN

    counts: dict[int, int] = {}
    for wafer in dataset.wafers:
        if COL_HBIN not in wafer.df.columns:
            continue
        series = wafer.df[COL_HBIN].dropna()
        for bin_value, cnt in series.value_counts().items():
            bin_int = int(bin_value)
            if fails_only and bin_int == config.PASS_HBIN:
                continue
            counts[bin_int] = counts.get(bin_int, 0) + int(cnt)
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)


def hbin_trend(
    dataset: BasicTypeDataset, *, top_n: int = 5
) -> tuple[list[int], list[int], dict[int, list[float]]]:
    """Per-wafer percentage of the top-N fail bins.

    Returns ``(wafer_numbers, top_bins, {bin: [pct per wafer]})``.
    """
    from .eff_parser import COL_HBIN

    pareto = hbin_pareto(dataset, fails_only=True)
    top_bins = [b for b, _ in pareto[:top_n]]
    wafer_numbers = dataset.wafer_numbers
    trend: dict[int, list[float]] = {b: [] for b in top_bins}
    for wafer in dataset.wafers:
        total = wafer.die_count or 1
        series = (
            wafer.df[COL_HBIN].dropna() if COL_HBIN in wafer.df.columns else None
        )
        vc = series.value_counts() if series is not None else {}
        for b in top_bins:
            cnt = int(vc.get(b, 0)) if hasattr(vc, "get") else 0
            trend[b].append(100.0 * cnt / total)
    return wafer_numbers, top_bins, trend
