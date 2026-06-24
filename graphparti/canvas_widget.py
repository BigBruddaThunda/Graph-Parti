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
    QLineEdit, QMenu, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from .canvas_view import CanvasView
from .document import Document
from .sound import SoundEngine
from .tools import (
    ArcTool, ArrayPolarTool, ArrayRectTool, BlockInsertTool, BlockSaveTool, BreakTool, CellTextTool, ChamferTool, CircleTool, ConstructionLineTool,
    CopyTool, DivideTool, EllipseTool,
    EyedropperTool, ExtendTool, FilletTool, HatchTool, JoinTool, LeaderTool, LinearDimTool, LineTool, MatchPropTool, MeasureTool, MirrorTool, OffsetTool,
    PaintTool, PEditTool, PerspectiveTool, PolygonTool, PolylineTool, RectTool, RotateTool, ScaleTool, SelectTool,
    SplineTool, StretchTool, TrimTool, WordTextTool,
    set_line_type, LINE_TYPES, set_line_weight, LINE_WEIGHTS,
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

_SCL_GROUPS = [
    ("Op", ["📍", "🧲", "🤌", "👀", "🐋", "🧸",
            "🚀", "🥨", "🦢", "🦉", "🪵", "✒️"]),
    ("Ax", ["🏛", "🔨", "🌹", "🪐", "⌛", "🐬"]),
    ("Or", ["🐂", "⛽", "🦋", "🧮",
            "🏟", "🌾", "⚖", "🖼"]),
    ("Co", ["⚫", "🟢", "🔵", "🟣", "🔴", "🟠", "🟡", "⚪"]),
    ("Md", ["🛒", "🪡", "🍗", "➕", "➖", "±"]),
    ("Bk", ["♨️", "🎯", "🔢", "🧈", "🫀", "▶️", "🎼", "♟️", "🪜", "🌎", "🎱",
            "🌋", "🪞", "🗿", "🛠", "🧩", "🪫", "🏖", "🏗", "🧬", "🚂", "🔠"]),
]

# 8-color SCL drafting register — each color carries default line type + weight
SCL_COLORS = {
    "⚫": {"hex": "#3C3C3C", "name": "Order",        "line_type": "continuous", "weight": "heavy"},
    "🟢": {"hex": "#348219", "name": "Growth",       "line_type": "continuous", "weight": "medium"},
    "🔵": {"hex": "#2464E5", "name": "Planning",     "line_type": "dashed",     "weight": "fine"},
    "🟣": {"hex": "#9255E5", "name": "Magnificence", "line_type": "dashdot",    "weight": "light"},
    "🔴": {"hex": "#C1140C", "name": "Passion",      "line_type": "continuous", "weight": "bold"},
    "🟠": {"hex": "#F57E16", "name": "Connection",   "line_type": "continuous", "weight": "medium"},
    "🟡": {"hex": "#F7B731", "name": "Play",         "line_type": "dot",        "weight": "fine"},
    "⚪": {"hex": "#F5F5DC", "name": "Eudaimonia",   "line_type": "dashed",     "weight": "hairline"},
}


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


class DraggableEmojiButton(QToolButton):
    """Emoji button: click = insert text, drag = place a book onto the canvas."""
    emoji_clicked = Signal(str)
    emoji_right_clicked = Signal(str)
    emoji_dragged = Signal(str)

    def __init__(self, glyph: str, parent=None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self._drag_start = None
        self.setText(glyph)
        self.setFixedSize(22, 22)
        self.setStyleSheet(
            "QToolButton { font-size:13px; padding:0; border:1px solid #ccc; }"
            "QToolButton:hover { background:#e0e0e0; }"
        )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.emoji_right_clicked.emit(self._glyph)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._drag_start is not None
                and (event.position().toPoint() - self._drag_start).manhattanLength() > 8):
            from PySide6.QtGui import QDrag
            from PySide6.QtCore import QMimeData
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self._glyph)
            mime.setData("application/x-scl-glyph", self._glyph.encode("utf-8"))
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
            self._drag_start = None
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if (self._drag_start is not None
                and (event.position().toPoint() - self._drag_start).manhattanLength() <= 8):
            self.emoji_clicked.emit(self._glyph)
        self._drag_start = None
        super().mouseReleaseEvent(event)


class EmojiGroupWidget(QWidget):
    """One SCL group: 2-row grid of draggable emoji buttons."""
    emoji_clicked = Signal(str)
    emoji_dragged = Signal(str)

    def __init__(self, glyphs: list[str], parent=None) -> None:
        super().__init__(parent)
        grid = QGridLayout(self)
        grid.setSpacing(1)
        grid.setContentsMargins(0, 0, 0, 0)
        cols = (len(glyphs) + 1) // 2
        for i, glyph in enumerate(glyphs):
            btn = DraggableEmojiButton(glyph)
            btn.emoji_clicked.connect(self.emoji_clicked.emit)
            btn.emoji_dragged.connect(self.emoji_dragged.emit)
            grid.addWidget(btn, i // cols, i % cols)


class TextComposerBox(QLineEdit):
    """63rd box: type/paste text or click emoji buttons to compose, then
    click-drag the composed text onto the canvas as a movable block.
    250 character limit. Drag emits application/x-scl-textblock mime."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("type or click glyphs → drag onto canvas")
        self.setMaxLength(250)
        self._drag_start = None
        self.setStyleSheet(
            "QLineEdit { font-size:11px; background:#4a4a4a; color:white;"
            " border:1px solid #555; padding:0 4px; }"
        )

    def insert_glyph(self, glyph: str) -> None:
        self.insert(glyph)
        self.setFocus()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._drag_start is not None
                and self.text().strip()
                and (event.position().toPoint() - self._drag_start).manhattanLength() > 12):
            from PySide6.QtGui import QDrag
            from PySide6.QtCore import QMimeData
            drag = QDrag(self)
            mime = QMimeData()
            text = self.text().strip()[:250]
            mime.setData("application/x-scl-textblock", text.encode("utf-8"))
            mime.setText(text)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
            self._drag_start = None
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_start = None
        super().mouseReleaseEvent(event)


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
            "offset": OffsetTool(self.view),
            "paint": PaintTool(self.view),
            "pedit": PEditTool(self.view),
            "perspective": PerspectiveTool(self.view),
            "word": WordTextTool(self.view),
            "cell": CellTextTool(self.view),
            "extend": ExtendTool(self.view),
            "divide": DivideTool(self.view),
            "rotate": RotateTool(self.view),
            "mirror": MirrorTool(self.view),
            "scale": ScaleTool(self.view),
            "ellipse": EllipseTool(self.view),
            "arc": ArcTool(self.view),
            "array_rect": ArrayRectTool(self.view),
            "array_polar": ArrayPolarTool(self.view),
            "block_save": BlockSaveTool(self.view),
            "block_insert": BlockInsertTool(self.view),
            "copy": CopyTool(self.view),
            "eyedropper": EyedropperTool(self.view),
            "fillet": FilletTool(self.view),
            "hatch": HatchTool(self.view),
            "chamfer": ChamferTool(self.view),
            "join": JoinTool(self.view),
            "leader": LeaderTool(self.view),
            "dim_linear": LinearDimTool(self.view),
            "xline": ConstructionLineTool(self.view),
            "matchprop": MatchPropTool(self.view),
            "measure": MeasureTool(self.view),
            "polygon": PolygonTool(self.view),
            "break_at": BreakTool(self.view),
            "spline": SplineTool(self.view),
            "stretch": StretchTool(self.view),
        }

        self.toolbar = self._build_toolbar()
        layout.addWidget(self.toolbar)

        # ── 32-color palette bar (16 line + 16 fill) ──
        palette_bar = self._build_palette_bar()
        layout.addWidget(palette_bar)

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
        self._layer_modes = ["parti", "both", "trace", "book"]
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

        add_layer_btn = QToolButton()
        add_layer_btn.setText("+")
        add_layer_btn.setFixedSize(20, 20)
        add_layer_btn.setToolTip("Add new vector layer")
        add_layer_btn.clicked.connect(self._add_user_layer)
        status_lay.addWidget(add_layer_btn)

        layout.addWidget(status_bar)

        # ── SCL bottom band (61 glyphs + ± + text composer) ──
        scl_band = QWidget()
        scl_band.setFixedHeight(28)
        scl_band.setStyleSheet("background: #3C3C3C;")
        scl_lay = QHBoxLayout(scl_band)
        scl_lay.setContentsMargins(2, 2, 2, 2)
        scl_lay.setSpacing(1)
        _btn_ss = (
            "QToolButton { font-size:12px; padding:0; border:1px solid #555;"
            " background:#4a4a4a; color:white; }"
            "QToolButton:hover { background:#666; }"
        )
        _color_glyphs = set(SCL_COLORS.keys())
        all_glyphs = []
        for _label, glyphs in _SCL_GROUPS:
            all_glyphs.extend(glyphs)
        self._scl_band_btns = {}
        for glyph in all_glyphs:
            btn = DraggableEmojiButton(glyph)
            btn.setFixedSize(20, 20)
            if glyph in _color_glyphs:
                props = SCL_COLORS[glyph]
                btn.setStyleSheet(
                    f"QToolButton {{ font-size:12px; padding:0;"
                    f" background:{props['hex']}; border:2px solid #D4935A;"
                    f" border-radius:10px; color:white; }}"
                    f"QToolButton:hover {{ border:2px solid #fff; }}"
                )
                btn.emoji_clicked.connect(
                    lambda g=glyph: self._on_scl_color_selected(g))
                btn.emoji_right_clicked.connect(self._on_color_right_click)
            else:
                btn.setStyleSheet(_btn_ss)
                btn.emoji_clicked.connect(self._on_emoji_band_click)
                btn.emoji_right_clicked.connect(self._on_emoji_right_click)
            scl_lay.addWidget(btn)
            self._scl_band_btns[glyph] = btn
        # 62nd: ± symbol
        pm_btn = DraggableEmojiButton("±")
        pm_btn.setFixedSize(20, 20)
        pm_btn.setStyleSheet(_btn_ss)
        pm_btn.emoji_clicked.connect(self._on_emoji_band_click)
        scl_lay.addWidget(pm_btn)
        # 63rd: text composer — type/paste text, click emojis into it, drag out
        self._text_composer = TextComposerBox()
        self._text_composer.setFixedHeight(22)
        self._text_composer.setMinimumWidth(120)
        scl_lay.addWidget(self._text_composer, 1)
        layout.addWidget(scl_band)

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
        self.view._extend_tool = self._tools["extend"]
        self._file_path = None
        self._autoload_template()

        from .joystick import ViewNavigator, JoystickNavigator, joystick_available
        self._navigator = ViewNavigator(self.view)
        self.view._navigator = self._navigator
        self._joystick = JoystickNavigator(self.view, self._navigator)
        self._joystick.start()
        if self._joystick.connected:
            self._status.setText("GRAPH PARTI — joystick detected")

        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self._save)
        self.addAction(save_act)

        open_act = QAction("Open", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open)
        self.addAction(open_act)

        export_act = QAction("Export PNG", self)
        export_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        export_act.triggered.connect(self._export_png)
        self.addAction(export_act)

        orders_act = QAction("5 Orders", self)
        orders_act.setShortcut(QKeySequence("Ctrl+5"))
        orders_act.triggered.connect(self._draw_five_orders)
        self.addAction(orders_act)

        # Save the current drawing into the District file system at its zip
        self._district = None  # lazy DistrictBridge
        district_act = QAction("Save to District", self)
        district_act.setShortcut(QKeySequence("Ctrl+Shift+D"))
        district_act.triggered.connect(self._save_to_district)
        self.addAction(district_act)

        self._sound_engine = SoundEngine()
        self.view._sound_engine = self._sound_engine
        self._sound_engine.start()

    def set_facets(self, operator=None, axis=None, order=None, color=None) -> None:
        """Host-callable: push the cockpit dial's zip onto the canvas."""
        self.view.set_current_facets(operator, axis, order, color)

    def _save_to_district(self) -> None:
        import os
        from PySide6.QtWidgets import QInputDialog
        from .district_bridge import DistrictBridge
        facets = self.view.current_facets
        if all(f is None for f in facets):
            self._status.setText("Set a zip on the cockpit dial first "
                                 "(no facets = no district address)")
            return
        title, ok = QInputDialog.getText(self, "Save to District",
                                         "Title for this room:")
        if not ok or not title.strip():
            return
        if self._district is None:
            root = os.path.join(os.path.dirname(__file__), os.pardir, "district-store")
            self._district = DistrictBridge(os.path.abspath(root))
        node = self._district.save_canvas(self.document, facets, title.strip())
        self._status.setText(f"Filed at {node.point_string()} → {node.file}")

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
            ("circle", "Circle", "C"), ("ellipse", "Ellipse", ""),
            ("arc", "Arc", ""), ("array_rect", "ArrR", ""), ("array_polar", "ArrP", ""),
            ("block_save", "BlkS", ""), ("block_insert", "BlkI", ""),
            ("trim", "Trim", "T"),
            ("extend", "Extend", ""), ("divide", "Divide", "D"),
            ("rotate", "Rotate", ""),
            ("mirror", "Mirror", "M"),
            ("scale", "Scale", "S"),
            ("offset", "Offset", "O"), ("paint", "Paint", "B"),
            ("pedit", "PEdit", ""),
            ("perspective", "VP", ""),
            ("word", "Word", "A"), ("cell", "Cell", "G"),
            ("copy", "Copy", ""),
            ("eyedropper", "Pick", "I"),
            ("fillet", "Fillet", ""),
            ("hatch", "Hatch", "H"),
            ("chamfer", "Chamfer", ""),
            ("join", "Join", "J"),
            ("leader", "Leader", ""),
            ("dim_linear", "Dim", ""),
            ("xline", "XLine", ""),
            ("matchprop", "Match", ""),
            ("measure", "Measure", ""),
            ("polygon", "Polygon", ""),
            ("break_at", "Break", ""),
            ("spline", "Spline", ""),
            ("stretch", "Stretch", ""),
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
        self._ortho_btn.setToolTip("Ortho lock (45°)")
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
        # Stacked undo/redo icon buttons (↶ over ↷) to save horizontal space
        ur_widget = QWidget()
        ur_lay = QVBoxLayout(ur_widget)
        ur_lay.setContentsMargins(0, 0, 0, 0)
        ur_lay.setSpacing(0)
        undo_btn = QToolButton()
        undo_btn.setText("↶")  # ↶
        undo_btn.setFixedSize(24, 15)
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        redo_btn = QToolButton()
        redo_btn.setText("↷")  # ↷
        redo_btn.setFixedSize(24, 15)
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        undo_btn.setEnabled(self.undo_stack.canUndo())
        redo_btn.setEnabled(self.undo_stack.canRedo())
        self.undo_stack.canUndoChanged.connect(undo_btn.setEnabled)
        self.undo_stack.canRedoChanged.connect(redo_btn.setEnabled)
        ur_lay.addWidget(undo_btn)
        ur_lay.addWidget(redo_btn)
        tb.addWidget(ur_widget)
        # Keep keyboard shortcuts via hidden actions
        undo_act = self.undo_stack.createUndoAction(self, "Undo")
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        undo_act.triggered.connect(lambda: self._sound_engine and self._sound_engine.feedback.undo())
        redo_act = self.undo_stack.createRedoAction(self, "Redo")
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        redo_act.triggered.connect(lambda: self._sound_engine and self._sound_engine.feedback.redo())
        self.addAction(undo_act)
        self.addAction(redo_act)

        # ── 16-swatch paint color palette (2×8) ──
        tb.addSeparator()
        paint_arrow = QAction("Paint →", self)
        paint_arrow.setEnabled(False)
        tb.addAction(paint_arrow)
        self._palette = ColorPalette()
        tb.addWidget(self._palette)
        self._palette.color_selected.connect(self._on_color_selected)

        self._fill_toggle = QAction("Fill", self)
        self._fill_toggle.setCheckable(True)
        self._fill_toggle.setChecked(False)
        self._fill_toggle.setToolTip("Auto-fill shapes with paint color (F)")
        self._fill_toggle.setShortcut(QKeySequence("F"))
        self._fill_toggle.toggled.connect(self._on_fill_toggled)
        tb.addAction(self._fill_toggle)

        # ── 8-color SCL drafting bar ──
        tb.addSeparator()
        line_arrow = QAction("Lines →", self)
        line_arrow.setEnabled(False)
        tb.addAction(line_arrow)
        self._color_bar = QWidget()
        color_lay = QHBoxLayout(self._color_bar)
        color_lay.setContentsMargins(2, 2, 2, 2)
        color_lay.setSpacing(2)
        self._scl_color_btns = {}
        for glyph, props in SCL_COLORS.items():
            btn = QToolButton()
            btn.setText(glyph)
            btn.setFixedSize(28, 28)
            btn.setCheckable(True)
            btn.setToolTip(f"{props['name']} — {props['line_type']} {props['weight']}")
            btn.setStyleSheet(
                f"QToolButton {{ background: {props['hex']}; border: 2px solid #D4935A;"
                f" font-size: 14px; border-radius: 3px; }}"
                f"QToolButton:checked {{ border: 3px solid #000; }}"
            )
            btn.clicked.connect(lambda _ch=False, g=glyph: self._on_scl_color_selected(g))
            color_lay.addWidget(btn)
            self._scl_color_btns[glyph] = btn
        tb.addWidget(self._color_bar)
        # Default to ⚫ Order (commit)
        self._active_scl_color = "⚫"
        self._scl_color_btns["⚫"].setChecked(True)

        # ── Line type cycle ──
        tb.addSeparator()
        self._line_type_idx = 0
        self._line_type_names = list(LINE_TYPES.keys())
        self._line_type_btn = QToolButton()
        self._line_type_btn.setText("——")
        self._line_type_btn.setToolTip("Line type: continuous")
        self._line_type_btn.setFixedWidth(40)
        self._line_type_btn.clicked.connect(self._cycle_line_type)
        tb.addWidget(self._line_type_btn)

        self._line_weight_idx = 3  # default = medium
        self._line_weight_names = list(LINE_WEIGHTS.keys())
        self._weight_btn = QToolButton()
        self._weight_btn.setText("M")
        self._weight_btn.setToolTip("Weight: medium")
        self._weight_btn.setFixedWidth(24)
        self._weight_btn.clicked.connect(self._cycle_line_weight)
        tb.addWidget(self._weight_btn)

        return tb

    def _build_palette_bar(self) -> QWidget:
        """Build the 32-color palette bar: 16 line colors | 16 fill colors | fill toggle."""
        _SCL_HEXES = [props["hex"] for props in SCL_COLORS.values()]
        _COPPER = "#D4935A"
        # 8 copper variations for fill (light to dark)
        _COPPER_FILLS = [
            "#F5E6D0", "#E8CBA8", "#D4935A", "#C47D3F",
            "#A86B35", "#8C5A2B", "#704920", "#543818",
        ]

        bar = QWidget()
        bar.setFixedHeight(42)
        bar.setStyleSheet("background: #E8E0D0;")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(4, 2, 4, 2)
        bar_lay.setSpacing(8)

        # ── LEFT: 16 line color boxes (8 SCL canon + 8 custom/empty) ──
        line_label = QLabel("Lines")
        line_label.setStyleSheet("font-size:10px; color:#666;")
        bar_lay.addWidget(line_label)

        line_widget = QWidget()
        line_grid = QGridLayout(line_widget)
        line_grid.setSpacing(1)
        line_grid.setContentsMargins(0, 0, 0, 0)
        self._line_swatch_btns = []
        # Row 0: 8 SCL canon colors
        for i, (glyph, props) in enumerate(SCL_COLORS.items()):
            btn = SwatchButton(QColor(props["hex"]))
            btn.setToolTip(f"{props['name']} line — {props['line_type']} {props['weight']}")
            btn.clicked.connect(lambda _ch=False, g=glyph: self._on_scl_color_selected(g))
            btn.right_clicked.connect(lambda g=glyph: self._on_color_right_click(g))
            line_grid.addWidget(btn, 0, i)
            self._line_swatch_btns.append(btn)
        # Row 1: 8 custom/free line color slots (default: light greys)
        _CUSTOM_LINE = ["#666666", "#999999", "#CCCCCC", "#1A1A1A",
                        "#00AAAA", "#FF69B4", "#006400", "#800080"]
        for i, hex_c in enumerate(_CUSTOM_LINE):
            btn = SwatchButton(QColor(hex_c))
            btn.setToolTip(f"Custom line color (right-click to change)")
            idx = len(self._line_swatch_btns)
            btn.clicked.connect(lambda _ch=False, c=hex_c: self.view.set_stroke(c))
            btn.right_clicked.connect(lambda ii=idx: self._pick_line_swatch(ii))
            line_grid.addWidget(btn, 1, i)
            self._line_swatch_btns.append(btn)
        bar_lay.addWidget(line_widget)

        bar_lay.addSpacing(12)

        # ── RIGHT: 16 fill color boxes (8 SCL canon + 8 copper variations) ──
        fill_label = QLabel("Fill")
        fill_label.setStyleSheet("font-size:10px; color:#666;")
        bar_lay.addWidget(fill_label)

        fill_widget = QWidget()
        fill_grid = QGridLayout(fill_widget)
        fill_grid.setSpacing(1)
        fill_grid.setContentsMargins(0, 0, 0, 0)
        self._fill_swatch_btns = []
        # Row 0: 8 SCL canon fill colors
        for i, (glyph, props) in enumerate(SCL_COLORS.items()):
            btn = SwatchButton(QColor(props["hex"]))
            btn.setToolTip(f"{props['name']} fill")
            btn.clicked.connect(lambda _ch=False, c=props["hex"]: self._set_fill_color(c))
            btn.right_clicked.connect(lambda ii=len(self._fill_swatch_btns): self._pick_fill_swatch(ii))
            fill_grid.addWidget(btn, 0, i)
            self._fill_swatch_btns.append(btn)
        # Row 1: 8 copper variation fill colors
        for i, hex_c in enumerate(_COPPER_FILLS):
            btn = SwatchButton(QColor(hex_c))
            btn.setToolTip(f"Copper fill variation")
            btn.clicked.connect(lambda _ch=False, c=hex_c: self._set_fill_color(c))
            btn.right_clicked.connect(lambda ii=len(self._fill_swatch_btns): self._pick_fill_swatch(ii))
            fill_grid.addWidget(btn, 1, i)
            self._fill_swatch_btns.append(btn)
        bar_lay.addWidget(fill_widget)

        # ── Fill toggle button ──
        self._fill_toggle_btn = QToolButton()
        self._fill_toggle_btn.setText("Fill\nOFF")
        self._fill_toggle_btn.setCheckable(True)
        self._fill_toggle_btn.setChecked(False)
        self._fill_toggle_btn.setFixedSize(36, 36)
        self._fill_toggle_btn.setStyleSheet(
            "QToolButton { background:#ccc; border:2px solid #D4935A; font-size:9px; }"
            "QToolButton:checked { background:#348219; color:white; }"
        )
        self._fill_toggle_btn.setToolTip("Toggle fill on/off (F)")
        self._fill_toggle_btn.toggled.connect(self._on_palette_fill_toggled)
        bar_lay.addWidget(self._fill_toggle_btn)

        bar_lay.addStretch(1)
        return bar

    def _set_fill_color(self, hex_color: str) -> None:
        """Set the fill color and activate fill mode."""
        paint = self._tools.get("paint")
        if paint:
            paint.set_color(QColor(hex_color))
        self.view.set_fill(hex_color)
        self._fill_toggle_btn.setChecked(True)
        self._fill_toggle_btn.setText("Fill\nON")

    def _on_palette_fill_toggled(self, on: bool) -> None:
        if on:
            self._fill_toggle_btn.setText("Fill\nON")
            last_fill = getattr(self, '_last_fill_hex', "#D4935A")
            self.view.set_fill(last_fill)
        else:
            self._fill_toggle_btn.setText("Fill\nOFF")
            self.view.set_fill(None)

    def _pick_line_swatch(self, idx: int) -> None:
        if idx >= len(self._line_swatch_btns):
            return
        btn = self._line_swatch_btns[idx]
        c = QColorDialog.getColor(btn.color(), self, "Choose Line Color")
        if c.isValid():
            btn.set_color(c)
            self.view.set_stroke(c.name())

    def _pick_fill_swatch(self, idx: int) -> None:
        if idx >= len(self._fill_swatch_btns):
            return
        btn = self._fill_swatch_btns[idx]
        c = QColorDialog.getColor(btn.color(), self, "Choose Fill Color")
        if c.isValid():
            btn.set_color(c)
            self._set_fill_color(c.name())

    def _activate_tool(self, key: str) -> None:
        self.view.set_tool(self._tools[key])
        if self._sound_engine is not None:
            self._sound_engine.on_tool_activate(key)

    def _on_color_selected(self, color: QColor) -> None:
        paint = self._tools.get("paint")
        if paint:
            paint.set_color(color)
        self._fill_toggle.setChecked(True)
        self.view.set_fill(color.name())
        if self.view.active_tool is self._tools.get("select"):
            self._tool_actions["paint"].setChecked(True)
            self._activate_tool("paint")

    def _on_fill_toggled(self, on: bool) -> None:
        if on:
            self.view.set_fill(self._palette.active_color().name())
        else:
            self.view.set_fill(None)

    def _on_line_color_selected(self, color: QColor) -> None:
        self.view.set_stroke(color.name())
        if self.view.active_tool is not self._tools.get("line"):
            self._tool_actions["line"].setChecked(True)
            self._activate_tool("line")

    def _on_scl_color_selected(self, glyph: str) -> None:
        """Select an SCL color — sets stroke color, line type, and line weight all at once."""
        props = SCL_COLORS.get(glyph)
        if not props:
            return
        self._active_scl_color = glyph
        # Uncheck all, check selected
        for g, btn in self._scl_color_btns.items():
            btn.setChecked(g == glyph)
        # Set stroke color
        self.view.set_stroke(props["hex"])
        # Set line type
        type_name = props["line_type"]
        self._line_type_idx = list(LINE_TYPES.keys()).index(type_name) if type_name in LINE_TYPES else 0
        labels = {"continuous": "——", "dashed": "- -", "hidden": "··",
                  "center": "—·—", "phantom": "—··", "dot": "····", "dashdot": "—·"}
        self._line_type_btn.setText(labels.get(type_name, type_name))
        self._line_type_btn.setToolTip(f"Line type: {type_name}")
        self.view._active_line_type = type_name
        # Set line weight
        weight_name = props["weight"]
        self._line_weight_idx = list(LINE_WEIGHTS.keys()).index(weight_name) if weight_name in LINE_WEIGHTS else 3
        wlabels = {"hairline": "H", "fine": "F", "light": "Lt",
                   "medium": "M", "bold": "B", "heavy": "Hv", "x-heavy": "XH"}
        self._weight_btn.setText(wlabels.get(weight_name, weight_name[:2]))
        self._weight_btn.setToolTip(f"Weight: {weight_name}")
        self.view._active_line_weight = LINE_WEIGHTS.get(weight_name, 0.5)
        # Apply to selected items
        for item in self.view.scene().selectedItems():
            if hasattr(item, 'setPen'):
                from PySide6.QtGui import QPen
                pen = QPen(item.pen())
                pen.setColor(QColor(props["hex"]))
                pen.setWidthF(LINE_WEIGHTS.get(weight_name, 0.5))
                # Set dash pattern
                from PySide6.QtCore import Qt as QtCore_Qt
                pattern = LINE_TYPES.get(type_name)
                if pattern is None:
                    pen.setStyle(QtCore_Qt.PenStyle.SolidLine)
                elif type_name == "dashed":
                    pen.setStyle(QtCore_Qt.PenStyle.DashLine)
                else:
                    pen.setStyle(QtCore_Qt.PenStyle.CustomDashLine)
                    pen.setDashPattern([float(v) for v in pattern])
                item.setPen(pen)

    def _cycle_line_type(self) -> None:
        names = list(LINE_TYPES.keys())
        self._line_type_idx = (self._line_type_idx + 1) % len(names)
        name = names[self._line_type_idx]
        labels = {"continuous": "——", "dashed": "- -", "hidden": "··",
                  "center": "—·—", "phantom": "—··", "dot": "····", "dashdot": "—·"}
        self._line_type_btn.setText(labels.get(name, name))
        self._line_type_btn.setToolTip(f"Line type: {name}")
        self.view._active_line_type = name
        for item in self.view.scene().selectedItems():
            set_line_type(item, name)

    def _cycle_line_weight(self) -> None:
        from .tools import LINE_WEIGHTS, set_line_weight
        names = list(LINE_WEIGHTS.keys())
        self._line_weight_idx = (self._line_weight_idx + 1) % len(names)
        name = names[self._line_weight_idx]
        labels = {"hairline": "H", "fine": "F", "light": "Lt",
                  "medium": "M", "bold": "B", "heavy": "Hv", "x-heavy": "XH"}
        self._weight_btn.setText(labels.get(name, name[:2]))
        self._weight_btn.setToolTip(f"Weight: {name}")
        self.view._active_line_weight = LINE_WEIGHTS[name]
        for item in self.view.scene().selectedItems():
            set_line_weight(item, name)

    def _on_emoji_clicked(self, glyph: str) -> None:
        from PySide6.QtWidgets import QGraphicsTextItem
        from PySide6.QtGui import QTextCursor
        focus = self.view.scene().focusItem()
        if isinstance(focus, QGraphicsTextItem):
            cursor = focus.textCursor()
            cursor.insertText(glyph)
            focus.setTextCursor(cursor)

    def _on_emoji_band_click(self, glyph: str) -> None:
        """Bottom-band emoji click → insert into text composer (63rd box)."""
        self._text_composer.insert_glyph(glyph)

    def _on_emoji_right_click(self, glyph: str) -> None:
        """Right-click non-color glyph → tool drawer popup."""
        drawer = TOOL_DRAWERS.get(glyph)
        if not drawer:
            return
        menu = QMenu(self)
        for tool_key, label in drawer:
            if tool_key in self._tools:
                act = menu.addAction(label)
                act.triggered.connect(
                    lambda _ch=False, k=tool_key: self._activate_tool(k))
        if menu.actions():
            btn = self.sender()
            if btn:
                menu.popup(btn.mapToGlobal(btn.rect().topLeft()))

    def _on_color_right_click(self, glyph: str) -> None:
        """Right-click a color glyph → color picker to customize."""
        props = SCL_COLORS.get(glyph)
        if not props:
            return
        current = QColor(props["hex"])
        color = QColorDialog.getColor(current, self, f"Customize {props['name']} color")
        if color.isValid():
            props["hex"] = color.name()
            btn = self._scl_band_btns.get(glyph)
            if btn:
                btn.setStyleSheet(
                    f"QToolButton {{ font-size:12px; padding:0;"
                    f" background:{color.name()}; border:2px solid #D4935A;"
                    f" border-radius:10px; color:white; }}"
                    f"QToolButton:hover {{ border:2px solid #fff; }}"
                )
            tb_btn = getattr(self, '_scl_color_btns', {}).get(glyph)
            if tb_btn:
                tb_btn.setStyleSheet(
                    f"QToolButton {{ background: {color.name()}; border: 2px solid #D4935A;"
                    f" font-size: 14px; border-radius: 3px; }}"
                    f"QToolButton:checked {{ border: 3px solid #000; }}"
                )
            if getattr(self, '_active_scl_color', None) == glyph:
                self.view.set_stroke(color.name())

    def _set_ortho_angle(self, angle: int) -> None:
        self.view.set_ortho_angle(angle)
        self._ortho_btn.setToolTip(f"Ortho lock ({angle}°)")

    def _autoload_template(self) -> None:
        import os
        root = os.path.join(os.path.dirname(__file__), os.pardir)
        template = os.path.join(root, "VIEWPORT-TEMPLATE.parti")
        if os.path.isfile(template):
            self.document.load_json(template)
            self._file_path = os.path.abspath(template)
            self.view.centerOn(1000, 700)
            self.view.viewport().update()

    # ─────────────────────────────────────────────────── save / load
    def _save(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        if self._file_path is None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Drawing", "", "PARTI files (*.parti);;JSON (*.json)")
            if not path:
                return
            self._file_path = path
        self.document.save_json(self._file_path)
        if self._sound_engine is not None:
            self._sound_engine.feedback.save_latch()
        self._status.setText(f"Saved: {self._file_path}")

    def _open(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Drawing", "", "PARTI files (*.parti);;JSON (*.json)")
        if not path:
            return
        self.undo_stack.clear()
        self.document.load_json(path)
        self._file_path = path
        self.view.viewport().update()
        self._status.setText(f"Opened: {path}")

    def _export_png(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtGui import QImage, QPainter
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG images (*.png)")
        if not path:
            return
        rect = self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20)
        img = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        img.fill(QColor("#F2EBD8"))
        painter = QPainter(img)
        self.scene.render(painter, source=rect)
        painter.end()
        img.save(path)
        self._status.setText(f"Exported: {path}")

    def _draw_five_orders(self) -> None:
        from .orders import generate_five_orders
        generate_five_orders(self.view)
        self.view.viewport().update()
        self._status.setText("Five Classical Orders drawn (Ctrl+Z to undo)")

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
        elif mode == "book":
            self.document.active_index = 2   # zip boxes compose on the book layer
        else:  # trace / both — drawing goes to trace
            self.document.active_index = 1
        self._refresh_layer_buttons()
        if self._sound_engine is not None:
            self._sound_engine.on_context_change({"layer": mode})

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

    def _add_user_layer(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        from .document import VectorLayer
        name, ok = QInputDialog.getText(self, "New Layer", "Layer name:")
        if ok and name.strip():
            layer = self.document.add_layer(
                VectorLayer(name.strip(), self.scene), active=True
            )
            self._layer_mode = name.strip()
            self.view._layer_mode = name.strip()
            self._refresh_layer_buttons()
