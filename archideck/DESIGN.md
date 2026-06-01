# Archideck cockpit — design notes (architect's vision, 2026-05-29)

GRAPH PARTI is the **canvas**. The Archideck is the **cockpit**. One program, two
halves — separable in code, unified in use.

## Split-pane
- One full-screen program. The GRAPH PARTI canvas fills the screen; the Archideck
  rides as a **portrait cockpit on the right** by default (left/right is a preference).
- The cockpit is the same **phone-native portrait design** that becomes the mobile
  app later — PC and mobile share one layout / navigation / tooling / zip system.
- Default size: cockpit ≈ the architect's Claude-window width — the scale that
  filters to mobile and full-screen portrait on a 2nd monitor.
- Detach / auto-hide behavior: deferred (many turns out).

## Isolation (load-bearing)
- `graphparti` is fully isolated — it never imports the cockpit. The `archideck`
  package **embeds** `graphparti.CanvasWidget`. One-way dependency only, so the
  canvas never inherits cockpit churn. "Two apps in one" that stay separable.

## Canvas-swap (mobile; deferred)
- On mobile, tapping the center **[Archideck]** copper plate **flips** the cockpit ↔
  the GRAPH PARTI canvas (and splits the 6 axes into 3 + plate + 3). The canvas
  scales to a full viewport. PC shows both side-by-side; the principle is the same.

## Cockpit anatomy
- **Color dial position = the base shell color** of the whole cockpit (8 colors).
- **12 Operators** = buttons mapped to **F1–F12**; clicking one fills the middle
  ground with that operator's tools (home-screen icons). Middle ground doubles as a
  phone preview.
- **Axis row:** 3 axes + copper **[Archideck]** plate + 3 axes. The plate later
  shows the username (e.g. `[BigBruddaThunda]`).
- **Zip dial:** 4 reels (operator / axis / order / color), center = active.
- **Z-pad:** the 5 Modifiers — ➕ up · ➖ down · 🛒 left · 🪡 right · 🍗 center.

## Zip tagging grammar  `[____] ± [_] | [free-text]`
- `[____]` — 4 positions accepting only the proper zip order (Op, Axis, Order,
  Color). Partial-tag with the dial: spin, click center to **stamp** that position;
  empty positions show empty space.
- `± [_]` — the tail. Z-pad left/right chooses the category (operator/axis/order/
  color/type/block/save); up/down moves within; center stamps. Caps at **4 emojis**
  (free multi-tag, NOT zip-locked).
- `| [free-text]` — anything after the bar is free text.
- Future: pops out at the point of origin like a painter's palette (or on right-click).

## w = Wilson button = lasso / sticky notes (deferred)
- Press **w** to bring out a lasso to circle / zip-address drawn content, then stamp
  with the dial. Sticky-note tagging on the canvas.

## Future flags
- **Event-logging flag** so the AI can *read* what was drafted on the canvas
  (lasso → read → tag).
- Roundtable little-brother / big-brother + cloud model access (the Emacs-side
  system), tied in later.

## Layout v2 — three vertical thirds (2026-05-30, architect notes)
Supersedes the single-column base shape. The cockpit reads top-to-bottom as **three
thirds**, all floating inside the color shell with **negative space (shell visible)**
between every window.

**Upper third — revelator + terminal** (two windows, *identical width*, centered with
shell margin around them):
- **Revelator** (top strip): thin, **single line**, **50-char budget**. Carries the
  zip code + tail + bar actions → becomes the notification rail. Shell shows all around.
- *(negative space)*
- **Terminal** (fills the rest of the upper third): same width as the revelator. The
  default output window. **5 buttons stacked on its right inner wall**; the **5th button
  sits on the text-input row**. A thin break separates terminal output from the input
  box. Input is a **single line that grows as you type**.
- *(negative space before the middle ground)*

**Middle third — work zone:**
- **Parallel slider** (left) · **middle ground** (center) · **12-operator rail** (right).
- The slider and the operator rail **scale to the middle-ground height** (as tall as the
  middle ground, not the whole panel).
- **Middle ground and terminal resize up/down together** — same behavior as the
  cockpit↔canvas split. Dragging the boundary trades terminal height for middle-ground
  height. (Two draggable boundaries total: cockpit↔canvas horizontal, terminal↔middle
  vertical.)

**Lower third — axis + instruments (thumb zone):**
- **Axis row** moves down to the top of this third: `🏛 ⌛ 🔨 [Archideck] 🐬 🌹 🪐`
  (split + copper plate spacing unchanged).
- **Instruments** below, all one height; lower third split into **3 columns**:
  - **Zip dial** — left **~2 columns**. *Much smaller* than the base shape: a compact
    **4×3 box** (4 reels × prev/active/next), shaped like the steampunk reel reference.
    Reels = **operator · axis · order · color** (confirmed 4). **Left edge flush** to the
    revelator/middle-ground left wall.
  - **Z-pad** — right column: **5 buttons in a box** (➕ up · ➖ down · 🛒 left · 🪡 right
    · 🍗 center). **Right edge flush** to the right wall — bookends the dial's left-flush.
- Placement = **general thumb location** (dial = left thumb, z-pad = right thumb).

**Confirmed at build (2026-05-31):**
- Z-pad right edge flush to the content's right wall (bookends the dial's left-flush). ✓
- Parallel slider stubbed as a vertical QSlider — wiring deferred to dual-mode spec below.

## Parallel slider — dual-mode behavior (future, 2026-05-31)
The slider has a **center-click button** and two modes:

**Archideck-active mode:** the slider lives inside the middle ground and slides up/down
within it (for workout program blocks / dropdown expanding windows / content blocks).

**GRAPH PARTI–active mode:** when the canvas window is active, the slider **expands up the
left side shell** of the cockpit, spanning the entire vertical length of the GRAPH PARTI
window. Shows viewport position. Clicking the center button while graph-parti is active
does NOT switch focus to the archideck — instead it pops out a **parallel bar in graph-parti**
that slides up/down using grid/scale/slide steps. The bar is a **snap-target for stylus/pen**
drawing (auto-snap to the bar to draw straight lines). Stylus and pen have different drawing
behaviors — the bar accommodates both. Mobile/tablet: same principle, bar becomes the primary
stylus guide for portrait-mode drawing.

## Status (this build)
**Layout v2 built (2026-05-31):** three-thirds cockpit in `panel.py` — revelator (thin
single-line strip, toolbar-height) + terminal (output + input + 5 modifier buttons on right
inner wall) / parallel slider (stub) + middle ground + 12-operator F1–F12 rail / axis row +
compact 4-reel zip dial + z-pad. QSplitter between terminal and middle ground. Shell tint +
working 4-dial zip display in revelator. No wiring between cockpit and canvas yet — by design.
