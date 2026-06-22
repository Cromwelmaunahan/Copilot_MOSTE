"""MCP server: Auto-EFF-Converter.

Drives the Infineon STDF Analyzer to convert ``.ST4`` files into ``.eff`` files.

Chat flow:

1. Trigger with "Convert ST4 to EFF".
2. The server lists the available basictypes under the FE data root; the user picks one.
3. The server lists the ST4 files in that basictype; the user picks one.
4. The analyzer opens the ST4 file and converts it to EFF.
5. The EFF is saved next to the ST4 as ``wafernum<N>_<base>.eff`` (wafer number from the
   ST4 file name). A timestamped copy is written if that name already exists.

Run with::

    python -m auto_eff_converter.server
"""
from __future__ import annotations

import logging

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field, create_model

from . import analyzer_driver, config, st4_index

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("auto_eff_converter")

mcp = FastMCP("Auto-EFF-Converter")


def _selection_model(model_name: str, field_name: str, label: str, options: list[str]):
    description = f"Choose one {label}. Available values: {', '.join(options)}"
    return create_model(
        model_name,
        **{
            field_name: (
                str,
                Field(description=description, json_schema_extra={"enum": options}),
            )
        },
    )


async def _resolve_basictype(basictype: str | None, ctx: Context | None) -> str:
    options = st4_index.list_basictypes()
    if not options:
        raise ValueError(f"No basictype folders found under {config.DATA_ROOT}.")
    if basictype:
        if basictype not in options:
            raise ValueError(
                f"Unknown basictype '{basictype}'. Available: {', '.join(options)}"
            )
        return basictype
    if ctx is None:
        raise ValueError("basictype is required.")

    model = _selection_model("BasictypeSelection", "basictype", "basictype", options)
    result = await ctx.elicit("Convert ST4 to EFF: select the basictype.", model)
    if result.action != "accept" or result.data is None:
        raise ValueError("Conversion cancelled before basictype selection.")
    return result.data.basictype


async def _resolve_st4_file(basictype: str, st4_file: str | None, ctx: Context | None) -> str:
    options = st4_index.list_st4_files(basictype)
    if not options:
        raise ValueError(f"No ST4 files found in basictype '{basictype}'.")
    if st4_file:
        if st4_file not in options:
            raise ValueError(
                f"Unknown ST4 file '{st4_file}' in '{basictype}'. "
                f"Available: {', '.join(options)}"
            )
        return st4_file
    if ctx is None:
        raise ValueError("st4_file is required.")

    model = _selection_model("St4Selection", "st4_file", "ST4 file", options)
    result = await ctx.elicit(
        f"Convert ST4 to EFF: select the ST4 file in '{basictype}'.", model
    )
    if result.action != "accept" or result.data is None:
        raise ValueError("Conversion cancelled before ST4 file selection.")
    return result.data.st4_file


@mcp.tool(
    title="List basictypes",
    description=(
        "List the available basictype folders under the FE data root so the user can "
        "choose one for ST4-to-EFF conversion."
    ),
)
def list_basictypes() -> dict:
    """List the basictype folders under the data root."""
    options = st4_index.list_basictypes()
    return {
        "data_root": str(config.DATA_ROOT),
        "basictypes": options,
        "count": len(options),
        "message": (
            "Choose a basictype, then call list_st4_files or convert_st4_to_eff."
            if options
            else f"No basictype folders found under {config.DATA_ROOT}."
        ),
    }


@mcp.tool(
    title="List ST4 files",
    description=(
        "List the ST4 files inside a basictype folder. If basictype is omitted, the user "
        "is asked to choose one."
    ),
)
async def list_st4_files(basictype: str | None = None, ctx: Context | None = None) -> dict:
    """List ST4 files in a basictype, with the wafer number parsed from each name."""
    resolved = await _resolve_basictype(basictype, ctx)
    files = st4_index.list_st4_files(resolved)
    return {
        "basictype": resolved,
        "count": len(files),
        "st4_files": [
            {"file": name, "wafer_number": st4_index.wafer_number_from_name(name)}
            for name in files
        ],
    }


@mcp.tool(
    name="convert_st4_to_eff",
    title="Convert ST4 to EFF",
    description=(
        "Convert a selected ST4 file to an EFF file using the STDF Analyzer. If basictype "
        "or st4_file is omitted, the user is asked to choose from the available options. "
        "The EFF is saved next to the ST4 as 'wafernum<N>_<base>.eff'."
    ),
)
async def convert_st4_to_eff(
    basictype: str | None = None,
    st4_file: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Open the ST4 in the analyzer, convert to EFF, and save it next to the ST4 file."""
    resolved_bt = await _resolve_basictype(basictype, ctx)
    resolved_st4 = await _resolve_st4_file(resolved_bt, st4_file, ctx)

    st4_path = st4_index.st4_path(resolved_bt, resolved_st4)
    wafer_number = st4_index.wafer_number_from_name(resolved_st4)
    if wafer_number is None:
        raise ValueError(
            f"Could not determine the wafer number from '{resolved_st4}'. "
            "Expected a '.st4_<number>_' token in the file name."
        )

    eff_target = st4_index.eff_output_path(st4_path, wafer_number)
    written = analyzer_driver.convert(st4_path, eff_target)
    return {
        "status": "ok",
        "basictype": resolved_bt,
        "st4_file": resolved_st4,
        "wafer_number": wafer_number,
        "eff_path": str(written),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
