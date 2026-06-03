"""The Five Classical Orders per American Vignola — vector line drawings.

All dimensions in Diameters (D) where 1D = 1 grid cell = grid_spacing scene units.
Proportions follow Giacomo Barozzi da Vignola's Regola delli cinque ordini
d'architettura (1562) as transmitted through William R. Ware's American Vignola.

Each order is drawn as QGraphicsLineItems on the active vector layer.
"""
from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem


# ─────────────────────────────────────────── proportional data (in Diameters)
# fmt: off
ORDERS = {
    "tuscan": {
        "column_h": 7.0, "entablature_h": 1.75,
        "base_h": 0.5, "capital_h": 0.5,
        "shaft_h": 6.0,
        "upper_d": 0.75, "plinth_w": 1.4,
        "architrave": 0.50, "frieze": 0.583, "cornice": 0.667,
        "flutes": 0,
    },
    "doric": {
        "column_h": 8.0, "entablature_h": 2.0,
        "base_h": 0.5, "capital_h": 0.667,
        "shaft_h": 6.833,
        "upper_d": 0.80, "plinth_w": 1.4,
        "architrave": 0.50, "frieze": 0.75, "cornice": 0.75,
        "flutes": 20,
    },
    "ionic": {
        "column_h": 9.0, "entablature_h": 2.25,
        "base_h": 0.5, "capital_h": 0.667,
        "shaft_h": 7.833,
        "upper_d": 0.833, "plinth_w": 1.5,
        "architrave": 0.625, "frieze": 0.75, "cornice": 0.875,
        "flutes": 24,
    },
    "corinthian": {
        "column_h": 10.0, "entablature_h": 2.5,
        "base_h": 0.5, "capital_h": 1.167,
        "shaft_h": 8.333,
        "upper_d": 0.833, "plinth_w": 1.5,
        "architrave": 0.625, "frieze": 0.75, "cornice": 1.125,
        "flutes": 24,
    },
    "composite": {
        "column_h": 10.0, "entablature_h": 2.5,
        "base_h": 0.5, "capital_h": 1.167,
        "shaft_h": 8.333,
        "upper_d": 0.833, "plinth_w": 1.5,
        "architrave": 0.625, "frieze": 0.75, "cornice": 1.125,
        "flutes": 24,
    },
}
# fmt: on

# Column order for placement (matches Archideck order dial 1-5)
ORDER_SEQUENCE = ["tuscan", "doric", "ionic", "corinthian", "composite"]

_STROKE = "#3C3C3C"
_LIGHT = "#999999"
_ACCENT = "#2464E5"


def _pen(color: str = _STROKE, width: float = 1.0) -> QPen:
    p = QPen(QColor(color))
    p.setWidthF(width)
    p.setCosmetic(True)
    return p


def _line(x1, y1, x2, y2, pen=None) -> QGraphicsLineItem:
    item = QGraphicsLineItem(QLineF(QPointF(x1, y1), QPointF(x2, y2)))
    item.setPen(pen or _pen())
    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    item.setData(0, {"zip": "", "note": ""})
    return item


def draw_order(name: str, cx: float, baseline: float, gs: float) -> list[QGraphicsLineItem]:
    """Draw one order centered at *cx*, baseline at *baseline* (scene coords).
    Returns list of line items. 1D = gs scene units."""
    o = ORDERS[name]
    items: list[QGraphicsLineItem] = []

    def D(v): return v * gs  # diameter to scene units
    def Y(d): return baseline - D(d)  # d above baseline

    col_h = o["column_h"]
    ent_h = o["entablature_h"]
    base_h = o["base_h"]
    cap_h = o["capital_h"]
    shaft_h = o["shaft_h"]
    upper = o["upper_d"]
    plinth_w = o["plinth_w"]
    arch_h = o["architrave"]
    frieze_h = o["frieze"]
    corn_h = o["cornice"]

    half = D(0.5)        # half diameter at base
    half_top = D(upper / 2)  # half diameter at top

    pen_main = _pen(_STROKE, 1.0)
    pen_light = _pen(_LIGHT, 0.5)
    pen_ref = _pen(_ACCENT, 0.5)

    # ──── centerline (reference) ────
    items.append(_line(cx, baseline + D(0.2), cx, Y(col_h + ent_h + 0.2), pen_ref))

    # ──── base (plinth + moldings) ────
    pw = D(plinth_w / 2)
    y_base_top = Y(base_h)
    plinth_h = D(base_h * 0.4)

    # Plinth rectangle
    items.append(_line(cx - pw, baseline, cx + pw, baseline, pen_main))  # bottom
    items.append(_line(cx - pw, baseline, cx - pw, baseline - plinth_h, pen_main))  # left
    items.append(_line(cx + pw, baseline, cx + pw, baseline - plinth_h, pen_main))  # right
    items.append(_line(cx - pw, baseline - plinth_h, cx + pw, baseline - plinth_h, pen_main))  # top

    # Torus (simplified as wider band above plinth)
    torus_w = D(0.6)
    torus_h = D(base_h * 0.3)
    y_torus = baseline - plinth_h
    items.append(_line(cx - torus_w, y_torus, cx - torus_w, y_torus - torus_h, pen_main))
    items.append(_line(cx + torus_w, y_torus, cx + torus_w, y_torus - torus_h, pen_main))
    items.append(_line(cx - torus_w, y_torus - torus_h, cx + torus_w, y_torus - torus_h, pen_main))

    # Fillet to shaft
    items.append(_line(cx - half, y_base_top, cx + half, y_base_top, pen_light))

    # ──── shaft (tapered) ────
    y_shaft_top = Y(base_h + shaft_h)
    items.append(_line(cx - half, y_base_top, cx - half_top, y_shaft_top, pen_main))
    items.append(_line(cx + half, y_base_top, cx + half_top, y_shaft_top, pen_main))

    # Entasis reference: 1/3 point (where entasis begins in Vignola)
    y_third = y_base_top - D(shaft_h / 3)
    items.append(_line(cx - half - D(0.15), y_third, cx - half + D(0.05), y_third, pen_light))
    items.append(_line(cx + half - D(0.05), y_third, cx + half + D(0.15), y_third, pen_light))

    # ──── capital ────
    y_cap_top = Y(col_h)

    if name == "tuscan":
        # Simple abacus + echinus (rectangular)
        ab_w = D(0.6)
        ab_h = D(cap_h * 0.3)
        ech_h = D(cap_h * 0.4)
        # Necking
        items.append(_line(cx - half_top, y_shaft_top, cx - half_top, y_shaft_top - D(cap_h * 0.3), pen_main))
        items.append(_line(cx + half_top, y_shaft_top, cx + half_top, y_shaft_top - D(cap_h * 0.3), pen_main))
        # Echinus (wider trapezoid)
        y_ech = y_shaft_top - D(cap_h * 0.3)
        items.append(_line(cx - half_top, y_ech, cx - ab_w, y_ech - ech_h, pen_main))
        items.append(_line(cx + half_top, y_ech, cx + ab_w, y_ech - ech_h, pen_main))
        items.append(_line(cx - ab_w, y_ech - ech_h, cx + ab_w, y_ech - ech_h, pen_main))
        # Abacus
        items.append(_line(cx - ab_w, y_ech - ech_h, cx - ab_w, y_cap_top, pen_main))
        items.append(_line(cx + ab_w, y_ech - ech_h, cx + ab_w, y_cap_top, pen_main))
        items.append(_line(cx - ab_w, y_cap_top, cx + ab_w, y_cap_top, pen_main))

    elif name == "doric":
        # Echinus + abacus + annulets + neck
        ab_w = D(0.6)
        neck_h = D(cap_h * 0.25)
        ann_h = D(cap_h * 0.1)
        ech_h = D(cap_h * 0.35)
        ab_h = D(cap_h * 0.3)
        y = y_shaft_top
        # Neck
        items.append(_line(cx - half_top, y, cx - half_top, y - neck_h, pen_main))
        items.append(_line(cx + half_top, y, cx + half_top, y - neck_h, pen_main))
        y -= neck_h
        # Annulets (3 thin rings)
        for i in range(3):
            ring_w = half_top + D(0.02 * (i + 1))
            items.append(_line(cx - ring_w, y, cx + ring_w, y, pen_main))
            y -= D(0.02)
        # Echinus (curved outward — simplified as trapezoid)
        items.append(_line(cx - half_top - D(0.05), y, cx - ab_w, y - ech_h, pen_main))
        items.append(_line(cx + half_top + D(0.05), y, cx + ab_w, y - ech_h, pen_main))
        items.append(_line(cx - ab_w, y - ech_h, cx + ab_w, y - ech_h, pen_main))
        y -= ech_h
        # Abacus
        items.append(_line(cx - ab_w, y, cx - ab_w, y_cap_top, pen_main))
        items.append(_line(cx + ab_w, y, cx + ab_w, y_cap_top, pen_main))
        items.append(_line(cx - ab_w, y_cap_top, cx + ab_w, y_cap_top, pen_main))

    elif name == "ionic":
        # Volute capital
        ab_w = D(0.55)
        vol_w = D(0.75)  # volutes extend beyond shaft
        vol_h = D(cap_h * 0.5)
        ech_h = D(cap_h * 0.2)
        ab_h = D(cap_h * 0.15)
        y = y_shaft_top
        # Echinus with egg-and-dart (simplified band)
        items.append(_line(cx - half_top - D(0.05), y, cx - ab_w, y - ech_h, pen_main))
        items.append(_line(cx + half_top + D(0.05), y, cx + ab_w, y - ech_h, pen_main))
        items.append(_line(cx - ab_w, y - ech_h, cx + ab_w, y - ech_h, pen_main))
        y -= ech_h
        # Volutes (simplified as rectangles extending out + spiral hint)
        items.append(_line(cx - vol_w, y, cx - ab_w, y, pen_main))
        items.append(_line(cx + ab_w, y, cx + vol_w, y, pen_main))
        items.append(_line(cx - vol_w, y, cx - vol_w, y - vol_h, pen_main))
        items.append(_line(cx + vol_w, y, cx + vol_w, y - vol_h, pen_main))
        items.append(_line(cx - vol_w, y - vol_h, cx - ab_w, y - vol_h, pen_main))
        items.append(_line(cx + ab_w, y - vol_h, cx + vol_w, y - vol_h, pen_main))
        # Spiral center marks
        spy = y - vol_h * 0.5
        items.append(_line(cx - vol_w + D(0.05), spy - D(0.05),
                           cx - vol_w + D(0.15), spy + D(0.05), pen_light))
        items.append(_line(cx + vol_w - D(0.15), spy - D(0.05),
                           cx + vol_w - D(0.05), spy + D(0.05), pen_light))
        y -= vol_h
        # Abacus
        items.append(_line(cx - ab_w, y, cx - ab_w, y_cap_top, pen_main))
        items.append(_line(cx + ab_w, y, cx + ab_w, y_cap_top, pen_main))
        items.append(_line(cx - ab_w, y_cap_top, cx + ab_w, y_cap_top, pen_main))

    elif name in ("corinthian", "composite"):
        # Tall bell capital with acanthus rows
        ab_w = D(0.65)
        bell_w_bot = half_top
        bell_w_top = D(0.6)
        cap_total = D(cap_h)
        ab_h = D(0.15)
        y = y_shaft_top
        # Bell shape (flared)
        items.append(_line(cx - bell_w_bot, y, cx - bell_w_top, y_cap_top + ab_h, pen_main))
        items.append(_line(cx + bell_w_bot, y, cx + bell_w_top, y_cap_top + ab_h, pen_main))
        # Acanthus row 1 (lower third)
        leaf_y1 = y - cap_total * 0.33
        leaf_w1 = bell_w_bot + (bell_w_top - bell_w_bot) * 0.33
        items.append(_line(cx - leaf_w1 - D(0.1), leaf_y1, cx + leaf_w1 + D(0.1), leaf_y1, pen_light))
        # Leaf tips (lower row)
        for sign in (-1, 1):
            items.append(_line(cx + sign * bell_w_bot, y,
                               cx + sign * (leaf_w1 + D(0.1)), leaf_y1, pen_light))
        # Acanthus row 2 (upper third)
        leaf_y2 = y - cap_total * 0.6
        leaf_w2 = bell_w_bot + (bell_w_top - bell_w_bot) * 0.6
        items.append(_line(cx - leaf_w2 - D(0.08), leaf_y2, cx + leaf_w2 + D(0.08), leaf_y2, pen_light))
        # Small volutes at top corners
        if name == "composite":
            # Ionic-style volutes
            vol_ext = D(0.12)
            vy = y_cap_top + ab_h + D(0.15)
            items.append(_line(cx - bell_w_top, vy, cx - bell_w_top - vol_ext, vy, pen_main))
            items.append(_line(cx + bell_w_top, vy, cx + bell_w_top + vol_ext, vy, pen_main))
            items.append(_line(cx - bell_w_top - vol_ext, vy,
                               cx - bell_w_top - vol_ext, vy + D(0.1), pen_main))
            items.append(_line(cx + bell_w_top + vol_ext, vy,
                               cx + bell_w_top + vol_ext, vy + D(0.1), pen_main))
        else:
            # Small caulicoli/volutes
            vy = y_cap_top + ab_h + D(0.1)
            items.append(_line(cx - bell_w_top + D(0.05), vy,
                               cx - bell_w_top - D(0.05), vy - D(0.08), pen_light))
            items.append(_line(cx + bell_w_top - D(0.05), vy,
                               cx + bell_w_top + D(0.05), vy - D(0.08), pen_light))
        # Abacus (concave sides for Corinthian)
        items.append(_line(cx - ab_w, y_cap_top + ab_h, cx - ab_w, y_cap_top, pen_main))
        items.append(_line(cx + ab_w, y_cap_top + ab_h, cx + ab_w, y_cap_top, pen_main))
        items.append(_line(cx - ab_w, y_cap_top, cx + ab_w, y_cap_top, pen_main))
        items.append(_line(cx - ab_w, y_cap_top + ab_h, cx + ab_w, y_cap_top + ab_h, pen_main))

    # ──── entablature ────
    ent_w = D(1.5)  # entablature extends beyond column
    y_ent = Y(col_h)

    # Architrave
    y_arch_top = y_ent - D(arch_h)
    items.append(_line(cx - ent_w, y_ent, cx + ent_w, y_ent, pen_main))
    items.append(_line(cx - ent_w, y_ent, cx - ent_w, y_arch_top, pen_main))
    items.append(_line(cx + ent_w, y_ent, cx + ent_w, y_arch_top, pen_main))
    items.append(_line(cx - ent_w, y_arch_top, cx + ent_w, y_arch_top, pen_main))

    # Architrave fascia (Ionic/Corinthian/Composite have 3 bands)
    if name in ("ionic", "corinthian", "composite"):
        for frac in (0.33, 0.67):
            fy = y_ent - D(arch_h * frac)
            items.append(_line(cx - ent_w + D(0.02), fy, cx + ent_w - D(0.02), fy, pen_light))

    # Frieze
    y_fri_top = y_arch_top - D(frieze_h)
    items.append(_line(cx - ent_w, y_arch_top, cx - ent_w, y_fri_top, pen_main))
    items.append(_line(cx + ent_w, y_arch_top, cx + ent_w, y_fri_top, pen_main))
    items.append(_line(cx - ent_w, y_fri_top, cx + ent_w, y_fri_top, pen_main))

    # Doric triglyphs (vertical bars in frieze)
    if name == "doric":
        trig_w = D(0.25)
        trig_sp = D(0.75)
        tx = cx - ent_w + D(0.25)
        while tx + trig_w < cx + ent_w:
            items.append(_line(tx, y_arch_top, tx, y_fri_top, pen_light))
            items.append(_line(tx + trig_w, y_arch_top, tx + trig_w, y_fri_top, pen_light))
            # Two channels inside triglyph
            items.append(_line(tx + trig_w * 0.33, y_arch_top - D(0.02),
                               tx + trig_w * 0.33, y_fri_top + D(0.02), pen_light))
            items.append(_line(tx + trig_w * 0.67, y_arch_top - D(0.02),
                               tx + trig_w * 0.67, y_fri_top + D(0.02), pen_light))
            tx += trig_sp

    # Cornice
    y_corn_top = y_fri_top - D(corn_h)
    corn_ext = D(0.2)  # cornice projects beyond frieze
    items.append(_line(cx - ent_w - corn_ext, y_fri_top, cx + ent_w + corn_ext, y_fri_top, pen_main))
    items.append(_line(cx - ent_w - corn_ext, y_fri_top, cx - ent_w - corn_ext, y_corn_top, pen_main))
    items.append(_line(cx + ent_w + corn_ext, y_fri_top, cx + ent_w + corn_ext, y_corn_top, pen_main))
    items.append(_line(cx - ent_w - corn_ext, y_corn_top, cx + ent_w + corn_ext, y_corn_top, pen_main))

    # Dentils (Ionic) or Modillions (Corinthian/Composite)
    if name == "ionic":
        dy = y_fri_top - D(corn_h * 0.3)
        items.append(_line(cx - ent_w, dy, cx + ent_w, dy, pen_light))
        dx = cx - ent_w + D(0.1)
        while dx < cx + ent_w:
            items.append(_line(dx, y_fri_top, dx, dy, pen_light))
            dx += D(0.15)
    elif name in ("corinthian", "composite"):
        my = y_fri_top - D(corn_h * 0.4)
        items.append(_line(cx - ent_w, my, cx + ent_w, my, pen_light))
        mx = cx - ent_w + D(0.2)
        while mx < cx + ent_w:
            items.append(_line(mx, y_fri_top, mx, my, pen_light))
            items.append(_line(mx + D(0.15), y_fri_top, mx + D(0.15), my, pen_light))
            mx += D(0.5)

    # ──── proportional reference lines ────
    ref_x = cx + ent_w + D(0.4)
    for label_d, y_pos in [
        (0, baseline),
        (base_h, Y(base_h)),
        (col_h, Y(col_h)),
        (col_h + ent_h, Y(col_h + ent_h)),
    ]:
        items.append(_line(ref_x - D(0.1), y_pos, ref_x + D(0.1), y_pos, pen_ref))

    return items


def generate_five_orders(canvas_view, spacing_d: float = 5.0) -> None:
    """Draw all 5 Classical Orders side by side on the active vector layer.
    Spacing between column centers = spacing_d diameters."""
    gs = canvas_view.grid_spacing
    baseline = 14 * gs  # 14 grid cells below origin

    total_width = (len(ORDER_SEQUENCE) - 1) * spacing_d
    start_x = -total_width / 2 * gs

    all_items = []
    for i, name in enumerate(ORDER_SEQUENCE):
        cx = start_x + i * spacing_d * gs
        items = draw_order(name, cx, baseline, gs)
        all_items.extend(items)

    if canvas_view.undo_stack:
        canvas_view.undo_stack.beginMacro("Five Orders")
    for item in all_items:
        canvas_view.add_item(item)
    if canvas_view.undo_stack:
        canvas_view.undo_stack.endMacro()
