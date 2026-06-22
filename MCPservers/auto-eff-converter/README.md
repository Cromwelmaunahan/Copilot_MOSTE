# Auto-EFF-Converter

An MCP (Model Context Protocol) server that drives the **Infineon STDF Analyzer** desktop
app to convert `.ST4` files into `.eff` files for a selected basictype.

## What it does

1. Lists the **basictype** folders under the FE data root; the user selects one.
2. Lists the **ST4 files** inside that basictype; the user selects one.
3. Opens the ST4 file in the STDF Analyzer (`File ▸ Open`) and converts it
   (`Convert ▸ To EFF`).
4. Saves the resulting `.eff` next to the ST4 file, named `wafernum<N>_<base>.eff`.
   - `<N>` = the wafer number taken from the ST4 file name (digits after `.st4_`,
     e.g. `...N.st4_006_...` → wafer 6).
   - If that name already exists, a timestamped copy is written (no overwrite).

## Usage guide (chat flow)

1. Trigger with: `Convert ST4 to EFF`
2. Select a basictype from the list shown (folders under
   `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data`).
3. Select the ST4 file to convert.
4. The EFF is saved in the same folder as the ST4 file.

## MCP tools

- `list_basictypes()` – list the basictype folders under the data root.
- `list_st4_files(basictype=None)` – list ST4 files in a basictype (asks for the basictype
  if omitted), with each file's parsed wafer number.
- `convert_st4_to_eff(basictype=None, st4_file=None)` – convert one ST4 to EFF. Prompts for
  the basictype and ST4 file when omitted.

## Configuration

Environment variables (all optional; defaults shown):

| Variable | Default |
| --- | --- |
| `AEC_DATA_ROOT` | `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data` |
| `AEC_ANALYZER_PATH` | `C:\Program Files\STDF Analyzer 3.4.1.1\_STDFAnalyser.exe` |
| `AEC_UI_BACKEND` | `uia` (use `win32` for classic WinForms menus) |
| `AEC_WINDOW_TITLE_RE` | `.*STDF Analy.*` |
| `AEC_MENU_OPEN` | `File->Open` |
| `AEC_MENU_CONVERT_EFF` | `Convert->To EFF` |
| `AEC_EFF_WATCH_DIR` | _(empty)_ — extra folder to watch if the analyzer writes EFF elsewhere |
| `AEC_KEEP_APP_OPEN` | `1` |

> The conversion uses Windows UI Automation (pywinauto) because the STDF Analyzer is a
> GUI-only .NET app with no command-line converter. It must run on the same machine where
> the analyzer is installed, with a visible interactive desktop. The window title and menu
> paths above can be re-calibrated via the environment variables without code changes.

## Run

```pwsh
python -m auto_eff_converter.server
```

## VS Code MCP registration

See `.vscode/mcp.json`.

## Project layout

```
auto-eff-converter/
├─ auto_eff_converter/
│  ├─ __init__.py
│  ├─ config.py            # paths, analyzer path, UI/menu/timeout settings (env-overridable)
│  ├─ st4_index.py         # basictype/ST4 enumeration, wafer-number parsing, EFF naming
│  ├─ analyzer_driver.py   # pywinauto automation of File>Open and Convert>To EFF
│  └─ server.py            # MCP server (FastMCP) — tool definitions
├─ .vscode/mcp.json
├─ requirements.txt
├─ pyproject.toml
└─ README.md
```
