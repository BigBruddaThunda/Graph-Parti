# TOOL-HUNT ROUND 2 — Fresh-Eyes Reconnaissance (2026-06-23)

> Gathered from a fresh AI session with zero Graph Parti context — just the pitch.
> The fresh take found lanes we hadn't explored. Filed here for the build session
> to mine when ready. Nothing here is built — it's all ore deposits.

## What the Fresh Eyes Saw

The side-chat independently arrived at the **Card → Deck → Board** ontology:
- **Card** = every discrete thing (a tool, an exercise, a character stat, a calendar event, a tile, a recipe, a reward tier, a moon phase)
- **Deck** = every collection (a toolbar, a workout program, a character sheet, a week, an inventory, a Kanban column, a TCG hand)
- **Board** = every workspace (the CAD canvas, the 2D world, the Kanban view, the calendar, the map)

This maps 1:1 to the existing architecture: `.parti` = boards, the 61-drawer system = decks, items = cards. The fresh session confirmed the shape without knowing the shape existed.

## New Lanes Identified (beyond Waves 1-5)

### Lane A: Math Solver Layer
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **SymPy** | Full CAS — symbolic solve, calculus, algebra, simplification | The kernel. Embeds directly. | Trivial |
| **SciPy** | Numerical computing — optimization, integration, interpolation | Complements SymPy (numeric vs symbolic) | Trivial |
| **mpmath** | Arbitrary precision arithmetic | For exact architectural proportions | Trivial |
| **Lark** | Parser generator (EBNF grammars) | Build the exercise notation parser, the NLP mini-language, the calculator input | Easy |
| **formulas** | Excel-style formula evaluator | Spreadsheet-feel for the math solver | Easy |

### Lane B: Graphing / Plotting
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **PyQtGraph** | Fast scientific plotting on Qt | Native fit — we're already PySide6 | Trivial |
| **Manim** | Mathematical animation engine (3Blue1Brown) | "Explain this visually" mode | Moderate |
| **Plotly** | Interactive graphing (zoom, pan, hover) | Embed in WebView for rich plots | Easy |

### Lane C: 3D / Blender / Unreal Adjacent
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **CadQuery / build123d** | Parametric 3D CAD on OpenCascade | Architectural solid modeling, exports STEP/STL | Easy |
| **Trimesh** | Triangular mesh manipulation, booleans, ray casting | Lighter than Blender for mesh ops | Trivial |
| **PyVista** | 3D plotting + mesh analysis on VTK | Matplotlib for 3D | Easy |
| **fogleman/sdf** | SDF mesh generation — math-defined 3D shapes | Elegant functional 3D | Trivial |
| **USD (pxr)** | Pixar's scene description — interchange format | Bridge to UE5/Blender/Houdini | Moderate |
| **glTF / pygltflib** | "JPEG of 3D" asset format | Prefab/template export | Trivial |

### Lane D: Procedural Generation
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Wave Function Collapse** | Constraint-based tile/pattern generation | Floor plans, cityscapes, textures, dungeon layouts | Easy |
| **L-Systems** | Fractal branching structures | Trees, road networks, city layouts | Trivial (from scratch) |
| **OpenSimplex / pynoise** | Noise generation (Perlin, Simplex, Worley) | Terrain, biomes, ore distribution | Trivial |
| **Poisson Disk Sampling** | Even point distribution | Tree/settlement placement | Trivial |

### Lane E: Pixel Art + Vector Expansion
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Potrace / pypotrace** | Bitmap-to-vector tracing | Trace hand-drawn sketches → vector | Easy |
| **VTracer** | Color image raster-to-SVG | Full-color vectorization | Moderate |
| **Pyxelate** | Photo-to-pixel-art converter | Pixel art pipeline | Trivial |
| **drawsvg / svg.py** | Programmatic SVG generation | Vector output for the art engine | Trivial |
| **Poline** | Esoteric color palette generation (polar coords) | Palette discovery | Easy |

### Lane F: Game / RPG / Deck-Builder
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **python-tcod (libtcod)** | Roguelike toolkit — FOV, pathfinding, BSP dungeons | Top-down RPG layer | Easy |
| **esper** | Entity Component System | Architecture for all game objects | Trivial |
| **transitions** | Finite state machine library | NPC AI, quest states, UI states | Trivial |
| **py_trees** | Behavior trees | Complex AI, dialog systems | Easy |
| **inkpy** | Ink narrative scripting runtime | Branching dialog/quests | Easy |
| **dnd-character** | D&D 5e character builder | Fork for Hero's Almanac | Trivial |
| **d20** | Dice notation parser (2d6+3, 4d6kh3) | Character creation, combat | Trivial |
| **NetworkX** | Graph theory — skill trees as DAGs, crafting as dependency graphs | Core infrastructure | Trivial |

### Lane G: Life Tools / Almanac
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Skyfield** | Astronomical computation — moon phases, sun position, planets | Farmer's almanac layer | Easy |
| **astral** | Simpler sun/moon calculations | Daily astronomy | Trivial |
| **icalendar** | RFC 5545 calendar file generation | Export schedules to any calendar app | Trivial |
| **recurring-ical-events** | Resolve recurrence rules to dates | "Every Mon+Thu for 12 weeks" | Trivial |
| **ReportLab / FPDF2** | PDF generation | Printable planners, character sheets, workout logs | Moderate/Easy |
| **WeasyPrint** | HTML/CSS → PDF | Template-based document generation | Easy |

### Lane H: Rendering Pipeline
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **ModernGL** | Python OpenGL wrapper | GPU-accelerated rendering | Moderate |
| **Taichi** | High-performance GPU computing in Python | Particle sims, fluid dynamics, ray tracing | Easy |
| **libfive** | Functional CAD kernel (implicit geometry / SDFs) | Infinite resolution geometry | Moderate |

### Lane I: Infrastructure / Cross-Cutting
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **NodeGraphQt / Ryven** | Node-based visual programming UI for Qt | Blueprint-style tool composition | Easy |
| **watchdog** | File system monitoring | Auto-load new plugins from folder | Easy |
| **msgpack / CBOR** | Binary serialization (faster than JSON) | .ppl/.parti file format optimization | Trivial |
| **pyfiglet** | ASCII art text banners | Terminal output, decorative headers | Trivial |
| **Rich + Textual** | Terminal UI framework | Beautiful console output, rapid UI prototyping | Easy |
| **fonttools** | Font manipulation (TTF/OTF read/write) | Glyph design, font customization | Easy |

### Lane J: Exercise Engine Specifics
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **1RM formulas** | Epley, Brzycki, Lombardi, Mayhew, O'Conner, Wathan | ~30 lines of Python, all 6 formulas | Trivial |
| **Exercise notation parser** | `3x12 @185lbs RPE8`, `5/3/1 @85%`, `AMRAP 10min` | Custom grammar via Lark or regex | Moderate |
| **Periodization models** | Linear, undulating, block, 5/3/1, GZCL, nSuns | Each is its own algorithm | Moderate |

### Lane K: CNC / CAM / Fabrication
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **ezdxf** | Read/write/modify DXF files | AutoCAD interop | Trivial |
| **dxf2gcode** | DXF → G-code for CNC | Fabrication pipeline | Easy |
| **gcodeutils** | G-code stream manipulation | Post-processing toolpaths | Trivial |

## Awesome-Lists to Keep Mining
- `terkelg/awesome-creative-coding` — 200+ creative coding tools
- `mlightcad/awesome-cad` — Open-source CAD tools, kernels, solvers
- `beardicus/awesome-plotters` — Pen plotter art and algorithms
- `Foadsf/Awesome-FLOSS-CAS` — Free computer algebra systems
- `xyflow/awesome-node-based-uis` — Node graph UI frameworks

## The Ore Detector Concept
Build a tool inside Graph Parti that:
1. Takes a keyword or description
2. Searches GitHub via API (PyGithub), filters by Python + stars + activity
3. Fetches README content
4. Uses an LLM to summarize: what it does, how it fits, integration difficulty
5. Logs as a .parti event so the AI collaborator can reference it

The tool-hunting process becomes a Graph Parti tool. The system mines for its own ore.

## Connection to Existing Architecture

| Fresh-Eyes Concept | Existing System Equivalent |
|--------------------|---------------------------|
| Card → Deck → Board | Item → 61-drawer → Canvas layer |
| Deck-builder UI paradigm | SCL band right-click drawers |
| Exercise notation parser | The workout engine's set/rep context (already designed in BLOCK-FUNCTION) |
| Skill tree as DAG | The 7-tuple maturity signature (HEROES-ALMANAC) |
| Crafting system | The 4,032-room lattice (zip addresses) |
| Moon phases / almanac | The daily Operis routine (already cron-scheduled) |
| Node-based visual programming | The roundtable agent ecosystem (future) |
| Rule engine / FSM | The Operator Bus event system (spec-complete, staged) |

The fresh eyes confirmed the architecture without knowing the architecture. That's convergence.

---

## Substrate Lanes (Lanes 29-36) — the Self-Composing Core

The second round of the fresh-eyes hunt went deeper — into the infrastructure
that makes the screen self-compose. This is the layer beneath tools: the constraint
solver + grammar + reactive binding + semantic index that lets every new content
type automatically know how to present itself.

### Lane 29: Constraint Layout Engine
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Kiwisolver** | Cassowary constraint solver (C++ w/ Python bindings) | THE layout heartbeat. Incremental re-solve when constraints change. Apple Auto Layout uses this algorithm. Already a Matplotlib dependency. | Easy |
| **python-constraint** | General CSP solver (backtracking, arc consistency) | For discrete layout choices (which template, which deck layout) | Trivial |
| **NuCS** | Pure Python constraint solver with global constraints | Complex allocation: "arrange 7 blocks, no overlap, largest = most important, related = adjacent" | Easy |
| **OR-Tools (Google)** | Industrial constraint programming + optimization | Overkill for simple layouts, essential for complex scheduling (periodization, budget optimization) | Moderate |
| **squarify** | Treemap rectangle packing | Treemap layouts: week sized by volume, exercises sized by sets | Trivial |

### Lane 30: Reactive Data Layer
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **RxPY** | ReactiveX observable streams | Event composition: content arrives → layout recalculates → rendering updates | Easy |
| **eventsourcing** | Event sourcing pattern library | Every state change = immutable event. AI reads the log. System can rewind/replay/branch. | Moderate |
| **watchdog** | File system event monitoring | Auto-load new plugins, detect .parti changes, trigger recomposition | Trivial |
| **Custom Signal/Observable** | 50-line reactive property pattern | `card.priority = 5` → auto-triggers layout recomposition on displaying boards | Trivial |

### Lane 31: Semantic Indexing
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **RDFlib** | RDF knowledge graph (subject → predicate → object triples) | Index the entire GP universe as a knowledge graph. SPARQL queries. | Moderate |
| **NetworkX** (deepened role) | Property graph for relationships | Same purpose as RDF but lighter. Nodes = things, edges = relationships, queries = graph traversal. | Trivial |
| **rtree** | R-tree spatial indexing | "What's near this point?" "What overlaps this rect?" Essential for layout collision detection. | Easy |
| **FAISS / Annoy** | Vector similarity search | Embed content descriptions, find semantically similar items. "This CAD tutorial is similar to this structural engineering article." | Moderate |

### Lane 32: Grammar-Based Composition
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Lark** (central role) | EBNF grammar parser | Exercise notation, card rule text, layout specification, search queries, NLP commands — all one consistent approach | Easy |
| **Tracery** | Text-expansion grammar (Kate Compton) | Procedural text: layout templates, card descriptions, quest text, planting instructions | Trivial |
| **Context-Free Layout Grammars** | Architecture pattern | `Page → Header Body Footer`, `Body → Column Column`, `Card → Title Content Action`. Grammar rules applied by content type + context. | Moderate (design) |

### Lane 33: Rule Engine
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **durable-rules** | Forward-chaining rule engine (Rete algorithm) | `when content.type == "exercise" AND context.mode == "workout" then use_template("exercise_card")` | Easy |
| **business-rules** | Simpler rule evaluation, JSON-serializable | Rules live in .parti files | Easy |

### Lane 34: Semantic Zoom / LOD
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **LOD Architecture** | Pattern: each card defines `icon → badge → summary → detail → editor` renderings | Zoom level + available space determines which LOD. Constraint solver handles the rest. | Pure architecture |
| **squarify** (again) | Treemap as a zoom interface | Zoom into a rectangle → it expands to show next LOD. Nested treemaps = infinite semantic zoom. | Trivial |

### Lane 35: NLP Command Layer
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **spaCy** | Industrial NLP — tokenization, POS, NER, dependency parsing | Parse natural language commands into structured intents | Moderate |
| **Rasa NLU** | Intent classification + entity extraction | "show this week's workouts" → intent:display, entity:time_range | Moderate |
| **rapidfuzz** | Fast fuzzy string matching | "bech press" → "Bench Press" in exercise DB. Already needed for Alt-command line. | Trivial |

### Lane 36: AST / Metaprogramming
| Tool | What | Fit | Wrap |
|------|------|-----|------|
| **Python `ast` module** | Parse and generate Python code | Widget factory: NLP → Python → widget. Inspect plugins at load time. | Trivial (stdlib) |
| **Jinja2** | Template engine | Generate HTML (Kickstarter), character sheets, planner pages, card text | Trivial |

### Research Precedents (Proof It's Buildable)
| System | What It Proved | Gap Graph Parti Fills |
|--------|---------------|----------------------|
| **SUPPLE** (Gajos & Weld 2004) | Constraint-optimization generates UIs from functional specs + device models + user traces | Extends from "adapting to devices" to "adapting to everything" |
| **Cassowary / Apple Auto Layout** | Incremental constraint solving is fast enough for real-time UI | GP uses this as the spatial resolution engine |
| **TeX/LaTeX** | Content describes itself, layout engine composes optimally. Knuth's paragraph-breaking is still the best. | Extends from documents to all content types |
| **Wave Function Collapse** | Local constraint propagation → globally coherent compositions | GP's layout = WFC applied to UI: each position has possible cards, constraints reduce, system collapses to coherent layout |
| **Morphogenesis in Architecture** (Menges, Sabin) | Biological paradigm: structures grow and adapt to environmental forces | GP's screen is morphogenic — grows based on content forces. Local rules → global order. |
| **Generative UI** (2024-present) | LLMs can generate UI on-the-fly | GP uses deterministic grammar + constraints, NOT LLM generation. AI reads event logs and suggests, not controls. |
