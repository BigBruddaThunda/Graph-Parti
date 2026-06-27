"""GRAPH PARTI application entry point."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Enable WinTab API for tablet/stylus support (UGEE M908 and similar EMR tablets).
# Qt6 defaults to Windows Ink which doesn't work with all WinTab-only devices.
# This must be set BEFORE QApplication is created.
os.environ.setdefault("QT_WINTAB_ENABLED", "1")

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow

_FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "VG5000-Regular.otf"
_FONT_FAMILY = "VG5000"
_FONT_SIZE = 10


def install_font(app: QApplication) -> str | None:
    """Load the bundled VG5000 (Velvetyne, OFL) and set it as the app-wide font."""
    fid = QFontDatabase.addApplicationFont(str(_FONT_PATH))
    families = QFontDatabase.applicationFontFamilies(fid) if fid != -1 else []
    if families:
        app.setFont(QFont(families[0], _FONT_SIZE))
        return families[0]
    return None


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GRAPH PARTI")
    app.setOrganizationName("PPL±")
    install_font(app)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
