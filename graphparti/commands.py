"""Undoable commands. GRAPH PARTI step 5.

Every mutation (draw, move, delete) is a QUndoCommand pushed onto the window's
QUndoStack, so Ctrl+Z / Ctrl+Shift+Z just work and the whole edit history is one
linear, inspectable stack.
"""
from __future__ import annotations

from PySide6.QtGui import QTransform, QUndoCommand
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
)


class AddItemCommand(QUndoCommand):
    def __init__(self, layer, item) -> None:
        super().__init__("draw")
        self.layer = layer
        self.item = item

    def redo(self) -> None:
        self.layer.add_item(self.item)

    def undo(self) -> None:
        self.layer.remove_item(self.item)


class MoveItemsCommand(QUndoCommand):
    def __init__(self, items, dx: float, dy: float) -> None:
        super().__init__("move")
        self.items = list(items)
        self.dx = dx
        self.dy = dy

    def redo(self) -> None:
        for it in self.items:
            it.moveBy(self.dx, self.dy)

    def undo(self) -> None:
        for it in self.items:
            it.moveBy(-self.dx, -self.dy)


class DeleteItemsCommand(QUndoCommand):
    def __init__(self, document, items) -> None:
        super().__init__("delete")
        # Capture each item's owning layer now, so undo can put it back.
        self.pairs = [(it, document.layer_for(it)) for it in items]

    def redo(self) -> None:
        for it, layer in self.pairs:
            if layer is not None:
                layer.remove_item(it)

    def undo(self) -> None:
        for it, layer in self.pairs:
            if layer is not None:
                layer.add_item(it)


class ReshapeCommand(QUndoCommand):
    """Reshape a geometry item (line/rect/ellipse/path) by swapping its geometry."""

    def __init__(self, item, old_geom, new_geom) -> None:
        super().__init__("reshape")
        self.item = item
        self.old_geom = old_geom
        self.new_geom = new_geom

    def redo(self) -> None:
        self._apply(self.new_geom)

    def undo(self) -> None:
        self._apply(self.old_geom)

    def _apply(self, geom) -> None:
        if isinstance(self.item, QGraphicsLineItem):
            self.item.setLine(geom)
        elif isinstance(self.item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            self.item.setRect(geom)
        elif isinstance(self.item, QGraphicsPathItem):
            self.item.setPath(geom)


class RotateCommand(QUndoCommand):
    """Rotate a set of items around a pivot. States captured as
    (item, old_pos, old_transform, new_pos, new_transform)."""

    def __init__(self, states) -> None:
        super().__init__("rotate")
        self.states = states

    def redo(self) -> None:
        for item, _op, _ot, np_, nt in self.states:
            item.setPos(np_)
            item.setTransform(nt)

    def undo(self) -> None:
        for item, op, ot, _np, _nt in self.states:
            item.setPos(op)
            item.setTransform(ot)
