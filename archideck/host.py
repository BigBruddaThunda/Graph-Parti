"""Host window: GRAPH PARTI canvas (left) + Archideck cockpit (right), split-pane.

This is the default program. The canvas fills; the cockpit rides on the right at
roughly the architect's Claude-window width. graphparti is embedded, not imported-from.
"""
from __future__ import annotations

import os
import sys

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

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._conductor = Conductor(api_key)
        self._thread_pool = QThreadPool.globalInstance()
        self._active_worker = None
        self.cockpit.terminal_submitted.connect(self._on_terminal_input)
        self.cockpit.zip_changed.connect(self._on_zip_for_conductor)
        self.canvas.view.handback_with_bounds.connect(self._on_handback_for_conductor)

    # ── Conductor wiring ──────────────────────────────────────────────

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
