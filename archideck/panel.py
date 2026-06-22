"""The Archideck portrait cockpit — Layout v2 (three vertical thirds).

Three windows floating inside the color shell (shell visible between them):
  Upper:  revelator (thin single-line zip strip, toolbar-height)
          terminal  (output + input + 5 modifier buttons on right inner wall)
  Middle: parallel slider (left, stub) · middle ground · 12-operator rail (right)
  Lower:  axis row (🏛 ⌛ 🔨 [Archideck] 🐬 🌹 🪐)
          instruments: compact zip dial (left ~2/3) + z-pad (right)

Terminal ↔ middle-ground boundary is a draggable QSplitter.
Color dial tints the entire shell. Working zip display in the revelator.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSlider,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .canon import (
    AXES, AXIS_LEFT, AXIS_RIGHT, COLORS, COPPER, MODIFIERS, OPERATORS, ORDERS,
)

# ── Viewport scaling law ──
# Reference frame: 600 × 1399 px (3:7). Every size = percentage of container.
# Non-uniform fill: width and height scale independently.
_REF_W, _REF_H = 600, 1399

_PCT_MARGIN_W = 1.0       # 6/600
_PCT_MARGIN_H = 0.43      # 6/1399
_PCT_REVELATOR = 2.0      # 28/1399
_PCT_COMBO = 1.57         # 22/1399
_PCT_AXIS = 2.6           # 36/1399
_PCT_INSTRUMENTS = 11.4   # 160/1399
_FONT_BASE = 0.0072       # ~10px at 1399
_FONT_DIAL = 0.0136       # ~19px at 1399
_FONT_ZIP = 0.0072        # revelator text


def _pct(dim: int, pct: float) -> int:
    return max(1, int(dim * pct / 100))


class _ClickLabel(QLabel):
    """A QLabel that emits clicked on left-press (for the dial on/off toggle)."""
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _DragButton(QToolButton):
    """A cockpit button that is also a drag source emitting (mime, payload).
    One seam for every spawn gesture: z-pad arrows, the 🍗 leg/handback, etc.
    Left-click still works as a normal button — only a drag fires the payload."""

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
    """The [Archideck] copper plate — drag it onto the canvas to spawn a zip box
    at the current dial coordinate. Right-click / Esc during the drag cancels."""

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


class DialReel(QWidget):
    """One zip dial reel: prev / ACTIVE / next, spun by ▲/▼.
    Click the ACTIVE glyph to toggle the dial off (blank) → partial zip."""

    changed = Signal()

    def __init__(self, glyphs: list[str], compact: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.glyphs = list(glyphs)
        self.index = 0
        self.enabled = True

        lay = QVBoxLayout(self)
        m = 1 if compact else 2
        lay.setContentsMargins(m, m, m, m)
        lay.setSpacing(0 if compact else 1)

        up = QToolButton()
        up.setText("▲")
        up.setAutoRaise(True)
        up.clicked.connect(lambda: self.spin(-1))

        dn = QToolButton()
        dn.setText("▼")
        dn.setAutoRaise(True)
        dn.clicked.connect(lambda: self.spin(1))

        self._prev = QLabel()
        self._prev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._prev.setStyleSheet("color: rgba(0,0,0,0.30);")

        self._active = _ClickLabel()
        self._active.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._active.setToolTip("click to toggle this dial off (partial zip)")
        self._active.clicked.connect(self.toggle)

        self._next = QLabel()
        self._next.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next.setStyleSheet("color: rgba(0,0,0,0.30);")

        for wdg in (up, self._prev, self._active, self._next, dn):
            lay.addWidget(wdg, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._refresh()

    def spin(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.glyphs)
        if not self.enabled:        # spinning re-enables a blanked dial
            self.enabled = True
        self._refresh()
        self.changed.emit()

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self._refresh()
        self.changed.emit()

    def _refresh(self) -> None:
        n = len(self.glyphs)
        self._prev.setText(self.glyphs[(self.index - 1) % n])
        self._active.setText(self.glyphs[self.index])
        self._next.setText(self.glyphs[(self.index + 1) % n])
        self._active.setStyleSheet(
            "" if self.enabled else "color: rgba(0,0,0,0.22);")

    def glyph(self) -> str:
        return self.glyphs[self.index]

    def value(self) -> str | None:
        """The dialed glyph, or None when the dial is toggled off (blank)."""
        return self.glyphs[self.index] if self.enabled else None


class ArchideckPanel(QWidget):
    """The portrait cockpit — three-thirds layout v2."""

    # Active zip (operator, axis, order, color) glyphs — the host wires this to
    # the canvas so drawings file at the dialed district.
    zip_changed = Signal(str, str, str, str)
    terminal_submitted = Signal(str)
    backend_changed = Signal(str, str)  # backend, model

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self._last_size = (0, 0)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ── Upper: Revelator ─────────────────────────────────────
        self._build_revelator(root)

        # ── Splitter: Terminal (top) ↔ Middle zone (bottom) ──────
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._build_terminal(self._splitter)
        self._build_middle_zone(self._splitter)
        self._splitter.setStretchFactor(0, 0)   # terminal keeps its height
        self._splitter.setStretchFactor(1, 1)   # middle ground gets extra
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        root.addWidget(self._splitter, 1)

        # ── Lower: Axis row + Instruments ────────────────────────
        self._build_axis_row(root)
        self._build_instruments(root)

        self._refresh_zip()
        self._retint()

    # ============================================================
    # REVELATOR — thin single-line zip strip (toolbar-height)
    # ============================================================
    def _build_revelator(self, root: QVBoxLayout) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._revelator_frame = frame

        row = QHBoxLayout(frame)
        row.setContentsMargins(6, 0, 6, 0)
        row.setSpacing(4)

        self._zip_glyphs = QLabel("[ _ _ _ _ ]")
        self._tail = QLabel("± [ _ ]")
        self._free = QLineEdit()
        self._free.setPlaceholderText("free-text")

        row.addWidget(self._zip_glyphs)
        row.addWidget(self._tail)
        sep = QLabel("|")
        sf = sep.font()
        sf.setPointSize(10)
        sep.setFont(sf)
        row.addWidget(sep)
        row.addWidget(self._free, 1)

        root.addWidget(frame)

    # ============================================================
    # TERMINAL — output + input + 5 buttons on right inner wall
    # ============================================================
    def _build_terminal(self, splitter: QSplitter) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)

        outer = QHBoxLayout(frame)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # ── left: output + break + input ──
        left = QVBoxLayout()
        left.setSpacing(2)

        self._terminal_output = QPlainTextEdit()
        self._terminal_output.setReadOnly(True)
        self._terminal_output.setPlaceholderText("terminal output")
        self._terminal_output.setFrameShape(QFrame.Shape.NoFrame)
        left.addWidget(self._terminal_output, 1)

        # thin break
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setFixedHeight(1)
        left.addWidget(sep)

        # model selector row
        model_row = QHBoxLayout()
        model_row.setSpacing(4)
        self._backend_combo = QComboBox()
        self._backend_combo.addItems(["ollama", "lmstudio", "anthropic"])
        self._backend_combo.setToolTip("AI backend")
        model_row.addWidget(self._backend_combo)
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setToolTip("model")
        model_row.addWidget(self._model_combo, 1)
        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("↻")
        self._refresh_btn.setAutoRaise(True)
        self._refresh_btn.setToolTip("refresh model list")
        self._refresh_btn.clicked.connect(self._refresh_models)
        model_row.addWidget(self._refresh_btn)
        left.addLayout(model_row)

        # input row — single line + the 5th modifier button
        input_row = QHBoxLayout()
        input_row.setSpacing(2)
        self._terminal_input = QLineEdit()
        self._terminal_input.setPlaceholderText("input")
        input_row.addWidget(self._terminal_input, 1)

        # 5th modifier button (➖ Ultra) — sits on the input row
        btn5_glyph, btn5_name = MODIFIERS[4]
        btn5 = QToolButton()
        btn5.setText(btn5_glyph)
        btn5.setToolTip(btn5_name)
        btn5.setAutoRaise(True)
        input_row.addWidget(btn5)

        left.addLayout(input_row)
        outer.addLayout(left, 1)

        # ── right inner wall: 4 buttons stacked (the 5th is on the input row) ──
        right = QVBoxLayout()
        right.setSpacing(2)
        right.addStretch(1)  # push buttons toward the bottom
        self._terminal_buttons: list[QToolButton] = []
        for glyph, name in MODIFIERS[:4]:
            b = QToolButton()
            b.setText(glyph)
            b.setToolTip(name)
            b.setAutoRaise(True)
            right.addWidget(b)
            self._terminal_buttons.append(b)
        self._terminal_buttons.append(btn5)
        outer.addLayout(right)

        self._terminal_input.returnPressed.connect(self._on_terminal_submit)

        splitter.addWidget(frame)

    # ============================================================
    # MIDDLE ZONE — slider · middle ground · 12-operator rail
    # ============================================================
    def _build_middle_zone(self, splitter: QSplitter) -> None:
        zone = QWidget()
        lay = QHBoxLayout(zone)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        # parallel slider (left, stubbed — wiring deferred)
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._slider.setRange(0, 100)
        self._slider.setValue(50)
        self._slider.setToolTip("parallel slider (stub)")
        lay.addWidget(self._slider)

        # middle ground (center)
        mg_frame = QFrame()
        mg_frame.setFrameShape(QFrame.Shape.StyledPanel)
        mg_lay = QVBoxLayout(mg_frame)
        self._middle = QLabel("middle ground\n\nclick an Operator  ·  F1–F12")
        self._middle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._middle.setWordWrap(True)
        mg_lay.addWidget(self._middle)
        lay.addWidget(mg_frame, 1)

        # 12-operator rail (right)
        rail = QVBoxLayout()
        rail.setSpacing(2)
        self._op_buttons: list[QToolButton] = []
        for i, (glyph, name) in enumerate(OPERATORS):
            b = QToolButton()
            b.setText(glyph)
            b.setToolTip(f"{name}  (F{i + 1})")
            b.setAutoRaise(True)
            b.clicked.connect(
                lambda _checked=False, idx=i: self._select_operator(idx)
            )
            rail.addWidget(b)
            self._op_buttons.append(b)
            sc = QShortcut(QKeySequence(f"F{i + 1}"), self)
            sc.activated.connect(lambda idx=i: self._select_operator(idx))
        lay.addLayout(rail)

        splitter.addWidget(zone)

    def _select_operator(self, i: int) -> None:
        glyph, name = OPERATORS[i]
        self._middle.setText(
            f"{glyph}  {name}\n\noperator tools appear here\n(wiring later)"
        )
        for j, b in enumerate(self._op_buttons):
            f = b.font()
            f.setBold(j == i)
            b.setFont(f)

    # ============================================================
    # AXIS ROW — 🏛 ⌛ 🔨 [Archideck] 🐬 🌹 🪐
    # ============================================================
    def _build_axis_row(self, root: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(4)
        for g in AXIS_LEFT:
            b = QToolButton()
            b.setText(g)
            b.setAutoRaise(True)
            row.addWidget(b)
        plate = _ZipPlate(self.current_zip)
        plate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plate.setStyleSheet(
            f"background:{COPPER}; color:#3A2A1A; font-weight:bold;"
            " border:1px solid #8A5A3A; border-radius:4px; padding:4px 10px;"
        )
        plate.setCursor(Qt.CursorShape.OpenHandCursor)
        row.addWidget(plate)
        for g in AXIS_RIGHT:
            b = QToolButton()
            b.setText(g)
            b.setAutoRaise(True)
            row.addWidget(b)
        root.addLayout(row)

    # ============================================================
    # INSTRUMENTS — compact zip dial (left ~2/3) + z-pad (right)
    # ============================================================
    def _build_instruments(self, root: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(6)

        # ── compact zip dial (4 reels × prev/active/next) ──
        dial_frame = QFrame()
        dial_frame.setFrameShape(QFrame.Shape.StyledPanel)
        dial_lay = QHBoxLayout(dial_frame)
        dial_lay.setContentsMargins(2, 2, 2, 2)
        dial_lay.setSpacing(2)

        self._dial_op = DialReel([g for g, _ in OPERATORS], compact=True)
        self._dial_ax = DialReel([g for g, _ in AXES], compact=True)
        self._dial_or = DialReel([g for g, _ in ORDERS], compact=True)
        self._dial_co = DialReel([g for g, _, _ in COLORS], compact=True)
        self._dials = [self._dial_op, self._dial_ax, self._dial_or, self._dial_co]

        for d in self._dials:
            d.changed.connect(self._refresh_zip)
            dial_lay.addWidget(d)
        self._dial_co.changed.connect(self._retint)

        row.addWidget(dial_frame, 2)  # ~2/3 width

        # ── z-pad (5 buttons, d-pad layout) ──
        zpad_frame = QFrame()
        zpad_frame.setFrameShape(QFrame.Shape.StyledPanel)
        grid = QGridLayout(zpad_frame)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(2)
        pad_map = {
            (0, 1): "➕", (1, 0): "🛒", (1, 1): "🍗", (1, 2): "🪡", (2, 1): "➖",
        }
        # up/down/left/right = draggable flow arrows; center 🍗 = the leg/handback
        dir_map = {(0, 1): "up", (2, 1): "down", (1, 0): "left", (1, 2): "right"}
        for (r, c), g in pad_map.items():
            direction = dir_map.get((r, c))
            if direction:
                b = _DragButton(g, "application/x-scl-arrow", direction,
                                f"drag onto the canvas → {direction} arrow "
                                "(flow / order / direction)")
            elif (r, c) == (1, 1):  # center 🍗 — leg it back to the Archideck
                b = _DragButton(g, "application/x-scl-handback", "leg",
                                "drag onto a district → hand it back to the "
                                "Archideck (system saves + flags for the round table)")
            else:
                b = QToolButton()
                b.setText(g)
                b.setAutoRaise(True)
            grid.addWidget(b, r, c)

        row.addWidget(zpad_frame, 1)  # ~1/3 width

        root.addLayout(row)

    # ============================================================
    # VIEWPORT SCALING — percentage-based resize (600×1399 ref)
    # ============================================================
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if (w, h) == self._last_size:
            return
        self._last_size = (w, h)
        self._apply_sizes(w, h)

    def _apply_sizes(self, w: int, h: int) -> None:
        m_w = _pct(w, _PCT_MARGIN_W)
        m_h = _pct(h, _PCT_MARGIN_H)
        self.layout().setContentsMargins(m_w, m_h, m_w, m_h)
        self.layout().setSpacing(m_h)

        rev_h = _pct(h, _PCT_REVELATOR)
        self._revelator_frame.setFixedHeight(rev_h)
        self._free.setFixedHeight(max(16, rev_h - 6))

        c_h = _pct(h, _PCT_COMBO)
        self._backend_combo.setFixedHeight(c_h)
        self._model_combo.setFixedHeight(c_h)
        self._refresh_btn.setFixedSize(c_h, c_h)

        base_px = max(8, int(h * _FONT_BASE))
        dial_px = max(10, int(h * _FONT_DIAL))

        for lbl in (self._zip_glyphs, self._tail, self._free):
            f = lbl.font()
            f.setPixelSize(base_px)
            lbl.setFont(f)

        for d in self._dials:
            f = d._active.font()
            f.setPixelSize(dial_px)
            d._active.setFont(f)
            prev_px = max(6, int(dial_px * 0.6))
            for lbl in (d._prev, d._next):
                f2 = lbl.font()
                f2.setPixelSize(prev_px)
                lbl.setFont(f2)

    # ============================================================
    # ZIP DISPLAY — updates the revelator from the dials
    # ============================================================
    def _refresh_zip(self) -> None:
        glyphs = " ".join((d.value() or "_") for d in self._dials)
        self._zip_glyphs.setText(f"[ {glyphs} ]")
        op, ax, orr, col = ((d.value() or "") for d in self._dials)
        self.zip_changed.emit(op, ax, orr, col)

    def current_zip(self) -> tuple:
        return tuple(d.value() for d in self._dials)

    # ============================================================
    # HANDBACK — a 🍗 legged in from the canvas (district → Archideck)
    # ============================================================
    def receive_handback(self, summary: str) -> None:
        """A district was legged back to the Archideck. Log it to the terminal —
        the seam the future round table reads for wiring / upkeep / tasks."""
        self._handbacks = getattr(self, "_handbacks", [])
        self._handbacks.append(summary)
        if hasattr(self, "_terminal_output"):
            self._terminal_output.appendPlainText(f"🍗 handback ← {summary}")

    def _on_terminal_submit(self) -> None:
        text = self._terminal_input.text().strip()
        if text:
            self.terminal_submitted.emit(text)
            self._terminal_input.clear()

    def append_terminal(self, text: str, prefix: str = "") -> None:
        line = f"{prefix} {text}" if prefix else text
        self._terminal_output.appendPlainText(line)

    # ============================================================
    # MODEL SELECTOR — backend + model combos
    # ============================================================
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

    # ============================================================
    # COLOR SHELL TINT — color dial → whole panel background
    # ============================================================
    def _retint(self) -> None:
        col = QColor(COLORS[self._dial_co.index][2])
        lum = (0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue()) / 255.0
        text = QColor("#1a1a1a") if lum > 0.55 else QColor("#f5f5f5")
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, col)
        pal.setColor(QPalette.ColorRole.WindowText, text)
        self.setPalette(pal)
