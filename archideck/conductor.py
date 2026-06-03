"""The Conductor (duco) — the Archideck's orchestrating agent.

Multi-backend bridge between the cockpit terminal and AI models. Supports:
  - Ollama (localhost:11434, free, local)
  - LM Studio (localhost:1234, free, local)
  - Anthropic API (cloud, requires ANTHROPIC_API_KEY)

Holds conversation history, builds the system prompt with context injection
(active zip + handback log), and defines canvas drawing tools for function
calling. A QRunnable worker runs the API call off the UI thread; signals
carry responses and tool calls back to the main thread.
"""
from __future__ import annotations

import json
import time

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

MAX_TOKENS = 1024

BACKENDS = {
    "ollama": {"base_url": "http://localhost:11434/v1", "api_key": "ollama"},
    "lmstudio": {"base_url": "http://localhost:1234/v1", "api_key": "lm-studio"},
    "anthropic": {"base_url": None, "api_key": None},
}

PERSONA = (
    "You are the Conductor (duco) — the Archideck's orchestrating agent. "
    "You work inside a precision hand-drafting environment called Graph Parti "
    "(PySide6 canvas, square grid, grid units). The architect speaks to you "
    "through the terminal. You can chat freely, and when given a handback "
    "(a flagged region on the canvas), you can draw geometry within its bounds "
    "using your tools. All coordinates are in grid units (1 = 1 grid cell). "
    "Stay concise — the terminal is a single-column text window, not a page."
)

TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "draw_line",
            "description": "Draw a straight line on the canvas. Coordinates in grid units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x1": {"type": "number", "description": "Start X in grid units"},
                    "y1": {"type": "number", "description": "Start Y in grid units"},
                    "x2": {"type": "number", "description": "End X in grid units"},
                    "y2": {"type": "number", "description": "End Y in grid units"},
                    "color": {"type": "string", "description": "Hex color. Omit for default."},
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_rect",
            "description": "Draw a rectangle. x,y = top-left corner in grid units.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "draw_circle",
            "description": "Draw a circle. cx,cy = center in grid units.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "draw_polyline",
            "description": "Draw a polyline (or polygon if closed). Points in grid units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2, "maxItems": 2,
                        },
                        "description": "List of [x, y] points in grid units",
                    },
                    "closed": {"type": "boolean", "description": "Close into polygon", "default": False},
                    "color": {"type": "string", "description": "Hex color. Omit for default."},
                },
                "required": ["points"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_region",
            "description": "Flood-fill a grid cell with color.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "Cell X in grid units"},
                    "y": {"type": "number", "description": "Cell Y in grid units"},
                    "color": {"type": "string", "description": "Fill color hex"},
                },
                "required": ["x", "y", "color"],
            },
        },
    },
]

TOOLS_ANTHROPIC = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOLS_OPENAI
]


def discover_models(backend: str) -> list[str]:
    """Query a running backend for its available models. Returns [] on error."""
    if backend == "anthropic":
        return ["claude-haiku-4-5-20251001", "claude-sonnet-4-6-20250514"]
    try:
        import openai
        cfg = BACKENDS[backend]
        client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
        resp = client.models.list()
        return sorted(m.id for m in resp.data)
    except Exception:
        return []


class Conductor:
    """Manages conversation state + multi-backend API calls."""

    def __init__(self, backend: str = "ollama", model: str = "") -> None:
        self.backend = backend
        self.model = model
        self._client = None
        self._anthropic_client = None
        self.conversation: list[dict] = []
        self.handbacks: list[str] = []
        self.active_zip: tuple = ("", "", "", "")
        self.last_handback_bounds: dict | None = None
        self._connect(backend)

    def _connect(self, backend: str) -> None:
        self.backend = backend
        self._client = None
        self._anthropic_client = None
        if backend == "anthropic":
            import os
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if key:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=key)
        elif backend in BACKENDS:
            import openai
            cfg = BACKENDS[backend]
            self._client = openai.OpenAI(
                base_url=cfg["base_url"], api_key=cfg["api_key"],
            )

    def switch_backend(self, backend: str, model: str = "") -> None:
        self._connect(backend)
        self.model = model
        self.conversation.clear()

    @property
    def available(self) -> bool:
        if self.backend == "anthropic":
            return self._anthropic_client is not None
        return self._client is not None

    @property
    def is_anthropic(self) -> bool:
        return self.backend == "anthropic" and self._anthropic_client is not None

    def set_context(self, zip_tuple=None, handbacks=None, bounds=None) -> None:
        if zip_tuple is not None:
            self.active_zip = zip_tuple
        if handbacks is not None:
            self.handbacks = list(handbacks)
        if bounds is not None:
            self.last_handback_bounds = bounds

    def add_handback(self, summary: str, bounds=None) -> None:
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
    """Runs a single Conductor send() off the UI thread."""

    def __init__(self, conductor: Conductor, user_text: str) -> None:
        super().__init__()
        self.conductor = conductor
        self.user_text = user_text
        self.signals = _WorkerSignals()
        self.setAutoDelete(True)
        self._tool_results: list[dict] = []

    def add_tool_result(self, tool_use_id: str, result: str) -> None:
        self._tool_results.append({
            "tool_call_id": tool_use_id,
            "role": "tool",
            "content": result,
        })

    @Slot()
    def run(self) -> None:
        c = self.conductor
        if not c.available:
            label = "ANTHROPIC_API_KEY" if c.backend == "anthropic" else c.backend
            self.signals.error.emit(
                f"cannot reach {label} — is it running?"
            )
            return
        c.conversation.append({"role": "user", "content": self.user_text})
        try:
            if c.is_anthropic:
                self._call_anthropic(c)
            else:
                self._call_openai(c)
        except Exception as e:
            self.signals.error.emit(str(e))

    # ── OpenAI-compatible backend (Ollama / LM Studio) ──────────────

    def _call_openai(self, c: Conductor) -> None:
        messages = [{"role": "system", "content": c.build_system_prompt()}]
        messages.extend(c.conversation)

        while True:
            full_text = ""
            tool_calls_acc: dict[int, dict] = {}
            try:
                stream = c._client.chat.completions.create(
                    model=c.model,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    tools=TOOLS_OPENAI,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta is None:
                        continue
                    if delta.content:
                        full_text += delta.content
                        self.signals.response_chunk.emit(delta.content)
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {
                                    "id": tc.id or f"call_{idx}",
                                    "name": "",
                                    "arguments": "",
                                }
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_acc[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_acc[idx]["arguments"] += tc.function.arguments
            except Exception as e:
                if "does not support tools" in str(e).lower() or "tool" in str(e).lower():
                    self._call_openai_no_tools(c)
                    return
                raise

            if not tool_calls_acc:
                c.conversation.append({"role": "assistant", "content": full_text})
                self.signals.response_done.emit(full_text)
                return

            assistant_msg = {"role": "assistant", "content": full_text or None, "tool_calls": []}
            tool_uses = []
            for idx in sorted(tool_calls_acc):
                tc = tool_calls_acc[idx]
                assistant_msg["tool_calls"].append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                })
                try:
                    args = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    args = {}
                tool_uses.append({"id": tc["id"], "name": tc["name"], "input": args})

            c.conversation.append(assistant_msg)
            messages.append(assistant_msg)

            self._tool_results.clear()
            for tu in tool_uses:
                self.signals.tool_call.emit(tu["name"], tu["input"], tu["id"])
            self.signals.tool_calls_done.emit()

            deadline = time.monotonic() + 10
            while len(self._tool_results) < len(tool_uses):
                if time.monotonic() > deadline:
                    break
                time.sleep(0.02)

            for tr in self._tool_results:
                tool_msg = {"role": "tool", "tool_call_id": tr["tool_call_id"], "content": tr["content"]}
                c.conversation.append(tool_msg)
                messages.append(tool_msg)

    def _call_openai_no_tools(self, c: Conductor) -> None:
        """Fallback for models that don't support tool use — chat only."""
        messages = [{"role": "system", "content": c.build_system_prompt()}]
        messages.extend(c.conversation)
        full_text = ""
        stream = c._client.chat.completions.create(
            model=c.model,
            messages=messages,
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_text += delta.content
                self.signals.response_chunk.emit(delta.content)
        c.conversation.append({"role": "assistant", "content": full_text})
        self.signals.response_done.emit(full_text)

    # ── Anthropic backend ───────────────────────────────────────────

    def _call_anthropic(self, c: Conductor) -> None:
        while True:
            full_text = ""
            tool_uses: list[dict] = []
            with c._anthropic_client.messages.stream(
                model=c.model,
                max_tokens=MAX_TOKENS,
                system=c.build_system_prompt(),
                messages=c.conversation,
                tools=TOOLS_ANTHROPIC,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            full_text += event.delta.text
                            self.signals.response_chunk.emit(event.delta.text)

            response = stream.get_final_message()
            for block in response.content:
                if block.type == "tool_use":
                    tool_uses.append({"id": block.id, "name": block.name, "input": block.input})

            c.conversation.append({"role": "assistant", "content": response.content})

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
                "content": [
                    {"type": "tool_result", "tool_use_id": tr["tool_call_id"], "content": tr["content"]}
                    for tr in self._tool_results
                ],
            })
