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

from .commands import AddItemCommand, DeleteItemsCommand, MoveItemsCommand


class CanvasView(QGraphicsView):
    cursor_moved = Signal(QPointF, str)  # resolved scene position, snap kind
    zoom_changed = Signal(float)

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
        self.document = None
        self.active_tool = None
        self.undo_stack = None
        self._stroke_color = "#3C3C3C"
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

        # Tab-type dimension input (floating over canvas)
        self._dim_input = QLineEdit(self)
        self._dim_input.setFixedWidth(80)
        self._dim_input.setStyleSheet(
            "background:#fff; color:#000; border:1px solid #2464E5;"
            " padding:2px 4px; font-size:12px; font-family:monospace;"
        )
        self._dim_input.setVisible(False)
        self._dim_input.returnPressed.connect(self._on_dim_confirm)
        self._dim_input.installEventFilter(self)

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
                if (self.active_tool and self.active_tool.name == "rect"
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
        return super().event(ev)

    def eventFilter(self, obj, ev) -> bool:
        from PySide6.QtCore import QEvent
        if obj is self._dim_input and ev.type() == QEvent.Type.KeyPress:
            if ev.key() == Qt.Key.Key_Tab:
                self._apply_dim_value()
                if (self.active_tool and self.active_tool.name == "rect"
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
                # Enter = auto-commit the shape immediately
                if self.active_tool and self.active_tool.in_progress:
                    self.active_tool.on_release(QPointF())
                    self.viewport().update()
                return True
            if ev.key() == Qt.Key.Key_Escape:
                self._dim_input.setVisible(False)
                self._dim_input.clear()
                self.setFocus()
                return True
        return super().eventFilter(obj, ev)

    def _apply_dim_value(self) -> None:
        text = self._dim_input.text().strip()
        if text:
            try:
                value = float(text)
                if self.active_tool:
                    self.active_tool.set_dimension(value)
                    self.viewport().update()
            except ValueError:
                pass

    # --------------------------------------------------------- tools / document
    def set_tool(self, tool) -> None:
        if self.active_tool is not None:
            self.active_tool.deactivate()
        self.active_tool = tool
        if tool is not None:
            tool.activate()
        self.viewport().update()

    def current_stroke(self) -> str:
        return self._stroke_color

    def set_stroke(self, color: str) -> None:
        self._stroke_color = color

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
        """Items selectable under the current layer mode (parti/both/trace)."""
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

    def select_in_rect(self, rect: QRectF, additive: bool = False) -> None:
        if not additive:
            self.scene().clearSelection()
        allowed = self._active_layer_items()
        for it in self.scene().items(rect):
            if it in allowed and bool(it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
                it.setSelected(True)

    def delete_selected(self) -> None:
        items = self.scene().selectedItems()
        if items and self.undo_stack is not None and self.document is not None:
            self.undo_stack.push(DeleteItemsCommand(self.document, items))

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

        # ── Find clicked sub-segment ──
        t_click = ((click.x() - p1.x()) * dx + (click.y() - p1.y()) * dy) / length_sq
        t_click = max(0.0, min(1.0, t_click))

        trim_left, trim_right = 0.0, 1.0
        for i in range(len(sorted_t) - 1):
            if sorted_t[i] - 1e-9 <= t_click <= sorted_t[i + 1] + 1e-9:
                trim_left = sorted_t[i]
                trim_right = sorted_t[i + 1]
                break

        # ── Atomic: delete original, keep exploded edges + remnants ──
        pen = item.pen()
        meta = item.data(0) or {"zip": "", "note": ""}
        layer = self.document.layer_for(item)
        if layer is None:
            return

        self.undo_stack.beginMacro("Trim")
        self.undo_stack.push(DeleteItemsCommand(self.document, [item]))

        # Keep other edges as individual lines (explode)
        for s in others:
            if s.length() > 1e-6:
                li = QGraphicsLineItem(s)
                li.setPen(pen)
                li.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                li.setData(0, dict(meta))
                self.undo_stack.push(AddItemCommand(layer, li))

        # Remnants of the trimmed edge
        if trim_left > 1e-9:
            pa = QPointF(p1)
            pb = QPointF(p1.x() + trim_left * dx, p1.y() + trim_left * dy)
            li = QGraphicsLineItem(QLineF(pa, pb))
            li.setPen(pen)
            li.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            li.setData(0, dict(meta))
            self.undo_stack.push(AddItemCommand(layer, li))

        if trim_right < 1.0 - 1e-9:
            pa = QPointF(p1.x() + trim_right * dx, p1.y() + trim_right * dy)
            pb = QPointF(p2)
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
        # Resize handles on selected pixmap items
        self._draw_resize_handles(painter)
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
            # Check resize handles first (before tool routing)
            raw_scene = self.mapToScene(event.position().toPoint())
            item, hidx = self._hit_handle(raw_scene)
            if item is not None:
                self._start_resize(item, hidx, raw_scene)
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
        # Apply any pending Tab dimension before committing the shape
        if event.button() == Qt.MouseButton.LeftButton and self._dim_input.isVisible():
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
        # Auto-type dimensions: digit/period keys open dim input while drawing
        if (self._tool_active() and self.active_tool.in_progress
                and not self._dim_input.isVisible()
                and event.text() and event.text() in "0123456789."):
            self._show_dim_input()
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
        if event.key() == Qt.Key.Key_X and not event.isAutoRepeat():
            self._wireframe = not self._wireframe
            self.viewport().update()
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
        super().keyReleaseEvent(event)

    # ----------------------------------------- drag-and-drop (reference images)
    def dragEnterEvent(self, event) -> None:
        md = event.mimeData()
        if md.hasImage() or md.hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasImage() or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        md = event.mimeData()
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

    # ----------------------------------------- image resize handles
    def _selected_pixmap(self):
        """Return the single selected QGraphicsPixmapItem, if any."""
        from PySide6.QtWidgets import QGraphicsPixmapItem
        sel = self.scene().selectedItems()
        if len(sel) == 1 and isinstance(sel[0], QGraphicsPixmapItem):
            return sel[0]
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
        pix = self._selected_pixmap()
        if pix is None:
            return
        handles = self._handle_rects(pix)
        pen = QPen(QColor("#2464E5"))
        pen.setCosmetic(True)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        for hr in handles:
            painter.drawRect(hr)

    def _hit_handle(self, scene_pos: QPointF):
        """Return (item, handle_index) if scene_pos hits a resize handle, else (None, None)."""
        pix = self._selected_pixmap()
        if pix is None:
            return None, None
        for i, hr in enumerate(self._handle_rects(pix)):
            if hr.contains(scene_pos):
                return pix, i
        return None, None

    def _start_resize(self, item, handle_idx, scene_pos):
        self._resize_handle = handle_idx
        self._resize_item = item
        self._resize_anchor = QPointF(scene_pos)
        br = item.mapToScene(item.boundingRect()).boundingRect()
        self._resize_origin = QRectF(br)

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
        # Apply: reposition + rescale the pixmap
        item = self._resize_item
        pm = item.pixmap()
        item.setPos(r.topLeft())
        sx = r.width() / pm.width()
        sy = r.height() / pm.height()
        from PySide6.QtGui import QTransform
        item.setTransform(QTransform.fromScale(sx, sy))
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

    def _on_dim_confirm(self) -> None:
        """Apply the typed dimension to the active tool (Enter key)."""
        self._apply_dim_value()
        self._dim_input.setVisible(False)
        self._dim_input.clear()
        self.setFocus()

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
        data = item.data(0)
        pos = item.pos()
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            return ("line", QLineF(item.mapToScene(ln.p1()), item.mapToScene(ln.p2())),
                    pen, data)
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            return ("rect", QRectF(tl, br), pen, data)
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            return ("ellipse", QRectF(tl, br), pen, data)
        elif isinstance(item, QGraphicsPathItem):
            # Clone the path in scene coords
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
            return ("path", sp, pen, data)
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
