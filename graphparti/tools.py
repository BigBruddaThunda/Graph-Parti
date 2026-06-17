"""Drawing tools. GRAPH PARTI — vector draw + trim + paint.

Measurement: all user-facing dimensions are in **grid units** (1 = 1 grid cell).
Internally scene units = grid_units × grid_spacing.

Ortho: when ortho is enabled (separate from snap), lines/polylines constrain to the
nearest angle multiple (90° = H/V, 45° = +diagonals, etc.).
"""
from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QTransform,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
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
    if abs(v - round(v)) < 0.005:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


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
    elif isinstance(item, QGraphicsEllipseItem):
        r = item.rect()
        cx = (r.left() + r.right()) / 2.0
        cy = (r.top() + r.bottom()) / 2.0
        rx, ry = r.width() / 2.0, r.height() / 2.0
        n = 72
        pts = [item.mapToScene(QPointF(
            cx + rx * math.cos(2.0 * math.pi * i / n),
            cy + ry * math.sin(2.0 * math.pi * i / n)))
            for i in range(n + 1)]
        for a, b in zip(pts, pts[1:]):
            segs.append(QLineF(a, b))
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

    def on_right_press(self, p: QPointF) -> None:
        self._rt_start = QPointF(p)
        self._rt_cur = QPointF(p)
        self._rt_dragged = False

    def on_right_move(self, p: QPointF) -> None:
        if hasattr(self, '_rt_start') and self._rt_start is not None:
            self._rt_cur = QPointF(p)
            if QLineF(self._rt_start, p).length() > _gs(self.canvas) * 0.3:
                self._rt_dragged = True

    def on_right_release(self, p: QPointF) -> None:
        if getattr(self, '_rt_dragged', False):
            self.canvas.trim_fence(self._rt_start, QPointF(p))
        else:
            self.idle_right_click(QPointF(p))
        self._rt_start = None
        self._rt_cur = None
        self._rt_dragged = False

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
        fill = getattr(self.canvas, '_fill_color', None)
        if fill is not None and hasattr(item, 'setBrush'):
            c = QColor(fill)
            c.setAlpha(180)
            item.setBrush(QBrush(c))
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


# ═══════════════════════════════════════════════════════════ ellipse
class EllipseTool(Tool):
    """2-point axis + drag width. Click two axis endpoints, move cursor
    perpendicular to set the minor-axis width, click to commit."""
    name = "ellipse"

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def reset(self) -> None:
        self._p1 = None
        self._p2 = None
        self._cursor = None
        self._phase = 0

    def cancel(self) -> None:
        self.reset()
        self.canvas.viewport().update()

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            self.cancel()

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            self._p1 = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._p2 = self._apply_ortho(self._p1, p)
            self._phase = 2
        elif self._phase == 2:
            self._commit_ellipse(QPointF(p))

    def on_move(self, p: QPointF) -> None:
        if self._phase == 1 and self._p1:
            self._cursor = self._apply_ortho(self._p1, p)
        else:
            self._cursor = QPointF(p)

    def _perp_dist(self, p: QPointF) -> float:
        dx = self._p2.x() - self._p1.x()
        dy = self._p2.y() - self._p1.y()
        length = math.hypot(dx, dy)
        if length < 1e-6:
            return 0.0
        return abs((p.x() - self._p1.x()) * (-dy / length) +
                   (p.y() - self._p1.y()) * (dx / length))

    def _commit_ellipse(self, p3: QPointF) -> None:
        if self._p1 is None or self._p2 is None:
            self.reset()
            return
        a = QLineF(self._p1, self._p2).length() / 2
        b = self._perp_dist(p3)
        if a < MIN_DRAG or b < MIN_DRAG:
            self.reset()
            return
        cx = (self._p1.x() + self._p2.x()) / 2
        cy = (self._p1.y() + self._p2.y()) / 2
        angle = math.degrees(math.atan2(
            self._p2.y() - self._p1.y(), self._p2.x() - self._p1.x()))
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), a, b)
        item = QGraphicsPathItem(path)
        tf = QTransform()
        tf.translate(cx, cy)
        tf.rotate(angle)
        item.setTransform(tf)
        self._commit(item)
        self.reset()
        self.canvas.viewport().update()

    def paint_preview(self, painter: QPainter) -> None:
        painter.setPen(self._preview_pen)
        if self._phase == 1 and self._p1 and self._cursor:
            painter.drawLine(QLineF(self._p1, self._cursor))
            gs = _gs(self.canvas)
            length = QLineF(self._p1, self._cursor).length() / gs
            if length > 0.1:
                _draw_dim_label(painter, self._cursor, _dim_text(length))
        elif self._phase == 2 and self._p1 and self._p2 and self._cursor:
            a = QLineF(self._p1, self._p2).length() / 2
            b = self._perp_dist(self._cursor)
            if a > 1 and b > 1:
                cx = (self._p1.x() + self._p2.x()) / 2
                cy = (self._p1.y() + self._p2.y()) / 2
                angle = math.degrees(math.atan2(
                    self._p2.y() - self._p1.y(), self._p2.x() - self._p1.x()))
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(angle)
                painter.drawEllipse(QPointF(0, 0), a, b)
                painter.restore()
                gs = _gs(self.canvas)
                _draw_dim_label(painter, self._cursor,
                                f"{_dim_text(2*a/gs)} × {_dim_text(2*b/gs)}")


# ═══════════════════════════════════════════════════════════ arc
class ArcTool(Tool):
    """3-click arc: start → end → drag through-point to define curvature."""
    name = "arc"

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def reset(self) -> None:
        self._p1 = None
        self._p2 = None
        self._cursor = None
        self._phase = 0

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            self._p1 = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._p2 = QPointF(p)
            self._phase = 2
        elif self._phase == 2:
            self._commit_arc(QPointF(p))

    def on_move(self, p: QPointF) -> None:
        self._cursor = QPointF(p)

    def cancel(self) -> None:
        self.reset()
        self.canvas.viewport().update()

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            self.cancel()

    def _arc_path(self, p1, p2, p3) -> QPainterPath | None:
        """Compute circular arc from p1 through p3 to p2."""
        ax, ay = p1.x(), p1.y()
        bx, by = p2.x(), p2.y()
        cx, cy = p3.x(), p3.y()
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-9:
            path = QPainterPath(p1)
            path.lineTo(p2)
            return path
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) +
              (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) +
              (cx * cx + cy * cy) * (bx - ax)) / d
        r = math.hypot(ax - ux, ay - uy)
        ang_start = math.degrees(math.atan2(-(ay - uy), ax - ux))
        ang_end = math.degrees(math.atan2(-(by - uy), bx - ux))
        ang_mid = math.degrees(math.atan2(-(cy - uy), cx - ux))

        def _norm(a):
            return a % 360

        ccw_to_mid = _norm(ang_mid - ang_start)
        ccw_to_end = _norm(ang_end - ang_start)
        if ccw_to_mid <= ccw_to_end:
            sweep = ccw_to_end
        else:
            sweep = ccw_to_end - 360

        rect = QRectF(ux - r, uy - r, 2 * r, 2 * r)
        path = QPainterPath()
        path.arcMoveTo(rect, ang_start)
        path.arcTo(rect, ang_start, sweep)
        return path

    def _commit_arc(self, p3: QPointF) -> None:
        path = self._arc_path(self._p1, self._p2, p3)
        if path is not None:
            self._commit(QGraphicsPathItem(path))
        self.reset()
        self.canvas.viewport().update()

    def paint_preview(self, painter: QPainter) -> None:
        painter.setPen(self._preview_pen)
        if self._phase == 1 and self._p1 is not None and self._cursor is not None:
            painter.drawLine(QLineF(self._p1, self._cursor))
        elif self._phase == 2 and self._p1 is not None and self._p2 is not None and self._cursor is not None:
            path = self._arc_path(self._p1, self._p2, self._cursor)
            if path is not None:
                painter.drawPath(path)


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
        eps = _gs(self.canvas) * 0.2
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
            gs = _gs(self.canvas)
            has_text = any(isinstance(it, QGraphicsTextItem) for it in self._orig)
            if has_text:
                d = QPointF(round(d.x() / gs) * gs, round(d.y() / gs) * gs)
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
    """Left-click = point trim (original). Left-click drag = fence trim
    (cuts every item the drag line crosses)."""
    name = "trim"

    @property
    def in_progress(self) -> bool:
        return self._dragging

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._dragging = False

    def on_press(self, p: QPointF) -> None:
        self._start = QPointF(p)
        self._cur = QPointF(p)
        self._dragging = True

    def on_move(self, p: QPointF) -> None:
        if self._dragging:
            self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if not self._dragging:
            return
        self._dragging = False
        end = QPointF(p)
        if QLineF(self._start, end).length() < _gs(self.canvas) * 0.3:
            self.canvas.trim_at(self._start)
        else:
            self.canvas.trim_fence(self._start, end)
        self.reset()

    def paint_preview(self, painter: QPainter) -> None:
        if self._dragging and self._start is not None and self._cur is not None:
            line = QLineF(self._start, self._cur)
            if line.length() > 1:
                pen = QPen(QColor("#C1140C"))
                pen.setCosmetic(True)
                pen.setWidthF(1.5)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(line)


# ═══════════════════════════════════════════════════════════ extend / fillet
class ExtendTool(Tool):
    """AutoCAD-style extend: click near a line endpoint → auto-extends to
    the nearest boundary (other geometry or grid).
    Right-click near two lines → fillet (trim/extend to meet).
    Works as a toolbar tool AND as a held-E modifier from any tool."""
    name = "extend"

    def reset(self) -> None:
        self._source_item = None
        self._source_end = None
        self._source_line_orig = None
        self._phase = 0
        self._cursor = None

    @property
    def in_progress(self) -> bool:
        return False

    def on_press(self, p: QPointF) -> None:
        item, end_idx = self._nearest_endpoint(p)
        if item is None:
            return
        orig = QLineF(item.line())
        target = self._find_extension_target(item, end_idx)
        if target is None:
            return
        if end_idx == 0:
            new_line = QLineF(target, orig.p2())
        else:
            new_line = QLineF(orig.p1(), target)
        us = self.canvas.undo_stack
        if us:
            from .commands import ReshapeCommand
            us.push(ReshapeCommand(item, orig, new_line))
        else:
            item.setLine(new_line)
        self.canvas.viewport().update()

    def _find_extension_target(self, item, end_idx) -> QPointF | None:
        """Project the line from the given endpoint and find the nearest
        intersection with any other geometry."""
        ln = item.line()
        p1 = item.mapToScene(ln.p1())
        p2 = item.mapToScene(ln.p2())
        if end_idx == 0:
            origin, dx, dy = p1, p1.x() - p2.x(), p1.y() - p2.y()
        else:
            origin, dx, dy = p2, p2.x() - p1.x(), p2.y() - p1.y()
        length = math.hypot(dx, dy)
        if length < 1e-6:
            return None
        dx /= length
        dy /= length
        max_dist = _gs(self.canvas) * 100
        ray_end = QPointF(origin.x() + dx * max_dist, origin.y() + dy * max_dist)
        ray = QLineF(origin, ray_end)
        best_pt = None
        best_dist = max_dist
        if self.canvas.document is None:
            return None
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for other in layer.items():
                if other is item:
                    continue
                for seg in _item_segments(other):
                    itype, ipt = ray.intersects(seg)
                    if itype == QLineF.IntersectionType.BoundedIntersection:
                        d = QLineF(origin, ipt).length()
                        if 1e-6 < d < best_dist:
                            best_dist = d
                            best_pt = QPointF(ipt)
        return best_pt

    def _nearest_endpoint(self, p: QPointF):
        best_item = None
        best_idx = None
        best_d = _gs(self.canvas) * 1.5
        if self.canvas.document is None:
            return None, None
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if isinstance(item, QGraphicsLineItem):
                    ln = item.line()
                    p1 = item.mapToScene(ln.p1())
                    p2 = item.mapToScene(ln.p2())
                    d1 = QLineF(p, p1).length()
                    d2 = QLineF(p, p2).length()
                    if d1 < best_d:
                        best_d, best_item, best_idx = d1, item, 0
                    if d2 < best_d:
                        best_d, best_item, best_idx = d2, item, 1
        return best_item, best_idx

    def _fillet_at(self, p: QPointF) -> None:
        if self.canvas.document is None:
            return
        lines = []
        for layer in self.canvas.document.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if isinstance(item, QGraphicsLineItem):
                    ln = item.line()
                    seg = QLineF(item.mapToScene(ln.p1()), item.mapToScene(ln.p2()))
                    d = self._pt_seg_dist(p, seg)
                    lines.append((d, item, seg))
        lines.sort(key=lambda x: x[0])
        if len(lines) < 2:
            return
        _, item_a, seg_a = lines[0]
        _, item_b, seg_b = lines[1]
        itype, ipt = seg_a.intersects(seg_b)
        if itype == QLineF.IntersectionType.NoIntersection:
            return
        us = self.canvas.undo_stack
        if us is None:
            return
        us.beginMacro("Fillet")
        from .commands import ReshapeCommand
        old_a = QLineF(item_a.line())
        da1 = QLineF(p, seg_a.p1()).length()
        da2 = QLineF(p, seg_a.p2()).length()
        new_a = QLineF(seg_a.p1(), ipt) if da1 < da2 else QLineF(ipt, seg_a.p2())
        new_a_l = QLineF(item_a.mapFromScene(new_a.p1()), item_a.mapFromScene(new_a.p2()))
        us.push(ReshapeCommand(item_a, old_a, new_a_l))
        old_b = QLineF(item_b.line())
        db1 = QLineF(p, seg_b.p1()).length()
        db2 = QLineF(p, seg_b.p2()).length()
        new_b = QLineF(seg_b.p1(), ipt) if db1 < db2 else QLineF(ipt, seg_b.p2())
        new_b_l = QLineF(item_b.mapFromScene(new_b.p1()), item_b.mapFromScene(new_b.p2()))
        us.push(ReshapeCommand(item_b, old_b, new_b_l))
        us.endMacro()
        self.canvas.viewport().update()

    @staticmethod
    def _pt_seg_dist(p: QPointF, seg: QLineF) -> float:
        a, b = seg.p1(), seg.p2()
        dx, dy = b.x() - a.x(), b.y() - a.y()
        lsq = dx * dx + dy * dy
        if lsq < 1e-12:
            return QLineF(p, a).length()
        t = max(0, min(1, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / lsq))
        return QLineF(p, QPointF(a.x() + t * dx, a.y() + t * dy)).length()


# ═══════════════════════════════════════════════════════════ paint
class OffsetTool(Tool):
    """Offset: click source → dim input auto-pops (last distance) → move cursor
    for direction → click to confirm. Right-click cancels."""
    name = "offset"
    _last_distance: float = 1.0

    def reset(self) -> None:
        self._source = None
        self._cursor = None
        self._phase = 0  # 0=pick source, 1=pick direction

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            pick = self.canvas.pick_item(p)
            if pick is None:
                return
            self._source = pick
            self._cursor = QPointF(p)
            self._phase = 1
            self.canvas.request_dim_input(p, _dim_text(self._last_distance))
        elif self._phase == 1:
            self._do_offset(self._source, self._cursor, self._last_distance)
            self._phase = 0

    def on_move(self, p: QPointF) -> None:
        if self._phase == 1:
            self._cursor = QPointF(p)

    def cancel(self) -> None:
        self.reset()
        self.canvas.viewport().update()

    def set_dimension(self, value: float) -> None:
        OffsetTool._last_distance = value

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase != 1 or self._source is None or self._cursor is None:
            return
        preview = self._compute_offset(self._source, self._cursor, self._last_distance)
        if preview is None:
            return
        painter.setPen(self._preview_pen)
        if isinstance(preview, QLineF):
            painter.drawLine(preview)
        elif isinstance(preview, QRectF):
            painter.drawRect(preview)

    def _compute_offset(self, item, cursor: QPointF, dist_grid: float):
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
                return None
            nx, ny = -dy / length, dx / length
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            if (cursor.x() - mid.x()) * nx + (cursor.y() - mid.y()) * ny < 0:
                nx, ny = -nx, -ny
            return QLineF(
                QPointF(p1.x() + nx * d, p1.y() + ny * d),
                QPointF(p2.x() + nx * d, p2.y() + ny * d))
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            sr = QRectF(tl, br).normalized()
            center = sr.center()
            out = (QLineF(center, cursor).length() > QLineF(center, sr.topLeft()).length())
            nr = sr.adjusted(-d, -d, d, d) if out else sr.adjusted(d, d, -d, -d)
            return nr if nr.width() > 0 and nr.height() > 0 else None
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            sr = QRectF(tl, br).normalized()
            center = sr.center()
            out = (QLineF(center, cursor).length() > sr.width() / 2)
            nr = sr.adjusted(-d, -d, d, d) if out else sr.adjusted(d, d, -d, -d)
            return nr if nr.width() > 0 and nr.height() > 0 else None
        return None

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
            if hasattr(item, 'brush'):
                new_item.setBrush(item.brush())
            new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
            new_item.setData(0, {"zip": "", "note": ""})
            self.canvas.add_item(new_item)
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            sr = QRectF(tl, br).normalized()
            center = sr.center()
            out = (QLineF(center, click).length() > QLineF(center, sr.topLeft()).length())
            nr = sr.adjusted(-d, -d, d, d) if out else sr.adjusted(d, d, -d, -d)
            if nr.width() > 0 and nr.height() > 0:
                new_item = QGraphicsRectItem(nr)
                new_item.setPen(item.pen())
                if hasattr(item, 'brush'):
                    new_item.setBrush(item.brush())
                new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                new_item.setData(0, {"zip": "", "note": ""})
                self.canvas.add_item(new_item)
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            tl = item.mapToScene(r.topLeft())
            br = item.mapToScene(r.bottomRight())
            sr = QRectF(tl, br).normalized()
            center = sr.center()
            out = (QLineF(center, click).length() > sr.width() / 2)
            nr = sr.adjusted(-d, -d, d, d) if out else sr.adjusted(d, d, -d, -d)
            if nr.width() > 0 and nr.height() > 0:
                new_item = QGraphicsEllipseItem(nr)
                new_item.setPen(item.pen())
                if hasattr(item, 'brush'):
                    new_item.setBrush(item.brush())
                new_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                new_item.setData(0, {"zip": "", "note": ""})
                self.canvas.add_item(new_item)


# ═══════════════════════════════════════════════════════════ divide
def _seg_dist(p: QPointF, seg: QLineF) -> float:
    a, b = seg.p1(), seg.p2()
    dx, dy = b.x() - a.x(), b.y() - a.y()
    lsq = dx * dx + dy * dy
    if lsq < 1e-12:
        return QLineF(p, a).length()
    t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / lsq))
    return QLineF(p, QPointF(a.x() + t * dx, a.y() + t * dy)).length()


class DivideTool(Tool):
    """Click a line / rect edge / polyline segment / circle → dim-input pops with
    the last-used division count (persists). Type N, live preview shows the tick
    marks, Enter (or click) commits N−1 interior points (N radial points for a
    circle). The points are real osnap targets. Right-click cancels."""
    name = "divide"
    _last_count: int = 4

    def reset(self) -> None:
        self._item = None
        self._pick_point = None
        self._count = DivideTool._last_count
        self._phase = 0       # 0 = pick segment, 1 = set count
        self._ready = False    # consumes the picking-click's own release
        self._preview_pts: list[QPointF] = []

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def cancel(self) -> None:
        self.reset()
        self.canvas.viewport().update()

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            pick = self.canvas.pick_item(p)
            if pick is None:
                return
            self._item = pick
            self._pick_point = QPointF(p)
            self._count = DivideTool._last_count
            self._ready = False
            self._phase = 1
            self._recompute_preview()
            self.canvas.request_dim_input(p, str(DivideTool._last_count))
        elif self._phase == 1:
            self._commit()

    def on_release(self, p: QPointF) -> None:
        if self._phase != 1:
            return
        if not self._ready:
            self._ready = True   # swallow the release from the picking click
            return
        self._commit()           # Enter-path: on_release(QPointF()) after count set

    def preview_dimension(self, value: float) -> None:
        """Live: update the preview as the user types (no commit)."""
        self._count = max(2, int(round(value)))
        self._recompute_preview()
        self.canvas.viewport().update()

    def set_dimension(self, value: float) -> None:
        """Enter/Tab: lock the count (commit happens via on_release)."""
        self._count = max(2, int(round(value)))
        DivideTool._last_count = self._count
        self._recompute_preview()

    def _recompute_preview(self) -> None:
        if self._item is None:
            self._preview_pts = []
        else:
            self._preview_pts = self._division_points(
                self._item, self._pick_point, self._count)

    def _commit(self) -> None:
        if self._item is None:
            self.reset()
            return
        pts = self._division_points(self._item, self._pick_point, self._count)
        if not pts:
            self.reset()
            return
        DivideTool._last_count = self._count
        gs = _gs(self.canvas)
        us = self.canvas.undo_stack
        vis = getattr(self.canvas, '_div_visible', True)
        if us:
            us.beginMacro(f"Divide /{self._count}")
        for sp in pts:
            marker = _make_div_marker(sp, gs)
            marker.setVisible(vis)
            self.canvas.add_item(marker)
        if us:
            us.endMacro()
        self.reset()
        self.canvas.viewport().update()

    def _division_points(self, item, click, n: int) -> list[QPointF]:
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            p1 = item.mapToScene(ln.p1())
            p2 = item.mapToScene(ln.p2())
            return _interior(p1, p2, n)
        if isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            cx = (r.left() + r.right()) / 2.0
            cy = (r.top() + r.bottom()) / 2.0
            rx, ry = r.width() / 2.0, r.height() / 2.0
            pts = []
            for i in range(n):  # N radial points around the circumference
                ang = 2.0 * math.pi * i / n - math.pi / 2.0  # start at top
                pts.append(item.mapToScene(
                    QPointF(cx + rx * math.cos(ang), cy + ry * math.sin(ang))))
            return pts
        if isinstance(item, QGraphicsRectItem):
            r = item.rect()
            corners = [item.mapToScene(c) for c in
                       (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft())]
            edges = [QLineF(corners[i], corners[(i + 1) % 4]) for i in range(4)]
            best = min(edges, key=lambda e: _seg_dist(click, e)) if click else edges[0]
            return _interior(best.p1(), best.p2(), n)
        if isinstance(item, QGraphicsPathItem):
            path = item.path()
            pts = [item.mapToScene(QPointF(path.elementAt(i).x, path.elementAt(i).y))
                   for i in range(path.elementCount())]
            segs = [QLineF(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
            if not segs:
                return []
            best = min(segs, key=lambda e: _seg_dist(click, e)) if click else segs[0]
            return _interior(best.p1(), best.p2(), n)
        return []

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase != 1 or not self._preview_pts:
            return
        gs = _gs(self.canvas)
        s = gs * 0.25
        pen = QPen(QColor("#C1140C"))
        pen.setCosmetic(True)
        pen.setWidthF(1.2)
        painter.setPen(pen)
        for sp in self._preview_pts:
            painter.drawLine(QLineF(sp.x() - s, sp.y(), sp.x() + s, sp.y()))
            painter.drawLine(QLineF(sp.x(), sp.y() - s, sp.x(), sp.y() + s))


def _interior(p1: QPointF, p2: QPointF, n: int) -> list[QPointF]:
    """N−1 equally-spaced interior points between p1 and p2."""
    return [QPointF(p1.x() + (p2.x() - p1.x()) * i / n,
                    p1.y() + (p2.y() - p1.y()) * i / n)
            for i in range(1, n)]


def _make_div_marker(scene_pt: QPointF, gs: float) -> QGraphicsPathItem:
    """A small red '+' construction mark whose centre is an osnap target."""
    s = gs * 0.25
    path = QPainterPath()
    path.moveTo(-s, 0); path.lineTo(s, 0)
    path.moveTo(0, -s); path.lineTo(0, s)
    item = QGraphicsPathItem(path)
    pen = QPen(QColor("#C1140C"))
    pen.setCosmetic(True)
    pen.setWidthF(1.2)
    item.setPen(pen)
    item.setPos(scene_pt)
    item.setData(0, {"zip": "", "note": ""})
    item.setData(1, "div_point")
    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    return item


# ═══════════════════════════════════════════════════════════ rotate
class RotateTool(Tool):
    """Rotate the current selection. Click a pivot (snaps to centre / points /
    grid), move the cursor to spin, click again to confirm. Free rotation when
    Ortho is off; snaps to the Ortho angle (45°/90°…) when Ortho is on.
    Right-click or Escape cancels."""
    name = "rotate"

    def reset(self) -> None:
        self._items: list = []
        self._pivot = None
        self._phase = 0          # 0 = pick pivot, 1 = spinning
        self._ref_angle = None
        self._orig: dict = {}
        self._cur_delta = 0.0
        self._cursor = None

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def cancel(self) -> None:
        self._restore()
        self.reset()
        self.canvas.viewport().update()

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            self.cancel()

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            items = [it for it in self.canvas.scene().selectedItems()]
            if not items:
                pick = self._pick_near(p)
                if pick is not None:
                    self.canvas.scene().clearSelection()
                    pick.setSelected(True)
                    items = [pick]
            if not items:
                return
            self._items = items
            self._pivot = QPointF(p)
            self._orig = {it: (QPointF(it.pos()), QTransform(it.transform()))
                          for it in self._items}
            self._ref_angle = None
            self._cur_delta = 0.0
            self._phase = 1
            self.canvas.viewport().update()
        elif self._phase == 1:
            self._commit()

    def _pick_near(self, p: QPointF):
        """Topmost item under p, or the nearest geometry within ~0.75 cell."""
        pick = self.canvas.pick_item(p)
        if pick is not None:
            return pick
        doc = self.canvas.document
        if doc is None:
            return None
        best, best_d = None, _gs(self.canvas) * 0.75
        for layer in doc.layers:
            if layer.kind != "vector" or not layer.visible:
                continue
            for item in layer.items():
                if item.data(1) == "div_point":
                    continue
                for seg in _item_segments(item):
                    d = _seg_dist(p, seg)
                    if d < best_d:
                        best_d, best = d, item
        return best

    def on_move(self, p: QPointF) -> None:
        if self._phase != 1 or self._pivot is None:
            return
        self._cursor = QPointF(p)
        vx, vy = p.x() - self._pivot.x(), p.y() - self._pivot.y()
        if math.hypot(vx, vy) < _gs(self.canvas) * 0.25:
            return
        ang = math.degrees(math.atan2(vy, vx))
        if self._ref_angle is None:
            self._ref_angle = ang
        delta = ang - self._ref_angle
        if getattr(self.canvas, '_ortho_enabled', False):
            step = getattr(self.canvas, '_ortho_angle', 45) or 45
            delta = round(delta / step) * step
        self._cur_delta = delta
        self._apply(delta)

    def _apply(self, deg: float) -> None:
        for item in self._items:
            op, ot = self._orig[item]
            s_old = QTransform(ot) * QTransform.fromTranslate(op.x(), op.y())
            rot = (QTransform.fromTranslate(-self._pivot.x(), -self._pivot.y())
                   * _pure_rotation(deg)
                   * QTransform.fromTranslate(self._pivot.x(), self._pivot.y()))
            s_new = s_old * rot
            item.setPos(0.0, 0.0)
            item.setTransform(s_new)
        self.canvas.viewport().update()

    def _restore(self) -> None:
        for item, (op, ot) in self._orig.items():
            item.setPos(op)
            item.setTransform(ot)

    def _commit(self) -> None:
        if not self._items or self._pivot is None:
            self.reset()
            return
        states = []
        for item in self._items:
            op, ot = self._orig[item]
            states.append((item, op, ot,
                           QPointF(item.pos()), QTransform(item.transform())))
        us = self.canvas.undo_stack
        if us:
            from .commands import RotateCommand
            us.push(RotateCommand(states))
        self.canvas.scene().clearSelection()
        self.reset()
        self.canvas.viewport().update()

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase != 1 or self._pivot is None:
            return
        gs = _gs(self.canvas)
        s = gs * 0.3
        pen = QPen(QColor("#9255E5"))
        pen.setCosmetic(True)
        pen.setWidthF(1.2)
        painter.setPen(pen)
        # pivot cross
        painter.drawLine(QLineF(self._pivot.x() - s, self._pivot.y(),
                                self._pivot.x() + s, self._pivot.y()))
        painter.drawLine(QLineF(self._pivot.x(), self._pivot.y() - s,
                                self._pivot.x(), self._pivot.y() + s))
        if self._cursor is not None:
            dash = QPen(QColor("#9255E5"))
            dash.setCosmetic(True)
            dash.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(dash)
            painter.drawLine(QLineF(self._pivot, self._cursor))
            _draw_dim_label(painter, self._cursor, f"{_dim_text(self._cur_delta)}°")


def _pure_rotation(deg: float) -> QTransform:
    t = QTransform()
    t.rotate(deg)
    return t


# ═══════════════════════════════════════════════════════════ mirror
class MirrorTool(Tool):
    """Mirror selected items across a two-click axis.
    1. Select items (or click one), 2. Click axis start, 3. Click axis end.
    Creates mirrored copies; originals stay."""
    name = "mirror"

    def reset(self) -> None:
        self._items: list = []
        self._p1 = None
        self._cursor = None
        self._phase = 0  # 0=pick first axis point, 1=pick second

    @property
    def in_progress(self) -> bool:
        return self._phase > 0

    def cancel(self) -> None:
        self.reset()
        self.canvas.viewport().update()

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            self.cancel()

    def on_press(self, p: QPointF) -> None:
        if self._phase == 0:
            items = list(self.canvas.scene().selectedItems())
            if not items:
                pick = self.canvas.pick_item(p)
                if pick:
                    self.canvas.scene().clearSelection()
                    pick.setSelected(True)
                    items = [pick]
            if not items:
                return
            self._items = items
            self._p1 = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._commit(QPointF(p))

    def on_move(self, p: QPointF) -> None:
        if self._phase == 1:
            self._cursor = QPointF(p)

    def _commit(self, p2: QPointF) -> None:
        if not self._items or self._p1 is None:
            self.reset()
            return
        axis = QLineF(self._p1, p2)
        if axis.length() < MIN_DRAG:
            self.reset()
            return
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Mirror")
        for item in self._items:
            mirrored = self._mirror_item(item, self._p1, p2)
            if mirrored is not None:
                self.canvas.add_item(mirrored)
        if us:
            us.endMacro()
        self.canvas.scene().clearSelection()
        self.reset()
        self.canvas.viewport().update()

    @staticmethod
    def _mirror_pt(p: QPointF, a: QPointF, b: QPointF) -> QPointF:
        dx, dy = b.x() - a.x(), b.y() - a.y()
        lsq = dx * dx + dy * dy
        if lsq < 1e-12:
            return QPointF(p)
        t = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / lsq
        proj_x = a.x() + t * dx
        proj_y = a.y() + t * dy
        return QPointF(2 * proj_x - p.x(), 2 * proj_y - p.y())

    def _mirror_item(self, item, a: QPointF, b: QPointF):
        mp = self._mirror_pt
        if isinstance(item, QGraphicsLineItem):
            ln = item.line()
            new = QGraphicsLineItem(QLineF(
                mp(item.mapToScene(ln.p1()), a, b),
                mp(item.mapToScene(ln.p2()), a, b)))
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            corners = [mp(item.mapToScene(c), a, b) for c in
                       (r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft())]
            path = QPainterPath(corners[0])
            for c in corners[1:]:
                path.lineTo(c)
            path.closeSubpath()
            new = QGraphicsPathItem(path)
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            cx, cy = (r.left() + r.right()) / 2, (r.top() + r.bottom()) / 2
            mc = mp(item.mapToScene(QPointF(cx, cy)), a, b)
            rx, ry = r.width() / 2, r.height() / 2
            new = QGraphicsEllipseItem(QRectF(mc.x() - rx, mc.y() - ry, 2 * rx, 2 * ry))
        elif isinstance(item, QGraphicsPathItem):
            old_path = item.path()
            new_path = QPainterPath()
            for i in range(old_path.elementCount()):
                el = old_path.elementAt(i)
                pt = mp(item.mapToScene(QPointF(el.x, el.y)), a, b)
                if i == 0:
                    new_path.moveTo(pt)
                else:
                    new_path.lineTo(pt)
            last_el = old_path.elementAt(old_path.elementCount() - 1)
            first_el = old_path.elementAt(0)
            if (abs(last_el.x - first_el.x) < 1e-6
                    and abs(last_el.y - first_el.y) < 1e-6):
                new_path.closeSubpath()
            new = QGraphicsPathItem(new_path)
        else:
            return None
        if hasattr(item, 'pen'):
            new.setPen(item.pen())
        if hasattr(item, 'brush'):
            new.setBrush(item.brush())
        new.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        new.setData(0, dict(item.data(0)) if item.data(0) else {"zip": "", "note": ""})
        return new

    def paint_preview(self, painter: QPainter) -> None:
        if self._phase != 1 or self._p1 is None or self._cursor is None:
            return
        painter.setPen(self._preview_pen)
        painter.drawLine(QLineF(self._p1, self._cursor))


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
        self._paint_at(p)

    def on_move(self, p: QPointF) -> None:
        if self._painting:
            self._paint_at(p)

    def on_release(self, p: QPointF) -> None:
        if self._painting:
            self._paint_at(p)
            us = self.canvas.undo_stack
            if us:
                us.endMacro()
            self._painting = False
            self._filled_cells = set()

    def _paint_at(self, p: QPointF) -> None:
        if getattr(self.canvas, '_wireframe', True):
            self._fill_cell(p)
        else:
            self._fill_region(p)

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
        barrier.setWidthF(3.0)
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
                if item.data(1) in ("cell_fill", "div_point"):
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


# ═══════════════════════════════════════════════════════════ text (shared)
def _load_vg5000(px: int) -> QFont:
    import os
    from PySide6.QtGui import QFontDatabase
    font_path = os.path.join(
        os.path.dirname(__file__), "assets", "fonts", "VG5000-Regular.otf")
    fam = QFontDatabase.applicationFontFamilies(
        QFontDatabase.addApplicationFont(font_path))
    name = fam[0] if fam else "monospace"
    f = QFont(name, px)
    f.setPixelSize(px)
    return f


def _exit_text(tool, canvas) -> None:
    """Shared Escape handler for both text tools."""
    item = tool._active_text
    if item is None:
        return
    item.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    item.clearFocus()
    if not item.toPlainText().strip():
        if canvas.undo_stack and canvas.document:
            from .commands import DeleteItemsCommand
            canvas.undo_stack.push(DeleteItemsCommand(canvas.document, [item]))
    tool._active_text = None


def _enter_existing(tool, item) -> None:
    """Re-enter edit mode on an existing text item."""
    item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
    item.setFocus()
    tool._active_text = item


# ═══════════════════════════════════════════════════════════ word text
class WordTextTool(Tool):
    """Flowing free-text entry, 50-char line budget."""
    name = "word"

    _FONT_PX = 12
    _LINE_BUDGET = 50

    def reset(self) -> None:
        self._active_text = None

    def deactivate(self) -> None:
        _exit_text(self, self.canvas)
        self.reset()

    def on_press(self, p: QPointF) -> None:
        gs = _gs(self.canvas)
        for item in self.canvas.scene().items(p):
            if isinstance(item, QGraphicsTextItem) and item.data(1) == "word_text":
                _enter_existing(self, item)
                return

        cx = math.floor(p.x() / gs) * gs
        cy = math.floor(p.y() / gs) * gs
        pad = gs * 0.1

        font = _load_vg5000(self._FONT_PX)
        from PySide6.QtGui import QFontMetricsF
        cw = QFontMetricsF(font).horizontalAdvance("M")

        text_item = QGraphicsTextItem("")
        text_item.setFont(font)
        text_item.setDefaultTextColor(QColor(DEFAULT_STROKE))
        text_item.setTextWidth(cw * self._LINE_BUDGET)
        text_item.setPos(cx + pad, cy + pad)
        text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        text_item.setData(0, {"zip": "", "note": ""})
        text_item.setData(1, "word_text")
        self.canvas.add_item(text_item)
        text_item.setFocus()
        self._active_text = text_item

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            _exit_text(self, self.canvas)


# ═══════════════════════════════════════════════════════════ cell text
class CellTextTool(Tool):
    """1 character per grid cell, graph-paper style."""
    name = "cell"

    _FONT_PX = 14
    _LINE_BUDGET = 50

    def reset(self) -> None:
        self._active_text = None

    def deactivate(self) -> None:
        _exit_text(self, self.canvas)
        self.reset()

    def on_press(self, p: QPointF) -> None:
        gs = _gs(self.canvas)
        for item in self.canvas.scene().items(p):
            if isinstance(item, QGraphicsTextItem) and item.data(1) == "cell_text":
                _enter_existing(self, item)
                return

        cx = math.floor(p.x() / gs) * gs
        cy = math.floor(p.y() / gs) * gs

        font = _load_vg5000(self._FONT_PX)
        from PySide6.QtGui import QFontMetricsF
        cw = QFontMetricsF(font).horizontalAdvance("M")
        spacing = gs - cw
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)

        text_item = QGraphicsTextItem("")
        text_item.setFont(font)
        text_item.setDefaultTextColor(QColor(DEFAULT_STROKE))
        text_item.setTextWidth(gs * self._LINE_BUDGET)
        text_item.setPos(cx, cy)
        text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        text_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        text_item.setData(0, {"zip": "", "note": ""})
        text_item.setData(1, "cell_text")
        doc = text_item.document()
        fmt = doc.rootFrame().frameFormat()
        fmt.setMargin(0)
        doc.rootFrame().setFrameFormat(fmt)
        self.canvas.add_item(text_item)
        text_item.setFocus()
        self._active_text = text_item

    def on_key(self, key) -> None:
        if key == Qt.Key.Key_Escape:
            _exit_text(self, self.canvas)
