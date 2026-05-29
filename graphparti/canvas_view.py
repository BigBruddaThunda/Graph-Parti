"""The canvas: infinite grid, zoom-to-cursor, pan, and grid-snapping with a readout.

GRAPH PARTI steps 1-2. The grid is painted in ``drawBackground`` (behind every
layer); the snap marker is painted in ``drawForeground`` (over the scene). We ride
Qt's coordinate system and view transforms — no hand-rolled pan/zoom math. Cosmetic
pens keep lines 1px-crisp at any zoom while the *spacing* scales with the scene.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class CanvasView(QGraphicsView):
    """A pannable, zoomable view that draws an infinite grid and snaps to it."""

    cursor_moved = Signal(QPointF, bool)  # snapped scene position, snap_active
    zoom_changed = Signal(float)          # current scale factor

    ZOOM_STEP = 1.15
    MIN_SCALE = 0.05
    MAX_SCALE = 40.0

    def __init__(self, scene: QGraphicsScene, grid_spacing: int = 20, major_every: int = 5, parent=None) -> None:
        super().__init__(scene, parent)
        self.grid_spacing = grid_spacing
        self.major_every = major_every
        self.snap_enabled = True
        self._panning = False
        self._pan_anchor = QPointF()
        self._cursor_scene: QPointF | None = None  # last snapped pos; None when outside

        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QColor("#1b1b1f"))

        self._minor_color = QColor("#2a2a31")
        self._major_color = QColor("#3b3b46")
        self._snap_color = QColor("#f7b731")  # NYC-taxi yellow

    # ----------------------------------------------------------------- snapping
    def set_snap_enabled(self, on: bool) -> None:
        self.snap_enabled = bool(on)
        self.viewport().update()

    def toggle_snap(self) -> None:
        self.set_snap_enabled(not self.snap_enabled)

    def snap_point(self, p: QPointF) -> QPointF:
        """Nearest grid intersection, or P unchanged when snap is off."""
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

    # --------------------------------------------------------- snap indicator
    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)
        if self._cursor_scene is None or not self.snap_enabled:
            return
        p = self._cursor_scene
        r = 5.0 / max(self.transform().m11(), 1e-6)  # ~5px regardless of zoom
        pen = QPen(self._snap_color); pen.setCosmetic(True); pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.drawLine(QLineF(p.x() - r, p.y(), p.x() + r, p.y()))
        painter.drawLine(QLineF(p.x(), p.y() - r, p.x(), p.y() + r))
        painter.drawRect(QRectF(p.x() - r, p.y() - r, 2 * r, 2 * r))

    # ------------------------------------------------------------- zoom (wheel)
    def wheelEvent(self, event: QWheelEvent) -> None:
        dy = event.angleDelta().y()
        if dy == 0:
            return
        factor = self.ZOOM_STEP if dy > 0 else 1.0 / self.ZOOM_STEP
        projected = self.transform().m11() * factor
        if projected < self.MIN_SCALE or projected > self.MAX_SCALE:
            return
        self.scale(factor, factor)  # AnchorUnderMouse keeps the point under the cursor fixed
        event.accept()
        self.zoom_changed.emit(self.transform().m11())

    # -------------------------------------------------------------- mouse / pan
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_anchor = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
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
        raw = self.mapToScene(event.position().toPoint())
        snapped = self.snap_point(raw)
        self._cursor_scene = snapped
        self.cursor_moved.emit(snapped, self.snap_enabled)
        self.viewport().update()  # repaint snap marker
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._panning and event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event) -> None:
        self._cursor_scene = None
        self.viewport().update()
        super().leaveEvent(event)

    # --------------------------------------------------------- pan (space-drag)
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        super().keyReleaseEvent(event)
