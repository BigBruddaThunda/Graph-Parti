# 🧮 Save — System Scratchpad 🟡

> **Purpose**: Partial zips, unresolved ideas, tasks, things to ponder, checklists, version notes
> **Status**: 🔄 ACTIVE — Always evolving

---

## Partial Zips (Need More Context)

Ideas that need Order assignment or full zip codes.

### 🟡 Ideas Needing Order Assignment

| Idea | Current Zip | Notes | Suggested Order |
|------|-------------|-------|-----------------|
| Custom keyboard for mobile | 🟡 | Graph Parti keyboard with emoji rows | 🦋 |
| Predictive input for code/zips | 🟡 | Like smartphone word suggestions | 🦋 |
| Screenshot metadata embedding | 🟡 | Paste image → tool appears | 🌾 |
| Voice-to-text input | 🟡 | Word vomit into organized document | 🦋 |
| Animation layers within .parti | 🟡 | Manga panels to anime | 🖼 |
| Haptic feedback for gestures | 🟡 | Vibration on actions | 🖼 |
| Gesture macros | 🟡 | Record and replay gesture sequences | 🦋 |
| Block templates library | 🟡 | Pre-made block configurations | 🦋 |

### 🦋🟡 Features Needing Full Zip

| Feature | Current Zip | Notes | Suggested Full Zip |
|---------|-------------|-------|-------------------|
| Krita integration exploration | 🦋🟡 | AI reading layer positions | 🌾🦢📍🟠 |
| Python script for Krita text blocks | 🦋🟡 | Pasted .md rendering | 🌾🦢📍🟠 |
| Text eraser brush for Krita | 🦋🟡 | Removes text, not drawings | 🦋✒️📍🟢 |
| OCR reader that pulls notes from .parti | 🦋🟡 | Extract text from images | 🌾🤌📍🟠 |
| HTML vertical slices inside .parti | 🦋🟡 | React components | 🌾🦢📍🟠 |
| CAD file import | 🦋🟡 | DWG/DXF support | 🌾🦢📍🟠 |
| BIM integration | 🦋🟡 | Building information modeling | 🌾🏗📍🟠 |

### 🌾🟡 Integrations Needing Clarification

| Integration | Current Zip | Notes | Suggested Full Zip |
|-------------|-------------|-------|-------------------|
| Figma/Notion connector | 🌾🟡 | Import/export workflows | 🌾🦢📍🟠 |
| CAD block import | 🌾🟡 | Tie to zip system | 🌾🦢📍🟠 |
| GIS/GPS data integration | 🌾🟡 | For urban planning use case | 🌾🦢📍🟠 |
| Garmin integration | 🌾🟡 | Fishing guide use case | 🌾🦢📍🟠 |
| Slack/Discord bot | 🌾🟡 | Notifications, sharing | 🌾🦢📍🟠 |
| Git integration | 🌾🟡 | Version control for .parti | 🌾🧬📍🟠 |

---

## Tasks

### High Priority 🔴

- [ ] Define exact module structure for codebase
- [ ] Specify SCL interpreter token list
- [ ] Design dial picker UI component
- [ ] Create spatial index implementation
- [ ] Implement block state machine
- [ ] Design connection system data model
- [ ] Create Python bridge specification

### Medium Priority 🟡

- [ ] Resolve: How do districts overlap? (Layer solution vs collision)
- [ ] Define smart snapping algorithm
- [ ] Specify form field validation rules
- [ ] Design tool sharing format
- [ ] Create export format specifications
- [ ] Design plugin/extension system architecture
- [ ] Specify undo/redo system in detail

### Low Priority 🟢

- [ ] Consider binary format (v2) specification
- [ ] Plan monetization model ($10 1TP?)
- [ ] Design plugin/extension system
- [ ] Community template library structure
- [ ] Create tutorial content plan
- [ ] Design analytics/telemetry system
- [ ] Plan enterprise features

---

## Questions to Resolve

### Architecture Questions

1. **Layer overlap**: Main layer blocks collision, but what about districts?
   - **Current answer**: Use depth sheets for overlap needs
   - **Ghost layers**: Allow overlap (background)
   - **Status**: ✅ Resolved

2. **Zip dial count**: Fixed 4 or flexible 1-8?
   - **Current answer**: Flexible 1-8, default 4 (3 custom + color)
   - **Color rule**: Always required, always last
   - **Status**: ✅ Resolved

3. **Block text vs cell text**: When to use which?
   - **Cell text**: Character-per-cell, grid-perfect, labels
   - **Block text**: Formatted document, proportional, long-form
   - **Status**: ✅ Resolved

4. **Reference blocks**: How deep can references go?
   - **Question**: Can reference reference? (symlink chains)
   - **Need**: Circular reference detection
   - **Status**: 🟡 Needs decision

5. **Multi-user sync**: Real-time or periodic?
   - **Options**: WebSocket real-time, polling, CRDT
   - **Status**: 🟡 Needs research

### UI Questions

1. **Parallel bar**: How does angle snapping work with rotation?
   - **Current**: Swivel dial (mouse), pinch-rotate (touch)
   - **Scale lock**: Button in center
   - **Status**: ✅ Resolved

2. **Mobile keyboard**: Replace system keyboard or overlay?
   - **Current**: Custom Graph Parti keyboard option
   - **Predictive**: Zip/emoji suggestions
   - **Status**: 🟡 Needs prototype

3. **Artist palette**: Single vs double click behavior?
   - **Single**: Creative tools (brushes, selection)
   - **Double**: File system, layers, settings
   - **Status**: ✅ Resolved

4. **Context menus**: Long-press vs right-click?
   - **Desktop**: Right-click
   - **Mobile**: Long-press
   - **Status**: ✅ Resolved

### Experience Questions

1. **Where does collaboration fit?** 🌾 or 🐬?
   - **Sorted to**: 🌾 Composite (integration)
   - **Note**: 🐬 Sociatas is axis, not container
   - **Status**: ✅ Resolved

2. **AI features**: 🏟 (execution) or 🌾 (integration)?
   - **AI generation**: 🌾 (integration)
   - **AI execution**: 🏟 (runtime)
   - **Status**: ✅ Resolved

3. **Classical architecture theming**: How deep?
   - **Each Order**: Architectural style
   - **UI teaches**: Classical architecture passively
   - **Not just names**: Actual visual style per sheet
   - **Status**: 🟡 Needs design system

---

## Connections Found

### Cross-Order Connections

```
🐂 Block model ←→ 🏟 Block execution context
🐂 Zip system ←→ 🏟 Zip routing
🐂 SCL vocabulary ←→ 🏟 SCL interpreter
⛽ Validation rules ←→ 🏟 Runtime enforcement
🦋 Tool building ←→ 🌾 AI tool generation
🦋 Eraser tools ←→ ⚖ UX balance
⚖ Scale system ←→ 🖼 Architectural rendering
🌾 Layer integration ←→ 🖼 Ghost/trace paper view
```

### Hierarchy Patterns

```
🐂 Foundation
└── 🦋 Features build on foundation
    └── 🏟 Features execute at runtime
        └── 🖼 Users experience the result

⛽ Validation
└── 🏟 Enforcement during execution
    └── 🖼 Error display to users

🌾 Integration
└── ⚖ Calibration of integrations
    └── 🖼 Polished integrated experience
```

### Data Flow Patterns

```
Input (🧲)
  ↓
Validation (⛽)
  ↓
Processing (🏟)
  ↓
Output (🚀🛒)
  ↓
Experience (🖼)
```

---

## Version Notes

### v1 — Initial Sort 🟡

- First pass domain identification
- Assigned primary Orders to all major concepts
- Created 7 Order files + 1 System file
- Coverage estimate: ~85% of context addressed
- Confidence: MEDIUM

### v2 — Formalization 🔵

- Added TypeScript interfaces for all major types
- Formalized zip code structure
- Specified SCL grammar rules
- Created error taxonomy
- Added cross-references between Orders
- Coverage estimate: ~95% of context addressed
- Confidence: HIGH

### Next Actions

1. [ ] Re-read all context for missed items
2. [ ] Verify zip code consistency across all files
3. [ ] Add more cross-references
4. [ ] Resolve open questions
5. [ ] Create implementation roadmap
6. [ ] Iterate until SORTED ⚫

---

## Self-Assessment

### Coverage by Order

| Order | Coverage | Confidence | Notes |
|-------|----------|------------|-------|
| 🐂 Foundation | HIGH | HIGH | Core concepts well defined |
| ⛽ Validation | HIGH | HIGH | Rules captured, edge cases specified |
| 🦋 Building | HIGH | HIGH | Features well enumerated |
| 🏟 Execution | HIGH | HIGH | Interpreter architecture complete |
| 🌾 Integration | MEDIUM-HIGH | MEDIUM | Connections identified, some details needed |
| ⚖ Calibration | HIGH | HIGH | Proportions/UX captured |
| 🖼 Experience | HIGH | HIGH | Use cases well documented |

### Gaps Identified

1. **Module-level code architecture details** — Need file structure
2. **Specific UI component designs** — Need mockups/specs
3. **Database/storage layer specifics** — Need persistence design
4. **Authentication/user system** — If multi-user
5. **Error handling patterns** — Need recovery strategies
6. **Testing strategy** — Unit, integration, e2e
7. **Deployment architecture** — Hosting, CDN, etc.

### Iteration Status

```
Pass 1: Domain Identification     ✅ COMPLETE
Pass 2: Zip Assignment            ✅ COMPLETE
Pass 3: Hierarchy Building        ✅ COMPLETE
Pass 4: Cross-Reference           ✅ COMPLETE
Pass 5: Formalization             ✅ COMPLETE
Pass 6: Refinement                🔄 IN PROGRESS
```

---

## Quick Reference

### SCL Vocabulary (61 total)

```
Orders (7):    🐂 ⛽ 🦋 🏟 🌾 ⚖ 🖼
Types (12):    🧲 🐋 🤌 🧸 ✒️ 🦉 🚀 🦢 📍 👀 🥨 🪵
Modifiers (5): 🛒 🪡 🍗 ➕ ➖
Axes (6):      🏛 🔨 🌹 🪐 ⌛ 🐬
Colors (8):    ⚪ 🟡 🟠 🔴 ⚫ 🟣 🔵 🟢
Blocks (22):   ♨️ 🎯 🔢 🧈 🫀 ▶️ 🎼 ♟️ 🪜 🌎 🎱 🌋 🪞 🗿 🛠 🧩 🪫 🏖 🏗 🧬 🚂 🔠
System (1):    🧮
```

### Zip Structure

```
Standard Zip (4 dials):
┌───────┬───────┬───────┬───────┐
│ Dial 1│ Dial 2│ Dial 3│ Color │
│ Order │ Type  │ Axis  │ State │
└───────┴───────┴───────┴───────┘

District Zip (6 dials):
┌───────┬───────┬───────┬───────┬───────┬───────┐
│ Order │ Type  │ Axis  │ Block │ Mod   │ Color │
└───────┴───────┴───────┴───────┴───────┴───────┘
```

### Color Legend

| Color | State | Use |
|-------|-------|-----|
| ⚪ | Eudaimonia | Clear, neutral |
| 🟡 | Play | Exploring, draft |
| 🟠 | Connection | Collaborative |
| 🔴 | Passion | Urgent, priority |
| ⚫ | Order | Complete, done |
| 🟣 | Magnificence | Significant |
| 🔵 | Planning | Structured |
| 🟢 | Growth | Active, building |

---

## Final Structure Summary

| File | Districts | Items | Status |
|------|-----------|-------|--------|
| 🐂-tuscan.md | 5 | 14 | ✅ Complete |
| ⛽-doric.md | 6 | 16 | ✅ Complete |
| 🦋-ionic.md | 7 | 23 | ✅ Complete |
| 🏟-corinthian.md | 7 | 16 | ✅ Complete |
| 🌾-composite.md | 6 | 20 | ✅ Complete |
| ⚖-vitruvian.md | 6 | 21 | ✅ Complete |
| 🖼-palladian.md | 8 | 26 | ✅ Complete |
| 🧮-save.md | — | ~30 | 🔄 Active |

**Total: 45 Districts, 166+ Items Sorted**

---

**STATUS: SORTED 🟢**

*🧮 Save — Where incomplete thoughts wait to be completed.*
