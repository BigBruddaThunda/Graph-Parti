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


def test_join_merges_two_lines(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
    from graphparti.tools import JoinTool, make_pen

    view, scene, undo = canvas_env

    l1 = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(60, 0)))
    l1.setPen(make_pen("#3C3C3C", 1.0))
    l1.setFlag(l1.GraphicsItemFlag.ItemIsSelectable, True)
    l1.setData(0, {"zip": "", "note": ""})
    view.add_item(l1)

    l2 = QGraphicsLineItem(QLineF(QPointF(60, 0), QPointF(120, 0)))
    l2.setPen(make_pen("#3C3C3C", 1.0))
    l2.setFlag(l2.GraphicsItemFlag.ItemIsSelectable, True)
    l2.setData(0, {"zip": "", "note": ""})
    view.add_item(l2)

    l1.setSelected(True)
    l2.setSelected(True)

    tool = JoinTool(view)
    tool.on_press(QPointF(60, 0))

    paths = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(paths) == 1, f"Expected 1 joined path, got {len(paths)}"
    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 0, f"Expected 0 remaining lines, got {len(lines)}"


def test_fillet_creates_arc_between_lines(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
    from graphparti.tools import FilletTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing

    h_line = QGraphicsLineItem(QLineF(QPointF(-100, 0), QPointF(0, 0)))
    h_line.setPen(make_pen("#3C3C3C", 1.0))
    h_line.setFlag(h_line.GraphicsItemFlag.ItemIsSelectable, True)
    h_line.setData(0, {"zip": "", "note": ""})
    view.add_item(h_line)

    v_line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(0, -100)))
    v_line.setPen(make_pen("#3C3C3C", 1.0))
    v_line.setFlag(v_line.GraphicsItemFlag.ItemIsSelectable, True)
    v_line.setData(0, {"zip": "", "note": ""})
    view.add_item(v_line)

    tool = FilletTool(view)
    tool._radius = 1.0  # 1 grid unit

    tool.on_press(QPointF(-50, 0))
    tool.on_press(QPointF(0, -50))

    arcs = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(arcs) >= 1, "Expected at least 1 arc path from fillet"


def test_chamfer_creates_bevel(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import ChamferTool, make_pen

    view, scene, undo = canvas_env

    h = QGraphicsLineItem(QLineF(QPointF(-100, 0), QPointF(0, 0)))
    h.setPen(make_pen("#3C3C3C", 1.0))
    h.setFlag(h.GraphicsItemFlag.ItemIsSelectable, True)
    h.setData(0, {"zip": "", "note": ""})
    view.add_item(h)

    v = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(0, -100)))
    v.setPen(make_pen("#3C3C3C", 1.0))
    v.setFlag(v.GraphicsItemFlag.ItemIsSelectable, True)
    v.setData(0, {"zip": "", "note": ""})
    view.add_item(v)

    tool = ChamferTool(view)
    tool._dist1 = 1.0
    tool._dist2 = 1.0

    tool.on_press(QPointF(-50, 0))
    tool.on_press(QPointF(0, -50))

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 3, f"Expected 3 lines after chamfer, got {len(lines)}"


def test_break_splits_line_at_point(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import BreakTool, make_pen

    view, scene, undo = canvas_env

    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    line.setData(0, {"zip": "", "note": ""})
    view.add_item(line)

    tool = BreakTool(view)
    tool.on_press(QPointF(50, 0))

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 2, f"Expected 2 lines after break, got {len(lines)}"


def test_pedit_moves_vertex(canvas_env):
    from PySide6.QtGui import QPainterPath
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import PEditTool, make_pen

    view, scene, undo = canvas_env

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(60, 0)
    path.lineTo(60, 60)
    item = QGraphicsPathItem(path)
    item.setPen(make_pen("#3C3C3C", 1.0))
    item.setFlag(item.GraphicsItemFlag.ItemIsSelectable, True)
    item.setData(0, {"zip": "", "note": ""})
    view.add_item(item)
    item.setSelected(True)

    tool = PEditTool(view)
    tool.activate()

    assert len(tool._handles) == 3, f"Expected 3 handles, got {len(tool._handles)}"

    tool._drag_vertex(1, QPointF(80, 0))

    new_path = item.path()
    el = new_path.elementAt(1)
    assert abs(el.x - 80) < 1, f"Expected vertex 1 x=80, got {el.x}"


def test_linear_dim_creates_annotation(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import LinearDimTool

    view, scene, undo = canvas_env
    gs = view.grid_spacing

    tool = LinearDimTool(view)
    tool.on_press(QPointF(0, 0))
    tool.on_press(QPointF(100, 0))
    tool.on_press(QPointF(50, -40))

    dims = [i for i in scene.items()
            if isinstance(i, QGraphicsPathItem) and i.data(1) == "dimension"]
    assert len(dims) == 1, f"Expected 1 dimension, got {len(dims)}"


def test_leader_creates_annotation(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import LeaderTool

    view, scene, undo = canvas_env

    tool = LeaderTool(view)
    tool.on_press(QPointF(100, 100))
    tool.on_press(QPointF(140, 80))
    tool._finish_leader("NOTE")

    leaders = [i for i in scene.items()
               if isinstance(i, QGraphicsPathItem) and i.data(1) == "leader"]
    assert len(leaders) == 1, f"Expected 1 leader, got {len(leaders)}"


def test_hatch_fills_closed_rect(canvas_env):
    from PySide6.QtCore import QRectF
    from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsPathItem
    from graphparti.tools import HatchTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing

    rect = QGraphicsRectItem(QRectF(0, 0, 80, 80))
    rect.setPen(make_pen("#3C3C3C", 1.0))
    rect.setFlag(rect.GraphicsItemFlag.ItemIsSelectable, True)
    rect.setData(0, {"zip": "", "note": ""})
    view.add_item(rect)

    tool = HatchTool(view)
    tool._angle = 45.0
    tool._spacing = 1.0

    tool.on_press(QPointF(40, 40))

    hatches = [i for i in scene.items()
               if isinstance(i, QGraphicsPathItem) and i.data(1) == "hatch_fill"]
    assert len(hatches) >= 1, "Expected at least 1 hatch pattern item"


def test_line_type_dashed(canvas_env):
    from PySide6.QtCore import QLineF, Qt
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import make_pen, set_line_type

    view, scene, undo = canvas_env

    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    view.add_item(line)

    set_line_type(line, "dashed")
    assert line.pen().style() == Qt.PenStyle.DashLine, "Expected DashLine style"

    set_line_type(line, "center")
    assert line.pen().style() == Qt.PenStyle.CustomDashLine, "Expected CustomDashLine for center"

    set_line_type(line, "continuous")
    assert line.pen().style() == Qt.PenStyle.SolidLine, "Expected SolidLine for continuous"
