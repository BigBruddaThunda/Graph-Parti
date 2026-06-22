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


def test_eyedropper_samples_stroke_color(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import EyedropperTool, make_pen

    view, scene, undo = canvas_env
    view._stroke_color = "#3C3C3C"  # initial

    # Place a red line
    red_line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    red_line.setPen(make_pen("#C1140C", 1.0))
    red_line.setFlag(red_line.GraphicsItemFlag.ItemIsSelectable, True)
    red_line.setData(0, {"zip": "", "note": ""})
    view.add_item(red_line)

    tool = EyedropperTool(view)
    tool.on_press(QPointF(50, 0))  # click on the red line

    assert view._stroke_color.upper() == "#C1140C", (
        f"Expected stroke #C1140C, got {view._stroke_color}"
    )


def test_construction_line_creates_long_line(canvas_env):
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import ConstructionLineTool

    view, scene, undo = canvas_env

    tool = ConstructionLineTool(view)
    # Click two points to define direction
    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(0, 0))
    tool.on_press(QPointF(100, 0))
    tool.on_release(QPointF(100, 0))

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)
             and i.data(1) == "construction"]
    assert len(lines) == 1, f"Expected 1 construction line, got {len(lines)}"
    # The line should extend far beyond the two clicked points
    ln = lines[0].line()
    assert ln.length() > 50000, f"Construction line too short: {ln.length()}"


def test_matchprop_copies_pen_color(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import MatchPropTool, make_pen

    view, scene, undo = canvas_env

    # Source line: red
    src = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    src.setPen(make_pen("#C1140C", 1.0))
    src.setFlag(src.GraphicsItemFlag.ItemIsSelectable, True)
    src.setData(0, {"zip": "", "note": ""})
    view.add_item(src)

    # Target line: default grey
    tgt = QGraphicsLineItem(QLineF(QPointF(0, 40), QPointF(100, 40)))
    tgt.setPen(make_pen("#3C3C3C", 1.0))
    tgt.setFlag(tgt.GraphicsItemFlag.ItemIsSelectable, True)
    tgt.setData(0, {"zip": "", "note": ""})
    view.add_item(tgt)

    tool = MatchPropTool(view)
    # Click source (at y=0, on the red line)
    tool.on_press(QPointF(50, 0))
    # Click target (at y=40, on the grey line)
    tool.on_press(QPointF(50, 40))

    assert tgt.pen().color().name() == "#c1140c", (
        f"Expected target pen #c1140c, got {tgt.pen().color().name()}"
    )


def test_polygon_creates_hexagon(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import PolygonTool

    view, scene, undo = canvas_env

    tool = PolygonTool(view)
    tool._sides = 6  # hexagon

    # Click center at origin, drag to radius = 3 grid cells = 60 scene units
    tool.on_press(QPointF(0, 0))
    tool.on_move(QPointF(60, 0))
    tool.on_release(QPointF(60, 0))

    paths = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(paths) >= 1, "Expected at least 1 path item (hexagon)"
    # A hexagon has 6 vertices → moveTo + 5 lineTo + closeSubpath element = 7 elements
    path = paths[0].path()
    assert path.elementCount() == 7, (
        f"Expected 7 path elements for hexagon, got {path.elementCount()}"
    )


def test_array_rect_creates_grid(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import ArrayRectTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    # Source line
    src = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(40, 0)))
    src.setPen(make_pen("#3C3C3C", 1.0))
    src.setFlag(src.GraphicsItemFlag.ItemIsSelectable, True)
    src.setData(0, {"zip": "", "note": ""})
    view.add_item(src)
    src.setSelected(True)

    tool = ArrayRectTool(view)
    tool._rows = 2
    tool._cols = 3
    tool._row_spacing = 2.0  # grid units
    tool._col_spacing = 3.0  # grid units
    tool.activate()
    tool.on_press(QPointF(0, 0))  # trigger the array

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    # 2 rows × 3 cols = 6 total (including original)
    assert len(lines) == 6, f"Expected 6 lines (2x3), got {len(lines)}"

    # Verify undo removes all clones at once
    undo.undo()
    lines_after = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines_after) == 1, f"After undo, expected 1 line, got {len(lines_after)}"


def test_array_polar_creates_ring(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import ArrayPolarTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    # Source line at (60, 0) — 3 cells right of origin
    src = QGraphicsLineItem(QLineF(QPointF(60, 0), QPointF(100, 0)))
    src.setPen(make_pen("#3C3C3C", 1.0))
    src.setFlag(src.GraphicsItemFlag.ItemIsSelectable, True)
    src.setData(0, {"zip": "", "note": ""})
    view.add_item(src)
    src.setSelected(True)

    tool = ArrayPolarTool(view)
    tool._count = 4
    tool._total_angle = 360.0
    tool.activate()
    # Click center at origin
    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(0, 0))

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    # 4 total (original + 3 copies at 90 degree intervals)
    assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
