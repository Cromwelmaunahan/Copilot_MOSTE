# Copilot_MOSTE — Shared GitHub Copilot Agent & Skills (ATV MOS D TE)

Custom GitHub Copilot **agent** and **skills** for MOS test-engineering work on ETS-88.
Author: Maunahan Cromwel Miranda (ATV MOS D TE).

After installing, your GitHub Copilot in VS Code will gain:

- **Agent:** `Super MOS TE` — an ETS-88 / MOS test-program specialist (with the ETS-88
  manual bundled as its knowledge base).
- **Skills** (trigger by phrase in Copilot Chat):
  - `relay-status-logger` — "Log relay status of <file>.cpp"
  - `resource-status-logger` — "Log resource status of <file>.cpp"
  - `commitdetails-update-track-all-changes` — "Update CommitDetails"
  - `flatten-store-relayconfig-oldhib-commentout` — "Comment out Indexparallel relays <file>.cpp"

---

## What this repo contains

```
Copilot_MOSTE/
├── agents/
│   ├── super-te.agent.md            <- the Super MOS TE agent
│   └── knowledge/                   <- ETS-88 manual (used by the agent)
├── skills/
│   ├── relay-status-logger/SKILL.md
│   ├── resource-status-logger/SKILL.md
│   ├── commitdetails-update-track-all-changes/SKILL.md
│   └── flatten-store-relayconfig-oldhib-commentout/SKILL.md
├── install.ps1                      <- one-command installer (Windows)
└── README.md
```

> IMPORTANT: GitHub Copilot does **not** read this repo directly. It only reads from a
> fixed folder on your machine: `%USERPROFILE%\.copilot\`. So you must **copy** the
> `agents` and `skills` folders into your own `.copilot` folder (steps below).
> This repo is just the shareable source — installing copies it into the right place.

---

## Install (Windows) — the easy way

1. **The repo is already in** `%USERPROFILE%\.copilot\Copilot_MOSTE`:

   ```powershell
   cd "$HOME\.copilot\Copilot_MOSTE"
   ```

2. **Run the installer** (copies `agents` + `skills` into your `%USERPROFILE%\.copilot\`):

   In PowerShell (opened in the `Copilot_MOSTE` folder), run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   Or: right-click inside `C:\Users\maunahan\.copilot\Copilot_MOSTE` → "Open in Terminal" → paste the command above.

   > **Other engineers**: Clone this repo, copy the `Copilot_MOSTE` folder into your `%USERPROFILE%\.copilot\`, then run the installer command above. All agents and skills will then be available in your GitHub Copilot.

3. **Restart / reload VS Code** so Copilot re-scans.
   Open Copilot Chat → the agent dropdown should now show **Super MOS TE**, and the
   skills above are usable by their trigger phrases.

That's it.

---

## Install — the manual way (if you prefer Explorer)

Copy these two folders from the cloned repo into your user `.copilot` folder:

| Copy from (this repo) | Paste into (your machine) |
| --------------------- | ------------------------- |
| `Copilot_MOSTE\agents` | `%USERPROFILE%\.copilot\agents` |
| `Copilot_MOSTE\skills` | `%USERPROFILE%\.copilot\skills` |

Final result on your machine must look like:

```
C:\Users\<you>\.copilot\
├── agents\super-te.agent.md   (+ knowledge\)
└── skills\<skill-name>\SKILL.md
```

Then restart VS Code.

> Note: the folders MUST land directly under `.copilot\` (i.e. `.copilot\agents`,
> `.copilot\skills`). Do not nest them inside an extra subfolder, or Copilot won't find them.

---

## Updating later

To get the newest version after the author pushes changes:

```powershell
cd "$HOME\Projects\Copilot_MOSTE"
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1   # re-copies the latest
```

Then reload VS Code.

---

## Notes & safety

- The installer only adds/overwrites the **specific** agent and skill folders shipped
  here. It does **not** delete or touch any other agents/skills you created yourself.
- If you already have a skill or agent with the **same name**, installing will overwrite
  it with this repo's version. Rename yours first if you want to keep both.
- Requires: GitHub Copilot + GitHub Copilot Chat extensions in VS Code, with an active
  Copilot license.
