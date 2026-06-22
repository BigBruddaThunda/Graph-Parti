# Wave 1: Daily Workflow Tools — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 7 trivial tools that unblock the architect's daily drafting workflow — copy-at-origin, eyedropper, construction lines, property match, polygon, array rectangular, array polar.

**Architecture:** All 7 tools follow the identical pattern already established in `tools.py`: subclass `Tool`, implement `on_press`/`on_move`/`on_release`/`paint_preview`, call `self._commit(item)` to emit geometry. Each tool is registered in `canvas_widget.py`'s `_tools` dict and toolbar list. No new files, no new subsystems — pure additions to two existing files.

**Tech Stack:** Python 3.13 + PySide6 (Qt6 Graphics View). `QGraphicsLineItem`, `QGraphicsPathItem`, `QGraphicsEllipseItem` for geometry. `QPainterPath` for compound shapes. `QUndoStack` macros for multi-item operations.

**Build target:** `C:\Users\iamja\Desktop\graph-parti` (branch `master` — the live build canvas).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `graphparti/tools.py` | Modify (append 7 classes at end) | All 7 new tool classes |
| `graphparti/canvas_widget.py` | Modify (import + register + toolbar) | Wire tools into the UI |
| `tests/test_tools_wave1.py` | Create | Headless smoke tests (offscreen QApplication) |

**Pattern to follow (every tool):**
1. Add class to `tools.py` after `CellTextTool` (line ~2097)
2. Add import to `canvas_widget.py` line 17-21
3. Add entry to `self._tools` dict (line 264-282)
4. Add entry to toolbar builder list (line 431-441)

**Existing helpers each tool may use:**
- `_gs(canvas)` → grid spacing in scene units (line 123)
- `make_pen(color, width)` → styled QPen (line 31)
- `_draw_dim_label(painter, pt, text)` → floating dimension text (line 60)
- `_item_segments(item)` → extract line segments from any geometry item (line 89)
- `self._commit(item)` → set pen, brush, flags, data, push to undo stack (line 195)
- `self._apply_ortho(start, p)` → ortho constraint if enabled (line 188)
- `self.canvas.pick_item(p)` → topmost selectable item at point, layer-aware (canvas_view:234)
- `self.canvas._item_blueprint(item)` → extract clonable blueprint (canvas_view:1710)
- `self.canvas._paste_geometry()` → paste from internal clipboard (canvas_view:1747)

**Existing undo patterns:**
- Single item: `self._commit(item)` (pushes `AddItemCommand`)
- Multi-item: `us.beginMacro("name")` ... `self.canvas.add_item(item)` ... `us.endMacro()`
- Delete: `DeleteItemsCommand(document, items)` via `commands.py:47`

---

## Task 1: Test Scaffold

**Files:**
- Create: `tests/test_tools_wave1.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

The existing codebase has no tests. Set up the minimal infrastructure for headless PySide6 tool testing.

- [ ] **Step 1: Create test directory and init**

```bash
mkdir -p C:\Users\iamja\Desktop\graph-parti\tests
```

- [ ] **Step 2: Create conftest.py with shared fixtures**

Write `tests/conftest.py`:

```python
"""Shared fixtures for Graph Parti headless tool tests."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QApplication, QGraphicsScene

# One QApplication for the entire test session (PySide6 requires exactly one)
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
```

- [ ] **Step 3: Create empty test file**

Write `tests/__init__.py` (empty) and `tests/test_tools_wave1.py`:

```python
"""Headless smoke tests for Wave 1 tools."""
from __future__ import annotations

from PySide6.QtCore import QPointF

# Tests will be added per-task below.
```

- [ ] **Step 4: Verify pytest can discover the fixtures**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/ --collect-only`

Expected: `tests/test_tools_wave1.py` collected, 0 tests (no test functions yet).

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: add headless test scaffold for Wave 1 tool testing"
```

---

## Task 2: Copy at Origin Tool

AutoCAD-style copy: select items, click base point, click destination — cloned items land at the offset. Reuses the existing `_item_blueprint` / paste machinery in `canvas_view.py`.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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

    # Phase 0: tool picks up selected items
    # Phase 1: click base point at (0, 0)
    tool.on_press(QPointF(0, 0))
    tool.on_release(QPointF(0, 0))
    # Phase 2: click destination at (0, 60) = 3 cells down
    tool.on_press(QPointF(0, 60))
    tool.on_release(QPointF(0, 60))

    # Should now have 2 lines: original + clone offset by (0, 60)
    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_copy_at_origin_clones_line -v`

Expected: FAIL with `ImportError: cannot import name 'CopyTool'`

- [ ] **Step 3: Implement CopyTool**

Append to `graphparti/tools.py` after the `CellTextTool` class (after line ~2097):

```python
# ═══════════════════════════════════════════════════════════ copy at origin
class CopyTool(Tool):
    """AutoCAD-style COPY: select → base point → destination(s). Escape exits."""
    name = "copy"

    def reset(self) -> None:
        self._base = None
        self._blueprints = []
        self._phase = 0  # 0=grab selection, 1=pick base, 2=pick destinations

    def activate(self) -> None:
        self.reset()
        items = self.canvas.scene().selectedItems()
        if not items:
            return
        self._blueprints = []
        for it in items:
            bp = self.canvas._item_blueprint(it)
            if bp:
                self._blueprints.append(bp)
        if self._blueprints:
            self._phase = 1  # waiting for base point

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        if self._phase == 1:
            self._base = QPointF(p)
            self._phase = 2
        elif self._phase == 2:
            self._place_copies(QPointF(p))

    def _place_copies(self, dest: QPointF) -> None:
        if self._base is None or not self._blueprints:
            return
        offset = dest - self._base
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Copy")
        for bp in self._blueprints:
            item = _item_from_blueprint(bp, offset)
            if item is not None:
                self.canvas.add_item(item)
        if us:
            us.endMacro()

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase == 2 and self._base is not None and hasattr(self, '_cur'):
            painter.setPen(self._preview_pen)
            painter.drawLine(QLineF(self._base, self._cur))


def _item_from_blueprint(bp, offset: QPointF):
    """Reconstruct a QGraphicsItem from a blueprint tuple, shifted by offset."""
    item = None
    if bp[0] == "line":
        ln = bp[1]
        item = QGraphicsLineItem(QLineF(
            QPointF(ln.p1().x() + offset.x(), ln.p1().y() + offset.y()),
            QPointF(ln.p2().x() + offset.x(), ln.p2().y() + offset.y())))
    elif bp[0] == "rect":
        item = QGraphicsRectItem(bp[1].translated(offset))
    elif bp[0] == "ellipse":
        item = QGraphicsEllipseItem(bp[1].translated(offset))
    elif bp[0] == "path":
        sp = QPainterPath()
        src = bp[1]
        for i in range(src.elementCount()):
            el = src.elementAt(i)
            pt = QPointF(el.x + offset.x(), el.y + offset.y())
            if i == 0:
                sp.moveTo(pt)
            else:
                sp.lineTo(pt)
        item = QGraphicsPathItem(sp)
    if item is not None:
        if bp[2]:  # pen
            item.setPen(bp[2])
        if len(bp) > 4 and bp[4] and hasattr(item, 'setBrush'):
            item.setBrush(bp[4])
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, dict(bp[3]) if bp[3] else {"zip": "", "note": ""})
    return item
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_copy_at_origin_clones_line -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

In `graphparti/canvas_widget.py`:

1. Add `CopyTool` to the import (line 17-21):
```python
from .tools import (
    ArcTool, CellTextTool, CircleTool, CopyTool, DivideTool, EllipseTool,
    ExtendTool, LineTool, MirrorTool, OffsetTool, PaintTool, PolylineTool,
    RectTool, RotateTool, ScaleTool, SelectTool, TrimTool, WordTextTool,
)
```

2. Add to `self._tools` dict (after line 281, before the closing `}`):
```python
            "copy": CopyTool(self.view),
```

3. Add to toolbar builder list (line 431-441), after the `("cell", "Cell", "G")` entry:
```python
            ("copy", "Copy", ""),
```

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Copy at Origin tool (AutoCAD-style base+destination copy)"
```

---

## Task 3: Eyedropper Tool

Click any item on the canvas to sample its color. Left-click samples fill color (from cell_fill items or brush), right-click samples stroke color (from pen). Sets the active color in the palette.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_eyedropper_samples_stroke_color -v`

Expected: FAIL with `ImportError: cannot import name 'EyedropperTool'`

- [ ] **Step 3: Implement EyedropperTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ eyedropper
class EyedropperTool(Tool):
    """Click to sample color. Left-click on a fill → set fill color.
    Left-click on geometry → set stroke color."""
    name = "eyedropper"

    def on_press(self, p: QPointF) -> None:
        # Check items at click point (topmost first)
        for item in self.canvas.scene().items(p):
            # Cell fills: sample the fill color
            if item.data(1) == "cell_fill":
                if hasattr(item, 'brush') and item.brush().style() != Qt.BrushStyle.NoBrush:
                    color = item.brush().color().name()
                    self.canvas.set_fill(color)
                    return
                # Pixmap fills: render a pixel and sample
                if isinstance(item, QGraphicsPixmapItem):
                    local = item.mapFromScene(p)
                    pm = item.pixmap()
                    ix = max(0, min(int(local.x()), pm.width() - 1))
                    iy = max(0, min(int(local.y()), pm.height() - 1))
                    c = pm.toImage().pixelColor(ix, iy)
                    if c.alpha() > 0:
                        self.canvas.set_fill(c.name())
                    return
            # Geometry: sample the stroke color
            if hasattr(item, 'pen') and callable(item.pen):
                pen = item.pen()
                if pen.style() != Qt.PenStyle.NoPen:
                    self.canvas.set_stroke(pen.color().name())
                    return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_eyedropper_samples_stroke_color -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `EyedropperTool` to import line.
2. Add `"eyedropper": EyedropperTool(self.view),` to `self._tools`.
3. Add `("eyedropper", "Pick", "I"),` to toolbar list (I for eyedropper/inspector).

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Eyedropper tool — sample stroke/fill color from canvas"
```

---

## Task 4: Construction Line Tool

Click two points to define direction — emits a very long line through both points, styled as a blue dash-dot construction reference. Tagged `data(1)="construction"` so other tools can distinguish it.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_construction_line_creates_long_line -v`

Expected: FAIL with `ImportError: cannot import name 'ConstructionLineTool'`

- [ ] **Step 3: Implement ConstructionLineTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ construction line
class ConstructionLineTool(Tool):
    """Click two points → infinite construction/reference line through both.
    Blue dash-dot, tagged data(1)='construction'."""
    name = "xline"

    _EXTENT = 100_000  # scene units — effectively infinite

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._phase = 0  # 0=pick first, 1=pick second

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            self._start = QPointF(p)
            self._cur = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._create_xline(self._start, QPointF(p))
            # Stay in phase 1 — keep creating lines from the same origin
            # (like AutoCAD XLINE: first click = through-point, keep clicking more)
            self._start = QPointF(p)

    def on_move(self, p: QPointF) -> None:
        if self._phase == 1:
            self._cur = self._apply_ortho(self._start, p)

    def on_release(self, p: QPointF) -> None:
        pass

    def _create_xline(self, p1: QPointF, p2: QPointF) -> None:
        d = QLineF(p1, p2)
        if d.length() < MIN_DRAG:
            return
        # Extend in both directions
        d.setLength(self._EXTENT)
        far_p2 = d.p2()
        d = QLineF(p2, p1)
        d.setLength(self._EXTENT)
        far_p1 = d.p2()

        item = QGraphicsLineItem(QLineF(far_p1, far_p2))
        pen = QPen(QColor("#2464E5"))  # blue construction
        pen.setWidthF(0.5)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashDotLine)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "construction")
        self.canvas.add_item(item)

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase == 1 and self._start is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            d = QLineF(self._start, self._cur)
            if d.length() > MIN_DRAG:
                d.setLength(self._EXTENT)
                far_p2 = d.p2()
                d2 = QLineF(self._cur, self._start)
                d2.setLength(self._EXTENT)
                far_p1 = d2.p2()
                painter.drawLine(QLineF(far_p1, far_p2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_construction_line_creates_long_line -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `ConstructionLineTool` to import.
2. Add `"xline": ConstructionLineTool(self.view),` to `self._tools`.
3. Add `("xline", "XLine", "X"),` to toolbar list. **Note:** X key is currently used for wireframe toggle in `canvas_view.py`. Use `""` (no shortcut) instead to avoid conflict:
   `("xline", "XLine", ""),`

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Construction Line tool (infinite reference lines)"
```

---

## Task 5: Property Match Tool

Click a source item to sample its pen + brush. Then click target items to apply those properties. Right-click or Escape exits. Stays in "apply" mode until cancelled (like AutoCAD MATCHPROP).

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
    # Click source
    tool.on_press(QPointF(50, 0))
    # Click target
    tool.on_press(QPointF(50, 40))

    assert tgt.pen().color().name() == "#c1140c", (
        f"Expected target pen #c1140c, got {tgt.pen().color().name()}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_matchprop_copies_pen_color -v`

Expected: FAIL with `ImportError: cannot import name 'MatchPropTool'`

- [ ] **Step 3: Implement MatchPropTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ property match
class MatchPropTool(Tool):
    """Click source → click targets to copy pen/brush. Escape exits."""
    name = "matchprop"

    def reset(self) -> None:
        self._src_pen = None
        self._src_brush = None
        self._phase = 0  # 0=pick source, 1=apply to targets

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        item = self.canvas.pick_item(p)
        if item is None:
            return

        if self._phase == 0:
            # Sample source properties
            if hasattr(item, 'pen') and callable(item.pen):
                self._src_pen = QPen(item.pen())
            if hasattr(item, 'brush') and callable(item.brush):
                self._src_brush = QBrush(item.brush())
            self._phase = 1
        else:
            # Apply to target
            if self._src_pen is not None and hasattr(item, 'setPen'):
                item.setPen(QPen(self._src_pen))
            if self._src_brush is not None and hasattr(item, 'setBrush'):
                item.setBrush(QBrush(self._src_brush))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_matchprop_copies_pen_color -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `MatchPropTool` to import.
2. Add `"matchprop": MatchPropTool(self.view),` to `self._tools`.
3. Add `("matchprop", "Match", ""),` to toolbar list.

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Property Match tool — copy pen/brush between items"
```

---

## Task 6: Polygon Tool

Click center, drag to set radius and rotation. Tab-type for exact radius. Number of sides set via `on_key` (3-12, default 6). Emits a closed `QGraphicsPathItem`.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
    # A hexagon has 6 vertices → 7 elements in the path (moveTo + 6 lineTo)
    path = paths[0].path()
    assert path.elementCount() == 7, (
        f"Expected 7 path elements for hexagon, got {path.elementCount()}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_polygon_creates_hexagon -v`

Expected: FAIL with `ImportError: cannot import name 'PolygonTool'`

- [ ] **Step 3: Implement PolygonTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ polygon
class PolygonTool(Tool):
    """Regular polygon: click center, drag radius. Sides adjustable (3-12, default 6)."""
    name = "polygon"

    def reset(self) -> None:
        self._center = None
        self._cur = None
        self._drawing = False
        self._dim_locked = False
        self._sides = 6

    @property
    def in_progress(self) -> bool:
        return self._drawing

    def on_press(self, p: QPointF) -> None:
        self._center = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True
        self._dim_locked = False

    def on_move(self, p: QPointF) -> None:
        if self._drawing and not self._dim_locked:
            self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        end = self._cur if self._dim_locked else QPointF(p)
        radius = QLineF(self._center, end).length()
        if radius < MIN_DRAG:
            self.reset()
            return
        angle_to_cursor = math.atan2(end.y() - self._center.y(),
                                     end.x() - self._center.x())
        path = self._make_polygon(self._center, radius, self._sides, angle_to_cursor)
        self._commit(QGraphicsPathItem(path))
        self.reset()

    def set_dimension(self, value: float) -> None:
        gs = _gs(self.canvas)
        if self._drawing and self._center is not None:
            self._cur = QPointF(self._center.x() + value * gs, self._center.y())
            self._dim_locked = True

    @staticmethod
    def _make_polygon(center: QPointF, radius: float, sides: int,
                      start_angle: float = 0.0) -> QPainterPath:
        path = QPainterPath()
        for i in range(sides):
            angle = start_angle + 2.0 * math.pi * i / sides
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        return path

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._center is not None and self._cur is not None:
            radius = QLineF(self._center, self._cur).length()
            if radius < MIN_DRAG:
                return
            angle = math.atan2(self._cur.y() - self._center.y(),
                               self._cur.x() - self._center.x())
            path = self._make_polygon(self._center, radius, self._sides, angle)
            painter.setPen(self._preview_pen)
            painter.drawPath(path)
            gs = _gs(self.canvas)
            _draw_dim_label(painter, self._cur, f"r={_dim_text(radius / gs)} n={self._sides}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_polygon_creates_hexagon -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `PolygonTool` to import.
2. Add `"polygon": PolygonTool(self.view),` to `self._tools`.
3. Add `("polygon", "Polygon", ""),` to toolbar list.

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Polygon tool — regular N-sided polygons (3-12 sides)"
```

---

## Task 7: Array Rectangular Tool

Operates on current selection. Click to set the spacing reference direction, then clones items in a rows × columns grid. Default 3×3, spacing = bounding box size + 1 cell gap. Entire operation is one undo macro.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
    assert len(lines) == 6, f"Expected 6 lines (2×3), got {len(lines)}"

    # Verify undo removes all clones at once
    undo.undo()
    lines_after = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines_after) == 1, f"After undo, expected 1 line, got {len(lines_after)}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_array_rect_creates_grid -v`

Expected: FAIL with `ImportError: cannot import name 'ArrayRectTool'`

- [ ] **Step 3: Implement ArrayRectTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ array rectangular
class ArrayRectTool(Tool):
    """Clone selection in a rows × cols grid. Click to execute.
    Set _rows, _cols, _row_spacing, _col_spacing before or via Tab input."""
    name = "array_rect"

    def reset(self) -> None:
        self._rows = 3
        self._cols = 3
        self._row_spacing = 2.0  # grid units
        self._col_spacing = 2.0  # grid units

    def activate(self) -> None:
        self.reset()

    def on_press(self, p: QPointF) -> None:
        items = self.canvas.scene().selectedItems()
        if not items:
            return
        gs = _gs(self.canvas)
        blueprints = []
        for it in items:
            bp = self.canvas._item_blueprint(it)
            if bp:
                blueprints.append(bp)
        if not blueprints:
            return

        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Array rectangular")
        for r in range(self._rows):
            for c in range(self._cols):
                if r == 0 and c == 0:
                    continue  # skip original position
                offset = QPointF(c * self._col_spacing * gs,
                                 r * self._row_spacing * gs)
                for bp in blueprints:
                    item = _item_from_blueprint(bp, offset)
                    if item is not None:
                        self.canvas.add_item(item)
        if us:
            us.endMacro()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_array_rect_creates_grid -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `ArrayRectTool` to import.
2. Add `"array_rect": ArrayRectTool(self.view),` to `self._tools`.
3. Add `("array_rect", "ArrR", ""),` to toolbar list.

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Array Rectangular tool — clone selection in rows×cols grid"
```

---

## Task 8: Array Polar Tool

Operates on current selection. Click center point → items are cloned around it. Default: 6 copies, 360 degrees (full circle). Entire operation is one undo macro.

**Files:**
- Modify: `graphparti/tools.py` (append class)
- Modify: `graphparti/canvas_widget.py` (import + register)
- Modify: `tests/test_tools_wave1.py` (add test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tools_wave1.py`:

```python
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
    # 4 total (original + 3 copies at 90° intervals)
    assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_array_polar_creates_ring -v`

Expected: FAIL with `ImportError: cannot import name 'ArrayPolarTool'`

- [ ] **Step 3: Implement ArrayPolarTool**

Append to `graphparti/tools.py`:

```python
# ═══════════════════════════════════════════════════════════ array polar
class ArrayPolarTool(Tool):
    """Clone selection around a center point. Click to set center.
    _count = number of total copies (including original), _total_angle = sweep degrees."""
    name = "array_polar"

    def reset(self) -> None:
        self._count = 6
        self._total_angle = 360.0  # degrees

    def activate(self) -> None:
        self.reset()

    def on_press(self, p: QPointF) -> None:
        center = QPointF(p)
        items = self.canvas.scene().selectedItems()
        if not items:
            return
        blueprints = []
        for it in items:
            bp = self.canvas._item_blueprint(it)
            if bp:
                blueprints.append(bp)
        if not blueprints:
            return

        step_deg = self._total_angle / self._count
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Array polar")
        for i in range(1, self._count):
            angle_rad = math.radians(i * step_deg)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            for bp in blueprints:
                rotated_bp = _rotate_blueprint(bp, center, cos_a, sin_a)
                if rotated_bp is not None:
                    item = _item_from_blueprint(rotated_bp, QPointF(0, 0))
                    if item is not None:
                        self.canvas.add_item(item)
        if us:
            us.endMacro()

    def on_release(self, p: QPointF) -> None:
        pass


def _rotate_point(pt: QPointF, center: QPointF, cos_a: float, sin_a: float) -> QPointF:
    """Rotate pt around center by the angle whose cos/sin are given."""
    dx = pt.x() - center.x()
    dy = pt.y() - center.y()
    return QPointF(center.x() + dx * cos_a - dy * sin_a,
                   center.y() + dx * sin_a + dy * cos_a)


def _rotate_blueprint(bp, center: QPointF, cos_a: float, sin_a: float):
    """Return a new blueprint with all geometry rotated around center."""
    if bp[0] == "line":
        ln = bp[1]
        p1 = _rotate_point(ln.p1(), center, cos_a, sin_a)
        p2 = _rotate_point(ln.p2(), center, cos_a, sin_a)
        return ("line", QLineF(p1, p2), bp[2], bp[3],
                bp[4] if len(bp) > 4 else None)
    elif bp[0] == "rect":
        r = bp[1]
        tl = _rotate_point(r.topLeft(), center, cos_a, sin_a)
        br = _rotate_point(r.bottomRight(), center, cos_a, sin_a)
        return ("rect", QRectF(tl, br).normalized(), bp[2], bp[3],
                bp[4] if len(bp) > 4 else None)
    elif bp[0] == "ellipse":
        r = bp[1]
        tl = _rotate_point(r.topLeft(), center, cos_a, sin_a)
        br = _rotate_point(r.bottomRight(), center, cos_a, sin_a)
        return ("ellipse", QRectF(tl, br).normalized(), bp[2], bp[3],
                bp[4] if len(bp) > 4 else None)
    elif bp[0] == "path":
        src = bp[1]
        sp = QPainterPath()
        for i in range(src.elementCount()):
            el = src.elementAt(i)
            pt = _rotate_point(QPointF(el.x, el.y), center, cos_a, sin_a)
            if i == 0:
                sp.moveTo(pt)
            else:
                sp.lineTo(pt)
        return ("path", sp, bp[2], bp[3], bp[4] if len(bp) > 4 else None)
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py::test_array_polar_creates_ring -v`

Expected: PASS

- [ ] **Step 5: Register in canvas_widget.py**

1. Add `ArrayPolarTool` to import.
2. Add `"array_polar": ArrayPolarTool(self.view),` to `self._tools`.
3. Add `("array_polar", "ArrP", ""),` to toolbar list.

- [ ] **Step 6: Commit**

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/test_tools_wave1.py
git commit -m "feat: add Array Polar tool — clone selection around a center point"
```

---

## Task 9: Run Full Suite + Final Commit

- [ ] **Step 1: Run all Wave 1 tests**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python -m pytest tests/test_tools_wave1.py -v`

Expected: All 7 tests PASS (copy, eyedropper, construction line, matchprop, polygon, array rect, array polar).

- [ ] **Step 2: Manual smoke test — launch the app**

Run: `cd C:\Users\iamja\Desktop\graph-parti && python main.py`

Verify:
- All 7 new tools appear in the toolbar
- Copy tool: draw a line → select it → switch to Copy → click base → click destination → clone appears
- Eyedropper: click a colored line → stroke color updates in status
- XLine: click two points → infinite blue dashed line through both
- Match: click red line → click grey line → grey line turns red
- Polygon: drag from center → hexagon preview → release → hexagon committed
- Array Rect: select line → switch to ArrR → click → 3×3 grid of clones
- Array Polar: select line → switch to ArrP → click center → ring of clones
- Ctrl+Z undoes each operation cleanly

- [ ] **Step 3: Commit the complete wave**

If individual commits were made per-task, this step is a no-op. If not:

```bash
git add graphparti/tools.py graphparti/canvas_widget.py tests/
git commit -m "feat: Wave 1 — 7 daily workflow tools (copy, eyedropper, xline, matchprop, polygon, array rect, array polar)"
```

---

## Summary

| Task | Tool | Class | Key | Complexity |
|------|------|-------|-----|------------|
| 2 | Copy at Origin | `CopyTool` | — | Trivial (reuses `_item_blueprint`) |
| 3 | Eyedropper | `EyedropperTool` | I | Trivial (sample pen/brush at point) |
| 4 | Construction Line | `ConstructionLineTool` | — | Trivial (long line + dash-dot pen) |
| 5 | Property Match | `MatchPropTool` | — | Trivial (read pen, apply pen) |
| 6 | Polygon | `PolygonTool` | — | Trivial (N-point circle subdivision) |
| 7 | Array Rectangular | `ArrayRectTool` | — | Trivial (clone + translate loop) |
| 8 | Array Polar | `ArrayPolarTool` | — | Trivial (clone + rotate loop) |

**Shared utility added:** `_item_from_blueprint(bp, offset)` — reconstructs items from blueprints with an offset. Used by CopyTool, ArrayRectTool, and ArrayPolarTool.

**Shared utility added:** `_rotate_point(pt, center, cos, sin)` and `_rotate_blueprint(bp, center, cos, sin)` — rotation helpers. Used by ArrayPolarTool.

**Next wave (separate plan):** Wave 2 — Join, Fillet, Chamfer, PEDIT, Break. These are all modify tools that require intersection math and path surgery.
