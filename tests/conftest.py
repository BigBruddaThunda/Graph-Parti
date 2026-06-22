"""Shared fixtures for Graph Parti headless tool tests."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QApplication, QGraphicsScene

_app = None

@pytest.fixture(scope="session", autouse=True)
def qapp():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication([])
    return _app


@pytest.fixture
def canvas_env():
    """A minimal CanvasView + Document + UndoStack wired up for tool testing.

    Returns (view, scene, undo_stack) — tools can be instantiated with `view`.
    Items land on the scene via view.add_item().
    """
    from PySide6.QtGui import QUndoStack
    from graphparti.canvas_view import CanvasView
    from graphparti.document import Document

    scene = QGraphicsScene()
    scene.setSceneRect(QRectF(-10000, -10000, 20000, 20000))
    view = CanvasView(scene, grid_spacing=20, major_every=7)
    doc = Document.default(scene, QRectF(-1000, -800, 2000, 1600))
    view.document = doc
    undo = QUndoStack()
    view.undo_stack = undo
    view._stroke_color = "#3C3C3C"
    view._fill_color = None
    return view, scene, undo
