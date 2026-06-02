"""Drawing tools. GRAPH PARTI — vector draw + trim + paint.

Measurement: all user-facing dimensions are in **grid units** (1 = 1 grid cell).
Internally scene units = grid_units × grid_spacing.

Ortho: when ortho is enabled (separate from snap), lines/polylines constrain to the
nearest angle multiple (90° = H/V, 45° = +diagonals, etc.).
"""
from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
)

DEFAULT_STROKE = "#3C3C3C"
DEFAULT_WIDTH = 1.0
MIN_DRAG = 1e-6


def make_pen(color: str, width: float) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCosmetic(True)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


def _ortho_snap(start: QPointF, p: QPointF, angle_step: int = 90) -> QPointF:
    """Constrain *p* to the nearest angle multiple of *angle_step* from *start*."""
    dx = p.x() - start.x()
    dy = p.y() - start.y()
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return QPointF(start)
    angle = math.degrees(math.atan2(dy, dx))
    snapped = round(angle / angle_step) * angle_step
    rad = math.radians(snapped)
    return QPointF(start.x() + dist * math.cos(rad),
                   start.y() + dist * math.sin(rad))


def _dim_text(v: float) -> str:
    return str(int(round(v))) if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _draw_dim_label(painter: QPainter, scene_pt: QPointF, text: str) -> None:
    vp = painter.transform().map(scene_pt)
    painter.save()
    painter.resetTransform()
    f = painter.font()
    f.setPixelSize(11)
    painter.setFont(f)
    painter.setPen(QPen(QColor("#3C3C3C")))
    painter.drawText(QPointF(vp.x() + 6, vp.y() - 4), text)
    painter.restore()


def _flood_fill(img: QImage, x: int, y: int, fill_pixel: int) -> None:
    """Stack-based flood fill on a QImage (ARGB32). Replaces the target pixel color."""
    w, h = img.width(), img.height()
    target = img.pixel(x, y)
    if target == fill_pixel:
        return
    stack = [(x, y)]
    while stack:
        px, py = stack.pop()
        if 0 <= px < w and 0 <= py < h and img.pixel(px, py) == target:
            img.setPixel(px, py, fill_pixel)
            stack.append((px + 1, py))
            stack.append((px - 1, py))
            stack.append((px, py + 1))
            stack.append((px, py - 1))


def _item_segments(item) -> list[QLineF]:
    """Extract line segments (scene coords) from a vector item."""
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
    return segs


def _gs(canvas) -> int:
    return getattr(canvas, 'grid_spacing', 20)


# ═══════════════════════════════════════════════════════════ base
class Tool:
    name = "tool"

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self._preview_pen = QPen(QColor("#9255E5"))
        self._preview_pen.setCosmetic(True)
        self._preview_pen.setWidthF(1.5)
        self._preview_pen.setStyle(Qt.PenStyle.DashLine)
        self.reset()

    @property
    def in_progress(self) -> bool:
        return False

    def activate(self) -> None:
        self.reset()

    def deactivate(self) -> None:
        self.reset()

    def cancel(self) -> None:
        self.reset()

    def reset(self) -> None:
        pass

    def on_press(self, p: QPointF) -> None: ...
    def on_move(self, p: QPointF) -> None: ...
    def on_release(self, p: QPointF) -> None: ...
    def on_double_click(self, p: QPointF) -> None: ...
    def on_key(self, key) -> None: ...
    def paint_preview(self, painter: QPainter) -> None: ...

    def idle_right_click(self, p: QPointF) -> None:
        self.canvas.trim_at(p)

    def set_dimension(self, value: float) -> None:
        pass

    def _apply_ortho(self, start: QPointF, p: QPointF) -> QPointF:
        """Apply ortho constraint if enabled."""
        if getattr(self.canvas, '_ortho_enabled', False):
            angle = getattr(self.canvas, '_ortho_angle', 90)
            return _ortho_snap(start, p, angle)
        return QPointF(p)

    def _commit(self, item: QGraphicsItem) -> None:
        item.setPen(make_pen(self.canvas.current_stroke(), DEFAULT_WIDTH))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        self.canvas.add_item(item)


# ═══════════════════════════════════════════════════════════ line
class LineTool(Tool):
    name = "line"

    @property
    def in_progress(self) -> bool:
        return self._drawing

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._drawing = False
        self._dim_locked = False

    def on_press(self, p: QPointF) -> None:
        self._start = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True
        self._dim_locked = False

    def on_move(self, p: QPointF) -> None:
        if self._drawing and self._start is not None and not self._dim_locked:
            self._cur = self._apply_ortho(self._start, p)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        if self._dim_locked:
            end = self._cur  # Tab-typed: use the locked dimension
        else:
            end = self._apply_ortho(self._start, p)  # Normal: use release pos
        line = QLineF(self._start, end)
        if line.length() > MIN_DRAG:
            self._commit(QGraphicsLineItem(line))
        self.reset()

    def set_dimension(self, value: float) -> None:
        gs = _gs(self.canvas)
        if self._drawing and self._start is not None and self._cur is not None:
            line = QLineF(self._start, self._cur)
            if line.length() > 1e-6:
                line.setLength(value * gs)
                self._cur = line.p2()
                self._dim_locked = True

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._start is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            line = QLineF(self._start, self._cur)
            painter.drawLine(line)
            gs = _gs(self.canvas)
            length = line.length() / gs
            if length > 0.1:
                mid = QPointF((self._start.x() + self._cur.x()) / 2,
                              (self._start.y() + self._cur.y()) / 2)
                _draw_dim_label(painter, mid, _dim_text(length))


# ═══════════════════════════════════════════════════════════ rect
class RectTool(Tool):
    name = "rect"

    @property
    def in_progress(self) -> bool:
        return self._drawing

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._drawing = False
        self._dim_phase = 0
        self._dim_locked = False

    def on_press(self, p: QPointF) -> None:
        self._start = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True
        self._dim_phase = 0
        self._dim_locked = False

    def on_move(self, p: QPointF) -> None:
        if self._drawing and not self._dim_locked:
            self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        end = self._cur if self._dim_locked else QPointF(p)
        r = QRectF(self._start, end).normalized()
        if r.width() > MIN_DRAG or r.height() > MIN_DRAG:
            self._commit(QGraphicsRectItem(r))
        self.reset()

    def set_dimension(self, value: float) -> None:
        gs = _gs(self.canvas)
        scene_val = value * gs
        if self._drawing and self._start is not None and self._cur is not None:
            sx = 1.0 if self._cur.x() >= self._start.x() else -1.0
            sy = 1.0 if self._cur.y() >= self._start.y() else -1.0
            if self._dim_phase == 0:
                self._cur = QPointF(self._start.x() + sx * scene_val, self._cur.y())
                self._dim_phase = 1
            else:
                self._cur = QPointF(self._cur.x(), self._start.y() + sy * scene_val)
                self._dim_phase = 0
                self._dim_locked = True

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._start is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            r = QRectF(self._start, self._cur).normalized()
            painter.drawRect(r)
            gs = _gs(self.canvas)
            if r.width() > 1 or r.height() > 1:
                label = f"{_dim_text(r.width()/gs)} × {_dim_text(r.height()/gs)}"
                _draw_dim_label(painter, QPointF(r.right(), r.bottom()), label)


# ═══════════════════════════════════════════════════════════ circle
class CircleTool(Tool):
    name = "circle"

    @property
    def in_progress(self) -> bool:
        return self._drawing

    def reset(self) -> None:
        self._center = None
        self._cur = None
        self._drawing = False
        self._dim_locked = False

    def on_press(self, p: QPointF) -> None:
        self._center = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True
        self._dim_locked = False

    def on_move(self, p: QPointF) -> None:
        if self._drawing and not self._dim_locked:
            self._cur = QPointF(p)

    def _rect_for(self, edge: QPointF) -> QRectF:
        r = QLineF(self._center, edge).length()
        return QRectF(self._center.x() - r, self._center.y() - r, 2 * r, 2 * r)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        end = self._cur if self._dim_locked else QPointF(p)
        if QLineF(self._center, end).length() > MIN_DRAG:
            self._commit(QGraphicsEllipseItem(self._rect_for(end)))
        self.reset()

    def set_dimension(self, value: float) -> None:
        gs = _gs(self.canvas)
        if self._drawing and self._center is not None:
            self._cur = QPointF(self._center.x() + value * gs, self._center.y())
            self._dim_locked = True

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._center is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawEllipse(self._rect_for(self._cur))
            gs = _gs(self.canvas)
            radius = QLineF(self._center, self._cur).length() / gs
            if radius > 0.1:
                _draw_dim_label(painter, self._cur, f"r={_dim_text(radius)}")


# ═══════════════════════════════════════════════════════════ polyline
class PolylineTool(Tool):
    name = "polyline"

    @property
    def in_progress(self) -> bool:
        return bool(self._pts)

    def reset(self) -> None:
        self._pts: list[QPointF] = []
        self._cur = None

    def on_press(self, p: QPointF) -> None:
        actual = self._apply_ortho(self._pts[-1], p) if self._pts else p
        if len(self._pts) >= 3 and self._is_start(actual):
            self._finish(closed=True)
            return
        self._pts.append(QPointF(actual))
        self._cur = QPointF(actual)

    def _is_start(self, p: QPointF) -> bool:
        eps = _gs(self.canvas) * 0.5
        return QLineF(p, self._pts[0]).length() <= eps

    def on_move(self, p: QPointF) -> None:
        if self._pts:
            self._cur = self._apply_ortho(self._pts[-1], p)
        else:
            self._cur = QPointF(p)

    def on_double_click(self, p: QPointF) -> None:
        self._finish()

    def on_key(self, key) -> None:
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish()
        elif key == Qt.Key.Key_Escape:
            self.reset()
            self.canvas.viewport().update()

    def _path(self, include_cursor: bool) -> QPainterPath:
        path = QPainterPath(self._pts[0])
        for pt in self._pts[1:]:
            path.lineTo(pt)
        if include_cursor and self._cur is not None:
            path.lineTo(self._cur)
        return path

    def _finish(self, closed: bool = False) -> None:
        if len(self._pts) >= 2:
            path = self._path(include_cursor=False)
            if closed and len(self._pts) >= 3:
                path.closeSubpath()
            self._commit(QGraphicsPathItem(path))
        self.reset()
        self.canvas.viewport().update()

    def paint_preview(self, painter: QPainter) -> None:
        if not self._pts:
            return
        painter.setPen(self._preview_pen)
        painter.drawPath(self._path(include_cursor=True))
        if self._cur is not None and self._pts:
            gs = _gs(self.canvas)
            seg = QLineF(self._pts[-1], self._cur)
            if seg.length() > 1:
                mid = QPointF((self._pts[-1].x() + self._cur.x()) / 2,
                              (self._pts[-1].y() + self._cur.y()) / 2)
                _draw_dim_label(painter, mid, _dim_text(seg.length() / gs))


# ═══════════════════════════════════════════════════════════ select
class SelectTool(Tool):
    """Select: pick/move/band-select (layer-isolated). Shift+click = multi-select.
    Right-click = delete selected."""
    name = "select"

    @property
    def in_progress(self) -> bool:
        return self._mode is not None

    def reset(self) -> None:
        self._mode = None
        self._anchor = None
        self._orig: dict = {}
        self._band_start = None
        self._band_cur = None
        self._moved = False
        self._shift = False

    def on_press(self, p: QPointF) -> None:
        scene = self.canvas.scene()
        # Check for Shift modifier (multi-select)
        from PySide6.QtWidgets import QApplication
        self._shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)

        pick = self.canvas.pick_item(p)
        if pick is not None:
            if self._shift:
                # Shift+click: toggle selection on this item
                pick.setSelected(not pick.isSelected())
                self._mode = None  # no move on shift-click
                return
            if not pick.isSelected():
                scene.clearSelection()
                pick.setSelected(True)
            self._mode = "move"
            self._anchor = QPointF(p)
            self._moved = False
            self._orig = {it: it.pos() for it in scene.selectedItems()}
        else:
            if not self._shift:
                scene.clearSelection()
            self._mode = "band"
            self._band_start = QPointF(p)
            self._band_cur = QPointF(p)

    def on_move(self, p: QPointF) -> None:
        if self._mode == "move":
            d = p - self._anchor
            if d.x() or d.y():
                self._moved = True
            for it, orig in self._orig.items():
                it.setPos(orig + d)
        elif self._mode == "band":
            self._band_cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if self._mode == "move" and self._moved:
            d = p - self._anchor
            for it, orig in self._orig.items():
                it.setPos(orig)
            self.canvas.push_move(list(self._orig.keys()), d.x(), d.y())
        elif self._mode == "band" and self._band_start is not None:
            self.canvas.select_in_rect(
                QRectF(self._band_start, self._band_cur).normalized(),
                additive=self._shift,
            )
        self.reset()

    def idle_right_click(self, p: QPointF) -> None:
        """Right-click = delete selected items, or the item under cursor if none selected."""
        items = list(self.canvas.scene().selectedItems())
        if not items:
            pick = self.canvas.pick_item(p)
            if pick:
                items = [pick]
        if items and self.canvas.undo_stack and self.canvas.document:
            from .commands import DeleteItemsCommand
            self.canvas.undo_stack.push(
                DeleteItemsCommand(self.canvas.document, items)
            )

    def paint_preview(self, painter: QPainter) -> None:
        if self._mode == "band" and self._band_start is not None and self._band_cur is not None:
            pen = QPen(QColor("#2464E5"))
            pen.setCosmetic(True)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(self._band_start, self._band_cur).normalized())


# ═══════════════════════════════════════════════════════════ trim
class TrimTool(Tool):
    name = "trim"

    def on_press(self, p: QPointF) -> None:
        self.canvas.trim_at(p)


# ═══════════════════════════════════════════════════════════ paint
class OffsetTool(Tool):
    """Offset: click a line, type distance, offset a parallel copy in cursor direction.
    After clicking the source, a dim input pops up to type the distance."""
    name = "offset"

    def reset(self) -> None:
        self._source = None
        self._click_pos = None
        self._waiting = False  # True = waiting for dim input before offsetting

    def on_press(self, p: QPointF) -> None:
        pick = self.canvas.pick_item(p)
        if pick is None:
            return
        self._source = pick
        self._click_pos = QPointF(p)
        self._waiting = True
        # Show dim input — user types distance, Enter/Tab confirms
        # The view's event() will detect in_progress and show dim input on Tab/digit

    @property
    def in_progress(self) -> bool:
        return self._waiting

    def set_dimension(self, value: float) -> None:
        """Distance typed → execute the offset now."""
        if not self._waiting or self._source is None or self._click_pos is None:
            return
        self._do_offset(self._source, self._click_pos, value)
        self._waiting = False

    def _do_offset(self, item, click: QPointF, dist_grid: float) -> None:
        gs = _gs(self.canvas)
        d = dist_grid * gs
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            p1 = item.mapToScene(ln.p1())
            p2 = item.mapToScene(ln.p2())
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.hypot(dx, dy)
            if length < 1e-6:
                return
            nx, ny = -dy / length, dx / length
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            if (click.x() - mid.x()) * nx + (click.y() - mid.y()) * ny < 0:
                nx, ny = -nx, -ny
            op1 = QPointF(p1.x() + nx * d, p1.y() + ny * d)
            op2 = QPointF(p2.x() + nx * d, p2.y() + ny * d)
            new_item = QGraphicsLineItem(QLineF(op1, op2))
            new_item.setPen(item.pen())
            new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            new_item.setData(0, {"zip": "", "note": ""})
            self.canvas.add_item(new_item)
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            center = r.center()
            out = (QLineF(center, click).length() > QLineF(center, r.topLeft()).length())
            nr = r.adjusted(-d, -d, d, d) if out else r.adjusted(d, d, -d, -d)
            if nr.width() > 0 and nr.height() > 0:
                new_item = QGraphicsRectItem(nr)
                new_item.setPen(item.pen())
                new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                new_item.setData(0, {"zip": "", "note": ""})
                self.canvas.add_item(new_item)
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            center = r.center()
            out = (QLineF(center, click).length() > r.width() / 2)
            nr = r.adjusted(-d, -d, d, d) if out else r.adjusted(d, d, -d, -d)
            if nr.width() > 0 and nr.height() > 0:
                new_item = QGraphicsEllipseItem(nr)
                new_item.setPen(item.pen())
                new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                new_item.setData(0, {"zip": "", "note": ""})
                self.canvas.add_item(new_item)


class PaintTool(Tool):
    """Region flood-fill: fills the closed region you click on (bounded by lines + grid)."""
    name = "paint"

    _RES = 4  # render resolution multiplier (4× = 80px per cell at gs=20)

    def reset(self) -> None:
        self._painting = False
        self._filled_cells: set[tuple[float, float]] = set()
        if not hasattr(self, '_color'):
            self._color = QColor("#C1140C")  # only set default on first init
        self._erasing = False
        self._erased_ids: set[int] = set()

    @property
    def in_progress(self) -> bool:
        return self._painting

    def set_color(self, color) -> None:
        self._color = QColor(color)

    # ── left-click: paint region ──
    def on_press(self, p: QPointF) -> None:
        self._painting = True
        self._filled_cells = set()
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Paint region")
        self._fill_region(p)

    def on_move(self, p: QPointF) -> None:
        if self._painting:
            self._fill_region(p)  # geometry-aware even when dragging

    def on_release(self, p: QPointF) -> None:
        if self._painting:
            self._fill_region(p)
            us = self.canvas.undo_stack
            if us:
                us.endMacro()
            self._painting = False
            self._filled_cells = set()

    def cancel(self) -> None:
        if self._painting:
            us = self.canvas.undo_stack
            if us:
                us.endMacro()
                us.undo()
            self._painting = False
            self._filled_cells = set()

    # ── right-click: drag-erase ──
    def on_right_press(self, p: QPointF) -> None:
        self._erasing = True
        self._erased_ids = set()
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Erase fills")
        self._erase_at(p)

    def on_right_move(self, p: QPointF) -> None:
        if self._erasing:
            self._erase_at(p)

    def on_right_release(self, p: QPointF) -> None:
        if self._erasing:
            us = self.canvas.undo_stack
            if us:
                us.endMacro()
            self._erasing = False
            self._erased_ids = set()

    _FILL_RADIUS = 15  # cells around click to render for flood fill

    # ── region-aware flood fill ──
    def _fill_region(self, click: QPointF) -> None:
        gs = _gs(self.canvas)
        cell_key = (math.floor(click.x() / gs) * gs, math.floor(click.y() / gs) * gs)
        if cell_key in self._filled_cells:
            return

        N = self._FILL_RADIUS
        area_x = cell_key[0] - N * gs
        area_y = cell_key[1] - N * gs
        area_w = (2 * N + 1) * gs
        area_h = (2 * N + 1) * gs
        area = QRectF(area_x, area_y, area_w, area_h)
        iw, ih = int(area_w), int(area_h)

        # ── render barriers ──
        img = QImage(iw, ih, QImage.Format.Format_ARGB32)
        img.fill(0)  # transparent = fillable space

        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        # Use a NON-black barrier color so black fill doesn't collide
        barrier = QPen(QColor(1, 0, 1, 255))  # barrier marker (never a real fill color)
        barrier.setWidthF(1.0)
        p.setPen(barrier)

        # Grid lines as barriers (only if wireframe is on)
        if getattr(self.canvas, '_wireframe', True):
            gx = int(math.ceil(area_x / gs) * gs)
            while gx <= area_x + area_w:
                ix = int(gx - area_x)
                p.drawLine(ix, 0, ix, ih - 1)
                gx += gs
            gy = int(math.ceil(area_y / gs) * gs)
            while gy <= area_y + area_h:
                iy = int(gy - area_y)
                p.drawLine(0, iy, iw - 1, iy)
                gy += gs

        # All vector geometry as barriers
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if item.data(1) == "cell_fill":
                    continue
                if not item.sceneBoundingRect().intersects(area):
                    continue
                for seg in _item_segments(item):
                    x1 = seg.p1().x() - area_x
                    y1 = seg.p1().y() - area_y
                    x2 = seg.p2().x() - area_x
                    y2 = seg.p2().y() - area_y
                    p.drawLine(QLineF(x1, y1, x2, y2))
        p.end()

        # Save clean barrier state (before flood fill modifies the image)
        barrier_snap = img.copy()

        # Flood fill from click (nudge if on a barrier)
        fx = max(0, min(int(click.x() - area_x), iw - 1))
        fy = max(0, min(int(click.y() - area_y), ih - 1))
        if img.pixel(fx, fy) != 0:
            fx = max(0, min(int(cell_key[0] + gs / 2 - area_x), iw - 1))
            fy = max(0, min(int(cell_key[1] + gs / 2 - area_y), ih - 1))
            if img.pixel(fx, fy) != 0:
                return

        fill_c = QColor(self._color.red(), self._color.green(), self._color.blue(), 255)
        fill_px = fill_c.rgba()
        _flood_fill(img, fx, fy, fill_px)

        # Extract only NEWLY filled pixels (was transparent before, is fill now).
        # This fixes the black-fill bug: barriers are stripped regardless of color.
        for iy in range(ih):
            for ix in range(iw):
                was_empty = (barrier_snap.pixel(ix, iy) == 0)
                is_filled = (img.pixel(ix, iy) == fill_px)
                if was_empty and is_filled:
                    ck = (math.floor((area_x + ix) / gs) * gs,
                          math.floor((area_y + iy) / gs) * gs)
                    self._filled_cells.add(ck)
                else:
                    img.setPixel(ix, iy, 0)

        filled = QGraphicsPixmapItem(QPixmap.fromImage(img))
        filled.setPos(area_x, area_y)
        filled.setOpacity(0.7)
        filled.setData(0, {"zip": "", "note": ""})
        filled.setData(1, "cell_fill")
        filled.setData(2, self._color.name())
        filled.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.canvas.add_item(filled)

    # ── fast cell fill (drag) ──
    def _fill_cell(self, p: QPointF) -> None:
        gs = _gs(self.canvas)
        cx = math.floor(p.x() / gs) * gs
        cy = math.floor(p.y() / gs) * gs
        key = (cx, cy)
        if key in self._filled_cells:
            return
        self._filled_cells.add(key)
        rect = QGraphicsRectItem(QRectF(cx, cy, gs, gs))
        rect.setBrush(QBrush(self._color))
        rect.setPen(QPen(Qt.PenStyle.NoPen))
        rect.setData(0, {"zip": "", "note": ""})
        rect.setData(1, "cell_fill")
        rect.setData(2, self._color.name())
        rect.setOpacity(0.7)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.canvas.add_item(rect)

    # ── erase fill at click point ──
    def _erase_at(self, p: QPointF) -> None:
        for item in self.canvas.scene().items(p):
            if item.data(1) == "cell_fill" and id(item) not in self._erased_ids:
                self._erased_ids.add(id(item))
                if self.canvas.undo_stack and self.canvas.document:
                    from .commands import DeleteItemsCommand
                    self.canvas.undo_stack.push(
                        DeleteItemsCommand(self.canvas.document, [item])
                    )
                break
