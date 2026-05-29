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

## Status (this build)
Base shape only: split-pane host, color-shell tint, working 4-dial zip dial, zip
field, 12 operators (F1–F12), axis row + copper plate, Z-pad. No wiring between the
cockpit and the canvas yet — by design.
