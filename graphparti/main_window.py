"""Main window: canvas + toolbar + status bar. GRAPH PARTI steps 1-2."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QGraphicsScene, QLabel, QMainWindow, QToolBar

from .canvas_view import CanvasView

# A large finite scene that reads as "infinite" at human zoom levels.
_SCENE_HALF = 100_000


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GRAPH PARTI")
        self.resize(1200, 800)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(QRectF(-_SCENE_HALF, -_SCENE_HALF, 2 * _SCENE_HALF, 2 * _SCENE_HALF))
        self.view = CanvasView(self.scene, grid_spacing=20, major_every=5)
        self.setCentralWidget(self.view)

        self._build_toolbar()
        self._build_statusbar()

        self.view.cursor_moved.connect(self._on_cursor_moved)
        self.view.zoom_changed.connect(self._on_zoom_changed)
        self.view.centerOn(0, 0)

    # ------------------------------------------------------------------ chrome
    def _build_toolbar(self) -> None:
        tb = QToolBar("Tools", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        self.snap_action = QAction("Snap", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.setShortcut(QKeySequence("F9"))
        self.snap_action.setToolTip("Snap to grid (F9)")
        self.snap_action.toggled.connect(self.view.set_snap_enabled)
        tb.addAction(self.snap_action)

    def _build_statusbar(self) -> None:
        self._coord_label = QLabel("X 0   Y 0")
        self._snap_label = QLabel("SNAP")
        self._zoom_label = QLabel("zoom 100%")
        for w in (self._coord_label, self._snap_label, self._zoom_label):
            w.setMinimumWidth(90)
            self.statusBar().addPermanentWidget(w)
        self.statusBar().showMessage(
            "GRAPH PARTI — wheel zoom · middle/space-drag pan · F9 snap"
        )

    # ------------------------------------------------------------------ slots
    def _on_cursor_moved(self, p: QPointF, snap_active: bool) -> None:
        self._coord_label.setText(f"X {p.x():.0f}   Y {p.y():.0f}")
        self._snap_label.setText("SNAP" if snap_active else "free")

    def _on_zoom_changed(self, scale: float) -> None:
        self._zoom_label.setText(f"zoom {scale * 100:.0f}%")
