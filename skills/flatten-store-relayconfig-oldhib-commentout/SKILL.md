---
name: flatten-store-relayconfig-oldhib-commentout
description: "For a chosen .cpp file, rewrite mStoreRelayConfig() by removing switch/case scaffolding, keeping only former case 1 and mHibVersion == false logic, then comment out every remaining line in that retained block. Triggered by typing: Comment out Indexparallel relays AAAAA.cpp"
argument-hint: "AAAAA.cpp — the target .cpp file to modify (e.g. Component_Check.cpp)"
user-invocable: true
disable-model-invocation: false
---

# Flatten mStoreRelayConfig To OldHIB And Comment Out

## When To Use
Triggered when the user types:
> "Comment out Indexparallel relays AAAAA.cpp"

where `AAAAA.cpp` is the target .cpp file (e.g. `Component_Check.cpp`).

## Required Behavior
Extract the target `.cpp` filename from the trigger phrase.
- If a filename is present, locate that file in the workspace (use `file_search` if the path is not obvious) and proceed.
- If no filename is present, ask: "Which .cpp file should I modify?" and wait for the user's answer.

## Target Function
Operate on:
- `void <ClassName>::mStoreRelayConfig()`

If the function is not found, stop and report that clearly.

## Transformation Rules
Apply all rules in order:

1. Remove sector switch scaffolding:
- Remove `switch (mTestInputInfo.SectorNumber)`.
- Remove `case 1:` and `case 2:` labels.
- Remove matching case-level `break;` lines.
- Remove the old `case 2` content.

2. Keep only former case 1 content.

3. Keep only old-HIB logic (`mHibVersion == false`):
- For `if (!mHibVersion) { A } else { B }`, keep `A`, delete `B`.
- For `if (mHibVersion) { A } else { B }`, keep `B`, delete `A`.
- For `if (mHibVersion) { A }` without `else`, delete the whole statement.
- For ternary expressions with `mHibVersion`, keep only the false branch.

4. After retaining only old-HIB lines, comment out every remaining line inside `mStoreRelayConfig()` body:
- Add `//` at the beginning of each non-empty, non-brace line.
- Keep braces as-is so the function remains syntactically valid.
- Existing comments can remain comments; do not duplicate `//` unnecessarily.

## Editing Constraints
- Modify only the target .cpp file.
- Keep indentation style and surrounding formatting unchanged.
- Do not alter code outside `mStoreRelayConfig()`.

## Completion Checklist
- No `switch (mTestInputInfo.SectorNumber)` remains in `mStoreRelayConfig()`.
- No `case 1:` / `case 2:` remains in `mStoreRelayConfig()`.
- No `mHibVersion == true` path remains in that function.
- Retained old-HIB lines are commented out line-by-line.

## Final Response
After the edit succeeds, show a completion notification with this exact message:

> Action is completed and successful

Then briefly report:
- Which file was modified.
- That the function now contains only old-HIB logic and all retained lines are commented out.
