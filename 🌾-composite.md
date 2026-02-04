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
@@ -129,51 +129,51 @@ interface FormWorkflow {
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
@@ -203,51 +203,51 @@ Graph Parti as the central hub connecting external systems.
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
@@ -313,51 +313,51 @@ Instead of words, point:
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

@@ -397,51 +397,51 @@ interface TracePaperVersioning {
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
@@ -468,51 +468,51 @@ interface CrossDeviceSync {
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
@@ -571,37 +571,37 @@ interface CrossZipConnection {
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