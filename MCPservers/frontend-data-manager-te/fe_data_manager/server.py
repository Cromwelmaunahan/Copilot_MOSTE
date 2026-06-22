"""MCP server: Frontend Data Manager for TE.

Exposes tools to list basictype folders, inspect a basictype, and generate a PowerPoint
report of frontend testing results from ``.eff`` files.

Run with::

    python -m fe_data_manager.server
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field, create_model

from . import analysis, config, report

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fe_data_manager")

mcp = FastMCP("Frontend Data Manager for TE")

_DEFAULT_FE_DATA_ROOT = Path(
    r"\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data"
)

if not os.environ.get("FE_DATA_ROOT"):
    config.DATA_ROOT = _DEFAULT_FE_DATA_ROOT
if not os.environ.get("FE_OUTPUT_DIR"):
    config.OUTPUT_DIR = config.DATA_ROOT / "Generated_PPT"


def _list_basictype_folders() -> list[str]:
    if not config.DATA_ROOT.is_dir():
        return []
    out = []
    for child in sorted(config.DATA_ROOT.iterdir()):
        if child.is_dir() and child.name not in config.IGNORED_FOLDERS:
            if any(child.glob("*.eff")):
                out.append(child.name)
    return out


def _build_basictype_selection_model(folders: list[str]):
    description = (
        "Choose one FE basictype folder from the FE data root. "
        f"Available values: {', '.join(folders)}"
    )
    return create_model(
        "BasictypeSelection",
        basictype=(
            str,
            Field(description=description, json_schema_extra={"enum": folders}),
        ),
    )


async def _resolve_basictype(basictype: str | None, ctx: Context | None = None) -> str:
    folders = _list_basictype_folders()
    if not folders:
        raise ValueError(
            f"No basictype folders with .eff files found under {config.DATA_ROOT}."
        )

    if basictype:
        return basictype

    if ctx is None:
        raise ValueError("basictype is required.")

    selection_model = _build_basictype_selection_model(folders)
    result = await ctx.elicit(
        "Generate a FE TE report: select the basictype to process.",
        selection_model,
    )
    if result.action != "accept" or result.data is None:
        raise ValueError("FE TE report generation was cancelled before basictype selection.")
    return result.data.basictype


def _generate_report_result(basictype: str, output_path: str | None) -> dict:
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


@mcp.tool(
    title="List FE basictypes",
    description=(
        "List all FE basictypes currently available under the FE data root so the user can "
        "choose one for FE TE report generation."
    ),
)
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
            "Choose a basictype and call generate_fe_te_report(basictype=...)."
            if folders
            else f"No basictype folders with .eff files found under {config.DATA_ROOT}."
        ),
    }


@mcp.tool(
    title="Inspect FE basictype",
    description=(
        "Summarize one FE basictype before report generation. Use this to review wafer "
        "count, test coverage, and yield for the selected basictype."
    ),
)
async def inspect_basictype(basictype: str | None = None, ctx: Context | None = None) -> dict:
    """Summarize a basictype without generating a report.

    Reports wafer count, wafer numbers, available test numbers, per-wafer yield and any
    skipped files.
    """
    ds = analysis.load_basictype(await _resolve_basictype(basictype, ctx))
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


@mcp.tool(
    name="generate_fe_te_report",
    title="Generate FE TE report",
    description=(
        "Generate a FE TE PowerPoint report for a selected basictype. The basictype "
        "parameter is exposed as a selectable list of all available FE data folders."
    ),
)
async def generate_fe_te_report(
    basictype: str | None = None,
    output_path: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Process all ``.eff`` files in a basictype folder and write the PowerPoint report.

    Args:
        basictype: The selected basictype folder name. If omitted, the server asks the
            user to choose from all available FE data folders.
        output_path: Optional override for the output ``.pptx`` path.

    Slides: Title, Overall Yield, HBIN Pareto, HBIN Trend, then one slide per test number
    (1..50) with a boxplot-per-wafer and a cumulative-frequency-per-wafer chart (both with
    spec limits), plus a per-wafer Mean/Cpk table and USL/LSL header.
    """
    return _generate_report_result(await _resolve_basictype(basictype, ctx), output_path)


@mcp.tool(
    name="generate_te_report",
    title="Generate TE report",
    description="Legacy alias for generate_fe_te_report.",
)
async def generate_te_report(
    basictype: str | None = None,
    output_path: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Compatibility alias for clients already calling ``generate_te_report``."""
    return _generate_report_result(await _resolve_basictype(basictype, ctx), output_path)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
