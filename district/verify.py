"""Floor verification — run: python -m district.verify

Asserts the lattice math (§3), seeds the empty city, stores a few objects, and
exercises the three reads (POINT / PATH / SET) + semantic search + the
.parti / .ppl distinction + multi-domain cross-zips.
"""
from __future__ import annotations

import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252 by default
except Exception:
    pass

from . import lattice
from .node import Node
from .store import DistrictStore


def main() -> None:
    print("── §3 lattice math ──")
    report = lattice.verify_counts()
    for pins, n in report["by_pins"].items():
        print(f"  {pins} pin(s): {n}")
    print(f"  base districts : {report['base_districts']:,}")
    print(f"  skeleton nodes : {report['skeleton_nodes']:,}")
    assert report["base_districts"] == 6_552
    assert report["skeleton_nodes"] == 406_224

    print("\n── numeric path (canon positions) ──")
    d = ("🦢", "🏛", "🌾", "⚫")
    print(f"  🦢🏛🌾⚫  POINT={lattice.point_string(d)}  "
          f"PATH={lattice.path_string(d)}  SET={lattice.set_string(d)}")
    print(f"  numeric_path = {lattice.numeric_path(d)}  (plico=9, ordo=1)")

    with tempfile.TemporaryDirectory() as tmp:
        store = DistrictStore(tmp)

        print("\n── seed the empty city ──")
        seeded = store.seed()
        print(f"  districts seeded into index: {seeded:,}")
        assert seeded == 6_552

        print("\n── store objects ──")
        room = Node(operator="🦢", axis="🏛", order="🌾", color="⚫",
                    title="projector fold", body="the room where folding happens",
                    page_type="parti")
        store.add_node(room)
        child = Node(operator="🦢", axis="🏛", order="🌾", color="⚫",
                     tail_text="wilson", title="wilson's fold",
                     body="wilson's instance", page_type="ppl")
        store.add_node(child)
        essay = Node(operator="🦉", axis="🪐", order="🖼", color="⚫",
                     title="deep essay", body="a long contemplative essay on folding",
                     page_type="md", cross_zips=["🦢🏛🌾⚫"])  # multi-domain edge
        store.add_node(essay)
        draft = Node(operator="✒️", color="🟡", tail=["📍"],
                     title="social draft", body="quick post about folding",
                     page_type="md")  # partial district ✒️__🟡±📍
        store.add_node(draft)
        print(f"  stored: room(.parti) child(.ppl) essay(.md) draft(partial)")
        print(f"  room.file={room.file}  child.file={child.file}  "
              f"(.parti vs .ppl from ± tail)")
        assert room.file.endswith(".parti") and child.file.endswith(".ppl")

        print("\n── POINT  (exact coordinate 🦢🏛🌾⚫) ──")
        pts = store.point(operator="🦢", axis="🏛", order="🌾", color="⚫")
        for n in pts:
            print(f"  • {n.point_string()}  '{n.title}'")
        assert len(pts) == 2  # room + child both sit at the point

        print("\n── SET  (operator-button filter: 🦢, any axis/order/color) ──")
        s = store.set(operator="🦢")
        for n in s:
            print(f"  • {n.point_string()}  '{n.title}'")
        assert len(s) == 2

        print("\n── SET  (color-only district 🟡) ──")
        sy = store.set(color="🟡")
        for n in sy:
            print(f"  • {n.point_string()}  '{n.title}'")
        assert len(sy) == 1 and sy[0].title == "social draft"

        print("\n── PATH  (drill-down tree, operator→axis→order→color) ──")
        for n in store.path():
            print(f"  {n.point_string():<18} '{n.title}'")

        print("\n── PATH  (reordered color→operator: a different tree, same store) ──")
        for n in store.path(slot_order=("color", "operator", "axis", "order")):
            print(f"  {n.point_string():<18} '{n.title}'")

        print("\n── semantic search ('essay') ──")
        for n in store.search("essay"):
            print(f"  • '{n.title}'  cross_zips={n.cross_zips}")

        print("\n── structural edge (everything sharing color ⚫) ──")
        e = store.edges("color", "⚫")
        print(f"  {len(e)} nodes share ⚫: {[n.title for n in e]}")
        assert len(e) == 3

        store.close()

    print("\n✅ floor verified — lattice math + 3 reads + edges + .parti/.ppl")


if __name__ == "__main__":
    main()
