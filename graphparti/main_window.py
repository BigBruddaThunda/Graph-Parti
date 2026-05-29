"""Main window: hosts the canvas and a status bar. GRAPH PARTI step 1."""
from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsScene, QLabel, QMainWindow

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

        self._zoom_label = QLabel("zoom 100%")
        self.statusBar().addPermanentWidget(self._zoom_label)
        self.statusBar().showMessage(
            "GRAPH PARTI — grid ready · wheel to zoom · middle-drag or space-drag to pan"
        )

        self.view.centerOn(0, 0)

    def on_zoom_changed(self, scale: float) -> None:
        self._zoom_label.setText(f"zoom {scale * 100:.0f}%")
