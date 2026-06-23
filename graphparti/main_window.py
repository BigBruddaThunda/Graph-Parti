"""Standalone GRAPH PARTI window — embeds the canvas widget.

The Archideck cockpit embeds the same CanvasWidget separately; this window is just
graphparti running on its own (`python -m graphparti` or `python main.py` if wired).
"""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from .canvas_widget import CanvasWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GRAPH PARTI")
        self.resize(1200, 800)
        self.canvas = CanvasWidget(self)
        self.setCentralWidget(self.canvas)

    def closeEvent(self, event):
        if hasattr(self.canvas, '_sound_engine'):
            self.canvas._sound_engine.stop()
        super().closeEvent(event)
