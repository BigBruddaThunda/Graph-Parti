# Wave 3: Annotation + Render — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 4 tools that enable architectural annotation and render: linear dimensions, leaders, hatch patterns, and line types.

**Architecture:** Dimensions and leaders are compound items (lines + text) emitted as `QGraphicsPathItem` + child `QGraphicsTextItem`. Hatch uses boundary detection (reuses PaintTool's barrier-rendering approach) then fills with clipped parallel lines. Line types extend the existing `QPen` with custom dash patterns.

**Tech Stack:** Python 3.13 + PySide6 (Qt6). `QPainterPath.arcTo()` for arrowheads. `QImage` + flood fill for boundary detection. `QPen.setDashPattern()` for line types.

**Build target:** `C:\Users\iamja\Desktop\graph-parti` (branch `master`).

---

## Task 1: Linear Dimension Tool

3-click workflow: pick point 1, pick point 2, pick offset direction → emits extension lines + dimension line + centered text showing distance in grid units. All geometry is a single `QGraphicsPathItem` with a child `QGraphicsTextItem`.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

```python
def test_linear_dim_creates_annotation(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import LinearDimTool

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    tool = LinearDimTool(view)
    # Click point 1 at (0, 0)
    tool.on_press(QPointF(0, 0))
    # Click point 2 at (100, 0) = 5 grid units apart
    tool.on_press(QPointF(100, 0))
    # Click offset point above (50, -40) = 2 cells above midpoint
    tool.on_press(QPointF(50, -40))

    dims = [i for i in scene.items()
            if isinstance(i, QGraphicsPathItem) and i.data(1) == "dimension"]
    assert len(dims) == 1, f"Expected 1 dimension, got {len(dims)}"
```

- [ ] **Step 2: Implement LinearDimTool**

```python
# ═══════════════════════════════════════════════════════════ linear dimension
class LinearDimTool(Tool):
    """3-click: pick pt1, pick pt2, pick offset → dimension annotation.
    Emits extension lines + dim line + oblique ticks + centered text."""
    name = "dim_linear"

    _EXT_OFFSET = 0.1    # gap before extension line starts (grid units)
    _EXT_OVERSHOOT = 0.15 # extension line past dim line (grid units)
    _TICK_SIZE = 0.15     # oblique tick length (grid units)
    _TEXT_HEIGHT = 10     # pixels

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
        if self._phase == 3:
            self._create_dimension()
            self.reset()

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def _create_dimension(self) -> None:
        p1, p2, offset_pt = self._pts
        gs = _gs(self.canvas)

        # Determine dimension direction: horizontal or vertical
        # based on which component of offset is larger
        dx_off = offset_pt.x() - (p1.x() + p2.x()) / 2
        dy_off = offset_pt.y() - (p1.y() + p2.y()) / 2

        if abs(dy_off) >= abs(dx_off):
            # Horizontal dimension (measuring X distance, offset in Y)
            dim_y = offset_pt.y()
            ext1_start = QPointF(p1.x(), p1.y() + self._EXT_OFFSET * gs * (1 if dim_y > p1.y() else -1))
            ext1_end = QPointF(p1.x(), dim_y + self._EXT_OVERSHOOT * gs * (1 if dim_y > p1.y() else -1))
            ext2_start = QPointF(p2.x(), p2.y() + self._EXT_OFFSET * gs * (1 if dim_y > p2.y() else -1))
            ext2_end = QPointF(p2.x(), dim_y + self._EXT_OVERSHOOT * gs * (1 if dim_y > p2.y() else -1))
            dim_left = QPointF(p1.x(), dim_y)
            dim_right = QPointF(p2.x(), dim_y)
            measured = abs(p2.x() - p1.x()) / gs
        else:
            # Vertical dimension (measuring Y distance, offset in X)
            dim_x = offset_pt.x()
            ext1_start = QPointF(p1.x() + self._EXT_OFFSET * gs * (1 if dim_x > p1.x() else -1), p1.y())
            ext1_end = QPointF(dim_x + self._EXT_OVERSHOOT * gs * (1 if dim_x > p1.x() else -1), p1.y())
            ext2_start = QPointF(p2.x() + self._EXT_OFFSET * gs * (1 if dim_x > p2.x() else -1), p2.y())
            ext2_end = QPointF(dim_x + self._EXT_OVERSHOOT * gs * (1 if dim_x > p2.x() else -1), p2.y())
            dim_left = QPointF(dim_x, p1.y())
            dim_right = QPointF(dim_x, p2.y())
            measured = abs(p2.y() - p1.y()) / gs

        path = QPainterPath()
        # Extension line 1
        path.moveTo(ext1_start)
        path.lineTo(ext1_end)
        # Extension line 2
        path.moveTo(ext2_start)
        path.lineTo(ext2_end)
        # Dimension line
        path.moveTo(dim_left)
        path.lineTo(dim_right)
        # Oblique ticks at each end (architectural style: 45-degree slash)
        tick = self._TICK_SIZE * gs
        for pt in (dim_left, dim_right):
            path.moveTo(QPointF(pt.x() - tick * 0.5, pt.y() + tick * 0.5))
            path.lineTo(QPointF(pt.x() + tick * 0.5, pt.y() - tick * 0.5))

        pen = QPen(QColor("#3C3C3C"))
        pen.setWidthF(0.5)
        pen.setCosmetic(True)

        item = QGraphicsPathItem(path)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "dimension")

        # Add text as child of the path item
        text = _dim_text(measured)
        txt = QGraphicsTextItem(text, item)
        from .tools import _load_vg5000
        txt.setFont(_load_vg5000(self._TEXT_HEIGHT))
        txt.setDefaultTextColor(QColor("#3C3C3C"))
        mid = QPointF((dim_left.x() + dim_right.x()) / 2,
                      (dim_left.y() + dim_right.y()) / 2)
        txt.setPos(mid.x() - txt.boundingRect().width() / 2,
                   mid.y() - txt.boundingRect().height() - 2)

        self.canvas.add_item(item)

    def paint_preview(self, painter: QPainter) -> None:
        if not self._pts or self._cur is None:
            return
        painter.setPen(self._preview_pen)
        if self._phase == 1 and len(self._pts) == 1:
            painter.drawLine(QLineF(self._pts[0], self._cur))
            gs = _gs(self.canvas)
            d = QLineF(self._pts[0], self._cur).length() / gs
            if d > 0.1:
                _draw_dim_label(painter, self._cur, _dim_text(d))
        elif self._phase == 2 and len(self._pts) == 2:
            # Show preview of where the dim line will go
            painter.drawLine(QLineF(self._pts[0], self._pts[1]))
            painter.drawLine(QLineF(
                QPointF((self._pts[0].x() + self._pts[1].x()) / 2,
                        (self._pts[0].y() + self._pts[1].y()) / 2),
                self._cur))
```

- [ ] **Step 3: Register** — import `LinearDimTool`, add `"dim_linear"` to tools + toolbar as `("dim_linear", "Dim", "")`.
- [ ] **Step 4: Run test, commit** with message `"feat: add Linear Dimension tool — architectural dimension annotations"`

---

## Task 2: Leader Tool

2-click + text: click arrow endpoint, click shoulder point → text input opens → creates arrow + shoulder line + text. Emits as `QGraphicsPathItem` with child `QGraphicsTextItem`.

- [ ] **Step 1: Write the failing test**

```python
def test_leader_creates_annotation(canvas_env):
    from PySide6.QtWidgets import QGraphicsPathItem
    from graphparti.tools import LeaderTool

    view, scene, undo = canvas_env

    tool = LeaderTool(view)
    tool.on_press(QPointF(100, 100))  # arrowhead point
    tool.on_press(QPointF(140, 80))   # shoulder point
    tool._finish_leader("NOTE")       # simulate text entry

    leaders = [i for i in scene.items()
               if isinstance(i, QGraphicsPathItem) and i.data(1) == "leader"]
    assert len(leaders) == 1, f"Expected 1 leader, got {len(leaders)}"
```

- [ ] **Step 2: Implement LeaderTool**

```python
# ═══════════════════════════════════════════════════════════ leader
class LeaderTool(Tool):
    """Click arrowhead point → click shoulder → type text → annotation."""
    name = "leader"

    _ARROW_LEN = 0.3   # grid units
    _ARROW_HALF = 0.1   # grid units, half-width of arrowhead
    _LANDING = 1.0      # grid units, horizontal landing line length

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
            self._finish_leader("—")  # default text; user can edit after

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def _finish_leader(self, text: str) -> None:
        if len(self._pts) < 2:
            return
        arrow_pt, shoulder = self._pts[0], self._pts[1]
        gs = _gs(self.canvas)

        path = QPainterPath()
        # Leader line
        path.moveTo(arrow_pt)
        path.lineTo(shoulder)

        # Arrowhead (filled triangle at arrow_pt)
        d = QLineF(shoulder, arrow_pt)
        if d.length() < 1e-6:
            return
        angle = math.atan2(d.dy(), d.dx())
        al = self._ARROW_LEN * gs
        ah = self._ARROW_HALF * gs
        tip = arrow_pt
        left = QPointF(tip.x() - al * math.cos(angle) - ah * math.sin(angle),
                       tip.y() - al * math.sin(angle) + ah * math.cos(angle))
        right = QPointF(tip.x() - al * math.cos(angle) + ah * math.sin(angle),
                        tip.y() - al * math.sin(angle) - ah * math.cos(angle))
        path.moveTo(tip)
        path.lineTo(left)
        path.lineTo(right)
        path.closeSubpath()

        # Horizontal landing line from shoulder
        landing_dir = 1.0 if shoulder.x() >= arrow_pt.x() else -1.0
        landing_end = QPointF(shoulder.x() + landing_dir * self._LANDING * gs, shoulder.y())
        path.moveTo(shoulder)
        path.lineTo(landing_end)

        pen = QPen(QColor("#3C3C3C"))
        pen.setWidthF(0.5)
        pen.setCosmetic(True)

        item = QGraphicsPathItem(path)
        item.setPen(pen)
        item.setBrush(QBrush(QColor("#3C3C3C")))  # fill the arrowhead
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "leader")

        # Text above the landing line
        txt = QGraphicsTextItem(text, item)
        txt.setFont(_load_vg5000(10))
        txt.setDefaultTextColor(QColor("#3C3C3C"))
        txt.setPos(shoulder.x() + (2 if landing_dir > 0 else -txt.boundingRect().width() - 2),
                   shoulder.y() - txt.boundingRect().height() - 1)

        self.canvas.add_item(item)
        self.reset()

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase == 1 and len(self._pts) == 1 and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawLine(QLineF(self._pts[0], self._cur))
```

NOTE: `_load_vg5000` is defined in tools.py. Verify it's accessible — it's a module-level function. If it's defined inside a class or a conditional, the import `from .tools import _load_vg5000` in the `_finish_leader` can be removed since we're already in tools.py.

- [ ] **Step 3: Register** — `LeaderTool`, `"leader"`, `("leader", "Leader", "")`
- [ ] **Step 4: Run test, commit** — `"feat: add Leader tool — annotation arrows with text"`

---

## Task 3: Hatch Tool

Click inside a closed boundary → fill with parallel line pattern. Uses the PaintTool's barrier-rendering approach for boundary detection, then generates clipped parallel lines at the chosen angle and spacing.

- [ ] **Step 1: Write the failing test**

```python
def test_hatch_fills_closed_rect(canvas_env):
    from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsPathItem
    from graphparti.tools import HatchTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    # Draw a rect to create a closed boundary
    rect = QGraphicsRectItem(QRectF(0, 0, 80, 80))
    rect.setPen(make_pen("#3C3C3C", 1.0))
    rect.setFlag(rect.GraphicsItemFlag.ItemIsSelectable, True)
    rect.setData(0, {"zip": "", "note": ""})
    view.add_item(rect)

    tool = HatchTool(view)
    tool._angle = 45.0
    tool._spacing = 1.0  # 1 grid unit between lines

    # Click inside the rect
    tool.on_press(QPointF(40, 40))

    hatches = [i for i in scene.items()
               if isinstance(i, QGraphicsPathItem) and i.data(1) == "hatch_fill"]
    assert len(hatches) >= 1, "Expected at least 1 hatch pattern item"
```

- [ ] **Step 2: Implement HatchTool**

This is the largest tool. The approach:
1. Render all geometry as barriers into an offscreen QImage (reuse PaintTool's technique)
2. Flood-fill from click point to find the closed region
3. Generate parallel lines at the specified angle + spacing across the bounding box
4. Clip each line to the filled region using per-pixel containment testing
5. Emit all clipped segments as a single QGraphicsPathItem

```python
# ═══════════════════════════════════════════════════════════ hatch
class HatchTool(Tool):
    """Click inside a closed boundary → fill with hatch pattern lines."""
    name = "hatch"

    _FILL_RADIUS = 15  # cells around click to consider

    def reset(self) -> None:
        if not hasattr(self, '_angle'):
            self._angle = 45.0    # degrees
        if not hasattr(self, '_spacing'):
            self._spacing = 0.5   # grid units between lines

    def on_press(self, p: QPointF) -> None:
        gs = _gs(self.canvas)
        # Step 1: Render barriers + flood fill to find boundary (reuse PaintTool approach)
        N = self._FILL_RADIUS
        area_x = math.floor(p.x() / gs) * gs - N * gs
        area_y = math.floor(p.y() / gs) * gs - N * gs
        area_w = (2 * N + 1) * gs
        area_h = (2 * N + 1) * gs
        area = QRectF(area_x, area_y, area_w, area_h)
        iw, ih = int(area_w), int(area_h)

        # Render barriers
        img = QImage(iw, ih, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        barrier_pen = QPen(QColor(1, 0, 1, 255))
        barrier_pen.setWidthF(2.0)
        painter.setPen(barrier_pen)

        # Grid as barriers
        if getattr(self.canvas, '_wireframe', True):
            gx = int(math.ceil(area_x / gs) * gs)
            while gx <= area_x + area_w:
                ix = int(gx - area_x)
                painter.drawLine(ix, 0, ix, ih - 1)
                gx += gs
            gy = int(math.ceil(area_y / gs) * gs)
            while gy <= area_y + area_h:
                iy = int(gy - area_y)
                painter.drawLine(0, iy, iw - 1, iy)
                gy += gs

        # Geometry as barriers
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if item.data(1) in ("cell_fill", "div_point", "hatch_fill"):
                    continue
                if not item.sceneBoundingRect().intersects(area):
                    continue
                for seg in _item_segments(item):
                    x1 = seg.p1().x() - area_x
                    y1 = seg.p1().y() - area_y
                    x2 = seg.p2().x() - area_x
                    y2 = seg.p2().y() - area_y
                    painter.drawLine(QLineF(x1, y1, x2, y2))
        painter.end()

        # Flood fill from click point
        fx = max(0, min(int(p.x() - area_x), iw - 1))
        fy = max(0, min(int(p.y() - area_y), ih - 1))
        if img.pixel(fx, fy) != 0:
            for dx_try, dy_try in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)]:
                nx, ny = fx + dx_try, fy + dy_try
                if 0 <= nx < iw and 0 <= ny < ih and img.pixel(nx, ny) == 0:
                    fx, fy = nx, ny
                    break
            else:
                return

        fill_marker = QColor(0, 255, 0, 255).rgba()
        _flood_fill(img, fx, fy, fill_marker)

        # Step 2: Generate parallel hatch lines across the filled region
        angle_rad = math.radians(self._angle)
        spacing_px = max(2, int(self._spacing * gs))
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        diag = math.hypot(iw, ih)
        cx, cy = iw / 2.0, ih / 2.0
        n_lines = int(diag / spacing_px) + 2

        hatch_path = QPainterPath()
        for i in range(-n_lines, n_lines + 1):
            offset = i * spacing_px
            # Line perpendicular offset from center
            ox = cx + offset * (-sin_a)
            oy = cy + offset * cos_a
            # Line endpoints (extend across full diagonal)
            lx1 = ox - diag * cos_a
            ly1 = oy - diag * sin_a
            lx2 = ox + diag * cos_a
            ly2 = oy + diag * sin_a

            # Walk the line and collect "inside" segments
            steps = max(2, int(math.hypot(lx2 - lx1, ly2 - ly1)))
            inside = False
            seg_start = None
            for s in range(steps + 1):
                t = s / steps
                sx = int(lx1 + t * (lx2 - lx1))
                sy = int(ly1 + t * (ly2 - ly1))
                is_in = (0 <= sx < iw and 0 <= sy < ih
                         and img.pixel(sx, sy) == fill_marker)
                if is_in and not inside:
                    seg_start = (lx1 + t * (lx2 - lx1), ly1 + t * (ly2 - ly1))
                    inside = True
                elif not is_in and inside and seg_start is not None:
                    seg_end = (lx1 + t * (lx2 - lx1), ly1 + t * (ly2 - ly1))
                    # Convert back to scene coords
                    hatch_path.moveTo(seg_start[0] + area_x, seg_start[1] + area_y)
                    hatch_path.lineTo(seg_end[0] + area_x, seg_end[1] + area_y)
                    inside = False
            if inside and seg_start is not None:
                seg_end = (lx2, ly2)
                hatch_path.moveTo(seg_start[0] + area_x, seg_start[1] + area_y)
                hatch_path.lineTo(seg_end[0] + area_x, seg_end[1] + area_y)

        if hatch_path.isEmpty():
            return

        item = QGraphicsPathItem(hatch_path)
        pen = QPen(QColor("#3C3C3C"))
        pen.setWidthF(0.5)
        pen.setCosmetic(True)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "hatch_fill")
        self.canvas.add_item(item)
```

- [ ] **Step 3: Register** — `HatchTool`, `"hatch"`, `("hatch", "Hatch", "H")`
- [ ] **Step 4: Run test, commit** — `"feat: add Hatch tool — parallel line pattern fill within boundaries"`

---

## Task 4: Line Type Support

Add a line type system: items can have dash patterns (continuous, dashed, center, hidden, phantom). Add a `_LINE_TYPES` dict to tools.py and a dropdown or cycle-button in the toolbar. Stored via `data(1)` tag and QPen dash pattern.

- [ ] **Step 1: Write the failing test**

```python
def test_line_type_dashed(canvas_env):
    from PySide6.QtCore import QLineF, Qt
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import LineTool, set_line_type

    view, scene, undo = canvas_env

    # Draw a line
    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    line.setPen(view.current_stroke() if hasattr(view, 'current_stroke') else "#3C3C3C")
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    view.add_item(line)

    # Apply "dashed" line type
    set_line_type(line, "dashed")
    assert line.pen().style() == Qt.PenStyle.DashLine, "Expected DashLine style"

    # Apply "center" line type
    set_line_type(line, "center")
    assert line.pen().style() == Qt.PenStyle.CustomDashLine, "Expected custom dash for center"
```

- [ ] **Step 2: Implement line type system**

Add to `graphparti/tools.py` (module-level, near the top after `make_pen`):

```python
LINE_TYPES = {
    "continuous": None,                     # solid (default)
    "dashed":     [8, 4],                   # - - - -
    "hidden":     [4, 4],                   # short dashes
    "center":     [16, 4, 4, 4],            # long-short-long
    "phantom":    [16, 4, 4, 4, 4, 4],      # long-short-short
    "dot":        [2, 4],                   # . . . .
    "dashdot":    [8, 4, 2, 4],             # -.-.-
}


def set_line_type(item, type_name: str) -> None:
    """Apply a named line type to a QGraphicsItem's pen."""
    if not hasattr(item, 'pen') or not hasattr(item, 'setPen'):
        return
    pen = QPen(item.pen())
    pattern = LINE_TYPES.get(type_name)
    if pattern is None:
        pen.setStyle(Qt.PenStyle.SolidLine)
    else:
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([float(v) for v in pattern])
    item.setPen(pen)
```

Then add a line-type cycle button to `canvas_widget.py` toolbar:

In `_build_toolbar()`, after the line palette section, add a line-type cycle button:

```python
        # ── Line type cycle ──
        self._line_type_idx = 0
        self._line_type_names = list(LINE_TYPES.keys())
        self._line_type_btn = QToolButton()
        self._line_type_btn.setText("——")
        self._line_type_btn.setToolTip("Line type: continuous")
        self._line_type_btn.clicked.connect(self._cycle_line_type)
        tb.addWidget(self._line_type_btn)
```

And the method:

```python
    def _cycle_line_type(self) -> None:
        from .tools import LINE_TYPES, set_line_type
        names = list(LINE_TYPES.keys())
        self._line_type_idx = (self._line_type_idx + 1) % len(names)
        name = names[self._line_type_idx]
        self._line_type_btn.setToolTip(f"Line type: {name}")
        labels = {"continuous": "——", "dashed": "- -", "hidden": "··",
                  "center": "—·—", "phantom": "—··—", "dot": "····", "dashdot": "—·"}
        self._line_type_btn.setText(labels.get(name, name))
        self.view._active_line_type = name
        # Apply to selected items
        for item in self.view.scene().selectedItems():
            set_line_type(item, name)
```

- [ ] **Step 3: Run test, commit** — `"feat: add line type system — dashed, center, hidden, phantom patterns"`

---

## Task 5: Integration Test

- [ ] **Step 1: Run all tests**

```bash
cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py -v
```

Expected: All 16 tests pass.

- [ ] **Step 2: Manual smoke test** — verify dim, leader, hatch, line types all work visually.
