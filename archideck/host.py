"""Host window: GRAPH PARTI canvas (left) + Archideck cockpit (right), split-pane.

This is the default program. The canvas fills; the cockpit rides on the right at
roughly the architect's Claude-window width. graphparti is embedded, not imported-from.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QColor, QIcon, QPen, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QMainWindow,
    QSplitter,
)

from graphparti.app import install_font
from graphparti.canvas_widget import CanvasWidget

from .conductor import Conductor, ConductorWorker
from .panel import ArchideckPanel

_COCKPIT_W = 560  # ~ the architect's Claude-window width


class HostWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Archideck  ·  GRAPH PARTI")
        # App icon (GP puzzle piece with party hat)
        _icon = os.path.join(os.path.dirname(__file__), os.pardir,
                             "graphparti", "assets", "icons", "gp-icon.png")
        if os.path.exists(_icon):
            self.setWindowIcon(QIcon(_icon))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = CanvasWidget()       # left — fills
        self.cockpit = ArchideckPanel()    # right — portrait cockpit
        # Cockpit zip dial → canvas facets (host wires it; graphparti stays
        # isolated — it receives plain glyph strings, never imports the cockpit).
        self.cockpit.zip_changed.connect(self.canvas.set_facets)
        self.canvas.set_facets(*self.cockpit.current_zip())

        # Canvas 🍗 handback → cockpit log (the district ties into the Archideck).
        self.canvas.view.handback_requested.connect(self.cockpit.receive_handback)

        splitter.addWidget(self.canvas)
        splitter.addWidget(self.cockpit)
        splitter.setStretchFactor(0, 1)    # extra width goes to the canvas
        splitter.setStretchFactor(1, 0)    # cockpit keeps its width
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.setCentralWidget(splitter)
        self.resize(1600, 1000)
        splitter.setSizes([1600 - _COCKPIT_W, _COCKPIT_W])
        self._splitter = splitter

        self._conductor = Conductor(backend="ollama")
        self._thread_pool = QThreadPool.globalInstance()
        self._active_worker = None
        self._shell_proc = None
        self._shell_stdin = None
        self.cockpit.terminal_submitted.connect(self._on_terminal_input)
        self.cockpit.zip_changed.connect(self._on_zip_for_conductor)
        self.canvas.view.handback_with_bounds.connect(self._on_handback_for_conductor)
        self.cockpit._backend_combo.currentTextChanged.connect(self._on_backend_changed)
        self.cockpit._model_combo.currentTextChanged.connect(self._on_model_changed)
        self.cockpit._refresh_models()

    # ── Conductor wiring ──────────────────────────────────────────────

    def _on_backend_changed(self, backend: str) -> None:
        model = self.cockpit.current_model()
        self._conductor.switch_backend(backend, model)
        self.cockpit._refresh_models()
        self.cockpit.append_terminal(f"switched to {backend}", prefix="~")

    def _on_model_changed(self, model: str) -> None:
        self._conductor.model = model

    # ── Shell mode ─────────────────────────────────────────────────

    _SHELL_CMDS = {"claude", "codex", "gsk", "ollama", "lms", "pip", "git",
                   "python", "node", "npm", "npx"}

    def _is_shell(self, text: str) -> bool:
        if text.startswith("!"):
            return True
        first = text.split()[0].lower() if text.strip() else ""
        return first in self._SHELL_CMDS

    def _translate_cmd(self, text: str) -> str:
        """Translate interactive CLI commands into non-interactive equivalents."""
        if text.startswith("!"):
            return text[1:].strip()
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if cmd == "claude":
            if not rest:
                return 'claude -p "hello — what can you do?"'
            if rest.startswith("-") or rest.startswith("/"):
                return text
            return f'claude -p "{rest}"'

        if cmd == "codex":
            if not rest:
                return "codex --help"
            if rest.startswith("exec") or rest.startswith("-") or rest.startswith("/"):
                return text
            return f'codex exec "{rest}"'

        return text

    def _run_shell(self, raw_cmd: str) -> None:
        cmd = self._translate_cmd(raw_cmd)
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._shell_proc = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            cwd=repo_dir,
            env={**os.environ, "PYTHONIOENCODING": "utf-8",
                 "PYTHONUNBUFFERED": "1", "NO_COLOR": "1"},
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self._shell_stdin = self._shell_proc.stdin

        def _stream():
            try:
                for raw in iter(self._shell_proc.stdout.readline, b""):
                    line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
                    if line:
                        self.cockpit.append_terminal(line)
            except Exception:
                pass
            code = self._shell_proc.wait()
            self.cockpit.append_terminal(f"(exit {code})", prefix="~")
            self._shell_proc = None
            self._shell_stdin = None

        threading.Thread(target=_stream, daemon=True).start()

    def _send_to_shell(self, text: str) -> None:
        if self._shell_stdin:
            try:
                self._shell_stdin.write((text + "\n").encode("utf-8"))
                self._shell_stdin.flush()
            except Exception:
                self.cockpit.append_terminal("(shell stdin closed)", prefix="!")

    def _kill_shell(self) -> None:
        proc = getattr(self, "_shell_proc", None)
        if proc is not None:
            proc.terminate()
            self.cockpit.append_terminal("(killed)", prefix="~")

    # ── Terminal input router ────────────────────────────────────

    def _on_terminal_input(self, text: str) -> None:
        self.cockpit.append_terminal(text, prefix=">")

        if getattr(self, "_shell_proc", None) is not None:
            self._send_to_shell(text)
            return

        if self._is_shell(text):
            self._run_shell(text)
            return

        if self._active_worker is not None:
            self.cockpit.append_terminal("(waiting for previous response...)")
            return
        self._conductor.model = self.cockpit.current_model()
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
            self.cockpit.append_terminal("")
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

    def _on_handback_for_conductor(self, summary: str, bounds) -> None:
        self._conductor.add_handback(summary, bounds)

    def _on_tool_call(self, name: str, args, tool_use_id: str) -> None:
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
                    "no active handback — drag \U0001f357 onto a zip box first "
                    "to define the working region",
                )
            self.cockpit.append_terminal(
                "(no handback region — drawing blocked)", prefix="!")
            self._pending_tool_calls.clear()
            return

        if has_draws:
            self.canvas.undo_stack.beginMacro("Conductor draw")

        from PySide6.QtCore import QPointF  # noqa: F811
        for name, args, tid in self._pending_tool_calls:
            result = self._execute_tool(name, args, gs, bounds, default_color)
            worker.add_tool_result(tid, result)

        if has_draws:
            self.canvas.undo_stack.endMacro()

        self._pending_tool_calls.clear()

    def _execute_tool(self, name: str, args, gs: int,
                      bounds, default_color: str) -> str:
        from PySide6.QtCore import QPointF
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
                "(fill_region not wired yet — needs paint tool access)", prefix="!")
            return "fill_region is not yet implemented"

        return f"unknown tool: {name}"


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archideck")
    app.setOrganizationName("PPL±")
    install_font(app)
    window = HostWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
