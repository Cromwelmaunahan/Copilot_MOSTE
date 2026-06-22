# Frontend Data Manager for TE

An MCP (Model Context Protocol) server that parses semiconductor **frontend test (`.eff`)**
files for a chosen *basictype* and generates a PowerPoint report of the testing results.

## What it does

Given a `basictype` (a subfolder of the data root), the server:

1. Reads every `*.eff` file in that folder (one file per wafer; wafer number comes from the
   `wafernumN_` filename prefix).
2. Parses the EFF column-oriented format (semicolon-delimited, with a multi-row metadata
   header carrying parameter names, parameter numbers, units and spec limits).
3. Computes per-wafer statistics (mean, std, **Cpk per wafer**) for test numbers 1..50.
4. Builds a `.pptx`:
   - Slide 1 – Title
   - Slide 2 – Overall Yield (table + chart)
   - Slide 3 – HBIN Pareto
   - Slide 4 – HBIN Trend
   - One slide per test number with a **boxplot per wafer** and a **cumulative-frequency
     plot per wafer**, both showing the spec limits, plus a per-wafer MEAN/CPK table and the
     USL/LSL in the header.

Pass/fail rule: **HBIN == 1 is a pass; any other HBIN (e.g. 8) is a fail.**

## Configuration

Environment variables (all optional; defaults shown):

| Variable | Default |
| --- | --- |
| `FE_DATA_ROOT` | `\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data` |
| `FE_OUTPUT_DIR` | `\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data\\Generated_PPT` |
| `FE_TEMPLATE_PPTX` | first `*.pptx` found in `FE_OUTPUT_DIR` (used as style template) |

## MCP tools

- `list_basictypes()` – list the available basictype folders under the data root.
- `generate_fe_te_report(basictype=None)` – process all EFF files in the folder and write
   the `.pptx`. If `basictype` is omitted, the server prompts the user to choose from the
   available basictype folders.
- `generate_te_report(basictype=None)` – compatibility alias for `generate_fe_te_report`.
- `inspect_basictype(basictype)` – quick summary (wafers, test numbers, yield) without
  generating a report.

## Usage guide (chat flow)

1. Trigger with: `Generate a FE TE report`
2. The server shows all available basictype folders from:
   `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data`
3. The user selects one basictype from the list.
4. The generated `.pptx` is saved to:
   `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data\Generated_PPT`

Preferred chat phrasing examples:

- `Generate a FE TE report`
- `Generate a FE TE report for P8286C`

When the chat does not include a basictype, the server shows the available basictypes from
`\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data` and
asks the user to choose one.

Generated PowerPoint files are saved under:
`\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data\Generated_PPT`.

## Run

```pwsh
python -m fe_data_manager.server
```

## VS Code MCP registration

See `.vscode/mcp.json` (created in the workspace where you want to use the server).
