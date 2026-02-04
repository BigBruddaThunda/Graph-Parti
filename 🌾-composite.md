# 🌾 Composite — Integration 🟠

> **Domain**: Combinations, merges, how pieces connect, cross-system flows
> **Phase**: 5 of 7 — The combination of elements into a whole
> **Architectural Style**: Combined, connected, flowing

---

## 🌾📍🐬🧈➕🟠 Collaboration District

Multi-user workflows and shared spaces.

### 🌾🐬📍🟠 - Multi-User Workflow.parti

```typescript
interface Collaboration {
  // Users
  users: Map<UserId, User>
  currentUser: UserId
  
  // Presence
  cursors: Map<UserId, CursorPosition>
  selections: Map<UserId, Selection>
  
  // Communication
  chat: Message[]
  annotations: Annotation[]  // Sticky notes, highlights
  
  // Permissions
  roles: {
    owner: 'full-control'
    editor: 'edit-content'
    viewer: 'view-only'
    commenter: 'add-comments'
  }
}

interface User {
  id: UserId
  name: string
  color: Color           // Cursor/selection color
  avatar: string
  status: 'active' | 'idle' | 'offline'
  lastSeen: Timestamp
}
```

**Collaboration Features:**
- Team working in same .parti file
- Text-based communication in space
- Timestamps log who/when
- Leave notes for next person
- Project manager assigns tasks

---

### 🌾🐬📍🟠 - Version Merging.parti

```typescript
interface VersionMerging {
  // Branches
  branches: Map<BranchName, Commit[]>
  currentBranch: BranchName
  
  // Merge process
  merge: {
    detectConflicts: (branchA: Branch, branchB: Branch) => Conflict[]
    autoResolve: (conflict: Conflict) => Resolution
    manualResolve: (conflict: Conflict) => Resolution
  }
  
  // Conflict types
  conflictTypes: [
    'same-block-edited',
    'block-deleted-edited',
    'zip-changed-both',
    'connection-added-removed'
  ]
}
```

**Merge Flow:**
```
Both parties work on own version
    ↓
Metadata logs track changes
    ↓
Merge versions with conflict detection
    ↓
Auto-resolve where possible
    ↓
Manual merge when needed
```

---

### 🌾🐬📍🟠 - Form Workflows.parti

```typescript
interface FormWorkflow {
  // Form lifecycle
  create: (template: FormTemplate) => Form
  distribute: (form: Form, recipients: User[]) => void
  collect: (form: Form) => Response[]
  export: (responses: Response[]) => ExportFormat
  
  // Storage
  responses: {
    storedIn: 'form_responses'  // Special block type
    exportFormats: ['csv', 'json', 'xlsx']
  }
}
```

**Form Workflow:**
- Fill forms, send .parti back
- Collect responses in same file
- Form data stored in `form_responses`
- Export responses to CSV

---

### 🌾🐬📍🟠 - Sharing Formats.parti

| Format | Use Case | Contains |
|--------|----------|----------|
| .parti file | Full project share | Everything |
| .parti snippet | Block/tool export | Selected blocks |
| Screenshot + metadata | Paste to import | Visual + embedded data |
| URL (future) | Social sharing | Link to hosted file |

```typescript
interface SharingFormats {
  partiFile: {
    extension: '.parti'
    contains: 'full-project'
    size: 'unlimited'
  }
  partiSnippet: {
    extension: '.parti-snippet'
    contains: 'selected-blocks'
    reusable: true
  }
  screenshot: {
    format: 'png'
    embeds: 'metadata'
    import: 'paste-to-import'
  }
}
```

---

## 🌾📍🦢🧈➕🟠 System Integrations District

### 🌾🦢📍🟠 - Hub and Spoke Model.parti

```
     External Systems         .parti Hub           Export Targets
     ┌─────────────┐         ┌─────────┐          ┌─────────────┐
     │ Databases   │────────▶│         │─────────▶│ Figma       │
     │ Spreadsheets│────────▶│         │─────────▶│ GitHub      │
     │ Notion      │────────▶│  .parti │─────────▶│ Linear      │
     │ Airtable    │────────▶│  Canvas │─────────▶│ AI Tools    │
     │ Clipboard   │────────▶│         │─────────▶│ .md / PDF   │
     │ APIs        │────────▶│         │─────────▶│ Slack       │
     └─────────────┘         └─────────┘          └─────────────┘
```

Graph Parti as the central hub connecting external systems.

---

### 🌾🦢📍🟠 - File Type Conversions.parti

**Import:**

| Source | Target Block | Conversion Process |
|--------|--------------|-------------------|
| .docx | 📝 Text Block | Convert to markdown |
| .pdf | 🖼 Media Block | Display or extract text |
| .xlsx | 📊 Table Block | Parse rows/columns |
| Images | 🖼 Media Block | Embed directly |
| CAD blocks | 📦 Composite Block | Map to zip system |
| GIS data | 🗺 Map Block | Geo coordinates |

**Export:**

| Source | Format | Output |
|--------|--------|--------|
| Viewport | PNG | Screenshot |
| Viewport | PDF | Vector output |
| Text Block | .md | Markdown |
| Table Block | .csv | Comma-separated |
| Code Block | .py/.js | Source file |
| Full document | .parti | Native format |

---

### 🌾🦢📍🟠 - External API Integration.parti

```typescript
interface APIIntegration {
  // Configuration
  apiKeys: Map<ServiceName, APIKey>
  
  // Supported services
  services: {
    llm: ['openai', 'anthropic', 'local']
    geolocation: ['google-maps', 'mapbox']
    weather: ['openweather', 'weatherapi']
    fitness: ['garmin', 'strava', 'fitbit']
  }
  
  // Usage in SCL
  syntax: '🧸🛒🎯 apiService endpoint data'
}
```

**API Integration:**
- User drops API key into .parti
- LLM integration for AI assistance
- Python bridge for external libraries
- Potential connectors: Garmin, GIS, weather, etc.

---

## 🌾📍🤌🧈➕🟠 AI Integration District

### 🌾🤌📍🟠 - Context for AI.parti

Graph Parti solves AI context fragmentation:

**Before:**
- 30 isolated PDFs
- Scattered context across files
- Token waste on tool calling
- Lost spatial relationships

**After:**
- 1 .parti with everything
- Spatial relationships preserved
- AI reads full context in one file
- Direct manipulation

```typescript
interface AIContext {
  // What AI can see
  readable: [
    'all-blocks',
    'all-connections',
    'all-variables',
    'canvas-layout',
    'zip-organization',
    'version-history'
  ]
  
  // Context window optimization
  tokenEfficiency: 'high'  // No wasted tool calls
}
```

---

### 🌾🤌📍🟠 - AI Capabilities.parti

| Capability | Description | Input | Output |
|------------|-------------|-------|--------|
| Natural language → SCL | Describe, AI builds | "Make a counter" | SCL code block |
| Tool generation | Create widgets | "Make me a calculator" | Tool block |
| Sketch cleanup | Messy → clean | Hand-drawn strokes | Clean shapes |
| Code explanation | Parse and explain | SCL/Python code | Natural language |
| Debugging | Find and fix issues | Error state | Fixed code |
| Procedural generation | .parti → interactive space | Canvas layout | 3D/interactive world |

---

### 🌾🤌📍🟠 - AI as Co-Creator.parti

```typescript
interface AICoCreator {
  // Modes
  modes: {
    onDemand: 'user-prompts-ai'
    proactive: 'ai-suggests'
    autonomous: 'ai-works-while-user-elsewhere'
  }
  
  // Capabilities
  builds: ['tools', 'widgets', 'skills', 'slash-commands']
  
  // Interaction
  operatesOn: 'canvas'
  whileUser: 'works-elsewhere'
  
  // Import
  screenshotImport: 'metadata-embedded-brings-tools-in'
}
```

**AI Co-Creation:**
- AI builds tools on the fly
- Widgets, skills, slash commands
- AI operates on canvas while you work elsewhere
- Screenshot import brings tools in (metadata embedded)

---

### 🌾🤌📍🟠 - Spatial Instruction.parti

Instead of words, point:

| Gesture | Meaning |
|---------|---------|
| Draw line | "Move element here" |
| Circle sketch | "Clean this up" |
| Arrow between items | "Show relationship" |
| Annotation | Instruction itself |

```typescript
interface SpatialInstruction {
  // Instruction types
  types: {
    line: 'move-to-location'
    circle: 'clean-up-area'
    arrow: 'show-relationship'
    annotation: 'direct-instruction'
  }
  
  // AI interpretation
  aiReads: 'gesture + context'
  generates: 'appropriate-action'
}
```

---

## 🌾📍🧬🧈➕🟠 Layer Integration District

### 🌾🧬📍🟠 - 7 Sheets Integration.parti

Each Order = a sheet layer:

```
🖼 Palladian   ─ Experience layer (final)
⚖ Vitruvian   ─ Calibration layer
🌾 Composite   ─ Integration layer
🏟 Corinthian  ─ Execution layer
🦋 Ionic       ─ Building layer
⛽ Doric       ─ Validation layer
🐂 Tuscan      ─ Foundation layer (base)
```

**Sheet Behavior:**
- Sheets build on sheet behind
- 7th sheet (🖼) is final experience
- Toggle visibility per sheet
- Each sheet has different tools/themes

---

### 🌾🧬📍🟠 - Ghost Layer System.parti

```typescript
interface GhostLayer {
  // Opacity control
  opacity: 0.0 - 1.0
  
  // Use cases
  useCases: {
    trace: 'copy-from-ghost-to-active'
    compare: 'see-previous-versions'
    reference: 'keep-old-layout-visible'
  }
  
  // Interaction
  copyFromGhost: true
  toggleVisibility: true
}
```

**Ghost Layer:**
- Toggle opacity of any layer
- Trace previous versions
- Copy from ghost to active
- Silhouette of prior version behind current

---

### 🌾🧬📍🟠 - Trace Paper Versioning.parti

```typescript
interface TracePaperVersioning {
  // Commits
  commits: Commit[]
  
  // Each commit = trace layer
  traceLayer: {
    opacity: 0.3
    visible: boolean
    content: CanvasState
  }
  
  // Features
  features: {
    toggleVisibility: 'per-version'
    slideshow: 'for-content-creation'
    compare: 'side-by-side'
    restore: 'revert-to-version'
  }
}
```

**Trace Paper:**
- Each 🧮 commit = trace layer
- Versions like trace paper in architecture
- Toggle visibility per version
- Slideshow for content creation

---

## 🌾📍🏗🧈➕🟠 Platform Integration District

### 🌾🏗📍🟠 - Cross-Device Sync.parti

```typescript
interface CrossDeviceSync {
  // Devices
  devices: ['phone', 'tablet', 'desktop']
  
  // Sync
  sync: {
    mode: 'real-time' | 'periodic' | 'manual'
    conflictResolution: 'last-write-wins' | 'manual'
  }
  
  // PWA
  pwa: {
    installable: true
    offline: true
    backgroundSync: true
  }
  
  // Workflows
  workflows: [
    'work-on-desktop',
    'sketch-on-tablet',
    'review-on-phone'
  ]
}
```

**Cross-Device:**
- Phone, tablet, PC all same file
- PWA for mobile install
- Offline first with sync
- Work on desktop, sketch on tablet

---

### 🌾🏗📍🟠 - Runtime Environments.parti

| Platform | Tech | Status |
|----------|------|--------|
| Web | HTML/CSS/JS, Canvas 2D | ✅ Primary |
| PWA | Service Worker, offline | ✅ Supported |
| Desktop | Tauri | 📋 Planned |
| Mobile | PWA + native later | 📋 Planned |

---

### 🌾🏗📍🟠 - Recursive Build Strategy.parti

```
Graph Parti builds → Graph Parti
       ↓
Graph Parti builds → ARCHIDECK (PPL±)
       ↓
ARCHIDECK uses → Graph Parti infrastructure
       ↓
Improvements → Graph Parti
       ↓
[Loop continues]
```

**Self-Building:**
- Graph Parti is used to build Graph Parti
- Dogfooding ensures quality
- Improvements feed back into the tool

---

## 🌾📍🔗🧈➕🟠 Connection System District

### 🌾🔗📍🟠 - Block Connections.parti

```typescript
interface Connection {
  // Endpoints
  from: {
    blockId: BlockId
    port: PortPosition
  }
  to: {
    blockId?: BlockId      // Direct connection
    zip?: ZipCode          // Zip routing
  }
  
  // Behavior
  trigger: Trigger
  condition: Condition | null
  action: Action
  
  // Visual
  style: {
    visible: boolean
    lineStyle: 'solid' | 'dashed' | 'dotted'
    color: Color
    width: number
  }
}
```

---

### 🌾🔗📍🟠 - Conditional Routing.parti

```
Tap Block A
    ↓
🦉 score > 10?
    ├── [yes] → Win Block
    └── [no]  → Lose Block
```

```typescript
interface ConditionalRouting {
  // Condition types
  conditionTypes: [
    'variable-comparison',
    'truthy-check',
    'range-check',
    'list-contains'
  ]
  
  // Routing
  routes: {
    true: Target
    false: Target
  }
}
```

---

### 🌾🔗📍🟠 - Cross-Zip Connections.parti

```typescript
interface CrossZipConnection {
  // Connect across zips
  connectByZip: true
  
  // Patterns
  patterns: {
    exact: '[🐂 🧲 🏛 🔵]'     // Exact match
    wildcard: '[🐂 _ _ _]'      // Any in Tuscan
    partial: '[_ _ 🏛 _]'       // Any structure
  }
  
  // Parent zip behavior
  parentZip: 'contains-child-connections'
}
```

**Cross-Zip:**
- Connect blocks across different zips
- Route by zip pattern, not just ID
- Parent zips contain child connections

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| 🌾 Integration | 🐂 Foundation | Integrates foundation elements |
| 🌾 Integration | 🏟 Execution | Executes integrations at runtime |
| 🌾 Integration | 🖼 Experience | Delivers integrated experience |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| Collaboration | 🌾📍🐬🧈➕🟠 | 4 | ✅ Complete |
| System Integrations | 🌾📍🦢🧈➕🟠 | 3 | ✅ Complete |
| AI Integration | 🌾📍🤌🧈➕🟠 | 4 | ✅ Complete |
| Layer Integration | 🌾📍🧬🧈➕🟠 | 3 | ✅ Complete |
| Platform Integration | 🌾📍🏗🧈➕🟠 | 3 | ✅ Complete |
| Connection System | 🌾📍🔗🧈➕🟠 | 3 | ✅ Complete |

**Total: 20 items across 6 districts**

---

*🌾 Composite — Where elements combine into a greater whole.*
