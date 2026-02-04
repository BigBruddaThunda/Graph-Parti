# ⚖ Vitruvian — Calibration 🔵

> **Domain**: Refinement, balance, tuning, proportions, UX polish
> **Phase**: 6 of 7 — The balanced refinement before completion
> **Architectural Style**: Balanced, refined, proportional

---

## ⚖📍🏛🧈➕🔵 Proportions & Scale District

The D unit system and scaling mechanics.

### ⚖🏛📍🔵 - D Unit System.parti

```typescript
interface DUnitSystem {
  // Base unit
  D: number              // Default: 48 pixels
  
  // Everything proportional to D
  proportions: {
    cellSize: '1D'
    minStrokeWidth: '0.02D'
    defaultStrokeWidth: '0.04D'
    blockMargin: '0.25D'
    selectionHandle: '0.25D'
  }
  
  // Scale variants
  variants: {
    '1/8D': 6             // 6px — Pixel art, icons
    '1/4D': 12            // 12px — Fine detail
    '1/2D': 24            // 24px — Compact UI
    '1D': 48              // 48px — Default
    '2D': 96              // 96px — Large elements
  }
}
```

**D Unit Philosophy:**
- D = base cell size (default 48px)
- Everything proportional to D
- Scale variants for different contexts
- Parallel bar moves in D increments when locked

---

### ⚖🏛📍🔵 - Scale Settings.parti

| Scale | Cell = | Use Case | Zip |
|-------|--------|----------|-----|
| 1:8 | 8px | Pixel art, icons | 🎨 |
| 1:16 | 16px | Standard pixel art | 🎨 |
| 1:48 | 48px | UI components | 🔵 |
| 1" print | 1 inch | Print design | 🖨 |
| Device-mapped | Varies | Test actual screen | 📱 |

```typescript
interface ScaleSettings {
  // Presets
  presets: {
    pixelArt: { ratio: '1:8', D: 8 }
    standard: { ratio: '1:1', D: 48 }
    print: { ratio: '1:1', D: 96 }  // 1 inch
    device: { ratio: 'variable', D: 'screen-dependent' }
  }
  
  // Switching
  switchScale: (preset: ScalePreset) => void
  maintainContent: true  // Scale content with grid
}
```

---

### ⚖🏛📍🔵 - Document Margins.parti

```typescript
interface DocumentMargins {
  // Pasted blocks
  pasteMargins: {
    top: 1      // cells
    bottom: 1
    left: 1
    right: 1
  }
  
  // Behavior
  marginsDefine: 'block-space'
  blockGrows: true        // With content added
  spacing: 'proportional' // For readability
}
```

**Margin Behavior:**
- Pasted blocks have whitespace borders
- Margins define block space
- Block grows with content added
- Proportional spacing for readability

---

## ⚖📍🔨🧈➕🔵 Drafting Tools District

### ⚖🔨📍🔵 - Parallel Bar.parti

```typescript
interface ParallelBar {
  // Modes
  modes: ['horizontal', 'vertical']
  
  // Rotation
  rotation: {
    mouse: 'swivel-dial'
    touch: 'pinch-rotate'
    snap: [0, 15, 30, 45, 60, 75, 90]
  }
  
  // Lock
  lock: {
    toggle: 'center-button'
    whenLocked: 'moves-in-increments-only'
    increment: '1D'
  }
  
  // Visual
  appearance: 'drafting-tool-aesthetic'
  color: '#4a90d9'
  opacity: 0.7
}
```

**Parallel Bar Features:**
- Horizontal and vertical modes
- Swivel dial for rotation (mouse)
- Pinch to rotate (touch)
- Center button: scale lock toggle
- Locked: moves in set increments only
- Unlocked: free movement

---

### ⚖🔨📍🔵 - Line Tools.parti

```typescript
interface LineTools {
  // Types
  types: {
    straight: 'point-to-point'
    freehand: 'stroke-based'
    parallel: 'follows-parallel-bar-angle'
  }
  
  // Stylus behavior
  stylusSnap: true          // Auto-snaps to parallel bar angle
  
  // Line weights (like pencil grades)
  weights: {
    '2H': { width: 0.5, opacity: 0.3 }   // Very light
    '4H': { width: 0.5, opacity: 0.5 }   // Light
    'HB': { width: 1.0, opacity: 0.7 }   // Medium
    '2B': { width: 1.5, opacity: 0.9 }   // Dark
    '4B': { width: 2.0, opacity: 1.0 }   // Very dark
  }
  
  // Scale snapping
  scaleSnap: 'proportional-lines'
}
```

---

### ⚖🔨📍🔵 - Shape Tools.parti

```typescript
interface ShapeTools {
  // Basic shapes
  shapes: ['rectangle', 'circle', 'ellipse', 'polygon']
  
  // Smart recognition
  smartRecognition: {
    trigger: 'draw-messy + hold'
    converts: 'messy → perfect'
    shapes: ['circle', 'rectangle', 'line']
  }
  
  // Alignment
  autoAlign: ['grid', 'parallel-bar', 'existing-shapes']
  
  // Creation
  creation: {
    rectangle: 'drag-corner-to-corner'
    circle: 'drag-center-to-edge'
    polygon: 'click-vertices'
  }
}
```

**Smart Shape Recognition:**
- Draw messy circle + hold → perfect circle
- Auto-align to grid/line
- Makes sketching fast and clean

---

### ⚖🔨📍🔵 - Dimension Callouts.parti

```typescript
interface DimensionCallouts {
  // Types
  types: {
    linear: 'distance-between-points'
    angular: 'angle-between-lines'
    radial: 'radius-of-circle'
  }
  
  // Style
  style: 'architectural-annotation'
  
  // Display
  display: {
    value: true
    unit: true
    scale: true
  }
  
  // Export
  includeInExport: true
}
```

**Dimension Features:**
- Measurement labels
- Scale indicator displays
- Architectural annotation style
- Export includes scale

---

## ⚖📍🌹🧈➕🔵 UI Calibration District

### ⚖🌹📍🔵 - Adaptive UI per Sheet.parti

```typescript
interface AdaptiveUI {
  // Each Order sheet has different UI
  sheets: {
    '🐂': { tools: 'basic', theme: 'tuscan' }
    '⛽': { tools: 'validation', theme: 'doric' }
    '🦋': { tools: 'building', theme: 'ionic' }
    '🏟': { tools: 'execution', theme: 'corinthian' }
    '🌾': { tools: 'integration', theme: 'composite' }
    '⚖': { tools: 'calibration', theme: 'vitruvian' }
    '🖼': { tools: 'presentation', theme: 'palladian' }
  }
  
  // Principles
  noStaticUI: true
  adaptsToContext: true
  relevantActionsOnly: true
}
```

**Adaptive Behavior:**
- Each Order sheet has different tools
- Color theme per sheet
- UI layout adapts
- Relevant actions only
- No static UI—adapts to current context

---

### ⚖🌹📍🔵 - Color Theming.parti

```typescript
interface ColorTheming {
  // Base themes
  themes: {
    tuscan: { primary: '#8B7355', accent: '#D4C4A8' }
    doric: { primary: '#4A5568', accent: '#A0AEC0' }
    ionic: { primary: '#553C9A', accent: '#B794F6' }
    corinthian: { primary: '#C05621', accent: '#FBD38D' }
    composite: { primary: '#276749', accent: '#9AE6B4' }
    vitruvian: { primary: '#2C5282', accent: '#90CDF4' }
    palladian: { primary: '#744210', accent: '#F6E05E' }
  }
  
  // Color blocks affect accent
  colorBlocks: {
    '🔴': 'urgent-accent'
    '🔵': 'planning-accent'
    '🟢': 'growth-accent'
    '🟡': 'play-accent'
  }
  
  // 8 colors = 8 tonal registers
  tonalRegisters: 8
}
```

---

### ⚖🌹📍🔵 - Zoom-Level Rendering.parti

| Zoom | What Shows | Detail Level |
|------|------------|--------------|
| Very far | Colored rectangle + zip emoji | Minimal |
| Far | Rectangle + title + zip | Low |
| Medium | Full content, normal | Standard |
| Close | Full + details + controls | High |
| Very close | Full fidelity, editing UI | Maximum |

```typescript
interface ZoomLevelRendering {
  levels: {
    veryFar: { zoom: '< 0.2', detail: 'minimal' }
    far: { zoom: '0.2 - 0.5', detail: 'low' }
    medium: { zoom: '0.5 - 2', detail: 'standard' }
    close: { zoom: '2 - 5', detail: 'high' }
    veryClose: { zoom: '> 5', detail: 'maximum' }
  }
}
```

---

### ⚖🌹📍🔵 - Zip Visibility.parti

```typescript
interface ZipVisibility {
  // Show/hide behavior
  showOn: ['hover', 'tap', 'select']
  
  // Zoom behavior
  atMaxZoom: 'emoji-only'
  
  // Clutter prevention
  preventsClutter: true
  
  // Preview
  previewOnHover: true
}
```

**Zip Display:**
- Zip codes show on hover/tap/select
- At max zoom: only emoji visible
- Prevents clutter in workspace
- Preview on hover

---

## ⚖📍🪐🧈➕🔵 UX Balance District

### ⚖🪐📍🔵 - Minimal UI Philosophy.parti

```typescript
interface MinimalUI {
  // Tools hidden until needed
  toolsHidden: true
  
  // Artist palette
  palette: {
    icon: 'thumb-hole'
    singleClick: 'creative-tools'
    doubleClick: 'file-system-settings'
  }
  
  // Collapse
  collapsesWhenNotUsed: true
  collapseDelay: 3000      // ms
}
```

**Minimal UI Principles:**
- Tools hidden until needed
- Artist palette button (thumb-hole icon)
- Single click: creative tools
- Double click: file system/settings
- UI collapses when not used

---

### ⚖🪐📍🔵 - Mobile-First Considerations.parti

```typescript
interface MobileFirst {
  // Thumb reach
  thumbReachable: true
  controlsAt: 'bottom-of-screen'
  
  // Notifications
  noLongReach: true
  notifications: 'bottom'
  
  // Keyboard
  customKeyboard: 'Graph Parti keyboard'
  predictive: 'emoji-zip-input'
  
  // Gestures
  gestures: ['tap', 'double-tap', 'long-press', 'pinch', 'pan']
}
```

**Mobile Design:**
- Thumb-reachable controls (bottom of screen)
- No long reach for notifications
- Custom Graph Parti keyboard
- Predictive emoji/zip input

---

### ⚖🪐📍🔵 - Intent Separation.parti

Different modes for different intent:

| Mode | UI | Available Actions |
|------|----|--------------------|
| Canvas | Palette tools | Draw, move, create |
| Text editing | Document toolbar | Type, format |
| Block editing | Block-specific | Type-relevant tools |
| Zoomed out | Overview | Navigate, organize |

```typescript
interface IntentSeparation {
  modes: {
    canvas: { ui: 'palette', actions: ['draw', 'move', 'create'] }
    textEditing: { ui: 'document-toolbar', actions: ['type', 'format'] }
    blockEditing: { ui: 'block-specific', actions: ['edit', 'resize', 'zip'] }
    zoomedOut: { ui: 'overview', actions: ['navigate', 'organize'] }
  }
  
  // Switching
  switch: 'automatic-based-on-context'
}
```

---

### ⚖🪐📍🔵 - Lock and Move Behavior.parti

```typescript
interface LockMoveBehavior {
  // Move
  move: {
    normal: 'click-hold-drag'
    locked: 'double-click-hold-unlock-first'
  }
  
  // Lock
  lock: {
    button: 'lock-icon'
    prevents: ['edit', 'move', 'delete']
    allows: ['execute', 'trigger']
  }
  
  // Eraser
  eraser: {
    ignoresLocked: true
  }
}
```

**Lock/Move Rules:**
- Click + hold = move element
- Lock button = prevent accidental moves
- Locked elements ignore eraser
- Double-click + hold = move locked items (unlock first)

---

## ⚖📍⌛🧈➕🔵 Performance Tuning District

### ⚖⌛📍🔵 - Render Optimization.parti

```typescript
interface RenderOptimization {
  // Lazy loading
  lazyLoading: {
    enabled: true
    threshold: '2x-viewport'
  }
  
  // Spatial indexing
  spatialIndex: {
    enabled: true
    structure: 'quadtree'
  }
  
  // Visibility
  onlyRenderVisible: true
  culling: 'viewport-culling'
  
  // Memory
  memoryManagement: 'pool-frequent-allocations'
}
```

**Optimization Strategies:**
- Lazy loading for off-viewport
- Spatial indexing for fast lookups
- Only render visible content
- Memory management for large files

---

### ⚖⌛📍🔵 - Input Responsiveness.parti

```typescript
interface InputResponsiveness {
  // Timing
  doubleTapDelay: 300       // ms
  
  // Feedback
  immediateFeedback: true
  
  // Blocking
  noBlockingOperations: true
  backgroundProcessing: true
  
  // Targets
  targetFPS: 60
  minFPS: 30
}
```

**Responsiveness Targets:**
- 300ms double-tap delay
- Immediate feedback on all actions
- No blocking operations
- Background processing for heavy tasks

---

### ⚖⌛📍🔵 - File Handling.parti

```typescript
interface FileHandling {
  // Formats
  v1: 'json'                // Human-readable, development
  v2: 'binary'              // Compact, production (future)
  
  // Compression
  gzip: {
    threshold: 100_000      // Bytes
    level: 6                // 1-9
  }
  
  // Loading
  chunkedLoading: true      // For huge files
  progressIndicator: true
}
```

**File Strategy:**
- JSON format for development (readable)
- Gzip compression for >100KB
- Binary format later for production
- Chunked loading for huge files

---

## ⚖📍🎯🧈➕🔵 Classical Architecture UI District

### ⚖🎯📍🔵 - Order-Themed Sheets.parti

Each sheet styled by its Order:

| Order | Architectural Style | Visual Theme |
|-------|---------------------|--------------|
| 🐂 Tuscan | Simple, foundational | Earth tones, sturdy |
| ⛽ Doric | Strong, structural | Bold lines, columnar |
| 🦋 Ionic | Elegant, growing | Curved forms, flowing |
| 🏟 Corinthian | Ornate, active | Detailed, decorative |
| 🌾 Composite | Combined elements | Mixed patterns |
| ⚖ Vitruvian | Balanced, refined | Symmetrical, measured |
| 🖼 Palladian | Complete, polished | Refined, harmonious |

---

### ⚖🎯📍🔵 - Educational UI.parti

```typescript
interface EducationalUI {
  // Teaching through interaction
  teaches: 'classical-architecture'
  
  // Principles embedded
  principles: [
    'Vitruvius: Firmitas, Utilitas, Venustas'
    'Palladio: Proportion, Symmetry'
    'Orders: Tuscan → Palladian progression'
  ]
  
  // Learning mode
  passiveLearning: true     // Learn while using
  noExplicitLessons: true   // No tutorials needed
}
```

**Educational Design:**
- Classical architecture in the UI itself
- Teaching through interaction
- Vitruvius + Palladio principles embedded
- Users learn classical orders passively

---

### ⚖🎯📍🔵 - Figure-Ground Rendering.parti

```typescript
interface FigureGroundRendering {
  // Style
  style: 'Nolli-map-inspired'
  
  // Rendering
  districts: 'render-as-figure-ground'
  visualAccent: 'for-elements'
  
  // Output
  colorMap: 'of-entire-canvas'
  
  // Use case
  useCase: 'overview-visualization'
}
```

**Figure-Ground:**
- Like Nolli maps
- Districts render as figure-ground
- Visual accent for elements
- Color map of entire canvas

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| ⚖ Calibration | 🐂 Foundation | Calibrates foundation |
| ⚖ Calibration | 🦋 Building | Refines features |
| ⚖ Calibration | 🖼 Experience | Delivers polished experience |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| Proportions & Scale | ⚖📍🏛🧈➕🔵 | 3 | ✅ Complete |
| Drafting Tools | ⚖📍🔨🧈➕🔵 | 4 | ✅ Complete |
| UI Calibration | ⚖📍🌹🧈➕🔵 | 4 | ✅ Complete |
| UX Balance | ⚖📍🪐🧈➕🔵 | 4 | ✅ Complete |
| Performance Tuning | ⚖📍⌛🧈➕🔵 | 3 | ✅ Complete |
| Classical Architecture UI | ⚖📍🎯🧈➕🔵 | 3 | ✅ Complete |

**Total: 21 items across 6 districts**

---

*⚖ Vitruvian — The balanced refinement that brings harmony.*
