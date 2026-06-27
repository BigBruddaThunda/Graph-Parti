"""The Archideck portrait cockpit — architect's cockpit template (v3).

Reference frame: 600 × 1400 px (matching the 600×1399 Archideck viewport).
Zone heights (percentage-based, top→bottom):

  Revelator          52 px   3.7%
  Terminal output   250 px  17.9%
  Terminal input+   84 px    6.0%
  Middle Ground     674 px  48.1%   ← left edge: 12 circular operator buttons
  Axis Row           60 px   4.3%   ← 🏛⌛🔨 [plate] 🐬🌹🪐
  Instrument Cluster 280 px 20.0%  ← Zip Dial (left ~2/3) + Z-Pad (right ~1/3)

All borders: copper #D4935A.
Shell background:  sheep's-wool paper #F2EBD8 (tinted by Color dial).
Font: VG5000 (falls back to monospace if not installed).
Shell margin: 6 px between all elements.
Z-pad: UP/DOWN = red #C1140C, LEFT/RIGHT/CENTER = black #3C3C3C.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal, QSize, QPointF, QRectF
from PySide6.QtGui import (
    QColor, QFont, QKeySequence, QPalette, QShortcut,
    QPainter, QPen, QBrush, QPolygonF,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .canon import (
    AXES, AXIS_LEFT, AXIS_RIGHT, COLORS, COPPER, MODIFIERS, OPERATORS, ORDERS,
)

# ── Design tokens ────────────────────────────────────────────────────────────
_COPPER       = "#D4935A"   # all borders
_PAPER        = "#F2EBD8"   # default shell background
_RED          = "#C1140C"   # z-pad UP/DOWN
_BLACK        = "#3C3C3C"   # z-pad LEFT/RIGHT/CENTER
_MARGIN       = 6           # shell gutter (px)

# Heights as percentages of the reference frame (1400 px)
_REF_H        = 1400
_H_REVELATOR  = 52 / _REF_H   # 3.7%
_H_TERM_OUT   = 250 / _REF_H  # 17.9%
_H_TERM_IN    = 84 / _REF_H   # 6.0%
_H_MIDDLE     = 674 / _REF_H  # 48.1%
_H_AXIS       = 60 / _REF_H   # 4.3%
_H_INSTR      = 280 / _REF_H  # 20.0%

_OP_RADIUS    = 12   # operator circle radius (px)

# ── Zip Dial sequences ────────────────────────────────────────────────────────
DIAL_SEQUENCES = {
    "operator": ["📍", "🧲", "🤌", "👀", "🐋", "🧸", "🚀", "🥨", "🦢", "🦉", "🪵", "✒️"],
    "axis":     ["🏛", "⌛", "🔨", "🐬", "🌹", "🪐"],
    "order":    ["🐂", "⛽", "🦋", "🏟", "🌾", "⚖", "🖼"],
    "color":    ["⚪", "🟡", "🟠", "🔴", "⚫", "🟣", "🔵", "🟢"],
}

DIAL_SIDES = {"operator": 12, "axis": 6, "order": 7, "color": 8}

COLOR_HEXES = {
    "⚪": "#F5F5DC", "🟡": "#F7B731", "🟠": "#F57E16", "🔴": "#C1140C",
    "⚫": "#3C3C3C", "🟣": "#9255E5", "🔵": "#2464E5", "🟢": "#348219",
}


def _vg_font(size: int = 10) -> QFont:
    """Return a VG5000 font (monospace fallback if not installed)."""
    f = QFont("VG5000")
    if not f.exactMatch():
        f = QFont("Courier New")
    f.setPointSize(size)
    return f


def _copper_frame(parent=None) -> QFrame:
    """A QFrame with a 1px copper border and paper background."""
    frame = QFrame(parent)
    frame.setFrameShape(QFrame.Shape.NoFrame)
    frame.setStyleSheet(
        f"QFrame {{ border: 1px solid {_COPPER}; "
        f"background: {_PAPER}; border-radius: 3px; }}"
    )
    return frame


# ── Helper widgets ────────────────────────────────────────────────────────────

class _ClickLabel(QLabel):
    """QLabel that emits clicked on left-press."""
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _CircleButton(QAbstractButton):
    """A small filled circle button for the 12-operator rail."""

    def __init__(self, glyph: str, tooltip: str = "", parent=None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self._active = False
        self.setFixedSize(_OP_RADIUS * 2 + 4, _OP_RADIUS * 2 + 4)
        if tooltip:
            self.setToolTip(tooltip)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = _OP_RADIUS
        cx = self.width() // 2
        cy = self.height() // 2
        fill = QColor(_COPPER) if self._active else QColor(_PAPER)
        p.setBrush(QBrush(fill))
        pen = QPen(QColor(_COPPER))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        p.setPen(QPen(QColor(_BLACK) if self._active else QColor(_COPPER)))
        f = _vg_font(7)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._glyph)

    def sizeHint(self) -> QSize:
        return QSize(_OP_RADIUS * 2 + 4, _OP_RADIUS * 2 + 4)


class _DragButton(QToolButton):
    """A cockpit button that is also a drag source."""

    def __init__(self, glyph: str, mime: str, payload: str,
                 tooltip: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setText(glyph)
        self.setAutoRaise(True)
        self._mime = mime
        self._payload = payload
        self._press = None
        if tooltip:
            self.setToolTip(tooltip)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._press is not None
                and (event.position().toPoint() - self._press).manhattanLength() > 8):
            from PySide6.QtGui import QDrag
            from PySide6.QtCore import QMimeData
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData(self._mime, self._payload.encode("utf-8"))
            mime.setText(self._payload)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
            self._press = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._press = None
        super().mouseReleaseEvent(event)


class _ZipPlate(QLabel):
    """The [Archideck] copper nameplate — drag onto canvas to spawn a zip box."""

    def __init__(self, zip_provider, parent=None) -> None:
        super().__init__("Archideck", parent)
        self._zip_provider = zip_provider
        self._press = None
        self.setToolTip("drag onto the canvas → drop a zip box (Esc cancels)")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._press is not None
                and (event.position().toPoint() - self._press).manhattanLength() > 8):
            from PySide6.QtGui import QDrag
            from PySide6.QtCore import QMimeData
            facets = self._zip_provider()
            payload = ",".join((g if g else "_") for g in facets)
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData("application/x-scl-zip", payload.encode("utf-8"))
            mime.setText(payload)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
            self._press = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._press = None
        super().mouseReleaseEvent(event)


# ── Dial Reel ─────────────────────────────────────────────────────────────────

class DialReel(QWidget):
    """One zip dial reel: UP click box / active display / DOWN click box.

    Each reel shows both the glyph and the name of the active entry.
    Spinning re-enables a blanked (toggled-off) dial.
    """

    changed = Signal()

    def __init__(self, entries: list[tuple[str, str]], parent=None) -> None:
        """entries: list of (glyph, name) pairs."""
        super().__init__(parent)
        self.entries = list(entries)
        self.index = 0
        self.enabled = True

        lay = QVBoxLayout(self)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(1)

        # ── UP click box ──────────────────────────────────────────
        self._up_box = QToolButton()
        self._up_box.setText("▲")
        self._up_box.setAutoRaise(True)
        self._up_box.setToolTip("spin up")
        self._up_box.clicked.connect(lambda: self.spin(-1))
        self._up_box.setStyleSheet(
            f"QToolButton {{ border: 1px solid {_COPPER}; "
            f"background: {_PAPER}; font-size: 9px; }}"
        )

        # ── Active display (glyph + name, click to toggle) ───────
        self._active = _ClickLabel()
        self._active.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._active.setWordWrap(True)
        self._active.setToolTip("click to toggle this dial off (partial zip)")
        self._active.clicked.connect(self.toggle)
        self._active.setStyleSheet(
            f"QLabel {{ border: 1px solid {_COPPER}; "
            f"background: {_PAPER}; padding: 2px; }}"
        )

        # ── DOWN click box ─────────────────────────────────────────
        self._dn_box = QToolButton()
        self._dn_box.setText("▼")
        self._dn_box.setAutoRaise(True)
        self._dn_box.setToolTip("spin down")
        self._dn_box.clicked.connect(lambda: self.spin(1))
        self._dn_box.setStyleSheet(
            f"QToolButton {{ border: 1px solid {_COPPER}; "
            f"background: {_PAPER}; font-size: 9px; }}"
        )

        lay.addWidget(self._up_box)
        lay.addWidget(self._active, 1)
        lay.addWidget(self._dn_box)
        self._refresh()

    def spin(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.entries)
        if not self.enabled:
            self.enabled = True
        self._refresh()
        self.changed.emit()

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self._refresh()
        self.changed.emit()

    def _refresh(self) -> None:
        g, name = self.entries[self.index]
        text = f"{g}\n{name}"
        self._active.setText(text)
        if self.enabled:
            self._active.setStyleSheet(
                f"QLabel {{ border: 1px solid {_COPPER}; "
                f"background: {_PAPER}; padding: 2px; color: {_BLACK}; }}"
            )
        else:
            self._active.setStyleSheet(
                f"QLabel {{ border: 1px solid {_COPPER}; "
                f"background: {_PAPER}; padding: 2px; color: rgba(0,0,0,0.22); }}"
            )

    def glyph(self) -> str:
        return self.entries[self.index][0]

    def value(self) -> str | None:
        """The dialed glyph, or None when toggled off."""
        return self.entries[self.index][0] if self.enabled else None


# ── Gem Dial Reel ─────────────────────────────────────────────────────────────

class GemDialReel(QWidget):
    """A single zip dial reel — shows 3 gem faces, spins up/down."""
    value_changed = Signal(str)  # emits the active glyph

    def __init__(self, name: str, sequence: list, sides: int,
                 color_map: dict | None = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._sequence = sequence
        self._sides = sides
        self._color_map = color_map  # only for color reel
        self._index = 0
        self.setMinimumSize(80, 160)
        self.setMaximumWidth(120)

    @property
    def active(self) -> str:
        return self._sequence[self._index]

    @property
    def prev(self) -> str:
        return self._sequence[(self._index - 1) % len(self._sequence)]

    @property
    def nxt(self) -> str:
        return self._sequence[(self._index + 1) % len(self._sequence)]

    def spin_up(self):
        self._index = (self._index - 1) % len(self._sequence)
        self.value_changed.emit(self.active)
        self.update()

    def spin_down(self):
        self._index = (self._index + 1) % len(self._sequence)
        self.value_changed.emit(self.active)
        self.update()

    def set_value(self, glyph: str):
        if glyph in self._sequence:
            self._index = self._sequence.index(glyph)
            self.update()

    def mousePressEvent(self, event):
        h = self.height()
        y = event.position().y()
        if y < h * 0.3:
            self.spin_up()
        elif y > h * 0.7:
            self.spin_down()
        event.accept()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        copper = QColor(_COPPER)
        paper = QColor(_PAPER)

        # Background
        p.fillRect(0, 0, w, h, paper)
        p.setPen(QPen(copper, 2))
        p.drawRect(1, 1, w - 2, h - 2)

        # Dividing lines between faces
        third = h / 3
        p.setPen(QPen(copper, 1.5))
        # Horizontal copper bars between faces
        bar_h = 6
        for y_pos in (third - bar_h / 2, 2 * third - bar_h / 2):
            p.setBrush(QBrush(copper))
            p.drawRect(QRectF(4, y_pos, w - 8, bar_h))
            # Small circles at bar ends (rivets)
            rivet_r = 3
            p.drawEllipse(QPointF(4 + rivet_r, y_pos + bar_h / 2), rivet_r, rivet_r)
            p.drawEllipse(QPointF(w - 4 - rivet_r, y_pos + bar_h / 2), rivet_r, rivet_r)

        # Draw 3 gem faces
        gem_w = w * 0.7
        gem_h = third * 0.65
        cx = w / 2

        # Top face (previous) — clipped to upper half
        self._draw_gem(p, cx, third * 0.45, gem_w * 0.75, gem_h * 0.75,
                       self.prev, clip="top")
        # Middle face (active) — full
        self._draw_gem(p, cx, h / 2, gem_w, gem_h, self.active, clip=None)
        # Bottom face (next) — clipped to lower half
        self._draw_gem(p, cx, h - third * 0.45, gem_w * 0.75, gem_h * 0.75,
                       self.nxt, clip="bottom")

        p.end()

    def _draw_gem(self, painter: QPainter, cx: float, cy: float,
                  w: float, h: float, glyph: str, clip: str | None = None):
        """Draw a faceted gem shape at (cx, cy) with width w and height h."""
        painter.save()

        # Clip region for top/bottom faces
        if clip == "top":
            clip_rect = QRectF(cx - w, cy - h, w * 2, h)
            painter.setClipRect(clip_rect)
        elif clip == "bottom":
            clip_rect = QRectF(cx - w, cy, w * 2, h)
            painter.setClipRect(clip_rect)

        n = self._sides
        rx, ry = w / 2, h / 2
        inner_scale = 0.55

        # Outer polygon
        outer = []
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2  # start from top
            outer.append(QPointF(cx + rx * math.cos(angle),
                                 cy + ry * math.sin(angle)))

        # Inner polygon
        inner = []
        for i in range(n):
            angle = 2 * math.pi * i / n - math.pi / 2
            inner.append(QPointF(cx + rx * inner_scale * math.cos(angle),
                                 cy + ry * inner_scale * math.sin(angle)))

        # Fill
        is_color_reel = self._color_map is not None
        if is_color_reel and glyph in self._color_map:
            fill_color = QColor(self._color_map[glyph])
            painter.setBrush(QBrush(fill_color))
        else:
            painter.setBrush(QBrush(QColor(_PAPER)))

        # Draw outer polygon
        poly = QPolygonF(outer + [outer[0]])
        pen = QPen(QColor(_BLACK), 1.5)
        painter.setPen(pen)
        painter.drawPolygon(poly)

        # Draw inner polygon
        if not is_color_reel:
            inner_poly = QPolygonF(inner + [inner[0]])
            painter.setBrush(QBrush(QColor(_PAPER)))
            painter.drawPolygon(inner_poly)

        # Draw radial facet lines (outer vertex to inner vertex)
        painter.setPen(QPen(QColor(_BLACK), 1.0))
        for i in range(n):
            painter.drawLine(outer[i], inner[i])

        # Draw glyph text in center
        font = painter.font()
        font.setPixelSize(max(12, int(min(w, h) * 0.3)))
        painter.setFont(font)
        painter.setPen(QPen(QColor(_BLACK) if not is_color_reel else QColor("white")))
        text_rect = QRectF(cx - w / 2, cy - h / 4, w, h / 2)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, glyph)

        painter.restore()


# ── Main Panel ────────────────────────────────────────────────────────────────

class ArchideckPanel(QWidget):
    """The portrait cockpit — architect's template v3 (percentage-based layout)."""

    zip_changed = Signal(str, str, str, str)
    terminal_submitted = Signal(str)
    backend_changed = Signal(str, str)  # backend, model

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self._paper_color = QColor(_PAPER)
        self._last_size = (0, 0)

        # Apply initial paper palette
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, self._paper_color)
        self.setPalette(pal)

        # Root layout — no spacing; we use fixed heights controlled in resizeEvent
        root = QVBoxLayout(self)
        root.setContentsMargins(_MARGIN, _MARGIN, _MARGIN, _MARGIN)
        root.setSpacing(_MARGIN)

        # ── Zone 1: Revelator ─────────────────────────────────────
        self._revelator = self._build_revelator()
        root.addWidget(self._revelator)

        # ── Zone 2+3: Terminal (output frame + input frame) ───────
        self._term_out_frame = self._build_terminal_output()
        root.addWidget(self._term_out_frame)

        self._term_in_frame = self._build_terminal_input()
        root.addWidget(self._term_in_frame)

        # ── Zone 4: Middle Ground ─────────────────────────────────
        self._middle_frame = self._build_middle_ground()
        root.addWidget(self._middle_frame, 1)  # gets the stretch

        # ── Zone 5: Axis Row ──────────────────────────────────────
        self._axis_frame = self._build_axis_row()
        root.addWidget(self._axis_frame)

        # ── Zone 6: Instrument Cluster ────────────────────────────
        self._instr_frame = self._build_instruments()
        root.addWidget(self._instr_frame)

        self._refresh_zip()
        self._retint()

    # =========================================================================
    # ZONE 1 — REVELATOR
    # =========================================================================
    def _build_revelator(self) -> QFrame:
        frame = _copper_frame()
        frame.setFixedHeight(52)

        row = QHBoxLayout(frame)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)

        self._zip_glyphs = QLabel("[ _ _ _ _ ]")
        self._zip_glyphs.setFont(_vg_font(11))
        self._zip_glyphs.setStyleSheet(f"color: {_BLACK}; background: transparent;")

        self._tail = QLabel("±")
        self._tail.setFont(_vg_font(10))
        self._tail.setStyleSheet("color: rgba(0,0,0,0.5); background: transparent;")

        self._free = QLineEdit()
        self._free.setPlaceholderText("free-text annotation")
        self._free.setFont(_vg_font(10))
        self._free.setStyleSheet(
            f"QLineEdit {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
            f"color: {_BLACK}; padding: 2px 4px; }}"
        )

        row.addWidget(self._zip_glyphs)
        row.addWidget(self._tail)
        sep = QLabel("│")
        sep.setStyleSheet(f"color: {_COPPER}; background: transparent;")
        row.addWidget(sep)
        row.addWidget(self._free, 1)

        return frame

    # =========================================================================
    # ZONE 2 — TERMINAL OUTPUT
    # =========================================================================
    def _build_terminal_output(self) -> QFrame:
        frame = _copper_frame()
        frame.setFixedHeight(250)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(0)

        self._terminal_output = QPlainTextEdit()
        self._terminal_output.setReadOnly(True)
        self._terminal_output.setPlaceholderText("terminal output")
        self._terminal_output.setFont(_vg_font(9))
        self._terminal_output.setFrameShape(QFrame.Shape.NoFrame)
        self._terminal_output.setStyleSheet(
            f"QPlainTextEdit {{ background: {_PAPER}; color: {_BLACK}; "
            f"border: none; }}"
        )
        lay.addWidget(self._terminal_output)

        return frame

    # =========================================================================
    # ZONE 3 — TERMINAL INPUT + MODEL ROW + MODIFIER BUTTONS
    # =========================================================================
    def _build_terminal_input(self) -> QFrame:
        frame = _copper_frame()
        frame.setFixedHeight(84)

        outer = QHBoxLayout(frame)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        left = QVBoxLayout()
        left.setSpacing(3)

        # model selector row
        model_row = QHBoxLayout()
        model_row.setSpacing(4)

        self._backend_combo = QComboBox()
        self._backend_combo.addItems(["ollama", "lmstudio", "anthropic"])
        self._backend_combo.setToolTip("AI backend")
        self._backend_combo.setFont(_vg_font(9))
        self._backend_combo.setStyleSheet(
            f"QComboBox {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
            f"color: {_BLACK}; padding: 1px 4px; }}"
        )
        self._backend_combo.setFixedHeight(24)
        model_row.addWidget(self._backend_combo)

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setToolTip("model")
        self._model_combo.setFont(_vg_font(9))
        self._model_combo.setStyleSheet(
            f"QComboBox {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
            f"color: {_BLACK}; padding: 1px 4px; }}"
        )
        self._model_combo.setFixedHeight(24)
        model_row.addWidget(self._model_combo, 1)

        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("↻")
        self._refresh_btn.setAutoRaise(True)
        self._refresh_btn.setToolTip("refresh model list")
        self._refresh_btn.setFixedSize(24, 24)
        self._refresh_btn.setStyleSheet(
            f"QToolButton {{ border: 1px solid {_COPPER}; background: {_PAPER}; }}"
        )
        self._refresh_btn.clicked.connect(self._refresh_models)
        model_row.addWidget(self._refresh_btn)

        left.addLayout(model_row)

        # input row
        input_row = QHBoxLayout()
        input_row.setSpacing(3)

        self._terminal_input = QLineEdit()
        self._terminal_input.setPlaceholderText("input")
        self._terminal_input.setFont(_vg_font(10))
        self._terminal_input.setFixedHeight(28)
        self._terminal_input.setStyleSheet(
            f"QLineEdit {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
            f"color: {_BLACK}; padding: 2px 6px; }}"
        )
        input_row.addWidget(self._terminal_input, 1)

        # 5th modifier button on the input row
        btn5_glyph, btn5_name = MODIFIERS[4]
        self._btn5 = QToolButton()
        self._btn5.setText(btn5_glyph)
        self._btn5.setToolTip(btn5_name)
        self._btn5.setAutoRaise(True)
        self._btn5.setFixedSize(28, 28)
        self._btn5.setStyleSheet(
            f"QToolButton {{ border: 1px solid {_COPPER}; background: {_PAPER}; }}"
        )
        input_row.addWidget(self._btn5)
        left.addLayout(input_row)

        outer.addLayout(left, 1)

        # right inner wall: 4 modifier buttons stacked
        right = QVBoxLayout()
        right.setSpacing(2)
        right.setContentsMargins(0, 0, 0, 0)
        _TYPE_NAMES = ["Push", "Pull", "Legs", "Plus", "Ultra"]
        self._terminal_buttons: list[QToolButton] = []
        for idx, (glyph, name) in enumerate(MODIFIERS[:4]):
            b = QToolButton()
            b.setText(glyph)
            b.setToolTip(name)
            b.setAutoRaise(True)
            b.setFixedSize(28, 18)
            b.setStyleSheet(
                f"QToolButton {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
                f"font-size: 10px; }}"
            )
            t = _TYPE_NAMES[idx]
            b.clicked.connect(lambda checked=False, tn=t: self.set_active_type(tn))
            right.addWidget(b)
            self._terminal_buttons.append(b)
        self._terminal_buttons.append(self._btn5)
        self._btn5.clicked.connect(lambda: self.set_active_type("Ultra"))

        outer.addLayout(right)

        self._terminal_input.returnPressed.connect(self._on_terminal_submit)

        return frame

    # =========================================================================
    # ZONE 4 — MIDDLE GROUND (operator circles left + content viewport)
    # =========================================================================
    def _build_middle_ground(self) -> QFrame:
        frame = _copper_frame()
        # height is flexible (stretch factor 1 in root layout)

        lay = QHBoxLayout(frame)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        # ── Left edge: 12 circular operator buttons ───────────────
        op_col = QVBoxLayout()
        op_col.setSpacing(2)
        op_col.setContentsMargins(0, 0, 0, 0)
        op_col.addStretch(1)

        self._op_buttons: list[_CircleButton] = []
        for i, (glyph, name) in enumerate(OPERATORS):
            b = _CircleButton(glyph, tooltip=f"{name}  (F{i + 1})")
            b.clicked.connect(lambda _=False, idx=i: self._select_operator(idx))
            op_col.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._op_buttons.append(b)
            sc = QShortcut(QKeySequence(f"F{i + 1}"), self)
            sc.activated.connect(lambda idx=i: self._select_operator(idx))

        op_col.addStretch(1)
        lay.addLayout(op_col)

        # ── Main content area ─────────────────────────────────────
        mg_inner = QFrame()
        mg_inner.setFrameShape(QFrame.Shape.NoFrame)
        mg_inner.setStyleSheet(
            f"QFrame {{ border: 1px solid {_COPPER}; background: transparent; }}"
        )
        mg_lay = QVBoxLayout(mg_inner)
        mg_lay.setContentsMargins(6, 6, 6, 6)
        from .workout_card import WorkoutCardWidget
        self._middle = WorkoutCardWidget()
        mg_lay.addWidget(self._middle)
        lay.addWidget(mg_inner, 1)

        return frame

    def _select_operator(self, i: int) -> None:
        glyph, name = OPERATORS[i]
        # reload card with current zip when operator changes
        self._load_workout_card()
        for j, b in enumerate(self._op_buttons):
            b.set_active(j == i)

    # =========================================================================
    # ZONE 5 — AXIS ROW
    # =========================================================================
    def _build_axis_row(self) -> QFrame:
        frame = _copper_frame()
        frame.setFixedHeight(60)

        row = QHBoxLayout(frame)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(4)

        btn_style = (
            f"QToolButton {{ border: 1px solid {_COPPER}; background: {_PAPER}; "
            f"color: {_BLACK}; font-size: 16px; border-radius: 3px; padding: 2px; }}"
            f"QToolButton:hover {{ background: {_COPPER}; }}"
        )

        for g in AXIS_LEFT:
            b = QToolButton()
            b.setText(g)
            b.setAutoRaise(True)
            b.setFixedSize(40, 40)
            b.setStyleSheet(btn_style)
            row.addWidget(b)

        row.addStretch(1)

        plate = _ZipPlate(self.current_zip)
        plate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plate.setFont(_vg_font(10))
        plate.setFixedHeight(40)
        plate.setStyleSheet(
            f"QLabel {{ background: {_COPPER}; color: #3A2A1A; font-weight: bold; "
            f"border: 1px solid #8A5A3A; border-radius: 4px; padding: 4px 12px; }}"
        )
        plate.setCursor(Qt.CursorShape.OpenHandCursor)
        row.addWidget(plate)

        row.addStretch(1)

        for g in AXIS_RIGHT:
            b = QToolButton()
            b.setText(g)
            b.setAutoRaise(True)
            b.setFixedSize(40, 40)
            b.setStyleSheet(btn_style)
            row.addWidget(b)

        return frame

    # =========================================================================
    # ZONE 6 — INSTRUMENT CLUSTER (Zip Dial left 2/3 + Z-Pad right 1/3)
    # =========================================================================
    def _build_instruments(self) -> QFrame:
        frame = _copper_frame()
        frame.setFixedHeight(280)

        row = QHBoxLayout(frame)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(6)

        # ── Zip Dial (4 GemDialReel reels) ───────────────────────
        dial_frame = _copper_frame()
        dial_lay = QHBoxLayout(dial_frame)
        dial_lay.setContentsMargins(3, 3, 3, 3)
        dial_lay.setSpacing(3)

        self._dial_op = GemDialReel(
            "operator", DIAL_SEQUENCES["operator"], DIAL_SIDES["operator"]
        )
        self._dial_ax = GemDialReel(
            "axis", DIAL_SEQUENCES["axis"], DIAL_SIDES["axis"]
        )
        self._dial_or = GemDialReel(
            "order", DIAL_SEQUENCES["order"], DIAL_SIDES["order"]
        )
        self._dial_co = GemDialReel(
            "color", DIAL_SEQUENCES["color"], DIAL_SIDES["color"],
            color_map=COLOR_HEXES,
        )
        self._gem_reels = [self._dial_op, self._dial_ax, self._dial_or, self._dial_co]

        # Column headers
        for label_text, reel in zip(
            ["Operator", "Axis", "Order", "Color"], self._gem_reels
        ):
            col = QVBoxLayout()
            col.setSpacing(1)
            lbl = QLabel(label_text)
            lbl.setFont(_vg_font(8))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"QLabel {{ color: {_COPPER}; background: transparent; "
                f"border: none; font-weight: bold; }}"
            )
            col.addWidget(lbl)
            col.addWidget(reel, 1)
            dial_lay.addLayout(col)

        for reel in self._gem_reels:
            reel.value_changed.connect(lambda _: self._refresh_zip())
        self._dial_co.value_changed.connect(lambda _: self._retint())

        row.addWidget(dial_frame, 2)  # ~2/3

        # ── Z-Pad ─────────────────────────────────────────────────
        zpad_frame = _copper_frame()
        grid = QGridLayout(zpad_frame)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(4)

        def _zpad_btn(glyph: str, bg: str, is_drag: bool = False,
                      mime: str = "", payload: str = "",
                      tip: str = "") -> QToolButton:
            if is_drag:
                b = _DragButton(glyph, mime, payload, tooltip=tip)
            else:
                b = QToolButton()
                b.setText(glyph)
                if tip:
                    b.setToolTip(tip)
            b.setAutoRaise(True)
            b.setFont(_vg_font(14))
            b.setStyleSheet(
                f"QToolButton {{ background: {bg}; color: #FFFFFF; "
                f"border: 2px solid {_COPPER}; border-radius: 4px; "
                f"font-size: 16px; padding: 4px; }}"
                f"QToolButton:hover {{ border: 2px solid #FFFFFF; }}"
            )
            b.setMinimumSize(44, 44)
            return b

        # UP (red) — ➕ Plus
        up_btn = _zpad_btn("➕", _RED, is_drag=True,
                           mime="application/x-scl-arrow", payload="up",
                           tip="Plus · click = set type · drag = canvas arrow")
        up_btn.clicked.connect(lambda: self.set_active_type("Plus"))
        grid.addWidget(up_btn, 0, 1)

        # LEFT (black) — 🛒 Push
        left_btn = _zpad_btn("🛒", _BLACK, is_drag=True,
                             mime="application/x-scl-arrow", payload="left",
                             tip="Push · click = set type · drag = canvas arrow")
        left_btn.clicked.connect(lambda: self.set_active_type("Push"))
        grid.addWidget(left_btn, 1, 0)

        # CENTER 🍗 (black) — Legs
        center_btn = _zpad_btn("🍗", _BLACK, is_drag=True,
                               mime="application/x-scl-handback", payload="leg",
                               tip="Legs · click = set type · drag = handback")
        center_btn.clicked.connect(lambda: self.set_active_type("Legs"))
        grid.addWidget(center_btn, 1, 1)

        # RIGHT (black) — 🪡 Pull
        right_btn = _zpad_btn("🪡", _BLACK, is_drag=True,
                              mime="application/x-scl-arrow", payload="right",
                              tip="Pull · click = set type · drag = canvas arrow")
        right_btn.clicked.connect(lambda: self.set_active_type("Pull"))
        grid.addWidget(right_btn, 1, 2)

        # DOWN (red) — ➖ Ultra
        down_btn = _zpad_btn("➖", _RED, is_drag=True,
                             mime="application/x-scl-arrow", payload="down",
                             tip="Ultra · click = set type · drag = canvas arrow")
        down_btn.clicked.connect(lambda: self.set_active_type("Ultra"))
        grid.addWidget(down_btn, 2, 1)

        # Stretch remaining columns/rows evenly
        for i in range(3):
            grid.setColumnStretch(i, 1)
        for i in range(3):
            grid.setRowStretch(i, 1)

        row.addWidget(zpad_frame, 1)  # ~1/3

        return frame

    # =========================================================================
    # ZIP ADDRESS — update revelator from dials
    # =========================================================================
    def _refresh_zip(self) -> None:
        glyphs = " ".join(r.active for r in self._gem_reels)
        self._zip_glyphs.setText(f"[ {glyphs} ]")
        op, ax, orr, col = (r.active for r in self._gem_reels)
        self.zip_changed.emit(op, ax, orr, col)
        self._load_workout_card()
        se = getattr(self, '_sound_engine', None)
        if se is not None:
            prev = getattr(self, '_prev_zip', ("", "", "", ""))
            names = ("operator", "axis", "order", "color")
            cur = (op, ax, orr, col)
            for name, old, new in zip(names, prev, cur):
                if new and new != old:
                    se.on_dial_spin(name, new)
            self._prev_zip = cur

    def current_zip(self) -> tuple:
        return tuple(r.active for r in self._gem_reels)

    # =========================================================================
    # WORKOUT CARD — load from DB on zip/type change
    # =========================================================================
    _active_type: str = "Push"

    def _load_workout_card(self) -> None:
        op, ax, orr, col = (r.active for r in self._gem_reels)
        if not all((op, ax, orr, col)):
            return
        self._middle.set_workout_from_db(op, ax, orr, col, self._active_type)

    def set_active_type(self, type_name: str) -> None:
        self._active_type = type_name
        self._load_workout_card()

    def show_parsed_exercise(self, parsed: dict) -> None:
        self._middle.set_exercise(parsed)

    # =========================================================================
    # COLOR SHELL TINT — color dial → panel background
    # =========================================================================
    def _retint(self) -> None:
        """Blend the active color dial's hue into the sheep's-wool paper base."""
        glyph = self._dial_co.active
        hex_col = COLOR_HEXES.get(glyph, _PAPER)
        tint = QColor(hex_col)
        paper = QColor(_PAPER)

        # Gentle blend: 85% paper + 15% color dial hue (luminosity-safe)
        r = int(paper.red()   * 0.85 + tint.red()   * 0.15)
        g = int(paper.green() * 0.85 + tint.green() * 0.15)
        b = int(paper.blue()  * 0.85 + tint.blue()  * 0.15)
        blended = QColor(r, g, b)

        lum = (0.299 * blended.red() + 0.587 * blended.green()
               + 0.114 * blended.blue()) / 255.0
        text_color = QColor("#1a1a1a") if lum > 0.55 else QColor("#f5f5f5")

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, blended)
        pal.setColor(QPalette.ColorRole.WindowText, text_color)
        self.setPalette(pal)
        self._paper_color = blended

    # =========================================================================
    # TERMINAL HELPERS
    # =========================================================================
    def _on_terminal_submit(self) -> None:
        text = self._terminal_input.text().strip()
        if text:
            self.terminal_submitted.emit(text)
            self._terminal_input.clear()

    def append_terminal(self, text: str, prefix: str = "") -> None:
        line = f"{prefix} {text}" if prefix else text
        self._terminal_output.appendPlainText(line)

    def receive_handback(self, summary: str) -> None:
        self._handbacks = getattr(self, "_handbacks", [])
        self._handbacks.append(summary)
        if hasattr(self, "_terminal_output"):
            self._terminal_output.appendPlainText(f"🍗 handback ← {summary}")

    # =========================================================================
    # MODEL SELECTOR
    # =========================================================================
    def _refresh_models(self) -> None:
        from .conductor import discover_models
        backend = self._backend_combo.currentText()
        models = discover_models(backend)
        self._model_combo.clear()
        if models:
            self._model_combo.addItems(models)
        else:
            self._model_combo.addItem(f"(no models — is {backend} running?)")

    def current_backend(self) -> str:
        return self._backend_combo.currentText()

    def current_model(self) -> str:
        return self._model_combo.currentText()

    def set_models(self, models: list[str]) -> None:
        self._model_combo.clear()
        self._model_combo.addItems(models)
