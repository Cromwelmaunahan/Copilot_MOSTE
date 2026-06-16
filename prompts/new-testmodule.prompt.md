---
mode: agent
description: Scaffold a new MOS test module
---

# Scaffold a new MOS test module

Create a new test module named `${input:name:Module name, e.g. SOA}` that mirrors the
structure and conventions of the **currently open project** in this workspace.

## Step 1 — Discover a reference module (do NOT assume a fixed module exists)

Different test programs ship different modules, so never hard-code `IGSS` or any specific
module — other projects may not have it. Inspect the active workspace first:

1. Find the test-modules root for this project (a folder containing one subfolder per
   module, e.g. `TestModules/`). Use file search if the layout differs.
2. List the existing module subfolders and pick a **reference module** to copy from:
   - Prefer the module the user names if they mention one.
   - Otherwise pick a representative module that derives from `TestModulesCommon` and has
     a matching unit test.
3. Read the reference module's `.h` and `.cpp`, the shared constants header (e.g.
   `TestModulesConstant.h`), and one existing unit test under the unit-test folder (e.g.
   `UnitTestsTestModules/`) so the new module matches THIS codebase's conventions.
4. State which reference module and paths you chose before generating any code.

The `SWA-style.instructions.md` rules apply to every file you create.

## Step 2 — Files to generate

Use the same roots you discovered in Step 1:

1. `<TestModulesRoot>/${input:name}/${input:name}.h`
2. `<TestModulesRoot>/${input:name}/${input:name}.cpp`
3. `<UnitTestRoot>/${input:name}UnitTest.cpp`

If a module with this name already exists, STOP and ask for a different name instead of
overwriting it.

## Required structure (mirror the reference module)

- Keep the banner header comment block (File / Description / Created on / Original author).
- Derive from `TestModulesCommon` and replicate the full constructor signature used by the
  reference module (typically `ITestInputVariable*`, `ITestOutput*`, `IETS*`,
  `IInstrumentMap*`, `ITerCBit*`, `ITerDatalog*`, `ITerTimer*`, `ITestEmulation*`,
  `bool bdualChip`, `bool bNewHibA`, `string sPackageName`).
- Follow the lifecycle: constructor → `Initialize()` → `Process()` → `Finalize()`.
- Use an `enum mTestState` state machine inside `Process()`.
- Register and validate PDS variables (`mRegisterPDSVars()`, `mITestInputVariable->Validate()`,
  `mGetAllPdsVariables()`) before any measurement.

## Hardware-safety rules (non-negotiable)

- Open the safety relays first, and pair every relay open/close call so relays are restored
  to a safe state afterwards.
- Use the named range/limit constants from the shared constants header — never hard-code
  ranges, voltages, currents, or wait times.
- Wrap measurement logic in `try/catch`. On error, log via `mITestLog->LogError`,
  disconnect the instrument, shut down APU/SPU/HPU, and call `mResetRelays()`.
- Guard unit-test-only code with `#ifdef _UNITTEST`.

## Unit test

- Create a matching unit test under the unit-test folder, following the style of the
  existing unit test you read in Step 1.
- Do not change any Datalog limits.

Finish with a short summary of: the reference module you copied from, the files you created,
and a reminder to run the project's unit-test suite before committing.
