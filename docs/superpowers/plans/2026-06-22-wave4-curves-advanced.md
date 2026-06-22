# Wave 4: Curves + Advanced — Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task.

**Goal:** Add 4 tools — spline/bezier curves, crossing select, stretch, and area/distance inquiry.

**Architecture:** Spline uses Catmull-Rom → cubic Bezier conversion via `QPainterPath.cubicTo()`. Crossing select extends SelectTool's band-select to include items that touch (not just fully inside) the selection rectangle. Stretch moves a subset of vertices. Distance/Area are single-click measurement tools.

**Build target:** `C:\Users\iamja\Desktop\graph-parti` (branch `master`).

---

## Task 1: Spline/Bezier Curve Tool

Click to place points, double-click to finish. Curve passes through all clicked points using Catmull-Rom interpolation converted to cubic Bezier segments.

- [ ] **Test**

```python
def test_spline_creates_smooth_curve(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import SplineTool

    view, scene, undo = canvas_env

    tool = SplineTool(view)
    tool.on_press(QPointF(0, 0))
    tool.on_press(QPointF(40, -30))
    tool.on_press(QPointF(80, 0))
    tool.on_press(QPointF(120, -30))
    tool.on_double_click(QPointF(120, -30))

    paths = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(paths) >= 1, "Expected at least 1 spline path"
    # Cubic bezier produces more elements than just lineTo (cubicTo = 3 elements each)
    path = paths[0].path()
    assert path.elementCount() > 4, f"Expected cubic elements, got {path.elementCount()}"
```

- [ ] **Implementation**

```python
# ═══════════════════════════════════════════════════════════ spline
class SplineTool(Tool):
    """Click to place points, double-click to finish. Catmull-Rom spline."""
    name = "spline"

    def reset(self) -> None:
        self._points = []
        self._drawing = False
        self._cur = None

    @property
    def in_progress(self) -> bool:
        return self._drawing

    def on_press(self, p: QPointF) -> None:
        self._points.append(QPointF(p))
        self._drawing = True

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def on_double_click(self, p: QPointF) -> None:
        if len(self._points) >= 2:
            self._create_spline()
        self.reset()

    def _create_spline(self) -> None:
        pts = self._points
        path = QPainterPath()
        path.moveTo(pts[0])

        if len(pts) == 2:
            path.lineTo(pts[1])
        elif len(pts) == 3:
            path.quadTo(pts[1], pts[2])
        else:
            for i in range(len(pts) - 1):
                p0 = pts[max(i - 1, 0)]
                p1 = pts[i]
                p2 = pts[min(i + 1, len(pts) - 1)]
                p3 = pts[min(i + 2, len(pts) - 1)]
                cp1 = QPointF(p1.x() + (p2.x() - p0.x()) / 6.0,
                              p1.y() + (p2.y() - p0.y()) / 6.0)
                cp2 = QPointF(p2.x() - (p3.x() - p1.x()) / 6.0,
                              p2.y() - (p3.y() - p1.y()) / 6.0)
                path.cubicTo(cp1, cp2, p2)

        self._commit(QGraphicsPathItem(path))

    def paint_preview(self, painter: QPainter) -> None:
        if not self._drawing or not self._points:
            return
        painter.setPen(self._preview_pen)
        pts = list(self._points)
        if self._cur is not None:
            pts.append(self._cur)
        if len(pts) < 2:
            return
        # Draw preview as polyline through points (approximate)
        for a, b in zip(pts, pts[1:]):
            painter.drawLine(QLineF(a, b))
        # Draw point markers
        gs = _gs(self.canvas)
        r = gs * 0.15
        for pt in self._points:
            painter.drawEllipse(pt, r, r)
```

- [ ] **Register** — `SplineTool`, `"spline"`, `("spline", "Spline", "")`
- [ ] **Commit** — `"feat: add Spline tool — Catmull-Rom smooth curves through clicked points"`

---

## Task 2: Crossing Select Mode

When band-selecting right-to-left (crossing), select items that TOUCH the rectangle, not just items fully inside it. Left-to-right remains window select (fully inside only). This modifies `SelectTool` behavior, not a new tool.

- [ ] **Test**

```python
def test_crossing_select_picks_touching_items(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import SelectTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing

    # A line that extends beyond the selection rect
    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(200, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    line.setData(0, {"zip": "", "note": ""})
    view.add_item(line)

    tool = SelectTool(view)
    view.set_tool(tool)

    # Right-to-left band select (crossing): rect covers only part of the line
    tool.on_press(QPointF(100, -20))
    tool.on_move(QPointF(50, 20))
    tool.on_release(QPointF(50, 20))

    selected = scene.selectedItems()
    assert len(selected) == 1, f"Crossing select should pick the touching line, got {len(selected)}"
```

- [ ] **Implementation** — Modify `SelectTool.on_release` in tools.py. The current band-select uses `scene.items(rect, Qt.ItemSelectionMode.ContainsItemShape)`. When the drag goes right-to-left (end.x < start.x), switch to `Qt.ItemSelectionMode.IntersectsItemShape`.

Find the band-select logic in `SelectTool.on_release` and add the crossing mode:

```python
    # In SelectTool.on_release, where the band-select rect is computed:
    # Determine selection mode: left-to-right = window (fully inside),
    # right-to-left = crossing (intersects/touches)
    if end.x() < start.x():
        mode = Qt.ItemSelectionMode.IntersectsItemShape  # crossing
    else:
        mode = Qt.ItemSelectionMode.ContainsItemShape    # window
    candidates = self.canvas.scene().items(rect, mode)
```

- [ ] **Register** — No registration needed (modifies existing SelectTool)
- [ ] **Commit** — `"feat: add crossing select — right-to-left band selects touching items"`

---

## Task 3: Stretch Tool

Select items with a crossing window, then drag → moves only the vertices that fall inside the window. Works on lines and paths.

- [ ] **Test**

```python
def test_stretch_moves_partial_vertices(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import StretchTool, make_pen

    view, scene, undo = canvas_env

    # Horizontal line from (0,0) to (100,0)
    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    line.setData(0, {"zip": "", "note": ""})
    view.add_item(line)

    tool = StretchTool(view)
    # Phase 1: crossing window around the right endpoint only (80-120, -20 to 20)
    tool.on_press(QPointF(120, -20))
    tool.on_move(QPointF(80, 20))
    tool.on_release(QPointF(80, 20))
    # Phase 2: drag the stretched vertices right by 40 units
    tool.on_press(QPointF(100, 0))
    tool.on_release(QPointF(140, 0))

    # The line's p2 should have moved from (100,0) to (140,0)
    ln = line.line()
    p2 = line.mapToScene(ln.p2())
    assert abs(p2.x() - 140) < 2, f"Expected p2.x ~ 140, got {p2.x()}"
    # p1 should NOT have moved
    p1 = line.mapToScene(ln.p1())
    assert abs(p1.x() - 0) < 2, f"Expected p1.x ~ 0, got {p1.x()}"
```

- [ ] **Implementation**

```python
# ═══════════════════════════════════════════════════════════ stretch
class StretchTool(Tool):
    """Crossing window → drag to move only captured vertices."""
    name = "stretch"

    def reset(self) -> None:
        self._phase = 0  # 0=draw window, 1=pick base, 2=pick destination
        self._window_start = None
        self._window_end = None
        self._captured = []  # list of (item, vertex_index, original_point)
        self._base = None
        self._cur = None

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            self._window_start = QPointF(p)
            self._window_end = QPointF(p)
        elif self._phase == 1:
            self._base = QPointF(p)
            self._phase = 2
        elif self._phase == 2:
            self._apply_stretch(QPointF(p))
            self.reset()

    def on_move(self, p: QPointF) -> None:
        if self._phase == 0 and self._window_start is not None:
            self._window_end = QPointF(p)
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if self._phase == 0 and self._window_start is not None:
            self._window_end = QPointF(p)
            self._capture_vertices()
            if self._captured:
                self._phase = 1
            else:
                self.reset()

    def _capture_vertices(self) -> None:
        rect = QRectF(self._window_start, self._window_end).normalized()
        self._captured = []
        if self.canvas.document is None:
            return
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if isinstance(item, QGraphicsLineItem):
                    ln = item.line()
                    p1 = item.mapToScene(ln.p1())
                    p2 = item.mapToScene(ln.p2())
                    if rect.contains(p1):
                        self._captured.append((item, 0, QPointF(p1)))
                    if rect.contains(p2):
                        self._captured.append((item, 1, QPointF(p2)))
                elif isinstance(item, QGraphicsPathItem):
                    path = item.path()
                    for i in range(path.elementCount()):
                        el = path.elementAt(i)
                        pt = item.mapToScene(QPointF(el.x, el.y))
                        if rect.contains(pt):
                            self._captured.append((item, i, QPointF(pt)))

    def _apply_stretch(self, dest: QPointF) -> None:
        if self._base is None or not self._captured:
            return
        dx = dest.x() - self._base.x()
        dy = dest.y() - self._base.y()
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Stretch")
        from .commands import ReshapeCommand
        processed = set()
        for item, vidx, orig_pt in self._captured:
            item_id = id(item)
            if isinstance(item, QGraphicsLineItem):
                if item_id in processed:
                    continue
                # Collect all vertices for this item
                verts = [(v, o) for it, v, o in self._captured if it is item]
                old_ln = QLineF(item.line())
                p1 = item.mapToScene(old_ln.p1())
                p2 = item.mapToScene(old_ln.p2())
                for v, _ in verts:
                    if v == 0:
                        p1 = QPointF(p1.x() + dx, p1.y() + dy)
                    elif v == 1:
                        p2 = QPointF(p2.x() + dx, p2.y() + dy)
                new_ln = QLineF(item.mapFromScene(p1), item.mapFromScene(p2))
                if us:
                    us.push(ReshapeCommand(item, old_ln, new_ln))
                else:
                    item.setLine(new_ln)
                processed.add(item_id)
            elif isinstance(item, QGraphicsPathItem):
                if item_id in processed:
                    continue
                verts = {v for it, v, o in self._captured if it is item}
                old_path = QPainterPath(item.path())
                new_path = QPainterPath()
                src = item.path()
                for i in range(src.elementCount()):
                    el = src.elementAt(i)
                    if i in verts:
                        pt = QPointF(el.x + dx, el.y + dy)
                    else:
                        pt = QPointF(el.x, el.y)
                    if i == 0:
                        new_path.moveTo(pt)
                    else:
                        new_path.lineTo(pt)
                if us:
                    us.push(ReshapeCommand(item, old_path, new_path))
                else:
                    item.setPath(new_path)
                processed.add(item_id)
        if us:
            us.endMacro()

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase == 0 and self._window_start is not None and self._window_end is not None:
            painter.setPen(self._preview_pen)
            rect = QRectF(self._window_start, self._window_end).normalized()
            painter.drawRect(rect)
        elif self._phase >= 1 and self._base is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawLine(QLineF(self._base, self._cur))
```

- [ ] **Register** — `StretchTool`, `"stretch"`, `("stretch", "Stretch", "")`
- [ ] **Commit** — `"feat: add Stretch tool — move partial vertices within crossing window"`

---

## Task 4: Distance / Area Inquiry Tool

Click two points → persistent dimension readout on canvas. Click a closed polyline/path → show area in grid units squared. Single-click mode.

- [ ] **Test**

```python
def test_measure_shows_distance(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import MeasureTool

    view, scene, undo = canvas_env

    tool = MeasureTool(view)
    tool.on_press(QPointF(0, 0))
    tool.on_press(QPointF(60, 0))

    measures = [i for i in scene.items()
                if isinstance(i, QGraphicsPathItem) and i.data(1) == "measure"]
    assert len(measures) == 1, f"Expected 1 measure annotation, got {len(measures)}"
```

- [ ] **Implementation**

```python
# ═══════════════════════════════════════════════════════════ measure
class MeasureTool(Tool):
    """Click two points → persistent distance annotation on canvas.
    Shows distance in grid units with a thin line."""
    name = "measure"

    def reset(self) -> None:
        self._pts = []
        self._phase = 0
        self._cur = None

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        self._pts.append(QPointF(p))
        self._phase += 1
        if self._phase == 2:
            self._create_measure()
            self.reset()

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def _create_measure(self) -> None:
        p1, p2 = self._pts
        gs = _gs(self.canvas)
        dist = QLineF(p1, p2).length() / gs

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)

        pen = QPen(QColor("#2464E5"))
        pen.setWidthF(0.5)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashLine)

        item = QGraphicsPathItem(path)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "measure")

        mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        txt = QGraphicsTextItem(_dim_text(dist), item)
        txt.setFont(_load_vg5000(10))
        txt.setDefaultTextColor(QColor("#2464E5"))
        txt.setPos(mid.x() - txt.boundingRect().width() / 2,
                   mid.y() - txt.boundingRect().height() - 2)

        self.canvas.add_item(item)

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase == 1 and len(self._pts) == 1 and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawLine(QLineF(self._pts[0], self._cur))
            gs = _gs(self.canvas)
            d = QLineF(self._pts[0], self._cur).length() / gs
            if d > 0.1:
                _draw_dim_label(painter, self._cur, _dim_text(d))
```

- [ ] **Register** — `MeasureTool`, `"measure"`, `("measure", "Measure", "")`
- [ ] **Commit** — `"feat: add Measure tool — persistent distance annotations"`

---

## Task 5: Integration Test

Run all 20 tests, verify everything works.
