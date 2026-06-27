"""The canvas: grid, zoom, pan, grid-snap + object-snap, and tool routing.

GRAPH PARTI steps 1-4. Snap resolution order while drawing: object-snap (endpoints
& midpoints of existing geometry, within a pixel radius) takes priority, then
grid-snap, then raw. Object-snap is the feature that makes it feel like CAD, so it
gets distinct markers: a square for endpoints, a triangle for midpoints (green);
the grid snap shows a red crosshair.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, Signal
from PySide6.QtGui import QBrush, QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap, QPolygonF, QWheelEvent
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from .commands import AddItemCommand, DeleteItemsCommand, MoveItemsCommand, ReshapeCommand


class CanvasView(QGraphicsView):
    cursor_moved = Signal(QPointF, str)  # resolved scene position, snap kind
    zoom_changed = Signal(float)
    handback_requested = Signal(str)     # district legged back to the Archideck
    handback_with_bounds = Signal(str, object)  # same + bounding rect in grid units

    ZOOM_STEP = 1.15
    MIN_SCALE = 0.05
    MAX_SCALE = 40.0
    OSNAP_PIXELS = 12.0

    def __init__(self, scene: QGraphicsScene, grid_spacing: int = 20, major_every: int = 5, parent=None) -> None:
        super().__init__(scene, parent)
        self.grid_spacing = grid_spacing
        self.major_every = major_every
        self.snap_enabled = True
        self._snap_pull = 0.125   # dead zone: only snap within 1/8 of grid spacing
        self._ortho_enabled = False
        self._ortho_angle = 45     # degrees — 45=H/V+diags (default), 90=H/V only
        self._layer_mode = "trace"  # "parti" | "both" | "trace"
        self._wireframe = True      # grid visible; X key toggles
        self._div_visible = True    # red division ticks visible; N key toggles
        self.document = None
        self.active_tool = None
        self.undo_stack = None
        self._stroke_color = "#3C3C3C"
        self._fill_color = None
        # Active zip facets (operator, axis, order, color) — set by the host from
        # the cockpit dial. Plain glyph strings; graphparti never imports the cockpit.
        self.current_facets: tuple = (None, None, None, None)
        self._e_held = False
        self._e_prev_tool = None
        self._extend_tool = None  # set by CanvasWidget after tool creation
        self._panning = False
        self._right_dragging = False
        self._resize_handle = None   # active resize handle index (0-7) or None
        self._resize_item = None     # QGraphicsPixmapItem being resized
        self._resize_origin = None   # original rect before resize
        self._resize_anchor = None   # mouse anchor for resize drag
        self._pan_anchor = QPointF()
        self._cursor_scene: QPointF | None = None
        self._snap_kind = ""  # "", "grid", "endpoint", "midpoint"

        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#F2EBD8"))  # warm sheep's-wool paper
        self.setAcceptDrops(True)  # accept image file drops → parti layer
        scene.selectionChanged.connect(self._on_selection_changed)

        # Tab-type dimension input (floating over canvas)
        self._dim_input = QLineEdit(self)
        self._dim_input.setFixedWidth(80)
        self._dim_input.setStyleSheet(
            "background:#fff; color:#000; border:1px solid #2464E5;"
            " padding:2px 4px; font-size:12px; font-family:monospace;"
        )
        self._dim_input.setVisible(False)
        self._dim_input.returnPressed.connect(self._on_dim_confirm)
        self._dim_input.textEdited.connect(self._on_dim_text_edited)
        self._dim_input.installEventFilter(self)
        self._dim_opened_this_press = False

        self._dim_edit_idx: int = 0
        self._dim_edit_item = None
        self._dim_editing_selected = False

        self._minor_color = QColor("#AECEE7")  # sky-blue notebook lines (minor)
        self._major_color = QColor("#7FB2D6")  # sky-blue (major, a touch stronger)
        self._grid_snap_color = QColor("#C1140C")   # red crosshair = grid snap
        self._osnap_color = QColor("#1f7a1f")        # green square/triangle = object snap

    # ------------------------------------------------ Tab intercept + event filter
    def event(self, ev) -> bool:
        """Intercept Tab before Qt uses it for focus-cycling."""
        from PySide6.QtCore import QEvent
        if ev.type() == QEvent.Type.KeyPress and ev.key() == Qt.Key.Key_Tab:
            if self._dim_input.isVisible():
                self._apply_dim_value()
                if self._has_selected_dims():
                    self._show_selected_dim_input()
                elif (self.active_tool and self.active_tool.name == "rect"
                        and getattr(self.active_tool, '_dim_phase', 0) > 0):
                    self._dim_input.clear()
                    self._dim_input.setFocus()
                else:
                    self._dim_input.setVisible(False)
                    self._dim_input.clear()
                    self.setFocus()
                return True
            if self._tool_active() and self.active_tool.in_progress:
                self._show_dim_input()
                return True
            if self._has_selected_dims():
                self._show_selected_dim_input()
                return True
        return super().event(ev)

    def eventFilter(self, obj, ev) -> bool:
        from PySide6.QtCore import QEvent
        if obj is self._dim_input and ev.type() == QEvent.Type.KeyPress:
            if ev.key() == Qt.Key.Key_Tab:
                self._apply_dim_value()
                if self._has_selected_dims():
                    self._show_selected_dim_input()
                elif (self.active_tool and self.active_tool.name == "rect"
                        and getattr(self.active_tool, '_dim_phase', 0) > 0):
                    self._dim_input.clear()
                else:
                    self._dim_input.setVisible(False)
                    self._dim_input.clear()
                    self.setFocus()
                return True
            if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._apply_dim_value()
                self._dim_input.setVisible(False)
                self._dim_input.clear()
                self.setFocus()
                if self.active_tool and self.active_tool.in_progress:
                    self.active_tool.on_release(QPointF())
                    self.viewport().update()
                return True
            if ev.key() == Qt.Key.Key_Escape:
                self._dim_input.setVisible(False)
                self._dim_input.clear()
                self._dim_editing_selected = False
                self.setFocus()
                return True
        return super().eventFilter(obj, ev)

    def _apply_dim_value(self) -> None:
        text = self._dim_input.text().strip()
        if not text:
            return
        try:
            value = float(text)
        except ValueError:
            return
        if self._dim_editing_selected:
            self._reshape_selected(value)
            self._dim_editing_selected = False
        elif self.active_tool:
            self.active_tool.set_dimension(value)
            self.viewport().update()

    # --------------------------------------------------------- tools / document
    def set_tool(self, tool) -> None:
        if self.active_tool is not None:
            self.active_tool.deactivate()
        self._defocus_active_text()
        self.active_tool = tool
        if tool is not None:
            tool.activate()
            if tool.name not in ("select", "rotate", "mirror"):
                self.scene().clearSelection()
        self.viewport().update()

    def current_stroke(self) -> str:
        return self._stroke_color

    def set_stroke(self, color: str) -> None:
        self._stroke_color = color

    def set_fill(self, color: str | None) -> None:
        self._fill_color = color

    def set_current_facets(self, operator=None, axis=None, order=None, color=None) -> None:
        """Host-callable: set the active zip facets from the cockpit dial.
        Empty strings (blanked dials) normalize to None (partial district)."""
        norm = lambda g: g if g else None
        self.current_facets = (norm(operator), norm(axis), norm(order), norm(color))

    def add_item(self, item: QGraphicsItem) -> None:
        layer = self.document.active_vector_layer() if self.document else None
        if layer is None:
            return
        if self.undo_stack is not None:
            self.undo_stack.push(AddItemCommand(layer, item))
        else:
            layer.add_item(item)

    # ----------------------------------------------------- selection / editing
    def _active_layer_items(self) -> set:
        """Items selectable under the current layer mode (parti/both/trace/book)."""
        if self.document is None:
            return set()
        result: set = set()
        mode = self._layer_mode
        if mode in ("parti", "both"):
            pl = self.document.layers[0]  # parti (raster)
            if hasattr(pl, '_ref_images'):
                result |= set(pl._ref_images)
        if mode in ("trace", "both"):
            tl = self.document.layers[1]  # trace (vector)
            if hasattr(tl, 'items'):
                result |= set(tl.items())
        if mode == "book" and len(self.document.layers) > 2:
            bl = self.document.layers[2]  # book (vector — zip boxes)
            if hasattr(bl, 'items'):
                result |= set(bl.items())
        return result

    def pick_item(self, scene_pos: QPointF):
        """Topmost selectable item under SCENE_POS — active layer only."""
        allowed = self._active_layer_items()
        for it in self.items(self.mapFromScene(scene_pos)):
            if it in allowed and bool(it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
                return it
        return None

    def push_move(self, items, dx: float, dy: float) -> None:
        if self.undo_stack is not None and items:
            self.undo_stack.push(MoveItemsCommand(items, dx, dy))

    def select_in_rect(self, rect: QRectF, additive: bool = False,
                       crossing: bool = False) -> None:
        if not additive:
            self.scene().clearSelection()
        allowed = self._active_layer_items()
        mode = (Qt.ItemSelectionMode.IntersectsItemShape if crossing
                else Qt.ItemSelectionMode.ContainsItemShape)
        for it in self.scene().items(rect, mode):
            if it in allowed and bool(it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
                it.setSelected(True)

    def delete_selected(self) -> None:
        items = self.scene().selectedItems()
        if items and self.undo_stack is not None and self.document is not None:
            self.undo_stack.push(DeleteItemsCommand(self.document, items))

    def explode_selected(self) -> None:
        """Break selected compound shapes into individual line segments."""
        from .commands import ExplodeCommand
        items = self.scene().selectedItems()
        if not items or self.undo_stack is None or self.document is None:
            return
        self.undo_stack.beginMacro("Explode")
        for item in items:
            segs = self._line_segments(item)
            if len(segs) < 2:
                continue
            pen = item.pen() if hasattr(item, 'pen') else None
            meta = item.data(0) or {"zip": "", "note": ""}
            new_items = []
            for seg in segs:
                if seg.length() < 1e-6:
                    continue
                li = QGraphicsLineItem(seg)
                if pen:
                    li.setPen(pen)
                li.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                li.setData(0, dict(meta))
                new_items.append(li)
            if new_items:
                self.undo_stack.push(ExplodeCommand(self.document, item, new_items))
        self.undo_stack.endMacro()
        self.viewport().update()

    def overkill_selected(self) -> None:
        """Remove duplicate/overlapping line segments from selection.
        Keeps fills and non-line items untouched."""
        from .commands import OverkillCommand
        items = self.scene().selectedItems()
        if not items or self.undo_stack is None or self.document is None:
            return
        lines = [it for it in items if isinstance(it, QGraphicsLineItem)]
        if len(lines) < 2:
            return
        tol = self.grid_spacing * 0.1
        seen: list[tuple[float, float, float, float]] = []
        dupes = []
        for li in lines:
            ln = li.line()
            p1 = li.mapToScene(ln.p1())
            p2 = li.mapToScene(ln.p2())
            k1 = (round(p1.x() / tol), round(p1.y() / tol),
                  round(p2.x() / tol), round(p2.y() / tol))
            k2 = (k1[2], k1[3], k1[0], k1[1])
            if k1 in seen or k2 in seen:
                dupes.append(li)
            else:
                seen.append(k1)
        if dupes:
            self.undo_stack.push(OverkillCommand(self.document, dupes))
        self.viewport().update()

    def trim_at(self, scene_pos: QPointF) -> None:
        """Trim: find the segment under the cursor, cut at grid + intersection boundaries."""
        item = self.pick_item(scene_pos)
        if item is None or self.undo_stack is None or self.document is None:
            return
        segments = self._line_segments(item)
        if not segments:
            self.undo_stack.push(DeleteItemsCommand(self.document, [item]))
            return
        # Closest segment to the click
        best_idx, best_dist = 0, float('inf')
        for i, seg in enumerate(segments):
            d = self._point_to_segment_dist(scene_pos, seg)
            if d < best_dist:
                best_dist = d
                best_idx = i
        self._trim_segment(item, segments, best_idx, scene_pos)

    def _trim_segment(self, item, all_segments: list[QLineF],
                      trim_idx: int, click: QPointF) -> None:
        """Explode shape into edges, trim the clicked edge at grid + intersections."""
        seg = all_segments[trim_idx]
        others = [s for i, s in enumerate(all_segments) if i != trim_idx]

        p1, p2 = seg.p1(), seg.p2()
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-12:
            return

        gs = self.grid_spacing
        target = QLineF(p1, p2)
        crossings: set[float] = {0.0, 1.0}

        # ── Grid crossings ──
        if abs(dx) > 1e-9:
            x_lo, x_hi = sorted([p1.x(), p2.x()])
            x = math.ceil(x_lo / gs) * gs
            while x <= x_hi + 1e-9:
                t = (x - p1.x()) / dx
                if -1e-9 <= t <= 1.0 + 1e-9:
                    crossings.add(max(0.0, min(1.0, t)))
                x += gs
        if abs(dy) > 1e-9:
            y_lo, y_hi = sorted([p1.y(), p2.y()])
            y = math.ceil(y_lo / gs) * gs
            while y <= y_hi + 1e-9:
                t = (y - p1.y()) / dy
                if -1e-9 <= t <= 1.0 + 1e-9:
                    crossings.add(max(0.0, min(1.0, t)))
                y += gs

        # ── Intersections with other items ──
        for layer in self.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for other_item in layer.items():
                if other_item is item:
                    continue
                for other_seg in self._line_segments(other_item):
                    itype, ipoint = target.intersects(other_seg)
                    if itype == QLineF.IntersectionType.BoundedIntersection:
                        t = ((ipoint.x() - p1.x()) * dx +
                             (ipoint.y() - p1.y()) * dy) / length_sq
                        if -1e-9 <= t <= 1.0 + 1e-9:
                            crossings.add(max(0.0, min(1.0, t)))

        # ── Intersections with sibling edges of the same shape ──
        for sib in others:
            itype, ipoint = target.intersects(sib)
            if itype == QLineF.IntersectionType.BoundedIntersection:
                t = ((ipoint.x() - p1.x()) * dx +
                     (ipoint.y() - p1.y()) * dy) / length_sq
                if -1e-9 <= t <= 1.0 + 1e-9:
                    crossings.add(max(0.0, min(1.0, t)))

        sorted_t = sorted(crossings)

        # ── Merge t-values that are very close (prevents micro-fragments) ──
        merged = [sorted_t[0]]
        for t in sorted_t[1:]:
            if t - merged[-1] > 0.005:
                merged.append(t)
            else:
                merged[-1] = max(merged[-1], t)
        sorted_t = merged

        # ── Find clicked sub-segment ──
        t_click = ((click.x() - p1.x()) * dx + (click.y() - p1.y()) * dy) / length_sq
        t_click = max(0.0, min(1.0, t_click))

        trim_left, trim_right = 0.0, 1.0
        for i in range(len(sorted_t) - 1):
            if sorted_t[i] - 1e-9 <= t_click <= sorted_t[i + 1] + 1e-9:
                trim_left = sorted_t[i]
                trim_right = sorted_t[i + 1]
                break

        # If no real crossings besides endpoints, delete the whole line
        if trim_left < 0.005 and trim_right > 0.995 and len(others) == 0:
            self.undo_stack.beginMacro("Trim")
            self.undo_stack.push(DeleteItemsCommand(self.document, [item]))
            self.undo_stack.endMacro()
            return

        # ── Atomic: delete original, keep exploded edges + remnants ──
        pen = item.pen()
        brush = item.brush() if hasattr(item, 'brush') else None
        meta = item.data(0) or {"zip": "", "note": ""}
        layer = self.document.layer_for(item)
        if layer is None:
            return

        self.undo_stack.beginMacro("Trim")
        self.undo_stack.push(DeleteItemsCommand(self.document, [item]))

        if others:
            tol = 2.0
            groups: list[list[QLineF]] = []
            cur_group = [others[0]]
            for s in others[1:]:
                if s.length() < 1e-6:
                    continue
                if QLineF(cur_group[-1].p2(), s.p1()).length() < tol:
                    cur_group.append(s)
                else:
                    groups.append(cur_group)
                    cur_group = [s]
            groups.append(cur_group)
            if (len(groups) > 1
                    and QLineF(groups[-1][-1].p2(), groups[0][0].p1()).length() < tol):
                groups[0] = groups.pop() + groups[0]
            for grp in groups:
                valid = [s for s in grp if s.length() > 1e-6]
                if not valid:
                    continue
                if len(valid) == 1:
                    pi = QGraphicsLineItem(valid[0])
                else:
                    path = QPainterPath(valid[0].p1())
                    for s in valid:
                        path.lineTo(s.p2())
                    pi = QGraphicsPathItem(path)
                pi.setPen(pen)
                pi.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                pi.setData(0, dict(meta))
                self.undo_stack.push(AddItemCommand(layer, pi))

        min_remnant = 0.01
        if trim_left > min_remnant:
            pa = QPointF(p1)
            pb = QPointF(p1.x() + trim_left * dx, p1.y() + trim_left * dy)
            if QLineF(pa, pb).length() > 1.0:
                li = QGraphicsLineItem(QLineF(pa, pb))
                li.setPen(pen)
                li.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                li.setData(0, dict(meta))
                self.undo_stack.push(AddItemCommand(layer, li))

        if trim_right < 1.0 - min_remnant:
            pa = QPointF(p1.x() + trim_right * dx, p1.y() + trim_right * dy)
            pb = QPointF(p2)
            if QLineF(pa, pb).length() > 1.0:
                li = QGraphicsLineItem(QLineF(pa, pb))
                li.setPen(pen)
                li.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                li.setData(0, dict(meta))
                self.undo_stack.push(AddItemCommand(layer, li))

        self.undo_stack.endMacro()

    @staticmethod
    def _point_to_segment_dist(p: QPointF, seg: QLineF) -> float:
        """Perpendicular distance from point *p* to line segment *seg*."""
        a, b = seg.p1(), seg.p2()
        dx, dy = b.x() - a.x(), b.y() - a.y()
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-12:
            return QLineF(p, a).length()
        t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / length_sq))
        proj = QPointF(a.x() + t * dx, a.y() + t * dy)
        return QLineF(p, proj).length()

    @staticmethod
    def _line_segments(item) -> list[QLineF]:
        """Extract QLineF segments (scene coords) from any geometry item."""
        segs: list[QLineF] = []
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            segs.append(QLineF(item.mapToScene(ln.p1()), item.mapToScene(ln.p2())))
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            corners = [item.mapToScene(c) for c in
                       (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft())]
            for i in range(4):
                segs.append(QLineF(corners[i], corners[(i + 1) % 4]))
        elif isinstance(item, QGraphicsPathItem):
            path = item.path()
            pts = [item.mapToScene(QPointF(path.elementAt(i).x, path.elementAt(i).y))
                   for i in range(path.elementCount())]
            for a, b in zip(pts, pts[1:]):
                segs.append(QLineF(a, b))
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            cx = (r.left() + r.right()) / 2.0
            cy = (r.top() + r.bottom()) / 2.0
            rx, ry = r.width() / 2.0, r.height() / 2.0
            n = 36
            pts = [item.mapToScene(QPointF(
                cx + rx * math.cos(2.0 * math.pi * i / n),
                cy + ry * math.sin(2.0 * math.pi * i / n)))
                for i in range(n + 1)]
            for a, b in zip(pts, pts[1:]):
                segs.append(QLineF(a, b))
        return segs

    def trim_fence(self, p1: QPointF, p2: QPointF) -> None:
        """Fence trim: cut every item the line p1→p2 crosses."""
        fence = QLineF(p1, p2)
        if self.document is None or self.undo_stack is None:
            return
        hits: list[QPointF] = []
        for layer in self.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in list(layer.items()):
                if item.data(1) in ("cell_fill", "div_point"):
                    continue
                for seg in self._line_segments(item):
                    itype, ipt = fence.intersects(seg)
                    if itype == QLineF.IntersectionType.BoundedIntersection:
                        hits.append(QPointF(ipt))
                        break
        if not hits:
            return
        self.undo_stack.beginMacro("Fence trim")
        for pt in hits:
            self.trim_at(pt)
        self.undo_stack.endMacro()

    def _tool_active(self) -> bool:
        return self.active_tool is not None and self.dragMode() == QGraphicsView.DragMode.NoDrag

    def _scene_pos(self, event: QMouseEvent) -> QPointF:
        point, _kind = self.resolve_snap(self.mapToScene(event.position().toPoint()))
        return point

    # ----------------------------------------------------------------- snapping
    def set_snap_enabled(self, on: bool) -> None:
        self.snap_enabled = bool(on)
        self.viewport().update()

    def set_ortho_enabled(self, on: bool) -> None:
        self._ortho_enabled = bool(on)

    def set_ortho_angle(self, degrees: int) -> None:
        self._ortho_angle = max(1, degrees)

    def snap_point(self, p: QPointF) -> QPointF:
        """Grid-only snap (nearest intersection, or P unchanged when off)."""
        if not self.snap_enabled:
            return QPointF(p)
        s = self.grid_spacing
        return QPointF(round(p.x() / s) * s, round(p.y() / s) * s)

    def resolve_snap(self, raw: QPointF) -> tuple[QPointF, str]:
        """Object-snap first, then grid-snap (with dead zone), then raw."""
        osnap = self._nearest_osnap(raw)
        if osnap is not None:
            return osnap
        if self.snap_enabled:
            snapped = self.snap_point(raw)
            if QLineF(raw, snapped).length() <= self.grid_spacing * self._snap_pull:
                return snapped, "grid"
        return QPointF(raw), ""

    def _nearest_osnap(self, raw: QPointF) -> tuple[QPointF, str] | None:
        if self.document is None or self.active_tool is None:
            return None
        radius = self.OSNAP_PIXELS / max(self.transform().m11(), 1e-6)
        best: tuple[QPointF, str] | None = None
        best_d = radius
        for layer in self.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if not item.isVisible():
                    continue
                for point, kind in self._osnap_candidates(item):
                    d = QLineF(raw, point).length()
                    if d <= best_d:
                        best_d = d
                        best = (point, kind)
        return best

    @staticmethod
    def _mid(a: QPointF, b: QPointF) -> QPointF:
        return QPointF((a.x() + b.x()) / 2.0, (a.y() + b.y()) / 2.0)

    def _osnap_candidates(self, item) -> list[tuple[QPointF, str]]:
        out: list[tuple[QPointF, str]] = []
        if item.data(1) == "div_point":
            # snap to the mark's centre (local origin), robust to rotate/move
            return [(item.mapToScene(QPointF(0.0, 0.0)), "endpoint")]
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            out.append((item.mapToScene(ln.p1()), "endpoint"))
            out.append((item.mapToScene(ln.p2()), "endpoint"))
            out.append((item.mapToScene(self._mid(ln.p1(), ln.p2())), "midpoint"))
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            for c in (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()):
                out.append((item.mapToScene(c), "endpoint"))
            cx, cy = (r.left() + r.right()) / 2.0, (r.top() + r.bottom()) / 2.0
            for m in (QPointF(cx, r.top()), QPointF(r.right(), cy), QPointF(cx, r.bottom()), QPointF(r.left(), cy)):
                out.append((item.mapToScene(m), "midpoint"))
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            cx, cy = (r.left() + r.right()) / 2.0, (r.top() + r.bottom()) / 2.0
            out.append((item.mapToScene(QPointF(cx, cy)), "midpoint"))  # center
            for q in (QPointF(r.left(), cy), QPointF(r.right(), cy), QPointF(cx, r.top()), QPointF(cx, r.bottom())):
                out.append((item.mapToScene(q), "endpoint"))
        elif isinstance(item, QGraphicsPathItem):
            path = item.path()
            verts = [QPointF(path.elementAt(i).x, path.elementAt(i).y) for i in range(path.elementCount())]
            for v in verts:
                out.append((item.mapToScene(v), "endpoint"))
            for a, b in zip(verts, verts[1:]):
                out.append((item.mapToScene(self._mid(a, b)), "midpoint"))
        return out

    # --------------------------------------------------------------------- grid
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawBackground(painter, rect)
        if not self._wireframe:
            return  # grid hidden (X toggle)
        s = self.grid_spacing
        if s <= 0:
            return
        left = math.floor(rect.left() / s) * s
        top = math.floor(rect.top() / s) * s
        minor_lines: list[QLineF] = []
        major_lines: list[QLineF] = []
        x = left
        while x < rect.right():
            line = QLineF(x, rect.top(), x, rect.bottom())
            (major_lines if round(x / s) % self.major_every == 0 else minor_lines).append(line)
            x += s
        y = top
        while y < rect.bottom():
            line = QLineF(rect.left(), y, rect.right(), y)
            (major_lines if round(y / s) % self.major_every == 0 else minor_lines).append(line)
            y += s
        minor_pen = QPen(self._minor_color); minor_pen.setCosmetic(True); minor_pen.setWidthF(1.0)
        major_pen = QPen(self._major_color); major_pen.setCosmetic(True); major_pen.setWidthF(0.8)
        painter.setPen(minor_pen); painter.drawLines(minor_lines)
        painter.setPen(major_pen); painter.drawLines(major_lines)

    # ---------------------------------------------------- foreground (overlays)
    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)
        if self.active_tool is not None:
            self.active_tool.paint_preview(painter)
        self._draw_selected_dims(painter)
        self._draw_resize_handles(painter)
        self._draw_text_borders(painter)
        if (self._right_dragging and self.active_tool
                and getattr(self.active_tool, '_rt_dragged', False)):
            pen = QPen(QColor("#C1140C"))
            pen.setCosmetic(True)
            pen.setWidthF(1.5)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(QLineF(self.active_tool._rt_start,
                                    self.active_tool._rt_cur))
        if self._cursor_scene is None or not self._snap_kind:
            return
        p = self._cursor_scene
        r = 6.0 / max(self.transform().m11(), 1e-6)
        if self._snap_kind == "grid":
            pen = QPen(self._grid_snap_color); pen.setCosmetic(True); pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.drawLine(QLineF(p.x() - r, p.y(), p.x() + r, p.y()))
            painter.drawLine(QLineF(p.x(), p.y() - r, p.x(), p.y() + r))
        elif self._snap_kind == "endpoint":
            pen = QPen(self._osnap_color); pen.setCosmetic(True); pen.setWidthF(2.0)
            painter.setPen(pen)
            painter.drawRect(QRectF(p.x() - r, p.y() - r, 2 * r, 2 * r))
        elif self._snap_kind == "midpoint":
            pen = QPen(self._osnap_color); pen.setCosmetic(True); pen.setWidthF(2.0)
            painter.setPen(pen)
            tri = QPolygonF([QPointF(p.x(), p.y() - r), QPointF(p.x() - r, p.y() + r), QPointF(p.x() + r, p.y() + r)])
            painter.drawPolygon(tri)

    # ------------------------------------------------------------- zoom (wheel)
    def wheelEvent(self, event: QWheelEvent) -> None:
        dy = event.angleDelta().y()
        if dy == 0:
            return
        factor = self.ZOOM_STEP if dy > 0 else 1.0 / self.ZOOM_STEP
        projected = self.transform().m11() * factor
        if projected < self.MIN_SCALE or projected > self.MAX_SCALE:
            return
        self.scale(factor, factor)
        event.accept()
        self.zoom_changed.emit(self.transform().m11())

    # -------------------------------------------------------- mouse: pan + tool
    def mousePressEvent(self, event: QMouseEvent) -> None:
        se = getattr(self, '_sound_engine', None)
        if se is not None:
            pos = event.position()
            se.on_mouse_click(pos.x(), pos.y(), str(event.button()))
        if event.button() == Qt.MouseButton.LeftButton:
            self._gesture_origin = self.mapToScene(event.position().toPoint())
        self._dim_opened_this_press = False
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_anchor = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.RightButton and self.active_tool is not None:
            if self.active_tool.in_progress:
                self.active_tool.cancel()
            elif hasattr(self.active_tool, 'on_right_press'):
                self.active_tool.on_right_press(self._scene_pos(event))
                self._right_dragging = True
            else:
                self.active_tool.idle_right_click(self._scene_pos(event))
            self.viewport().update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._defocus_active_text()
            # Check resize handles first (before tool routing)
            raw_scene = self.mapToScene(event.position().toPoint())
            item, hidx = self._hit_handle(raw_scene)
            if item is not None:
                self._start_resize(item, hidx, raw_scene)
                event.accept()
                return
            # Select + click on a district's tail/free-text → edit it in place
            if (self._tool_active() and self.active_tool.name == "select"
                    and self._focus_zipbox_text(raw_scene)):
                event.accept()
                return
            if self._tool_active():
                self.active_tool.on_press(self._scene_pos(event))
                self.viewport().update()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning:
            delta = event.position() - self._pan_anchor
            self._pan_anchor = event.position()
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(int(hbar.value() - delta.x()))
            vbar.setValue(int(vbar.value() - delta.y()))
            event.accept()
            return
        point, kind = self.resolve_snap(self.mapToScene(event.position().toPoint()))
        self._cursor_scene = point
        self._snap_kind = kind
        self.cursor_moved.emit(point, kind)
        if self._resize_handle is not None:
            raw = self.mapToScene(event.position().toPoint())
            self._do_resize(raw)
        if self._right_dragging and hasattr(self.active_tool, 'on_right_move'):
            self.active_tool.on_right_move(point)
        if self.active_tool is not None:
            self.active_tool.on_move(point)
        self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton and self._right_dragging:
            if hasattr(self.active_tool, 'on_right_release'):
                self.active_tool.on_right_release(self._scene_pos(event))
            self._right_dragging = False
            self.viewport().update()
            event.accept()
            return
        # End resize drag
        if event.button() == Qt.MouseButton.LeftButton and self._resize_handle is not None:
            self._end_resize()
            self.viewport().update()
            event.accept()
            return
        # Apply any pending Tab dimension before committing the shape.
        # Skip the release that belongs to the very press that opened the input
        # (e.g. the picking click in Divide/Offset) so the input stays up to type.
        if (event.button() == Qt.MouseButton.LeftButton and self._dim_input.isVisible()
                and not self._dim_opened_this_press):
            self._apply_dim_value()
            self._dim_input.setVisible(False)
            self._dim_input.clear()
        if self._panning and event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool_active():
            self.active_tool.on_release(self._scene_pos(event))
            se = getattr(self, '_sound_engine', None)
            origin = getattr(self, '_gesture_origin', None)
            if se is not None and origin is not None:
                end = self.mapToScene(event.position().toPoint())
                dx, dy = end.x() - origin.x(), end.y() - origin.y()
                import math
                length = math.hypot(dx, dy)
                angle = math.atan2(dy, dx)
                if length > 5:
                    se.on_gesture(length, angle)
            self.viewport().update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._tool_active():
            self.active_tool.on_double_click(self._scene_pos(event))
            self.viewport().update()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def leaveEvent(self, event) -> None:
        self._cursor_scene = None
        self._snap_kind = ""
        self.viewport().update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------- keys
    def keyPressEvent(self, event: QKeyEvent) -> None:
        se = getattr(self, '_sound_engine', None)
        if se is not None:
            se.on_keystroke(event.text() or "")

        # Ctrl-V: paste geometry (if copied) or image from clipboard
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if hasattr(self, '_geometry_clipboard') and self._geometry_clipboard:
                self._paste_geometry()
            else:
                self._paste_from_clipboard()
            event.accept()
            return
        # Ctrl-C: copy selected items (stores in _clipboard)
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._copy_selected()
            event.accept()
            return
        # Arrow keys → viewport navigation (same grammar as joystick / z-pad)
        _ARROW_MAP = {
            Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
            Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1),
        }
        if event.key() in _ARROW_MAP and not self._text_item_has_focus():
            dx, dy = _ARROW_MAP[event.key()]
            nav = getattr(self, '_navigator', None)
            if nav is not None:
                if self._wireframe:
                    nav.step(dx, dy)
                else:
                    nav.scroll_free(dx * 15, dy * 15)
            else:
                gs = self.grid_spacing
                zoom = self.transform().m11()
                hbar = self.horizontalScrollBar()
                vbar = self.verticalScrollBar()
                hbar.setValue(int(hbar.value() + dx * gs * zoom))
                vbar.setValue(int(vbar.value() + dy * gs * zoom))
            event.accept()
            return

        # Ctrl+E = explode selected, Ctrl+K = overkill selected
        if event.key() == Qt.Key.Key_E and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.explode_selected()
            event.accept()
            return
        if event.key() == Qt.Key.Key_K and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.overkill_selected()
            event.accept()
            return

        # Don't intercept keys when a text item is being edited (let text handle them)
        if self._text_item_has_focus():
            if event.key() == Qt.Key.Key_Escape:
                focus = self.scene().focusItem()
                from PySide6.QtWidgets import QGraphicsTextItem
                if isinstance(focus, QGraphicsTextItem):
                    focus.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                    focus.clearFocus()
                    if not focus.toPlainText().strip():
                        if self.undo_stack and self.document:
                            self.undo_stack.push(DeleteItemsCommand(self.document, [focus]))
                    if self.active_tool and hasattr(self.active_tool, '_active_text'):
                        self.active_tool._active_text = None
                    event.accept()
                    return
            super().keyPressEvent(event)
            return
        # Auto-type dimensions: digit/period keys open dim input while drawing
        if (self._tool_active() and self.active_tool.in_progress
                and not self._dim_input.isVisible()
                and event.text() and event.text() in "0123456789."):
            self._show_dim_input()
            self._dim_input.setText(event.text())
            event.accept()
            return
        if (self._has_selected_dims()
                and not self._dim_input.isVisible()
                and event.text() and event.text() in "0123456789."):
            self._show_selected_dim_input()
            self._dim_input.setText(event.text())
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Tab and self._tool_active() and self.active_tool.in_progress:
            self._show_dim_input()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Tab and self._has_selected_dims():
            self._show_selected_dim_input()
            event.accept()
            return
        if event.key() == Qt.Key.Key_X and not event.isAutoRepeat():
            self._wireframe = not self._wireframe
            self.viewport().update()
            event.accept()
            return
        if event.key() == Qt.Key.Key_N and not event.isAutoRepeat():
            self._toggle_division_marks()
            event.accept()
            return
        if event.key() == Qt.Key.Key_E and not event.isAutoRepeat():
            if not self._e_held and self._extend_tool is not None:
                self._e_held = True
                self._e_prev_tool = self.active_tool
                self.set_tool(self._extend_tool)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif self.active_tool is not None and event.key() in (
            Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter,
        ):
            self.active_tool.on_key(event.key())
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        if event.key() == Qt.Key.Key_E and not event.isAutoRepeat():
            if self._e_held:
                self._e_held = False
                if self.active_tool and hasattr(self.active_tool, 'cancel'):
                    if self.active_tool.in_progress:
                        self.active_tool.cancel()
                if self._e_prev_tool is not None:
                    self.set_tool(self._e_prev_tool)
                    self._e_prev_tool = None
                self.viewport().update()
        super().keyReleaseEvent(event)

    def tabletEvent(self, event) -> None:
        """Handle UGEE M908 (passive EMR) and other tablet/stylus input.

        The M908 sends absolute coordinates + 16384 pressure levels + tilt via
        WinTab or Windows Ink drivers. Qt wraps these as QTabletEvent.

        Key fixes for cheap EMR tablets:
        - Throttle TabletMove events (EMR hovering floods at ~200Hz)
        - Accept all tablet events to prevent Qt mouse synthesis (double-processing)
        - Treat barrel button 1 as right-click, barrel button 2 as middle-click
        - Store pressure for future pressure-sensitive drawing
        """
        import time
        from PySide6.QtCore import QEvent

        event.accept()

        etype = event.type()

        # Throttle hover/move events to ~60fps to prevent UI freeze
        if etype == QEvent.Type.TabletMove:
            now = time.monotonic()
            if hasattr(self, '_last_tablet_move') and now - self._last_tablet_move < 0.016:
                return
            self._last_tablet_move = now

        scene_pos = self.mapToScene(event.position().toPoint())

        # Store pressure and tilt for tools that want them
        self._tablet_pressure = event.pressure()
        self._tablet_tilt_x = event.xTilt()
        self._tablet_tilt_y = event.yTilt()

        # Resolve snap
        resolved, kind = self.resolve_snap(scene_pos)
        self._cursor_scene = resolved
        self._snap_kind = kind
        self.cursor_moved.emit(resolved, kind)

        # Map barrel buttons: button() returns which button changed,
        # buttons() returns which are currently held
        from PySide6.QtCore import Qt as _Qt
        pen_btn = event.button()
        is_eraser = (event.pointerType() == event.PointerType.Eraser)

        if etype == QEvent.Type.TabletPress:
            if is_eraser:
                if self.active_tool:
                    self.active_tool.on_right_press(resolved)
            elif pen_btn == _Qt.MouseButton.RightButton:
                if self.active_tool:
                    self.active_tool.on_right_press(resolved)
            elif pen_btn == _Qt.MouseButton.MiddleButton:
                self._panning = True
                self._pan_anchor = event.position()
            else:
                if self.active_tool:
                    self.active_tool.on_press(resolved)

        elif etype == QEvent.Type.TabletMove:
            if self._panning:
                delta = event.position() - self._pan_anchor
                self._pan_anchor = event.position()
                self.horizontalScrollBar().setValue(
                    int(self.horizontalScrollBar().value() - delta.x()))
                self.verticalScrollBar().setValue(
                    int(self.verticalScrollBar().value() - delta.y()))
            elif self.active_tool:
                self.active_tool.on_move(resolved)
            self.viewport().update()

        elif etype == QEvent.Type.TabletRelease:
            if self._panning:
                self._panning = False
            elif is_eraser or pen_btn == _Qt.MouseButton.RightButton:
                if self.active_tool:
                    self.active_tool.on_right_release(resolved)
            else:
                if self.active_tool:
                    self.active_tool.on_release(resolved)
            self.viewport().update()

        elif etype == QEvent.Type.TabletEnterProximity:
            pass  # pen entered EMR field — just acknowledge

        elif etype == QEvent.Type.TabletLeaveProximity:
            pass  # pen left EMR field
            self.viewport().update()

    # ----------------------------------------- drag-and-drop (reference images)
    _DRAG_FORMATS = ("application/x-scl-glyph", "application/x-scl-zip",
                     "application/x-scl-arrow", "application/x-scl-handback",
                     "application/x-scl-textblock")

    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md.hasImage() or md.hasUrls() or any(md.hasFormat(f) for f in self._DRAG_FORMATS):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        md = event.mimeData()
        if md.hasImage() or md.hasUrls() or any(md.hasFormat(f) for f in self._DRAG_FORMATS):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        md = event.mimeData()

        # ── SCL handback (drag 🍗 onto a district → leg it to the Archideck) ──
        if md.hasFormat("application/x-scl-handback"):
            scene_pos = self.mapToScene(event.position().toPoint())
            self._leg_handback(scene_pos)
            event.acceptProposedAction()
            self.viewport().update()
            return

        # ── SCL arrow drop (drag a z-pad direction → flow/direction arrow) ──
        if md.hasFormat("application/x-scl-arrow"):
            direction = bytes(md.data("application/x-scl-arrow")).decode("utf-8")
            scene_pos = self.mapToScene(event.position().toPoint())
            if self.snap_enabled:
                gs = self.grid_spacing
                scene_pos = QPointF(round(scene_pos.x() / gs) * gs,
                                    round(scene_pos.y() / gs) * gs)
            self._drop_arrow(direction, scene_pos)
            event.acceptProposedAction()
            self.viewport().update()
            return

        # ── SCL zip drop (drag the [Archideck] plate → spawn a zip box) ──
        if md.hasFormat("application/x-scl-zip"):
            raw = bytes(md.data("application/x-scl-zip")).decode("utf-8")
            facets = tuple((g if g != "_" else None) for g in raw.split(","))
            scene_pos = self.mapToScene(event.position().toPoint())
            if self.snap_enabled:
                gs = self.grid_spacing
                scene_pos = QPointF(round(scene_pos.x() / gs) * gs,
                                    round(scene_pos.y() / gs) * gs)
            self._drop_zip_box(facets, scene_pos)
            event.acceptProposedAction()
            self.viewport().update()
            return

        # ── Text block drop (drag from composer box → place text) ──
        if md.hasFormat("application/x-scl-textblock"):
            text = bytes(md.data("application/x-scl-textblock")).decode("utf-8")
            scene_pos = self.mapToScene(event.position().toPoint())
            self._place_text_block(text, scene_pos)
            event.acceptProposedAction()
            self.viewport().update()
            return

        # ── SCL glyph drop (drag from emoji palette → place icon/order) ──
        if md.hasFormat("application/x-scl-glyph"):
            glyph = bytes(md.data("application/x-scl-glyph")).decode("utf-8")
            scene_pos = self.mapToScene(event.position().toPoint())
            # Icons always free-place (no snap). Orders still snap.
            is_order = glyph in self._ORDER_GLYPH_MAP
            if is_order and self.snap_enabled:
                gs = self.grid_spacing
                scene_pos = QPointF(
                    round(scene_pos.x() / gs) * gs,
                    round(scene_pos.y() / gs) * gs)
            if self._handle_glyph_drop(glyph, scene_pos):
                event.acceptProposedAction()
                self.viewport().update()
                return

        pixmap = None

        # Try image data first (clipboard paste / drag)
        if md.hasImage():
            from PySide6.QtGui import QImage
            img = md.imageData()
            if isinstance(img, QImage) and not img.isNull():
                pixmap = QPixmap.fromImage(img)

        # Then try file URLs (drag from Explorer / desktop)
        if pixmap is None and md.hasUrls():
            _IMG_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
            for url in md.urls():
                path = url.toLocalFile()
                if path and path.lower().endswith(_IMG_EXTS):
                    pm = QPixmap(path)
                    if not pm.isNull():
                        pixmap = pm
                        break

        if pixmap is not None and not pixmap.isNull() and self.document is not None:
            # Find the parti (raster/reference) layer
            parti = None
            for layer in self.document.layers:
                if layer.kind == "raster" and layer.name == "parti":
                    parti = layer
                    break
            if parti is not None:
                # Map drop position to scene coordinates, snap to grid
                scene_pos = self.mapToScene(event.position().toPoint())
                if self.snap_enabled:
                    gs = self.grid_spacing
                    scene_pos = QPointF(
                        round(scene_pos.x() / gs) * gs,
                        round(scene_pos.y() / gs) * gs,
                    )
                parti.add_reference_image(pixmap, scene_pos)
                event.acceptProposedAction()
                self.viewport().update()
                return

        super().dropEvent(event)

    # ----------------------------------------- resize handles (Select + Snap-off)
    def _selected_pixmap(self):
        """Return the single selected QGraphicsPixmapItem, if any."""
        from PySide6.QtWidgets import QGraphicsPixmapItem
        sel = self.scene().selectedItems()
        if len(sel) == 1 and isinstance(sel[0], QGraphicsPixmapItem):
            return sel[0]
        return None

    def _resizable_selected(self):
        """The single selected resizable item (image, zip box, text, or icon) — or None.
        Resize is tied to Select + Snap OFF: snap is the lock (move-only when on),
        snap-off lets the same Select drag resize. System-wide, no separate tool."""
        if self.snap_enabled:
            return None
        if not (self.active_tool and self.active_tool.name == "select"):
            return None
        from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem
        sel = self.scene().selectedItems()
        if len(sel) != 1:
            return None
        it = sel[0]
        if isinstance(it, QGraphicsPixmapItem):
            return it
        if isinstance(it, QGraphicsRectItem) and it.data(1) == "zip_box":
            return it
        if isinstance(it, QGraphicsTextItem):
            return it
        return None

    def _handle_rects(self, item):
        """8 handle positions (scene rects) for a pixmap item: corners + edge mids."""
        br = item.mapToScene(item.boundingRect())
        # br is a QPolygonF — get the bounding rect
        r = br.boundingRect()
        hs = 6.0 / max(self.transform().m11(), 0.01)  # handle size in scene units
        pts = [
            r.topLeft(), QPointF(r.center().x(), r.top()),       r.topRight(),
            QPointF(r.right(), r.center().y()),
            r.bottomRight(), QPointF(r.center().x(), r.bottom()), r.bottomLeft(),
            QPointF(r.left(), r.center().y()),
        ]
        return [QRectF(p.x() - hs, p.y() - hs, hs * 2, hs * 2) for p in pts]

    def _draw_resize_handles(self, painter: QPainter) -> None:
        target = self._resizable_selected()
        if target is None:
            return
        pen = QPen(QColor("#2464E5"))
        pen.setCosmetic(True)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        for hr in self._handle_rects(target):
            painter.drawRect(hr)

    def _hit_handle(self, scene_pos: QPointF):
        """Return (item, handle_index) if scene_pos hits a resize handle, else (None, None)."""
        target = self._resizable_selected()
        if target is None:
            return None, None
        for i, hr in enumerate(self._handle_rects(target)):
            if hr.contains(scene_pos):
                return target, i
        return None, None

    def _start_resize(self, item, handle_idx, scene_pos):
        self._resize_handle = handle_idx
        self._resize_item = item
        self._resize_anchor = QPointF(scene_pos)
        br = item.mapToScene(item.boundingRect()).boundingRect()
        self._resize_origin = QRectF(br)
        if isinstance(item, QGraphicsTextItem):
            f = item.font()
            self._resize_orig_font_px = f.pixelSize() if f.pixelSize() > 0 else f.pointSize()

    def _do_resize(self, scene_pos: QPointF):
        if self._resize_item is None or self._resize_origin is None:
            return
        r = QRectF(self._resize_origin)
        h = self._resize_handle
        # Corners: 0=TL, 2=TR, 4=BR, 6=BL.  Edges: 1=T, 3=R, 5=B, 7=L.
        if h in (0, 6, 7):  # left edge
            r.setLeft(scene_pos.x())
        if h in (2, 3, 4):  # right edge
            r.setRight(scene_pos.x())
        if h in (0, 1, 2):  # top edge
            r.setTop(scene_pos.y())
        if h in (4, 5, 6):  # bottom edge
            r.setBottom(scene_pos.y())
        r = r.normalized()
        if r.width() < 2 or r.height() < 2:
            return
        item = self._resize_item
        from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem
        from PySide6.QtGui import QTransform
        if isinstance(item, QGraphicsPixmapItem):
            pm = item.pixmap()
            item.setPos(r.topLeft())
            item.setTransform(QTransform.fromScale(r.width() / pm.width(),
                                                   r.height() / pm.height()))
        elif isinstance(item, QGraphicsRectItem):
            # zip box: resize the boundary, reflow the body text width. Placed
            # children keep their local positions, so text isn't disturbed.
            item.setPos(r.topLeft())
            item.setRect(0, 0, r.width(), r.height())
            pad = self.grid_spacing * 0.35
            for ch in item.childItems():
                if ch.data(1) == "zip_box_text":
                    ch.setTextWidth(max(10.0, r.width() - 2 * pad))
        elif isinstance(item, QGraphicsTextItem):
            # Text / SCL icon: scale font size proportionally to the resize
            orig = self._resize_origin
            scale_factor = r.height() / max(orig.height(), 1)
            font = item.font()
            orig_px = font.pixelSize()
            if orig_px <= 0:
                orig_px = font.pointSize()
            if not hasattr(self, '_resize_orig_font_px'):
                self._resize_orig_font_px = orig_px
            new_px = max(6, int(self._resize_orig_font_px * scale_factor))
            font.setPixelSize(new_px)
            item.setFont(font)
            item.setTextWidth(max(10.0, r.width()))
            item.setPos(r.topLeft())
        self.viewport().update()

    def _end_resize(self):
        self._resize_handle = None
        self._resize_item = None
        self._resize_origin = None
        self._resize_anchor = None

    # ----------------------------------------- Tab-type dimensions
    def _show_dim_input(self) -> None:
        """Show the floating dimension input near the cursor."""
        if self._cursor_scene:
            vp = self.mapFromScene(self._cursor_scene)
            self._dim_input.move(vp.x() + 15, max(0, vp.y() - 10))
        self._dim_input.clear()
        self._dim_input.setVisible(True)
        self._dim_input.setFocus()

    # ----------------------------------------- glyph drag-and-drop (books)
    # Map order glyphs to their Vignola order names
    _ORDER_GLYPH_MAP = {
        "🐂": "tuscan", "⛽": "doric", "🦋": "ionic",
        "🏟": "corinthian", "🌾": "composite",
    }

    def _drop_zip_box(self, facets: tuple, scene_pos: QPointF) -> None:
        """Spawn a zip box (a district seed) on the Book layer at scene_pos:
        a bounded rect carrying the emoji zip + empty ± tail, with an editable
        free-text body you can type into immediately."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from .tools import _load_vg5000
        if self.document is None or len(self.document.layers) < 3:
            return
        book = self.document.layers[2]
        gs = self.grid_spacing
        w, h = 12 * gs, 7 * gs
        pad = gs * 0.35
        zipstr = "".join(g if g else "_" for g in facets)

        rect = QGraphicsRectItem(QRectF(0, 0, w, h))
        rect.setPos(scene_pos)
        pen = QPen(QColor("#2464E5")); pen.setCosmetic(True); pen.setWidthF(1.5)
        rect.setPen(pen)
        rect.setBrush(QBrush(QColor(255, 255, 255, 40)))
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        rect.setData(0, {"facets": list(facets), "tail_text": "", "note": ""})
        rect.setData(1, "zip_box")

        # Add the rect to the book layer FIRST so it is in the scene, THEN parent
        # the labels with an explicit setParentItem (QGraphicsTextItem(rect) is
        # ambiguous — the first positional arg can be text, leaving it parentless).
        if self.undo_stack is not None:
            self.undo_stack.push(AddItemCommand(book, rect))
        else:
            book.add_item(rect)

        # Revelator line: LOCKED zip + editable "± tail | free-text".
        zip_label = QGraphicsTextItem()
        zip_label.setParentItem(rect)
        zip_label.setFont(_load_vg5000(12))
        zip_label.setDefaultTextColor(QColor("#2464E5"))
        zip_label.setPlainText(f"{zipstr} ±")
        zip_label.setPos(pad, pad)
        zip_label.setData(1, "zip_box_zip")          # locked — no text interaction

        tail = QGraphicsTextItem()
        tail.setParentItem(rect)
        tail.setFont(_load_vg5000(12))
        tail.setDefaultTextColor(QColor("#2464E5"))
        tail.setPlainText(" | ")                      # bar present by default
        tail.setPos(pad + zip_label.boundingRect().width(), pad)
        tail.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        tail.setData(1, "zip_box_tail")               # tail before |, free-text after

        body = QGraphicsTextItem()
        body.setParentItem(rect)
        body.setFont(_load_vg5000(12))
        body.setDefaultTextColor(QColor("#3C3C3C"))
        body.setTextWidth(w - 2 * pad)
        body.setPos(pad, pad + 22)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        body.setData(1, "zip_box_text")               # inner content — never touches the zip
        body.setFocus()  # instant typing

    def _zip_box_at(self, scene_pos: QPointF):
        """The zip-box rect under scene_pos (matching the item or its parent)."""
        for it in self.scene().items(scene_pos):
            if it.data(1) == "zip_box":
                return it
            p = it.parentItem()
            if p is not None and p.data(1) == "zip_box":
                return p
        return None

    def _leg_handback(self, scene_pos: QPointF) -> None:
        """🍗 dropped on a district → flag it as handed back to the Archideck.
        Still lives on the .parti and stays findable; this marks it as a working
        copy passed to the round table for wiring / upkeep / tasks."""
        box = self._zip_box_at(scene_pos)
        if box is None:
            return
        data = box.data(0) or {}
        data["handback"] = True
        box.setData(0, data)
        pen = QPen(QColor("#C8772E")); pen.setCosmetic(True); pen.setWidthF(2.0)
        box.setPen(pen)  # copper border = legged to the Archideck
        if not any(ch.data(1) == "zip_box_handback" for ch in box.childItems()):
            from PySide6.QtWidgets import QGraphicsTextItem
            from .tools import _load_vg5000
            badge = QGraphicsTextItem()
            badge.setParentItem(box)
            badge.setFont(_load_vg5000(12))
            badge.setPlainText("🍗")
            badge.setPos(box.rect().width() - 22, 2)
            badge.setData(1, "zip_box_handback")
        facets = data.get("facets") or []
        zipstr = "".join(g if g else "_" for g in facets) if facets else "____"
        title = ""
        for ch in box.childItems():
            if ch.data(1) == "zip_box_text":
                title = (ch.toPlainText() or "").strip().replace("\n", " ")[:40]
        self.handback_requested.emit(zipstr + (f'  "{title}"' if title else ""))
        bounds_grid = {
            "x": box.rect().x() / self.grid_spacing,
            "y": box.rect().y() / self.grid_spacing,
            "w": box.rect().width() / self.grid_spacing,
            "h": box.rect().height() / self.grid_spacing,
        }
        self.handback_with_bounds.emit(
            zipstr + (f'  "{title}"' if title else ""), bounds_grid)

    def _focus_zipbox_text(self, scene_pos: QPointF) -> bool:
        """Select + click on a district's tail/free-text field → edit it (the zip
        emojis stay locked). Top-row glyph buttons then insert into the focus."""
        from PySide6.QtWidgets import QGraphicsTextItem
        for it in self.scene().items(scene_pos):
            if (isinstance(it, QGraphicsTextItem)
                    and it.data(1) in ("zip_box_tail", "zip_box_text")):
                it.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
                it.setFocus()
                return True
        return False

    _ARROW_DIRS = {"up": (0.0, -1.0), "down": (0.0, 1.0),
                   "left": (-1.0, 0.0), "right": (1.0, 0.0)}

    def _drop_arrow(self, direction: str, scene_pos: QPointF) -> None:
        """Drop a flow/direction arrow (a pointer mark) at scene_pos. Seeds the
        later junction/navigation layer — marked data(1)='arrow' for future wiring."""
        from PySide6.QtGui import QPainterPath
        dx, dy = self._ARROW_DIRS.get(direction, (1.0, 0.0))
        gs = self.grid_spacing
        shaft = 3.0 * gs
        head = 0.6 * gs
        base = QPointF(scene_pos)
        tip = QPointF(base.x() + dx * shaft, base.y() + dy * shaft)
        ang = math.atan2(dy, dx)
        path = QPainterPath(base)
        path.lineTo(tip)
        for off in (math.radians(150), math.radians(-150)):
            path.moveTo(tip)
            path.lineTo(QPointF(tip.x() + head * math.cos(ang + off),
                                tip.y() + head * math.sin(ang + off)))
        item = QGraphicsPathItem(path)
        pen = QPen(QColor("#3C3C3C")); pen.setCosmetic(True); pen.setWidthF(2.0)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"direction": direction, "note": ""})
        item.setData(1, "arrow")
        self.add_item(item)  # active vector layer, undoable

    def _handle_glyph_drop(self, glyph: str, scene_pos: QPointF) -> bool:
        """Handle a glyph dragged from the palette onto the canvas.
        Returns True if the glyph had a drop action."""
        order_name = self._ORDER_GLYPH_MAP.get(glyph)
        if order_name is not None:
            from .orders import draw_order
            gs = self.grid_spacing
            items = draw_order(order_name, scene_pos.x(), scene_pos.y(), gs)
            if self.undo_stack:
                self.undo_stack.beginMacro(f"Place {order_name}")
            for item in items:
                self.add_item(item)
            if self.undo_stack:
                self.undo_stack.endMacro()
            return True
        self._place_glyph_icon(glyph, scene_pos)
        return True

    def _place_glyph_icon(self, glyph: str, scene_pos: QPointF) -> None:
        """Place a 0.5D movable emoji icon block on the book layer.
        Snaps to nodes (endpoints/midpoints) only — never grid lines.
        Centers the glyph on the snap/drop point."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from .tools import _load_vg5000
        osnap = self._nearest_osnap(scene_pos)
        if osnap is not None:
            scene_pos = osnap[0]
        gs = self.grid_spacing
        half_d = gs * 0.5
        item = QGraphicsTextItem()
        font = _load_vg5000(int(half_d * 0.8))
        item.setFont(font)
        item.setPlainText(glyph)
        br = item.boundingRect()
        item.setPos(scene_pos.x() - br.width() / 2,
                    scene_pos.y() - br.height() / 2)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setData(1, "scl_icon")
        self._add_to_book_layer(item)

    def _place_text_block(self, text: str, scene_pos: QPointF) -> None:
        """Place a movable text block on the book layer. Centered on drop point.
        Snaps to nodes only. For the 63rd-box drag-out."""
        from PySide6.QtWidgets import QGraphicsTextItem
        from .tools import _load_vg5000
        osnap = self._nearest_osnap(scene_pos)
        if osnap is not None:
            scene_pos = osnap[0]
        gs = self.grid_spacing
        item = QGraphicsTextItem()
        font = _load_vg5000(int(gs * 0.4))
        item.setFont(font)
        item.setPlainText(text[:250])
        br = item.boundingRect()
        item.setPos(scene_pos.x() - br.width() / 2,
                    scene_pos.y() - br.height() / 2)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setData(1, "text_block")
        self._add_to_book_layer(item)

    def _add_to_book_layer(self, item) -> None:
        """Add an item to the book layer (index 2) with undo support."""
        if self.document is None or len(self.document.layers) < 3:
            self.add_item(item)
            return
        book = self.document.layers[2]
        from .commands import AddItemCommand
        if self.undo_stack is not None:
            self.undo_stack.push(AddItemCommand(book, item))
        else:
            book.add_item(item)

    def _draw_text_borders(self, painter: QPainter) -> None:
        """Thin dotted border around committed text items — shows claimed space."""
        if self.document is None:
            return
        from PySide6.QtWidgets import QGraphicsTextItem
        pen = QPen(QColor("#BBBBBB"))
        pen.setCosmetic(True)
        pen.setWidthF(0.5)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for layer in self.document.layers:
            if not layer.visible or layer.kind != "vector":
                continue
            for item in layer.items():
                if not isinstance(item, QGraphicsTextItem):
                    continue
                if item.data(1) not in ("word_text", "cell_text", "text_block"):
                    continue
                if item.textInteractionFlags() & Qt.TextInteractionFlag.TextEditorInteraction:
                    continue
                poly = item.mapToScene(item.boundingRect())
                painter.drawPolygon(poly)

    def _defocus_active_text(self) -> None:
        """Remove text editing focus from any active QGraphicsTextItem."""
        from PySide6.QtWidgets import QGraphicsTextItem
        focus = self.scene().focusItem()
        if isinstance(focus, QGraphicsTextItem):
            focus.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            focus.clearFocus()
            if not focus.toPlainText().strip():
                if self.undo_stack and self.document:
                    self.undo_stack.push(DeleteItemsCommand(self.document, [focus]))
            if self.active_tool and hasattr(self.active_tool, '_active_text'):
                self.active_tool._active_text = None

    def _toggle_division_marks(self) -> None:
        """N key: show/hide all red division tick marks."""
        self._div_visible = not self._div_visible
        if self.document is not None:
            for layer in self.document.layers:
                if layer.kind != "vector":
                    continue
                for item in layer.items():
                    if item.data(1) == "div_point":
                        item.setVisible(self._div_visible)
        self.viewport().update()

    def request_dim_input(self, scene_pos: QPointF, prefill: str = "") -> None:
        """Tool-callable: show dim input at a scene position with pre-filled text."""
        vp = self.mapFromScene(scene_pos)
        self._dim_input.move(vp.x() + 15, max(0, vp.y() - 10))
        self._dim_input.setText(prefill)
        self._dim_input.selectAll()
        self._dim_input.setVisible(True)
        self._dim_input.setFocus()
        self._dim_opened_this_press = True

    def _on_dim_text_edited(self, text: str) -> None:
        """Live-preview hook: feed the typed value to a tool that wants it."""
        if self.active_tool and hasattr(self.active_tool, 'preview_dimension'):
            try:
                self.active_tool.preview_dimension(float(text))
            except ValueError:
                pass

    def _on_dim_confirm(self) -> None:
        """Apply the typed dimension to the active tool (Enter key)."""
        self._apply_dim_value()
        self._dim_input.setVisible(False)
        self._dim_input.clear()
        self.setFocus()

    # ----------------------------------------- selected-item dimension labels
    def _on_selection_changed(self) -> None:
        sel = self.scene().selectedItems()
        item = sel[0] if len(sel) == 1 else None
        if item is not self._dim_edit_item:
            self._dim_edit_idx = 0
            self._dim_edit_item = item

    def _text_item_has_focus(self) -> bool:
        focus = self.scene().focusItem()
        from PySide6.QtWidgets import QGraphicsTextItem
        return isinstance(focus, QGraphicsTextItem)

    def _has_selected_dims(self) -> bool:
        sel = self.scene().selectedItems()
        if len(sel) != 1:
            return False
        from PySide6.QtWidgets import QGraphicsTextItem
        if isinstance(sel[0], QGraphicsTextItem):
            return False
        return bool(self._item_dimensions(sel[0]))

    def _show_selected_dim_input(self) -> None:
        sel = self.scene().selectedItems()
        if len(sel) != 1:
            return
        dims = self._item_dimensions(sel[0])
        if not dims:
            return
        idx = self._dim_edit_idx % len(dims)
        mid, length, prefix = dims[idx]
        vp = self.mapFromScene(mid)
        self._dim_input.move(vp.x() + 15, max(0, vp.y() - 10))
        from .tools import _dim_text
        self._dim_input.setText(_dim_text(length))
        self._dim_input.selectAll()
        self._dim_input.setVisible(True)
        self._dim_input.setFocus()
        self._dim_editing_selected = True

    def _item_dimensions(self, item):
        """Return [(midpoint, length_grid, label_prefix)] for each editable dimension."""
        if item.data(1) in ("cell_fill", "cell_text", "word_text", "div_point",
                            "arrow", "zip_box"):
            return []
        gs = self.grid_spacing
        dims = []
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            p1 = item.mapToScene(ln.p1())
            p2 = item.mapToScene(ln.p2())
            mid = self._mid(p1, p2)
            dims.append((mid, QLineF(p1, p2).length() / gs, ""))
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            corners = [item.mapToScene(c) for c in
                       (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft())]
            for i in range(4):
                a, b = corners[i], corners[(i + 1) % 4]
                mid = self._mid(a, b)
                dims.append((mid, QLineF(a, b).length() / gs, ""))
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            cx = (r.left() + r.right()) / 2.0
            cy = (r.top() + r.bottom()) / 2.0
            radius = r.width() / 2.0 / gs
            center = item.mapToScene(QPointF(cx, cy))
            edge = item.mapToScene(QPointF(r.right(), cy))
            mid = self._mid(center, edge)
            dims.append((mid, radius, "r="))
        elif isinstance(item, QGraphicsPathItem):
            path = item.path()
            pts = [item.mapToScene(QPointF(path.elementAt(i).x, path.elementAt(i).y))
                   for i in range(path.elementCount())]
            for a, b in zip(pts, pts[1:]):
                mid = self._mid(a, b)
                dims.append((mid, QLineF(a, b).length() / gs, ""))
        return dims

    def _draw_selected_dims(self, painter: QPainter) -> None:
        sel = self.scene().selectedItems()
        if len(sel) != 1:
            return
        item = sel[0]
        dims = self._item_dimensions(item)
        if not dims:
            return
        from .tools import _dim_text
        for i, (mid, length, prefix) in enumerate(dims):
            active = (i == self._dim_edit_idx % len(dims))
            vp = painter.transform().map(mid)
            painter.save()
            painter.resetTransform()
            f = painter.font()
            f.setPixelSize(11)
            painter.setFont(f)
            color = QColor("#2464E5") if active else QColor("#3C3C3C")
            painter.setPen(QPen(color))
            text = f"{prefix}{_dim_text(length)}"
            if active:
                text = f"[{text}]"
            painter.drawText(QPointF(vp.x() + 6, vp.y() - 4), text)
            painter.restore()

    def _reshape_selected(self, new_value: float) -> None:
        """Reshape the selected item's active dimension to new_value (grid units)."""
        sel = self.scene().selectedItems()
        if len(sel) != 1 or self.undo_stack is None:
            return
        item = sel[0]
        dims = self._item_dimensions(item)
        if not dims:
            return
        idx = self._dim_edit_idx % len(dims)
        gs = self.grid_spacing
        scene_val = new_value * gs

        if isinstance(item, QGraphicsLineItem):
            old_line = QLineF(item.line())
            p1 = item.mapToScene(old_line.p1())
            p2 = item.mapToScene(old_line.p2())
            ln = QLineF(p1, p2)
            if ln.length() < 1e-6:
                return
            ln.setLength(scene_val)
            new_line = QLineF(item.mapFromScene(ln.p1()), item.mapFromScene(ln.p2()))
            self.undo_stack.push(ReshapeCommand(item, old_line, new_line))

        elif isinstance(item, QGraphicsRectItem):
            old_rect = QRectF(item.rect())
            r = QRectF(old_rect)
            if idx in (0, 2):
                r.setWidth(scene_val)
            else:
                r.setHeight(scene_val)
            self.undo_stack.push(ReshapeCommand(item, old_rect, r))

        elif isinstance(item, QGraphicsEllipseItem):
            old_rect = QRectF(item.rect())
            cx = (old_rect.left() + old_rect.right()) / 2.0
            cy = (old_rect.top() + old_rect.bottom()) / 2.0
            new_rect = QRectF(cx - scene_val, cy - scene_val,
                              2 * scene_val, 2 * scene_val)
            self.undo_stack.push(ReshapeCommand(item, old_rect, new_rect))

        elif isinstance(item, QGraphicsPathItem):
            old_path = item.path()
            pts = [QPointF(old_path.elementAt(i).x, old_path.elementAt(i).y)
                   for i in range(old_path.elementCount())]
            if idx >= len(pts) - 1:
                return
            a, b = pts[idx], pts[idx + 1]
            seg = QLineF(a, b)
            if seg.length() < 1e-6:
                return
            seg.setLength(scene_val)
            pts[idx + 1] = seg.p2()
            from PySide6.QtGui import QPainterPath
            new_path = QPainterPath(pts[0])
            for pt in pts[1:]:
                new_path.lineTo(pt)
            if old_path.elementCount() > 2:
                last_el = old_path.elementAt(old_path.elementCount() - 1)
                first_el = old_path.elementAt(0)
                if (abs(last_el.x - first_el.x) < 1e-6
                        and abs(last_el.y - first_el.y) < 1e-6):
                    new_path.closeSubpath()
            self.undo_stack.push(ReshapeCommand(item, old_path, new_path))

        self._dim_edit_idx = (idx + 1) % len(dims)
        self.viewport().update()

    def _copy_selected(self) -> None:
        """Ctrl-C: clone selected geometry items to internal clipboard."""
        items = self.scene().selectedItems()
        if not items:
            return
        # Store item blueprints (type + geometry + pen + data) for paste
        self._geometry_clipboard = []
        # Compute bounding rect center for relative positioning on paste
        r = QRectF()
        for it in items:
            r = r.united(it.sceneBoundingRect())
        self._clipboard_center = r.center()
        for it in items:
            bp = self._item_blueprint(it)
            if bp:
                self._geometry_clipboard.append(bp)

    @staticmethod
    def _item_blueprint(item):
        """Extract a clonable blueprint from a QGraphicsItem."""
        from PySide6.QtWidgets import QGraphicsPixmapItem
        pen = item.pen() if hasattr(item, 'pen') else None
        brush = item.brush() if hasattr(item, 'brush') else None
        data = item.data(0)
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            return ("line", QLineF(item.mapToScene(ln.p1()), item.mapToScene(ln.p2())),
                    pen, data, brush)
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            return ("rect", QRectF(tl, br), pen, data, brush)
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            return ("ellipse", QRectF(tl, br), pen, data, brush)
        elif isinstance(item, QGraphicsPathItem):
            path = item.path()
            from PySide6.QtGui import QPainterPath
            sp = QPainterPath()
            for i in range(path.elementCount()):
                el = path.elementAt(i)
                pt = item.mapToScene(QPointF(el.x, el.y))
                if i == 0:
                    sp.moveTo(pt)
                else:
                    sp.lineTo(pt)
            return ("path", sp, pen, data, brush)
        elif isinstance(item, QGraphicsPixmapItem):
            return ("pixmap", item.pixmap(), item.pos(), item.transform(),
                    item.opacity(), data)
        return None

    def _paste_geometry(self) -> None:
        """Ctrl-V (when geometry clipboard has items): paste cloned geometry at viewport center."""
        if not hasattr(self, '_geometry_clipboard') or not self._geometry_clipboard:
            return
        center = self.mapToScene(self.viewport().rect().center())
        offset = center - self._clipboard_center
        if self.snap_enabled:
            gs = self.grid_spacing
            offset = QPointF(round(offset.x() / gs) * gs, round(offset.y() / gs) * gs)
        layer = self.document.active_vector_layer() if self.document else None
        if layer is None:
            return
        if self.undo_stack:
            self.undo_stack.beginMacro("Paste")
        for bp in self._geometry_clipboard:
            item = None
            if bp[0] == "line":
                ln = bp[1]
                item = QGraphicsLineItem(QLineF(
                    QPointF(ln.p1().x() + offset.x(), ln.p1().y() + offset.y()),
                    QPointF(ln.p2().x() + offset.x(), ln.p2().y() + offset.y())))
            elif bp[0] == "rect":
                r = bp[1].translated(offset)
                item = QGraphicsRectItem(r)
            elif bp[0] == "ellipse":
                r = bp[1].translated(offset)
                item = QGraphicsEllipseItem(r)
            elif bp[0] == "path":
                from PySide6.QtGui import QPainterPath
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
                if self.undo_stack:
                    from .commands import AddItemCommand
                    self.undo_stack.push(AddItemCommand(layer, item))
                else:
                    layer.add_item(item)
        if self.undo_stack:
            self.undo_stack.endMacro()
        self.viewport().update()

    def _paste_from_clipboard(self) -> None:
        """Ctrl-V: paste clipboard image onto the parti layer at viewport center."""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QImage
        clipboard = QApplication.clipboard()
        md = clipboard.mimeData()
        pixmap = None
        if md.hasImage():
            img = md.imageData()
            if isinstance(img, QImage) and not img.isNull():
                pixmap = QPixmap.fromImage(img)
        if pixmap is None or pixmap.isNull() or self.document is None:
            return
        parti = None
        for layer in self.document.layers:
            if layer.kind == "raster" and layer.name == "parti":
                parti = layer
                break
        if parti is not None:
            center = self.mapToScene(self.viewport().rect().center())
            if self.snap_enabled:
                gs = self.grid_spacing
                center = QPointF(round(center.x() / gs) * gs,
                                 round(center.y() / gs) * gs)
            parti.add_reference_image(pixmap, center)
            self.viewport().update()
