"""GRAPH PARTI application entry point."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def run() -> int:
    """Create the QApplication, show the main window, and run the event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("GRAPH PARTI")
    app.setOrganizationName("PPL±")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
