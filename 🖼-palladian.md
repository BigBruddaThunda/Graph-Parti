# 🖼 Palladian — Experience 🟣

> **Domain**: Final layer, what users see/feel, UI, rendering, presentation
> **Phase**: 7 of 7 — The complete, polished experience
> **Architectural Style**: Complete, polished, harmonious

---

## 🖼👀🧈🟣 User Experience District

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
- Each sheet adds complexity
- Learning by using, not tutorials
- Rewards exploration and play

---

### 🖼👀📍🟣 - Kinesthetic Familiarity.parti

Target feel:

| Aspect | Description |
|--------|-------------|
| Core feel | Microsoft Paint meets AutoCAD on graph paper |
| Learning path | Legos + crayons → realize they're code commands |
| Icon behavior | Icons become tools, typing becomes programming |
| Learning curve | No 10 YouTube videos needed |

```typescript
interface KinestheticFamiliarity {
  // Metaphors
  metaphors: {
    visual: 'Paint + AutoCAD + graph paper'
    learning: 'Legos → realize they are code'
    tools: 'Icons become physical tools'
  }
  
  // Goal
  goal: 'intuitive-without-tutorials'
  
  // Approach
  approach: 'rewards-figuring-it-out'
}
```

---

### 🖼👀📍🟣 - Intuitive Onboarding.parti

| Gesture | Action | Learning Speed |
|---------|--------|----------------|
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

## 🖼🌹🧈🟣 Visual Rendering District

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
  }
}
```

---

### 🖼🌹📍🟣 - Visual States.parti

| State | Visual Indicator |
|-------|------------------|
| Normal | Default appearance |
| Selected | Highlight border, handles |
| Hovered | Subtle highlight |
| Locked | Lock icon, dimmed |
| Executing | Pulse animation |
| Error | Red border, error icon |
| Connected | Connection lines visible |

```typescript
interface VisualStates {
  states: {
    normal: { appearance: 'default' }
    selected: { border: 'highlight', handles: true }
    hovered: { highlight: 'subtle' }
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

## 🖼🎼🧈🟣 Presentation District

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

### 🖼🎼📍🟣 - Viewport Saving.parti

```typescript
interface ViewportSaving {
  // Output
  output: 'hi-res-image'
  
  // Quality
  textQuality: 'not-pixelated'
  sketchQuality: 'maintained'
  
  // Metadata
  includes: 'scale-annotations'
  
  // Use case
  useCase: 'presentation-quality-export'
}
```

**Viewport Save:**
- Save viewport as hi-res image
- Text doesn't look pixelated
- Sketches maintain quality
- Scale annotations included

---

### 🖼🎼📍🟣 - Presentation Mode.parti

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

## 🖼🏛🧈🟣 Use Case Experience District

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
- 3D print ready export

---

### 🖼🏛📍🟣 - Education.parti

```typescript
interface Education {
  // Scope
  scope: 'entire-4-year-college-career'
  
  // Projects
  capstone: 'full-history'
  trades: 'collaboration-timber-blacksmith'
  
  // Tools
  draftingCopilot: true
  
  // Output
  portfolio: 'LinkedIn-resume-ready'
}
```

**For Students:**
- Entire 4-year college career in one .parti
- Capstone projects with full history
- Trades collaboration (timber, blacksmith, etc.)
- Digital drafting copilot
- Portfolio for LinkedIn/resume

---

### 🖼🏛📍🟣 - Construction & Development.parti

```typescript
interface ConstructionDevelopment {
  // Applications
  applications: {
    realEstate: 'development-maps'
    jobsite: 'daily-photos-project-update'
    contractor: 'communication'
    planning: 'city-planning-zoning-maps'
    dot: 'project-planning'
  }
}
```

**For Construction:**
- Real estate development maps
- Jobsite daily photos → project update
- Contractor communication
- City planning, zoning maps
- DOT project planning

---

### 🖼🏛📍🟣 - Creative Work.parti

```typescript
interface CreativeWork {
  // Media
  manga: 'panels-with-prose'
  storyboards: 'with-audio-notes'
  comics: 'panel-layouts'
  
  // Games
  gameDev: 'floor-plan-quest-notes'
  pixelArt: 'with-tile-maps'
  
  // Other
  twitch: 'emote-packs'
}
```

**For Creatives:**
- Manga panels with prose
- Storyboards with audio notes
- Comic book panels
- Game level design (floor plan → quest notes)
- Pixel art with tile maps
- Twitch emote packs

---

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

## 🖼🤌🧈🟣 Interactive Experience District

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
  ]
}
```

---

### 🖼🤌📍🟣 - AI-Rendered Experience.parti

```typescript
interface AIRenderedExperience {
  // Input
  aiReads: '.parti-context'
  
  // Generation
  generates: 'interactive-space'
  
  // Features
  features: {
    codeBlocks: 'become-functional'
    rendering: 'watercolor-interaction'
    logic: 'backrooms-rpg-dungeons'
  }
}
```

**AI Rendering:**
- AI reads .parti context
- Procedurally generates interactive space
- Code blocks become functional
- Watercolor renderings + interaction
- Backrooms logic, RPG dungeons

---

### 🖼🤌📍🟣 - Embedded Interactivity.parti

```typescript
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

## 🖼🐬🧈🟣 Social Experience District

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
```

**Jury Mode:**
- Digital critique like architecture jury
- Presenter draws on screen
- Walk through floor plans, click zips
- Panel comments, circles elements
- Collaborative whiteboard

---

### 🖼🐬📍🟣 - Team Experience.parti

```typescript
interface TeamExperience {
  // Presence
  multiplePeople: 'live-document'
  aiAgents: 'plus-human-teammates'
  
  // Communication
  notes: 'for-next-person'
  timestamps: true
  metadata: 'logs'
}
```

**Team Features:**
- Multiple people in live document
- AI agents + human teammates
- Notes for next person
- Timestamps, metadata logs

---

### 🖼🐬📍🟣 - Sharing Experience.parti

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

## 🖼🧬🧈🟣 Platform Experience District

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
- Same file on phone/tablet/PC
- Stylus on tablet, finger on phone
- Custom keyboard with emojis
- Portrait and landscape modes
- Test UI at actual device scale

---

### 🖼🧬📍🟣 - Offline Experience.parti

```typescript
interface OfflineExperience {
  // Functionality
  fullFunctionality: 'offline'
  
  // Sync
  cloudSync: 'when-connected'
  
  // Philosophy
  philosophy: 'local-first-online-bonus'
  
  // Quality
  noDegradedExperience: true
}
```

**Offline:**
- Full functionality offline
- Cloud sync when connected
- Local first, online bonus
- No degraded experience

---

### 🖼🧬📍🟣 - PWA Experience.parti

```typescript
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

## 🖼🪐🧈🟣 Product Vision District

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

---

### 🖼🪐📍🟣 - Who It's For.parti

| User | Primary Use |
|------|-------------|
| Architects | Blueprints, renderings, construction |
| Students | Portfolio, capstone, learning |
| Developers | PRDs, mockups, code |
| Game devs | Levels, pixel art, quest maps |
| Artists | Storyboards, emotes, mood boards |
| Coaches | Programs, training blocks |
| Writers | Story maps, world building |
| Teams | Shared spaces, form workflows |
| ADHD people | Everything in one window, no alt-tab |

---

### 🖼🪐📍🟣 - The Tagline.parti

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
| User Experience | 🖼👀🧈🟣 | 3 | ✅ Complete |
| Visual Rendering | 🖼🌹🧈🟣 | 3 | ✅ Complete |
| Presentation | 🖼🎼🧈🟣 | 3 | ✅ Complete |
| Use Case Experience | 🖼🏛🧈🟣 | 5 | ✅ Complete |
| Interactive Experience | 🖼🤌🧈🟣 | 3 | ✅ Complete |
| Social Experience | 🖼🐬🧈🟣 | 3 | ✅ Complete |
| Platform Experience | 🖼🧬🧈🟣 | 3 | ✅ Complete |
| Product Vision | 🖼🪐🧈🟣 | 3 | ✅ Complete |

**Total: 26 items across 8 districts**

---

*🖼 Palladian — The complete, polished experience that emerges from all Orders.*
