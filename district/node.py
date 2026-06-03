"""The Node record — a coordinate-plus-body pair (the doc's §13).

Two planes per node:
  • structural (the facets + tail)  — closed, the coordinate, sets the *mode*
  • content    (title + body)       — open, the material, read in that mode

The same body at a different coordinate reads differently: the zip is the
register, '|' is the material, the register says what to do with the material.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import canon, lattice


@dataclass
class Node:
    # ── structural plane (facet index) ──
    operator: str | None = None
    axis: str | None = None
    order: str | None = None
    color: str | None = None
    type: str | None = None              # optional modifier glyph
    tail: list[str] = field(default_factory=list)   # ordered canon glyphs
    tail_text: str = ""                  # freetext leaf (semantically indexed)

    # ── content plane (semantic index) ──
    title: str = ""
    body: str = ""
    page_type: str = ""                  # md|py|yaml|parti|ppl|raster|vector|ics|nested
    inline_zips: list[str] = field(default_factory=list)

    # ── edges ──
    cross_zips: list[str] = field(default_factory=list)  # body-declared semantic edges

    # ── storage ──
    numeric_path: str = ""
    file: str = ""
    git_branch: str = ""

    # ── derived views ──
    @property
    def district(self) -> tuple:
        return (self.operator, self.axis, self.order, self.color)

    @property
    def pin_count(self) -> int:
        return lattice.pin_count(self.district)

    @property
    def is_skeleton(self) -> bool:
        """A node is skeleton iff its tail is 0 or 1 canon glyph (no leaves)."""
        return len(self.tail) <= 1 and not self.tail_text

    @property
    def is_ppl(self) -> bool:
        """A person-scoped tail makes it a .ppl child; otherwise a .parti room."""
        return bool(self.tail_text) or bool(self.tail)

    def point_string(self) -> str:
        base = lattice.point_string(self.district)
        if self.tail or self.tail_text:
            suffix = "".join(self.tail)
            if self.tail_text:
                suffix = (suffix + "|" if suffix else "") + self.tail_text
            return f"{base}±{suffix}"
        return base

    def compute_numeric_path(self) -> str:
        self.numeric_path = lattice.numeric_path(self.district)
        return self.numeric_path

    def validate(self) -> list[str]:
        """Return a list of canon violations (empty = valid)."""
        problems = []
        for slot, g in zip(canon.SLOTS, self.district):
            if not canon.is_valid(slot, g):
                problems.append(f"{slot}={g!r} not canon")
        if self.type is not None and self.type not in canon.MODIFIERS:
            problems.append(f"type={self.type!r} not a modifier")
        for g in self.tail:
            if not canon.is_canon(g):
                problems.append(f"tail glyph {g!r} not canon")
        return problems

    def to_dict(self) -> dict:
        return {
            "operator": self.operator, "axis": self.axis,
            "order": self.order, "color": self.color,
            "type": self.type, "tail": list(self.tail), "tail_text": self.tail_text,
            "title": self.title, "body": self.body, "page_type": self.page_type,
            "inline_zips": list(self.inline_zips), "cross_zips": list(self.cross_zips),
            "numeric_path": self.numeric_path, "file": self.file,
            "git_branch": self.git_branch,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(
            operator=d.get("operator"), axis=d.get("axis"),
            order=d.get("order"), color=d.get("color"),
            type=d.get("type"), tail=list(d.get("tail") or []),
            tail_text=d.get("tail_text", ""),
            title=d.get("title", ""), body=d.get("body", ""),
            page_type=d.get("page_type", ""),
            inline_zips=list(d.get("inline_zips") or []),
            cross_zips=list(d.get("cross_zips") or []),
            numeric_path=d.get("numeric_path", ""), file=d.get("file", ""),
            git_branch=d.get("git_branch", ""),
        )
