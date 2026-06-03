"""Host window: GRAPH PARTI canvas (left) + Archideck cockpit (right), split-pane.

This is the default program. The canvas fills; the cockpit rides on the right at
roughly the architect's Claude-window width. graphparti is embedded, not imported-from.
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from graphparti.app import install_font
from graphparti.canvas_widget import CanvasWidget

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
