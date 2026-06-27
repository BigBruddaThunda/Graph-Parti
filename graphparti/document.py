"""Document model: an ordered layer stack. GRAPH PARTI core model.

Items are added directly to the single QGraphicsScene (not nested in a
QGraphicsItemGroup — a group swallows per-item selection). Each layer tracks its
own items in a list and manages their visibility, lock state, and Z value. Layer
order = Z (back layers low, front layers high).
"""
from __future__ import annotations

import base64
import io
import json
import math
import uuid

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QLineF, QPointF, QRectF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QImage, QPainterPath, QPen, QPixmap, QTransform,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
)


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
    def __init__(self, name: str, scene: QGraphicsScene, paper: QRectF,
                 opacity: float = 1.0) -> None:
        super().__init__(name, "raster")
        self._scene = scene
        self._opacity = opacity
        pm = QPixmap(int(paper.width()), int(paper.height()))
        pm.fill(QColor(0, 0, 0, 0))  # transparent until painted (step 7)
        self.item = QGraphicsPixmapItem(pm)
        self.item.setOffset(paper.left(), paper.top())
        self.item.setOpacity(opacity)
        scene.addItem(self.item)
        self.pixmap = pm
        self._ref_images: list[QGraphicsPixmapItem] = []

    def add_reference_image(self, pixmap: QPixmap, pos: QPointF) -> QGraphicsPixmapItem:
        """Drop a reference image onto this layer at the given scene position."""
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(pos)
        item.setZValue(self.z_index)
        item.setOpacity(self._opacity)
        item.setVisible(self._visible)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self._scene.addItem(item)
        self._ref_images.append(item)
        return item

    def set_visible(self, on: bool) -> None:
        self._visible = bool(on)
        self.item.setVisible(self._visible)
        for img in self._ref_images:
            img.setVisible(self._visible)

    def set_locked(self, on: bool) -> None:
        self._locked = bool(on)

    def apply_z(self) -> None:
        self.item.setZValue(self.z_index)
        for img in self._ref_images:
            img.setZValue(self.z_index)


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

    def remove_layer(self, layer: Layer) -> bool:
        """Remove a layer and all its items. Returns False if it's the last layer."""
        if layer not in self.layers or len(self.layers) <= 1:
            return False
        idx = self.layers.index(layer)
        if isinstance(layer, VectorLayer):
            for item in list(layer.items()):
                layer.remove_item(item)
        self.layers.remove(layer)
        if self.active_index >= len(self.layers):
            self.active_index = len(self.layers) - 1
        self._reindex_z()
        return True

    def move_layer(self, layer: Layer, delta: int) -> None:
        """Move a layer up (delta=+1) or down (delta=-1) in the stack."""
        idx = self.layers.index(layer)
        new_idx = max(0, min(len(self.layers) - 1, idx + delta))
        if new_idx == idx:
            return
        self.layers.pop(idx)
        self.layers.insert(new_idx, layer)
        if self.active_index == idx:
            self.active_index = new_idx
        self._reindex_z()

    def _reindex_z(self) -> None:
        """Recompute z-index for all layers after a reorder/remove."""
        for i, layer in enumerate(self.layers):
            layer.z_index = i + 1
            layer.apply_z()

    @classmethod
    def default(cls, scene: QGraphicsScene, paper: QRectF) -> "Document":
        """parti (raster ref) · trace (vector, active) · draw (vector, freehand) · book (vector, zip boxes).

        Layer indices: 0=parti, 1=trace, 2=draw, 3=book."""
        doc = cls(scene)
        doc.add_layer(RasterLayer("parti", scene, paper, opacity=0.50), active=False)
        doc.add_layer(VectorLayer("trace", scene), active=True)
        doc.add_layer(VectorLayer("draw", scene), active=False)
        doc.add_layer(VectorLayer("book", scene), active=False)
        return doc

    # ─────────────────────────────────────────────────── save / load
    def to_dict(self) -> dict:
        """Serialize the whole document to a plain dict (the .parti body)."""
        data = {"version": 1, "layers": []}
        for layer in self.layers:
            ld: dict = {"name": layer.name, "kind": layer.kind,
                        "visible": layer.visible}
            if isinstance(layer, VectorLayer):
                ld["items"] = [self._serialize_item(it) for it in layer.items()]
            elif isinstance(layer, RasterLayer):
                ld["ref_images"] = []
                for img in layer._ref_images:
                    ld["ref_images"].append({
                        "pos": [img.pos().x(), img.pos().y()],
                        "data": _pixmap_to_b64(img.pixmap()),
                    })
            data["layers"].append(ld)
        return data

    def from_dict(self, data: dict, clear: bool = True) -> None:
        """Rebuild the document from a dict. When clear is False, items are
        added on top of what's already present (used for placing a book)."""
        if clear:
            for layer in self.layers:
                if isinstance(layer, VectorLayer):
                    for it in list(layer.items()):
                        layer.remove_item(it)
                elif isinstance(layer, RasterLayer):
                    for img in list(layer._ref_images):
                        sc = img.scene()
                        if sc:
                            sc.removeItem(img)
                    layer._ref_images.clear()
        for ld in data.get("layers", []):
            kind = ld.get("kind")
            name = ld.get("name")
            layer = None
            for l in self.layers:
                if l.name == name and l.kind == kind:
                    layer = l
                    break
            if layer is None:
                continue
            if isinstance(layer, VectorLayer):
                for sd in ld.get("items", []):
                    item = self._deserialize_item(sd)
                    if item is not None:
                        layer.add_item(item)
            elif isinstance(layer, RasterLayer):
                for rd in ld.get("ref_images", []):
                    pm = _b64_to_pixmap(rd["data"])
                    if pm and not pm.isNull():
                        layer.add_reference_image(
                            pm, QPointF(rd["pos"][0], rd["pos"][1]))

    def save_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_json(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            self.from_dict(json.load(f))

    @staticmethod
    def _serialize_item(item) -> dict:
        d: dict = {}
        if item.data(1) == "div_point":
            d["type"] = "div_point"
            sp = item.mapToScene(QPointF(0.0, 0.0))  # true centre, survives rotate
            d["pos"] = [sp.x(), sp.y()]
            return d
        if isinstance(item, QGraphicsTextItem):
            d["type"] = "text"
            d["pos"] = [item.pos().x(), item.pos().y()]
            d["text"] = item.toPlainText()
            d["kind"] = item.data(1) or "word_text"
            f = item.font()
            d["font_px"] = f.pixelSize()
            d["text_width"] = item.textWidth()
            d["letter_spacing"] = f.letterSpacing()
            d["color"] = item.defaultTextColor().name()
        elif isinstance(item, QGraphicsPixmapItem):
            d["type"] = "pixmap"
            d["pos"] = [item.pos().x(), item.pos().y()]
            d["data"] = _pixmap_to_b64(item.pixmap())
            d["opacity"] = item.opacity()
            d["marker"] = item.data(1)
            d["fill_color"] = item.data(2)
        elif isinstance(item, QGraphicsLineItem):
            ln = item.line()
            d["type"] = "line"
            d["p1"] = [ln.p1().x(), ln.p1().y()]
            d["p2"] = [ln.p2().x(), ln.p2().y()]
        elif isinstance(item, QGraphicsRectItem):
            r = item.rect()
            d["type"] = "rect"
            d["rect"] = [r.x(), r.y(), r.width(), r.height()]
        elif isinstance(item, QGraphicsEllipseItem):
            r = item.rect()
            d["type"] = "circle"
            d["rect"] = [r.x(), r.y(), r.width(), r.height()]
        elif isinstance(item, QGraphicsPathItem):
            path = item.path()
            pts = []
            for i in range(path.elementCount()):
                el = path.elementAt(i)
                pts.append([el.x, el.y])
            d["type"] = "path"
            d["points"] = pts
            if path.elementCount() > 2:
                last = path.elementAt(path.elementCount() - 1)
                first = path.elementAt(0)
                d["closed"] = (abs(last.x - first.x) < 1e-6
                               and abs(last.y - first.y) < 1e-6)
            else:
                d["closed"] = False
        else:
            return {"type": "unknown"}
        if hasattr(item, 'pen'):
            pen = item.pen()
            d["pen"] = {"color": pen.color().name(), "width": pen.widthF()}
        if hasattr(item, 'brush') and item.brush().style() != 0:
            b = item.brush()
            d["brush"] = b.color().name()
            d["brush_alpha"] = b.color().alpha()
        # Position + transform (move/rotate fidelity) for every item type
        d["pos"] = [item.pos().x(), item.pos().y()]
        tf = item.transform()
        if not tf.isIdentity():
            d["transform"] = [tf.m11(), tf.m12(), tf.m13(),
                              tf.m21(), tf.m22(), tf.m23(),
                              tf.m31(), tf.m32(), tf.m33()]
        d["data"] = item.data(0) or {}
        return d

    @staticmethod
    def _deserialize_item(sd: dict):
        t = sd.get("type")
        item = None
        if t == "div_point":
            from .tools import _make_div_marker
            m = _make_div_marker(QPointF(sd["pos"][0], sd["pos"][1]), 20.0)
            return m
        if t == "line":
            item = QGraphicsLineItem(QLineF(
                QPointF(sd["p1"][0], sd["p1"][1]),
                QPointF(sd["p2"][0], sd["p2"][1])))
        elif t == "rect":
            r = sd["rect"]
            item = QGraphicsRectItem(QRectF(r[0], r[1], r[2], r[3]))
        elif t == "circle":
            r = sd["rect"]
            item = QGraphicsEllipseItem(QRectF(r[0], r[1], r[2], r[3]))
        elif t == "path":
            pts = sd["points"]
            if len(pts) >= 2:
                path = QPainterPath(QPointF(pts[0][0], pts[0][1]))
                for p in pts[1:]:
                    path.lineTo(QPointF(p[0], p[1]))
                if sd.get("closed"):
                    path.closeSubpath()
                item = QGraphicsPathItem(path)
        elif t == "text":
            item = QGraphicsTextItem(sd.get("text", ""))
            from .tools import _load_vg5000
            f = _load_vg5000(sd.get("font_px", 12))
            ls = sd.get("letter_spacing", 0)
            if ls:
                f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, ls)
            item.setFont(f)
            item.setDefaultTextColor(QColor(sd.get("color", "#3C3C3C")))
            item.setTextWidth(sd.get("text_width", -1))
            item.setPos(sd["pos"][0], sd["pos"][1])
            item.setData(1, sd.get("kind", "word_text"))
        elif t == "pixmap":
            pm = _b64_to_pixmap(sd.get("data", ""))
            if pm is None or pm.isNull():
                return None
            item = QGraphicsPixmapItem(pm)
            item.setPos(sd["pos"][0], sd["pos"][1])
            item.setOpacity(sd.get("opacity", 0.7))
            item.setData(1, sd.get("marker"))
            item.setData(2, sd.get("fill_color"))
        if item is None:
            return None
        if "pen" in sd and hasattr(item, 'setPen'):
            pen = QPen(QColor(sd["pen"]["color"]))
            pen.setWidthF(sd["pen"].get("width", 1.0))
            pen.setCosmetic(True)
            item.setPen(pen)
        if "brush" in sd and hasattr(item, 'setBrush'):
            c = QColor(sd["brush"])
            c.setAlpha(sd.get("brush_alpha", 180))
            item.setBrush(QBrush(c))
        # Restore position + transform (move/rotate fidelity)
        if "pos" in sd:
            item.setPos(sd["pos"][0], sd["pos"][1])
        if "transform" in sd:
            m = sd["transform"]
            item.setTransform(QTransform(m[0], m[1], m[2],
                                         m[3], m[4], m[5],
                                         m[6], m[7], m[8]))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, sd.get("data", {}))
        return item


def _pixmap_to_b64(pm: QPixmap) -> str:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pm.save(buf, "PNG")
    return base64.b64encode(ba.data()).decode("ascii")


def _b64_to_pixmap(s: str) -> QPixmap | None:
    if not s:
        return None
    raw = base64.b64decode(s)
    pm = QPixmap()
    pm.loadFromData(raw, "PNG")
    return pm
