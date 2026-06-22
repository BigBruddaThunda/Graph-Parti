# Wave 5: Infrastructure — Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task.

**Goal:** Add ground-level infrastructure: user-created named layers, line weight picker, perspective vanishing-point assistant, and a blocks/symbols library (insert reusable groups).

**Architecture:** Named layers extend the existing `Document` + `Layer` system (already supports N layers, just hardcoded to 3). Line weights extend the existing QPen infrastructure. Perspective assistant is a drawing aid that constrains cursor toward vanishing points. Blocks library saves/loads named item groups as reusable stamps.

**Build target:** `C:\Users\iamja\Desktop\graph-parti` (branch `master`).

---

## Task 1: User-Created Named Layers

Add the ability to create, rename, delete, and reorder vector layers beyond the default 3. Add a layer panel widget in the status bar area.

- [ ] **Test**

```python
def test_add_named_layer(canvas_env):
    from graphparti.document import VectorLayer

    view, scene, undo = canvas_env
    doc = view.document

    initial_count = len(doc.layers)
    new_layer = doc.add_layer(VectorLayer("details", scene), active=True)

    assert len(doc.layers) == initial_count + 1
    assert doc.active_layer().name == "details"
    assert new_layer.kind == "vector"
```

- [ ] **Implementation**

Add `remove_layer`, `move_layer_up`, `move_layer_down`, `rename_layer` methods to `Document` in `document.py`:

```python
    def remove_layer(self, layer: Layer) -> bool:
        if layer not in self.layers or len(self.layers) <= 1:
            return False
        idx = self.layers.index(layer)
        if isinstance(layer, VectorLayer):
            for item in list(layer.items()):
                layer.remove_item(item)
        self.layers.remove(layer)
        if self.active_index >= len(self.layers):
            self.active_index = len(self.layers) - 1
        self._reindex_z()
        return True

    def move_layer(self, layer: Layer, delta: int) -> None:
        idx = self.layers.index(layer)
        new_idx = max(0, min(len(self.layers) - 1, idx + delta))
        if new_idx == idx:
            return
        self.layers.pop(idx)
        self.layers.insert(new_idx, layer)
        if self.active_index == idx:
            self.active_index = new_idx
        self._reindex_z()

    def _reindex_z(self) -> None:
        for i, layer in enumerate(self.layers):
            layer.z_index = i + 1
            layer.apply_z()
```

Then add a "+" button next to the layer buttons in `canvas_widget.py` that creates a new VectorLayer with a prompted name, and a right-click context menu on layer buttons for rename/delete/move.

For the toolbar, after the existing 4 LayerButtons, add:

```python
        add_layer_btn = QToolButton()
        add_layer_btn.setText("+")
        add_layer_btn.setFixedSize(20, 20)
        add_layer_btn.setToolTip("Add layer")
        add_layer_btn.clicked.connect(self._add_user_layer)
        status_lay.addWidget(add_layer_btn)
```

And the method:

```python
    def _add_user_layer(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "New Layer", "Layer name:")
        if ok and name.strip():
            from .document import VectorLayer
            layer = self.document.add_layer(
                VectorLayer(name.strip(), self.scene), active=True
            )
            self._rebuild_layer_buttons()

    def _rebuild_layer_buttons(self) -> None:
        # Clear old layer buttons, rebuild from document.layers
        # This replaces the hardcoded 4-button setup with a dynamic one
        ...
```

- [ ] **Register** — No new tool class. Changes to `document.py` and `canvas_widget.py`.
- [ ] **Commit** — `"feat: add user-created named layers with add/remove/reorder"`

---

## Task 2: Line Weight Picker

Add a line weight system with ISO/Rapidograph presets. A dropdown or cycle button in the toolbar sets the active line weight. Applied to new geometry and selectable items.

- [ ] **Test**

```python
def test_line_weight_applies(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import make_pen, set_line_weight, LINE_WEIGHTS

    view, scene, undo = canvas_env

    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    view.add_item(line)

    set_line_weight(line, "bold")
    assert abs(line.pen().widthF() - LINE_WEIGHTS["bold"]) < 0.01
```

- [ ] **Implementation**

Add to `graphparti/tools.py` near `LINE_TYPES` (module level):

```python
LINE_WEIGHTS = {
    "hairline": 0.13,
    "fine":     0.25,
    "light":    0.35,
    "medium":   0.50,
    "bold":     0.70,
    "heavy":    1.00,
    "x-heavy":  1.40,
}


def set_line_weight(item, weight_name: str) -> None:
    if not hasattr(item, 'pen') or not hasattr(item, 'setPen'):
        return
    pen = QPen(item.pen())
    pen.setWidthF(LINE_WEIGHTS.get(weight_name, 1.0))
    item.setPen(pen)
```

Add cycle button in `canvas_widget.py` toolbar (same pattern as line type button):

```python
        self._line_weight_idx = 3  # default = medium
        self._line_weight_names = list(LINE_WEIGHTS.keys())
        self._weight_btn = QToolButton()
        self._weight_btn.setText("M")
        self._weight_btn.setToolTip("Weight: medium")
        self._weight_btn.setFixedWidth(24)
        self._weight_btn.clicked.connect(self._cycle_line_weight)
        tb.addWidget(self._weight_btn)
```

- [ ] **Commit** — `"feat: add line weight system — ISO pen ladder with cycle button"`

---

## Task 3: Perspective Assistant

Place 1, 2, or 3 vanishing points on the canvas. While the assistant is active, drawing tools (line, polyline) get an additional snap mode: the cursor constrains toward the nearest vanishing-point line. Visual guide rays radiate from each VP.

- [ ] **Test**

```python
def test_perspective_assistant_stores_vps(canvas_env):
    from graphparti.tools import PerspectiveTool

    view, scene, undo = canvas_env

    tool = PerspectiveTool(view)
    tool.on_press(QPointF(300, -200))  # place VP1
    tool.on_press(QPointF(-300, -200)) # place VP2

    assert len(tool._vanishing_points) == 2
    assert tool._vanishing_points[0] == QPointF(300, -200)
```

- [ ] **Implementation**

```python
# ═══════════════════════════════════════════════════════════ perspective
class PerspectiveTool(Tool):
    """Place vanishing points. While active, guide rays radiate from each VP.
    Other tools can query active VPs for perspective-constrained drawing."""
    name = "perspective"

    def reset(self) -> None:
        if not hasattr(self, '_vanishing_points'):
            self._vanishing_points = []
        self._cur = None

    def activate(self) -> None:
        self.reset()

    def on_press(self, p: QPointF) -> None:
        self._vanishing_points.append(QPointF(p))
        if len(self._vanishing_points) > 3:
            self._vanishing_points.pop(0)

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def clear_vps(self) -> None:
        self._vanishing_points = []

    def paint_preview(self, painter: QPainter) -> None:
        if not self._vanishing_points:
            return
        gs = _gs(self.canvas)
        vp_pen = QPen(QColor("#9255E5"))
        vp_pen.setCosmetic(True)
        vp_pen.setWidthF(1.5)

        ray_pen = QPen(QColor("#9255E5"))
        ray_pen.setCosmetic(True)
        ray_pen.setWidthF(0.3)
        ray_pen.setStyle(Qt.PenStyle.DotLine)

        extent = 200 * gs
        n_rays = 24

        for vp in self._vanishing_points:
            # Draw VP marker (cross)
            painter.setPen(vp_pen)
            painter.drawLine(QLineF(vp.x() - gs, vp.y(), vp.x() + gs, vp.y()))
            painter.drawLine(QLineF(vp.x(), vp.y() - gs, vp.x(), vp.y() + gs))

            # Draw radiating guide rays
            painter.setPen(ray_pen)
            for i in range(n_rays):
                angle = 2.0 * math.pi * i / n_rays
                end = QPointF(vp.x() + extent * math.cos(angle),
                              vp.y() + extent * math.sin(angle))
                painter.drawLine(QLineF(vp, end))

        # If cursor is active, draw line from nearest VP to cursor
        if self._cur is not None and self._vanishing_points:
            nearest = min(self._vanishing_points,
                         key=lambda v: QLineF(v, self._cur).length())
            painter.setPen(vp_pen)
            painter.drawLine(QLineF(nearest, self._cur))
```

- [ ] **Register** — `PerspectiveTool`, `"perspective"`, `("perspective", "VP", "")`
- [ ] **Commit** — `"feat: add Perspective assistant — vanishing point placement with guide rays"`

---

## Task 4: Blocks / Symbols Library

Select items → save as a named block (JSON). Insert block at a click point. Blocks are stored in a `blocks/` directory alongside the .parti file.

- [ ] **Test**

```python
def test_block_save_and_insert(canvas_env):
    from PySide6.QtCore import QLineF
    from PySide6.QtWidgets import QGraphicsLineItem
    from graphparti.tools import BlockSaveTool, BlockInsertTool, make_pen

    view, scene, undo = canvas_env

    # Create source geometry
    line = QGraphicsLineItem(QLineF(QPointF(0, 0), QPointF(40, 0)))
    line.setPen(make_pen("#3C3C3C", 1.0))
    line.setFlag(line.GraphicsItemFlag.ItemIsSelectable, True)
    line.setData(0, {"zip": "", "note": ""})
    view.add_item(line)
    line.setSelected(True)

    # Save as block
    save_tool = BlockSaveTool(view)
    block_data = save_tool._capture_block("test_block")
    assert block_data is not None
    assert block_data["name"] == "test_block"
    assert len(block_data["items"]) == 1

    # Insert the block at offset
    insert_tool = BlockInsertTool(view)
    insert_tool._block_data = block_data
    insert_tool.on_press(QPointF(100, 100))

    lines = [i for i in scene.items() if isinstance(i, QGraphicsLineItem)]
    assert len(lines) == 2, f"Expected 2 lines (original + inserted), got {len(lines)}"
```

- [ ] **Implementation**

```python
# ═══════════════════════════════════════════════════════════ block save
class BlockSaveTool(Tool):
    """Select items → save as a named block (reusable group)."""
    name = "block_save"

    def on_press(self, p: QPointF) -> None:
        selected = self.canvas.scene().selectedItems()
        if not selected:
            return
        self._capture_block("block")

    def _capture_block(self, name: str) -> dict | None:
        selected = self.canvas.scene().selectedItems()
        if not selected:
            return None
        # Compute bounding rect center as the block's origin
        r = QRectF()
        for it in selected:
            r = r.united(it.sceneBoundingRect())
        origin = r.center()

        blueprints = []
        for it in selected:
            bp = self.canvas._item_blueprint(it)
            if bp:
                blueprints.append(bp)
        if not blueprints:
            return None

        # Serialize blueprints relative to origin
        items_data = []
        for bp in blueprints:
            shifted = _item_from_blueprint(bp, QPointF(-origin.x(), -origin.y()))
            if shifted is not None:
                from .document import Document
                sd = Document._serialize_item(shifted)
                if sd.get("type") != "unknown":
                    items_data.append(sd)
                # Clean up the temp item
                sc = shifted.scene()
                if sc:
                    sc.removeItem(shifted)

        block = {"name": name, "origin": [origin.x(), origin.y()],
                 "items": items_data}
        self._last_block = block
        return block


# ═══════════════════════════════════════════════════════════ block insert
class BlockInsertTool(Tool):
    """Click to insert a saved block at the click point."""
    name = "block_insert"

    def reset(self) -> None:
        if not hasattr(self, '_block_data'):
            self._block_data = None
        self._cur = None

    def on_press(self, p: QPointF) -> None:
        if self._block_data is None:
            return
        items_data = self._block_data.get("items", [])
        if not items_data:
            return

        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Insert block")

        for sd in items_data:
            from .document import Document
            item = Document._deserialize_item(sd)
            if item is not None:
                item.moveBy(p.x(), p.y())
                self.canvas.add_item(item)

        if us:
            us.endMacro()

    def on_move(self, p: QPointF) -> None:
        self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        pass

    def paint_preview(self, painter: QPainter) -> None:
        if self._cur is not None and self._block_data is not None:
            painter.setPen(self._preview_pen)
            gs = _gs(self.canvas)
            painter.drawEllipse(self._cur, gs * 0.3, gs * 0.3)
            painter.drawLine(QLineF(self._cur.x() - gs * 0.5, self._cur.y(),
                                     self._cur.x() + gs * 0.5, self._cur.y()))
            painter.drawLine(QLineF(self._cur.x(), self._cur.y() - gs * 0.5,
                                     self._cur.x(), self._cur.y() + gs * 0.5))
```

- [ ] **Register** — `BlockSaveTool` as `"block_save"` / `"BlkS"`, `BlockInsertTool` as `"block_insert"` / `"BlkI"`
- [ ] **Commit** — `"feat: add Block save/insert — reusable symbol groups"`

---

## Task 5: Integration Test

Run all 24+ tests, verify everything.
