"""graphparti ↔ district bridge.

The canvas writes its .parti drawings into the District file system as nodes that
carry their address as facets (from the active zip dial), and resolves placed
"books" back out of the index. This is the one allowed cross-package dependency:
graphparti → district (the storage layer the doc intends the canvas to write).
graphparti still never imports the Archideck cockpit — facets arrive as plain
glyph strings the host sets on the canvas.
"""
from __future__ import annotations

import json

from district import DistrictStore, Node

from .document import Document


def document_to_node(doc: Document, facets: tuple, title: str,
                     tail_text: str = "", page_type: str = "parti",
                     cross_zips: list[str] | None = None) -> Node:
    """Wrap a drawing as a district Node. facets = (operator, axis, order, color),
    each a glyph or None (None = a wider/partial district)."""
    op, ax, orr, col = facets
    return Node(
        operator=op, axis=ax, order=orr, color=col,
        tail_text=tail_text,
        title=title,
        body=json.dumps(doc.to_dict(), ensure_ascii=False),
        page_type="ppl" if tail_text else page_type,
        cross_zips=list(cross_zips or []),
    )


def node_into_document(node: Node, doc: Document, clear: bool = True) -> None:
    """Rehydrate a node's drawing body back onto a document. clear=False places
    the book on top of the current drawing (drag-from-shelf)."""
    if not node.body:
        return
    doc.from_dict(json.loads(node.body), clear=clear)


class DistrictBridge:
    """Thin facade tying the canvas's document to a DistrictStore."""

    def __init__(self, store_root: str) -> None:
        self.store = DistrictStore(store_root)

    def seed(self) -> int:
        return self.store.seed()

    def save_canvas(self, doc: Document, facets: tuple, title: str,
                    tail_text: str = "", cross_zips=None) -> Node:
        """Write the current drawing as a district node at its zip coordinate."""
        node = document_to_node(doc, facets, title, tail_text=tail_text,
                                cross_zips=cross_zips)
        return self.store.add_node(node)

    def place_book(self, doc: Document, *, operator=None, axis=None,
                   order=None, color=None, clear: bool = False) -> Node | None:
        """Resolve a book by its POINT coordinate and place its drawing onto the
        document. Returns the resolved node (or None). Edit-once-update-everywhere:
        re-resolving pulls the current content at that address."""
        hits = self.store.point(operator=operator, axis=axis,
                                order=order, color=color)
        if not hits:
            return None
        node = hits[0]
        node_into_document(node, doc, clear=clear)
        return node

    def close(self) -> None:
        self.store.close()
