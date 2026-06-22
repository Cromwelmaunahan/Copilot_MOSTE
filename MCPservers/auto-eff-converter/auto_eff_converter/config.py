"""Configuration for the Auto-EFF-Converter MCP server.

All paths and automation settings can be overridden via environment variables so the
server is portable and the UI-automation can be re-calibrated without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path

# Root folder that contains one subfolder per basictype (e.g. P8266B), each holding ST4
# files to convert. Same share used by the Frontend Data Manager.
DATA_ROOT = Path(
    os.environ.get(
        "AEC_DATA_ROOT",
        r"\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data",
    )
)

# Folder names under DATA_ROOT that are NOT basictypes and must be ignored when listing.
IGNORED_FOLDERS = {"Generated_PPT"}

# Path to the STDF Analyzer executable (Infineon eSquare STDF Analyzer).
ANALYZER_PATH = Path(
    os.environ.get(
        "AEC_ANALYZER_PATH",
        r"C:\Program Files\STDF Analyzer 3.4.1.1\_STDFAnalyser.exe",
    )
)

# pywinauto backend ("uia" for modern .NET/WPF, "win32" for classic WinForms).
UI_BACKEND = os.environ.get("AEC_UI_BACKEND", "uia")

# Regex used to locate the STDF Analyzer main window by title.
WINDOW_TITLE_RE = os.environ.get("AEC_WINDOW_TITLE_RE", ".*STDF Analy.*")

# Menu paths (arrow-separated) for the two actions. Override if the app's menu text
# differs. These are passed to pywinauto ``menu_select``.
MENU_OPEN = os.environ.get("AEC_MENU_OPEN", "File->Open")
MENU_CONVERT_EFF = os.environ.get("AEC_MENU_CONVERT_EFF", "Convert->To EFF")

# Timeouts (seconds).
APP_START_TIMEOUT = float(os.environ.get("AEC_APP_START_TIMEOUT", "60"))
DIALOG_TIMEOUT = float(os.environ.get("AEC_DIALOG_TIMEOUT", "30"))
CONVERT_TIMEOUT = float(os.environ.get("AEC_CONVERT_TIMEOUT", "180"))

# Optional extra directory to watch for the produced EFF if the analyzer writes it to a
# default output location instead of the ST4 folder. Empty = watch the ST4 folder only.
_WATCH_ENV = os.environ.get("AEC_EFF_WATCH_DIR", "").strip()
EFF_WATCH_DIR: Path | None = Path(_WATCH_ENV) if _WATCH_ENV else None

# Keep the analyzer process open between conversions (faster) or close it each time.
KEEP_APP_OPEN = os.environ.get("AEC_KEEP_APP_OPEN", "1") not in {"0", "false", "False"}
