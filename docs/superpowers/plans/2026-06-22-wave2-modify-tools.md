# Wave 2: Modify Tools — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 modify tools that complete the architectural drafting vocabulary — Join, Fillet, Chamfer, Break, PEDIT (polyline vertex editing).

**Architecture:** These tools operate on existing geometry by computing intersections, splitting paths, and rebuilding QPainterPaths. They all use the existing `_item_segments()` helper, `ReshapeCommand` for undoable geometry changes, and `DeleteItemsCommand`/`AddItemCommand` for item replacement. Each follows the established `Tool` subclass pattern.

**Tech Stack:** Python 3.13 + PySide6 (Qt6 Graphics View). `QLineF.intersects()` for segment intersection. `QPainterPath` for path assembly. `ReshapeCommand` for geometry mutation.

**Build target:** `C:\Users\iamja\Desktop\graph-parti` (branch `master`).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `graphparti/tools.py` | Modify (append 5 classes) | All 5 new tool classes |
| `graphparti/canvas_widget.py` | Modify (import + register) | Wire tools into the UI |
| `tests/test_tools_wave1.py` | Modify (append 5 tests) | Reuse existing test file |

**Existing helpers these tools use:**
- `_item_segments(item)` → line segments from any geometry (tools.py:90)
- `_gs(canvas)` → grid spacing (tools.py:123)
- `make_pen(color, width)` → styled QPen (tools.py:31)
- `_item_from_blueprint(bp, offset)` → reconstruct item from blueprint (tools.py:2160)
- `ExtendTool._pt_seg_dist(p, seg)` → point-to-segment distance (tools.py:920)
- `canvas.pick_item(p)` → topmost selectable item (canvas_view.py:234)
- `canvas._item_blueprint(item)` → extract clonable blueprint (canvas_view.py:1710)
- `canvas._line_segments(item)` → same as `_item_segments` but on canvas (canvas_view.py:499)

**Existing undo patterns:**
- `ReshapeCommand(item, old_geom, new_geom)` — for in-place geometry edits
- `DeleteItemsCommand(document, items)` + `AddItemCommand(layer, item)` — for replace operations
- `us.beginMacro("name")` ... `us.endMacro()` — group into single undo

---

## Task 1: Join Tool

Merge adjacent/overlapping line segments or QGraphicsLineItems into a single QGraphicsPathItem. Select 2+ items, click Join (or press shortcut). Finds endpoints within tolerance and chains them into one path.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
def test_join_merges_two_lines(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
    from graphparti.tools import JoinTool, make_pen

    view, scene, undo = canvas_env

    # Two collinear lines sharing an endpoint at (60, 0)
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

    # Should now have 1 path item (the two lines merged)
    paths = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(paths) == 1, f"Expected 1 joined path, got {len(paths)}"
    # Original lines should be gone
    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 0, f"Expected 0 remaining lines, got {len(lines)}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_join_merges_two_lines -v`

- [ ] **Step 3: Implement JoinTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ join
class JoinTool(Tool):
    """Join selected line segments into a single polyline/path.
    Chains endpoints that are within tolerance."""
    name = "join"

    def on_press(self, p: QPointF) -> None:
        selected = self.canvas.scene().selectedItems()
        selected = [it for it in selected
                    if isinstance(it, (QGraphicsLineItem, QGraphicsPathItem))]
        if len(selected) < 2:
            return

        # Extract all segments from selected items
        all_segs = []
        for it in selected:
            all_segs.extend(_item_segments(it))
        if len(all_segs) < 2:
            return

        tolerance = _gs(self.canvas) * 0.15
        chain = self._chain_segments(all_segs, tolerance)
        if chain is None or len(chain) < 2:
            return

        # Build the joined path
        path = QPainterPath()
        path.moveTo(chain[0])
        for pt in chain[1:]:
            path.lineTo(pt)

        pen = selected[0].pen() if hasattr(selected[0], 'pen') else make_pen("#3C3C3C", 1.0)
        meta = selected[0].data(0) or {"zip": "", "note": ""}

        us = self.canvas.undo_stack
        doc = self.canvas.document
        if us is None or doc is None:
            return
        layer = doc.layer_for(selected[0])
        if layer is None:
            return

        us.beginMacro("Join")
        from .commands import DeleteItemsCommand, AddItemCommand
        us.push(DeleteItemsCommand(doc, selected))
        joined = QGraphicsPathItem(path)
        joined.setPen(pen)
        joined.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        joined.setData(0, dict(meta))
        us.push(AddItemCommand(layer, joined))
        us.endMacro()

    @staticmethod
    def _chain_segments(segs: list[QLineF], tol: float) -> list[QPointF] | None:
        """Greedy nearest-endpoint chaining of line segments into a point list."""
        if not segs:
            return None
        used = [False] * len(segs)
        used[0] = True
        chain = [segs[0].p1(), segs[0].p2()]

        for _ in range(len(segs) - 1):
            tail = chain[-1]
            head = chain[0]
            best_idx = -1
            best_dist = tol
            best_end = 0  # 0=append to tail, 1=prepend to head
            best_flip = False

            for i, seg in enumerate(segs):
                if used[i]:
                    continue
                # Try appending: tail → seg.p1 or tail → seg.p2
                d1 = QLineF(tail, seg.p1()).length()
                d2 = QLineF(tail, seg.p2()).length()
                if d1 < best_dist:
                    best_dist, best_idx, best_end, best_flip = d1, i, 0, False
                if d2 < best_dist:
                    best_dist, best_idx, best_end, best_flip = d2, i, 0, True
                # Try prepending: head → seg.p1 or head → seg.p2
                d3 = QLineF(head, seg.p2()).length()
                d4 = QLineF(head, seg.p1()).length()
                if d3 < best_dist:
                    best_dist, best_idx, best_end, best_flip = d3, i, 1, False
                if d4 < best_dist:
                    best_dist, best_idx, best_end, best_flip = d4, i, 1, True

            if best_idx < 0:
                break
            used[best_idx] = True
            seg = segs[best_idx]
            if best_end == 0:  # append
                chain.append(seg.p2() if not best_flip else seg.p1())
            else:  # prepend
                chain.insert(0, seg.p1() if not best_flip else seg.p2())

        return chain
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_join_merges_two_lines -v`

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `JoinTool` to import.
2. Add `"join": JoinTool(self.view),` to `self._tools`.
3. Add `("join", "Join", "J"),` to toolbar list.

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Join tool — merge line segments into single polyline"
```

---

## Task 2: Fillet Tool

Pick two intersecting lines → compute tangent arc at specified radius → trim lines to tangent points → insert arc. The existing `ExtendTool._fillet_at()` does zero-radius (extend-to-meet); this adds the arc.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

```python
def test_fillet_creates_arc_between_lines(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsPathItem
    from graphparti.tools import FilletTool, make_pen

    view, scene, undo = canvas_env
    gs = view.grid_spacing  # 20

    # Two perpendicular lines meeting at origin
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
    tool._radius = 1.0  # 1 grid unit = 20 scene units

    # Click near the horizontal line, then near the vertical line
    tool.on_press(QPointF(-50, 0))   # first: horizontal
    tool.on_press(QPointF(0, -50))   # second: vertical

    # Should have: 2 trimmed lines + 1 arc path
    arcs = [i for i in scene.items() if isinstance(i, QGraphicsPathItem)]
    assert len(arcs) >= 1, "Expected at least 1 arc path from fillet"
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Implement FilletTool**

```python
# ═══════════════════════════════════════════════════════════ fillet
class FilletTool(Tool):
    """Click two lines near their intersection → round corner with arc of set radius.
    Radius 0 = extend-to-meet (like AutoCAD FILLET R=0)."""
    name = "fillet"

    def reset(self) -> None:
        self._first_item = None
        self._first_pick = None
        self._phase = 0
        if not hasattr(self, '_radius'):
            self._radius = 1.0  # grid units

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def set_dimension(self, value: float) -> None:
        self._radius = value

    def on_press(self, p: QPointF) -> None:
        item = self.canvas.pick_item(p)
        if item is None or not isinstance(item, QGraphicsLineItem):
            return
        if self._phase == 0:
            self._first_item = item
            self._first_pick = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._apply_fillet(self._first_item, item,
                               self._first_pick, QPointF(p))
            self.reset()

    def _apply_fillet(self, item_a, item_b, pick_a, pick_b) -> None:
        gs = _gs(self.canvas)
        r = self._radius * gs

        seg_a = QLineF(item_a.mapToScene(item_a.line().p1()),
                        item_a.mapToScene(item_a.line().p2()))
        seg_b = QLineF(item_b.mapToScene(item_b.line().p1()),
                        item_b.mapToScene(item_b.line().p2()))

        # Find intersection (bounded or unbounded)
        itype, ix_pt = seg_a.intersects(seg_b)
        if itype == QLineF.IntersectionType.NoIntersection:
            return

        us = self.canvas.undo_stack
        if us is None:
            return

        if r < 1e-6:
            # Zero radius = extend-to-meet (same as existing fillet_at)
            us.beginMacro("Fillet R=0")
            from .commands import ReshapeCommand
            old_a = QLineF(item_a.line())
            da1 = QLineF(pick_a, seg_a.p1()).length()
            new_a = QLineF(seg_a.p1(), ix_pt) if da1 < QLineF(pick_a, seg_a.p2()).length() else QLineF(ix_pt, seg_a.p2())
            new_a_l = QLineF(item_a.mapFromScene(new_a.p1()), item_a.mapFromScene(new_a.p2()))
            us.push(ReshapeCommand(item_a, old_a, new_a_l))

            old_b = QLineF(item_b.line())
            db1 = QLineF(pick_b, seg_b.p1()).length()
            new_b = QLineF(seg_b.p1(), ix_pt) if db1 < QLineF(pick_b, seg_b.p2()).length() else QLineF(ix_pt, seg_b.p2())
            new_b_l = QLineF(item_b.mapFromScene(new_b.p1()), item_b.mapFromScene(new_b.p2()))
            us.push(ReshapeCommand(item_b, old_b, new_b_l))
            us.endMacro()
            return

        # Compute fillet arc: find tangent points on each line at distance r from intersection
        angle_a = math.atan2(seg_a.dy(), seg_a.dx())
        angle_b = math.atan2(seg_b.dy(), seg_b.dx())

        # Direction vectors along each line (unit)
        ua = QPointF(math.cos(angle_a), math.sin(angle_a))
        ub = QPointF(math.cos(angle_b), math.sin(angle_b))

        # Determine which side of each line the pick was on
        # to find the correct endpoint direction from intersection
        da1 = QLineF(pick_a, seg_a.p1()).length()
        da2 = QLineF(pick_a, seg_a.p2()).length()
        dir_a = -1.0 if da1 > da2 else 1.0  # toward the far endpoint

        db1 = QLineF(pick_b, seg_b.p1()).length()
        db2 = QLineF(pick_b, seg_b.p2()).length()
        dir_b = -1.0 if db1 > db2 else 1.0

        # Tangent points: intersection + r along each line (away from the pick)
        tp_a = QPointF(ix_pt.x() + dir_a * r * ua.x(),
                       ix_pt.y() + dir_a * r * ua.y())
        tp_b = QPointF(ix_pt.x() + dir_b * r * ub.x(),
                       ix_pt.y() + dir_b * r * ub.y())

        # Arc center: offset r perpendicular from each line, find the common point
        # For simplicity, use the midpoint approach:
        # center = intersection of the two offset lines (perpendicular at distance r)
        perp_a = QPointF(-ua.y(), ua.x())
        perp_b = QPointF(-ub.y(), ub.x())

        # Determine correct perpendicular direction (toward the interior)
        mid = QPointF((tp_a.x() + tp_b.x()) / 2, (tp_a.y() + tp_b.y()) / 2)
        test_a = QPointF(tp_a.x() + r * perp_a.x(), tp_a.y() + r * perp_a.y())
        test_a2 = QPointF(tp_a.x() - r * perp_a.x(), tp_a.y() - r * perp_a.y())
        # Pick the perpendicular direction that's closer to the other tangent point
        if QLineF(test_a, tp_b).length() < QLineF(test_a2, tp_b).length():
            center = test_a
        else:
            center = test_a2

        # Build the arc path from tp_a to tp_b
        arc_path = QPainterPath()
        start_angle = math.degrees(math.atan2(-(tp_a.y() - center.y()),
                                               tp_a.x() - center.x()))
        end_angle = math.degrees(math.atan2(-(tp_b.y() - center.y()),
                                             tp_b.x() - center.x()))
        sweep = end_angle - start_angle
        if sweep > 180:
            sweep -= 360
        elif sweep < -180:
            sweep += 360

        arc_rect = QRectF(center.x() - r, center.y() - r, 2 * r, 2 * r)
        arc_path.arcMoveTo(arc_rect, start_angle)
        arc_path.arcTo(arc_rect, start_angle, sweep)

        us.beginMacro("Fillet")
        from .commands import ReshapeCommand, AddItemCommand

        # Trim line A: keep the segment from the far end to tp_a
        old_a = QLineF(item_a.line())
        if da1 > da2:
            new_a = QLineF(seg_a.p1(), tp_a)
        else:
            new_a = QLineF(tp_a, seg_a.p2())
        new_a_l = QLineF(item_a.mapFromScene(new_a.p1()), item_a.mapFromScene(new_a.p2()))
        us.push(ReshapeCommand(item_a, old_a, new_a_l))

        # Trim line B: keep the segment from tp_b to the far end
        old_b = QLineF(item_b.line())
        if db1 > db2:
            new_b = QLineF(seg_b.p1(), tp_b)
        else:
            new_b = QLineF(tp_b, seg_b.p2())
        new_b_l = QLineF(item_b.mapFromScene(new_b.p1()), item_b.mapFromScene(new_b.p2()))
        us.push(ReshapeCommand(item_b, old_b, new_b_l))

        # Insert the arc
        arc_item = QGraphicsPathItem(arc_path)
        pen = item_a.pen()
        arc_item.setPen(pen)
        arc_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        arc_item.setData(0, {"zip": "", "note": ""})
        layer = self.canvas.document.layer_for(item_a) if self.canvas.document else None
        if layer:
            us.push(AddItemCommand(layer, arc_item))

        us.endMacro()
        self.canvas.viewport().update()
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Register in canvas_widget.py** — import `FilletTool`, add to `_tools` and toolbar
- [ ] **Step 6: Commit**

---

## Task 3: Chamfer Tool

Like Fillet but creates a straight bevel (connecting segment) instead of an arc. Pick two intersecting lines → trim at specified distances → insert connecting line.

**Files:** Same pattern as Task 2.

- [ ] **Step 1: Write the failing test**

```python
def test_chamfer_creates_bevel(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import ChamferTool, make_pen

    view, scene, undo = canvas_env

    # Two perpendicular lines meeting at origin
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
    tool._dist1 = 1.0  # 1 grid unit on first line
    tool._dist2 = 1.0  # 1 grid unit on second line

    tool.on_press(QPointF(-50, 0))
    tool.on_press(QPointF(0, -50))

    # Should now have 3 lines: 2 trimmed originals + 1 chamfer bevel
    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 3, f"Expected 3 lines after chamfer, got {len(lines)}"
```

- [ ] **Step 2-3: Implement ChamferTool**

```python
# ═══════════════════════════════════════════════════════════ chamfer
class ChamferTool(Tool):
    """Click two lines → trim and insert straight bevel at set distances."""
    name = "chamfer"

    def reset(self) -> None:
        self._first_item = None
        self._first_pick = None
        self._phase = 0
        if not hasattr(self, '_dist1'):
            self._dist1 = 1.0  # grid units
        if not hasattr(self, '_dist2'):
            self._dist2 = 1.0

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def set_dimension(self, value: float) -> None:
        self._dist1 = value
        self._dist2 = value

    def on_press(self, p: QPointF) -> None:
        item = self.canvas.pick_item(p)
        if item is None or not isinstance(item, QGraphicsLineItem):
            return
        if self._phase == 0:
            self._first_item = item
            self._first_pick = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._apply_chamfer(self._first_item, item,
                                self._first_pick, QPointF(p))
            self.reset()

    def _apply_chamfer(self, item_a, item_b, pick_a, pick_b) -> None:
        gs = _gs(self.canvas)
        d1 = self._dist1 * gs
        d2 = self._dist2 * gs

        seg_a = QLineF(item_a.mapToScene(item_a.line().p1()),
                        item_a.mapToScene(item_a.line().p2()))
        seg_b = QLineF(item_b.mapToScene(item_b.line().p1()),
                        item_b.mapToScene(item_b.line().p2()))

        itype, ix_pt = seg_a.intersects(seg_b)
        if itype == QLineF.IntersectionType.NoIntersection:
            return

        us = self.canvas.undo_stack
        doc = self.canvas.document
        if us is None or doc is None:
            return

        # Direction vectors
        angle_a = math.atan2(seg_a.dy(), seg_a.dx())
        angle_b = math.atan2(seg_b.dy(), seg_b.dx())
        ua = QPointF(math.cos(angle_a), math.sin(angle_a))
        ub = QPointF(math.cos(angle_b), math.sin(angle_b))

        da1 = QLineF(pick_a, seg_a.p1()).length()
        dir_a = -1.0 if da1 > QLineF(pick_a, seg_a.p2()).length() else 1.0
        db1 = QLineF(pick_b, seg_b.p1()).length()
        dir_b = -1.0 if db1 > QLineF(pick_b, seg_b.p2()).length() else 1.0

        # Chamfer points: offset from intersection along each line
        cp_a = QPointF(ix_pt.x() + dir_a * d1 * ua.x(),
                       ix_pt.y() + dir_a * d1 * ua.y())
        cp_b = QPointF(ix_pt.x() + dir_b * d2 * ub.x(),
                       ix_pt.y() + dir_b * d2 * ub.y())

        us.beginMacro("Chamfer")
        from .commands import ReshapeCommand, AddItemCommand

        old_a = QLineF(item_a.line())
        if da1 > QLineF(pick_a, seg_a.p2()).length():
            new_a = QLineF(seg_a.p1(), cp_a)
        else:
            new_a = QLineF(cp_a, seg_a.p2())
        us.push(ReshapeCommand(item_a, old_a,
                QLineF(item_a.mapFromScene(new_a.p1()), item_a.mapFromScene(new_a.p2()))))

        old_b = QLineF(item_b.line())
        if db1 > QLineF(pick_b, seg_b.p2()).length():
            new_b = QLineF(seg_b.p1(), cp_b)
        else:
            new_b = QLineF(cp_b, seg_b.p2())
        us.push(ReshapeCommand(item_b, old_b,
                QLineF(item_b.mapFromScene(new_b.p1()), item_b.mapFromScene(new_b.p2()))))

        # Insert the bevel line
        bevel = QGraphicsLineItem(QLineF(cp_a, cp_b))
        bevel.setPen(item_a.pen())
        bevel.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        bevel.setData(0, {"zip": "", "note": ""})
        layer = doc.layer_for(item_a)
        if layer:
            us.push(AddItemCommand(layer, bevel))

        us.endMacro()
        self.canvas.viewport().update()
```

- [ ] **Step 4-6: Test, register, commit**

---

## Task 4: Break Tool

Click an item, click a point on it → split at that point into two items.

- [ ] **Step 1: Write the failing test**

```python
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
    tool.on_press(QPointF(50, 0))  # click midpoint

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 2, f"Expected 2 lines after break, got {len(lines)}"
```

- [ ] **Step 2-3: Implement BreakTool**

```python
# ═══════════════════════════════════════════════════════════ break
class BreakTool(Tool):
    """Click on a line/path → split at the nearest point into two items."""
    name = "break"

    def on_press(self, p: QPointF) -> None:
        item = self.canvas.pick_item(p)
        if item is None:
            return
        doc = self.canvas.document
        us = self.canvas.undo_stack
        if doc is None or us is None:
            return

        if isinstance(item, QGraphicsLineItem):
            self._break_line(item, p, doc, us)
        elif isinstance(item, QGraphicsPathItem):
            self._break_path(item, p, doc, us)

    def _break_line(self, item, click, doc, us) -> None:
        ln = item.line()
        p1 = item.mapToScene(ln.p1())
        p2 = item.mapToScene(ln.p2())
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        lsq = dx * dx + dy * dy
        if lsq < 1e-12:
            return
        t = max(0.01, min(0.99, ((click.x() - p1.x()) * dx + (click.y() - p1.y()) * dy) / lsq))
        split = QPointF(p1.x() + t * dx, p1.y() + t * dy)

        pen = item.pen()
        meta = item.data(0) or {"zip": "", "note": ""}
        layer = doc.layer_for(item)
        if layer is None:
            return

        us.beginMacro("Break")
        from .commands import DeleteItemsCommand, AddItemCommand
        us.push(DeleteItemsCommand(doc, [item]))

        l1 = QGraphicsLineItem(QLineF(p1, split))
        l1.setPen(pen)
        l1.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        l1.setData(0, dict(meta))
        us.push(AddItemCommand(layer, l1))

        l2 = QGraphicsLineItem(QLineF(split, p2))
        l2.setPen(pen)
        l2.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        l2.setData(0, dict(meta))
        us.push(AddItemCommand(layer, l2))
        us.endMacro()

    def _break_path(self, item, click, doc, us) -> None:
        segs = _item_segments(item)
        if not segs:
            return
        # Find closest segment
        best_i, best_d = 0, float('inf')
        for i, seg in enumerate(segs):
            d = ExtendTool._pt_seg_dist(click, seg)
            if d < best_d:
                best_d, best_i = d, i

        pen = item.pen()
        meta = item.data(0) or {"zip": "", "note": ""}
        layer = doc.layer_for(item)
        if layer is None:
            return

        # Split at the break point
        seg = segs[best_i]
        dx, dy = seg.p2().x() - seg.p1().x(), seg.p2().y() - seg.p1().y()
        lsq = dx * dx + dy * dy
        if lsq < 1e-12:
            return
        t = max(0.01, min(0.99, ((click.x() - seg.p1().x()) * dx +
                (click.y() - seg.p1().y()) * dy) / lsq))
        split = QPointF(seg.p1().x() + t * dx, seg.p1().y() + t * dy)

        us.beginMacro("Break")
        from .commands import DeleteItemsCommand, AddItemCommand
        us.push(DeleteItemsCommand(doc, [item]))

        # First half: segments 0..best_i + partial
        if best_i > 0 or t > 0.01:
            path1 = QPainterPath()
            path1.moveTo(segs[0].p1())
            for s in segs[:best_i]:
                path1.lineTo(s.p2())
            path1.lineTo(split)
            p1 = QGraphicsPathItem(path1)
            p1.setPen(pen)
            p1.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            p1.setData(0, dict(meta))
            us.push(AddItemCommand(layer, p1))

        # Second half: partial + segments best_i+1..end
        if best_i < len(segs) - 1 or t < 0.99:
            path2 = QPainterPath()
            path2.moveTo(split)
            path2.lineTo(seg.p2())
            for s in segs[best_i + 1:]:
                path2.lineTo(s.p2())
            p2_item = QGraphicsPathItem(path2)
            p2_item.setPen(pen)
            p2_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            p2_item.setData(0, dict(meta))
            us.push(AddItemCommand(layer, p2_item))

        us.endMacro()
```

- [ ] **Step 4-6: Test, register (`"break_at"`, `"Break"`, `""`)**, commit

---

## Task 5: PEDIT (Polyline Edit) Tool

Select a QGraphicsPathItem → show draggable vertex handles → drag to move vertices → right-click a handle to delete vertex → double-click segment midpoint to insert vertex.

- [ ] **Step 1: Write the failing test**

```python
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

    # The tool should have found 3 vertices
    assert len(tool._handles) == 3, f"Expected 3 handles, got {len(tool._handles)}"

    # Simulate dragging vertex 1 (60,0) to (80,0)
    tool._drag_vertex(1, QPointF(80, 0))

    # Verify the path was updated
    new_path = item.path()
    el = new_path.elementAt(1)
    assert abs(el.x - 80) < 1, f"Expected vertex 1 x=80, got {el.x}"
```

- [ ] **Step 2-3: Implement PEditTool**

```python
# ═══════════════════════════════════════════════════════════ polyline edit
class PEditTool(Tool):
    """Select a path → show vertex handles. Drag = move vertex.
    Right-click handle = delete vertex. Double-click segment = insert vertex."""
    name = "pedit"

    def reset(self) -> None:
        self._target = None
        self._handles = []
        self._dragging_idx = -1
        self._drag_start = None

    def activate(self) -> None:
        self.reset()
        selected = [i for i in self.canvas.scene().selectedItems()
                    if isinstance(i, QGraphicsPathItem)]
        if selected:
            self._target = selected[0]
            self._build_handles()

    def deactivate(self) -> None:
        self._remove_handles()
        self.reset()

    def _build_handles(self) -> None:
        if self._target is None:
            return
        self._remove_handles()
        path = self._target.path()
        self._handles = []
        for i in range(path.elementCount()):
            el = path.elementAt(i)
            pt = self._target.mapToScene(QPointF(el.x, el.y))
            self._handles.append(pt)

    def _remove_handles(self) -> None:
        self._handles = []

    def _vertices(self) -> list[QPointF]:
        if self._target is None:
            return []
        path = self._target.path()
        return [self._target.mapToScene(QPointF(path.elementAt(i).x, path.elementAt(i).y))
                for i in range(path.elementCount())]

    def on_press(self, p: QPointF) -> None:
        if self._target is None:
            # Try to pick a new target
            item = self.canvas.pick_item(p)
            if isinstance(item, QGraphicsPathItem):
                self._target = item
                self._build_handles()
            return

        # Check if click is near a handle
        gs = _gs(self.canvas)
        for i, hp in enumerate(self._handles):
            if QLineF(p, hp).length() < gs * 0.5:
                self._dragging_idx = i
                self._drag_start = QPointF(hp)
                return

    def on_move(self, p: QPointF) -> None:
        if self._dragging_idx >= 0:
            self._handles[self._dragging_idx] = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if self._dragging_idx >= 0:
            self._drag_vertex(self._dragging_idx, QPointF(p))
            self._dragging_idx = -1
            self._drag_start = None

    def _drag_vertex(self, idx: int, new_pos: QPointF) -> None:
        if self._target is None:
            return
        old_path = QPainterPath(self._target.path())
        new_path = QPainterPath()
        src = self._target.path()
        local_pos = self._target.mapFromScene(new_pos)
        for i in range(src.elementCount()):
            el = src.elementAt(i)
            pt = QPointF(local_pos.x(), local_pos.y()) if i == idx else QPointF(el.x, el.y)
            if i == 0:
                new_path.moveTo(pt)
            else:
                new_path.lineTo(pt)

        us = self.canvas.undo_stack
        if us:
            from .commands import ReshapeCommand
            us.push(ReshapeCommand(self._target, old_path, new_path))
        else:
            self._target.setPath(new_path)
        self._build_handles()

    def paint_preview(self, painter: QPainter) -> None:
        if not self._handles:
            return
        handle_pen = QPen(QColor("#2464E5"))
        handle_pen.setCosmetic(True)
        handle_pen.setWidthF(2.0)
        handle_brush = QBrush(QColor("#2464E5"))
        gs = _gs(self.canvas)
        r = gs * 0.2
        for i, hp in enumerate(self._handles):
            if i == self._dragging_idx:
                painter.setPen(QPen(QColor("#C1140C")))
                painter.setBrush(QBrush(QColor("#C1140C")))
            else:
                painter.setPen(handle_pen)
                painter.setBrush(handle_brush)
            painter.drawEllipse(hp, r, r)
```

- [ ] **Step 4-6: Test, register (`"pedit"`, `"PEdit"`, `""`)**, commit

---

## Task 6: Run Full Suite + Final Commit

- [ ] **Step 1: Run all tests**

```bash
cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py -v
```

Expected: All 12 tests PASS (7 from Wave 1 + 5 from Wave 2).

- [ ] **Step 2: Manual smoke test**

Launch `python main.py` and verify:
- Join: draw two touching lines → select both → Join → one path
- Fillet: draw two lines at an angle → Fillet → rounded corner with arc
- Chamfer: two lines → Chamfer → straight bevel
- Break: click midpoint of a line → splits into two
- PEdit: draw a polyline → select → PEdit → blue handles appear → drag a vertex

- [ ] **Step 3: Commit if needed**
