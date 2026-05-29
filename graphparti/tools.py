"""Drawing tools. GRAPH PARTI step 3 (vector tools).

CanvasView feeds each tool *scene-space, already-snapped* points. A tool builds a
QGraphicsItem and commits it to the active vector layer via ``canvas.add_item``.
Geometry lives in plain ``on_press/on_move/on_release`` methods so the tools can be
exercised headlessly (no synthetic Qt events needed to test them).
"""
from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
)

DEFAULT_STROKE = "#3C3C3C"
DEFAULT_WIDTH = 2.0
MIN_DRAG = 1e-6


def make_pen(color: str, width: float) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


class Tool:
    name = "tool"

    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self._preview_pen = QPen(QColor("#9255E5"))
        self._preview_pen.setCosmetic(True)
        self._preview_pen.setWidthF(1.5)
        self._preview_pen.setStyle(Qt.PenStyle.DashLine)
        self.reset()

    # lifecycle
    def activate(self) -> None:
        self.reset()

    def deactivate(self) -> None:
        self.reset()

    def reset(self) -> None:
        pass

    # events (scene-space, snapped)
    def on_press(self, p: QPointF) -> None: ...
    def on_move(self, p: QPointF) -> None: ...
    def on_release(self, p: QPointF) -> None: ...
    def on_double_click(self, p: QPointF) -> None: ...
    def on_key(self, key) -> None: ...

    def paint_preview(self, painter: QPainter) -> None: ...

    # commit helper
    def _commit(self, item: QGraphicsItem) -> None:
        item.setPen(make_pen(self.canvas.current_stroke(), DEFAULT_WIDTH))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})  # metadata for the ZIP stamper (step 8)
        self.canvas.add_item(item)


class LineTool(Tool):
    name = "line"

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._drawing = False

    def on_press(self, p: QPointF) -> None:
        self._start = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True

    def on_move(self, p: QPointF) -> None:
        if self._drawing:
            self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        line = QLineF(self._start, QPointF(p))
        if line.length() > MIN_DRAG:
            self._commit(QGraphicsLineItem(line))
        self.reset()

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._start is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawLine(QLineF(self._start, self._cur))


class RectTool(Tool):
    name = "rect"

    def reset(self) -> None:
        self._start = None
        self._cur = None
        self._drawing = False

    def on_press(self, p: QPointF) -> None:
        self._start = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True

    def on_move(self, p: QPointF) -> None:
        if self._drawing:
            self._cur = QPointF(p)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        r = QRectF(self._start, QPointF(p)).normalized()
        if r.width() > MIN_DRAG or r.height() > MIN_DRAG:
            self._commit(QGraphicsRectItem(r))
        self.reset()

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._start is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawRect(QRectF(self._start, self._cur).normalized())


class CircleTool(Tool):
    name = "circle"

    def reset(self) -> None:
        self._center = None
        self._cur = None
        self._drawing = False

    def on_press(self, p: QPointF) -> None:
        self._center = QPointF(p)
        self._cur = QPointF(p)
        self._drawing = True

    def on_move(self, p: QPointF) -> None:
        if self._drawing:
            self._cur = QPointF(p)

    def _rect_for(self, edge: QPointF) -> QRectF:
        r = QLineF(self._center, edge).length()
        return QRectF(self._center.x() - r, self._center.y() - r, 2 * r, 2 * r)

    def on_release(self, p: QPointF) -> None:
        if not self._drawing:
            return
        self._drawing = False
        if QLineF(self._center, QPointF(p)).length() > MIN_DRAG:
            self._commit(QGraphicsEllipseItem(self._rect_for(QPointF(p))))
        self.reset()

    def paint_preview(self, painter: QPainter) -> None:
        if self._drawing and self._center is not None and self._cur is not None:
            painter.setPen(self._preview_pen)
            painter.drawEllipse(self._rect_for(self._cur))


class PolylineTool(Tool):
    name = "polyline"

    def reset(self) -> None:
        self._pts: list[QPointF] = []
        self._cur = None

    def on_press(self, p: QPointF) -> None:
        self._pts.append(QPointF(p))
        self._cur = QPointF(p)

    def on_move(self, p: QPointF) -> None:
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

    def _finish(self) -> None:
        if len(self._pts) >= 2:
            self._commit(QGraphicsPathItem(self._path(include_cursor=False)))
        self.reset()
        self.canvas.viewport().update()

    def paint_preview(self, painter: QPainter) -> None:
        if not self._pts:
            return
        painter.setPen(self._preview_pen)
        painter.drawPath(self._path(include_cursor=True))
