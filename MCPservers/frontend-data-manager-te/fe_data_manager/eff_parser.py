"""Parser for semiconductor frontend test ``.eff`` files.

EFF format (as produced by the STDF analyser used for MOSFET FE testing) is
**semicolon-delimited and column-oriented**:

* The first line is ``<<EFF:1.00>>;Headers=..;Rows=..;Columns=N;..`` and declares the
  number of data columns ``N``.
* A set of *metadata* rows follow, each prefixed by a ``<tag>;`` token, e.g.
  ``<+ParameterName>``, ``<+ParameterNumber>``, ``<PARATTR:UNIT>``,
  ``<LIMIT:SPEC:LOWER_VALUE>``, ``<LIMIT:SPEC:UPPER_VALUE>``. After dropping the leading
  tag token, the remaining ``N`` values align 1:1 with the data columns.
* The remaining lines are *data* rows (no ``<`` prefix), one per die. Each row has ``N``
  semicolon-separated fields aligned to the column names. Text fields may be wrapped in
  double quotes; empty fields mean "no measurement" and are treated as ``NaN``.

Each measurement parameter is a *column*; its **test number** is given by the
``<+ParameterNumber>`` metadata row. Per-die status columns ``HBIN`` / ``PF`` / ``SBIN``
appear near the start of every row.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_WAFER_RE = re.compile(r"wafernum(\d+)_", re.IGNORECASE)

# Metadata row tags we care about (without the surrounding angle brackets handling).
_TAG_COLUMN_NAMES = "<+EFF:"  # row that carries the data column names
_TAG_PARAM_NAME = "<+ParameterName>"
_TAG_PARAM_NUMBER = "<+ParameterNumber>"
_TAG_UNIT = "<PARATTR:UNIT>"
_TAG_LSL = "<LIMIT:SPEC:LOWER_VALUE>"
_TAG_USL = "<LIMIT:SPEC:UPPER_VALUE>"

# Status column names (as they appear in the <+EFF:..> column-name row).
COL_WAFER = "Wafer"
COL_HBIN = "HBIN"
COL_SBIN = "SBIN"
COL_PF = "PF"


@dataclass(frozen=True)
class TestParam:
    """Metadata for one measurement parameter (one test number)."""

    number: int
    name: str
    unit: str
    lsl: float | None
    usl: float | None
    column: str  # data-column name this parameter lives in


@dataclass
class WaferData:
    """Parsed contents of a single ``.eff`` file (one wafer)."""

    path: Path
    wafer_number: int
    df: pd.DataFrame
    params: dict[int, TestParam] = field(default_factory=dict)

    @property
    def die_count(self) -> int:
        return len(self.df)

    @property
    def hbin(self) -> pd.Series:
        return self.df[COL_HBIN] if COL_HBIN in self.df.columns else pd.Series(dtype="Int64")

    def pass_count(self, pass_hbin: int = 1) -> int:
        return int((self.hbin == pass_hbin).sum())

    def values(self, test_number: int) -> np.ndarray:
        """Return the valid (non-NaN) measured values for a test number."""
        param = self.params.get(test_number)
        if param is None or param.column not in self.df.columns:
            return np.empty(0, dtype=float)
        series = pd.to_numeric(self.df[param.column], errors="coerce")
        return series.dropna().to_numpy(dtype=float)


def _strip(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        token = token[1:-1]
    return token.strip()


def _to_float(token: str) -> float | None:
    token = _strip(token)
    if token == "":
        return None
    try:
        return float(token)
    except ValueError:
        return None


def wafer_number_from_name(path: Path) -> int | None:
    """Extract the wafer number from a ``wafernumN_...`` filename, or None."""
    match = _WAFER_RE.search(path.name)
    return int(match.group(1)) if match else None


def parse_eff_file(path: Path, *, test_min: int = 1, test_max: int = 50) -> WaferData:
    """Parse one ``.eff`` file into a :class:`WaferData`.

    Raises ``ValueError`` if the file does not look like a valid EFF file.
    """
    path = Path(path)
    wafer_number = wafer_number_from_name(path)
    if wafer_number is None:
        raise ValueError(f"Cannot determine wafer number from filename: {path.name}")

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    if not lines or not lines[0].startswith("<<EFF"):
        raise ValueError(f"Not an EFF file (missing <<EFF header): {path.name}")

    n_columns = _declared_columns(lines[0])

    column_names: list[str] = []
    meta: dict[str, list[str]] = {}
    data_rows: list[list[str]] = []

    for line in lines:
        if not line:
            continue
        if line.startswith(_TAG_COLUMN_NAMES) and not column_names:
            column_names = line.split(";")[1:]
        elif line.startswith("<"):
            tag = line.split(";", 1)[0]
            if tag in (_TAG_PARAM_NAME, _TAG_PARAM_NUMBER, _TAG_UNIT, _TAG_LSL, _TAG_USL):
                meta[tag] = line.split(";")[1:]
        else:
            data_rows.append(line.split(";"))

    if not column_names:
        raise ValueError(f"No column-name row (<+EFF:..>) found in {path.name}")

    if n_columns is None:
        n_columns = len(column_names)
    column_names = _normalize_width(column_names, n_columns, fill="")

    # The analyser inserts one or more unlabeled die-level columns just before the
    # status block (HBIN/CHIP_ID). This means raw data rows are wider than the column
    # name row and are shifted from that point on. Detect the shift from the PF anchor
    # and realign so that names[i] maps to the correct field.
    offset, boundary = _detect_offset(column_names, data_rows)
    cleaned = [_realign_row(row, column_names, boundary, offset) for row in data_rows]
    df = pd.DataFrame(cleaned, columns=column_names)

    # Coerce key status columns to numeric where present.
    for col in (COL_HBIN, COL_SBIN):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    params = _build_params(column_names, meta, test_min, test_max)

    # Coerce measurement columns to numeric for fast downstream use.
    for param in params.values():
        if param.column in df.columns:
            df[param.column] = pd.to_numeric(df[param.column], errors="coerce")

    return WaferData(path=path, wafer_number=wafer_number, df=df, params=params)


def _declared_columns(header_line: str) -> int | None:
    match = re.search(r"Columns=(\d+)", header_line)
    return int(match.group(1)) if match else None


def _normalize_width(values: list[str], width: int, fill: str) -> list[str]:
    if len(values) > width:
        return values[:width]
    if len(values) < width:
        return values + [fill] * (width - len(values))
    return values


def _detect_offset(column_names: list[str], data_rows: list[list[str]]) -> tuple[int, int]:
    """Detect the column shift between the name row and the data rows.

    Returns ``(offset, boundary)`` where data field ``i + offset`` maps to
    ``column_names[i]`` for every name index ``i >= boundary`` (front identity columns
    below ``boundary`` are read at offset 0).

    The offset is anchored on the ``PF`` (pass/fail) column, whose data values are
    predominantly ``P``/``F``; the boundary is the ``HBIN`` column (the start of the
    status block, just after the inserted die-level column).
    """
    if COL_PF not in column_names or not data_rows:
        return 0, len(column_names)
    pf_name_idx = column_names.index(COL_PF)
    boundary = column_names.index(COL_HBIN) if COL_HBIN in column_names else pf_name_idx

    # Find the data field index that holds P/F values across a sample of rows.
    sample = data_rows[: min(200, len(data_rows))]
    best_idx, best_hits = pf_name_idx, -1
    width = max(len(r) for r in sample)
    for idx in range(width):
        hits = 0
        for row in sample:
            if idx < len(row) and _strip(row[idx]) in ("P", "F"):
                hits += 1
        if hits > best_hits:
            best_hits, best_idx = hits, idx
    offset = best_idx - pf_name_idx if best_hits > 0 else 0
    if offset < 0:
        offset = 0
    return offset, boundary


def _realign_row(
    row: list[str], column_names: list[str], boundary: int, offset: int
) -> list[object]:
    """Map a raw data row onto the column names, accounting for the inserted column(s)."""
    out: list[object] = []
    for i in range(len(column_names)):
        src = i if i < boundary else i + offset
        token = row[src] if 0 <= src < len(row) else ""
        cleaned = _strip(token)
        out.append(cleaned if cleaned != "" else None)
    return out


def _build_params(
    column_names: list[str],
    meta: dict[str, list[str]],
    test_min: int,
    test_max: int,
) -> dict[int, TestParam]:
    numbers = meta.get(_TAG_PARAM_NUMBER, [])
    names = meta.get(_TAG_PARAM_NAME, [])
    units = meta.get(_TAG_UNIT, [])
    lsls = meta.get(_TAG_LSL, [])
    usls = meta.get(_TAG_USL, [])

    width = len(column_names)
    numbers = _normalize_width(numbers, width, fill="")
    names = _normalize_width(names, width, fill="")
    units = _normalize_width(units, width, fill="")
    lsls = _normalize_width(lsls, width, fill="")
    usls = _normalize_width(usls, width, fill="")

    params: dict[int, TestParam] = {}
    for idx, raw_num in enumerate(numbers):
        num = _to_float(raw_num)
        if num is None:
            continue
        if num != int(num):
            continue
        test_number = int(num)
        if not (test_min <= test_number <= test_max):
            continue
        name = _strip(names[idx]) or column_names[idx]
        params[test_number] = TestParam(
            number=test_number,
            name=name,
            unit=_strip(units[idx]),
            lsl=_to_float(lsls[idx]),
            usl=_to_float(usls[idx]),
            column=column_names[idx],
        )
    return dict(sorted(params.items()))
