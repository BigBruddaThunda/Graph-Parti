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
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QPolygonF, QWheelEvent
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
        self.document = None
        self.active_tool = None
        self.undo_stack = None
        self._stroke_color = "#3C3C3C"
        self._panning = False
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

        self._minor_color = QColor("#AECEE7")  # sky-blue notebook lines (minor)
        self._major_color = QColor("#7FB2D6")  # sky-blue (major, a touch stronger)
        self._grid_snap_color = QColor("#C1140C")   # red crosshair = grid snap
        self._osnap_color = QColor("#1f7a1f")        # green square/triangle = object snap

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
    def pick_item(self, scene_pos: QPointF):
        """Topmost selectable item under SCENE_POS (pixel-accurate hit-test)."""
        for it in self.items(self.mapFromScene(scene_pos)):
            if bool(it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
                return it
        return None

    def push_move(self, items, dx: float, dy: float) -> None:
        if self.undo_stack is not None and items:
            self.undo_stack.push(MoveItemsCommand(items, dx, dy))

    def select_in_rect(self, rect: QRectF) -> None:
        self.scene().clearSelection()
        for it in self.scene().items(rect):
            if bool(it.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable):
                it.setSelected(True)

    def delete_selected(self) -> None:
        items = self.scene().selectedItems()
        if items and self.undo_stack is not None and self.document is not None:
            self.undo_stack.push(DeleteItemsCommand(self.document, items))

    def _tool_active(self) -> bool:
        return self.active_tool is not None and self.dragMode() == QGraphicsView.DragMode.NoDrag

    def _scene_pos(self, event: QMouseEvent) -> QPointF:
        point, _kind = self.resolve_snap(self.mapToScene(event.position().toPoint()))
        return point

    # ----------------------------------------------------------------- snapping
    def set_snap_enabled(self, on: bool) -> None:
        self.snap_enabled = bool(on)
        self.viewport().update()

    def snap_point(self, p: QPointF) -> QPointF:
        """Grid-only snap (nearest intersection, or P unchanged when off)."""
        if not self.snap_enabled:
            return QPointF(p)
        s = self.grid_spacing
        return QPointF(round(p.x() / s) * s, round(p.y() / s) * s)

    def resolve_snap(self, raw: QPointF) -> tuple[QPointF, str]:
        """Object-snap first, then grid-snap, then raw. Returns (point, kind)."""
        osnap = self._nearest_osnap(raw)
        if osnap is not None:
            return osnap
        if self.snap_enabled:
            return self.snap_point(raw), "grid"
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
        major_pen = QPen(self._major_color); major_pen.setCosmetic(True); major_pen.setWidthF(1.0)
        painter.setPen(minor_pen); painter.drawLines(minor_lines)
        painter.setPen(major_pen); painter.drawLines(major_lines)

    # ---------------------------------------------------- foreground (overlays)
    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)
        if self.active_tool is not None:
            self.active_tool.paint_preview(painter)
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
            self.active_tool.cancel()  # cancel any in-progress draw
            self.viewport().update()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._tool_active():
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
        if self.active_tool is not None:
            self.active_tool.on_move(point)
        self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
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
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
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
