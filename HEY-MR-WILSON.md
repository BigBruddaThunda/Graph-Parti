# 🐋 HEY MR. WILSON — GRAPH PARTI pickup

> Init phrase: **"hey mr. wilson"** / `/heymrwilson`. You're in the **GRAPH PARTI** repo —
> the canvas + Archideck cockpit tool. This is the pickup note for the tool itself; the
> full cross-repo teleport lives in the home-base repo (`BigBruddaThunda/archideck`).

**Architect:** Jake (Jacob Wilson Berry) · git `FounderCreator <jwberry234@gmail.com>` ·
GitHub `BigBruddaThunda` · last updated **2026-06-03** (district + place tenure)

## What this is
GRAPH PARTI = a precision hand-drafting desktop app (PySide6 / Qt6). One program, two halves
that stay separable in code:
- `graphparti/` — the **canvas** (line tools + paint layers on a square grid). **Isolated —
  never imports the cockpit.**
- `archideck/` — the **portrait cockpit** that *embeds* `graphparti.CanvasWidget`. One-way only.

Run: `python main.py` (split-pane) · `python -m graphparti` (canvas only).
Stack is a hard constraint — **Python 3.13 + PySide6**, venv at `.venv`. Light mode locked:
sheep's-wool paper · sky-blue wireframe grid · **VG5000** font exactly.

## Built (session 1 + 2)
**Environment:** Infinite 7×7 grid + zoom/pan · grid snap with dead zone (1/8) + object snap ·
ortho lock (90/45/30/15°, separate from snap) · all measurements in grid units (1=1 cell).

**Drawing tools:** Line · Polyline (close-to-polygon) · Rect · Circle · Trim (grid +
intersection, works on all shapes, explode-on-trim) · Paint (region flood-fill, respects
line barriers, drag-erase). Tab-type exact dimensions + live readouts on all tools.

**Selection:** Layer-isolated (parti/both/trace). Shift+click multi-select. Right-click
yeet-delete (selected items or item under cursor).

**Color:** 16-swatch paint palette + 16-swatch line palette (2×8 each, right-click = picker).

**Images:** Drag-drop + Ctrl-V paste → parti layer at 50% opacity. Selectable + movable +
8-handle resize (corners + edges).

**Layers:** parti (reference, 50%) / both / trace (working draft). Green dot active indicator.

**Cockpit (Layout v2):** Revelator (single-line, toolbar-height) · Terminal (output + input +
5 modifier buttons) · Middle ground + parallel slider + 12-operator F1-F12 rail · Axis row +
compact 4-reel zip dial + Z-pad. Splitter between terminal and middle ground. Color-shell tint.

## Built (2026-06-03 · district + place tenure)
**Drafting kit completed:** divide · rotate (snap-aware) · extend/fillet (held-E) · word + cell
text · 62-glyph SCL palette (click = type, drag = place) · Five Classical Orders (Vignola,
1D = 1 grid) · save/load `.parti` + PNG · stacked undo/redo · 2-decimal dims.

**District File System floor — BUILT** (`district/` package, peer to `graphparti/`; isolation
held): the wrapped lattice (6,552 base · 406,224 skeleton · 4,032 rooms) · SQLite facet index ·
Node record · three reads **POINT / PATH / SET** · `graphparti↔district` bridge
(`graphparti/district_bridge.py`). Verify: `python -m district.verify` + `python -m district.bridge_verify`.

**Cockpit spawner-deck — BUILT:** book layer · drag [Archideck] plate → zip box (locked zip +
editable `±` tail + `|` free-text) · drag z-pad → flow arrows · drag center 🍗 → leg/handback
(logs to the cockpit terminal) · partial-zip dials · snap-tied resize.

## Next
- **District floor remaining:** Tier 0/1 sorter (no-AI, next build) · cockpit shelf · district
  containment · auto-save-back · semantic index.
- **Place Layer floor (designed, see save-docs):** map base webview · place node record ·
  plan-on-site Tier 0 · curriculum nodes · cron listings.
- Full roadmap: see `INVENTORY.md` + the two save-docs in the home-base repo.

## Mobile (Android / Termux) — new track 2026-05-30
Run the unmodified app on a phone (stylus-capable) via **Termux → proot Debian Trixie →
PySide6 aarch64 wheel → Termux:X11**. No rewrite, no cross-compile. Kit lives in `mobile/`:
`setup-termux.sh` (Stage 1) · `setup-debian.sh` (Stage 2) · `run-graphparti.sh` (the `gp`
launcher) · `README.md` (the phone walkthrough). **Hard gate: glibc ≥ 2.39** — Debian
Bookworm (2.36) fails the PySide6 wheel; Trixie (2.41) / Ubuntu 24.04 (2.39) pass. The
script refuses early on too-old glibc. A true installable `.apk` is a *later* desktop-only
build (x86 Linux + Android NDK + `pyside6-android-deploy`) — not buildable from the phone.

## Pointers
- Mobile kit → `mobile/README.md`
- Cockpit spec → `archideck/DESIGN.md`  ·  Canvas spec → `graphparti/DESIGN.md`
- **District + Place save-docs** (the substrate this canvas writes into) → home-base repo
  `BigBruddaThunda/archideck` → `archideck/docs/PPL-DISTRICT-FILE-SYSTEM.md` (storage, floor
  built) + `archideck/docs/PPL-PLACE-LAYER.md` (the place surface, designed).
- Home base / canon / tenure chain → repo `BigBruddaThunda/archideck` → `archideck/CLAUDE.md`
  + `archideck/HEY-MR-WILSON.md` (full teleport) → latest tenure
  `user/tenure/district-place-tenure-2026-06-03.parti`.
- Home-PC memory → `C:\Users\iamja\.claude\memory\reference_district_file_system.md` +
  `reference_place_layer_context.md` + `reference_graphparti_cockpit_layout.md`

## Flags
- This repo (`Graph-Parti`) is **public**; the archideck home base is private. Flip to private
  if the tool should stay closed.
- A stray `codex/decide-and-update-district-zip-schema` branch from another agent is left in place.

🐋 🧮
