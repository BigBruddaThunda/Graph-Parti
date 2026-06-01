# GRAPH PARTI — Full Inventory & Roadmap

> **Last updated:** 2026-05-31 (session 2 — major tool build)
> **Repo:** https://github.com/BigBruddaThunda/Graph-Parti
> **Run:** `python main.py` (split-pane) · `python -m graphparti` (canvas only)
> **Stack:** Python 3.13 + PySide6 (Qt6 Graphics View) · venv at `.venv`

## What GRAPH PARTI Is

GRAPH PARTI is a **precision hand-drafting environment** — AutoCAD-style line tools + paint
fill on a square grid, with the Archideck portrait cockpit docked alongside. One program,
two halves that stay separable in code:

- `graphparti/` — the **environment** (infinite grid canvas with drawing tools, snap, trim,
  paint, layers). **Fully isolated — never imports the cockpit.**
- `archideck/` — the **portrait cockpit** that *embeds* `graphparti.CanvasWidget`. One-way
  dependency only. The cockpit is the Archideck's instrument face: zip dial, operator rail,
  terminal, revelator.

The environment is called "the environment" (not "the canvas") going forward.

## Architecture

```
main.py                    → launches HostWindow (split-pane)
archideck/
  host.py                  → HostWindow: QSplitter[CanvasWidget | ArchideckPanel]
  panel.py                 → ArchideckPanel: Layout v2 (three-thirds cockpit)
  canon.py                 → SCL closed-61 constants (operators, axes, orders, colors, modifiers)
  DESIGN.md                → cockpit design notes + layout v2 spec + parallel slider spec
graphparti/
  __main__.py              → standalone launcher (python -m graphparti)
  app.py                   → install_font (VG5000) + run()
  main_window.py           → MainWindow wraps CanvasWidget
  canvas_widget.py         → CanvasWidget: embeddable isolation boundary
                              toolbar (Select/Line/Polyline/Rect/Circle/Trim/Paint + Snap + Ortho
                              + Undo/Redo + Paint palette 16 + Line palette 16)
                              status bar (coords · snap · zoom · scale · parti/both/trace)
  canvas_view.py           → CanvasView: grid, zoom, pan, snap (grid+osnap+dead-zone),
                              tool routing, trim (grid+intersection), drag-drop images,
                              Ctrl-V paste, Tab dimension input, resize handles, ortho lock
  document.py              → Layer model: RasterLayer (parti, 50% opacity, ref images)
                              + VectorLayer (trace). Items added directly to scene.
  tools.py                 → Tool base + LineTool + RectTool + CircleTool + PolylineTool
                              + SelectTool + TrimTool + PaintTool
  commands.py              → AddItemCommand / MoveItemsCommand / DeleteItemsCommand (QUndoStack)
  assets/fonts/            → VG5000-Regular.otf + .ttf + OFL.txt
```

## Tools Built (This Session)

### Drawing Tools
| Tool | Key | Description |
|------|-----|-------------|
| **Select** | V | Pick/move/band-select. Layer-isolated. Shift+click=multi-select. Right-click=delete. |
| **Line** | L | Ortho lock (when Ortho on). Live dimension readout. Tab-type exact length. |
| **Polyline** | P | Click vertices, close-to-polygon (>=3 pts near start). Ortho-constrained. |
| **Rect** | R | Drag to draw. Tab: width then height. Live W×H readout. |
| **Circle** | C | Center+radius. Tab-type radius. Live r= readout. Explodes on trim. |
| **Trim** | T | Grid-cell + intersection trim. Works on lines, rects, polylines, circles. Right-click when idle = trim. |
| **Paint** | B | Region flood-fill (respects internal lines as barriers). Right-drag = erase. |

### Snap & Constraint
- **Grid snap** with **dead zone** (1/8 of cell — only snaps near grid corners, free in cell centers)
- **Object snap** (endpoints + midpoints) with priority over grid snap
- **Ortho lock** (separate from snap) with angle menu: 90° / 45° / 30° / 15°

### Measurement
- All dimensions in **grid units** (1 = 1 grid cell)
- **Tab-type dimensions**: hold left-click, press Tab, type value, release to commit
- **Live readouts**: line length, rect W×H, circle radius, polyline segment length
- Status bar shows coordinates in grid units

### Layers
- **parti** (back, 50% opacity) — reference images, traced over. Raster layer.
- **trace** (front, full opacity) — the working draft. Vector layer.
- **both** — select/move from either layer. Drawing goes to trace.
- Layer buttons: 🟢 active / ⚪ inactive. Right-click = toggle visibility.

### Color
- **Paint palette** (16 swatches, 2×8) — left-click = select fill color, right-click = color picker
- **Line palette** (16 swatches, 2×8) — left-click = select stroke color, right-click = picker
- Region flood-fill respects line barriers within cells

### Image Handling
- **Drag-drop** images from Explorer onto the environment → parti layer at 50% opacity
- **Ctrl-V paste** from clipboard → parti layer at viewport center
- Images are **selectable + movable** (Switch to parti layer, use Select tool)
- **8 resize handles** (corners + edge midpoints) for stretch/scale

### Cockpit (Archideck Panel — Layout v2)
- **Revelator** — thin single-line strip (50-char budget), toolbar-height aligned
- **Terminal** — output area + input line + 5 modifier buttons on right inner wall
- **Middle ground** — with parallel slider (left, stub) + 12-operator F1-F12 rail (right)
- **Axis row** — 🏛 ⌛ 🔨 [Archideck] 🐬 🌹 🪐 with copper plate
- **Instruments** — compact 4-reel zip dial (left ~2/3) + Z-pad d-pad (right)
- Terminal ↔ middle-ground: draggable QSplitter
- Color dial tints the entire shell (8 SCL colors)

## Ideas Captured (Not Yet Built)

### Canvas / Environment Tools
- **Shift-block drawing** — hold Shift while drawing lines → auto-connect as a block/compound
- **Cell free-text** — click a grid cell center → type text in place, reflows as you type.
  50-char line budget (matches the revelator).
- **Length-toggle on existing geometry** — select a line/shape, Tab cycles through its
  dimensions, type to override. (Currently Tab only works during draw.)
- **Text eraser** — swipe over text to mass-delete. Dual-layer aware (grid lines protected,
  freehand erasable).
- **Smart curve corrector** — draw curves freely, tool smooths/corrects in real time.
  Stylus + mouse compatible.
- **Arc tools** — dedicated arc drawing (3-point, center-radius-angle).
- **Curving trim** — trim arcs at intersections.
- **Image crop-to-selection** — rubber-band on an image cuts it; the selected region becomes
  the new image, the rest is removed. Interior holes respected.

### Parallel Slider (Archideck)
- **Archideck-active mode**: slides within the middle ground (workout blocks / dropdown content).
- **Graph-parti-active mode**: expands up the left shell, spans full canvas height. Shows
  viewport position. Center-click pops a parallel snap-bar in graph-parti for stylus drawing.

### Cockpit Wiring (Future)
- Operators → tool panels in the middle ground
- Zip stamping onto canvas geometry (partial-tag with the dial)
- Wilson "w" lasso for zip-addressing drawn content
- Canvas-swap via [Archideck] copper plate (mobile: flip cockpit ↔ canvas)
- Event-logging flag (AI reads what was drafted)
- Terminal ↔ AI chat / command interface
- Middle-ground = canvas viewport preview (minimap)

### DLC-Layer Features (Future Graph Parti Expansions)
- **Raster paint layer** (step 7) — pen/brush/eraser on the parti layer (Krita-style)
- **On-canvas ZIP stamper** (step 8) — 4-dial stamp metadata onto selected geometry
- **Save/load .parti** (step 9) — JSON v1 file format + export flattened PNG
- **Custom line weights** — the 16 line-color slots evolve into weight presets with
  functional meaning (structure, annotation, hidden, center, etc.)
- **Procedural rendering** — line weights map to design tokens for AI/automated drawing
- **Multiple named layers** — beyond parti/trace, user-created layers with visibility/lock
- **Blocks / symbols** — reusable component groups that stamp into the environment
- **Dimension annotations** — leader lines + dimension text (architectural standard)
- **Hatch patterns** — cross-hatch, section-cut, material fills
- **Grid scale modes** — architectural scales (1:100, 1:50, 1:20) with real-world units

## Commit History
| Hash | Message |
|------|---------|
| 0b7428d | setup + step 1: scaffold + infinite grid canvas (zoom/pan) |
| 4e69824 | step 2: snap-to-grid + live coordinate readout |
| dbea4c9 | step 3: vector tools (line, polyline, rect, circle) + layer model |
| 676c314 | theme: warm-wool paper, sky-blue notebook grid, VG5000 font (light mode) |
| cc8166d | step 4: object snap (endpoints + midpoints) |
| ca3ca66 | step 5: select / move / delete + undo (QUndoStack) |
| fe89c89 | fix: polyline closes into a polygon; right-click cancels in-progress draw |
| 5925ad7 | archideck: split-pane cockpit + portrait Archideck + working zip dial |
| d43f103 | docs: cockpit layout v2 + canvas dimensioning/free-text notes |
| be48ca4 | docs: Hey Mr. Wilson teleport / session pickup note |
| (next) | session 2: cockpit v2 + full tool suite (trim/paint/ortho/Tab-dim/image/layers) |

## Cross-Repo Pointers
- **Home base (substrate)**: `BigBruddaThunda/archideck` (private) — canon, tenure chain,
  CLAUDE.md, the closed 61-glyph SCL system.
- **This tool**: `BigBruddaThunda/Graph-Parti` (public) — the drafting environment.
- **Tenure chain**: `archideck/user/tenure/graphparti-tenure-2026-05-30.parti` (session 1 close).
- **Memory**: `~/.claude/memory/reference_graphparti_cockpit_layout.md` (home PC).
- **Hey Mr. Wilson**: `HEY-MR-WILSON.md` in both repos — session teleport / init phrase.
- **Desktop shortcut**: `Archideck GRAPH PARTI.lnk` on the Windows desktop.

## Build Posture
- Spine-out: verify headless (offscreen QApplication, drive tools programmatically, assert
  item counts/types) then commit per step.
- Stack is a HARD constraint: Python 3.13 + PySide6 (Qt6). Do not substitute.
- Light mode locked: warm sheep's-wool paper (#F2EBD8) + sky-blue wireframe grid + VG5000 font.
- Isolation: graphparti never imports archideck. One-way only.
- Grid: 7×7 major lines, 20 scene units per cell, 1 grid unit = 1 cell in all user-facing dims.
