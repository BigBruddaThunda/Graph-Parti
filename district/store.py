"""The git bridge — one canonical numeric tree + a SQLite facet index.

Git wants a real directory tree; the system wants facet-views. Reconciled:

  • on disk  — ONE canonical numeric path per object (git diffs/merges/forks it)
  • beside it — state.sqlite holds the facets; POINT/PATH/SET views generate from it

Nothing is stored three times. The PATH/SET spellings are computed; only the
numeric PATH home is materialized, and only for objects that actually land
(the empty skeleton lives in the index, not as 406k empty dirs).
"""
from __future__ import annotations

import json
import os
import re

from .index import FacetIndex
from .node import Node


def _slug(text: str, fallback: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:48] or fallback


class DistrictStore:
    def __init__(self, root: str) -> None:
        self.root = root
        self.content_dir = os.path.join(root, "content")
        os.makedirs(self.content_dir, exist_ok=True)
        self.index = FacetIndex(os.path.join(root, "state.sqlite"))

    # ────────────────────────────────────────────── seed the empty city
    def seed(self, include_single_tails: bool = False) -> int:
        return self.index.seed_districts(include_single_tails)

    # ────────────────────────────────────────────── store an object
    def add_node(self, node: Node, ext: str | None = None) -> Node:
        """Write the object to its canonical numeric home and index its facets.
        ext defaults to 'ppl' for person-scoped (tailed) nodes, else 'parti'."""
        problems = node.validate()
        if problems:
            raise ValueError(f"non-canon node: {problems}")
        node.compute_numeric_path()
        if ext is None:
            ext = "ppl" if node.is_ppl else "parti"
        dir_path = os.path.join(self.content_dir, *node.numeric_path.split("/"))
        os.makedirs(dir_path, exist_ok=True)
        if not node.file:
            node.file = f"{_slug(node.title, 'room')}.{ext}"
        with open(os.path.join(dir_path, node.file), "w", encoding="utf-8") as f:
            json.dump(node.to_dict(), f, indent=2, ensure_ascii=False)
        self.index.add(node)
        return node

    # ────────────────────────────────────────────── the three reads
    def point(self, **facets) -> list[Node]:
        return self.index.point(**facets)

    def set(self, **facets) -> list[Node]:
        return self.index.set_query(**facets)

    def path(self, slot_order=None) -> list[Node]:
        return (self.index.path_view(slot_order) if slot_order
                else self.index.path_view())

    def search(self, text: str) -> list[Node]:
        return self.index.search(text)

    def edges(self, slot: str, glyph: str) -> list[Node]:
        return self.index.structural_edges(slot, glyph)

    def close(self) -> None:
        self.index.close()
