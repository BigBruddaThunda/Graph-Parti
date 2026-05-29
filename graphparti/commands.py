"""Undoable commands. GRAPH PARTI step 5.

Every mutation (draw, move, delete) is a QUndoCommand pushed onto the window's
QUndoStack, so Ctrl+Z / Ctrl+Shift+Z just work and the whole edit history is one
linear, inspectable stack.
"""
from __future__ import annotations

from PySide6.QtGui import QUndoCommand


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
