"""Enumeration and naming helpers for ST4 files under the FE data root.

A "basictype" is a subfolder of :data:`config.DATA_ROOT`. Inside it the ST4 files are bare
files whose name carries a ``.st4_<NNN>_`` token, e.g.::

    877503864_S_20250514102543_VF524022_S11P_N.st4_002_TSTV10-15_P8266BFFT3T1

The wafer number is the digits right after ``.st4_`` (``002`` -> wafer 2). Sibling
``.tar.gz`` archives and already-converted ``.eff`` files are excluded.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from . import config

# Wafer number: digits immediately following the ".st4_" token (case-insensitive).
_WAFER_RE = re.compile(r"\.st4_(\d+)", re.IGNORECASE)

# Extensions that are never an openable ST4 source file.
_EXCLUDED_SUFFIXES = (".eff", ".gz", ".tar", ".zip", ".pptx", ".csv")


def list_basictypes() -> list[str]:
    """Return the basictype folder names under the data root (sorted)."""
    if not config.DATA_ROOT.is_dir():
        return []
    return sorted(
        child.name
        for child in config.DATA_ROOT.iterdir()
        if child.is_dir() and child.name not in config.IGNORED_FOLDERS
    )


def is_st4_file(name: str) -> bool:
    """True if ``name`` looks like an openable ST4 source file (not an archive/EFF)."""
    lowered = name.lower()
    if lowered.endswith(_EXCLUDED_SUFFIXES):
        return False
    return ".st4" in lowered


def list_st4_files(basictype: str) -> list[str]:
    """Return the ST4 file names inside ``basictype`` (sorted)."""
    folder = config.DATA_ROOT / basictype
    if not folder.is_dir():
        return []
    return sorted(
        child.name
        for child in folder.iterdir()
        if child.is_file() and is_st4_file(child.name)
    )


def wafer_number_from_name(name: str) -> int | None:
    """Extract the wafer number from an ST4 file name, or ``None`` if absent.

    Leading zeros are stripped (``006`` -> ``6``).
    """
    match = _WAFER_RE.search(name)
    return int(match.group(1)) if match else None


def st4_path(basictype: str, st4_file: str) -> Path:
    """Resolve the absolute path of an ST4 file inside a basictype folder."""
    return config.DATA_ROOT / basictype / st4_file


def eff_output_path(st4_file_path: Path, wafer_number: int) -> Path:
    """Build the destination ``.eff`` path next to the ST4 file.

    Pattern: ``wafernum<N>_<st4-base-name>.eff`` in the same folder. If that name already
    exists, a timestamp suffix is appended so nothing is overwritten.
    """
    base = st4_file_path.name
    target = st4_file_path.with_name(f"wafernum{wafer_number}_{base}.eff")
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = st4_file_path.with_name(f"wafernum{wafer_number}_{base}_{stamp}.eff")
    return target
