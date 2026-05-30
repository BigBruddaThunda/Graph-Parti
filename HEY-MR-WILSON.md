# 🐋 HEY MR. WILSON — GRAPH PARTI pickup

> Init phrase: **"hey mr. wilson"** / `/heymrwilson`. You're in the **GRAPH PARTI** repo —
> the canvas + Archideck cockpit tool. This is the pickup note for the tool itself; the
> full cross-repo teleport lives in the home-base repo (`BigBruddaThunda/archideck`).

**Architect:** Jake (Jacob Wilson Berry) · git `FounderCreator <jwberry234@gmail.com>` ·
GitHub `BigBruddaThunda` · last updated **2026-05-30**

## What this is
GRAPH PARTI = a precision hand-drafting desktop app (PySide6 / Qt6). One program, two halves
that stay separable in code:
- `graphparti/` — the **canvas** (line tools + paint layers on a square grid). **Isolated —
  never imports the cockpit.**
- `archideck/` — the **portrait cockpit** that *embeds* `graphparti.CanvasWidget`. One-way only.

Run: `python main.py` (split-pane) · `python -m graphparti` (canvas only).
Stack is a hard constraint — **Python 3.13 + PySide6**, venv at `.venv`. Light mode locked:
sheep's-wool paper · sky-blue wireframe grid · **VG5000** font exactly.

## Built (committed on `master`)
Infinite grid + zoom/pan · grid + object snap (endpoints/midpoints) · vector tools
(line / polyline-with-close / rect / circle) · select / move / delete + QUndoStack ·
warm-wool light theme + sky-blue grid + VG5000 · split-pane host + portrait cockpit
(zip field · 12-operator F1–F12 rail · axis row + copper [Archideck] plate · working 4-dial
zip dial · Z-pad).

## Next (specced, not built)
- **Cockpit layout v2** — three vertical thirds (revelator + terminal / parallel-slider +
  middle-ground + 12-operator rail / axis row + zip dial + z-pad). Spec: `archideck/DESIGN.md`
  → "Layout v2".
- **Canvas length-toggle** dimensioning (readout at segment center origin; **Tab cycles** a
  shape's sides) + **click-in-cell free text** (reflows as you type) + 50-char line budget.
  Spec: `graphparti/DESIGN.md`.
- Canvas brief steps 7–10: raster paint layer · on-canvas ZIP stamper · save/load `.parti`
  + PNG export · palette/chrome.

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
