"""Main window: canvas + tool toolbar + status bar. GRAPH PARTI steps 1-3."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QGraphicsScene, QLabel, QMainWindow, QToolBar

from .canvas_view import CanvasView
from .document import Document
from .tools import CircleTool, LineTool, PolylineTool, RectTool

_SCENE_HALF = 100_000
_PAPER = QRectF(-1000, -800, 2000, 1600)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GRAPH PARTI")
        self.resize(1200, 800)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(-_SCENE_HALF, -_SCENE_HALF, 2 * _SCENE_HALF, 2 * _SCENE_HALF))
        self.view = CanvasView(self.scene, grid_spacing=20, major_every=5)
        self.setCentralWidget(self.view)

        self.document = Document.default(self.scene, _PAPER)
        self.view.document = self.document

        self._tools = {
            "line": LineTool(self.view),
            "polyline": PolylineTool(self.view),
            "rect": RectTool(self.view),
            "circle": CircleTool(self.view),
        }

        self._build_toolbar()
        self._build_statusbar()
        self.view.cursor_moved.connect(self._on_cursor_moved)
        self.view.zoom_changed.connect(self._on_zoom_changed)
        self.view.centerOn(0, 0)

        self._tool_actions["line"].setChecked(True)
        self.view.set_tool(self._tools["line"])

    # ------------------------------------------------------------------ chrome
    def _build_toolbar(self) -> None:
        tb = QToolBar("Tools", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)
        self._tool_actions: dict[str, QAction] = {}
        for key, label, shortcut in [
            ("line", "Line", "L"),
            ("polyline", "Polyline", "P"),
            ("rect", "Rect", "R"),
            ("circle", "Circle", "C"),
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
        self.snap_action.setToolTip("Snap to grid (F9)")
        self.snap_action.toggled.connect(self.view.set_snap_enabled)
        tb.addAction(self.snap_action)

    def _activate_tool(self, key: str) -> None:
        self.view.set_tool(self._tools[key])
        self.statusBar().showMessage(f"{key} tool", 1500)

    def _build_statusbar(self) -> None:
        self._coord_label = QLabel("X 0   Y 0")
        self._snap_label = QLabel("SNAP")
        self._zoom_label = QLabel("zoom 100%")
        for w in (self._coord_label, self._snap_label, self._zoom_label):
            w.setMinimumWidth(90)
            self.statusBar().addPermanentWidget(w)
        self.statusBar().showMessage(
            "GRAPH PARTI — pick a tool · left-drag to draw · F9 snap · middle/space-drag pan"
        )

    # ------------------------------------------------------------------ slots
    def _on_cursor_moved(self, p: QPointF, kind: str) -> None:
        self._coord_label.setText(f"X {p.x():.0f}   Y {p.y():.0f}")
        label = {"grid": "SNAP", "endpoint": "■ end", "midpoint": "▲ mid", "": "free"}
        self._snap_label.setText(label.get(kind, "free"))

    def _on_zoom_changed(self, scale: float) -> None:
        self._zoom_label.setText(f"zoom {scale * 100:.0f}%")
