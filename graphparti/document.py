"""Document model: an ordered layer stack. GRAPH PARTI core model.

Layers map onto the single QGraphicsScene:
- a **vector** layer is a QGraphicsItemGroup container; its children are the drawn
  items, kept individually selectable via setHandlesChildEvents(False);
- a **raster** layer is a QGraphicsPixmapItem holding one QPixmap (painted in step 7).

Layer stacking order = the container's Z value. The layer *panel* (step 6) will
manipulate this model; tools target the active vector layer.
"""
from __future__ import annotations

import uuid

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QGraphicsItemGroup, QGraphicsPixmapItem, QGraphicsScene


class Layer:
    def __init__(self, name: str, kind: str, root) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.kind = kind  # "vector" | "raster"
        self.root = root  # the QGraphicsItem container living in the scene
        self._visible = True
        self._locked = False

    @property
    def visible(self) -> bool:
        return self._visible

    def set_visible(self, on: bool) -> None:
        self._visible = bool(on)
        self.root.setVisible(self._visible)

    @property
    def locked(self) -> bool:
        return self._locked

    def set_locked(self, on: bool) -> None:
        self._locked = bool(on)


class VectorLayer(Layer):
    def __init__(self, name: str, scene: QGraphicsScene) -> None:
        group = QGraphicsItemGroup()
        group.setHandlesChildEvents(False)  # children stay individually interactive
        scene.addItem(group)
        super().__init__(name, "vector", group)

    def add_item(self, item) -> None:
        self.root.addToGroup(item)

    def items(self) -> list:
        return list(self.root.childItems())


class RasterLayer(Layer):
    def __init__(self, name: str, scene: QGraphicsScene, paper: QRectF) -> None:
        pm = QPixmap(int(paper.width()), int(paper.height()))
        pm.fill(QColor(0, 0, 0, 0))  # transparent until painted (step 7)
        item = QGraphicsPixmapItem(pm)
        item.setOffset(paper.left(), paper.top())
        scene.addItem(item)
        super().__init__(name, "raster", item)
        self.pixmap = pm


class Document:
    """An ordered layer stack with an active layer."""

    def __init__(self, scene: QGraphicsScene) -> None:
        self.scene = scene
        self.layers: list[Layer] = []
        self.active_index = 0

    def add_layer(self, layer: Layer, active: bool = True) -> Layer:
        self.layers.append(layer)
        layer.root.setZValue(len(self.layers))
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

    @classmethod
    def default(cls, scene: QGraphicsScene, paper: QRectF) -> "Document":
        """Open with a raster 'back' beneath a vector 'front'; front active."""
        doc = cls(scene)
        doc.add_layer(RasterLayer("back", scene, paper), active=False)
        doc.add_layer(VectorLayer("front", scene), active=True)
        return doc
