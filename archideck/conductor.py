"""The Conductor (duco) — the Archideck's orchestrating agent.

Thin bridge between the cockpit terminal and Claude Haiku. Holds conversation
history, builds the system prompt with context injection (active zip + handback
log), and defines canvas drawing tools for function calling. A QRunnable worker
runs the API call off the UI thread; signals carry responses and tool calls
back to the main thread for display and canvas execution.
"""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

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
        "description": "Draw a straight line on the canvas. Coordinates in grid units.",
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
        "description": "Draw a polyline (or polygon if closed). Points in grid units.",
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
        "description": "Flood-fill a grid cell with color. x,y = the cell to fill.",
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
            lines = "\n".join(f"  - \U0001f357 {h}" for h in reversed(self.handbacks))
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
    tool_call = Signal(str, object, str)  # name, args dict, tool_use_id
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

            deadline = time.monotonic() + 10
            while len(self._tool_results) < len(tool_uses):
                if time.monotonic() > deadline:
                    break
                time.sleep(0.02)

            c.conversation.append({
                "role": "user",
                "content": list(self._tool_results),
            })
