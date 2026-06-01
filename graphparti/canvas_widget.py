"""Embeddable canvas: the whole GRAPH PARTI drawing surface as one QWidget.

This is the isolation boundary. Both the standalone app and the Archideck cockpit
EMBED this widget; `graphparti` never imports anything from the cockpit side, so the
canvas can never inherit cockpit churn.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QUndoStack
from PySide6.QtWidgets import (
    QColorDialog, QGraphicsScene, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from .canvas_view import CanvasView
from .document import Document
from .tools import (
    CircleTool, LineTool, PaintTool, PolylineTool, RectTool, SelectTool, TrimTool,
)

_SCENE_HALF = 100_000
_PAPER = QRectF(-1000, -800, 2000, 1600)

# Default 16 palette colors (row 1 = bold, row 2 = accent/light)
_PALETTE = [
    "#C1140C", "#F57E16", "#F7B731", "#348219",
    "#2464E5", "#9255E5", "#3C3C3C", "#FFFFFF",
    "#E08080", "#F5C2AF", "#FCE4A8", "#7FBF7F",
    "#80B0F0", "#C4A8F0", "#808080", "#F5F5DC",
]

# Line stroke colors (row 1 = structure/primary, row 2 = accent/dark)
_LINE_PALETTE = [
    "#3C3C3C", "#1A1A1A", "#666666", "#999999",
    "#C1140C", "#2464E5", "#348219", "#9255E5",
    "#F57E16", "#F7B731", "#00AAAA", "#FF69B4",
    "#8B4513", "#006400", "#191970", "#800080",
]


class SwatchButton(QToolButton):
    """One color swatch: left-click = select, right-click = open picker."""
    right_clicked = Signal()

    def __init__(self, color: QColor, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(18, 18)
        self.set_color(color)

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)
        self.setStyleSheet(
            f"QToolButton {{ background:{color.name()}; border:1px solid #888; }}"
            f"QToolButton:checked {{ border:2px solid #000; }}"
        )

    def color(self) -> QColor:
        return QColor(self._color)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class ColorPalette(QWidget):
    """16-swatch palette (2 rows × 8). Left-click = select, right-click = pick."""
    color_selected = Signal(QColor)

    def __init__(self, colors: list[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        palette = colors or _PALETTE
        grid = QGridLayout(self)
        grid.setSpacing(2)
        grid.setContentsMargins(2, 2, 2, 2)

        self._buttons: list[SwatchButton] = []
        self._active = 0

        for i, hex_c in enumerate(palette):
            btn = SwatchButton(QColor(hex_c))
            idx = i
            btn.clicked.connect(lambda _ch=False, ii=idx: self._select(ii))
            btn.right_clicked.connect(lambda ii=idx: self._pick(ii))
            grid.addWidget(btn, i // 8, i % 8)
            self._buttons.append(btn)
        self._update()

    def _select(self, idx: int) -> None:
        self._active = idx
        self._update()
        self.color_selected.emit(self._buttons[idx].color())

    def _pick(self, idx: int) -> None:
        cur = self._buttons[idx].color()
        c = QColorDialog.getColor(cur, self, "Choose Color")
        if c.isValid():
            self._buttons[idx].set_color(c)
            if idx == self._active:
                self.color_selected.emit(c)

    def _update(self) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == self._active)

    def active_color(self) -> QColor:
        return self._buttons[self._active].color()


class LayerButton(QToolButton):
    right_clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class CanvasWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(
            QRectF(-_SCENE_HALF, -_SCENE_HALF, 2 * _SCENE_HALF, 2 * _SCENE_HALF)
        )
        self.view = CanvasView(self.scene, grid_spacing=20, major_every=7)
        self.document = Document.default(self.scene, _PAPER)
        self.view.document = self.document
        self.undo_stack = QUndoStack(self)
        self.view.undo_stack = self.undo_stack

        self._tools = {
            "select": SelectTool(self.view),
            "line": LineTool(self.view),
            "polyline": PolylineTool(self.view),
            "rect": RectTool(self.view),
            "circle": CircleTool(self.view),
            "trim": TrimTool(self.view),
            "paint": PaintTool(self.view),
        }

        self.toolbar = self._build_toolbar()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.view, 1)

        # ── Status bar ──
        status_bar = QWidget()
        status_lay = QHBoxLayout(status_bar)
        status_lay.setContentsMargins(8, 2, 8, 2)
        status_lay.setSpacing(8)

        self._status = QLabel("GRAPH PARTI")
        status_lay.addWidget(self._status)
        status_lay.addStretch(1)
        self._scale_label = QLabel("1:1")
        status_lay.addWidget(self._scale_label)

        self._layer_mode = "trace"
        self._layer_modes = ["parti", "both", "trace"]
        self._layer_buttons: list[LayerButton] = []
        for mode in self._layer_modes:
            btn = LayerButton()
            btn.setAutoRaise(True)
            m = mode
            btn.clicked.connect(lambda _ch=False, mm=m: self._set_layer_mode(mm))
            if mode in ("parti", "trace"):
                btn.right_clicked.connect(
                    lambda mm=m: self._toggle_layer_visibility_by_name(mm)
                )
            status_lay.addWidget(btn)
            self._layer_buttons.append(btn)

        layout.addWidget(status_bar)

        # ── Signals + init ──
        self._last_coord = "X 0  Y 0"
        self._last_kind = "SNAP"
        self._last_zoom = "100%"
        self.view.cursor_moved.connect(self._on_cursor)
        self.view.zoom_changed.connect(self._on_zoom)
        self.view.centerOn(0, 0)
        self._refresh_layer_buttons()

        self._tool_actions["line"].setChecked(True)
        self.view.set_tool(self._tools["line"])

    # ─────────────────────────────────────────────────── toolbar
    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar("Tools", self)
        tb.setMovable(False)
        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)
        self._tool_actions: dict[str, QAction] = {}
        for key, label, shortcut in [
            ("select", "Select", "V"), ("line", "Line", "L"),
            ("polyline", "Polyline", "P"), ("rect", "Rect", "R"),
            ("circle", "Circle", "C"), ("trim", "Trim", "T"),
            ("paint", "Paint", "B"),
        ]:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setShortcut(QKeySequence(shortcut))
            act.setToolTip(f"{label} ({shortcut})")
            act.triggered.connect(lambda _ch, k=key: self._activate_tool(k))
            self._tool_group.addAction(act)
            tb.addAction(act)
            self._tool_actions[key] = act
        tb.addSeparator()
        self.snap_action = QAction("Snap", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.setShortcut(QKeySequence("F9"))
        self.snap_action.toggled.connect(self.view.set_snap_enabled)
        tb.addAction(self.snap_action)

        # Ortho button: left-click toggles, dropdown arrow picks angle
        self._ortho_btn = QToolButton()
        self._ortho_btn.setText("Ortho")
        self._ortho_btn.setCheckable(True)
        self._ortho_btn.setToolTip("Ortho lock (90°)")
        self._ortho_btn.toggled.connect(self.view.set_ortho_enabled)
        ortho_menu = QMenu()
        for angle in [90, 45, 30, 15]:
            act = ortho_menu.addAction(f"{angle}°")
            act.triggered.connect(
                lambda _ch=False, a=angle: self._set_ortho_angle(a)
            )
        self._ortho_btn.setMenu(ortho_menu)
        self._ortho_btn.setPopupMode(
            QToolButton.ToolButtonPopupMode.MenuButtonPopup
        )
        tb.addWidget(self._ortho_btn)

        tb.addSeparator()
        undo_act = self.undo_stack.createUndoAction(self, "Undo")
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        redo_act = self.undo_stack.createRedoAction(self, "Redo")
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        tb.addAction(undo_act)
        tb.addAction(redo_act)

        # ── 16-swatch paint color palette (2×8) ──
        tb.addSeparator()
        paint_arrow = QAction("Paint →", self)
        paint_arrow.setEnabled(False)
        tb.addAction(paint_arrow)
        self._palette = ColorPalette()
        tb.addWidget(self._palette)
        self._palette.color_selected.connect(self._on_color_selected)

        # ── 16-swatch line color palette (2×8) ──
        tb.addSeparator()
        line_arrow = QAction("Lines →", self)
        line_arrow.setEnabled(False)
        tb.addAction(line_arrow)
        self._line_palette = ColorPalette(colors=_LINE_PALETTE)
        tb.addWidget(self._line_palette)
        self._line_palette.color_selected.connect(self._on_line_color_selected)

        return tb

    def _activate_tool(self, key: str) -> None:
        self.view.set_tool(self._tools[key])

    def _on_color_selected(self, color: QColor) -> None:
        paint = self._tools.get("paint")
        if paint:
            paint.set_color(color)

    def _on_line_color_selected(self, color: QColor) -> None:
        self.view.set_stroke(color.name())

    def _set_ortho_angle(self, angle: int) -> None:
        self.view.set_ortho_angle(angle)
        self._ortho_btn.setToolTip(f"Ortho lock ({angle}°)")

    # ─────────────────────────────────────────────────── status
    def _refresh_status(self) -> None:
        self._status.setText(
            f"{self._last_coord}   ·   {self._last_kind}   ·   zoom {self._last_zoom}"
        )

    def _on_cursor(self, p: QPointF, kind: str) -> None:
        gs = self.view.grid_spacing
        self._last_coord = f"X {p.x()/gs:.0f}  Y {p.y()/gs:.0f}"
        self._last_kind = {
            "grid": "SNAP", "endpoint": "■ end", "midpoint": "▲ mid", "": "free",
        }.get(kind, "free")
        self._refresh_status()

    def _on_zoom(self, scale: float) -> None:
        self._last_zoom = f"{scale * 100:.0f}%"
        if scale >= 1:
            self._scale_label.setText(f"{scale:.0f}:1")
        else:
            self._scale_label.setText(f"1:{1 / scale:.0f}")
        self._refresh_status()

    # ─────────────────────────────────────────────────── layer mode
    def _set_layer_mode(self, mode: str) -> None:
        self._layer_mode = mode
        self.view._layer_mode = mode
        if mode == "parti":
            self.document.active_index = 0
        elif mode == "trace":
            self.document.active_index = 1
        else:  # both — drawing goes to trace
            self.document.active_index = 1
        self._refresh_layer_buttons()

    def _toggle_layer_visibility_by_name(self, name: str) -> None:
        idx = 0 if name == "parti" else 1
        if idx < len(self.document.layers):
            layer = self.document.layers[idx]
            layer.set_visible(not layer.visible)
            self._refresh_layer_buttons()
            self.view.viewport().update()

    def _refresh_layer_buttons(self) -> None:
        for i, btn in enumerate(self._layer_buttons):
            mode = self._layer_modes[i]
            active = (mode == self._layer_mode)
            dot = "\U0001F7E2" if active else "⚪"  # green / white circle
            btn.setText(f"{dot} {mode}")
            f = btn.font()
            f.setBold(active)
            btn.setFont(f)
