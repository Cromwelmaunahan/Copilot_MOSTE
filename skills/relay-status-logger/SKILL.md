---
name: relay-status-logger
description: 'Log relay status of a cpp file. Use when the user says "Log relay status of <filename>.cpp". Analyzes the Process() function of the given .cpp file, tracks all mSetRelays() calls to determine which relays are closed at each TerResults measurement point, and writes only a summary table with the cpp filename at the top.'
argument-hint: '<filename>.cpp — the cpp file to analyze (e.g. Trace_001.cpp)'
---

# Relay Status Logger

## When to Use

Triggered when the user says:
> "Log relay status of AAAAA.cpp"

where `AAAAA.cpp` is any `.cpp` file inside the project (e.g. `Trace_001.cpp`).

---

## The 4 Scenarios

Every analysis run must produce **4 separate scenario logs**, one for each combination of `SectorNumber` and `gHibVersion`/`mHibVersion`:

| Scenario | Output Label | SectorNumber | gHibVersion / mHibVersion |
|----------|--------------|-------------|--------------------------|
| A | OldHIB-A | 1 | false |
| B | NewHIB-A | 1 | true |
| C | OldHIB-B | 2 | false |
| D | NewHIB-B | 2 | true |

Each scenario has its own:
- **Relay Name Catalog** (AssignIntBit/AssignExtBit calls are inside `if (sectorNumber == N)` + `if (gHibVersion)` / `else` branches in `LoadCBitConfiguration`)
- **Relay variable values** (`mStoreRelayConfig()` branches on `SectorNumber` and `mHibVersion` for some variables)
- **Active code path** in `Process()` (branches on `SectorNumber` and `mHibVersion`)

---

## Procedure

### Step 1 — Locate the target file

Search the workspace for the `.cpp` file named in the user's request. Use `file_search` or `grep_search` if the path is not obvious.

### Step 2 — Collect TerResults variable names

Find the companion `.h` header file (same folder or same base name). Scan it for all member variables declared with type `TerResults`. Collect every variable name.

Example header pattern:
```cpp
TerResults testResultRelayClose, testResult;
TerResults testResultRelayOpenPosCurrent;
TerResults testResultRelayOpenNegCurrent;
```
Collected names: `testResultRelayClose`, `testResult`, `testResultRelayOpenPosCurrent`, `testResultRelayOpenNegCurrent`

> Also collect `TerResults` variables declared inside the `Process()` function body (local variables), and inside any helper functions that are called from within `Process()`.

### Step 3 — Build 4 Relay Name Catalogs from AssignIntBit / AssignExtBit

Search the entire workspace for `LoadCBitConfiguration` (typically in `DibCheckModulesUtility.cpp`). Read the full function body.

The function is structured as nested branches:
```
if (sectorNumber == 1)
    if (gHibVersion == true)  → Scenario B catalog
    else                      → Scenario A catalog
else  (sectorNumber == 2)
    if (gHibVersion == true)  → Scenario D catalog
    else                      → Scenario C catalog
```

For each of the 4 branches, collect all `AssignIntBit` and `AssignExtBit` calls found **within that branch only**. Extract the first argument of each call as the relay name.

```cpp
mITerCBit->AssignIntBit("KIY61_KIZ61", 3, false, MS_ALL, "...", "V23086");
//                       ^^^^^^^^^^^^^ ← relay name

mITerCBit->AssignExtBit("KSB3", 0, 0, 0, true, MS_ALL, "...", "V23086");
//                       ^^^^^^ ← relay name
```

Result: 4 separate relay name catalogs (A, B, C, D).

### Step 4 — Resolve relay variable values for each scenario

Find `mStoreRelayConfig()` in the target `.cpp` file. It branches on `SectorNumber` (and sometimes `mHibVersion`) to assign values to relay string variables (`ClosedRelays`, `OpenRelays1`, ...).

For each scenario, determine the value of every relay string variable used in `mSetRelays()` calls:

- If the variable is assigned a **string constant name** (e.g., `OpenRelays1 = m12AextK001_ApuToSf1a`), look up that constant's string value in the same `.cpp` or `.h` file. Relay names in those strings must be validated against the scenario's catalog (Step 3). Flag any name not in the catalog as `[!UNKNOWN]`.
- If the assignment uses a **ternary on `mHibVersion`** (e.g., `(!mHibVersion ? m1ABintK100_ApuLoToGnd : "")`), resolve separately for mHibVersion=false and mHibVersion=true.
- If a variable resolves to `""` (empty string), it contributes no relays.

Build a **resolved relay map** per scenario: `{ VariableName → [relay1, relay2, ...] }`.

### Step 5 — Simulate relay state for each scenario

For each of the 4 scenarios independently, walk through the `Process()` function body and track the **"currently closed relays"** set.

**Branching rules:**
- For lines inside `if (mTestInputInfo.SectorNumber == 1)`: active only in Scenarios A and B.
- For lines inside the `else` (Sector 2): active only in Scenarios C and D.
- For lines inside `if (!mHibVersion)`: active only in Scenarios A and C.
- For lines inside `if (mHibVersion)`: active only in Scenarios B and D.
- Lines outside any such branch: active in all scenarios.

**Relay tracking rules for `mSetRelays(openArg, closeArg)`:**
- `openArg`: look up its resolved relay list → remove those relays from the closed set.
- `closeArg`: look up its resolved relay list → add those relays to the closed set.
- If an argument is `""`: no change for that slot.
- If it resolves to an empty list: no change.

### Step 6 — Build the summary-table rows for each scenario

For every line that **contains a reference to any TerResults variable** (usage, not declaration) and is **active in a given scenario**:

- Record one summary-table row for that measurement point.
- Store the closed relay names at that point.
- If no relays are closed, store `(none)`.
- If the line is skipped due to branching in a given scenario, store `[SKIPPED]` for that scenario.

Do not emit annotated source code in the final txt output. Use these collected rows only to build the final summary tables.

### Step 7 — Save the summary table to a txt file

Save to:
```
C:\Users\maunahan\Projects\SOFTWARES\GIT_Modified_codes\gitlab\<BaseName>_RelayStatusLog.txt
```
Example: `Trace_001_RelayStatusLog.txt`

The file must contain only these parts, in this order:

1. The `.cpp` filename on the very first line.
2. **SectorA Table** containing Scenario A and Scenario B only.
3. **SectorB Table** containing Scenario C and Scenario D only.

Required output shape:
```
Trace_001.cpp

// ============================================================
//  SECTORA TABLE
// ============================================================
//  Test Number                         | OldHIB-A       | NewHIB-A
//  ------------------------------------|----------------|----------------
//  TestLimits(&testResultRelayClose)   | KSB3,KL255,... | KSB3,KL255,...
//  TestLimits(&testResultRelayOpenP)#1 | KSB3,KL255,... | ...
//  ...
// ============================================================

// ============================================================
//  SECTORB TABLE
// ============================================================
//  Test Number                         | OldHIB-B       | NewHIB-B
//  ------------------------------------|----------------|----------------
//  TestLimits(&testResultRelayClose)   | KSB3,KL255,... | KSB3,KL255,...
//  TestLimits(&testResultRelayOpenP)#1 | KSB3,KL255,... | ...
//  ...
// ============================================================
```

Do not include relay catalogs, resolved relay-variable sections, or annotated `Process()` code in the final txt file.

Use `create_file` to write the file. If it already exists, overwrite with `replace_string_in_file`.

After saving, confirm to the user with the full file path.

---

## Relay Tracking Rules (detailed)

> **CRITICAL — `mSetRelays` signature:** `void mSetRelays(std::string open, std::string close)`. The FIRST argument is OPENED, the SECOND argument is CLOSED. Inline `//` comments next to `mSetRelays(...)` calls in module .cpp files are often wrong or copy-pasted from elsewhere — ALWAYS trust this signature, NEVER infer from the inline comment.

| Situation | Action |
|---|---|
| `mSetRelays("", X)` | Add resolved relay names of X to closed set |
| `mSetRelays(X, "")` | Remove resolved relay names of X from closed set |
| `mSetRelays(X, Y)` | Remove resolved names of X, then add resolved names of Y |
| `mSetRelays("", "")` | No change |
| Variable resolves to empty string `""` | No change |
| Relay name not in scenario's catalog | Flag as `[!UNKNOWN: name]` |
| Line inside branch not active for this scenario | Mark as `[SKIPPED]` |

---

## Output Format Example

```
Trace_001.cpp

// ============================================================
//  SECTORA TABLE
// ============================================================
//  Test Number                                  | OldHIB-A        | NewHIB-A
//  ---------------------------------------------|-----------------|-----------------
//  TestLimits(&testResultRelayClose)            | K001,K055,...   | KA1,KH155,...
//  TestLimits(&testResultRelayOpenPosCurrent)#1 | Lim_SF_1A,...   | KSA1,KH155,...
//  TestLimits(&testResultRelayOpenNegCurrent)   | K001,K055,...   | [SKIPPED]
//  TestLimits(&testResult)#1                    | [SKIPPED]       | [SKIPPED]
// ============================================================

// ============================================================
//  SECTORB TABLE
// ============================================================
//  Test Number                                  | OldHIB-B        | NewHIB-B
//  ---------------------------------------------|-----------------|-----------------
//  TestLimits(&testResultRelayClose)            | K001,K016,K002  | KA1,KSA1,...
//  TestLimits(&testResultRelayOpenPosCurrent)#1 | [SKIPPED]       | [SKIPPED]
//  TestLimits(&testResultRelayOpenNegCurrent)   | Lim_SF_2B,...   | KSB3,KH255,...
//  TestLimits(&testResult)#1                    | K001,K016,K002  | KA1,KSA1,...
// ============================================================
```

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

## Output Quality Rules (MUST follow on first pass)

These rules exist because past runs failed user review. Apply them up-front, not after feedback.

1. **No decorative lines.** Do NOT emit `// --- Trace NNN ---` separators, blank `//` lines, legend blocks, or alias-definition sections. The output is data rows only: filename, SECTORA header (3 lines: title + column header + ruler), data rows, SECTORB header (3 lines), data rows. Nothing else.
2. **One row per `TerResults TestLimits()` call**, in source order. Tag with `T<traceNumber>` (or the explicit measurement label from the surrounding context) plus the helper that produced it and a `#N` running index per `TerResults` variable. Example: `T103 RelayTest_APU_GND TestLimits(&testResultVoltage)#1`.
3. **Never write `(all closed)`, `(none, all closed)`, or similar placeholders.** Always enumerate every closed relay name, comma-separated, no spaces. Empty set is the only case allowed to use `(none)`.
4. **Never invent aliases** such as `TRU_A_new`, `Spu100_openFS_n`, `<var>_expanded`. The two columns hold raw relay names only.
5. **OldHIB column = raw C++ string verbatim.** If the source resolves to a compound token like `TRU_A`, `TRU_B`, `Spu100_openFS`, `K23_K123`, `K28_K29`, `K35_K135`, write that exact token. Do NOT expand it into component relay names in the OldHIB column even if a catalog mapping exists.
6. **NewHIB column = fully expanded relay names**, comma-joined in source order. When a variable resolves via `gHibVersion ? "A,B,C" : "X"`, the NewHIB column gets `A,B,C` written out (every name), not the variable name and not a shortened form.
7. **Preserve C++ string-concatenation duplicates.** If the source code concatenates a CloseRelay string and a TestRelay string and they share a relay name, the duplicate stays in the row (it reflects what `mSetRelays` actually receives). Do not silently de-duplicate.
8. **Sector with no active code path** collapses to a single data row (one per inactive sector, replacing all TerResults rows):
    - SectorA inactive: `//  Selected Test Label is not tested on SectorA          | N/A      | N/A`
    - SectorB inactive: `//  Selected Test Label is not tested on SectorB           | N/A      | N/A`
    Do not pad with `[SKIPPED]` rows, and do not use the old `// All TerResults: [N/A - <reason>]` format.
9. **List ONLY closed/energized relays.** Each cell shows the comma-joined set of relays that are CLOSED at that measurement point. Never list opened relays, never write `[open: ...]`, `[still open]`, or post-loop cleanup state.
10. **No conditionals in rows.** Never write `if dVal>=0`, `[state per sign of dVal]`, `<setupInductor_uH(N)>`, or any runtime/PDS-dependent placeholder. Resolve to the canonical branch and list the resulting closed relays directly:
    - PDS test currents / sign-dependent toggles → assume positive (RelayList closed branch).
    - `mHibVersion` ternaries → use the false branch for OldHIB columns and the true branch for NewHIB columns.
    - Inductor helper (`setupInductor_uH`) → omit the inductor-box KL_xx relays entirely (runtime-detected box type).
11. **No trailing Notes block.** The output ends at the second sector's closing `// ===...` line. No `// Notes:` section, no commentary.

## Helper Function Expansion Rules

Several helpers in `DibCheckModulesCommon.cpp` emit MORE than one `TerResults` row per call. You MUST expand each call into its actual emitted rows before writing the table. Verify the helper body in source before counting rows.

| Helper | Rows emitted (in order) |
|---|---|
| `RelayTest_APU_GND(..., TestRelayList[N], ...)` | 1 row `testResultVoltage` with all-closed state (i = -1 baseline), then N rows `testResultVoltage` where each `TestRelayList[i]` is opened one at a time. Total = 1 + N. |
| `RelayTest_APU_GND_Dual(..., TestRelayList[N], ...)` | 1 row `testResultCloseVoltage` (all closed), then N rows `testResultOpenVoltage` (each `TestRelayList[i]` opened one at a time). Total = 1 + N. |
| `RelayTest_SPU_GND(..., TestRelayList[N], ...)` | 1 row `Kclosed` (all closed), then N rows `Kopen` (each `TestRelayList[i]` opened). Total = 1 + N. |
| `mMeasureSPU` / `mMeasureVoltagetCalcResis` / inline `sp100mv`+`R_Ohm` | Each `TestLimits()` inside the helper = one row. Count them directly in the helper body. |

When opening a relay for the i-th row, the closed-set for that row = (baseline closed-set) − {TestRelayList[i]}. List the remaining closed relays.

## Verification Checklist (run before saving)

Confirm every item is true. If any fails, fix BEFORE calling `create_file`.

- [ ] Both sector header blocks match the Mandatory Header Template byte-for-byte (the three `// ===...` / title / `// ===...` lines, the column header line, and the ruler line).
- [ ] No line starts with `// ---` or is a bare `//`.
- [ ] No occurrence of `(all closed)`, `all closed`, `TRU_A_new`, `TRU_B_new`, `_expanded`, `_n` suffix aliases.
- [ ] Every helper call has been expanded to its real row count per the table above.
- [ ] OldHIB column shows raw source tokens (`TRU_A`, `Spu100_openFS`, `K23_K123`, etc.) where the source uses them.
- [ ] NewHIB column shows enumerated relay names — no variable references, no `...`, no abbreviations.
- [ ] Row count per sector equals the sum of (rows-per-helper-call) for all active code paths.
- [ ] If a sector has no active code, the only data row under its header is `//  Selected Test Label is not tested on Sector<A|B>          | N/A      | N/A`.

## Notes

- **4 scenarios must always be logged**: Sector1+HIBfalse (A=OldHIB-A), Sector1+HIBtrue (B=NewHIB-A), Sector2+HIBfalse (C=OldHIB-B), Sector2+HIBtrue (D=NewHIB-B).
- **Relay name source**: relay names come from the first argument of `AssignIntBit` / `AssignExtBit` calls inside the matching sector+HIBversion branch of `LoadCBitConfiguration`.
- **Relay variable resolution**: `mStoreRelayConfig()` in the target `.cpp` assigns relay group variables. Resolve them per scenario — pay attention to ternary expressions on `mHibVersion` (e.g., `(!mHibVersion ? X : "")`).
- **Process() branching**: `if (SectorNumber==1)` / `else` and `if (!mHibVersion)` / `if (mHibVersion)` gates determine which lines are active per scenario. Mark skipped lines as `[SKIPPED]` in the summary table.
- **Relay constant lookup**: relay group variables are often assigned from named constants (e.g., `m12AextK001_ApuToSf1a`). Look up these constants in the `.cpp`/`.h` files to get their actual string values (the real relay names).
- **Output file content**: only the cpp filename at the top plus 2 summary tables: SectorA Table (OldHIB-A/NewHIB-A) and SectorB Table (OldHIB-B/NewHIB-B).
