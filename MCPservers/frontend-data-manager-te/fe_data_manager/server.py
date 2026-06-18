"""MCP server: Frontend Data Manager for TE.

Exposes tools to list basictype folders, inspect a basictype, and generate a PowerPoint
report of frontend testing results from ``.eff`` files.

Run with::

    python -m fe_data_manager.server
"""
from __future__ import annotations

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import analysis, config, report

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fe_data_manager")

mcp = FastMCP("Frontend Data Manager for TE")


def _list_basictype_folders() -> list[str]:
    if not config.DATA_ROOT.is_dir():
        return []
    out = []
    for child in sorted(config.DATA_ROOT.iterdir()):
        if child.is_dir() and child.name not in config.IGNORED_FOLDERS:
            if any(child.glob("*.eff")):
                out.append(child.name)
    return out


@mcp.tool()
def list_basictypes() -> dict:
    """List the available basictype folders (each containing ``.eff`` files).

    Returns the data root and the basictype names the user can choose from.
    """
    folders = _list_basictype_folders()
    return {
        "data_root": str(config.DATA_ROOT),
        "basictypes": folders,
        "count": len(folders),
        "message": (
            "Choose a basictype and call generate_te_report(basictype=...)."
            if folders
            else f"No basictype folders with .eff files found under {config.DATA_ROOT}."
        ),
    }


@mcp.tool()
def inspect_basictype(basictype: str) -> dict:
    """Summarize a basictype without generating a report.

    Reports wafer count, wafer numbers, available test numbers, per-wafer yield and any
    skipped files.
    """
    ds = analysis.load_basictype(basictype)
    yields = analysis.compute_yields(ds)
    return {
        "basictype": ds.basictype,
        "p_code": ds.p_code,
        "vf_code": ds.vf_code,
        "wafer_count": len(ds.wafers),
        "wafer_numbers": ds.wafer_numbers,
        "test_numbers": ds.test_numbers,
        "yields": [
            {"wafer": y.wafer_number, "total": y.total, "pass": y.passed,
             "yield_pct": round(y.yield_pct, 2)}
            for y in yields
        ],
        "skipped_files": [{"file": f, "reason": r} for f, r in ds.skipped_files],
    }


@mcp.tool()
def generate_te_report(basictype: str, output_path: str | None = None) -> dict:
    """Process all ``.eff`` files in a basictype folder and write the PowerPoint report.

    Args:
        basictype: The basictype folder name (call ``list_basictypes`` to see options).
        output_path: Optional override for the output ``.pptx`` path.

    Slides: Title, Overall Yield, HBIN Pareto, HBIN Trend, then one slide per test number
    (1..50) with a boxplot-per-wafer and a cumulative-frequency-per-wafer chart (both with
    spec limits), plus a per-wafer Mean/Cpk table and USL/LSL header.
    """
    ds = analysis.load_basictype(basictype)
    out = Path(output_path) if output_path else report.default_output_path(ds)
    written = report.build_report(ds, out)
    return {
        "status": "ok",
        "output_path": str(written),
        "basictype": ds.basictype,
        "p_code": ds.p_code,
        "vf_code": ds.vf_code,
        "wafer_count": len(ds.wafers),
        "test_numbers": ds.test_numbers,
        "slide_count": 4 + len(ds.test_numbers),
        "skipped_files": [{"file": f, "reason": r} for f, r in ds.skipped_files],
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
