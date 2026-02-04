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
@@ -78,51 +78,51 @@ interface ScaleSettings {
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
@@ -215,51 +215,51 @@ interface DimensionCallouts {
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
@@ -328,51 +328,51 @@ interface ZoomLevelRendering {

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
@@ -447,51 +447,51 @@ interface LockMoveBehavior {
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
@@ -538,51 +538,51 @@ interface InputResponsiveness {
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
@@ -625,37 +625,37 @@ interface FigureGroundRendering {
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