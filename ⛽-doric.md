# ⛽ Doric — Validation 🔵

> **Domain**: Testing, checks, constraints, rules, what must be TRUE
> **Phase**: 2 of 7 — The pillar that supports what stands
> **Architectural Style**: Strong, structural, load-bearing

---

## ⛽📍🏛🧈➕🔵 Structural Constraints District

Rules governing the physical structure of the canvas and its contents.

### ⛽🏛📍🔵 - Grid Rules.parti

```typescript
interface GridConstraints {
  // Block positioning
  snapToGrid: boolean           // Default: true
  snapThreshold: number         // Pixels (default: 8)
  
  // Size limits
  minBlockSize: { width: 1, height: 1 }     // In cells
  maxBlockSize: { width: null, height: null }  // No limit
  
  // Overlap behavior
  allowOverlap: boolean         // Default: false for text
  zOrderResolution: 'last-wins' | 'zip-based' | 'manual'
  
  // Cell occupancy
  cellOccupancy: 'exclusive' | 'shared' | 'layered'
}
```

**Grid Rules:**
@@ -112,51 +112,51 @@ interface LockState {
```typescript
interface LayerCollisionRules {
  // Main layer rules
  textOnText: 'block'      // Cannot overlap
  textOnDrawing: 'allow'   // Can overlap
  drawingOnAnything: 'allow'  // Drawings float above
  
  // For overlap needs
  useDepthLayers: boolean  // Use sheet layers
  ghostLayerOpacity: 0.3   // Background layers
}
```

**Collision Matrix:**

| Content A | Content B | Result |
|-----------|-----------|--------|
| Text | Text | ❌ Blocked |
| Text | Drawing | ✅ Allowed |
| Drawing | Drawing | ✅ Allowed |
| Block | Block | ⚠️ Z-order |
| Block | Drawing | ✅ Allowed |

---

## ⛽📍🔨🧈➕🔵 Input Validation District

### ⛽🔨📍🔵 - Paste Detection.parti

Content type auto-detection on paste:

| Input Pattern | Detected Type | Creates Block |
|---------------|---------------|---------------|
| Plain text (no markup) | text | 📝 Text Block |
| Tabular (TSV/CSV) | table | 📊 Table Block |
| Image data (base64, blob) | media | 🖼 Media Block |
| Code pattern (syntax detected) | code | 💻 Code Block |
| Markdown | markdown | 📝 Text Block (rendered) |
| HTML | html | 📝 Text Block (converted) |
| JSON | json | 💻 Code Block or 📊 Table |
| URL | url | 🖼 Media Block (embed) |

```typescript
interface PasteDetection {
  detectContentType(data: ClipboardData): ContentType
  
  // Detection heuristics
  heuristics: {
    table: /\t|\n.*\t/           // Tabs or multiline with tabs
    markdown: /#{1,6}\s|```|\[.*\]\(.*\)/  // Headers, code blocks, links
    json: /^\s*[\{\[]/          // Starts with { or [
@@ -213,51 +213,51 @@ function validateBlock(block: Block): ValidationResult {
  if (block.size.width < 1) errors.push('Width must be >= 1')
  if (block.size.height < 1) errors.push('Height must be >= 1')
  
  // Position constraints
  if (!Number.isInteger(block.position.x)) {
    errors.push('Position x must be integer (grid snap)')
  }
  if (!Number.isInteger(block.position.y)) {
    errors.push('Position y must be integer (grid snap)')
  }
  
  // Zip validation
  if (block.zip && !validateZip(block.zip).valid) {
    errors.push(`Invalid zip: ${block.zip}`)
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}
```

---

## ⛽📍🦉🧈➕🔵 SCL Syntax Validation District

### ⛽🦉📍🔵 - Statement Structure.parti

```
[Order] [Type] [Modifier] [Operand] [Color]
   │       │       │          │        │
   │       │       │          │        └── State (optional inline)
   │       │       │          └── What to operate on
   │       │       └── Direction (optional)
   │       └── Action verb
   └── Phase marker (optional)
```

**Statement Examples:**
```scl
🐂📍 x 0                    ← init place variable x = 0
🧲🪡 name "Enter name:"    ← capture pull input with prompt
🚀🛒 "Hello World"         ← dispatch push output
🦉 score > 10              ← parse evaluate condition
➕ x 1                      ← add increment x by 1
```

---

### ⛽🦉📍🔵 - Expression Rules.parti
@@ -293,51 +293,51 @@ interface TypeSystem {
  // Type checking rules
  rules: {
    '➕➖': ['number', 'number'] → 'number'    // Arithmetic
    '🚀🛒': [any] → 'void'                      // Output accepts any
    '🦉': [any] → 'boolean'                     // Conditions return boolean
    '🧲🪡': ['string' | 'undefined'] → 'string' // Input returns string
  }
  
  // Scope levels
  scopes: ['global', 'block', 'local', 'zip']
}
```

**Type Compatibility:**

| Operation | Allowed Types | Result Type |
|-----------|---------------|-------------|
| `➕` `➖` | number | number |
| `🦉` (compare) | any | boolean |
| `🧲🪡` | string (prompt) | string |
| `🚀🛒` | any | void |
| `📍` (assign) | any | any |

---

## ⛽📍🌹🧈➕🔵 Connection Validation District

### ⛽🌹📍🔵 - Trigger Types.parti

Valid trigger configurations:

| Type | Config Required | Fires When |
|------|-----------------|------------|
| tap | none | User taps block |
| swipe | direction | User swipes in direction |
| hover | duration (ms) | Cursor hovers for duration |
| load | none | Block loads into viewport |
| timer | delay, repeat?, interval? | Time-based trigger |
| value | variable, comparison, threshold | Variable meets condition |
| submit | formId | Form is submitted |
| complete | codeBlockId | Code block finishes |
| custom | SCL expression | Expression evaluates true |

```typescript
interface Trigger {
  type: TriggerType
  config: TriggerConfig
  condition?: Condition    // Optional gate
  action: Action
  target: Target
}
@@ -361,95 +361,95 @@ interface Condition {

// Examples:
// Simple: 🦉 score > 10
// Compound: 🦉 (score > 10) and (lives > 0)
```

---

### ⛽🌹📍🔵 - Action Types.parti

Valid action types for connections:

| Action | Description | Parameters |
|--------|-------------|------------|
| navigate | Go to target block | target: BlockId or Zip |
| execute | Run target's code | target: BlockId |
| show | Make block visible | target: BlockId |
| hide | Hide block | target: BlockId |
| toggle | Toggle visibility | target: BlockId |
| set | Change variable | name, value |
| call | Invoke tool | toolId, inputs |
| custom | Run SCL expression | expression |

---

## ⛽📍⌛🧈➕🟡 Performance Constraints District

### ⛽⌛📍🟡 - Scale Limits.parti

**Target Performance Metrics:**

| Metric | Target | Maximum |
|--------|--------|---------|
| Cells | 100k | 1M |
| Strokes | 10k | 100k |
| Blocks | 1k | 10k |
| Viewport FPS | 60 | 30 (minimum) |
| Load time | < 2s | < 5s |
| Save time | < 1s | < 3s |

**Optimization Strategies:**
- Lazy loading for off-viewport content
- Spatial indexing for fast lookups
- Level-of-detail rendering based on zoom
- Memory pooling for frequent allocations

---

### ⛽⌛📍🟡 - File Size.parti

```typescript
interface FileSizeConstraints {
  // Format options
  v1: 'json'           // Human-readable, development
  v2: 'binary'         // Compact, production (future)
  
  // Compression
  gzipThreshold: 100_000  // Bytes
  gzipLevel: 6            // 1-9
  
  // Size targets
  typicalSize: 500_000    // 500KB average
  largeSize: 5_000_000    // 5MB warning threshold
  maxSize: 50_000_000     // 50MB hard limit
}
```

---

## ⛽📍🌋🧈➕🔵 Error Taxonomy District

### ⛽🌋📍🔵 - Error Types.parti

```typescript
type ErrorCategory = 
  | 'syntax'      // SCL syntax errors
  | 'validation'  // Constraint violations
  | 'runtime'     // Execution errors
  | 'system'      // Platform/infra errors
  | 'network'     // Connection errors
  | 'user'        // User input errors

interface GraphPartiError {
  category: ErrorCategory
  code: string           // e.g., 'SCL-001'
  message: string
  blockId?: BlockId      // Associated block
  line?: number          // Line number (for code)
  recoverable: boolean   // Can execution continue?
}
```

**Error Codes:**

| Code | Category | Meaning |
@@ -458,37 +458,37 @@ interface GraphPartiError {
| SCL-002 | syntax | Color not at end |
| SCL-003 | syntax | Unknown emoji |
| VAL-001 | validation | Block size too small |
| VAL-002 | validation | Invalid position |
| VAL-003 | validation | Text collision |
| RUN-001 | runtime | Undefined variable |
| RUN-002 | runtime | Division by zero |
| RUN-003 | runtime | Infinite loop detected |

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| ⛽ Validation | 🐂 Foundation | Validates foundation structures |
| ⛽ Validation | 🏟 Execution | Enforces constraints at runtime |
| ⛽ Validation | 🖼 Experience | Displays errors to users |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| Structural Constraints | ⛽📍🏛🧈➕🔵 | 4 | ✅ Complete |
| Input Validation | ⛽📍🔨🧈➕🔵 | 3 | ✅ Complete |
| SCL Syntax Validation | ⛽📍🦉🧈➕🔵 | 3 | ✅ Complete |
| Connection Validation | ⛽📍🌹🧈➕🔵 | 3 | ✅ Complete |
| Performance Constraints | ⛽📍⌛🧈➕🟡 | 2 | ✅ Complete |
| Error Taxonomy | ⛽📍🌋🧈➕🔵 | 1 | ✅ Complete |

**Total: 16 items across 6 districts**

---

*⛽ Doric — The pillar that ensures what stands, stands true.*