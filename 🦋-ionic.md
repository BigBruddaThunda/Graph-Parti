# 🦋 Ionic — Building 🟢

> **Domain**: Features in progress, iterations, accumulating functionality
> **Phase**: 3 of 7 — The volute that grows and accumulates
> **Architectural Style**: Elegant, growing, iterative

---

## 🦋📍🏛🧈➕🟢 Canvas Features District

Core canvas interaction and manipulation features.

### 🦋🏛📍🟢 - Pan and Zoom.parti

```typescript
interface ViewportControls {
  // Pan
  pan: {
    gesture: 'drag' | 'two-finger'  // Mouse: drag, Touch: two-finger
    inertia: boolean               // Smooth deceleration
    boundary: 'infinite' | 'soft'  // No bounds vs elastic
  }
  
  // Zoom
  zoom: {
    gesture: 'pinch' | 'wheel' | 'buttons'
    min: 0.1    // 10%
    max: 10.0   // 1000%
    step: 0.1   // Increment
    centerOnCursor: true  // Zoom to mouse position
  }
  
  // Rotation (optional)
  rotation: {
    enabled: boolean
    gesture: 'two-finger-rotate'
    snap: [0, 90, 180, 270]  // Snap angles
  }
}
```

**Zoom Level Behaviors:**

| Zoom | Visual Detail | Interaction |
|------|---------------|-------------|
| 0.1x - 0.5x | Colored rectangles + zip emoji only | Navigation only |
| 0.5x - 1x | Rectangle + title + zip | Organize mode |
| 1x - 2x | Full content, normal | Standard editing |
| 2x - 5x | Full + details + controls | Detailed editing |
| 5x - 10x | Full fidelity, editing UI | Precision work |

---

### 🦋🏛📍🟢 - Grid Toggle.parti

```typescript
interface GridSystem {
  // Visibility
  visible: boolean
  toggleKey: 'g'           // Keyboard shortcut
  toggleGesture: 'triple-tap'
  
  // Style
  style: {
    color: '#e0e0e0'
    opacity: 0.5
    lineWidth: 1
  }
  
  // Adaptive
  fadeAtZoom: 0.3          // Fade out when zoomed far
  autoHide: true           // Hide when not needed
}
```

**Grid Philosophy:**
- Structure without tyranny
- Grid disappears when not needed
- Always there when you need precision

---

### 🦋🏛📍🟢 - Selection System.parti

```typescript
interface SelectionSystem {
  // Selection modes
  modes: {
    single: 'tap'
    region: 'drag-lasso'
    additive: 'shift-click' | 'ctrl-click'
    subtractive: 'alt-click'
  }
  
  // Selection types
  types: ['cell', 'stroke', 'block', 'district', 'mixed']
  
  // Visual feedback
  highlight: {
    color: '#4a90d9'
    opacity: 0.3
    borderWidth: 2
    animate: true
  }
  
  // Actions on selection
  actions: ['move', 'resize', 'delete', 'group', 'zip', 'copy', 'paste']
}
```

**Selection Gestures:**

| Gesture | Action |
|---------|--------|
| Tap | Select single element |
| Drag | Lasso select region |
| Shift + click | Add to selection |
| Ctrl/Cmd + click | Toggle in selection |
| Double-tap | Select block + enter edit |
| Long-press | Context menu |

---

### 🦋🏛📍🟢 - Undo System.parti

```typescript
interface UndoSystem {
  stackSize: 50            // MAX_UNDO_STACK
  
  // Action types that add to stack
  destructiveActions: [
    'create',
    'delete',
    'move',
    'resize',
    'edit',
    'zip-change',
    'connection-add',
    'connection-remove'
  ]
  
  // Stack management
  coalesceWindow: 500      // ms — combine rapid actions
  maxStackSize: 50
  
  // Gestures
  undoGesture: 'shake'     // Mobile
  undoKey: 'ctrl+z'        // Desktop
  redoKey: 'ctrl+shift+z'
}
```

**Undo Philosophy:**
- Nothing is precious when undo exists
- Encourage experimentation
- 50 actions = deep enough for real work

---

## 🦋📍🔨🧈➕🟢 Input Features District

### 🦋🔨📍🟢 - Double-Tap to Type.parti

```typescript
interface TextInput {
  // Activation
  trigger: 'double-tap'
  doubleTapDelay: 300      // ms (DOUBLE_TAP_DELAY)
  
  // Behavior
  preventsAccidental: true // Won't trigger on scroll
  mobileFirst: true        // Designed for touch
  
  // Keyboard
  keyboard: {
    type: 'system' | 'custom'
    customLayout: 'emoji-rows'  // Graph Parti keyboard
    predictive: true
  }
}
```

**Why Double-Tap:**
- Prevents accidental keyboard popup during pan
- Intentional action = intentional result
- Mobile-first consideration

---

### 🦋🔨📍🟢 - Stylus Drawing.parti

```typescript
interface DrawingSystem {
  // Input
  supports: ['stylus', 'finger', 'mouse']
  pressureSensitive: true
  tiltSensitive: true      // For advanced styluses
  
  // Canvas behavior
  canvasLocksDuringDraw: true
  
  // Stroke properties
  stroke: {
    smoothing: 0.5         // 0-1, curve smoothing
    minDistance: 2         // Min points per pixel
    maxPoints: 1000        // Per stroke
  }
  
  // Tools
  tools: ['pen', 'pencil', 'marker', 'eraser']
}
```

**Stroke Data Structure:**
```typescript
interface Stroke {
  id: StrokeId
  points: Point[]          // {x, y, pressure, timestamp}
  style: {
    color: Color
    width: number
    opacity: number
  }
  bounds: Bounds
}
```

---

### 🦋🔨📍🟢 - Paste Handling.parti

```typescript
interface PasteSystem {
  // Auto-detection
  detectContentType: true
  
  // Formatting
  columnWidth: 40          // COLUMN_WIDTH for text wrap
  autoFormat: true
  
  // Margins
  margin: {
    top: 1     // cells
    bottom: 1
    left: 1
    right: 1
  }
  
  // Block creation
  createBlock: true        // Wrap paste in block
  blockType: 'auto'        // Detect from content
}
```

**Paste Flow:**
```
Paste Event
    ↓
Detect Content Type
    ↓
Create Appropriate Block
    ↓
Format Content
    ↓
Position at Cursor/Selection
    ↓
Add Margins
```

---

### 🦋🔨📍🟢 - Text Block Modes.parti

Two modes of text in Graph Parti:

**Cell Text:**
- Character-per-cell
- Grid-perfect alignment
- Use for: labels, annotations, short text
- Fixed to grid coordinates

**Block Text:**
- Formatted document inside grid container
- Proportional font
- Use for: long-form content, markdown, notes
- Container snaps to grid, content flows freely

```typescript
interface TextModes {
  cellText: {
    binding: 'per-cell'
    font: 'monospace'
    alignment: 'center'
    useCase: 'labels, annotations'
  }
  
  blockText: {
    binding: 'container'
    font: 'proportional'
    format: 'markdown'
    useCase: 'documents, notes'
  }
}
```

**Conversion:**
- Click cell → "Make Block" = convert to block text
- Paste long text → auto-becomes block

---

## 🦋📍✒️🧈➕🟢 Eraser Tools District

### 🦋✒️📍🟢 - Line Eraser.parti

```typescript
interface LineEraser {
  // Mode
  mode: 'stroke' | 'segment'
  
  // Behavior
  affects: ['strokes']     // Only strokes, not text
  detectThreshold: 10      // Pixels from line
  
  // Input
  input: 'stylus' | 'finger'
  
  // Visual
  preview: true            // Show what will erase
  cursor: 'circle'         // Eraser cursor
}
```

**Usage:**
- Stylus/brush mode
- Drag across strokes to erase
- Only affects drawn lines, not text

---

### 🦋✒️📍🟢 - Text Eraser.parti

```typescript
interface TextEraser {
  // Mode
  mode: 'strikethrough'
  
  // Behavior
  gesture: 'drag-across-letters'
  effect: 'delete-on-release'
  
  // Visual
  strikethroughStyle: {
    color: '#ff0000'
    width: 2
  }
  
  // Comparison
  fasterThan: 'select-backspace'
}
```

**Why It Works:**
- Like crossing out words on paper
- Natural gesture
- Faster than select → backspace

---

### 🦋✒️📍🟢 - Snippet Eraser.parti

```typescript
interface SnippetEraser {
  // Target
  target: 'pasted-content'
  
  // Selection
  select: 'tap-block' | 'lasso'
  
  // Action
  action: 'delete-entire-snippet'
  
  // Use case
  useCase: 'remove pasted document quickly'
}
```

---

## 🦋📍🧲🧈➕🟢 Block Features District

### 🦋🧲📍🟢 - Block Creation.parti

| Action | Creates | Block Type |
|--------|---------|------------|
| Paste text | Text Block | 📝 |
| Paste table | Table Block | 📊 |
| Paste image | Media Block | 🖼 |
| Paste code | Code Block | 💻 |
| Toolbar create | Empty block | User selects |
| AI generate | Appropriate type | AI determines |
| Group selection | Composite Block | 📦 |
| Reference another | Reference Block | 🔗 |

```typescript
interface BlockCreation {
  // Methods
  methods: {
    paste: 'auto-detect-type'
    toolbar: 'select-type-first'
    ai: 'prompt → generate'
    group: 'selection → composite'
    reference: 'target → proxy'
  }
  
  // Defaults
  defaultSize: { width: 4, height: 4 }
  defaultZip: '🟡'
  defaultPosition: 'cursor-location'
}
```

---

### 🦋🧲📍🟢 - Block Editing.parti

```typescript
interface BlockEditing {
  // Move
  move: {
    gesture: 'drag'
    snap: 'grid'
    constraints: 'collision-check'
  }
  
  // Resize
  resize: {
    gesture: 'drag-edge-or-corner'
    snap: 'grid'
    minSize: { width: 1, height: 1 }
  }
  
  // Edit content
  editContent: {
    gesture: 'double-click'
    mode: 'type-specific'
  }
  
  // Change zip
  changeZip: {
    gesture: 'dial-picker'
    location: 'center-of-selection'
  }
  
  // Lock/unlock
  lock: {
    gesture: 'context-menu' | 'lock-button'
    confirmation: false
  }
}
```

---

### 🦋🧲📍🟢 - Block Full-Screen.parti

```typescript
interface FullScreenMode {
  // Activation
  trigger: 'double-click-block'
  
  // Behavior
  focusMode: true
  differentFromZoom: true
  
  // UI changes
  toolbar: 'document-specific'
  context: 'block-only'
  
  // Exit
  exitGesture: 'escape-key' | 'double-click-outside'
}
```

**Full-Screen vs Zoom:**
- Zoom: Still see surrounding context
- Full-screen: Block becomes entire viewport
- Different toolbars appear

---

### 🦋🧲📍🟢 - Block Scaling.parti

```typescript
interface BlockScaling {
  // Unit system
  unit: 'D'                 // Base cell unit
  D: 48                     // pixels (default)
  
  // Scale variants
  variants: {
    '1/8D': 6              // Pixel art
    '1/4D': 12
    '1/2D': 24
    '1D': 48               // Default
    '2D': 96
  }
  
  // Behavior
  proportional: true
  autoResize: true          // Grow with content
  snapToGrid: true
}
```

---

## 🦋📍📍🧈➕🟢 Zip Features District

### 🦋📍📍🟢 - Dial Picker.parti

```typescript
interface DialPicker {
  // Activation
  trigger: 'select-block → zip-button'
  
  // UI
  dials: 4                  // Default (3 custom + 1 color)
  location: 'center-of-selection'
  
  // Customization
  customEmojis: true        // Per project
  emojiCategories: ['orders', 'types', 'modifiers', 'axes', 'blocks']
  
  // Interaction
  spin: 'click-arrow' | 'swipe' | 'scroll'
  preview: true             // Show zip as you spin
}
```

---

### 🦋📍📍🟢 - Zip Evolution.parti

Zips grow over time as understanding deepens:

```
Day 1:  [_ _ _ 🟡]      ← just color (exploring)
Day 7:  [🌱 _ _ 🟡]     ← add dial 1 (category)
Day 14: [🌱 📝 _ 🟡]    ← add dial 2 (type)
Day 30: [🌱 📝 🏛 🔵]   ← full zip + color change (structured)
```

**Evolution Philosophy:**
- Start simple, grow complex
- Color changes as state changes
- Zips tell the story of development

---

### 🦋📍📍🟢 - Zip Queries.parti

```typescript
interface ZipQuery {
  // Query patterns
  patterns: {
    allUrgent: '[_ _ _ 🔴]'
    allInitPhase: '[🐂 _ _ _]'
    allCapture: '[_ 🧲 _ _]'
    allStructure: '[_ _ 🏛 _]'
  }
  
  // Results
  highlight: true           // Highlight matching on canvas
  select: true              // Select all matches
  navigate: true            // Jump to first match
  
  // Wildcards
  wildcard: '_'             // Matches any
}
```

**Query Examples:**
```
[_ _ _ 🔴]     → All urgent items
[🐂 _ _ _]     → All foundation phase
[_ 🧲 _ _]     → All capture operations
[_ _ 🏛 _]     → All structure lens
[🐂 🧲 🏛 🔵]  → Exact match
```

---

### 🦋📍📍🟢 - Snap to Zip.parti

```typescript
interface SnapToZip {
  // Activation
  trigger: 'snap-to-zip-button'
  
  // Behavior
  gather: true              // Bring same-zip content together
  group: true               // Group for drag
  highlight: true           // Auto-highlight zip regions
  
  // Layout
  layout: 'grid' | 'cluster' | 'original-positions'
}
```

---

## 🦋📍🛠🧈➕🟢 Tool Building District

### 🦋🛠📍🟢 - Tool from Selection.parti

```typescript
interface ToolFromSelection {
  // Creation
  select: 'blocks'          // Select blocks to convert
  save: 'as-tool'
  
  // Tool properties
  properties: {
    inputs: InputDef[]      // Define inputs
    outputs: OutputDef[]    // Define outputs
    reusable: true          // Across projects
  }
  
  // Export/Import
  format: '.parti-snippet'
  shareable: true
}
```

---

### 🦋🛠📍🟢 - AI Tool Generation.parti

```typescript
interface AIToolGeneration {
  // Prompt
  prompt: string            // "Make me a calculator"
  
  // Generation
  aiBuilds: 'SCL + Python'
  output: 'Tool block on canvas'
  
  // Iteration
  iterate: 'feedback-loop'
  refine: 'natural-language'
  
  // Examples
  examples: [
    'Make me a calculator',
    'Create a todo list widget',
    'Build a unit converter'
  ]
}
```

---

### 🦋🛠📍🟢 - Slash Commands.parti

```typescript
interface SlashCommands {
  // Syntax
  syntax: '/command argument'
  
  // Built-in commands
  builtIn: [
    '/directory',           // List all commands
    '/save',                // Save file
    '/export',              // Export options
    '/undo',                // Undo last action
    '/search',              // Search canvas
    '/zip',                 // Set zip on selection
  ]
  
  // Custom commands
  custom: true              // User can create
  projectSpecific: true     // Per .parti file
}
```

---

## 🦋📍🪜🧈➕🟡 Development Roadmap District

### 🦋🪜📍🟡 - Phase Progress.parti

| Phase | Status | Features | Zip |
|-------|--------|----------|-----|
| 1. Foundation | ✅ Complete | Canvas, text, drawing, selection, undo | 🐂 |
| 2. Tables & MD | 🔄 In Progress | Table paste, markdown rendering | 🦋 |
| 3. Forms | 📋 Planned | Interactive form builder | 🦋 |
| 4. AI Cleanup | 📋 Planned | Select + prompt → structure | 🌾 |
| 5. Color & Fill | 📋 Planned | Paint bucket, pixel art | 🦋 |
| 6. Layers | 📋 Planned | Content + version layers | 🌾 |
| 7. Versions (🧮) | 📋 Planned | Ghost/trace paper mode | 🧮 |
| 8. Scale & Drafting | 📋 Planned | Pixel mapping, parallel bar | ⚖ |
| 9. Block Library | 📋 Planned | Reusable blocks | 🦋 |
| 10. Export | 📋 Planned | .parti, PNG, PDF, MD | 🖼 |
| 11. Zip System | 📋 Planned | Dial canvas, tagging, queries | 🐂 |
| 12. Collaboration | 📋 Planned | Cloud sync, form workflows | 🌾 |
| 13. AI Integration | 📋 Planned | Procedural generation | 🌾 |

**Status Legend:**
- ✅ Complete
- 🔄 In Progress
- 📋 Planned
- 🟡 Exploring

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| 🦋 Building | 🐂 Foundation | Builds on foundation |
| 🦋 Building | 🏟 Execution | Features execute at runtime |
| 🦋 Building | ⚖ Calibration | Features get refined |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| Canvas Features | 🦋📍🏛🧈➕🟢 | 4 | ✅ Complete |
| Input Features | 🦋📍🔨🧈➕🟢 | 4 | ✅ Complete |
| Eraser Tools | 🦋📍✒️🧈➕🟢 | 3 | ✅ Complete |
| Block Features | 🦋📍🧲🧈➕🟢 | 4 | ✅ Complete |
| Zip Features | 🦋📍📍🧈➕🟢 | 4 | ✅ Complete |
| Tool Building | 🦋📍🛠🧈➕🟢 | 3 | ✅ Complete |
| Development Roadmap | 🦋📍🪜🧈➕🟡 | 1 | 🟡 Active |

**Total: 23 items across 7 districts**

---

*🦋 Ionic — The volute that grows, accumulates, and builds.*
