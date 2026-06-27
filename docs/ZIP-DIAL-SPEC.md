# ZIP DIAL SPECIFICATION — the 4-reel instrument

> The zip dial is a mechanical-feeling 4-column instrument in the Archideck cockpit.
> Each reel shows 3 faces: top (previous), middle (active), bottom (next).
> Clicking UP scrolls the reel backward, DOWN scrolls forward.
> The reels wrap — after the last glyph, it cycles back to the first.

## Design

Each reel is a vertical column showing 3 gem-shaped faces:
- **Top face:** half-visible (clipped at the top edge), showing the PREVIOUS glyph
- **Middle face:** fully visible, the ACTIVE selection — this is the one that counts
- **Bottom face:** half-visible (clipped at the bottom), showing the NEXT glyph

The faces are faceted gem shapes (see VIEWPORT-TEMPLATE.parti):
- **Reel 1 (Operator, 12 faces):** 12-sided rosette — radiating segments like a compass rose
- **Reel 2 (Axis, 6 faces):** hexagonal gem — 6-sided with inner hexagon and facet lines
- **Reel 3 (Order, 7 faces):** heptagonal gem — 7-sided with inner heptagon
- **Reel 4 (Color, 8 faces):** octagonal gem — 8-sided with inner octagon, SOLID FILLED with the SCL color

Above and below each reel: rectangular click boxes that show the name of the
adjacent glyph. Click = spin up/down.

The whole instrument sits in a copper-bordered frame.

## Spin Sequences (wrapping circular lists)

### Reel 1: Operator (12 glyphs)
```
Sequence: 📍 🧲 🤌 👀 🐋 🧸 🚀 🥨 🦢 🦉 🪵 ✒️
```

| Active (middle) | Top (prev) | Bottom (next) |
|-----------------|-----------|---------------|
| 📍 pono | ✒️ grapho | 🧲 capio |
| 🧲 capio | 📍 pono | 🤌 facio |
| 🤌 facio | 🧲 capio | 👀 specio |
| 👀 specio | 🤌 facio | 🐋 duco |
| 🐋 duco | 👀 specio | 🧸 fero |
| 🧸 fero | 🐋 duco | 🚀 mitto |
| 🚀 mitto | 🧸 fero | 🥨 tendo |
| 🥨 tendo | 🚀 mitto | 🦢 plico |
| 🦢 plico | 🥨 tendo | 🦉 logos |
| 🦉 logos | 🦢 plico | 🪵 teneo |
| 🪵 teneo | 🦉 logos | ✒️ grapho |
| ✒️ grapho | 🪵 teneo | 📍 pono |

### Reel 2: Axis (6 glyphs)
```
Sequence: 🏛 ⌛ 🔨 🐬 🌹 🪐
```

| Active | Top | Bottom |
|--------|-----|--------|
| 🏛 Firmitas | 🪐 Gravitas | ⌛ Temporitas |
| ⌛ Temporitas | 🏛 Firmitas | 🔨 Utilitas |
| 🔨 Utilitas | ⌛ Temporitas | 🐬 Sociatas |
| 🐬 Sociatas | 🔨 Utilitas | 🌹 Venustas |
| 🌹 Venustas | 🐬 Sociatas | 🪐 Gravitas |
| 🪐 Gravitas | 🌹 Venustas | 🏛 Firmitas |

### Reel 3: Order (7 glyphs)
```
Sequence: 🐂 ⛽ 🦋 🏟 🌾 ⚖ 🖼
```

| Active | Top | Bottom |
|--------|-----|--------|
| 🐂 Tuscan | 🖼 Palladian | ⛽ Doric |
| ⛽ Doric | 🐂 Tuscan | 🦋 Ionic |
| 🦋 Ionic | ⛽ Doric | 🏟 Corinthian |
| 🏟 Corinthian | 🦋 Ionic | 🌾 Composite |
| 🌾 Composite | 🏟 Corinthian | ⚖ Vitruvian |
| ⚖ Vitruvian | 🌾 Composite | 🖼 Palladian |
| 🖼 Palladian | ⚖ Vitruvian | 🐂 Tuscan |

### Reel 4: Color (8 glyphs)
```
Sequence: ⚪ 🟡 🟠 🔴 ⚫ 🟣 🔵 🟢
```

| Active | Top | Bottom | Hex |
|--------|-----|--------|-----|
| ⚪ Eudaimonia | 🟢 Growth | 🟡 Play | #F5F5DC |
| 🟡 Play | ⚪ Eudaimonia | 🟠 Connection | #F7B731 |
| 🟠 Connection | 🟡 Play | 🔴 Passion | #F57E16 |
| 🔴 Passion | 🟠 Connection | ⚫ Order | #C1140C |
| ⚫ Order | 🔴 Passion | 🟣 Magnificence | #3C3C3C |
| 🟣 Magnificence | ⚫ Order | 🔵 Planning | #9255E5 |
| 🔵 Planning | 🟣 Magnificence | 🟢 Growth | #2464E5 |
| 🟢 Growth | 🔵 Planning | ⚪ Eudaimonia | #348219 |

**Color reel special behavior:** The gem faces on reel 4 are SOLID FILLED with the
SCL color (not outlined like the other 3 reels). The active color changes the
entire cockpit shell tint.

## Gem Face Geometry

Each gem is drawn as a polygon with facet lines:
- **12-sided (operator):** outer dodecagon + inner smaller dodecagon + 12 radial lines
- **6-sided (axis):** outer hexagon + inner hexagon + 6 radial lines
- **7-sided (order):** outer heptagon + inner heptagon + 7 radial lines
- **8-sided (color):** outer octagon + inner octagon + 8 radial lines, solid color fill

The top and bottom faces are clipped to show only the upper/lower half,
giving the impression of a rotating cylinder.
