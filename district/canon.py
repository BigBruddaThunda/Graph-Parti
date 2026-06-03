"""Closed SCL canon for the District file system.

Mirrors system/scl/constants.yaml (SCL v5 — the closed 61). District is a peer
package: neither graphparti nor archideck imports the other through it, so this
canon is self-contained here rather than imported across the isolation boundary.

The four address slots are Operator · Axis · Order · Color (12·6·7·8). Each slot
also has a *blank* state (None) — the blank is what makes partial districts
first-class (a partial zip is a wider district).
"""
from __future__ import annotations

# ── the four address slots, in canon position order (1-based positions) ──
OPERATORS = ["📍", "🧲", "🤌", "👀", "🐋", "🧸",
             "🚀", "🥨", "🦢", "🦉", "🪵", "✒️"]            # 12
AXES = ["🏛", "🔨", "🌹", "🪐", "⌛", "🐬"]                   # 6
ORDERS = ["🐂", "⛽", "🦋", "🏟", "🌾", "⚖", "🖼"]           # 7
COLORS = ["⚫", "🟢", "🔵", "🟣", "🔴", "🟠", "🟡", "⚪"]      # 8

# ── the rest of the closed 61 (valid tail glyphs) ──
MODIFIERS = ["🛒", "🪡", "🍗", "➕", "➖"]                     # 5
BLOCKS = ["♨️", "🎯", "🔢", "🧈", "🫀", "▶️", "🎼", "♟️", "🪜", "🌎", "🎱",
          "🌋", "🪞", "🗿", "🛠", "🧩", "🪫", "🏖", "🏗", "🧬", "🚂", "🔠"]   # 22
SYSTEM = ["🧮"]                                               # 1

CANON_61 = OPERATORS + AXES + ORDERS + COLORS + MODIFIERS + BLOCKS + SYSTEM
assert len(CANON_61) == 61, f"canon must be 61 glyphs, got {len(CANON_61)}"

# ── slot machinery ──
SLOTS = ("operator", "axis", "order", "color")
SLOT_GLYPHS = {
    "operator": OPERATORS,
    "axis": AXES,
    "order": ORDERS,
    "color": COLORS,
}

# glyph -> 1-based position within its slot (per slot)
_POS = {slot: {g: i + 1 for i, g in enumerate(glyphs)}
        for slot, glyphs in SLOT_GLYPHS.items()}


def position(slot: str, glyph: str | None) -> int:
    """1-based position of glyph within its slot; 0 for blank."""
    if glyph is None:
        return 0
    return _POS[slot][glyph]


def is_valid(slot: str, glyph: str | None) -> bool:
    return glyph is None or glyph in _POS[slot]


def is_canon(glyph: str) -> bool:
    return glyph in CANON_61


def numeric_segment(slot: str, glyph: str | None) -> str:
    """Numeric path segment for a facet. Operator is zero-padded to 2 digits;
    the others are single digits. Blank renders as '_'."""
    n = position(slot, glyph)
    if n == 0:
        return "_"
    return f"{n:02d}" if slot == "operator" else str(n)
