# Graph Parti

Graph Parti is a **semantic canvas** for architecture, design, and complex thinking. It combines a figure‑ground drawing space with a semantic addressing system so ideas, blocks, and interactions can be organized, navigated, and executed using emoji‑based zip codes. The core premise: **your canvas is also a language**, and every element on it can be addressed, linked, and evolved through that language.【F:Ralph parti.txt†L1-L120】【F:INDEX.md†L1-L286】

---

## What Graph Parti Is

Graph Parti is a multi‑layered creative environment where each “Order” (Tuscan → Palladian) represents a distinct phase of meaning—foundation, validation, building, execution, integration, calibration, and experience. Each Order is a district file that organizes ideas into parent containers with nested children, so the system grows like a living map of the project.【F:INDEX.md†L1-L286】【F:Ralph parti.txt†L1-L210】

**In short:**
- A **canvas** for drawing, planning, and spatial thinking.
- A **semantic file system** where everything has a zip code.
- A **language** (SCL) that lets you describe, navigate, and execute ideas by address.【F:Ralph parti.txt†L1-L210】【F:SCL.md†L1-L120】

---

## Core Concepts

### 1) The 7+1 Order Files
Graph Parti organizes all context into seven parent Orders (domains) plus a system scratchpad. Each Order has a corresponding `.md` file containing districts and items for that domain.【F:INDEX.md†L1-L286】【F:Ralph parti.txt†L1-L70】

| Order | File | Domain |
|------|------|--------|
| 🐂 | `🐂-tuscan.md` | Foundation (definitions, models) |
| ⛽ | `⛽-doric.md` | Validation (rules, constraints) |
| 🦋 | `🦋-ionic.md` | Building (features, iterations) |
| 🏟 | `🏟-corinthian.md` | Execution (runtime behavior) |
| 🌾 | `🌾-composite.md` | Integration (connections, flows) |
| ⚖ | `⚖-vitruvian.md` | Calibration (tuning, balance) |
| 🖼 | `🖼-palladian.md` | Experience (UI, presentation) |
| 🧮 | `🧮-save.md` | Scratchpad (partials, tasks) |

---

### 2) SCL (Semantic Compression Language)
SCL is the emoji‑based language Graph Parti uses to encode meaning. It is both **a labeling system** and **an interaction language**. The same emoji set defines Orders, Types, Axes, Modifiers, Blocks, and Colors, which combine into short semantic “zip codes.”【F:Ralph parti.txt†L1-L210】【F:SCL.md†L1-L200】

SCL principles:
- **Color terminates**: every zip ends with a state color.
- **Partial zips are valid**: even a single emoji can be meaningful.
- **Context defines meaning**: the same emoji can shift meaning by Order.
- **Districts contain districts**: hierarchies can nest infinitely.【F:Ralph parti.txt†L300-L340】

---

### 3) Zip Codes (Semantic Addresses)
Every idea, block, and district has a zip code that encodes its meaning. There are two key formats:

**Standard Zip (4 dials)**
```
Order · Type · Axis · Color
```

**District Zip (6 dials for parent containers)**
```
Order · Type · Axis · Block · Modifier · Color
```

This makes parent containers explicitly addressable while still keeping child items lightweight and readable.【F:Ralph parti.txt†L60-L120】【F:INDEX.md†L24-L96】

---

## How the System Works (Ralph Loop)

Graph Parti uses an iterative sorting loop to absorb a “wall of context” and map it into districts:

1. Read context from multiple angles.  
2. Identify domains and container relationships.  
3. Assign zip codes.  
4. Sort into Order files.  
5. Leave unresolved items in 🧮.  
6. Re‑read and refine.  
7. Repeat until stable.  

This loop transforms raw context into a structured, navigable architecture of ideas.【F:Ralph parti.txt†L1-L40】【F:Ralph parti.txt†L240-L310】

---

## File/Directory Layout

```
├── INDEX.md            # Master zip index + rules
├── SCL.md              # Semantic Compression Language reference
├── Ralph parti.txt     # Full system primer + raw context
├── 🐂-tuscan.md         # Foundation district file
├── ⛽-doric.md          # Validation district file
├── 🦋-ionic.md          # Building district file
├── 🏟-corinthian.md     # Execution district file
├── 🌾-composite.md      # Integration district file
├── ⚖-vitruvian.md       # Calibration district file
├── 🖼-palladian.md       # Experience district file
└── 🧮-save.md           # Scratchpad / unresolved items
```
【F:INDEX.md†L1-L286】【F:Ralph parti.txt†L1-L70】

---

## Typical Workflow

1. Start at **INDEX.md** to see the full district map and navigation order.
2. Use **SCL.md** to decode or craft zip codes.
3. Open an Order file (e.g., `🐂-tuscan.md`) to expand a district.
4. Add new ideas as `.parti` items with proper zip codes.
5. Use 🧮 to track partials or unresolved items.

This creates a living, expandable “project atlas” where every part of the system has a semantic address and a clear place to live.【F:INDEX.md†L1-L334】【F:🐂-tuscan.md†L1-L220】

---

## Design Philosophy

Graph Parti is built around the idea that **learning happens by using**. The interface and emoji vocabulary are designed to be **kinesthetic and intuitive**, like picking up a tool and learning its function by doing. It emphasizes clarity, hierarchy, and semantic structure without sacrificing the freedom of sketching and spatial exploration.【F:Ralph parti.txt†L360-L430】【F:🖼-palladian.md†L9-L120】

---

## Status

The current repository contains a complete first pass of the 7 Orders plus a live scratchpad. The structure is designed to evolve with each loop as more context is sorted and refined.【F:INDEX.md†L320-L336】【F:🧮-save.md†L300-L336】

---

## Getting Started (Quick Read)

1. **Read** `Ralph parti.txt` for the full system narrative.
2. **Open** `INDEX.md` to navigate the districts.
3. **Use** `SCL.md` as the emoji vocabulary reference.
4. **Explore** any Order file to see structured examples.

---

## License

License is not yet specified. Add one if you plan to distribute or open‑source the project.
