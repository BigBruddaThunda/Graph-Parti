"""The Archideck portrait cockpit panel — base shape. GRAPH PARTI step 6.

A vertical command cockpit: zip field · middle ground + 12-operator rail · axis row
with the copper [Archideck] plate · the working 4-dial zip dial · Z-pad. The active
color in the color dial tints the whole shell. Wiring (operator tools, tail logic,
lasso, canvas-swap) is deferred — this is the base shape with a working dial.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .canon import AXES, AXIS_LEFT, AXIS_RIGHT, COLORS, COPPER, OPERATORS, ORDERS


class DialReel(QWidget):
    """One zip dial: a vertical reel showing prev / ACTIVE / next, spun by ▲/▼."""

    changed = Signal()

    def __init__(self, caption: str, glyphs: list[str], parent=None) -> None:
        super().__init__(parent)
        self.glyphs = list(glyphs)
        self.index = 0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(1)

        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cf = cap.font(); cf.setPointSize(8); cap.setFont(cf)

        up = QToolButton(); up.setText("▲"); up.setAutoRaise(True)
        up.clicked.connect(lambda: self.spin(-1))
        dn = QToolButton(); dn.setText("▼"); dn.setAutoRaise(True)
        dn.clicked.connect(lambda: self.spin(1))

        self._prev = QLabel(); self._prev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._prev.setStyleSheet("color: rgba(0,0,0,0.30);")
        self._active = QLabel(); self._active.setAlignment(Qt.AlignmentFlag.AlignCenter)
        af = self._active.font(); af.setPointSize(22); self._active.setFont(af)
        self._next = QLabel(); self._next.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next.setStyleSheet("color: rgba(0,0,0,0.30);")

        for wdg in (cap, up, self._prev, self._active, self._next, dn):
            lay.addWidget(wdg, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._refresh()

    def spin(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.glyphs)
        self._refresh()
        self.changed.emit()

    def _refresh(self) -> None:
        n = len(self.glyphs)
        self._prev.setText(self.glyphs[(self.index - 1) % n])
        self._active.setText(self.glyphs[self.index])
        self._next.setText(self.glyphs[(self.index + 1) % n])

    def glyph(self) -> str:
        return self.glyphs[self.index]


class ArchideckPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._build_zip_field(root)
        self._build_middle(root)
        self._build_axis_row(root)
        self._build_dials(root)
        self._build_zpad(root)

        self._refresh_zip()
        self._retint()

    # ------------------------------------------------------------- zip field
    def _build_zip_field(self, root: QVBoxLayout) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        row = QHBoxLayout(frame)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)
        self._zip_glyphs = QLabel("[ _ _ _ _ ]")
        zf = self._zip_glyphs.font(); zf.setPointSize(15); self._zip_glyphs.setFont(zf)
        self._tail = QLabel("[ _ ]")
        self._free = QLineEdit(); self._free.setPlaceholderText("free-text")
        row.addWidget(self._zip_glyphs)
        row.addWidget(QLabel("±"))
        row.addWidget(self._tail)
        row.addWidget(QLabel("|"))
        row.addWidget(self._free, 1)
        root.addWidget(frame)

    # ----------------------------------------------------- middle + operators
    def _build_middle(self, root: QVBoxLayout) -> None:
        mid = QHBoxLayout()
        mid.setSpacing(6)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        fl = QVBoxLayout(frame)
        self._middle = QLabel("middle ground\n\nclick an Operator  ·  F1–F12")
        self._middle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._middle.setWordWrap(True)
        fl.addWidget(self._middle)
        mid.addWidget(frame, 1)

        rail = QVBoxLayout()
        rail.setSpacing(2)
        self._op_buttons: list[QToolButton] = []
        for i, (glyph, name) in enumerate(OPERATORS):
            b = QToolButton()
            b.setText(glyph)
            b.setToolTip(f"{name}  (F{i + 1})")
            b.setAutoRaise(True)
            b.clicked.connect(lambda _checked=False, idx=i: self._select_operator(idx))
            rail.addWidget(b)
            self._op_buttons.append(b)
            sc = QShortcut(QKeySequence(f"F{i + 1}"), self)
            sc.activated.connect(lambda idx=i: self._select_operator(idx))
        mid.addLayout(rail)
        root.addLayout(mid, 1)

    def _select_operator(self, i: int) -> None:
        glyph, name = OPERATORS[i]
        self._middle.setText(f"{glyph}  {name}\n\noperator tools appear here\n(wiring later)")
        for j, b in enumerate(self._op_buttons):
            f = b.font(); f.setBold(j == i); b.setFont(f)

    # ------------------------------------------------------------- axis row
    def _build_axis_row(self, root: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(4)
        for g in AXIS_LEFT:
            b = QToolButton(); b.setText(g); b.setAutoRaise(True); row.addWidget(b)
        plate = QLabel("Archideck")
        plate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plate.setStyleSheet(
            f"background:{COPPER}; color:#3A2A1A; font-weight:bold;"
            " border:1px solid #8A5A3A; border-radius:4px; padding:4px 10px;"
        )
        row.addWidget(plate)
        for g in AXIS_RIGHT:
            b = QToolButton(); b.setText(g); b.setAutoRaise(True); row.addWidget(b)
        root.addLayout(row)

    # ---------------------------------------------------------------- dials
    def _build_dials(self, root: QVBoxLayout) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        row = QHBoxLayout(frame)
        row.setSpacing(8)
        self._dial_op = DialReel("op", [g for g, _ in OPERATORS])
        self._dial_ax = DialReel("axis", [g for g, _ in AXES])
        self._dial_or = DialReel("order", [g for g, _ in ORDERS])
        self._dial_co = DialReel("color", [g for g, _, _ in COLORS])
        self._dials = [self._dial_op, self._dial_ax, self._dial_or, self._dial_co]
        for d in self._dials:
            d.changed.connect(self._refresh_zip)
            row.addWidget(d)
        self._dial_co.changed.connect(self._retint)
        root.addWidget(frame)

    def _refresh_zip(self) -> None:
        glyphs = " ".join(d.glyph() for d in self._dials)
        self._zip_glyphs.setText(f"[ {glyphs} ]")

    # ----------------------------------------------------------------- z-pad
    def _build_zpad(self, root: QVBoxLayout) -> None:
        grid = QGridLayout()
        grid.setSpacing(2)
        # the 5 Modifiers: ➕ up · ➖ down · 🛒 left · 🪡 right · 🍗 center
        for (r, c), g in {(0, 1): "➕", (1, 0): "🛒", (1, 1): "🍗", (1, 2): "🪡", (2, 1): "➖"}.items():
            b = QToolButton(); b.setText(g); b.setAutoRaise(True)
            grid.addWidget(b, r, c)
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addLayout(grid)
        wrap.addStretch(1)
        root.addLayout(wrap)

    # ------------------------------------------------------- color shell tint
    def _retint(self) -> None:
        col = QColor(COLORS[self._dial_co.index][2])
        lum = (0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue()) / 255.0
        text = QColor("#1a1a1a") if lum > 0.55 else QColor("#f5f5f5")
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, col)
        pal.setColor(QPalette.ColorRole.WindowText, text)
        self.setPalette(pal)
