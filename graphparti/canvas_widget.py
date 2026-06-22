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
from .tools import (
    ArcTool, CellTextTool, CircleTool, ConstructionLineTool, CopyTool,
    DivideTool, EllipseTool,
    EyedropperTool, ExtendTool, LineTool, MirrorTool, OffsetTool, PaintTool,
    PolylineTool, RectTool, RotateTool, ScaleTool, SelectTool, TrimTool,
    WordTextTool,
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


class DraggableEmojiButton(QToolButton):
    """Emoji button: click = insert text, drag = place a book onto the canvas."""
    emoji_clicked = Signal(str)
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
            "word": WordTextTool(self.view),
            "cell": CellTextTool(self.view),
            "extend": ExtendTool(self.view),
            "divide": DivideTool(self.view),
            "rotate": RotateTool(self.view),
            "mirror": MirrorTool(self.view),
            "scale": ScaleTool(self.view),
            "ellipse": EllipseTool(self.view),
            "arc": ArcTool(self.view),
            "copy": CopyTool(self.view),
            "eyedropper": EyedropperTool(self.view),
            "xline": ConstructionLineTool(self.view),
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
        all_glyphs = []
        for _label, glyphs in _SCL_GROUPS:
            all_glyphs.extend(glyphs)
        for glyph in all_glyphs:
            btn = DraggableEmojiButton(glyph)
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(_btn_ss)
            btn.emoji_clicked.connect(self._on_emoji_band_click)
            scl_lay.addWidget(btn)
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
            ("arc", "Arc", ""), ("trim", "Trim", "T"),
            ("extend", "Extend", ""), ("divide", "Divide", "D"),
            ("rotate", "Rotate", ""),
            ("mirror", "Mirror", "M"),
            ("scale", "Scale", "S"),
            ("offset", "Offset", "O"), ("paint", "Paint", "B"),
            ("word", "Word", "A"), ("cell", "Cell", "G"),
            ("copy", "Copy", ""),
            ("eyedropper", "Pick", "I"),
            ("xline", "XLine", ""),
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
        redo_act = self.undo_stack.createRedoAction(self, "Redo")
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
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
