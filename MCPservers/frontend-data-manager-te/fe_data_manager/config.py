"""Configuration for the Frontend Data Manager for TE MCP server.

All paths can be overridden via environment variables so the server is portable.
"""
from __future__ import annotations

import os
from pathlib import Path

# Root folder that contains one subfolder per basictype (e.g. P8266B), plus Generated_PPT.
DATA_ROOT = Path(
    os.environ.get("FE_DATA_ROOT", r"C:\Users\maunahan\Projects\Copilot_FE_data")
)

# Where generated .pptx files are written.
OUTPUT_DIR = Path(
    os.environ.get("FE_OUTPUT_DIR", str(DATA_ROOT / "Generated_PPT"))
)

# Optional reference/template .pptx used for slide styling. If unset, the first *.pptx
# found in OUTPUT_DIR is used (if any); otherwise a blank presentation is created.
_TEMPLATE_ENV = os.environ.get("FE_TEMPLATE_PPTX", "").strip()
TEMPLATE_PPTX: Path | None = Path(_TEMPLATE_ENV) if _TEMPLATE_ENV else None

# Folder name that is NOT a basictype and must be ignored when listing.
IGNORED_FOLDERS = {"Generated_PPT"}

# Test numbers to report on (inclusive). Missing ones are simply skipped.
TEST_NUMBER_MIN = 1
TEST_NUMBER_MAX = 50

# Pass/fail definition.
PASS_HBIN = 1


def resolve_template() -> Path | None:
    """Return the template .pptx to use, or None if no template is available."""
    if TEMPLATE_PPTX is not None and TEMPLATE_PPTX.is_file():
        return TEMPLATE_PPTX
    if OUTPUT_DIR.is_dir():
        candidates = sorted(OUTPUT_DIR.glob("*.pptx"))
        if candidates:
            return candidates[0]
    return None
