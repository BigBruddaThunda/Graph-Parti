"""Host window: GRAPH PARTI canvas (left) + Archideck cockpit (right), split-pane.

This is the default program. The canvas fills; the cockpit rides on the right at
roughly the architect's Claude-window width. graphparti is embedded, not imported-from.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from graphparti.app import install_font
from graphparti.canvas_widget import CanvasWidget

from .panel import ArchideckPanel

_COCKPIT_W = 560  # ~ the architect's Claude-window width


class HostWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Archideck  ·  GRAPH PARTI")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.canvas = CanvasWidget()       # left — fills
        self.cockpit = ArchideckPanel()    # right — portrait cockpit
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
