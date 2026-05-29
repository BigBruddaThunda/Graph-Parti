"""Embeddable canvas: the whole GRAPH PARTI drawing surface as one QWidget.

This is the isolation boundary. Both the standalone app and the Archideck cockpit
EMBED this widget; `graphparti` never imports anything from the cockpit side, so the
canvas can never inherit cockpit churn.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QUndoStack
from PySide6.QtWidgets import QGraphicsScene, QLabel, QToolBar, QVBoxLayout, QWidget

from .canvas_view import CanvasView
from .document import Document
from .tools import CircleTool, LineTool, PolylineTool, RectTool, SelectTool

_SCENE_HALF = 100_000
_PAPER = QRectF(-1000, -800, 2000, 1600)


class CanvasWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(-_SCENE_HALF, -_SCENE_HALF, 2 * _SCENE_HALF, 2 * _SCENE_HALF))
        self.view = CanvasView(self.scene, grid_spacing=20, major_every=5)
        self.document = Document.default(self.scene, _PAPER)
        self.view.document = self.document
        self.undo_stack = QUndoStack(self)
        self.view.undo_stack = self.undo_stack

        self._tools = {
            "select": SelectTool(self.view),
            "line": LineTool(self.view),
            "polyline": PolylineTool(self.view),
            "rect": RectTool(self.view),
            "circle": CircleTool(self.view),
        }

        self.toolbar = self._build_toolbar()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.view, 1)

        self._status = QLabel("GRAPH PARTI")
        self._status.setContentsMargins(8, 2, 8, 2)
        layout.addWidget(self._status)

        self._last_coord = "X 0  Y 0"
        self._last_kind = "SNAP"
        self._last_zoom = "100%"
        self.view.cursor_moved.connect(self._on_cursor)
        self.view.zoom_changed.connect(self._on_zoom)
        self.view.centerOn(0, 0)

        self._tool_actions["line"].setChecked(True)
        self.view.set_tool(self._tools["line"])

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar("Tools", self)
        tb.setMovable(False)
        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)
        self._tool_actions: dict[str, QAction] = {}
        for key, label, shortcut in [
            ("select", "Select", "V"), ("line", "Line", "L"),
            ("polyline", "Polyline", "P"), ("rect", "Rect", "R"), ("circle", "Circle", "C"),
        ]:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setShortcut(QKeySequence(shortcut))
            act.setToolTip(f"{label} ({shortcut})")
            act.triggered.connect(lambda _checked, k=key: self._activate_tool(k))
            self._tool_group.addAction(act)
            tb.addAction(act)
            self._tool_actions[key] = act
        tb.addSeparator()
        self.snap_action = QAction("Snap", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.setShortcut(QKeySequence("F9"))
        self.snap_action.toggled.connect(self.view.set_snap_enabled)
        tb.addAction(self.snap_action)
        tb.addSeparator()
        undo_act = self.undo_stack.createUndoAction(self, "Undo")
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        redo_act = self.undo_stack.createRedoAction(self, "Redo")
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        tb.addAction(undo_act)
        tb.addAction(redo_act)
        return tb

    def _activate_tool(self, key: str) -> None:
        self.view.set_tool(self._tools[key])

    def _refresh_status(self) -> None:
        self._status.setText(f"{self._last_coord}   ·   {self._last_kind}   ·   zoom {self._last_zoom}")

    def _on_cursor(self, p: QPointF, kind: str) -> None:
        self._last_coord = f"X {p.x():.0f}  Y {p.y():.0f}"
        self._last_kind = {"grid": "SNAP", "endpoint": "■ end", "midpoint": "▲ mid", "": "free"}.get(kind, "free")
        self._refresh_status()

    def _on_zoom(self, scale: float) -> None:
        self._last_zoom = f"{scale * 100:.0f}%"
        self._refresh_status()
