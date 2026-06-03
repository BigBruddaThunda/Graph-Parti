"""The district lattice — the fixed, finite address space.

A district is a 4-slot coordinate where each slot is a canon glyph OR blank
(None). Pin-count (how many slots are filled) is district *width*: 0 pins is the
whole city, 4 pins is one room. The lattice is closed and enumerable:

    (12+1) · (6+1) · (7+1) · (8+1) = 13·7·8·9 = 6,552 base districts

With each base district carrying a no-tail form plus 61 single-glyph-tail
children: 6,552 · 62 = 406,224 fixed skeleton nodes. The skeleton never grows;
growth lives in leaves (free text / multi-glyph tails) parented to skeleton nodes.
"""
from __future__ import annotations

import itertools
from typing import Iterator

from . import canon

# A district is a tuple (operator, axis, order, color), each glyph or None.
District = tuple

BASE_DISTRICT_COUNT = 6_552
SKELETON_COUNT = 406_224          # 6,552 × (1 no-tail + 61 single-tail)
SINGLE_TAIL_FANOUT = 62           # 1 + 61


def base_districts() -> Iterator[District]:
    """Yield every base district: one pick per slot, including the blank state."""
    opts = [
        [None] + canon.OPERATORS,
        [None] + canon.AXES,
        [None] + canon.ORDERS,
        [None] + canon.COLORS,
    ]
    for op, ax, orr, col in itertools.product(*opts):
        yield (op, ax, orr, col)


def pin_count(district: District) -> int:
    """How many slots are filled (district width: 0=city … 4=room)."""
    return sum(1 for slot in district if slot is not None)


def count_by_pins() -> dict[int, int]:
    """Exact district counts grouped by pin-count (the §3 enumeration)."""
    counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for d in base_districts():
        counts[pin_count(d)] += 1
    return counts


def numeric_path(district: District) -> str:
    """Canonical numeric path for git's on-disk tree, e.g. 🦢🏛🌾⚫ -> '09/1/5/1'.
    Blank slots render as '_'."""
    op, ax, orr, col = district
    return "/".join([
        canon.numeric_segment("operator", op),
        canon.numeric_segment("axis", ax),
        canon.numeric_segment("order", orr),
        canon.numeric_segment("color", col),
    ])


def point_string(district: District) -> str:
    """The POINT spelling — glyphs concatenated, blanks shown as '_'."""
    return "".join(g if g is not None else "_" for g in district)


def path_string(district: District) -> str:
    """The PATH spelling — glyphs slash-joined (drill-down tree form)."""
    return "/".join(g if g is not None else "_" for g in district)


def set_string(district: District) -> str:
    """The SET spelling — filled facets comma-joined (faceted filter form)."""
    return ",".join(g for g in district if g is not None)


def verify_counts() -> dict:
    """Assert the lattice math matches the canon enumeration. Returns the report."""
    by_pins = count_by_pins()
    expected = {0: 1, 1: 33, 2: 398, 3: 2088, 4: 4032}
    assert by_pins == expected, f"pin-count mismatch: {by_pins} != {expected}"
    total = sum(by_pins.values())
    assert total == BASE_DISTRICT_COUNT, f"{total} != {BASE_DISTRICT_COUNT}"
    skeleton = total * SINGLE_TAIL_FANOUT
    assert skeleton == SKELETON_COUNT, f"{skeleton} != {SKELETON_COUNT}"
    return {
        "by_pins": by_pins,
        "base_districts": total,
        "skeleton_nodes": skeleton,
    }
