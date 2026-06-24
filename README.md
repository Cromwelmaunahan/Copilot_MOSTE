# Copilot Customization Pack (ATV MOS D TE)

Custom GitHub Copilot setup for MOS test-engineering work on ETS-88.
Author: Maunahan Cromwel Miranda (ATV MOS D TE).

This `.copilot` setup now covers all four customization areas:

- **Agent:** `Super MOS TE`
- **Skills:** relay/resource loggers, CommitDetails updater, relay-config helper, HIB circuit viewer
- **Prompts:** reusable prompt files under `.copilot\prompts`
- **MCP servers:** `frontend-data-manager-te`, `auto-eff-converter`

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
- `Create HIB circuit view`

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

How to use in chat:

1. Trigger with: `Generate a FE TE report`
2. The server shows all available basictypes from:
  `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data`
3. Select one basictype from the list.
4. The generated `.pptx` is saved to:
  `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data\Generated_PPT`

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
        "FE_DATA_ROOT": "\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data",
        "FE_OUTPUT_DIR": "\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data\\Generated_PPT"
      }
    }
  }
}
```

Important:
- Replace `$HOME` with your actual user-home path if your tool does not expand environment variables in JSON.
- Keep only one MCP markdown descriptor (inside the server folder).

### Auto-EFF-Converter

A second MCP server that drives the local **STDF Analyzer** app to convert `.ST4` files into
`.eff` files.

- **Server ID:** `auto-eff-converter`
- **Server folder:** `$HOME\.copilot\MCPservers\auto-eff-converter`
- **Entry module:** `python -m auto_eff_converter.server`

How to use in chat:

1. Trigger with: `Convert ST4 to EFF`
2. Select a basictype from the list shown (folders under
   `\\Mucsdn31\ATV_Power_Pro\MOSFET_TE\Test_program_status_tracking\Copilot_FE_data`).
3. Select the ST4 file to convert.
4. The `.eff` is saved next to the ST4 as `wafernum<N>_<base>.eff` (wafer number taken from
   the ST4 file name).

Registration example (`.vscode/mcp.json` template):

```json
{
  "servers": {
    "auto-eff-converter": {
      "type": "stdio",
      "command": "$HOME/AppData/Local/Microsoft/WindowsApps/python3.11.exe",
      "args": ["-m", "auto_eff_converter.server"],
      "cwd": "$HOME/.copilot/MCPservers/auto-eff-converter",
      "env": {
        "AEC_DATA_ROOT": "\\\\Mucsdn31\\ATV_Power_Pro\\MOSFET_TE\\Test_program_status_tracking\\Copilot_FE_data",
        "AEC_ANALYZER_PATH": "C:\\Program Files\\STDF Analyzer 3.4.1.1\\_STDFAnalyser.exe"
      }
    }
  }
}
```

> This server uses Windows UI automation (pywinauto), so it must run on the same machine as
> the STDF Analyzer with a visible interactive desktop. Window title and menu paths are
> re-calibratable via `AEC_*` environment variables.

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
