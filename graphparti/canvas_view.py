"""The canvas: grid, zoom, pan, grid-snap, and routing events to the active tool.

GRAPH PARTI steps 1-3. Grid in drawBackground; tool rubber-band preview + snap
marker in drawForeground. The view owns the document and the active tool, and feeds
the tool scene-space snapped points. Item commits funnel through ``add_item`` (a
single chokepoint that step 5 will wrap in a QUndoCommand).
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView


class CanvasView(QGraphicsView):
    cursor_moved = Signal(QPointF, bool)  # snapped scene position, snap_active
    zoom_changed = Signal(float)

    ZOOM_STEP = 1.15
    MIN_SCALE = 0.05
    MAX_SCALE = 40.0

    def __init__(self, scene: QGraphicsScene, grid_spacing: int = 20, major_every: int = 5, parent=None) -> None:
        super().__init__(scene, parent)
        self.grid_spacing = grid_spacing
        self.major_every = major_every
        self.snap_enabled = True
        self.document = None         # set by MainWindow
        self.active_tool = None      # set via set_tool
        self._stroke_color = "#3C3C3C"
        self._panning = False
        self._pan_anchor = QPointF()
        self._cursor_scene: QPointF | None = None

        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#F2EBD8"))  # warm sheep's-wool paper

        self._minor_color = QColor("#AECEE7")  # sky-blue notebook lines (minor)
        self._major_color = QColor("#7FB2D6")  # sky-blue (major, a touch stronger)
        self._snap_color = QColor("#C1140C")   # red snap marker — pops on paper

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
        """Commit a freshly drawn item to the active vector layer."""
        layer = self.document.active_vector_layer() if self.document else None
        if layer is not None:
            layer.add_item(item)

    def _tool_active(self) -> bool:
        return self.active_tool is not None and self.dragMode() == QGraphicsView.DragMode.NoDrag

    def _scene_pos(self, event: QMouseEvent) -> QPointF:
        return self.snap_point(self.mapToScene(event.position().toPoint()))

    # ----------------------------------------------------------------- snapping
    def set_snap_enabled(self, on: bool) -> None:
        self.snap_enabled = bool(on)
        self.viewport().update()

    def snap_point(self, p: QPointF) -> QPointF:
        if not self.snap_enabled:
            return QPointF(p)
        s = self.grid_spacing
        return QPointF(round(p.x() / s) * s, round(p.y() / s) * s)

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
        if self._cursor_scene is not None and self.snap_enabled:
            p = self._cursor_scene
            r = 5.0 / max(self.transform().m11(), 1e-6)
            pen = QPen(self._snap_color); pen.setCosmetic(True); pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.drawLine(QLineF(p.x() - r, p.y(), p.x() + r, p.y()))
            painter.drawLine(QLineF(p.x(), p.y() - r, p.x(), p.y() + r))

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
        snapped = self._scene_pos(event)
        self._cursor_scene = snapped
        self.cursor_moved.emit(snapped, self.snap_enabled)
        if self.active_tool is not None:
            self.active_tool.on_move(snapped)
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
        self.viewport().update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------- keys
    def keyPressEvent(self, event: QKeyEvent) -> None:
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
