---
description: 'SWA style instruction — shared coding & hardware-safety rules for ETS88 MOSFET TestModules.'
applyTo: 'TestModules/**/*.cpp,TestModules/**/*.h,UnitTestsTestModules/**/*.cpp'
---

# SWA Style Instruction

Persistent rules every Test Engineer (and Copilot) must follow when editing this ETS88
MOSFET test software. Goal: one consistent style, hardware kept safe by default, fewer
review cycles, and zero tribal knowledge for new joiners.

## 1. Consistent coding style across all TEs

- Mirror the existing module style. Use [TestModules/IGSS/IGSS.cpp](../../TestModules/IGSS/IGSS.cpp),
  [TestModules/BVDSS/BVDSS.cpp](../../TestModules/BVDSS/BVDSS.cpp) and
  [TestModules/GST/GST.cpp](../../TestModules/GST/GST.cpp) as the reference templates.
- Start every `.cpp` with the standard banner block (`File:`, `Description:`, `Created on:`,
  `Original author:`). Keep the existing format — do not invent a new header layout.
- Member variables use the `m` prefix; booleans use `mb` (e.g. `mbDualChip`, `mbNewHib`);
  doubles use `md`, integers `mi`, strings `ms`. Global doubles use the `gd` prefix.
- Keep the module lifecycle structure: constructor → `Initialize()` → `Process()` →
  `Finalize()`. Drive `Process()` with the existing `enum mTestState { ... }` state machine.
- Document public methods with the existing Doxygen `/** @brief ... */` style.
- Use `using namespace TestModules;` and the established interface members
  (`mITestLog`, `mITerDatalog`, `mIETS`, `mICBit`, `mITestInputVariable`, `mIInstrumentMap`).

## 2. Encode hardware safety directly into behavior

These rules are NON-NEGOTIABLE — they protect the HIB, APU/SPU/HPU and the DUT.

- Open safety / function relays BEFORE energizing and AFTER measuring. Follow the
  `mSetRelays("", relays)` (close) / `mSetRelays(relays, "")` (open) pairing seen in
  [TestModules/BVDSS/BVDSS.cpp](../../TestModules/BVDSS/BVDSS.cpp). Never leave a relay
  closed on an error path.
- Every `Process()` / `Finalize()` must wrap work in `try/catch (exception& ex)` and, on
  failure, log via `mITestLog->LogError(TestModulesComponent, ex.what())`, shut down
  instruments (`mAPUDisconnect()`, `mSPUDisconnect()`, `mDeactivateSPU()` / HPU off as
  applicable), call `mResetRelays()` (or the module's `mSetHwUsedBackToSafeState()`), then
  re-throw `TestModulesException`.
- Disable alarms only around the measurement that requires it and ALWAYS re-enable with
  `mIETS->alarmset(ALARM_ALL, TestModulesUtility::AlarmState)` before returning
  (see BVDSS Kelvin-alarm handling).
- Respect HIB voltage/sector limits — validate forcing conditions before applying them
  (see `mSelectMode()` / `mValidateLimits()` in BVDSS). Never force a voltage the sector
  does not support.
- Use named constants from [TestModules/TestModulesConstant.h](../../TestModules/TestModulesConstant.h)
  for all timings, voltages, currents and counts. NEVER hardcode magic numbers for HW
  forcing values or wait times.

## 3. Less back-and-forth in code review

- Validate inputs at the boundary: register and `Validate()` PDS variables, and
  `Validate()` the instrument map in the constructor before use.
- Remove dead/abandoned code (old relay/instrument lines that no longer run). This rule is
  about deleting unused logic — it does NOT mean removing the explanatory comments required
  in section 5.
- Keep relay name strings in named variables/constants, never inline raw `"Kxxx"` literals
  scattered through logic.
- After ANY edit to a module, re-run its matching test in
  [UnitTestsTestModules/](../../UnitTestsTestModules/) and confirm it passes before committing.
- Do not change Datalog limit logic (`mITerDatalog->TestLimits(...)`, bins, limits) without
  an explicit TE sign-off.

## 4. New joiners follow the rules immediately

- When adding a new test module, copy the structure of an existing one rather than starting
  blank — constructor registry pattern, state-machine `Process()`, and safe-state error path.
- Software bins come from the named bin vectors in
  [TestModules/TestModulesConstant.h](../../TestModules/TestModulesConstant.h)
  (e.g. `IgssBin`, `BvdssBin`, `RDSonBin`) — never type bin numbers by hand.
- Guard unit-test-only code with `#ifdef _UNITTEST` / `#if _UNITTEST`, matching the
  existing modules.
- If a rule here conflicts with what you are about to write, STOP and ask a TE — do not
  silently work around hardware-safety rules.

## 5. Explain routines with inline comments so anyone can follow the flow

The goal is that a new TE (or a reviewer) can read the code top-to-bottom and understand
WHAT each routine does and WHY — without asking the original author.

- Above every method body, add a short comment line explaining the routine's purpose in plain
  language, e.g. `// Open the function relays and select the measurement path for this test.`
- Inside `Process()`, comment each state of the `enum mTestState` machine so the test flow
  reads like a checklist:
  ```cpp
  switch (currentState)
  {
  case InitState:
      // Open safety relays first, then close the relays this test needs.
      mActivationRelays(msRelayIGSS, "");
      currentState = mTestState::TestState;
      break;
  case TestState:
      // Force the gate voltage and capture the leakage current measurement.
      mTestIGSS();
      currentState = mTestState::End;
  case End:
      // Test finished — fall through and return to a safe state.
      break;
  }
  ```
- Comment every hardware-relevant step (relay switching, instrument connect/disconnect,
  forcing values, alarm enable/disable) with a one-line note on what it does to the HW.
- Explain WHY, not just WHAT, when a line is non-obvious (e.g. why a settle time is needed,
  why an alarm is disabled, why a sector/HIB branch exists).
- Keep comments short, accurate, and updated when the code changes — a stale comment is worse
  than none. These explanatory comments are REQUIRED and are different from the dead-code in
  section 3 (which must be deleted).
