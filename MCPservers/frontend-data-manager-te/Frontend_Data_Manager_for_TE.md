# Frontend Data Manager for TE — MCP Server

An MCP (Model Context Protocol) server that parses MOSFET **frontend test (`.eff`)** files
for a chosen *basictype* and generates a PowerPoint report of the testing results.

- **Server name:** `Frontend Data Manager for TE`
- **Project:** `C:\Users\maunahan\Projects\frontend-data-manager-te`
- **Language / stack:** Python 3.11, `mcp`, `pandas`, `numpy`, `matplotlib`, `python-pptx`
- **Entry point:** `python -m fe_data_manager.server`

---

## 1. Purpose

Given a `basictype` (a subfolder of the data root, named after the basictype), the server:

1. Reads every `*.eff` file in that folder. **One file = one wafer**; the wafer number is
   taken from the `wafernumN_` filename prefix (`wafernum1_…` → Wafer #1, etc.).
2. Parses the EFF column-oriented format.
3. Computes per-wafer statistics for **test numbers 1..50** (those that exist).
4. Builds a `.pptx` and writes it to the `Generated_PPT` folder.

---

## 2. MCP tools

| Tool | Description |
| --- | --- |
| `list_basictypes()` | List basictype folders (those containing `.eff` files) under the data root. |
| `inspect_basictype(basictype)` | Summary only: wafers, test numbers, per-wafer yield, skipped files. |
| `generate_te_report(basictype, output_path=None)` | Parse all EFF files and write the report `.pptx`. |

Typical flow: call `list_basictypes()`, ask the user which basictype, then
`generate_te_report(basictype="P8266B")`.

---

## 3. Configuration (environment variables)

| Variable | Default |
| --- | --- |
| `FE_DATA_ROOT` | `C:\Users\maunahan\Projects\Copilot_FE_data` |
| `FE_OUTPUT_DIR` | `<FE_DATA_ROOT>\Generated_PPT` |
| `FE_TEMPLATE_PPTX` | first `*.pptx` in `FE_OUTPUT_DIR` (used for slide-size reference) |

> The original data location was the UNC share
> `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data`. It was
> copied locally because VS Code blocks UNC hosts by default. To read the share directly,
> add `"security.allowedUNCHosts": ["Mucsdn31"]` to settings and set `FE_DATA_ROOT` to the
> UNC path.

---

## 4. Output `.pptx`

File name pattern: **`<P-code> – <VF-code> FE Testing Results.pptx`**, e.g.
`P8266B – VF524022 FE Testing Results.pptx`, written to `FE_OUTPUT_DIR`.

- `P-code` = the basictype folder name.
- `VF-code` = the `Wafer` field inside the EFF data (e.g. `VF524022`).

### Slide structure

1. **Title** — P-code, VF-code, basictype, wafer/file counts, date.
2. **Overall Yield** — bar chart of pass% per wafer + a summary table.
3. **HBIN Pareto** — fail-bin counts (descending) with cumulative % line.
4. **HBIN Trend** — fail % of the top fail bins across wafer numbers.
5. **One slide per test number (1..50 that exist)**, each with:
   - Header: test name + unit, **USL**, **LSL**, overall mean.
   - **Left:** boxplot, one box per wafer, with USL/LSL limit lines.
   - **Right:** cumulative-frequency plot (dotted line per wafer), with USL/LSL limit lines.
   - **Bottom:** per-wafer table of N, **Mean**, **Cpk** (Cpk computed *per wafer*).

---

## 5. Statistics

For each test number and **each wafer**:

- Mean (μ) and sample std (σ, ddof=1) over the valid (non-blank) measured values.
- **Cpk (per wafer):** `min((USL − μ)/(3σ), (μ − LSL)/(3σ))`. Single-sided when only one
  limit exists; returns n/a when σ = 0 or there is no data.

**Pass/fail rule:** `HBIN == 1` is a **pass**; any other HBIN (e.g. 8, 11, 12, 19, 31) is a
**fail**. Yield% = passing dies / total dies.

---

## 6. EFF file format (parser notes)

The `.eff` files are **semicolon-delimited and column-oriented** (not one row per test):

- Line 1: `<<EFF:1.00>>;Headers=..;Rows=..;Columns=N;..` declares column count `N`.
- Metadata rows (prefixed by a `<tag>;`) carry per-column attributes; after dropping the
  leading tag, the values align to the data columns:
  - `<+EFF:..>` → data **column names** (`Lot, Wafer, X, Y, CHIP_ID, HBIN, …, PF, …`).
  - `<+ParameterName>` → clean parameter name (e.g. `BVDSS1MA`, `VGSTH`).
  - `<+ParameterNumber>` → the **test number** for that column (this is the `TestNr`).
    Measurement tests use 1..50; columns numbered ≥300000 are DPAT/limit helpers (ignored).
  - `<PARATTR:UNIT>` → unit (VOLTS, AMPS, Ohms, …).
  - `<LIMIT:SPEC:LOWER_VALUE>` → **LSL**; `<LIMIT:SPEC:UPPER_VALUE>` → **USL**.
- Data rows (no `<` prefix): one per die; quoted text fields; empty fields → `NaN` (failed
  dies have blank measurements).

### Critical alignment detail

The analyser inserts **one extra unlabeled die-level column** just before the
`HBIN`/`CHIP_ID` status block, so raw data rows are one field wider than the name row and
are shifted from that point on. The parser:

1. Detects the shift by locating the `PF` column (values are `P`/`F`) and comparing to the
   `PF` name index.
2. Applies that offset to all columns from `HBIN` onward (status + every measurement),
   while reading the leading identity columns (`Lot, Wafer, X, Y`) at offset 0.

This was verified on `P8266B/wafernum1_…eff`: HBIN==1 count (9570) matches PF=`P` count, and
measurements fall within their spec limits.

---

## 7. VS Code MCP registration

`.vscode/mcp.json` in the project:

```json
{
  "servers": {
    "frontend-data-manager-te": {
      "type": "stdio",
      "command": "C:/Users/maunahan/AppData/Local/Microsoft/WindowsApps/python3.11.exe",
      "args": ["-m", "fe_data_manager.server"],
      "cwd": "C:/Users/maunahan/Projects/frontend-data-manager-te",
      "env": { "FE_DATA_ROOT": "C:/Users/maunahan/Projects/Copilot_FE_data" }
    }
  }
}
```

After saving, start the server from the MCP Servers view (or it auto-discovers), then ask
Copilot: *"List basictypes"* and *"Generate the TE report for P8266B"*.

---

## 8. Project layout

```
frontend-data-manager-te/
├─ fe_data_manager/
│  ├─ __init__.py
│  ├─ config.py        # paths & constants (env-overridable)
│  ├─ eff_parser.py    # EFF format parser (alignment-aware)
│  ├─ analysis.py      # dataset loading, yield, Cpk, HBIN pareto/trend
│  ├─ report.py        # matplotlib charts + python-pptx assembly
│  └─ server.py        # MCP server (FastMCP) — tool definitions
├─ .vscode/mcp.json
├─ requirements.txt
├─ pyproject.toml
└─ README.md
```
