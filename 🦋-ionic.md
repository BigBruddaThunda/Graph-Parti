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
@@ -135,51 +135,51 @@ interface UndoSystem {
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
@@ -287,51 +287,51 @@ Two modes of text in Graph Parti:

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
@@ -365,51 +365,51 @@ interface TextEraser {
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
  
@@ -493,51 +493,51 @@ interface FullScreenMode {

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
@@ -588,51 +588,51 @@ interface ZipQuery {
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
@@ -664,80 +664,80 @@ interface AIToolGeneration {
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