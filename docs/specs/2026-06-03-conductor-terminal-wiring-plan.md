# Conductor Terminal Wiring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the cockpit terminal to Claude Haiku so the architect can chat and (via 🍗 handback) command the Conductor to draw geometry on the canvas.

**Architecture:** One new file (`archideck/conductor.py`) holds the Anthropic client, conversation history, system prompt builder, tool definitions, and a QRunnable worker. Three existing files get small edits: `panel.py` emits a signal on terminal input, `host.py` orchestrates the Conductor + canvas tool execution, `canvas_view.py` enriches the handback signal with bounding-rect data.

**Tech Stack:** Python 3.13, PySide6, `anthropic` SDK, claude-haiku-4-5-20251001

**Live repo:** `C:\Users\iamja\Desktop\graph-parti`

**Key codebase facts:**
- Grid: `grid_spacing = 20` scene units per cell. 1 grid unit = 1 cell = 20 scene units.
- Layers: index 0=parti (raster), 1=trace (vector, default active), 2=book (vector, zip boxes).
- Undo: `canvas.undo_stack` (QUndoStack). `view.add_item(item)` pushes `AddItemCommand`.
- Macro: `undo_stack.beginMacro("name")` / `endMacro()` groups multiple commands.
- Pens: cosmetic (`pen.setCosmetic(True)`), width 1.5–2.0.
- Line color: `canvas._line_palette.active_color()` returns current QColor.
- Handback: `view.handback_requested(str)` signal. Zip box rect is `box.rect()` in scene units.
- Host wiring: `host.py` connects cockpit signals to canvas methods.

---

### Task 1: Install `anthropic` and update requirements

**Files:**
- Modify: `C:\Users\iamja\Desktop\graph-parti\requirements.txt`

- [ ] **Step 1: Install anthropic into the venv**

```
cd C:\Users\iamja\Desktop\graph-parti
.venv\Scripts\pip install anthropic
```

- [ ] **Step 2: Update requirements.txt**

```
PySide6
anthropic
```

- [ ] **Step 3: Verify import works**

```
.venv\Scripts\python -c "import anthropic; print(anthropic.__version__)"
```

Expected: prints a version string (e.g., `0.52.0`), no errors.

- [ ] **Step 4: Commit**

```
git add requirements.txt
git commit -m "add anthropic SDK dependency for Conductor terminal wiring"
```

---

### Task 2: Add `terminal_submitted` signal + `append_terminal` method to panel.py

**Files:**
- Modify: `C:\Users\iamja\Desktop\graph-parti\archideck\panel.py`

- [ ] **Step 1: Add `terminal_submitted` signal to ArchideckPanel**

At line 207 (inside `ArchideckPanel`, after `zip_changed`):

```python
class ArchideckPanel(QWidget):
    """The portrait cockpit — three-thirds layout v2."""

    zip_changed = Signal(str, str, str, str)
    terminal_submitted = Signal(str)
```

- [ ] **Step 2: Wire `_terminal_input.returnPressed` to emit the signal**

At the end of `_build_terminal` (after `splitter.addWidget(frame)`, around line 341), add:

```python
        self._terminal_input.returnPressed.connect(self._on_terminal_submit)
```

- [ ] **Step 3: Add `_on_terminal_submit` method**

After `receive_handback` (around line 504):

```python
    def _on_terminal_submit(self) -> None:
        text = self._terminal_input.text().strip()
        if text:
            self.terminal_submitted.emit(text)
            self._terminal_input.clear()
```

- [ ] **Step 4: Add `append_terminal` method**

After `_on_terminal_submit`:

```python
    def append_terminal(self, text: str, prefix: str = "") -> None:
        line = f"{prefix} {text}" if prefix else text
        self._terminal_output.appendPlainText(line)
```

- [ ] **Step 5: Verify the app launches**

```
cd C:\Users\iamja\Desktop\graph-parti
.venv\Scripts\python main.py
```

Type into the terminal input and press Enter — the text should disappear (cleared). Nothing else happens yet (no consumer wired). Close the app.

- [ ] **Step 6: Commit**

```
git add archideck/panel.py
git commit -m "panel: emit terminal_submitted signal + append_terminal method"
```

---

### Task 3: Enrich handback signal with bounding rect

**Files:**
- Modify: `C:\Users\iamja\Desktop\graph-parti\graphparti\canvas_view.py`

- [ ] **Step 1: Add `handback_with_bounds` signal**

At line 32 (after `handback_requested`):

```python
    handback_requested = Signal(str)     # district legged back to the Archideck
    handback_with_bounds = Signal(str, dict)  # same + bounding rect in grid units
```

- [ ] **Step 2: Emit `handback_with_bounds` in `_leg_handback`**

At the end of `_leg_handback` (line 1138), after the existing `handback_requested.emit(...)`, add:

```python
        bounds_grid = {
            "x": box.rect().x() / self.grid_spacing,
            "y": box.rect().y() / self.grid_spacing,
            "w": box.rect().width() / self.grid_spacing,
            "h": box.rect().height() / self.grid_spacing,
        }
        self.handback_with_bounds.emit(
            zipstr + (f'  "{title}"' if title else ""), bounds_grid)
```

Note: zip box rects are in scene units. Dividing by `grid_spacing` (20) converts to grid units.

- [ ] **Step 3: Verify the app launches and handback still works**

```
.venv\Scripts\python main.py
```

Drag [Archideck] plate onto canvas to create a zip box. Drag 🍗 onto the zip box. Terminal should still show `🍗 handback ← ...`. Close the app.

- [ ] **Step 4: Commit**

```
git add graphparti/canvas_view.py
git commit -m "canvas: emit handback_with_bounds signal with grid-unit bounding rect"
```

---

### Task 4: Create `archideck/conductor.py` — the Conductor class

**Files:**
- Create: `C:\Users\iamja\Desktop\graph-parti\archideck\conductor.py`

- [ ] **Step 1: Write the Conductor class**

```python
"""The Conductor (duco) — the Archideck's orchestrating agent.

Thin bridge between the cockpit terminal and Claude Haiku. Holds conversation
history, builds the system prompt with context injection (active zip + handback
log), and defines canvas drawing tools for function calling. A QRunnable worker
runs the API call off the UI thread; signals carry responses and tool calls
back to the main thread for display and canvas execution.
"""
from __future__ import annotations

import json
import os
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

PERSONA = (
    "You are the Conductor (duco) — the Archideck's orchestrating agent. "
    "You work inside a precision hand-drafting environment called Graph Parti "
    "(PySide6 canvas, square grid, grid units). The architect speaks to you "
    "through the terminal. You can chat freely, and when given a handback "
    "(a flagged region on the canvas), you can draw geometry within its bounds "
    "using your tools. All coordinates are in grid units (1 = 1 grid cell). "
    "Stay concise — the terminal is a single-column text window, not a page."
)

TOOLS = [
    {
        "name": "draw_line",
        "description": (
            "Draw a straight line on the canvas. Coordinates in grid units."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x1": {"type": "number", "description": "Start X in grid units"},
                "y1": {"type": "number", "description": "Start Y in grid units"},
                "x2": {"type": "number", "description": "End X in grid units"},
                "y2": {"type": "number", "description": "End Y in grid units"},
                "color": {
                    "type": "string",
                    "description": "Hex color (e.g. '#C1140C'). Omit for current palette color.",
                },
            },
            "required": ["x1", "y1", "x2", "y2"],
        },
    },
    {
        "name": "draw_rect",
        "description": "Draw a rectangle. x,y = top-left corner in grid units.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "Left edge in grid units"},
                "y": {"type": "number", "description": "Top edge in grid units"},
                "width": {"type": "number", "description": "Width in grid units"},
                "height": {"type": "number", "description": "Height in grid units"},
                "color": {"type": "string", "description": "Hex color. Omit for default."},
            },
            "required": ["x", "y", "width", "height"],
        },
    },
    {
        "name": "draw_circle",
        "description": "Draw a circle. cx,cy = center in grid units.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cx": {"type": "number", "description": "Center X in grid units"},
                "cy": {"type": "number", "description": "Center Y in grid units"},
                "radius": {"type": "number", "description": "Radius in grid units"},
                "color": {"type": "string", "description": "Hex color. Omit for default."},
            },
            "required": ["cx", "cy", "radius"],
        },
    },
    {
        "name": "draw_polyline",
        "description": (
            "Draw a polyline (or polygon if closed). Points in grid units."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "points": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "description": "List of [x, y] points in grid units",
                },
                "closed": {
                    "type": "boolean",
                    "description": "Close the path into a polygon",
                    "default": False,
                },
                "color": {"type": "string", "description": "Hex color. Omit for default."},
            },
            "required": ["points"],
        },
    },
    {
        "name": "fill_region",
        "description": (
            "Flood-fill a grid cell with color. x,y = the cell to fill."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "Cell X in grid units"},
                "y": {"type": "number", "description": "Cell Y in grid units"},
                "color": {
                    "type": "string",
                    "description": "Fill color as hex (e.g. '#2464E5')",
                },
            },
            "required": ["x", "y", "color"],
        },
    },
]


class Conductor:
    """Manages conversation state + Anthropic API calls."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.conversation: list[dict] = []
        self.handbacks: list[str] = []
        self.active_zip: tuple = ("", "", "", "")
        self.last_handback_bounds: dict | None = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def set_context(
        self,
        zip_tuple: tuple | None = None,
        handbacks: list[str] | None = None,
        bounds: dict | None = None,
    ) -> None:
        if zip_tuple is not None:
            self.active_zip = zip_tuple
        if handbacks is not None:
            self.handbacks = list(handbacks)
        if bounds is not None:
            self.last_handback_bounds = bounds

    def add_handback(self, summary: str, bounds: dict | None = None) -> None:
        self.handbacks.append(summary)
        if bounds is not None:
            self.last_handback_bounds = bounds

    def reset(self) -> None:
        self.conversation.clear()
        self.handbacks.clear()
        self.last_handback_bounds = None

    def build_system_prompt(self) -> str:
        parts = [PERSONA]
        zg = " ".join((g if g else "_") for g in self.active_zip)
        parts.append(f"\nCurrent zip dial: [{zg}]")
        if self.handbacks:
            lines = "\n".join(
                f"  - 🍗 {h}" for h in reversed(self.handbacks)
            )
            parts.append(f"\nHandback log (most recent first):\n{lines}")
            if self.last_handback_bounds:
                b = self.last_handback_bounds
                parts.append(
                    f"\nThe most recent handback bounds: "
                    f"({b['x']:.1f}, {b['y']:.1f}) → "
                    f"({b['x'] + b['w']:.1f}, {b['y'] + b['h']:.1f}) "
                    f"[{b['w']:.1f} × {b['h']:.1f} grid cells]. "
                    "When asked to draw, fit your geometry within these bounds."
                )
        return "\n".join(parts)


class _WorkerSignals(QObject):
    response_chunk = Signal(str)
    response_done = Signal(str)
    tool_call = Signal(str, dict, str)  # name, args, tool_use_id
    tool_calls_done = Signal()
    error = Signal(str)


class ConductorWorker(QRunnable):
    """Runs a single Conductor API call off the UI thread."""

    def __init__(self, conductor: Conductor, user_text: str) -> None:
        super().__init__()
        self.conductor = conductor
        self.user_text = user_text
        self.signals = _WorkerSignals()
        self.setAutoDelete(True)
        self._tool_results: list[dict] = []

    def add_tool_result(self, tool_use_id: str, result: str) -> None:
        self._tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result,
        })

    @Slot()
    def run(self) -> None:
        c = self.conductor
        if not c.available:
            self.signals.error.emit(
                "set ANTHROPIC_API_KEY to enable the Conductor"
            )
            return
        c.conversation.append({"role": "user", "content": self.user_text})
        try:
            self._call_api(c)
        except Exception as e:
            self.signals.error.emit(str(e))

    def _call_api(self, c: Conductor) -> None:
        while True:
            full_text = ""
            tool_uses: list[dict] = []
            with c._client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=c.build_system_prompt(),
                messages=c.conversation,
                tools=TOOLS,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            full_text += event.delta.text
                            self.signals.response_chunk.emit(event.delta.text)

            response = stream.get_final_message()
            for block in response.content:
                if block.type == "tool_use":
                    tool_uses.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            c.conversation.append({
                "role": "assistant",
                "content": response.content,
            })

            if not tool_uses:
                self.signals.response_done.emit(full_text)
                return

            self._tool_results.clear()
            for tu in tool_uses:
                self.signals.tool_call.emit(tu["name"], tu["input"], tu["id"])

            self.signals.tool_calls_done.emit()

            import time
            deadline = time.monotonic() + 10
            while len(self._tool_results) < len(tool_uses):
                if time.monotonic() > deadline:
                    break
                time.sleep(0.02)

            c.conversation.append({
                "role": "user",
                "content": self._tool_results,
            })
```

- [ ] **Step 2: Verify the module imports cleanly**

```
cd C:\Users\iamja\Desktop\graph-parti
set PYTHONIOENCODING=utf-8
.venv\Scripts\python -c "from archideck.conductor import Conductor, ConductorWorker, TOOLS; print(f'{len(TOOLS)} tools defined'); c = Conductor(); print(f'available={c.available}'); print(c.build_system_prompt()[:80])"
```

Expected: `5 tools defined`, `available=False`, first 80 chars of the persona.

- [ ] **Step 3: Commit**

```
git add archideck/conductor.py
git commit -m "conductor: Anthropic SDK bridge — Conductor class + ConductorWorker + 5 canvas tools"
```

---

### Task 5: Wire the Conductor into host.py

**Files:**
- Modify: `C:\Users\iamja\Desktop\graph-parti\archideck\host.py`

- [ ] **Step 1: Add imports and Conductor setup**

Add to the imports at the top of host.py:

```python
import os

from PySide6.QtCore import QPointF, QRectF, QThreadPool
from PySide6.QtGui import QColor, QPen, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
)

from .conductor import Conductor, ConductorWorker
```

(Keep existing imports; `os` and `sys` are already imported. Add the Qt imports that aren't already there and the conductor import.)

- [ ] **Step 2: Create the Conductor in HostWindow.__init__**

After `self._splitter = splitter` (line 54), add:

```python
        # ── Conductor (terminal → Claude Haiku) ──
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._conductor = Conductor(api_key)
        self._thread_pool = QThreadPool.globalInstance()
        self._active_worker = None

        # Terminal input → send to Conductor
        self.cockpit.terminal_submitted.connect(self._on_terminal_input)

        # Zip dial changes → update Conductor context
        self.cockpit.zip_changed.connect(self._on_zip_for_conductor)

        # Handback with bounds → update Conductor context
        self.canvas.view.handback_with_bounds.connect(self._on_handback_for_conductor)
```

- [ ] **Step 3: Add the input handler + worker launcher**

After `__init__`, add these methods to HostWindow:

```python
    def _on_terminal_input(self, text: str) -> None:
        self.cockpit.append_terminal(text, prefix=">")
        if self._active_worker is not None:
            self.cockpit.append_terminal("(waiting for previous response...)")
            return
        self._conductor.set_context(
            zip_tuple=self.cockpit.current_zip(),
            handbacks=list(getattr(self.cockpit, "_handbacks", [])),
        )
        worker = ConductorWorker(self._conductor, text)
        self._active_worker = worker
        self._pending_tool_calls = []
        worker.signals.response_chunk.connect(self._on_response_chunk)
        worker.signals.response_done.connect(self._on_response_done)
        worker.signals.tool_call.connect(self._on_tool_call)
        worker.signals.tool_calls_done.connect(self._on_tool_calls_done)
        worker.signals.error.connect(self._on_conductor_error)
        self._streaming_started = False
        self._thread_pool.start(worker)

    def _on_response_chunk(self, chunk: str) -> None:
        if not self._streaming_started:
            self.cockpit.append_terminal("")  # blank line before response
            self._streaming_started = True
        cursor = self.cockpit._terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.cockpit._terminal_output.setTextCursor(cursor)
        self.cockpit._terminal_output.ensureCursorVisible()

    def _on_response_done(self, full_text: str) -> None:
        self._active_worker = None

    def _on_conductor_error(self, msg: str) -> None:
        self.cockpit.append_terminal(msg, prefix="!")
        self._active_worker = None

    def _on_zip_for_conductor(self, op: str, ax: str, orr: str, col: str) -> None:
        self._conductor.set_context(zip_tuple=(op, ax, orr, col))

    def _on_handback_for_conductor(self, summary: str, bounds: dict) -> None:
        self._conductor.add_handback(summary, bounds)
```

- [ ] **Step 4: Add the tool call executor**

```python
    def _on_tool_call(self, name: str, args: dict, tool_use_id: str) -> None:
        self._pending_tool_calls.append((name, args, tool_use_id))

    def _on_tool_calls_done(self) -> None:
        worker = self._active_worker
        if worker is None:
            return
        gs = self.canvas.view.grid_spacing
        bounds = self._conductor.last_handback_bounds
        default_color = self.canvas._line_palette.active_color().name()

        has_draws = any(n.startswith("draw_") or n == "fill_region"
                        for n, _, _ in self._pending_tool_calls)
        if has_draws and bounds is None:
            for name, args, tid in self._pending_tool_calls:
                worker.add_tool_result(
                    tid,
                    "no active handback — drag 🍗 onto a zip box first "
                    "to define the working region",
                )
            self.cockpit.append_terminal(
                "(no handback region — drawing blocked)", prefix="!")
            self._pending_tool_calls.clear()
            return

        if has_draws:
            self.canvas.undo_stack.beginMacro("Conductor draw")

        for name, args, tid in self._pending_tool_calls:
            result = self._execute_tool(name, args, gs, bounds, default_color)
            worker.add_tool_result(tid, result)

        if has_draws:
            self.canvas.undo_stack.endMacro()

        self._pending_tool_calls.clear()

    def _execute_tool(self, name: str, args: dict, gs: int,
                      bounds: dict | None, default_color: str) -> str:
        color_hex = args.get("color", default_color)
        pen = QPen(QColor(color_hex))
        pen.setCosmetic(True)
        pen.setWidthF(1.5)

        if name == "draw_line":
            item = QGraphicsLineItem(
                args["x1"] * gs, args["y1"] * gs,
                args["x2"] * gs, args["y2"] * gs,
            )
            item.setPen(pen)
            self.canvas.view.add_item(item)
            return f"line drawn ({args['x1']},{args['y1']})→({args['x2']},{args['y2']})"

        if name == "draw_rect":
            item = QGraphicsRectItem(
                args["x"] * gs, args["y"] * gs,
                args["width"] * gs, args["height"] * gs,
            )
            item.setPen(pen)
            self.canvas.view.add_item(item)
            return f"rect drawn at ({args['x']},{args['y']}) {args['width']}×{args['height']}"

        if name == "draw_circle":
            r = args["radius"] * gs
            cx, cy = args["cx"] * gs, args["cy"] * gs
            item = QGraphicsEllipseItem(cx - r, cy - r, 2 * r, 2 * r)
            item.setPen(pen)
            self.canvas.view.add_item(item)
            return f"circle drawn center ({args['cx']},{args['cy']}) r={args['radius']}"

        if name == "draw_polyline":
            pts = args["points"]
            if len(pts) < 2:
                return "error: need at least 2 points"
            path = QPainterPath(QPointF(pts[0][0] * gs, pts[0][1] * gs))
            for p in pts[1:]:
                path.lineTo(QPointF(p[0] * gs, p[1] * gs))
            if args.get("closed"):
                path.closeSubpath()
            item = QGraphicsPathItem(path)
            item.setPen(pen)
            self.canvas.view.add_item(item)
            return f"polyline drawn with {len(pts)} points" + (" (closed)" if args.get("closed") else "")

        if name == "fill_region":
            self.cockpit.append_terminal(
                f"(fill_region not wired yet — needs paint tool access)", prefix="!")
            return "fill_region is not yet implemented"

        return f"unknown tool: {name}"
```

Note: `fill_region` is stubbed — it requires reaching into the PaintTool's flood-fill internals, which is a deeper integration. The four draw tools are the core of v1.

- [ ] **Step 5: Verify the app launches with the Conductor wired**

```
cd C:\Users\iamja\Desktop\graph-parti
.venv\Scripts\python main.py
```

Without `ANTHROPIC_API_KEY` set: type in the terminal, press Enter → should show `> your text` then `! set ANTHROPIC_API_KEY to enable the Conductor`. Close the app.

- [ ] **Step 6: Commit**

```
git add archideck/host.py
git commit -m "host: wire Conductor to terminal input, zip dial, handback, and canvas tool execution"
```

---

### Task 6: End-to-end smoke test with a real API key

**Files:** None (manual verification)

- [ ] **Step 1: Set the API key and launch**

```
cd C:\Users\iamja\Desktop\graph-parti
set ANTHROPIC_API_KEY=sk-ant-...your-key...
.venv\Scripts\python main.py
```

- [ ] **Step 2: Test free chat (no handback)**

Type into the terminal: `hello, what are you?`

Expected: streaming response appears in the terminal output, identifying itself as the Conductor. No canvas changes.

- [ ] **Step 3: Test chat remembers context**

Type: `what did I just ask you?`

Expected: refers back to the previous question (multi-turn memory working).

- [ ] **Step 4: Test drawing via handback**

1. Drag [Archideck] plate onto the canvas → creates a zip box.
2. Drag 🍗 onto the zip box → copper border + badge + terminal log.
3. Type: `draw a small rectangle in the middle of the handback region`

Expected: a rectangle appears on the canvas within (or near) the zip box's bounds. The terminal shows the streaming response + tool execution.

- [ ] **Step 5: Test undo**

Press Ctrl+Z.

Expected: the rectangle the Conductor drew disappears (single undo step via macro).

- [ ] **Step 6: Test draw rejection without handback**

Restart the app (no handbacks in memory). Type: `draw a circle at 5,5 with radius 2`

Expected: terminal shows `! (no handback region — drawing blocked)`. No canvas changes.

- [ ] **Step 7: Commit (if any fixes were needed)**

```
git add -A
git commit -m "conductor: fix [describe any issue found during smoke test]"
```

---

### Task 7: Update HEY-MR-WILSON.md and INVENTORY.md

**Files:**
- Modify: `C:\Users\iamja\Desktop\graph-parti\HEY-MR-WILSON.md`
- Modify: `C:\Users\iamja\Desktop\graph-parti\INVENTORY.md`

- [ ] **Step 1: Add Conductor to HEY-MR-WILSON.md "Built" section**

Under the `## Built (2026-06-03 · district + place tenure)` section, add a new section:

```markdown
## Built (2026-06-03 · Conductor terminal wiring)
**Conductor (duco) wired to terminal:** Claude Haiku (claude-haiku-4-5-20251001) via Anthropic
SDK. Two-tempo interface: free chat in the terminal (multi-turn) + 🍗 handback to define a
working region, then command drawing within those bounds. Tools: draw_line, draw_rect,
draw_circle, draw_polyline (fill_region stubbed). Undo-integrated (Ctrl-Z undoes Conductor
draws as one macro). Context injection: active zip + handback log + bounding rect. New file:
`archideck/conductor.py`. API key via `ANTHROPIC_API_KEY` env var.
```

- [ ] **Step 2: Add Conductor to INVENTORY.md "Cockpit Wiring (Future)" section**

Change the "Cockpit Wiring (Future)" section to reflect what's now built:

```markdown
### Cockpit Wiring (Built)
- Terminal ↔ Claude Haiku chat (streaming, multi-turn, `archideck/conductor.py`)
- 🍗 handback bounds → Conductor context (draw within the flagged region)
- Tool use: draw_line, draw_rect, draw_circle, draw_polyline (undo-integrated)
- API key: `ANTHROPIC_API_KEY` env var
```

Keep the remaining "Future" items (operators → tool panels, Wilson lasso, canvas-swap, event-logging, minimap) under a separate "Cockpit Wiring (Future)" heading.

- [ ] **Step 3: Commit**

```
git add HEY-MR-WILSON.md INVENTORY.md
git commit -m "docs: record Conductor terminal wiring in teleport + inventory"
```
