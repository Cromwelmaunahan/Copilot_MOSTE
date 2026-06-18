# Copilot Customization Pack (ATV MOS D TE)

Custom GitHub Copilot setup for MOS test-engineering work on ETS-88.
Author: Maunahan Cromwel Miranda (ATV MOS D TE).

This `.copilot` setup now covers all four customization areas:

- **Agent:** `Super MOS TE`
- **Skills:** relay/resource loggers, CommitDetails updater, relay-config helper
- **Prompts:** reusable prompt files under `.copilot\prompts`
- **MCP server:** `frontend-data-manager-te`

For sharing with other engineers, treat paths as user-relative:

- Your local path example: `C:\Users\maunahan\.copilot`
- Any engineer path pattern: `C:\Users\<their-username>\.copilot`
- Equivalent PowerShell form (recommended in docs/commands): `$HOME\.copilot`

`$HOME` automatically points to the current Windows user profile, so each engineer can run the same commands without editing usernames.

---

## Folder layout (single source)

Use this as the canonical structure:

```
$HOME\.copilot\
├── agents\
├── skills\
├── prompts\
├── MCPservers\
│   └── frontend-data-manager-te\
│       └── Frontend_Data_Manager_for_TE.md
├── instructions\
└── README.md
```

Notes:
- Do not use `$HOME\.copilot\Copilot_MOSTE` anymore.
- Keep customization files directly under `$HOME\.copilot\...`.

---

## Quick start

1. Open PowerShell in your `.copilot` folder:

   ```powershell
   cd "$HOME\.copilot"
   ```

2. Verify your key folders exist:

   ```powershell
   Get-ChildItem "$HOME\.copilot"
   ```

3. **MCP server — extra step required:**
   The MCP server is NOT auto-discovered from `.copilot`. You must register it manually
   in the `.vscode\mcp.json` file inside each workspace where you want to use it.
   See the [MCP server](#mcp-server) section below for the registration block.
   Replace `<your-username>` with your Windows login name (run `$env:USERNAME` to check).

4. Reload VS Code so Copilot re-scans customizations.
   - Agent, Skills, Prompts, and MCP server will all be available after reload.

---

## Agent and Skills

Agent:
- `Super MOS TE` — ETS-88 / MOS test-program specialist.

Skill trigger examples:
- `Log relay status of <file>.cpp`
- `Log resource status of <file>.cpp`
- `Update CommitDetails`
- `Comment out Indexparallel relays <file>.cpp`

---

## Prompts

Prompt files are supported and should follow a single-source rule.

- **Canonical prompts folder:** `$HOME\.copilot\prompts`

Recommended practice:
- Keep master prompt files in `$HOME\.copilot\prompts`.
- Keep a single source only in this folder to avoid duplicate prompt versions.

---

## MCP server

This setup includes an MCP server under `.copilot`:

- **Server ID:** `frontend-data-manager-te`
- **Server folder:** `$HOME\.copilot\MCPservers\frontend-data-manager-te`
- **Server docs (single source):** `$HOME\.copilot\MCPservers\frontend-data-manager-te\Frontend_Data_Manager_for_TE.md`
- **Entry module:** `python -m fe_data_manager.server`

Registration example (`.vscode/mcp.json` template):

```json
{
  "servers": {
    "frontend-data-manager-te": {
      "type": "stdio",
      "command": "$HOME/AppData/Local/Microsoft/WindowsApps/python3.11.exe",
      "args": ["-m", "fe_data_manager.server"],
      "cwd": "$HOME/.copilot/MCPservers/frontend-data-manager-te",
      "env": {
        "FE_DATA_ROOT": "\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data"
      }
    }
  }
}
```

Important:
- Replace `$HOME` with your actual user-home path if your tool does not expand environment variables in JSON.
- Keep only one MCP markdown descriptor (inside the server folder).

---

## Updating later

If your `.copilot` folder is managed with Git:

```powershell
cd "$HOME\.copilot"
git pull
```

Then reload VS Code.

---

## Notes & safety

- This setup is for **Agent + Skills + Prompts + MCP server** customizations.
- Keep paths generic with `$HOME` in docs/examples for reuse by other engineers.
- Requires GitHub Copilot + GitHub Copilot Chat extensions in VS Code, with an active Copilot license.
