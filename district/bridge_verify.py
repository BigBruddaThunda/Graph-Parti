"""Bridge verification — run: python -m district.bridge_verify

Proves the graphparti ↔ district data path headless (offscreen Qt):
a canvas drawing is filed as a district node at its zip, then resolved back
out of the index onto a fresh document (the book resolve-path).
"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF, QLineF, QPointF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsLineItem

from graphparti.document import Document
from graphparti.district_bridge import DistrictBridge


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as tmp:
        bridge = DistrictBridge(tmp)
        print("seeded districts:", bridge.seed())

        # Build a drawing (3 lines) on a document
        scene = QGraphicsScene()
        doc = Document.default(scene, QRectF(-100, -100, 200, 200))
        for i in range(3):
            ln = QGraphicsLineItem(QLineF(0, i * 20, 40, i * 20))
            ln.setData(0, {"zip": "", "note": ""})
            doc.layers[1].add_item(ln)
        print("drawing items:", len(doc.layers[1].items()))

        # File it as a district node at 🦢🏛🌾⚫
        facets = ("🦢", "🏛", "🌾", "⚫")
        node = bridge.save_canvas(doc, facets, "projector cockpit frame")
        print(f"filed at {node.point_string()}  →  {node.file}  ({node.numeric_path})")
        assert node.file.endswith(".parti")

        # POINT lookup finds it
        hits = bridge.store.point(operator="🦢", axis="🏛", order="🌾", color="⚫")
        assert len(hits) == 1 and hits[0].title == "projector cockpit frame"
        print("POINT lookup:", hits[0].title)

        # Resolve the book onto a FRESH document (the drag-from-shelf path)
        scene2 = QGraphicsScene()
        doc2 = Document.default(scene2, QRectF(-100, -100, 200, 200))
        placed = bridge.place_book(doc2, operator="🦢", axis="🏛",
                                   order="🌾", color="⚫", clear=True)
        print("resolved book items:", len(doc2.layers[1].items()))
        assert placed is not None
        assert len(doc2.layers[1].items()) == 3  # round-tripped through the index

        bridge.close()
    print("\n✅ bridge verified — canvas drawing → district node → resolved back")


if __name__ == "__main__":
    main()
