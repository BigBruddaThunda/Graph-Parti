# 🐂 Tuscan — Foundation 🔵

> **Domain**: Core definitions, init concepts, base architecture, what things ARE
> **Phase**: 1 of 7 — The ground upon which all else stands
> **Architectural Style**: Simple, foundational, sturdy

---

## 🐂📍🏛🧈➕🔵 Core Architecture District

Parent container for all foundational structural definitions. Everything in Graph Parti rests on these primitives.

### 🐂🏛📍🔵 - Canvas Primitives.parti

The infinite 2D coordinate space where all content lives.

```typescript
interface Canvas {
  // Coordinate system
  cells: Map<CellCoord, Cell>      // Grid-based content
  strokes: Stroke[]                // Freehand drawings (float above grid)
  blocks: Map<BlockId, Block>      // Bounded containers
  districts: District[]            // Logical groupings
  
  // Viewport
  viewport: {
    x: number                      // Pan X offset
    y: number                      // Pan Y offset
    zoom: number                   // Scale factor (0.1x to 10x)
    rotation: number               // Canvas rotation (degrees)
  }
  
  // Configuration
  config: {
@@ -181,51 +181,51 @@ interface District {
  // Geometry
  bounds: Bounds           // Rectangle or polygon
  
  // Contents
  blocks: BlockId[]        // Direct children
  elements: ElementId[]    // Cells, strokes
  districts: DistrictId[]  // Nested districts
  
  // Behavior
  locked: boolean          // Becomes block-like when locked
  visible: boolean
  opacity: number          // For ghost/trace layers
  
  // Styling
  style: {
    fill: Color
    stroke: Color
    strokeWidth: number
    labelPosition: 'center' | 'top' | 'bottom'
  }
}
```

**District Hierarchy:**
```
🐂📍🏛🧈➕🔵 Core Architecture (PARENT)
├── 🐂🏛📍🔵 Canvas primitives
├── 🐂🏛📍🔵 Block model
├── 🐂🏛📍🔵 Zip code system
├── 🐂🏛📍🔵 District model
└── 🐂🏛📍🔵 Layer architecture
```

---

### 🐂🏛📍🔵 - Layer Architecture.parti

Three layer types for organizing content across dimensions.

```typescript
type LayerType = 'trace' | 'sheet' | 'page'

interface Layer {
  id: LayerId
  type: LayerType
  name: string
  order: number           // Z-index / stacking order
  visible: boolean
  opacity: number         // 0.0 - 1.0
  locked: boolean
  
@@ -253,51 +253,51 @@ interface Layer {
- Text blocks: pages of content
- Code blocks: multiple scripts
- Form blocks: multi-step forms

**Layer Stack:**
```
┌─────────────────────────────────┐
│  🖼 Palladian (Experience)       │ ← Top
├─────────────────────────────────┤
│  ⚖ Vitruvian (Calibration)      │
├─────────────────────────────────┤
│  🌾 Composite (Integration)     │
├─────────────────────────────────┤
│  🏟 Corinthian (Execution)      │
├─────────────────────────────────┤
│  🦋 Ionic (Building)            │
├─────────────────────────────────┤
│  ⛽ Doric (Validation)          │
├─────────────────────────────────┤
│  🐂 Tuscan (Foundation)         │ ← Bottom
└─────────────────────────────────┘
```

---

## 🐂📍🧲🧈➕🔵 SCL Language Core District

The Semantic Compression Language — 61 emojis as semantic anchors.

### 🐂🧲📍🔵 - 61 Emoji Vocabulary.parti

| Category | Count | Emojis | Purpose |
|----------|-------|--------|---------|
| **Orders** | 7 | 🐂 ⛽ 🦋 🏟 🌾 ⚖ 🖼 | Developmental phase |
| **Types** | 12 | 🧲 🐋 🤌 🧸 ✒️ 🦉 🚀 🦢 📍 👀 🥨 🪵 | Action verbs |
| **Modifiers** | 5 | 🛒 🪡 🍗 ➕ ➖ | Direction/operation |
| **Axes** | 6 | 🏛 🔨 🌹 🪐 ⌛ 🐬 | Dimensional lenses |
| **Colors** | 8 | ⚪ 🟡 🟠 🔴 ⚫ 🟣 🔵 🟢 | State/tone |
| **Blocks** | 22 | ♨️ 🎯 🔢 🧈 🫀 ▶️ 🎼 ♟️ 🪜 🌎 🎱 🌋 🪞 🗿 🛠 🧩 🪫 🏖 🏗 🧬 🚂 🔠 | Process containers |
| **System** | 1 | 🧮 | Scratchpad/save |

**Total: 61 canonical emojis**

---

### 🐂🧲📍🔵 - Type Operators.parti

Latin/Greek roots for action verbs.

| Emoji | Root | Meaning | Code Usage |
|-------|------|---------|------------|
@@ -343,56 +343,56 @@ Latin/Greek roots for action verbs.
**Principle 1: Emoji Precedes Word**
```
🐂 init          ← correct
init 🐂          ← incorrect
```

**Principle 2: Context Determines Meaning**
The same emoji means different things in different contexts:
```
🐂 in code:     init, declare, define
🐂 in convo:    "starting," "naming pieces"
🐂 as header:   "this section initializes"
```

**Principle 3: Grammar Guides, Doesn't Police**
Rules describe how the language tends to work — not the only way.

**Principle 4: Color Terminates**
Every complete thought ends with a color. Colors mark state.

**Principle 5: Partial Zips Valid**
```
🟡              ← valid (idea, untagged)
🐂🟡            ← valid (foundation idea)
🐂🏛🟡          ← valid (foundation structure idea)
🐂📍🏛🧈➕🟡        ← valid (foundation structure core idea)
```

---

## 🐂📍🔨🧈➕🔵 .parti File Format District

### 🐂🔨📍🔵 - File Structure.parti

```
.parti file (JSON v1)
├── header
│   ├── id: UUID
│   ├── name: string
│   ├── version: "1.0.0"
│   ├── created: ISO8601
│   └── modified: ISO8601
├── config
│   ├── cellSize: number (default: 48)
│   ├── dialSystem: DialConfig
│   └── theme: ThemeConfig
├── canvas
│   ├── cells: CellData[]
│   ├── strokes: StrokeData[]
│   └── viewport: ViewportState
├── content
│   ├── blocks: BlockData[]
│   ├── districts: DistrictData[]
│   └── layers: LayerData[]
├── logic
│   ├── connections: ConnectionData[]
@@ -402,129 +402,129 @@ Every complete thought ends with a color. Colors mark state.
│   ├── runtime: RuntimeState
│   └── history: ActionHistory[]
├── tools
│   └── embeddedTools: ToolData[]
├── history
│   └── commits: CommitData[]
└── assets
    └── media: MediaData[]
```

---

### 🐂🔨📍🔵 - Content Types.parti

| Type | Grid-Bound | Description | Use Case |
|------|------------|-------------|----------|
| Cells | Yes | Single char/emoji per cell | Labels, annotations |
| Strokes | No (floats) | Hand-drawn lines | Sketches, diagrams |
| Tables | Yes (area) | Rows/columns of data | Structured content |
| Forms | Yes (area) | Interactive fields | User input |
| Images | Optional | Embedded media | References, traces |
| Blocks | Yes | Bounded containers | Everything else |

---

## 🐂📍🪐🧈➕🔵 Core Principles District

### 🐂🪐📍🔵 - Design Philosophy.parti

**Hand + Computer Together**
Neither sacrificed. The tool amplifies both human creativity and computational power.

**Pixel Perfect, Grid Optional**
Snap when you want precision. Float when you want freedom.

**Infinite Canvas**
No page boundaries. Ideas expand as needed.

**Versions Not Files**
🧮 commits preserve history. One .parti contains entire project lineage.

**Layers Like Trace Paper**
Architects overlay sheets. Graph Parti overlays layers.

**Context Is Everything**
Where something is matters as much as what it is.

**Offline First, Local First**
Full functionality without connection. Cloud sync is bonus.

---

### 🐂🪐📍🔵 - The Name Meaning.parti

**Graph Parti** = Graph + Parti

- **Graph**: Grid, blocks, structure, connections
- **Parti**: Architectural sketch, essential idea, organizing concept

**Hidden Meaning:**
Graph Parti ≈ Block Party 🎉

**Tagline:**
> *"Graph Parti is Figure-Ground for your ideas."*

**Figure-Ground Interpretations:**
- Figure = figuring it out (process)
- Ground = grounding your ideas (outcome)
- Like Nolli maps — public vs private space
- Multiple depth interpretations simultaneously

---

## 🐂📍🧬🧈➕🔵 Block Lifecycle District

### 🐂🧬📍🔵 - Lifecycle States.parti

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   [Create] ──▶ [Edit] ──▶ [Lock] ──▶ [Execute] ──▶ [Archive]│
│       │         │         │           │            │        │
│       ▼         ▼         ▼           ▼            ▼        │
│    🟡 Draft   🟢 Active  🔵 Spec'd   🟠 Running   ⚫ Done   │
│                                                             │
│   [Delete] ◀── Any State (goes to 🧮 undo stack)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**State Transitions:**
| From | To | Trigger |
|------|-----|---------|
| created | idle | initialization complete |
| idle | executing | trigger fired |
| executing | complete | success |
| executing | error | failure |
| any | locked | user lock |
| any | hidden | user hide |
| any | deleted | user delete (→ undo stack) |

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| 🐂 Foundation | 🦋 Building | Foundation defines what gets built |
| 🐂 Foundation | 🏟 Execution | Foundation defines what executes |
| 🐂 Foundation | ⛽ Validation | Foundation defines what's validated |
| 🐂 Foundation | 🖼 Experience | Foundation enables the experience |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| Core Architecture | 🐂📍🏛🧈➕🔵 | 5 | ✅ Complete |
| SCL Language Core | 🐂📍🧲🧈➕🔵 | 4 | ✅ Complete |
| .parti File Format | 🐂📍🔨🧈➕🔵 | 2 | ✅ Complete |
| Core Principles | 🐂📍🪐🧈➕🔵 | 2 | ✅ Complete |
| Block Lifecycle | 🐂📍🧬🧈➕🔵 | 1 | ✅ Complete |

**Total: 14 items across 5 districts**

---

*🐂 Tuscan — The foundation upon which all Orders rest.*