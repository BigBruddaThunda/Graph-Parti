# 🐋 HEY MR. WILSON — GRAPH PARTI pickup

> Init phrase: **"hey mr. wilson"** / `/heymrwilson`. You're in the **GRAPH PARTI** repo —
> the canvas + Archideck cockpit tool. This is the pickup note for the tool itself; the
> full cross-repo teleport lives in the home-base repo (`BigBruddaThunda/archideck`).

**Architect:** Jake (Jacob Wilson Berry) · git `FounderCreator <jwberry234@gmail.com>` ·
GitHub `BigBruddaThunda` · last updated **2026-06-09** (Conductor terminal wiring + shell mode)

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

## Built (2026-06-09 · Conductor terminal wiring + shell mode)
**Conductor (duco) — multi-backend, WORKING.** First successful test: LM Studio LFM2.5-1.2B
drew circles, rects, polylines on the canvas from chat commands. Multi-backend bridge in
`archideck/conductor.py`: Ollama (localhost:11434) · LM Studio (localhost:1234) · Anthropic API.
OpenAI-compatible API for local models, Anthropic SDK for cloud. Model selector dropdown +
refresh button in the terminal area (`panel.py`). Tools: draw_line, draw_rect, draw_circle,
draw_polyline (fill_region stubbed). Undo-integrated (Ctrl-Z undoes Conductor draws as one
macro). Context injection: active zip + handback log + bounding rect. 🍗 handback auto-notifies
the Conductor (no follow-up message needed).

**Shell mode in the terminal — BUILT.** The terminal is a real terminal. Known CLI commands
(`claude`, `codex`, `gsk`, `ollama`, `lms`, `git`, `python`, `node`, `npm`, `pip`) run as
subprocesses with stdout streamed to the terminal output. `!` prefix runs any shell command.
Smart translation: `claude prompt` → `claude -p "prompt"` (non-interactive), `codex prompt` →
`codex exec "prompt"`. Subsequent input pipes to the running process's stdin.

**CLI tools installed:** `gsk` (Genspark CLI, logged in, 130+ action tools) · `codex` (OpenAI
Codex CLI) · `claude` (Claude Code) · `ollama` (qwen2.5:1.5b pulled) · `lms` (LM Studio
headless, 3 models: LFM2.5-1.2B, Nemotron-3-Nano-4B, Qwen3.5-9B).

**Dependencies added:** `anthropic` + `openai` Python packages in `.venv`.

## Next
- **Codex as a proper Conductor backend** — wire `codex exec --json` with structured output
  parsing so Codex can use its full tool system (file edits, MCP, web search) for canvas work.
- **Genspark tools as Conductor tools** — web search, image gen, audio gen callable from chat.
- **Model quality for tool use** — small local models (1.5B) can't call tools reliably; need
  Qwen3.5-9B (LM Studio) or cloud models for real tool use. Local models are runners for chat.
- **Codex crashing the app** — needs investigation (may need `CREATE_NO_WINDOW` flag adjustment).
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

## Built (2026-06-17 · Wave 1 tool pass + joystick + build plan)
**Tool additions:** Mirror (M) · Ellipse (2-point axis + width) · Arc (3-point) · Fence trim
(left-drag on Trim tool, or right-drag on any tool). **Bug fixes:** selection clears on tool
switch · text defocus on click-away/tool-switch · copy carries fill color · offset works on
moved items · rotate clears selection · trim merges micro-fragments · polyline tighter close
threshold. **Paint tool:** grid-on uses solid cell rects (no more pixelated flood fill).
**Text:** dotted border shows claimed space. Text tools properly deactivate on tool switch.
**Trim keeps shapes as one piece:** sibling edges stay as connected QGraphicsPathItem, not
individual lines.

**Viewport navigation system** (`graphparti/joystick.py`): `ViewNavigator` — one movement
grammar, three input surfaces (joystick, arrow keys, future z-pad). Two modes: grid-on =
cell-stepped orthogonal (tile-based), grid-off = smooth analog (free-roam). Joystick reads
via `winmm.dll`, polls at 60fps, only active when window has focus.

**Build plan ratified** (6 phases): A stabilize → B size math (600x1399, 3:7, percentage
anchors) → C tool polish → D icon discipline → E engine prototype → F operator panels.

## Built (2026-06-23 · Waves 1-5 tool campaign + 61-drawer organization)
**22 new tool classes** across 5 waves (tools.py: 17 → 39 classes, ~2100 → 3925 lines):

**Wave 1 — Daily Workflow:** CopyTool, EyedropperTool, ConstructionLineTool,
MatchPropTool, PolygonTool, ArrayRectTool, ArrayPolarTool.

**Wave 2 — Modify:** JoinTool, FilletTool (radius arc), ChamferTool (straight bevel),
BreakTool (split at point), PEditTool (polyline vertex editing with drag handles).

**Wave 3 — Annotation + Render:** LinearDimTool (architectural dimensions with oblique
ticks), LeaderTool (annotation arrows), HatchTool (parallel line pattern fill within
boundaries — the #1 render request), LINE_TYPES dict + set_line_type() (dashed/center/
hidden/phantom/dot/dashdot cycle button).

**Wave 4 — Curves + Advanced:** SplineTool (Catmull-Rom → cubic Bezier through all points),
crossing select (right-to-left = green, touches items), StretchTool (partial vertex move),
MeasureTool (persistent distance annotations).

**Wave 5 — Infrastructure:** Named layers (add/remove/reorder beyond default 3),
LINE_WEIGHTS dict + set_line_weight() (ISO pen ladder cycle button), PerspectiveTool
(vanishing point placement with 24 radiating guide rays), BlockSaveTool + BlockInsertTool
(reusable symbol groups).

**61-Drawer Tool Organization:** Every SCL glyph on the bottom row is now a tool drawer.
Right-click = popup menu of tools in that drawer. Left-click = glyph character (current
behavior). `TOOL_DRAWERS` dict maps 27 glyphs to tool lists. Tools overlap across drawers
by design (mirror lives in 🪞 AND 🏟). Alt-key command line: tap Alt → floating input →
type tool name (fuzzy match) → Enter activates. `TOOL_COMMANDS` dict: 60+ aliases.

**Test infrastructure:** 25 headless tests (offscreen QApplication), all passing in <1s.
conftest.py with `canvas_env` fixture that properly cleans up Qt objects between tests.

**Docs added:** `docs/TOOL-INVENTORY.md` (full 3-domain cross-reference), `docs/TOOL-DRAWERS.md`
(61-glyph organization map), `docs/TOOL-HUNT-ROUND2.md` (fresh-eyes reconnaissance —
SymPy/CadQuery/WFC/tcod/Lark/NodeGraphQt/Skyfield + 11 new lanes), wave 1-5 implementation
plans in `docs/superpowers/plans/`.

## Flags
- **seam:GP-PATH RESOLVED** — `C:\Users\iamja\Desktop\graph-parti` (branch **master**) is
  the **live build canvas**. `C:\Users\iamja\Documents\graph parti\Graph-Parti` (branch
  **main**) is the **research/design canvas** (base-diameter docs, cascades). Same remote
  (`BigBruddaThunda/Graph-Parti`), different branches. Build work goes to Desktop/master.
- This repo (`Graph-Parti`) is **public**; the archideck home base is private. Flip to private
  if the tool should stay closed.
- A stray `codex/decide-and-update-district-zip-schema` branch from another agent is left in place.
- `.parti` test files (`ALPHA.parti`, `alpha1.parti`) in repo root from smoke testing — not committed.
- **LM Studio headless:** start with `lms server start` (serves at :1234, JIT model loading).
- **Ollama:** `ollama serve` (auto-starts on install), models at `ollama list`.
- **Genspark CLI:** logged in, config at `~/.genspark-tool-cli/config.json`.

🐋 🧮
