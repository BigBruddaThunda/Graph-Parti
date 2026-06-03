"""The facet index — SQLite over one store.

This is the structural index (coordinates). It answers the three reads:
  • POINT — objects at an exact 4-facet coordinate
  • SET   — objects whose facets include the given ones (partial, any order)
  • PATH  — objects ordered by a chosen slot sequence (a tree renders from this)

plus a keyword semantic read over the '|' body (embeddings come later). The PATH
and SET *views* are generated here from facets — never stored as duplicate
folders. One store, three reads.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Iterable

from . import canon, lattice
from .node import Node

# DB column <-> Node facet (f_order avoids the SQL reserved word ORDER)
_FACET_COLS = {"operator": "f_operator", "axis": "f_axis",
               "order": "f_order", "color": "f_color"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS districts (
    point_string TEXT PRIMARY KEY,
    numeric_path TEXT,
    pin_count    INTEGER
);
CREATE TABLE IF NOT EXISTS nodes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    f_operator   TEXT, f_axis TEXT, f_order TEXT, f_color TEXT,
    type         TEXT,
    tail         TEXT, tail_text TEXT,
    title        TEXT, body TEXT, page_type TEXT,
    inline_zips  TEXT, cross_zips TEXT,
    numeric_path TEXT, file TEXT, git_branch TEXT
);
CREATE INDEX IF NOT EXISTS ix_nodes_facets
    ON nodes (f_operator, f_axis, f_order, f_color);
CREATE INDEX IF NOT EXISTS ix_nodes_path ON nodes (numeric_path);
"""


class FacetIndex:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    # ────────────────────────────────────────────── skeleton seed
    def seed_districts(self, include_single_tails: bool = False) -> int:
        """Lay the empty city into the index. Base = 6,552 rows. (Physical git
        dirs stay lazy — created only when an object lands; see store.py.)"""
        rows = []
        for d in lattice.base_districts():
            rows.append((lattice.point_string(d), lattice.numeric_path(d),
                         lattice.pin_count(d)))
        self.conn.executemany(
            "INSERT OR REPLACE INTO districts VALUES (?,?,?)", rows)
        self.conn.commit()
        return len(rows)

    # ────────────────────────────────────────────── write
    def add(self, node: Node) -> int:
        if not node.numeric_path:
            node.compute_numeric_path()
        cur = self.conn.execute(
            """INSERT INTO nodes
               (f_operator,f_axis,f_order,f_color,type,tail,tail_text,
                title,body,page_type,inline_zips,cross_zips,
                numeric_path,file,git_branch)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (node.operator, node.axis, node.order, node.color, node.type,
             json.dumps(node.tail), node.tail_text,
             node.title, node.body, node.page_type,
             json.dumps(node.inline_zips), json.dumps(node.cross_zips),
             node.numeric_path, node.file, node.git_branch))
        self.conn.commit()
        return cur.lastrowid

    # ────────────────────────────────────────────── three reads
    def point(self, operator=None, axis=None, order=None, color=None) -> list[Node]:
        """Exact coordinate: every facet matched, NULLs matched as NULL."""
        wanted = {"operator": operator, "axis": axis, "order": order, "color": color}
        clauses, params = [], []
        for slot, val in wanted.items():
            col = _FACET_COLS[slot]
            if val is None:
                clauses.append(f"{col} IS NULL")
            else:
                clauses.append(f"{col} = ?")
                params.append(val)
        return self._query(" AND ".join(clauses), params)

    def set_query(self, **facets) -> list[Node]:
        """Faceted filter: only the provided (non-None) facets constrain; the
        rest are free. This is the operator-button filter + partial-zip query."""
        clauses, params = [], []
        for slot, val in facets.items():
            if val is None:
                continue
            col = _FACET_COLS[slot]
            clauses.append(f"{col} = ?")
            params.append(val)
        where = " AND ".join(clauses) if clauses else "1=1"
        return self._query(where, params)

    def path_view(self, slot_order: Iterable[str] = canon.SLOTS) -> list[Node]:
        """Drill-down tree: nodes sorted by a chosen slot sequence. Reorder the
        slots and you get a different tree over the same store, for free."""
        cols = [_FACET_COLS[s] for s in slot_order]
        order_by = ", ".join(f"{c} IS NULL, {c}" for c in cols)
        return self._query("1=1", [], order_by=order_by)

    def structural_edges(self, slot: str, glyph: str) -> list[Node]:
        """Every node sharing a facet — the computed (automatic) web edges."""
        return self.set_query(**{slot: glyph})

    def search(self, text: str) -> list[Node]:
        """Keyword read over the body plane (embeddings later)."""
        like = f"%{text}%"
        return self._query(
            "(title LIKE ? OR body LIKE ? OR tail_text LIKE ?)",
            [like, like, like])

    # ────────────────────────────────────────────── internals
    def _query(self, where: str, params: list, order_by: str = "id") -> list[Node]:
        sql = f"SELECT * FROM nodes WHERE {where} ORDER BY {order_by}"
        return [self._row_to_node(r) for r in self.conn.execute(sql, params)]

    @staticmethod
    def _row_to_node(r: sqlite3.Row) -> Node:
        return Node(
            operator=r["f_operator"], axis=r["f_axis"],
            order=r["f_order"], color=r["f_color"], type=r["type"],
            tail=json.loads(r["tail"] or "[]"), tail_text=r["tail_text"] or "",
            title=r["title"] or "", body=r["body"] or "",
            page_type=r["page_type"] or "",
            inline_zips=json.loads(r["inline_zips"] or "[]"),
            cross_zips=json.loads(r["cross_zips"] or "[]"),
            numeric_path=r["numeric_path"] or "", file=r["file"] or "",
            git_branch=r["git_branch"] or "")

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def district_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM districts").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
