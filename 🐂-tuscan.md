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
    cellSize: number               // D unit (default: 48px)
    gridVisible: boolean
    snapToGrid: boolean
    showZips: 'always' | 'hover' | 'selected' | 'never'
  }
}

type CellCoord = `${number},${number}`  // "x,y" string keys
```

**Cell Properties:**
- Each cell holds: character, emoji, or empty
- Cells are addressable via `🐂📍 x y` in SCL
- Character-per-cell for grid-perfect layouts
- Emoji-per-cell for visual markers

**Stroke Properties:**
- Array of `{x, y, pressure, timestamp}` points
- Pressure-sensitive (stylus support)
- Floats above grid (no snap)
- Rendered as smooth curves

---

### 🐂🏛📍🔵 - Block Model.parti

8 fundamental block types — bounded containers that can DO things.

```typescript
interface Block {
  id: BlockId                      // UUID v4
  type: BlockType                  // One of 8 types
  name: string                     // Display name
  zip: ZipCode                     // Semantic address
  
  // Geometry
  position: { x: number, y: number }     // Top-left cell coord
  size: { width: number, height: number } // In cells
  
  // State
  state: BlockState
  locked: boolean
  visible: boolean
  
  // Content (type-specific)
  content: BlockContent
  
  // Connections
  connections: Connection[]
  
  // Metadata
  created: Timestamp
  modified: Timestamp
  author: UserId
  version: number
}

type BlockType = 
  | 'text'      // 📝 Formatted documents, notes
  | 'table'     // 📊 Rows/columns, structured data
  | 'form'      // 📋 Interactive input fields
  | 'code'      // 💻 SCL or Python execution
  | 'media'     // 🖼 Images, video, embedded
  | 'tool'      // 🛠 Widgets, calculators, utilities
  | 'composite' // 📦 Contains other blocks
  | 'reference' // 🔗 Points to another block

type BlockState = 
  | 'created'     // Just spawned
  | 'idle'        // Waiting
  | 'executing'   // Running code/triggers
  | 'complete'    // Finished successfully
  | 'error'       // Something went wrong
  | 'paused'      // Suspended
  | 'locked'      // Protected from edits
  | 'hidden'      // Invisible but exists
```

**Block Type Specifications:**

| Type | Emoji | Grid-Bound | Can Execute | Contains |
|------|-------|------------|-------------|----------|
| Text | 📝 | Yes | No | Markdown, rich text |
| Table | 📊 | Yes | No | Cells, formulas |
| Form | 📋 | Yes | Yes | Input fields, validation |
| Code | 💻 | Yes | Yes | SCL or Python |
| Media | 🖼 | Optional | No | Images, video, audio |
| Tool | 🛠 | Yes | Yes | UI widgets, handlers |
| Composite | 📦 | Yes | Yes | Nested blocks |
| Reference | 🔗 | Yes | Yes | Proxy to target block |

---

### 🐂🏛📍🔵 - Zip Code System.parti

Semantic addresses for everything in Graph Parti.

**Standard Zip (4 dials):**
```
┌───────┬───────┬───────┬───────┐
│ Dial 1│ Dial 2│ Dial 3│ Color │
│ Order │ Type  │ Axis  │ State │
└───────┴───────┴───────┴───────┘
```

**District Zip (6 dials for parent containers):**
```
┌───────┬───────┬───────┬───────┬───────┬───────┐
│ Order │ Type  │ Axis  │ Block │ Mod   │ Color │
└───────┴───────┴───────┴───────┴───────┴───────┘
```

**Valid Zip Forms:**
```
🟡                    ← color only (bullet, status marker)
🐂🟡                  ← order + color (phase + state)
🐂🧲🟡                ← order + type + color (phase + action + state)
🐂🧲🛒🟡              ← full zip (phase + action + direction + state)
🏛🧈🔵                ← axis + block + color (lens + container + state)
♨️🟢                  ← block + color (container + state)
```

**Zip as Filename Convention:**
```
🐂🛒🐬🟡 Subject.parti     ← Full zip + descriptive name
🐂🧲🟡 Notes.parti         ← Partial zip + name
🟡 Draft.parti            ← Color only + name
```

**Color Termination Rule:**
- Color MUST be the last position in any zip with content
- `🐂🧲🛒🟡` ✓ valid
- `🐂🟡🧲🛒` ✗ invalid (color in middle)

---

### 🐂🏛📍🔵 - District Model.parti

Logical regions containing blocks, elements, and other districts.

```typescript
interface District {
  id: DistrictId
  name: string
  zip: ZipCode
  
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
  
  // Content
  cells: Map<CellCoord, Cell>
  strokes: Stroke[]
  blocks: BlockId[]
}
```

**Trace Layers (Version):**
- Each 🧮 commit creates a trace layer
- Like architectural trace paper
- Toggle visibility to compare versions
- Copy from ghost to active

**Sheet Layers (Depth):**
- 7 Orders = 7 sheet layers
- Each sheet adds complexity
- Build on the sheet behind
- 🖼 Palladian is the final experience layer

**Page Layers (Sequential):**
- Within blocks that support pages
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
| 🧲 | capio | capture, get, receive, contain | `🧲🪡 input` — pull from user |
| 🐋 | duco | orchestrate, lead, conduct | `🐋🎼 arrangement` — compose elements |
| 🤌 | facio | act, make, execute, create | `🤌🎯 task` — execute action |
| 🧸 | fero | channel, carry, transfer | `🧸🛒 output` — carry to destination |
| ✒️ | grapho | write, record, inscribe | `✒️📝 document` — write content |
| 🦉 | logos | parse, reason, evaluate | `🦉 condition` — evaluate logic |
| 🚀 | mitto | dispatch, send, emit | `🚀🛒 result` — send output |
| 🦢 | plico | compress, fold, layer | `🦢🧬 layers` — merge/nest |
| 📍 | pono | set, place, position | `📍 x 0` — set variable |
| 👀 | specio | inspect, observe, query | `👀🎯 target` — examine block |
| 🥨 | tendo | span, stretch, extend | `🥨📐 line` — draw connection |
| 🪵 | teneo | pause, hold, retain | `🪵 1000` — wait ms |

---

### 🐂🧲📍🔵 - Color System.parti

**Color Context Vernacular v1.0** — Fixed 8 colors.

| Color | Name | State | Register | Use When |
|-------|------|-------|----------|----------|
| ⚪ | Eudaimonia | clear | Clear, honest, neutral | Baseline, truth |
| 🟡 | Play | exploring | Sandbox, draft, idea | Experimenting |
| 🟠 | Connection | connected | Warm, relational, shared | Collaborating |
| 🔴 | Passion | urgent | Urgent, intense, priority | Critical path |
| ⚫ | Order | complete | Done, archived, resolved | Finished |
| 🟣 | Magnificence | significant | Deep, significant, breakthrough | Important |
| 🔵 | Planning | structured | Organized, methodical, spec'd | Designing |
| 🟢 | Growth | active | Active, steady, progressing | Building |

**Color Behavior:**
- **Terminator**: Always last position in zips with content
- **Standalone**: Complete statement when alone
- **State marker**: Indicates current condition

---

### 🐂🧲📍🔵 - Grammar Rules.parti

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
│   ├── triggers: TriggerData[]
│   └── variables: VariableData[]
├── state
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
