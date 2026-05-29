"""Document model: an ordered layer stack. GRAPH PARTI core model.

Items are added directly to the single QGraphicsScene (not nested in a
QGraphicsItemGroup — a group swallows per-item selection). Each layer tracks its
own items in a list and manages their visibility, lock state, and Z value. Layer
order = Z (back layers low, front layers high).
"""
from __future__ import annotations

import uuid

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene


class Layer:
    def __init__(self, name: str, kind: str) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.kind = kind  # "vector" | "raster"
        self._visible = True
        self._locked = False
        self.z_index = 0

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def locked(self) -> bool:
        return self._locked

    # subclasses implement: set_visible, set_locked, apply_z


class VectorLayer(Layer):
    def __init__(self, name: str, scene: QGraphicsScene) -> None:
        super().__init__(name, "vector")
        self.scene = scene
        self._items: list = []

    def add_item(self, item) -> None:
        item.setZValue(self.z_index)
        item.setVisible(self._visible)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not self._locked)
        self.scene.addItem(item)
        if item not in self._items:
            self._items.append(item)

    def remove_item(self, item) -> None:
        sc = item.scene()
        if sc is not None:
            sc.removeItem(item)
        if item in self._items:
            self._items.remove(item)

    def items(self) -> list:
        return list(self._items)

    def set_visible(self, on: bool) -> None:
        self._visible = bool(on)
        for it in self._items:
            it.setVisible(self._visible)

    def set_locked(self, on: bool) -> None:
        self._locked = bool(on)
        for it in self._items:
            it.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not self._locked)
            if self._locked:
                it.setSelected(False)

    def apply_z(self) -> None:
        for it in self._items:
            it.setZValue(self.z_index)


class RasterLayer(Layer):
    def __init__(self, name: str, scene: QGraphicsScene, paper: QRectF) -> None:
        super().__init__(name, "raster")
        pm = QPixmap(int(paper.width()), int(paper.height()))
        pm.fill(QColor(0, 0, 0, 0))  # transparent until painted (step 7)
        self.item = QGraphicsPixmapItem(pm)
        self.item.setOffset(paper.left(), paper.top())
        scene.addItem(self.item)
        self.pixmap = pm

    def set_visible(self, on: bool) -> None:
        self._visible = bool(on)
        self.item.setVisible(self._visible)

    def set_locked(self, on: bool) -> None:
        self._locked = bool(on)

    def apply_z(self) -> None:
        self.item.setZValue(self.z_index)


class Document:
    def __init__(self, scene: QGraphicsScene) -> None:
        self.scene = scene
        self.layers: list[Layer] = []
        self.active_index = 0

    def add_layer(self, layer: Layer, active: bool = True) -> Layer:
        self.layers.append(layer)
        layer.z_index = len(self.layers)
        layer.apply_z()
        if active:
            self.active_index = len(self.layers) - 1
        return layer

    def active_layer(self) -> Layer | None:
        if 0 <= self.active_index < len(self.layers):
            return self.layers[self.active_index]
        return None

    def active_vector_layer(self) -> VectorLayer | None:
        layer = self.active_layer()
        return layer if isinstance(layer, VectorLayer) else None

    def layer_for(self, item) -> "VectorLayer | None":
        for layer in self.layers:
            if isinstance(layer, VectorLayer) and item in layer.items():
                return layer
        return None

    @classmethod
    def default(cls, scene: QGraphicsScene, paper: QRectF) -> "Document":
        """Open with a raster 'back' beneath a vector 'front'; front active."""
        doc = cls(scene)
        doc.add_layer(RasterLayer("back", scene, paper), active=False)
        doc.add_layer(VectorLayer("front", scene), active=True)
        return doc
