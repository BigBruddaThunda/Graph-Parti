# Canvas Text System — Design Spec (2026-06-02)

## Two text tools

| Tool | Button | Key | data(1) | Behavior |
|------|--------|-----|---------|----------|
| Word | Word | A | word_text | Flowing text, 50-char wrap, VG5000 12px |
| Cell | Cell | G | cell_text | 1 char = 1 grid cell (20x20). VG5000 sized + letter-spaced so advance = grid_spacing. Line height = grid_spacing. |

Both use QGraphicsTextItem with TextEditorInteraction for full text editing.

## 61 SCL emoji palette (toolbar, 2-row grids per group)

Placed in the toolbar after the line color palette. Each group is a 2-row grid of 18x18 QToolButtons with a label arrow before it, matching the paint/line palette pattern.

- Operators (12): 2x6 — `📍🧲🤌👀🐋🧸` / `🚀🥨🦢🦉🪵✒️`
- Axes (6): 2x3 — `🏛🔨🌹` / `🪐⌛🐬`
- Orders (7): 3+4 — `🐂⛽🦋` / `🏟🌾⚖🖼`
- Colors (8): 2x4 — `⚫🟢🔵🟣` / `🔴🟠🟡⚪`
- Modifiers (5): 3+2 — `🛒🪡🍗` / `➕➖`
- Blocks (22): 2x11 — `♨️🎯🔢🧈🫀▶️🎼♟️🪜🌎🎱` / `🌋🪞🗿🛠🧩🪫🏖🏗🧬🚂🔠`
- System (1): `🧮`

Click inserts that emoji at the cursor in the active text item.

## Editing behaviors

- Click text item (with text tool active) -> re-enter edit mode
- Move via SelectTool drag -> position snaps to grid on release
- Overlap guard: on text creation, if a text item exists at that cell -> edit existing
- Paste: word text pastes normal; cell text spaces chars 1-per-cell

## Files

- tools.py: rename TextTool -> WordTextTool, add CellTextTool
- canvas_widget.py: register both tools, build EmojiPalette widgets in toolbar
- canvas_view.py: grid-snap on text move release, cell-paste intercept
