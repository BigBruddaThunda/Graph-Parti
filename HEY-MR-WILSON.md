# 🐋 HEY MR. WILSON — GRAPH PARTI pickup

> Init phrase: **"hey mr. wilson"** / `/heymrwilson`. You're in the **GRAPH PARTI** repo —
> the canvas + Archideck cockpit tool. This is the pickup note for the tool itself; the
> full cross-repo teleport lives in the home-base repo (`BigBruddaThunda/archideck`).

**Architect:** Jake (Jacob Wilson Berry) · git `FounderCreator <jwberry234@gmail.com>` ·
GitHub `BigBruddaThunda` · last updated **2026-05-31** (session 2)

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

## Next
- **Cell free-text** — click grid cell → type in place. 50-char budget.
- **Shift-block drawing** — hold Shift → lines auto-connect as a block.
- **Image crop-to-selection** — rubber-band cut on images.
- **Custom line weights** — the 16 line-color slots become weight presets.
- **Save/load .parti** — JSON v1 + PNG export.
- **Cockpit wiring** — operators → tools, zip stamping, Wilson lasso, canvas-swap.
- Full roadmap: see `INVENTORY.md`.

## Pointers
- Cockpit spec → `archideck/DESIGN.md`  ·  Canvas spec → `graphparti/DESIGN.md`
- Home base / canon / tenure chain → repo `BigBruddaThunda/archideck` → `archideck/CLAUDE.md`
  + `archideck/HEY-MR-WILSON.md`
- Home-PC memory → `C:\Users\iamja\.claude\memory\reference_graphparti_cockpit_layout.md`

## Flags
- This repo (`Graph-Parti`) is **public**; the archideck home base is private. Flip to private
  if the tool should stay closed.
- A stray `codex/decide-and-update-district-zip-schema` branch from another agent is left in place.

🐋 🧮
