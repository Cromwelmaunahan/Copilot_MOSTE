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
| `FE_DATA_ROOT` | `C:\Users\maunahan\Projects\Copilot_FE_data` |
| `FE_OUTPUT_DIR` | `<FE_DATA_ROOT>\Generated_PPT` |
| `FE_TEMPLATE_PPTX` | first `*.pptx` found in `FE_OUTPUT_DIR` (used as style template) |

## MCP tools

- `list_basictypes()` – list the available basictype folders under the data root.
- `generate_te_report(basictype)` – process all EFF files in the folder and write the `.pptx`.
- `inspect_basictype(basictype)` – quick summary (wafers, test numbers, yield) without
  generating a report.

## Run

```pwsh
python -m fe_data_manager.server
```

## VS Code MCP registration

See `.vscode/mcp.json` (created in the workspace where you want to use the server).
