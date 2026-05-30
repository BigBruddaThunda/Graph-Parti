# GRAPH PARTI — canvas design notes

GRAPH PARTI is the **canvas**: a precision hand-drafting surface (AutoCAD-style line
tools + Krita-style paint layers on a square grid). It is fully **isolated** — it never
imports the Archideck cockpit. These notes cover canvas-only behavior. (The cockpit that
*embeds* the canvas keeps its own notes in `../archideck/DESIGN.md`.)

## Dimensioned drawing — length toggle (planned, 2026-05-30)
While a primitive is being drawn (or when one is selected), show an editable **length
readout** so the architect can set exact magnitudes by hand ("this line is 80", "this
one is 6"):
- **Line / polyline segment** — length label at the **segment's center origin**.
- **Triangle** — a length on **all 3 sides**.
- **Rect / square (cube)** — a length per side.
- **Circle** — radius (and/or diameter).
- **Tab cycles** the active/editable readout through the available lengths when a shape
  has more than one (triangle's 3 sides, rect's sides, etc.). Tab → next segment.
- Typing a value sets that dimension and the geometry snaps to it. Works *alongside* grid
  snap + object snap (does not replace them).
- The readout **pops out at the segment's center origin** (like the dimension floats off
  the line), not in a side panel.

## Cell free-text (planned, 2026-05-30)
- **Click the center of a grid cell → free-text entry**, in place. Text **moves / reflows
  as you type**. Grid-cell-anchored labels and notes living on the canvas.

## 50-char line budget (formatting rule)
- Target **50 characters max per line** before wrapping to the row below.
- Rationale: matches the window width the architect drafts at, and mirrors the Archideck
  **revelator's single-line 50-char budget** (zip code + tail + bar all fit in 50). Keeps
  canvas free-text and the cockpit readout on the same measure.
- Ruler: `12345678901234567890123456789012345678901234567890`

## Status
Planned / captured 2026-05-30 — **not yet built**. Current canvas: infinite grid +
zoom/pan, snap (grid + object endpoints/midpoints), vector tools
(line / polyline-with-close / rect / circle), select / move / delete + QUndoStack,
warm-wool light theme + sky-blue wireframe grid + VG5000 font.
