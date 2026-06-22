"""Headless smoke tests for Wave 1 tools."""
from __future__ import annotations

from PySide6.QtCore import QPointF


def test_copy_at_origin_clones_line(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import CopyTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    # Draw a source line from (0,0) to (100,0) = 5 grid units
    src = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    src.setPen(make_pen("#3C3C3C", 1.0))
    src.setFlag(src.GraphicsItemFlag.ItemIsSelectable, True)
    src.setData(0, {"zip": "", "note": ""})
    view.add_item(src)
    src.setSelected(True)

    tool = CopyTool(view)
    tool.activate()

    # Phase 1: click base point at (0, 0)
    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(0, 0))
    # Phase 2: click destination at (0, 60) = 3 cells down
    tool.on_press(QPointF(0, 60))
    tool.on_release(QPointF(0, 60))

    # Should now have 2 lines: original + clone offset by (0, 60)
    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
