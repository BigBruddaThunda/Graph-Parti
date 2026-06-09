# Conductor Terminal Wiring — Design Spec

> **Date:** 2026-06-03
> **Status:** approved (brainstorming complete)
> **Track:** Agent ecosystem / round table — first nerve
> **Approach:** (A) Thin bridge — single file, sync-in-thread
> **Model:** claude-haiku-4-5-20251001 (cheapest, tool-use capable)
> **New dependency:** `anthropic` Python package
> **New file:** `archideck/conductor.py`
> **Files modified:** `archideck/panel.py`, `archideck/host.py`, `graphparti/canvas_view.py`

## What This Is

Wire the Archideck cockpit terminal to Claude Haiku via the Anthropic SDK.
The terminal becomes a two-tempo interface:

1. **Chat to think** — free multi-turn conversation in the terminal. No canvas
   action. The Conductor (duco) responds as a concise collaborator.
2. **Handback to act** — drag 🍗 onto a zip box to define a working region,
   then type a command. The Conductor draws geometry within those bounds using
   tool use (function calling).

The conversation builds understanding across turns; the 🍗 handback is the
"go" signal that provides spatial context.

## 1 — Conductor Class + Threading

One new file: `archideck/conductor.py`.

```
Conductor
├── __init__(api_key: str)
│   ├── anthropic.Anthropic(api_key)
│   ├── conversation: list[dict]       # message history [{role, content}]
│   ├── handbacks: list[str]           # copied from panel._handbacks
│   ├── active_zip: tuple              # (op, ax, order, color) from dials
│   └── last_handback_bounds: dict|None # {x, y, w, h} in grid units
│
├── set_context(zip, handbacks, bounds)   # called before each send
├── _build_system_prompt() -> str         # assembles persona + context
├── send(user_text: str) -> generator     # appends to history, calls API
└── reset()                               # clears conversation + context
```

### ConductorWorker (QRunnable)

Runs `Conductor.send()` in `QThreadPool`. Signals:

| Signal | Payload | Purpose |
|--------|---------|---------|
| `response_chunk` | `str` | One streaming token for live display |
| `response_done` | `str` | Full assembled response text |
| `tool_call_requested` | `str, dict` | Tool name + args dict for canvas execution |
| `error` | `str` | API or network error message |

The main thread stays responsive during API calls. Canvas tool execution
happens on the main thread (received via signal from the worker).

### API Key

Reads `ANTHROPIC_API_KEY` from `os.environ`. If missing, the terminal shows
on first send attempt:

> `set ANTHROPIC_API_KEY to enable the Conductor`

No crash, no dialog, no startup check. Chat is simply inert until the key exists.

### Streaming

Responses stream token-by-token into the terminal output. Haiku is fast enough
that streaming is visible but not laggy. The terminal output widget appends
chunks as they arrive.

## 2 — System Prompt + Context Injection

The system prompt rebuilds on every send (cheap string concat). Three layers:

### Layer 1 — Persona (static)

> You are the Conductor (duco) — the Archideck's orchestrating agent. You work
> inside a precision hand-drafting environment called Graph Parti (PySide6
> canvas, square grid, grid units). The architect speaks to you through the
> terminal. You can chat freely, and when given a handback (a flagged region on
> the canvas), you can draw geometry within its bounds using your tools. All
> coordinates are in grid units (1 = 1 grid cell). Stay concise — the terminal
> is a single-column text window, not a page.

### Layer 2 — Active zip (dynamic, always present)

> Current zip dial: [🦢 🏛 🌾 ⚫]

Blank dials show as `_`. Tells the Conductor which district the architect is
working in.

### Layer 3 — Handback context (dynamic, only when handbacks exist)

> Handback log (most recent first):
> - 🍗 🦢🏛🌾⚫ "social-media-drafts" — bounds: (3, 2) → (7, 6) [4×4 grid cells]
>
> The most recent handback is your active working region. When asked to draw,
> fit your geometry within its bounds.

When no handbacks exist, Layer 3 is omitted entirely.

### Conversation History

Standard `messages` list: `[{role: "user", content: "..."}, ...]`. No
summarization, no windowing — keep all messages for the session. Haiku's
200k context is large enough that a single app session won't overflow it.
Resets on app restart. No persistence for v1.

## 3 — Canvas Tools (Function Calling)

Haiku receives these as tool definitions. All coordinates in grid units.

| Tool | Parameters | Creates |
|------|-----------|---------|
| `draw_line` | `x1, y1, x2, y2, color?` | Line item on trace layer |
| `draw_rect` | `x, y, width, height, color?` | Rect item |
| `draw_circle` | `cx, cy, radius, color?` | Circle item |
| `draw_polyline` | `points: [[x,y],...], closed?, color?` | Polyline / polygon |
| `fill_region` | `x, y, color` | Flood-fill paint at grid cell |

### Color Handling

Default color = active line palette color (if not specified by the model).
The model can pass hex (`"#C1140C"`) or named colors (`"red"`, `"blue"`) —
we normalize to hex before execution.

### Bounds Enforcement

Before executing any tool call, check that the geometry fits inside
`last_handback_bounds`. If it doesn't, the tool call returns an error to Haiku:

> `geometry exceeds handback bounds (3,2)→(7,6)`

Haiku can retry with corrected coordinates.

If there's no active handback and the model tries a draw tool:

> `no active handback — drag 🍗 onto a zip box first to define the working region`

Chat always works; drawing requires the handback gesture.

### Undo Integration

Every tool call wraps in an `AddItemCommand` on the `QUndoStack`. Ctrl-Z
undoes the Conductor's draws exactly like hand-drawn items. A multi-tool
response (e.g., "draw a star" = 16 lines) groups into one undo macro via
`beginMacro` / `endMacro`.

### Execution Path

```
ConductorWorker emits tool_call_requested(name, args)
    → host._execute_tool(name, args)
        → creates QGraphicsItem on the canvas scene (trace layer)
        → wraps in AddItemCommand (undo stack)
        → returns result string to worker
            → worker sends tool result back to Haiku
                → Haiku continues (more tools or final text response)
```

## 4 — Wiring (Changes to Existing Files)

### `archideck/panel.py` (2 changes)

1. **Terminal input signal:** `_terminal_input.returnPressed` emits a new
   signal `terminal_submitted(str)` carrying the input text, then clears the
   input. The panel doesn't know about the Conductor.

2. **Terminal output method:** New `append_terminal(text: str, prefix: str = "")`
   method. Writes a formatted line to `_terminal_output`. Unifies the handback
   log and Conductor responses into one output method.

### `archideck/host.py` (the orchestrator)

1. Creates `Conductor(os.environ.get("ANTHROPIC_API_KEY", ""))` on startup.
2. `panel.terminal_submitted` → spawns `ConductorWorker` in `QThreadPool`.
3. `worker.response_chunk` → `panel.append_terminal()` (streaming display).
4. `worker.tool_call_requested` → `host._execute_tool()` (creates canvas items).
5. On handback (`handback_requested`): existing wiring unchanged. Add one line
   to also pass the handback zip + bounds rect to `conductor.set_context()`.
6. On dial change (`zip_changed`): existing wiring unchanged. Add one line to
   pass the new zip to `conductor.set_context()`.

### `graphparti/canvas_view.py` (1 change)

1. `_leg_handback` currently emits `handback_requested(str)` with a summary
   string. Add a second signal `handback_with_bounds(str, dict)` that also
   includes the bounding rect of the zip box in grid units:
   `{"x": gx, "y": gy, "w": gw, "h": gh}`. The host reads the bounds dict
   and passes it to `conductor.set_context()`.

### No changes to:

`canvas_widget.py`, `document.py`, `tools.py`, `commands.py`,
`district_bridge.py`, or any `district/` files.

## 5 — Dependency

```
pip install anthropic
```

Added to `.venv`. No other new dependencies. The `anthropic` package handles
auth, streaming, tool use, and retries.

## 6 — What This Does NOT Include (v1 boundary)

- No bus (`operator-bus.jsonl`) — the Conductor calls the API directly.
  Bus wraps around later as a one-line-per-action emitter.
- No persistence — conversation resets on app restart.
- No multi-agent — one Conductor, one terminal, one conversation thread.
- No I.N.P.U.T. verb-hat wiring — the 5 modifier buttons stay inert.
- No district index queries — the Conductor sees handback summaries and
  the active zip, not the full node index. (Upgrade path: add a
  `query_district` tool later.)
- No image generation or raster operations — draw tools only.
- No canvas read-back — the Conductor can't see what's already drawn.
  (Upgrade path: add a `describe_region` tool that summarizes items in bounds.)
