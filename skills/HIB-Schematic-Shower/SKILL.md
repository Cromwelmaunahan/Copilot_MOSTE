---
name: HIB-Schematic-Shower
description: 'Upgrade the ETS88 HIB Index Parallel Maintenance Guide HTML with a top-level tab bar (Data View + 4 schematic tabs), an inline standalone PDF viewer per setup, and a new "Involve Circuitry" section that lists the schematic pages affected by the selected Sector/HIB/Test-Label. Triggered by typing: execute HIB-Schematic-Shower to "<test label name>".'
argument-hint: 'the test label, e.g. execute HIB-Schematic-Shower to "Resis R32"'
---

# HIB Schematic Shower

## When to Use

Triggered when the user chats (the quoted text is the **test label**):

> `execute HIB-Schematic-Shower to "<test label name>"`

Example: `execute HIB-Schematic-Shower to "Resis R32"`.

This skill edits the maintenance-guide HTML so that:

1. The page gains a **top-level tab bar**: `Data View` + 4 schematic tabs.
2. Each schematic tab shows that setup's PDF **inline (standalone, relative path)**.
3. A new **Involve Circuitry** section (placed **after Relay Status, before Additional
   Notes**) shows the schematic reference link and a **simple list of affected pages**
   (sheet label + page title) for the selected Sector / HIB / Test-Label.

The skill is **idempotent**: the tab scaffold, the 4 schematic tabs, and the Involve
Circuitry shell are created **once**; re-running for a new test label only adds/updates
that label's affected-pages data.

---

## Target File

```
C:\Users\maunahan\Projects\SOFTWARES\GIT_Modified_codes\gitlab\dibchecker_indexparallel_swa\TestMethodology\ETS88-HIB-Index-Parallel-Maintenance-Guide.html
```

### How the target HTML is structured (read it first)

- All TXT data is embedded as a JavaScript `var files = [ ... ]` array (one long line).
  Each file entry has `name`, `header[]`, `notes`, and `blocks[]`. Each block has
  `section`, `title`, `columns[]`, `rows[]` (array of arrays).
  Relevant sections: `"Resource Status and Condition"` and `"Relay Status"`.
  Sector tables are titled `"SECTORA TABLE"` / `"SECTORB TABLE"`.
  HIB columns are named `OldHIB-A` / `NewHIB-A` / `OldHIB-B` / `NewHIB-B`.
- Three dropdown filters drive the page: `#sectorSelect`, `#hibSelect`, `#fileSelect`.
- Existing render pipeline (reuse — do not rewrite): `renderSelectedFile(fileName)`,
  `groupBySection(blocks)`, `renderBlock(block)`, `getVisibleIndexes(columns)`,
  `findFileByName(name)`, `renderCell()`, `escapeHtml()`, `strIncludes()`.
- Existing content sections (in order): **File Header Info** -> dynamic blocks rendered
  into `<div id="blocksContainer">` (Resource Status then Relay Status) -> **Additional
  Notes** (`#notesBox`). No tabs, no schematic code, and no PDF references exist yet.
- The CSS block is near the top of the file. Reuse these theme classes/colors:
  `.panel`, `.header`, `.section-title`, `.table-wrap`, `.table-block-title`, `.badge`,
  `.notes-box`, `.controls`, `.empty`, `.footer`; primary blue `#0a66c2` / `#1e88e5`,
  light blue `#eaf3ff` / `#f0f7ff`, teal `#0a9396`, orange `#c46a00`.

> Always read the file before editing and detect what already exists (tab bar, schematic
> tabs, Involve Circuitry, `SCHEMATIC_REFS`, `INVOLVE_PAGES`, `switchTab()`,
> `renderInvolve()`) so the build steps stay idempotent.

---

## Reference data (relay & resource status)

The authoritative TXT source for each test label's resource/relay status lives in:

```
C:\Users\maunahan\Projects\SOFTWARES\ETS88-HIB-Index-Parallel-Maintenance-Guide\TestMethod_txtfiles
```

These TXT files mirror the data already embedded in the HTML `files[]` array. Prefer the
embedded HTML data for parsing (it is structured); use the TXT files to cross-check.

---

## Schematic Reference Mapping (repo-relative paths)

| Sector | HIB    | Schematic PDF (repo-relative) |
|--------|--------|-------------------------------|
| A      | NewHIB | `dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf` |
| B      | NewHIB | `dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf` |
| A      | OldHIB | `dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\658-458-01_Schematic_2019Apr12_HIBA.pdf` |
| B      | OldHIB | `dibchecker_indexparallel_swa\Schematics\HIBB\SCHEM\658-459-01_Schematic_2019Apr11_HIB_B.pdf` |

Store these in the HTML as a JS map `SCHEMATIC_REFS` keyed `"SECTOR|HIB"` (e.g.
`"A|NEWHIB"`). The 4 tabs are exactly these 4 combos (NewHIB A & B share one PDF).

The exact reference strings shown in the Involve Circuitry section (item 8 wording):

```
Schematic reference (NewHIB Sector A):
dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf
Schematic reference (NewHIB Sector B):
dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf
Schematic reference (OldHIB Sector A):
dibchecker_indexparallel_swa\Schematics\HIBA\SCHEM\658-458-01_Schematic_2019Apr12_HIBA.pdf
Schematic reference (OldHIB Sector B):
dibchecker_indexparallel_swa\Schematics\HIBB\SCHEM\658-459-01_Schematic_2019Apr11_HIB_B.pdf
```

---

## Allowed PDF page-search ranges (printed sheet labels — NOT physical page index)

Each PDF prints a sheet label in the **lower-right corner** like `SHEET 15 of 29`. The
ranges below are those **printed `X of Y` sheet numbers**. The physical PDF page count can
differ from `Y` (e.g. `HIB AB VER 3.20` has ~38 physical pages but prints `... of 24`), so
**match by the printed sheet label, never by the physical page index.**

| PDF | Search ONLY these printed sheets |
|-----|----------------------------------|
| `HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf` | `4 of 24` … `13 of 24`  AND  `18 of 24` … `23 of 24` |
| `658-458-01_Schematic_2019Apr12_HIBA.pdf`       | `5 of 29` … `20 of 29` |
| `658-459-01_Schematic_2019Apr11_HIB_B.pdf`      | `5 of 22` … `13 of 22` |

Pages whose printed sheet number falls **outside** these ranges must be ignored.

> **Report every matching page.** If an affected relay or resource appears on more than
> one page within the allowed ranges, list **all** of those pages (each with its sheet
> label + page title) — do not stop at the first match.

---

## Procedure

### Step 0 — Parse & validate the test label
- Extract the quoted `<test label name>` from the trigger phrase.
- Validate it against the `<option>` values in the HTML `#fileSelect` (accept with or
  without the `.txt` extension; match case-insensitively).
- If it is not a valid label, **ask the user again** (optionally list close matches). Do
  not proceed until a valid label is given.

### Step 1 — Read the target HTML and detect existing scaffold
Read the file. Determine whether each of these already exists so you only add what is
missing: the tab bar, the 4 schematic tab panels, `SCHEMATIC_REFS`, the Involve Circuitry
section, `INVOLVE_PAGES`, `switchTab()`, `renderInvolve()`.

### Step 2 — Build the tab scaffold (only if missing)
- Wrap the existing data UI (the `.controls` dropdowns + `#blocksContainer` +
  Additional Notes `#notesBox`) inside a **Data View** tab panel
  (`<div id="tab-dataview" class="tab-panel">`).
- Insert a **top-level tab bar** above the panels with 5 buttons, in order:
  `Data View`, `Sector A NewHIB`, `Sector A OldHIB`, `Sector B NewHIB`, `Sector B OldHIB`.
- Add a `switchTab(id)` JS function that toggles `.active` on the buttons and shows the
  matching `.tab-panel` (hide the others). Default active = `Data View`.
- Add CSS for `.tab-bar`, `.tab-btn`, `.tab-btn.active`, `.tab-panel`,
  `.tab-panel.active` reusing the existing blue/teal theme (active tab = `#0a66c2`
  background / white text; inactive = light blue).

### Step 3 — Build the 4 schematic tabs (only if missing) — standalone via embedded PDFs
For each of the 4 setups, create a `.tab-panel` whose body shows the mapped PDF:
- An inline **`<iframe>`** (or `<embed>`) carrying a `data-pdf="NEWHIB|OLDHIB_A|OLDHIB_B"`
  attribute and a **relative-path `src`** as a graceful fallback (the HTML is in
  `TestMethodology\`, so the relative path is `..\Schematics\...`). Give it a tall height
  (e.g. `height:80vh; width:100%`). At load `initPdfBlobs()` overwrites `src` with the
  embedded blob URL (see Step 7b).
- A visible **"Open PDF in new tab"** anchor (`<a class="schem-open" data-pdf="…"
  target="_blank" rel="noopener">`) with the same relative-path fallback href, plus the
  full repo-relative path shown as text.
- No external JS/CSS libraries and no CDN. The HTML stays **fully standalone**: the PDFs
  are **embedded as base64** (Step 7b) and rendered via in-memory **blob URLs**, so the
  tabs work on any machine, offline, even when only the HTML file is copied.

> NewHIB Sector A and NewHIB Sector B both point to
> `..\Schematics\HIBA\SCHEM\HIB AB VER 3.20 (FULL RELEASED DOC V1.05).pdf`
> (`data-pdf="NEWHIB"` — embedded once, shared by both tabs).

### Step 4 — Build the Involve Circuitry section (only if missing)
Insert a new section **inside the Data View panel, after the Relay Status blocks
(`#blocksContainer`) and before Additional Notes (`#notesBox`)**:
- `<h2 class="section-title">Involve Circuitry</h2>` (reuse the existing section styling).
- A container `<div id="involveContainer">` rendered by `renderInvolve()`.
- `renderInvolve()` reads the current `#sectorSelect` / `#hibSelect` / `#fileSelect`
  values and shows, per visible (Sector, HIB) combo:
  1. The **schematic reference** line + path from `SCHEMATIC_REFS` (item 8 wording).
  2. A **simple list of affected pages** from `INVOLVE_PAGES` for `"label|SECTOR|HIB"`:
     each item = printed **sheet label** (e.g. `SHEET 15 of 29`) **and** the **page
     title** (big-font heading), de-duplicated and **sorted by sheet number**, grouped by
     whether the match came from a relay or a resource.
     - Each item also shows a clickable **"Open sheet"** link that opens the mapped PDF
       **in a new tab jumped to that exact page** via the URL fragment
       `ref.href + "#page=" + pg.page`, where `pg.page` is the **physical** PDF page index
       (see Step 6/7). Render it as
       `<a class="ic-open" href="<href>#page=<page>" target="_blank" rel="noopener">`.
       Only emit the link when `pg.page` is present.
  3. If a combo is not tested (`N/A` / "not tested") or has no indexed pages yet, show a
     clear placeholder (e.g. "Run `execute HIB-Schematic-Shower to \"<label>\"` to index
     this combo.").
- Hook `renderInvolve()` into the existing change handlers so it re-renders whenever the
  sector / HIB / file dropdowns change (call it from the same place `renderSelectedFile`
  is triggered, and once on initial load).

### Step 5 — Resolve the affected resources & relays for the test label
For each concrete `(sector, hib)` combo that the selected label is tested on (skip combos
whose Resource/Relay rows say `N/A` or "not tested"):
- **Resources:** in the `"Resource Status and Condition"` block for that sector, read the
  HIB column (`OLDHIB` -> `OldHIB-*`, `NEWHIB` -> `NewHIB-*`). For each non-skipped row,
  take the text **before the first `:`** -> instrument + channel (e.g. `APU12 CH0`).
  Collect the unique set. Map channels to schematic pin/net tokens using the file's
  "Pin Map Consideration" notes when present (e.g. `RS1_APU12_1 = APU12 channel 0`).
- **Relays:** in the `"Relay Status"` block for that sector, read the same HIB column,
  split each non-skipped cell on commas, trim, and build the ordered **union** of relay
  designators (e.g. `K100, K044, KA4, KA21, ...`).

### Step 6 — Search the PDF for those tokens (within the allowed sheet ranges)
There is **no native PDF reader**. Install PyMuPDF first:
`python -m pip install pymupdf` (import as `fitz`). Vision may be unavailable, so work from
**text + coordinates**, never from a rendered image.

For the PDF mapped to the combo:
1. `doc = fitz.open(pdf)`. For every physical page, get `page.get_text("words")`
   -> tuples `(x0, y0, x1, y1, word, block, line, wordno)`.
2. **Printed sheet label:** find the `SHEET <n> of <total>` text near the **lower-right**
   corner (largest `y`, large `x`). Capture `<n>` (the printed sheet number). Skip the
   page if `<n>` is outside the allowed ranges for that PDF.
3. **Page title:** find the **big-font** heading at the **top** of the page (smallest `y`,
   usually top-left or top-center). Use `page.get_text("dict")` and pick the span(s) with
   the **largest font size** in the top band of the page; join them into the title string.
4. **Token match:** a page is "affected" if it contains any of the combo's relay
   designators (whole-word match, e.g. `KA4` must not match `KA44`) or its resource
   instrument tokens (e.g. `APU12`, and the channel/pin token when derivable).
5. Record each match as `{ sheet: "SHEET <n> of <total>", title: "<page title>",
   via: "relay"|"resource", token: "<matched token>" }`.
   - Also capture the **physical PDF page index** (`pno + 1`, 1-based) as `page`. This is
     what the **"Open sheet"** link targets with `#page=<page>`. For OLDHIB the physical
     page equals the printed sheet; for NEWHIB they coincide only for the in-range sheets
     (≤ 24) — always use the **physical** index for the link, never the printed sheet.

> Reuse the helper scripts in `C:\Users\maunahan\Projects\SOFTWARES\_pdf_tools\` if
> present (e.g. `scan_r32.py` is a working scanner — copy and change the `COMBOS` tokens
> for a new test label). Known page hints (OldHIB-A `658-458-01`): p7 = `DUT_A`
> (K001-K009, R32-R36), p13 = `I2V_PGA_A` (K020, K021). Verify against the live text;
> do not hard-code.

#### Verified extraction recipe (learned — both PDF families differ)
- **Tokens are not adjacent** in `get_text("words")` reading order across schematic
  columns. Group words into lines by `round(y/3)`, sort each line by `x`, then run regex
  per line.
- **Whole-word match:** `(?<![A-Z0-9_])TOKEN(?![A-Z0-9])` so `KA4` does not match `KA44`
  or `RKA4`.
- **Relay pole/contact suffix — drop the last letter.** On the DUT / circuit pages a relay
  is drawn with a trailing **pole/contact letter** (e.g. sheet 4 shows `KA12B`, `KA10B`),
  while the bare coil name only appears on the relay-coil sheets. Treat a token that is the
  base relay name **plus one optional trailing uppercase letter** as the **same** relay:
  `KA4B` = `KA4C` = `KA4`. Match every base relay `R` with
  `(?<![A-Z0-9_])R(?:[A-Z])?(?![A-Z0-9])` — this matches `R` and `R<letter>` but **not**
  `R<digit>` (so `KA4` still excludes `KA40`, and `K012` excludes `K0123`). When reporting,
  **collapse the suffix back to the base relay name** (report `KA4`, not `KA4B`). **Apply
  this only to relays** — resource pins (`APU12_FH1`, etc.) must still match exactly.
- **Resource match must use the specific channel pins** (e.g. `APU12 CH1` ->
  `APU12_FH1 / SH1 / FL1 / SL1`). The bare instrument token (`APU12`) appears on nearly
  every DUT page and is too broad.
- **NEWHIB `HIB AB VER 3.20`** (page `rotation == 0`): sheet label = per-line regex
  `Sheet\s+(\d+)\s+of\s+(\d+)`; page title = `File Name\s+\d+\s*-\s*(.+?)\.SchDoc`
  (fallback `Sheet Title\s+(.+?)\s+Release Date`). It has ~38 physical pages but prints
  `... of 24`; for the in-range sheets the physical page equals the printed sheet.
  Allowed sheets: `4`-`13` and `18`-`23` (of 24).
- **OLDHIB `658-458-01` / `658-459-01`** (page `rotation == 90`, **rotated title block** on
  the right edge): find the word `SHEET` (x ~821); the sheet number is the numeric word at
  the **same x (±10)** just **above** it (smaller y); the total is the next number above
  that. **Dedupe overlapping duplicate words** first. Printed sheet equals the physical
  page (`of 29` / `of 22`). Page title = the **largest-font span** (`dir == (0,-1)`) at the
  **smallest x** (the displayed top) in the drawing body, e.g. `DUT_A`, `I2V_PGA_A`,
  `GATE_DRIVER`.

#### Relay-token normalisation (learned from processing all 39 labels)
The TXT relay cells contain tokens that are **not** literal schematic net names. Normalise
before matching:

- **Grouped underscore tokens — split into separate relays.** A single cell token may pack
  several relays joined by `_`. Expand them:
  - `KL160_KL260_KL360_KL460` -> `KL160, KL260, KL360, KL460` (each part already a full
    `K…` name).
  - `K52_K56` -> `K52, K56`.
  - `K352_356` -> `K352, K356` — a **bare-digit** trailing part **inherits the `K` prefix**
    of the first part.
  - `KA23_B23` -> `KA23, KB23` and `KA28_A29` -> `KA28, KA29` — a `letter+digit` trailing
    part gets **`K` prepended**.
  - Split on **whitespace** too, to survive typos like `K100 K152_K156`.
  - **Do not split** a token whose first part is **not** a `K`-relay (e.g. `Lim_SF_1A`,
    `HPU_KELVIN`) — keep it whole (and such non-relay tokens are pseudo-tokens, see below).
- **Trailing net-suffix — strip it.** `K101GD` = `K101` (the `GD` is a net/grid suffix).
  Add the stripped variant: `re.fullmatch(r"(K[A-Z]*\d+)[A-Z]+", token)`.
- **Trailing pole/contact suffix can be TWO letters (force/sense + pole).** On NEWHIB the
  circuit pages draw a relay with a **force/sense letter (`F`/`S`) then a pole letter**, e.g.
  `KA33` is drawn `KA33FB` / `KA33SB` (sheet 11) and `KB33` -> `KB33FB` / `KB33SB`
  (sheet 12). OLDHIB uses a single pole letter (`K33B` / `K33C`, `K133B` / `K133C`). Match
  the relay allowing an **optional force/sense + optional pole** suffix:
  `(?<![A-Z0-9_])VARIANT(?:[FS]?[A-Z]?)(?![A-Z0-9])`. This catches `KA33FB`/`KA33SB` and
  the single-letter poles, but **not** `KA40` (digit) nor `KA33GF` (first of two letters
  must be `F`/`S`).
- **Non-derivable renames — use an explicit `ALIASES` map.** Some TXT relays are simply
  named differently on the schematic with no strip/zero rule: `KY64` is drawn `KIY64` /
  `KIY64B` (NEWHIB sheet 7). Keep a small `ALIASES = {"KY64": ["KIY64"]}` dict and add its
  values to the variant list. **Get these from the user — do not guess.**
- **Leading-zero padding — 3-digit `K0DD` = 2-digit `KDD`.** `K064` = `K64`, `K067` = `K67`
  (the gate-driver relays are drawn 2-digit on sheet 18). Add variant via
  `re.fullmatch(r"(K[A-Z]*)0(\d\d)", base)`. **Keep this tight** (only `K0DD`→`KDD`); a
  generic `0+` strip wrongly turns `K004`→`K4`.
- When matching a normalised relay, still allow the **optional trailing pole/contact
  letter** from the rule above: `(?<![A-Z0-9_])VARIANT(?:[A-Z])?(?![A-Z0-9])`.
- **Pseudo-tokens — ignore (never schematic relays).** Skip and report as "not a relay":
  `(none)`, `N/A`, `SAME AS …`, `L=…uH`, `<setupInductor_uH(10)>`, `HPU_KELVIN`,
  `HPU_openFS`, `PGA_A0_Pat_AB`, `PGA_A1_Pat_AB`, and any `Lim_*` limiter descriptor.
- **TIB relays — exclude (not on the HIB schematic).** `KL_01` / `KL_10` / `KL_20` /
  `KL_30` (pattern `KL_\d+`) live on the **TIB, not the HIB**, so they are **not** in any
  HIB PDF. Drop them in `build_config.py` (never searched, never a not-found). If asked,
  tell the user those relays are on the TIB.
- **Genuinely-unresolved relays — never guess; ask the user.** When a TXT relay has no
  confident schematic match, leave it in a `not_found` list and **ask the user to confirm**.
  (Resolved this way: `KA33`=`KA33FB/SB` sheet 11, `KB33`=`KB33FB/SB` sheet 12,
  `KY64`=`KIY64` sheet 7, all on NEWHIB; OLDHIB `K33`/`K133` on sheets 13/14 (HIBA) and
  9/10 (HIBB).) Schematic naming is inconsistent (some families 3-digit zero-padded, gate
  relays 2-digit), so **follow the PDF text, not the TXT**, and confirm anything unclear.

#### Resource-token mapping (learned)
- Only **APU12** is fully mapped: `APU12 CHn` -> `APU12_FHn / SHn / FLn / SLn`. On a
  high-side measurement page the low-side pins (`FLn`/`SLn`) are often **not drawn** — those
  not-founds are **expected**, not errors.
- **SPU / HPU** instruments (`SPU112`, `SPU500`, `HPU…`) are **not yet mapped** to schematic
  pin names; for those labels only the relays are matched. If a label needs SPU/HPU pins,
  first discover their schematic net naming in the PDF before claiming a page.


### Step 7 — Bake the results into the HTML
- Add/update a JS object `INVOLVE_PAGES` keyed `"<label>|<SECTOR>|<HIB>"` (e.g.
  `"Resis R32|A|OLDHIB"`). The value is the de-duplicated, sheet-sorted list of
  `{ sheet, page, title, via, tokens[] }` produced in Step 6, where `page` is the
  **physical** PDF page index used by the `#page=<page>` "Open sheet" link.
- Only touch the entries for the test label being processed; leave other labels intact.
- Ensure `SCHEMATIC_REFS` and the Involve Circuitry shell exist (from Steps 2-4).

### Step 8 — Validate
Run `get_errors` on the HTML — there must be no errors. Confirm: the tab bar switches
panels; each schematic tab loads its **embedded** PDF (blob URL); the Involve Circuitry
section renders the reference link + affected-page list for the selected combo and its
"Open sheet" deep-links jump to the right page; and the original Data View tables/notes
still render. **Acid test for standalone:** copy ONLY the HTML to a folder with no repo
(or another machine) — the tabs and links must still work.

### Step 9 — Notify success or failure
- **Success:** state the file path, the test label processed, the combos indexed, and for
  each combo the affected pages found (sheet label + title).
- **Failure:** state that it did not finish, name the blocker (invalid label, label not
  tested on a sector, missing block, PyMuPDF not installed, PDF not found, or a
  parse/validation error), and what is needed to proceed.

---

## Bulk mode — index ALL test labels at once

Triggered when the user asks to run the skill for **all** available labels (e.g.
`execute HIB-Schematic-Shower to "(all available test labels)"`). Do **not** hand-parse 39
files — use the **automated, config-driven pipeline** under
`C:\Users\maunahan\Projects\SOFTWARES\_pdf_tools\` (create the scripts there if missing):

1. **`build_config.py`** — parses every TXT in `…\TestMethod_txtfiles\`, extracts the
   SECTORA/SECTORB Resource + Relay tables per HIB column, applies the relay normalisation
   and resource mapping above, resolves `same as OldHIB/NewHIB` cross-references, and writes
   `cfg_all.json` (combos with `relays[]` + `respins[]` per `"label|SECTOR|HIB"`). It also
   keeps a `_resource_raw` field for unmapped SPU/HPU descriptors.
2. **`scan_label.py`** — generic scanner. Holds the `PDFS` map (path + allowed sheet
   ranges), `expand_relays()` (grouped-underscore splitting), `relay_variants()`
   (net-suffix + leading-zero variants), `present_relay()` (variant loop with optional
   trailing pole letter) and `present()` (exact whole-word for resource pins). Accepts a
   single config or `{"labels":[…]}` batch; records matches + `not_found_relays` /
   `not_found_respins` per combo.
3. **`bake.py`** — loads `cfg_all.json`, scans all combos, and emits
   `involve_pages.js` (a complete `var INVOLVE_PAGES = { … };` block, each entry
   `{ sheet, page, title, relays:[], resources:[] }`) plus a `not_found.txt` diagnostic.
4. **`splice_html.py`** — regex-replaces the existing `var INVOLVE_PAGES = { … };` block in
   the target HTML with the freshly baked one (pattern
   `^[ \t]*var INVOLVE_PAGES = \{.*?^[ \t]*\};` with `re.S | re.M`). Leaves everything else
   untouched.

**Run order:** `python build_config.py` -> `python bake.py` -> `python splice_html.py` ->
`python embed_pdfs.py` -> `get_errors` on the HTML. Then review `not_found.txt`: the only
entries left should be the **pseudo-tokens** (ignored) and the **genuinely-unresolved
relays** (report to the user). Validate a few combos manually against the TXT (e.g.
R32/R33/R34) before trusting the batch.

5. **`embed_pdfs.py`** — makes the report truly **standalone**. Base64-encodes the 3
   schematic PDFs and injects a single `<script id="pdf-embed-data">var PDF_DATA =
   {"NEWHIB":…,"OLDHIB_A":…,"OLDHIB_B":…};</script>` right before the main app `<script>`.
   Idempotent (regex-removes any prior block first). **Run LAST** (after `splice_html.py`,
   which only rewrites `INVOLVE_PAGES`). Result ≈ 18.5 MB HTML. At load, `initPdfBlobs()`
   in the HTML decodes each base64 → `Uint8Array` → `Blob('application/pdf')` →
   `URL.createObjectURL()` and assigns the resulting **blob URL** to the 4 tab iframes,
   the `.schem-open` links, and `SCHEMATIC_REFS[*].href` (so the Involve "Open sheet"
   `href + "#page=" + pg.page` links also use the embedded PDF). Use **blob URLs, never
   `data:` URIs** — Chrome blocks `data:` PDFs for new-tab navigation and breaks `#page=N`;
   blob URLs work in an iframe, in a new tab, AND with `#page`.

### Manual page overrides (special items the scan can't derive)
Some combos must show a schematic page that is **not** reachable from any relay/resource
token (e.g. `HWID` Sector A & B NewHIB must always show `HIB AB VER 3.20` **sheet 20**
"EEPROM,1W,DebugPort"). Add these to the `OVERRIDES` dict in `bake.py`, keyed
`"<label>|<SECTOR>|<HIB>"`, each page = `{sheet, total, page, title, relays:[], resources:[]}`.
The bake step **merges** overrides into the scanned pages (de-duped by sheet, sheet-sorted),
so they survive every re-bake. Confirm the exact `page`/`total`/`title` from the PDF first
(physical page == printed sheet for in-range NEWHIB sheets <= 24).

---



| Input | Valid values | On invalid |
|-------|--------------|-----------|
| Test Label | any `#fileSelect` option (±`.txt`, case-insensitive) | Re-ask Step 0 |
| Combo tested? | Resource/Relay rows are not `N/A` / "not tested" | Skip combo; if none remain, report failure |
| PDF sheet | printed `X of Y` within the allowed ranges | Ignore page |

---

## Notes
- The HTML must stay **standalone**: tabs and the Involve Circuitry list are inline
  HTML/CSS/JS; the PDFs are **embedded as base64** by `embed_pdfs.py` and shown via
  in-memory **blob URLs** (relative paths remain only as a fallback). No external library
  or CDN. Run `embed_pdfs.py` last so the single HTML works anywhere, offline.
- Match by the **printed sheet label** (`X of Y`), not the physical PDF page index — the
  two differ for `HIB AB VER 3.20`.
- Always show **both** the sheet label and the big-font page title for every affected page.
- Keep edits minimal and idempotent; reuse existing helpers
  (`groupBySection`, `getVisibleIndexes`, `escapeHtml`, `strIncludes`,
  `findFileByName`) instead of re-implementing them. Do not refactor unrelated parts.
