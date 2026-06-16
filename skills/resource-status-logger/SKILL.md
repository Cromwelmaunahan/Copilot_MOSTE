---
name: resource-status-logger
description: 'Log resource status of a cpp file. Use when the user says "Log resource status of <filename>.cpp". Analyzes the Process() flow of the given .cpp file, tracks instrument/resource usage and signal configuration at each TerResults measurement point, and writes only summary tables with the cpp filename at the top.'
argument-hint: '<filename>.cpp - the cpp file to analyze (e.g. Trace_001.cpp)'
---

# Resource Status Logger

## When to Use

Triggered when the user says:
> "Log resource status of AAAAA.cpp"

where `AAAAA.cpp` is any `.cpp` file inside the project (e.g. `Trace_001.cpp`).

---

## The 4 Scenarios

Every analysis run must produce 4 scenario views, one for each combination of `SectorNumber` and `gHibVersion`/`mHibVersion`:

| Scenario | Output Label | SectorNumber | gHibVersion / mHibVersion |
|----------|--------------|-------------|---------------------------|
| A | OldHIB-A | 1 | false |
| B | NewHIB-A | 1 | true |
| C | OldHIB-B | 2 | false |
| D | NewHIB-B | 2 | true |

---

## Procedure

### Step 1 - Locate the target file

Search the workspace for the `.cpp` file named in the user request. Use `file_search` or `grep_search` if the path is not obvious.

### Step 2 - Collect TerResults measurement points

Find the companion `.h` header file (same folder or same base name). Collect all variables of type `TerResults`.

Also collect local `TerResults` variables in `Process()` and in helper functions that are called by `Process()`.

### Step 3 - Build a resource catalog from RegisterInstrument()

Read `RegisterInstrument()` in the target `.cpp` file and collect resources from instrument maps and switch branches.

Capture:
- Resource logical name (e.g. `RS1_APU12_1`)
- Resource type (e.g. `APU12`, `HPU`, `SPU112`)
- Sector-specific availability (SectorA path, SectorB path)
- Alias-to-resource mapping via ID assignments (e.g. `APU12_1 = mRS1_APU12_1.ID`)

Result: scenario-specific resource catalog for A/B/C/D.

### Step 4 - Build signal-operation catalog from Process() call path

From `Process()` and called helper functions, capture all resource operations and signal settings, including but not limited to:
- `apu12set`, `apu12mv`, `apu12mi`
- `hpuset`, `hpumv`
- `sp100set`, `sp100mi`, `sp100clamp`
- Other resource control calls that set force/measure modes, clamps, delays, sample count, and timing.

For each operation, capture:
- Resource identity (resolved from function argument/alias)
- Command/mode (example: `FI`, `FV`, `MV`, `MI`, `OFF`)
- Force target (voltage/current value or variable)
- Sample count and sample delay arguments
- Any clamp or special signal options

Keep only signal-driving details that matter at the measurement point. Do not log setup noise such as automatic range text, hold-state wording, or deactivate sequences unless they are the main signal action being measured.

### Step 5 - Simulate per-scenario execution path

For each scenario independently, walk through `Process()` in order and follow branch gating.

Branching rules:
- Code inside `if (mTestInputInfo.SectorNumber == 1)` is active only for A/B.
- Code inside the Sector 2 `else` is active only for C/D.
- Code inside `if (!mHibVersion)` is active only for A/C.
- Code inside `if (mHibVersion)` is active only for B/D.
- Lines outside these branch conditions are active for all scenarios.

Track resource signal state over time:
- Maintain each resource's latest active command settings.
- Update state whenever a resource command is executed.
- Ignore cleanup-only deactivate/off commands when summarizing a measurement row.

### Step 6 - Build summary rows at TerResults usage lines

For every line that references any `TerResults` variable (usage, not declaration), and is active in a scenario:
- Record one row for that measurement point.
- Store a compact resource status summary that lists active resources and their signal settings at that point.

Expected row content example:
- `RS1_APU12_1(APU12_1): FI=mdTestCurrent1, MV(count=miSampleCount1, delay=mdSampleDelay1)`
- `RS1_HPU_1(HPU_1): HPU_HI_FI=5.0, MV(count=miSampleCount1, delay=mdSampleDelay1); RS1_SP112_1(SP112_1): SP_FV=5.0, CLAMP(100,100), MI(count=miSampleCount1, delay=mdSampleDelay1)`

If no active resource setting exists at a measurement line, use `(none)`.
If the line is inactive for a scenario, use `[SKIPPED]`.

### Step 7 - Save summary tables to txt

Save to the same root location pattern used by relay-status logs:

`C:\Users\maunahan\Projects\SOFTWARES\GIT_Modified_codes\gitlab\<BaseName>_ResourceStatusLog.txt`

Example: `Trace_001_ResourceStatusLog.txt`

File content must contain only:
1. The `.cpp` filename on the first line.
2. `SECTORA TABLE` with `OldHIB-A` and `NewHIB-A` columns.
3. `SECTORB TABLE` with `OldHIB-B` and `NewHIB-B` columns.

Required output shape:

```txt
Trace_001.cpp

// ============================================================
//  SECTORA TABLE
// ============================================================
//  Test Number                         | OldHIB-A                                | NewHIB-A
//  ------------------------------------|------------------------------------------|------------------------------------------
//  TestLimits(&testResultRelayClose)   | APU12_1: FI=..., MEAS=MV(...)            | APU12_1: FI=..., MEAS=MV(...)
//  ...
// ============================================================

// ============================================================
//  SECTORB TABLE
// ============================================================
//  Test Number                         | OldHIB-B                                | NewHIB-B
//  ------------------------------------|------------------------------------------|------------------------------------------
//  TestLimits(&testResult)#1           | APU12_3: FI=..., APU12_4: FV=...         | APU12_3: FI=..., APU12_4: FV=...
//  ...
// ============================================================
```

Do not include relay catalogs, full annotated source code, or intermediate debug notes in the output file.

Use `create_file` to write the file. If it already exists, overwrite with `replace_string_in_file`.

After saving, confirm to the user with the full file path.

---

## Mandatory Header Template (copy verbatim, do not reformat)

Every output file MUST use exactly this header block for each sector. Do not change spacing, do not change ruler width, do not change column widths, do not add or remove `=` characters. Copy these lines literally and only swap the `A`/`B` suffix:

```
// ============================================================
//  SECTORA TABLE
// ============================================================
//  Test Number                              | OldHIB-A                                                                     | NewHIB-A
//  ------------------------------------|------------------------------------------------------|------------------------------------------------------
```

```
// ============================================================
//  SECTORB TABLE
// ============================================================
//  Test Number                              | OldHIB-B                                                                     | NewHIB-B
//  ------------------------------------|------------------------------------------------------|------------------------------------------------------
```

Close each sector block with exactly one line:
```
// ============================================================
```

Data rows start with `//  ` (two spaces) and use `|` as column separator. Do not pad cells to align — let the columns be ragged. The ruler line above is the fixed reference; row content width is not constrained to match it.

If the resource/signal config is identical between OldHIB-X and NewHIB-X, write the same content in both columns, or write `same` in the NewHIB-X column. Do NOT merge the two columns into one — the header template always has three columns.

## Output Quality Rules (MUST follow on first pass)

These rules exist because past runs failed user review. Apply them up-front, not after feedback.

1. **No decorative lines.** Do NOT emit `// --- Trace NNN ---` separators, blank `//` lines, or legend blocks. Output = filename, SECTORA header (title + column header + ruler), data rows, SECTORB header, data rows. Nothing else.
2. **One row per `TerResults TestLimits()` call**, in source order. Row label format: `T<trace> <helperName> TestLimits(&<varName>)#<N>` where `#N` is the running index per `TerResults` variable.
3. **HIB version rarely changes instrument/signal configuration**, but the header template ALWAYS keeps three columns. When the two HIB versions are identical, write `same` in the NewHIB-X cell. Do not merge or rename the column header.
4. **Row content is the active driver(s) at the measurement point**, in this shape:  
   `RS<sector>_<inst>_<id>(<alias>): <forceMode>=<value> [(range/clamp)]; ...; MEAS <measFn>(<args>)`  
   Example: `RS2_SP112_1(SP112_1): SP_FV=mdTestVolatge1 (SP_10V/SP_20MA) clamp=100/100/50/50; MEAS sp100mi(SP112_1, SP_MV_1X/SP_MI_1X, count=miSampleCount1, delay=mdSampleDelay1)`.
5. **Helpers that emit multiple TerResults rows must be expanded** (same rules as relay-status-logger). Every emitted row repeats the helper's active signal config — copy it for each row; do not collapse to one summary line per helper call.
6. **Inactive sector collapses to a single data row** (replacing all TerResults rows):
    - SectorA inactive: `//  Selected Test Label is not tested on SectorA          | N/A      | N/A`
    - SectorB inactive: `//  Selected Test Label is not tested on SectorB           | N/A      | N/A`
    Do not pad with `[SKIPPED]` rows, and do not use the old `// All TerResults: [N/A - <reason>]` format.
7. **No filler.** Skip `VR=Auto`, `CR=Auto`, hold states, deactivate sequences, automatic-range chatter. Keep only the force target, range/clamp when explicitly set, sample count, sample delay, and the measurement function call.

## Helper Function Expansion Rules

| Helper | Rows emitted (in order) |
|---|---|
| `RelayTest_APU_GND(..., TestRelayList[N], ...)` | 1 row baseline + N rows (one per opened relay). All N+1 rows share the same APU signal config; copy it on every row. |
| `RelayTest_APU_GND_Dual(..., TestRelayList[N], ...)` | 1 close row + N open rows. The close row uses the helper's "close" signal config (typically `FV=0 -> FI=I`, count=miSampleCount1). The open rows use the helper's "open" signal config (typically `FI=I`, count=50). |
| `RelayTest_SPU_GND(..., TestRelayList[N], ...)` | 1 Kclosed + N Kopen rows. Kclosed row often has `SP_FV=0 (NOCLAMP) -> SP_FI=...`; Kopen rows are `SP_FI=...` only. |
| `mMeasureSPU` | 1 `testResultSPUCurrent` row (MEAS `sp100mi` on the SP_FV resource) + 1 `testResultSPUVoltage` row (MEAS `sp100mv` on the SP_FI resource). Both share the same setup. |
| `mMeasureVoltagetCalcResis` | 1 `testResultResis` row. APU set FV=0 then FI=current, MEAS `apu12mv`. |
| Inline `sp100mv` + R_Ohm | 1 `R_Ohm` row. Capture force step, `lwait`, sample count, delay, and the R = V/I formula context. |

## Verification Checklist (run before saving)

- [ ] Both sector header blocks match the Mandatory Header Template byte-for-byte (the three `// ===...` / title / `// ===...` lines, the column header line, and the ruler line).
- [ ] Every sector keeps three columns (Line | OldHIB-X | NewHIB-X); use `same` instead of collapsing columns.
- [ ] No line starts with `// ---` or is a bare `//`.
- [ ] Every helper call is expanded to its real row count (matches the relay-status-logger row count for the same .cpp).
- [ ] Each row shows force target, optional range/clamp, sample count, sample delay, and the measurement call.
- [ ] Combined `OldHIB-X / NewHIB-X` column is used when signal config doesn't branch on `mHibVersion`.
- [ ] No `VR=Auto`, `CR=Auto`, hold-state, or deactivate noise.
- [ ] Inactive sector collapses to one row: `//  Selected Test Label is not tested on Sector<A|B>          | N/A      | N/A`.

## Notes

- This skill is resource-focused, not relay-focused.
- Resource names and signal settings must be derived from the target `.cpp` call path (`RegisterInstrument()`, `Process()`, and called helper functions).
- Keep summary rows focused on the signal the resource is forcing or measuring, such as `FI=...`, `FV=...`, `MV(...)`, `MI(...)`, and needed clamp settings.
- Do not include filler details like `VR=Auto`, `CR=Auto`, `DEACT=...`, or `FV0 hold` in the final summary rows.
- Scenario output labels must always be OldHIB-A, NewHIB-A, OldHIB-B, NewHIB-B.
- Output location must match relay-status logger root location pattern, but filename suffix must be `_ResourceStatusLog.txt`.
