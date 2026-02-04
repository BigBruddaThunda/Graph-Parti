# 🖼 Palladian — Experience 🟣

> **Domain**: Final layer, what users see/feel, UI, rendering, presentation
> **Phase**: 7 of 7 — The complete, polished experience
> **Architectural Style**: Complete, polished, harmonious

---

## 🖼📍👀🧈➕🟣 User Experience District

The feel and flow of using Graph Parti.

### 🖼👀📍🟣 - First Experience.parti

```typescript
interface FirstExperience {
  // Starting point
  opensOn: '🐂 Tuscan sheet'
  
  // Progression
  sheetProgression: 'each-adds-complexity'
  
  // Learning
  learningMethod: 'by-using'
  tutorials: 'none-required'
  
  // Reward
  rewardsExploration: true
  rewardsPlay: true
}
```

**First Launch:**
- Opens on 🐂 Tuscan sheet (simple front door)
@@ -75,51 +75,51 @@ interface KinestheticFamiliarity {
| Drag | Pan canvas | Immediate |
| Pinch | Zoom | Immediate |
| Double-tap | Type | First use |
| Stylus | Draw | Natural |
| Select | Multi-gesture | Discovered |

```typescript
interface Onboarding {
  // Gestures
  gestures: {
    drag: { action: 'pan-canvas', learning: 'immediate' }
    pinch: { action: 'zoom', learning: 'immediate' }
    doubleTap: { action: 'type', learning: 'first-use' }
    stylus: { action: 'draw', learning: 'natural' }
    select: { action: 'multi-gesture', learning: 'discovered' }
  }
  
  // Philosophy
  noExplicitTutorial: true
  discoverable: true
}
```

---

## 🖼📍🌹🧈➕🟣 Visual Rendering District

### 🖼🌹📍🟣 - Block Rendering Layers.parti

```
┌─────────────────────────────────┐
│         Annotations             │ ← Strokes on top
├─────────────────────────────────┤
│         UI Elements             │ ← Buttons, inputs
├─────────────────────────────────┤
│         Content                 │ ← Text, table, image
├─────────────────────────────────┤
│         Background              │ ← Fill, border
├─────────────────────────────────┤
│         Shadow/Effects          │ ← Drop shadow, glow
└─────────────────────────────────┘
```

```typescript
interface BlockRenderingLayers {
  layers: {
    annotations: { zIndex: 5, content: 'strokes' }
    uiElements: { zIndex: 4, content: 'buttons-inputs' }
    content: { zIndex: 3, content: 'text-table-image' }
    background: { zIndex: 2, content: 'fill-border' }
    shadowEffects: { zIndex: 1, content: 'drop-shadow-glow' }
@@ -150,51 +150,51 @@ interface VisualStates {
    locked: { icon: 'lock', dimmed: true }
    executing: { animation: 'pulse' }
    error: { border: 'red', icon: 'error' }
    connected: { lines: 'visible' }
  }
}
```

---

### 🖼🌹📍🟣 - Type-Specific Rendering.parti

Each block type has distinct visual:

| Type | Header | Content Style | Special Features |
|------|--------|---------------|------------------|
| 📝 Text | Document icon | Markdown rendered | Page footer |
| 💻 Code | Code icon | Dark theme | Line numbers, run button |
| 🛠 Tool | Tool icon | UI layout | Interactive widgets |
| 📋 Form | Form icon | Field labels | Submit button |
| 📊 Table | Table icon | Grid cells | Sortable columns |
| 🖼 Media | Media icon | Embedded content | Full-screen view |

---

## 🖼📍🎼🧈➕🟣 Presentation District

### 🖼🎼📍🟣 - Export Formats.parti

| Format | Use Case | Quality |
|--------|----------|---------|
| PNG | High-res viewport screenshot | Raster |
| PDF | Vector output, print-ready | Vector |
| .md | Markdown conversion | Text |
| .parti | Native, complete | Full |
| GIF/MP4 | Version history slideshow | Animation |

```typescript
interface ExportFormats {
  formats: {
    png: { use: 'screenshot', quality: 'high-res' }
    pdf: { use: 'print', quality: 'vector' }
    md: { use: 'markdown-export', quality: 'text' }
    parti: { use: 'native', quality: 'complete' }
    gif: { use: 'slideshow', quality: 'animation' }
  }
}
```

---

@@ -229,51 +229,51 @@ interface ViewportSaving {

```typescript
interface PresentationMode {
  // Activation
  activation: 'full-screen-block-view'
  
  // Navigation
  navigation: 'click-through-connected-blocks'
  
  // Comparison
  like: 'PowerPoint-but-spatial'
  
  // Audience
  audienceNavigation: true
}
```

**Presentation:**
- Full-screen block view
- Click through connected blocks
- Like PowerPoint but spatial
- Audience can navigate

---

## 🖼📍🏛🧈➕🟣 Use Case Experience District

### 🖼🏛📍🟣 - Architecture & Design.parti

```typescript
interface ArchitectureDesign {
  // Features
  features: {
    blueprints: 'in-one-file'
    moodboards: 'combined-with-drawings'
    revisions: 'version-history'
    rendering: 'watercolor-not-sterile-3d'
    education: 'classical-architecture-ui-teaches'
    drawings: 'floor-plans-elevations-sections-together'
    cadBlocks: 'tied-to-zip-system'
    export3d: '3d-print-ready'
  }
}
```

**For Architects:**
- Blueprints + moodboards + revisions in one
- Watercolor rendering (not sterile 3D)
- Classical architecture UI teaches while using
- Floor plans, elevations, sections together
- CAD blocks tied to zips
@@ -363,51 +363,51 @@ interface CreativeWork {

### 🖼🏛📍🟣 - Software Development.parti

```typescript
interface SoftwareDevelopment {
  // Documentation
  prd: 'with-embedded-mockups'
  wireframes: 'at-device-scale'
  
  // Code
  executable: 'code-blocks-run'
  
  // History
  decisions: 'version-history-of-architecture'
}
```

**For Developers:**
- PRD with embedded mockups
- UI wireframes at device scale
- Code blocks that execute
- Version history of architecture decisions

---

## 🖼📍🤌🧈➕🟣 Interactive Experience District

### 🖼🤌📍🟣 - .parti as Universe.parti

A .parti file can become:

| Form | Description |
|------|-------------|
| App | Functional application |
| Game | Interactive experience |
| Document | Rich content |
| Tool | Utility/widget |
| World | Explorable space |
| Interactive story | Narrative experience |
| City | Urban exploration |

```typescript
interface PartiAsUniverse {
  forms: [
    'app',
    'game',
    'document',
    'tool',
    'world',
    'interactive-story',
    'city'
@@ -451,51 +451,51 @@ interface AIRenderedExperience {
interface EmbeddedInteractivity {
  // Games
  arcade: '1-shot-games-in-space'
  
  // Media
  galleries: 'slideshows-photo-galleries'
  
  // Ambient
  mood: 'color-changes-while-panning'
  sound: 'sound-effects-music-layers'
  
  // Context
  relatedInfo: 'beside-games'
}
```

**Interactivity:**
- 1-shot arcade games in space
- Related info beside games
- Slideshows, photo galleries
- Ambient mood, color changes while panning
- Sound effects, music layers

---

## 🖼📍🐬🧈➕🟣 Social Experience District

### 🖼🐬📍🟣 - Jury/Critique Mode.parti

```typescript
interface JuryCritiqueMode {
  // Setting
  setting: 'digital-critique-like-architecture-jury'
  
  // Presenter
  presenterCan: {
    draw: 'on-screen'
    walkthrough: 'floor-plans'
    navigate: 'click-zips'
  }
  
  // Panel
  panelCan: {
    comment: true
    circle: 'elements'
    sketch: 'ideas'
  }
  
  // Comparison
  like: 'powerpoint-but-collaborative'
}
@@ -537,51 +537,51 @@ interface TeamExperience {

```typescript
interface SharingExperience {
  // Screenshot
  screenshot: {
    embeds: 'metadata'
    import: 'paste-screenshot-tool-appears'
  }
  
  // Blocks
  shareBlocks: 'between-projects'
  
  // Vision
  vision: '.parti-as-new-standard-like-md'
}
```

**Sharing:**
- Screenshot with embedded metadata
- Paste screenshot → tool appears
- Share blocks between projects
- .parti as new standard (like .md)

---

## 🖼📍🧬🧈➕🟣 Platform Experience District

### 🖼🧬📍🟣 - Mobile Experience.parti

```typescript
interface MobileExperience {
  // Cross-device
  sameFile: 'phone-tablet-pc'
  
  // Input
  stylus: 'on-tablet'
  finger: 'on-phone'
  
  // Keyboard
  customKeyboard: 'Graph-Parti-keyboard'
  
  // Orientation
  portrait: true
  landscape: true
  
  // Testing
  testAtScale: 'actual-device-scale'
}
```

**Mobile:**
@@ -625,51 +625,51 @@ interface OfflineExperience {
interface PWAExperience {
  // Install
  install: 'to-home-screen'
  
  // Window
  window: 'standalone'
  
  // Branding
  icon: 'app-icon'
  
  // Features
  backgroundSync: true
  pushNotifications: 'future'
}
```

**PWA:**
- Install to home screen
- Standalone window
- App icon
- Background sync
- Push notifications (future)

---

## 🖼📍🪐🧈➕🟣 Product Vision District

### 🖼🪐📍🟣 - What Graph Parti IS.parti

```typescript
interface WhatGraphPartiIs {
  // Metaphors
  metaphors: [
    'Drafting table for everything',
    'Swiss army knife of creative tools',
    'Obsidian that does not feel like a mess',
    'Notion that lets you draw',
    'CAD + Word + Paint + Pixel mapping baby'
  ]
  
  // Core
  core: 'spatial-thinkin-tool'
}
```

**Graph Parti is:**
- Drafting table for everything
- Swiss army knife of creative tools
- Obsidian that doesn't feel like a mess
- Notion that lets you draw
- CAD + Word + Paint + Pixel mapping baby
@@ -696,39 +696,39 @@ interface WhatGraphPartiIs {

> **"Graph Parti is Figure-Ground for your ideas."**

**Interpretations:**
- **Figure** = figuring it out (process)
- **Ground** = grounding your ideas (outcome)
- Like Nolli maps — public vs private space
- Multiple depth interpretations simultaneously

---

## Cross-References

| This Order | References | Relationship |
|------------|------------|--------------|
| 🖼 Experience | All Orders | Final output of all Orders |
| 🖼 Experience | 🐂 Foundation | Users interact with foundation |
| 🖼 Experience | 🏟 Execution | Runtime powers experience |

---

## District Summary

| District | Zip | Items | Status |
|----------|-----|-------|--------|
| User Experience | 🖼📍👀🧈➕🟣 | 3 | ✅ Complete |
| Visual Rendering | 🖼📍🌹🧈➕🟣 | 3 | ✅ Complete |
| Presentation | 🖼📍🎼🧈➕🟣 | 3 | ✅ Complete |
| Use Case Experience | 🖼📍🏛🧈➕🟣 | 5 | ✅ Complete |
| Interactive Experience | 🖼📍🤌🧈➕🟣 | 3 | ✅ Complete |
| Social Experience | 🖼📍🐬🧈➕🟣 | 3 | ✅ Complete |
| Platform Experience | 🖼📍🧬🧈➕🟣 | 3 | ✅ Complete |
| Product Vision | 🖼📍🪐🧈➕🟣 | 3 | ✅ Complete |

**Total: 26 items across 8 districts**

---

*🖼 Palladian — The complete, polished experience that emerges from all Orders.*