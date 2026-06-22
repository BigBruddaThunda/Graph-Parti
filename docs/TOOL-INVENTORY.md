# TOOL-INVENTORY — Graph Parti Definitive Build List
> Gathered 2026-06-22. Three domains (AutoCAD 2D, Krita, pixel painting) cross-referenced against `tools.py`, the architect's canon, and PySide6/Qt6 capabilities.
>
> **Source truth:** `graphparti/tools.py` (17 tool classes, ~2100 lines) + `canvas_view.py` (keyboard routing, snap, trim dispatch).
> **Stack:** Python 3.13 + PySide6 (Qt6 Graphics View). Hard constraint.
> **Grid:** 1D = 1 grid cell = 20 scene units. All user-facing dimensions in grid units.

---

## Section A: What's Built

### Drawing Tools (7)

| Tool | Class | Key | Status | Notes |
|------|-------|-----|--------|-------|
| **Line** | `LineTool` | L | Working | Ortho lock, tab-type exact length, live dimension readout, osnap |
| **Rect** | `RectTool` | R | Working | Drag to draw, Tab: W then H, live W×H readout |
| **Circle** | `CircleTool` | C | Working | Center+radius, tab-type radius, explodes on trim |
| **Ellipse** | `EllipseTool` | — | Working | 2-point axis definition + perpendicular width drag |
| **Arc** | `ArcTool` | — | Working | 3-point arc (click start, click mid, click end) |
| **Polyline** | `PolylineTool` | P | Working | Click vertices, close-to-polygon (>=3 pts near start), ortho-constrained |
| **Paint** | `PaintTool` | B | Working | Two modes: grid-on = solid cell rects; grid-off = flood-fill (renders barriers into QImage, stack-based fill). Right-drag = erase. Respects line barriers within cells |

### Modify Tools (8)

| Tool | Class | Key | Status | Notes |
|------|-------|-----|--------|-------|
| **Select** | `SelectTool` | V | Working | Band-select, layer-isolated (parti/both/trace), Shift+click multi-select, right-click delete, drag-move |
| **Trim** | `TrimTool` | T | Working | Grid-cell + intersection trim on lines/rects/polylines/circles. Fence trim via left-drag (or right-drag on any tool). Sibling edges stay as connected QGraphicsPathItem |
| **Extend** | `ExtendTool` | E (held) | Working | Auto-extend line to nearest boundary. Hold-E = temporary switch from current tool |
| **Offset** | `OffsetTool` | O | Working | Offset geometry parallel at a distance |
| **Divide** | `DivideTool` | — | Working | Two modes: mark (place division points) and cut (split geometry at divisions) |
| **Rotate** | `RotateTool` | — | Working | Pivot + angle, snap-aware |
| **Mirror** | `MirrorTool` | M | Working | Mirror geometry across a defined axis |
| **Scale** | `ScaleTool` | — | Working | Band-select + drag to set scale factor |

### Text Tools (2)

| Tool | Class | Key | Status | Notes |
|------|-------|-----|--------|-------|
| **Word Text** | `WordTextTool` | A | Working | Flowing 50-char-wrap text, VG5000 12px |
| **Cell Text** | `CellTextTool` | G | Working | 1 character = 1 grid cell, letter-spaced advance = grid_spacing |

### Built-In Operations (not separate tools)

| Operation | Trigger | Notes |
|-----------|---------|-------|
| **Explode** | Ctrl+E | Decompose compound shapes into primitives |
| **Overkill** | Ctrl+K | Remove duplicate/overlapping geometry |
| **Copy** | Ctrl+C | Copy selected to clipboard |
| **Paste** | Ctrl+V | Paste from clipboard / paste images to parti layer |
| **Undo/Redo** | Ctrl+Z / Ctrl+Y | Full QUndoStack with macro grouping |
| **Delete** | Delete/Backspace | Delete selected items |
| **Right-click delete** | Right-click | Yeet-delete (selected or under cursor) |
| **Pan** | Space (hold) or middle-click | Viewport pan |
| **Wireframe toggle** | X | Show/hide grid |
| **Division toggle** | N | Show/hide division ticks |
| **Tab dimensions** | Tab (during draw) | Type exact dimension, commits on release |
| **Tab edit dims** | Tab (with selection) | Cycle through selected shape's dimensions |

### Snap & Constraint System

| Feature | Status | Notes |
|---------|--------|-------|
| Grid snap | Working | 1/8-cell dead zone (snaps near corners, free in centers) |
| Object snap (osnap) | Working | Endpoints + midpoints, 12px priority, distinct markers (square/triangle) |
| Ortho lock | Working | Separate from snap. Angle menu: 90°/45°/30°/15° |
| Live dimension readout | Working | All draw tools show dimensions during drag |

### Layers

| Layer | Type | Notes |
|-------|------|-------|
| **parti** | Raster | Back, 50% opacity, reference images, traced over |
| **trace** | Vector | Front, full opacity, working draft |
| **book** | Vector | Zip boxes, spawner-deck items |

### I/O

| Feature | Status | Notes |
|---------|--------|-------|
| Save .parti JSON | Working | Ctrl+S, v1 format |
| Open .parti | Working | Ctrl+O |
| Export PNG | Working | Ctrl+Shift+S |
| Save to District | Working | Ctrl+Shift+D (zip-addressed) |
| Image drag-drop | Working | Explorer → parti layer at 50% |
| Image paste | Working | Ctrl+V from clipboard |
| Image resize | Working | 8 handles (corners + edge midpoints) |

---

## Section B: Critical Missing Tools (Architect's Priority List)

These are tools Jake has explicitly asked for or that the canon documents call out as needed for daily architectural drafting work. Ordered by workflow impact.

### Tier 1 — Blocks Daily Work (build these first)

| # | Tool | AutoCAD Equiv | Why Critical | Complexity |
|---|------|---------------|-------------|------------|
| 1 | **Hatch Patterns** | HATCH | Section cuts, material fills, poché. The architect's #1 render request. Intaglio cross-hatching is the canon aesthetic. Canon: "no solid fills, no gradients" — tone by line density. | Large — needs a hatch engine (pattern definition, boundary detection, clipping) |
| 2 | **Dimension Annotations** | DIM + LEADER/QLEADER | Architectural dimensions with extension lines, dimension lines, arrows, and text. Leaders for callouts. Cannot draft without these. | Medium — geometry math + text placement + arrowheads |
| 3 | **Spline/Bezier Curves** | SPLINE | Smooth curves for molding profiles, site contours, organic forms. PySide6 has `QPainterPath.cubicTo()` native. | Medium — control point editing is the hard part |
| 4 | **Fillet** | FILLET | Round corners at specified radius. Fundamental modify command. | Medium — arc-tangent calculation at intersections |
| 5 | **Chamfer** | CHAMFER | Angled corners at specified distances. Companion to fillet. | Medium — line-trim + new segment at intersection |
| 6 | **Join** | JOIN | Merge adjacent/overlapping line segments into polylines. Essential cleanup. | Medium — endpoint proximity detection + path merging |
| 7 | **Array (Rectangular)** | ARRAY | Repeat geometry in rows × columns at specified spacing. Columns, windows, structural grids. | Trivial — clone + translate in a loop |
| 8 | **Array (Polar)** | ARRAY (polar) | Repeat geometry around a center point. Rose windows, radial plans. | Trivial — clone + rotate in a loop |
| 9 | **Copy at Origin** | COPY (with base point) | Copy selected items in-place or to a specified base point, not just Ctrl+C/V clipboard. AutoCAD-style: select → pick base point → pick destination. | Trivial — clone + single move |
| 10 | **PEDIT (Polyline Edit)** | PEDIT | Edit polyline vertices: move, add, delete vertices. Convert lines to polylines. Essential for cleaning up geometry. | Medium — vertex handle system + insert/delete logic |

### Tier 2 — Enables Full Drafting Vocabulary

| # | Tool | AutoCAD Equiv | Why Critical | Complexity |
|---|------|---------------|-------------|------------|
| 11 | **Construction Lines** | XLINE/RAY | Infinite reference lines for layout. The blue reference lines in `orders.py` are a prototype — needs a proper construction line mode. | Trivial — infinite-length lines clipped to viewport |
| 12 | **Property Match** | MATCHPROP | Click source item → click target → target gets source's pen/brush/properties. Huge time saver. | Trivial — read properties, apply to target |
| 13 | **Eyedropper** | — (Krita) | Pick color from canvas (fill or stroke). The architect explicitly asked for this. | Trivial — sample pixel at click point, set active color |
| 14 | **Polygon** | POLYGON | Regular polygon with N sides (3-12). Hexagons, octagons. | Trivial — N-point circle subdivision |
| 15 | **Line Types** | LINETYPE | Dashed, center, hidden, phantom, section-cut lines. The canon defines 8 color-mapped line types. Only solid + preview-dash exist now. | Medium — QPen dash patterns + per-item storage |
| 16 | **Line Weights** | LINEWEIGHT | Full ISO/Rapidograph pen ladder (0.13-1.00mm). The 16 line-color slots are planned to evolve into weight presets. | Medium — weight picker UI + pen mapping |
| 17 | **Stretch** | STRETCH | Move a subset of vertices on selected objects while keeping others fixed. Window stretching. | Medium — vertex identification + selective move |
| 18 | **Break** | BREAK | Split an object at a point or between two points. | Medium — point-on-curve calculation + split |
| 19 | **Area Inquiry** | AREA | Calculate enclosed area of polylines/regions. | Trivial — shoelace formula on polyline vertices |
| 20 | **Distance Inquiry** | DIST | Point-to-point measurement tool (persist on canvas). Currently only live during draw. | Trivial — two-click + dim label placement |

---

## Section C: The Full Map — All Three Domains

### Domain 1: AutoCAD 2D Commands

#### Drawing Commands

| AutoCAD | Graph Parti | Status | Priority | PySide6 Approach |
|---------|-------------|--------|----------|-----------------|
| LINE | `LineTool` | **BUILT** | — | `QGraphicsLineItem` |
| PLINE | `PolylineTool` | **BUILT** | — | `QPainterPath` → `QGraphicsPathItem` |
| CIRCLE | `CircleTool` | **BUILT** | — | `QGraphicsEllipseItem` |
| ARC | `ArcTool` | **BUILT** | — | `QPainterPath.arcTo()` |
| ELLIPSE | `EllipseTool` | **BUILT** | — | `QGraphicsEllipseItem` with transform |
| RECTANG | `RectTool` | **BUILT** | — | `QGraphicsRectItem` |
| SPLINE | — | **NOT BUILT** | Critical | `QPainterPath.cubicTo()` for Bezier; control-point handles for editing |
| XLINE | — | **NOT BUILT** | Important | Infinite `QGraphicsLineItem` clipped to viewport rect; data(1)="construction" tag |
| RAY | — | **NOT BUILT** | Nice-to-have | Half-infinite line (same as XLINE but one direction) |
| MLINE | — | **NOT BUILT** | Future | Parallel line pair offset by a width; `QPainterPath` with two stroked sub-paths |
| POLYGON | — | **NOT BUILT** | Important | N-sided regular polygon: compute vertices on circle, emit as `QGraphicsPathItem` |
| DONUT | — | **NOT BUILT** | Future | Two concentric circles with fill between; `QPainterPath` with subpath hole |
| HELIX | — | **N/A** | — | 3D only, skip |
| REGION | — | **NOT BUILT** | Future | Closed boundary → area object. `QPainterPath` boolean ops |
| BOUNDARY | — | **NOT BUILT** | Future | Auto-detect closed boundary from geometry. Ray-casting or flood-fill-then-trace |

#### Modify Commands

| AutoCAD | Graph Parti | Status | Priority | PySide6 Approach |
|---------|-------------|--------|----------|-----------------|
| MOVE | `SelectTool` | **BUILT** | — | Drag-move on scene items |
| COPY | Ctrl+C/V | **PARTIAL** | Critical | Need base-point copy: clone items, pick base point, pick destination → translate |
| ROTATE | `RotateTool` | **BUILT** | — | `QGraphicsItem.setRotation()` / transform |
| MIRROR | `MirrorTool` | **BUILT** | — | Reflect geometry across axis |
| SCALE | `ScaleTool` | **BUILT** | — | `QGraphicsItem.setScale()` / transform rebuild |
| STRETCH | — | **NOT BUILT** | Important | Identify vertices inside crossing window, move only those; QPainterPath vertex manipulation |
| TRIM | `TrimTool` | **BUILT** | — | Grid + intersection + fence modes |
| EXTEND | `ExtendTool` | **BUILT** | — | Auto to nearest boundary |
| FILLET | — | **NOT BUILT** | Critical | Compute tangent arc between two lines at intersection; trim lines to tangent points, insert arc |
| CHAMFER | — | **NOT BUILT** | Critical | Compute chamfer distances on two lines at intersection; trim lines, insert connecting segment |
| BREAK | — | **NOT BUILT** | Important | Split item at point: compute point-on-curve, create two new items from split |
| JOIN | — | **NOT BUILT** | Critical | Find endpoints within tolerance, merge segments into single `QPainterPath` |
| EXPLODE | Ctrl+E | **BUILT** | — | Decompose compound to primitives |
| OFFSET | `OffsetTool` | **BUILT** | — | Parallel offset geometry |
| ARRAY (rect) | — | **NOT BUILT** | Critical | Clone + translate(row*dx, col*dy) in nested loop |
| ARRAY (polar) | — | **NOT BUILT** | Critical | Clone + rotate(i*angle) around center in loop |
| ALIGN | — | **NOT BUILT** | Nice-to-have | 3-point alignment: two source + two destination → compute transform |
| LENGTHEN | — | **NOT BUILT** | Nice-to-have | Resize line by delta or percentage from an endpoint |
| PEDIT | — | **NOT BUILT** | Critical | Vertex editing: display handles on polyline vertices, drag to move, right-click to insert/delete |

#### Annotation Commands

| AutoCAD | Graph Parti | Status | Priority | PySide6 Approach |
|---------|-------------|--------|----------|-----------------|
| TEXT | `WordTextTool` | **BUILT** | — | `QGraphicsTextItem` |
| MTEXT | — | **NOT BUILT** | Nice-to-have | Multi-line text box with formatting; `QGraphicsTextItem` with `setTextWidth()` |
| LEADER | — | **NOT BUILT** | Critical | Arrowhead + polyline + text. `QPainterPath` for arrow, `QGraphicsPathItem` + `QGraphicsTextItem` |
| QLEADER | — | **NOT BUILT** | Critical | Quick leader: click endpoint, click shoulder, type text |
| DIM linear | — | **NOT BUILT** | Critical | Extension lines + dimension line + text centered. All from two picked points + offset direction |
| DIM aligned | — | **NOT BUILT** | Critical | Same as linear but aligned to the measured segment angle |
| DIM angular | — | **NOT BUILT** | Important | Arc between two lines + degree text |
| DIM radius | — | **NOT BUILT** | Important | Leader from center to arc + "R" prefix text |
| DIM diameter | — | **NOT BUILT** | Important | Line through center + "Ø" prefix text |
| DIM ordinate | — | **NOT BUILT** | Nice-to-have | X or Y coordinate relative to origin |
| DIM baseline | — | **NOT BUILT** | Nice-to-have | Stacked dimensions from common baseline |
| DIM continue | — | **NOT BUILT** | Nice-to-have | Chain dimensions end-to-end |
| TABLE | — | **NOT BUILT** | Future | Grid of text cells; `QGraphicsRectItem` grid + `QGraphicsTextItem` per cell |
| HATCH | — | **NOT BUILT** | Critical | Pattern fill within closed boundary. See Section E for architecture |
| GRADIENT | — | **NOT BUILT** | Future | `QLinearGradient`/`QRadialGradient` fill within boundary |

#### Construction & Inquiry

| AutoCAD | Graph Parti | Status | Priority | PySide6 Approach |
|---------|-------------|--------|----------|-----------------|
| POINT | — | **NOT BUILT** | Nice-to-have | Small marker at coordinates; `QGraphicsEllipseItem` 3px |
| DIVIDE | `DivideTool` | **BUILT** | — | Mark + cut modes |
| MEASURE | — | **NOT BUILT** | Nice-to-have | Place points at equal intervals along a curve |
| DIST | Partial (live readout) | **PARTIAL** | Important | Need persistent dimension: two-click → placed dimension annotation |
| AREA | — | **NOT BUILT** | Important | Shoelace formula on polyline vertices → display |
| LIST | — | **NOT BUILT** | Nice-to-have | Property inspector panel |
| ID | — | **NOT BUILT** | Nice-to-have | Click → report grid coordinates |

#### Selection Modes

| AutoCAD | Graph Parti | Status | Priority |
|---------|-------------|--------|----------|
| Window (left-to-right) | `SelectTool` band-select | **BUILT** | — |
| Crossing (right-to-left) | — | **NOT BUILT** | Important |
| Fence | Fence trim (right-drag) | **BUILT** (trim only) | Need fence select |
| Last | — | **NOT BUILT** | Nice-to-have |
| Previous | — | **NOT BUILT** | Nice-to-have |
| WPolygon | — | **NOT BUILT** | Future |
| CPolygon | — | **NOT BUILT** | Future |

#### Properties

| AutoCAD | Graph Parti | Status | Priority |
|---------|-------------|--------|----------|
| LAYER | 3 fixed layers | **PARTIAL** | Future: user-created named layers |
| LINETYPE | Solid only | **NOT BUILT** | Important |
| LINEWEIGHT | Per-item pen width (saved) | **PARTIAL** | Important: weight picker UI |
| COLOR | 16-swatch palettes | **BUILT** | — |
| PROPERTIES | — | **NOT BUILT** | Nice-to-have |
| MATCHPROP | — | **NOT BUILT** | Important |

### Domain 2: Krita Drawing Tools

#### Brush Engines

| Krita Tool | Graph Parti | Status | Priority | Notes |
|------------|-------------|--------|----------|-------|
| Pixel brush | `PaintTool` (cell fill) | **PARTIAL** | Future | GP's paint is cell-based, not freehand pixel. A raster brush layer is DLC-tier |
| Smudge brush | — | **N/A** | — | Not relevant to CAD drafting |
| Color smudge | — | **N/A** | — | Not relevant |
| Hatching brush | — | **NOT BUILT** | Critical | The canon's intaglio aesthetic = hatching. But as a HATCH ENGINE, not a brush |
| Spray brush | — | **NOT BUILT** | Future | Stipple/spray for rendered drawings |
| Shape brush | — | **NOT BUILT** | Future | Stamp shapes along a path |
| Clone brush | — | **NOT BUILT** | Future | Clone from source point |
| Deform brush | — | **N/A** | — | Not relevant |

#### Selection Tools

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Rectangular select | `SelectTool` band-select | **BUILT** | — |
| Elliptical select | — | **NOT BUILT** | Nice-to-have |
| Polygonal select | — | **NOT BUILT** | Nice-to-have |
| Freehand select | — | **NOT BUILT** | Future |
| Contiguous (magic wand) | — | **NOT BUILT** | Future |
| Similar color | — | **NOT BUILT** | Future |
| Bezier select | — | **NOT BUILT** | Future |

#### Transform Tools

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Move | `SelectTool` | **BUILT** | — |
| Rotate | `RotateTool` | **BUILT** | — |
| Scale | `ScaleTool` | **BUILT** | — |
| Shear | — | **NOT BUILT** | Nice-to-have |
| Perspective | — | **NOT BUILT** | Future |
| Warp | — | **N/A** | — |
| Cage | — | **N/A** | — |
| Liquify | — | **N/A** | — |

#### Vector Tools

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Path tool (bezier) | — | **NOT BUILT** | Critical (= SPLINE) |
| Calligraphy | — | **NOT BUILT** | Future |
| Rectangle shape | `RectTool` | **BUILT** | — |
| Ellipse shape | `EllipseTool` | **BUILT** | — |
| Polygon shape | — | **NOT BUILT** | Important |

#### Line Tools

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Straight line | `LineTool` | **BUILT** | — |
| Bezier curve | — | **NOT BUILT** | Critical |
| Freehand path | — | **NOT BUILT** | Future (raster paint layer) |

#### Fill Tools

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Flood fill | `PaintTool` | **BUILT** | — |
| Pattern fill | — | **NOT BUILT** | Critical (= HATCH) |
| Gradient fill | — | **NOT BUILT** | Future |

#### Assistants (Drawing Aids)

| Krita Tool | Graph Parti | Status | Priority | Notes |
|------------|-------------|--------|----------|-------|
| Vanishing point | — | **NOT BUILT** | Important | Perspective lines converge to point. Huge for architectural drawing |
| Parallel ruler | Ortho lock | **PARTIAL** | — | Ortho constrains to angle multiples; true parallel ruler constrains to an arbitrary reference angle |
| Concentric ellipse | — | **NOT BUILT** | Nice-to-have | Constrain ellipses to share center |
| Spline assistant | — | **NOT BUILT** | Future | Guide curves |
| Perspective (1/2/3pt) | — | **NOT BUILT** | Important | Full perspective grid system |

#### Layer Operations

| Krita Tool | Graph Parti | Status | Priority |
|------------|-------------|--------|----------|
| Merge layers | — | **NOT BUILT** | Future |
| Flatten | Export PNG | **BUILT** | — |
| Clone layer | — | **NOT BUILT** | Future |
| Transform mask | — | **N/A** | — |
| Multiple named layers | 3 fixed | **PARTIAL** | Future |

### Domain 3: Pixel Painting / MS Paint Level

| Tool | Graph Parti | Status | Priority | Notes |
|------|-------------|--------|----------|-------|
| Pencil (1px) | — | **NOT BUILT** | Future | Single-pixel drawing. GP's cell text is the closest (1 char = 1 cell) |
| Bucket fill | `PaintTool` | **BUILT** | — | Region flood-fill |
| Spray can | — | **NOT BUILT** | Future | Random scatter in radius |
| Eraser | `PaintTool` right-drag | **BUILT** | — | Right-drag erases fill rects |
| Color picker/eyedropper | — | **NOT BUILT** | Important | Sample canvas color → set active |
| Crop | — | **NOT BUILT** | Nice-to-have | Crop canvas bounds |
| Canvas resize | — | **NOT BUILT** | Nice-to-have | Infinite canvas makes this less needed |
| Stamps/patterns | — | **NOT BUILT** | Future | Reusable symbol library (= AutoCAD BLOCK/INSERT) |
| Transparency/alpha | Partial (fill α=180) | **PARTIAL** | — | Fill opacity is hardcoded at 180/255 |
| Dithering patterns | — | **NOT BUILT** | Future | Ordered dither for the ASCII/1-bit render writers |
| Clean cell-fill | `PaintTool` (grid-on mode) | **BUILT** | — | Grid-on = solid cell rects, pixel-perfect within cell bounds |
| Color picker palette | 16 swatches × 2 | **BUILT** | — | Paint palette + line palette, right-click = custom picker |

---

## Section D: PySide6 Pseudocode — Critical Missing Tools

### D.1 Hatch Engine

The architect's #1 request. The intaglio aesthetic requires tone by line density, not solid fills. This needs a hatch pattern system that can fill arbitrary closed boundaries.

**Architecture:** A `HatchPattern` definition (line angle, spacing, offset) + a `HatchFill` operation (detect boundary → clip pattern to boundary → emit as `QGraphicsPathItem`).

```python
# ── hatch_engine.py ──

class HatchPattern:
    """A repeating line pattern defined by angle + spacing."""
    def __init__(self, angle_deg: float, spacing: float, offset: float = 0.0):
        self.angle = angle_deg
        self.spacing = spacing   # in grid units
        self.offset = offset

# Preset patterns (architectural standard)
PATTERNS = {
    "ansi31":    [HatchPattern(45, 1.0)],                              # section cut
    "ansi32":    [HatchPattern(45, 1.0), HatchPattern(45, 1.0, 0.5)],  # steel
    "ansi37":    [HatchPattern(45, 0.5)],                               # dense fill
    "cross":     [HatchPattern(45, 1.0), HatchPattern(-45, 1.0)],       # cross-hatch
    "brick":     [...],  # horizontal + offset vertical
    "earth":     [HatchPattern(0, 0.5), HatchPattern(90, 0.5), HatchPattern(45, 1.0)],
    "concrete":  [...],  # random dots + triangles
    "wood":      [HatchPattern(0, 0.3)],                                # horizontal grain
    "insulation":[...],  # wavy lines
}


def hatch_fill(boundary_path: QPainterPath, patterns: list[HatchPattern],
               gs: int) -> QGraphicsPathItem:
    """Fill a closed boundary with hatch lines.
    
    Algorithm:
    1. Get bounding rect of boundary_path
    2. For each HatchPattern:
       a. Generate parallel lines across the bounding rect at pattern.angle
          and pattern.spacing (converted to scene units via gs)
       b. Clip each line to the boundary using QPainterPath.intersected()
    3. Combine all clipped segments into one QGraphicsPathItem
    """
    result = QPainterPath()
    rect = boundary_path.boundingRect()
    
    for pat in patterns:
        # Expand rect to cover rotation
        diag = math.hypot(rect.width(), rect.height())
        cx, cy = rect.center().x(), rect.center().y()
        
        # Generate parallel lines perpendicular to angle
        spacing_scene = pat.spacing * gs
        rad = math.radians(pat.angle)
        perp = math.radians(pat.angle + 90)
        
        # Sweep lines across the expanded rect
        n_lines = int(diag / spacing_scene) + 2
        for i in range(-n_lines, n_lines + 1):
            offset = (i * spacing_scene) + (pat.offset * gs)
            # Line origin offset perpendicular to hatch angle
            ox = cx + offset * math.cos(perp)
            oy = cy + offset * math.sin(perp)
            # Line extends along hatch angle
            p1 = QPointF(ox - diag * math.cos(rad), oy - diag * math.sin(rad))
            p2 = QPointF(ox + diag * math.cos(rad), oy + diag * math.sin(rad))
            
            # Clip to boundary
            line_path = QPainterPath()
            line_path.moveTo(p1)
            line_path.lineTo(p2)
            clipped = boundary_path.intersected(line_path)
            # QPainterPath.intersected works on closed shapes —
            # for line clipping, use parametric intersection instead:
            # walk the line, test containment at intervals, emit segments
            
            # ALTERNATIVE (more reliable): parametric walk
            # Sample points along line, toggle in/out based on
            # boundary_path.contains(point), emit segments for "in" runs
            result.addPath(clipped)
    
    item = QGraphicsPathItem(result)
    item.setPen(make_pen("#3C3C3C", 0.5))
    item.setData(1, "hatch_fill")
    return item


class HatchTool(Tool):
    """Pick a closed boundary → fill with the active hatch pattern."""
    name = "hatch"
    
    def on_press(self, p: QPointF):
        # 1. Detect closed boundary at click point
        #    (same approach as PaintTool._fill_region — render barriers,
        #     flood fill, then trace the filled region back to a QPainterPath)
        boundary = self._detect_boundary(p)
        if boundary is None:
            return
        # 2. Apply active pattern
        pattern = self._active_pattern  # set from UI pattern picker
        item = hatch_fill(boundary, pattern, _gs(self.canvas))
        self._commit(item)
    
    def _detect_boundary(self, p: QPointF) -> QPainterPath | None:
        # Reuse PaintTool's barrier-rendering approach:
        # render geometry to QImage → flood fill → trace outline
        # → convert pixel boundary back to scene-coordinate QPainterPath
        ...
```

**Boundary detection** is the hard part. The PaintTool already solves this (renders barriers to QImage, flood fills). The hatch engine reuses that, then traces the filled region back to a `QPainterPath` for clipping.

### D.2 Dimension System

Architectural dimensions: extension lines + dimension line + centered text + arrowheads. A `DimAnnotation` compound item.

```python
# ── dimensions.py ──

class DimStyle:
    """Dimension appearance settings (architectural standard)."""
    ext_offset = 0.1       # gap between geometry and extension line start (grid units)
    ext_overshoot = 0.15   # extension line past dimension line
    arrow_size = 0.15      # arrowhead length (grid units)
    text_height = 0.3      # text height (grid units)
    text_gap = 0.05        # gap between dim line and text
    tick_style = "oblique"  # "oblique" (architectural) | "arrow" (engineering)


class LinearDimTool(Tool):
    """Click two points + offset direction → dimension annotation."""
    name = "dim_linear"
    
    def reset(self):
        self._pts = []      # [origin1, origin2, offset_point]
        self._phase = 0     # 0=pick pt1, 1=pick pt2, 2=pick offset
    
    def on_press(self, p):
        self._pts.append(QPointF(p))
        self._phase += 1
        
        if self._phase == 3:
            self._create_dimension()
            self.reset()
    
    def _create_dimension(self):
        p1, p2, offset_pt = self._pts
        gs = _gs(self.canvas)
        style = DimStyle()
        
        # Determine dimension direction (horizontal or vertical from offset)
        # ... compute dim_line endpoints, extension lines, text position
        
        path = QPainterPath()
        
        # Extension line 1: from p1 toward dim line
        # Extension line 2: from p2 toward dim line
        # Dimension line: between the two extension lines (with gap for text)
        # Arrowheads or oblique ticks at each end
        # Text: distance value centered on dimension line
        
        # The measured distance in grid units:
        dist = QLineF(p1, p2).length() / gs
        text = _dim_text(dist)
        
        # Emit as a compound QGraphicsItemGroup or single QGraphicsPathItem + child text
        item = QGraphicsPathItem(path)
        item.setPen(make_pen("#3C3C3C", 0.5))
        
        # Add text as child
        txt = QGraphicsTextItem(text, item)
        txt.setFont(QFont("VG5000", 10))
        # Position text centered on dim line midpoint
        
        item.setData(1, "dimension")
        self._commit(item)
    
    def paint_preview(self, painter):
        # Show live preview as points are picked
        ...


class LeaderTool(Tool):
    """Click endpoint → click shoulder → type text. Annotation with arrow."""
    name = "leader"
    
    def reset(self):
        self._pts = []
        self._phase = 0
    
    def on_press(self, p):
        self._pts.append(QPointF(p))
        self._phase += 1
        
        if self._phase == 2:
            # Open text input at shoulder point
            self.canvas.open_dim_input(callback=self._finish_leader)
    
    def _finish_leader(self, text: str):
        p1, p2 = self._pts  # arrowhead, shoulder
        path = QPainterPath()
        
        # Line from p1 to p2
        path.moveTo(p1)
        path.lineTo(p2)
        
        # Arrowhead at p1 (compute from direction p2→p1)
        # ... triangle or oblique tick
        
        # Horizontal landing line from p2
        landing_end = QPointF(p2.x() + len(text) * 8, p2.y())
        path.moveTo(p2)
        path.lineTo(landing_end)
        
        item = QGraphicsPathItem(path)
        item.setPen(make_pen("#3C3C3C", 0.5))
        
        # Text above the landing line
        txt = QGraphicsTextItem(text, item)
        txt.setPos(p2.x(), p2.y() - 15)
        
        item.setData(1, "leader")
        self._commit(item)
```

### D.3 Spline/Bezier Curve Tool

Smooth curves using cubic Bezier segments. PySide6's `QPainterPath.cubicTo()` does the heavy lifting.

```python
class SplineTool(Tool):
    """Click to place control points; cubic Bezier curve through them."""
    name = "spline"
    
    def reset(self):
        self._points = []       # clicked points (the curve passes through these)
        self._drawing = False
    
    def on_press(self, p):
        self._points.append(QPointF(p))
        self._drawing = True
    
    def on_double_click(self, p):
        # Finish the spline
        if len(self._points) >= 2:
            self._create_spline()
        self.reset()
    
    def _create_spline(self):
        pts = self._points
        path = QPainterPath()
        path.moveTo(pts[0])
        
        if len(pts) == 2:
            # Simple line
            path.lineTo(pts[1])
        elif len(pts) == 3:
            # Quadratic bezier (upgrade to cubic)
            path.quadTo(pts[1], pts[2])
        else:
            # Catmull-Rom → cubic Bezier conversion
            # (passes through all control points, unlike raw cubic Bezier)
            for i in range(len(pts) - 1):
                p0 = pts[max(i - 1, 0)]
                p1 = pts[i]
                p2 = pts[min(i + 1, len(pts) - 1)]
                p3 = pts[min(i + 2, len(pts) - 1)]
                
                # Catmull-Rom to cubic Bezier control points
                cp1 = QPointF(
                    p1.x() + (p2.x() - p0.x()) / 6.0,
                    p1.y() + (p2.y() - p0.y()) / 6.0
                )
                cp2 = QPointF(
                    p2.x() - (p3.x() - p1.x()) / 6.0,
                    p2.y() - (p3.y() - p1.y()) / 6.0
                )
                path.cubicTo(cp1, cp2, p2)
        
        item = QGraphicsPathItem(path)
        self._commit(item)
    
    def paint_preview(self, painter):
        if self._drawing and len(self._points) >= 1:
            painter.setPen(self._preview_pen)
            # Draw existing segments + curve preview
            ...
```

### D.4 Fillet Tool

Round corners at a specified radius. Pick two intersecting lines → compute tangent arc → trim lines → insert arc.

```python
class FilletTool(Tool):
    """Click two lines at their intersection → round with arc of set radius."""
    name = "fillet"
    
    def reset(self):
        self._radius = 1.0   # grid units (settable via Tab)
        self._first_item = None
        self._phase = 0
    
    def on_press(self, p):
        item = self._pick_item(p)
        if item is None:
            return
        
        if self._phase == 0:
            self._first_item = item
            self._first_pick = QPointF(p)
            self._phase = 1
        elif self._phase == 1:
            self._apply_fillet(self._first_item, item,
                               self._first_pick, QPointF(p))
            self.reset()
    
    def _apply_fillet(self, item1, item2, pick1, pick2):
        gs = _gs(self.canvas)
        r = self._radius * gs
        
        # 1. Get the line segments from both items
        seg1 = self._nearest_segment(item1, pick1)
        seg2 = self._nearest_segment(item2, pick2)
        
        # 2. Find intersection point
        intersect_type, ix_pt = seg1.intersects(seg2)
        if intersect_type != QLineF.IntersectionType.BoundedIntersection:
            # Try unbounded intersection
            ...
        
        # 3. Compute fillet arc center and tangent points
        # The arc center is at distance r from both lines
        # Use angle bisector + offset by r/sin(half_angle)
        angle1 = seg1.angle()
        angle2 = seg2.angle()
        half = (angle2 - angle1) / 2.0
        
        # Tangent points on each line at distance r from intersection
        # ... compute tp1 on seg1, tp2 on seg2
        
        # 4. Trim both lines to their tangent points
        # 5. Insert arc from tp1 to tp2 with radius r
        arc_path = QPainterPath()
        arc_path.moveTo(tp1)
        arc_path.arcTo(...)  # arc rect + start angle + sweep
        
        arc_item = QGraphicsPathItem(arc_path)
        self._commit(arc_item)
    
    def set_dimension(self, value):
        self._radius = value
```

### D.5 Array (Rectangular + Polar)

```python
class ArrayRectTool(Tool):
    """Select items → specify rows, cols, row spacing, col spacing → array."""
    name = "array_rect"
    
    def activate(self):
        selected = self.canvas.scene().selectedItems()
        if not selected:
            return
        # Prompt: rows, cols, row_spacing, col_spacing (via Tab input or dialog)
        rows, cols = 3, 3           # defaults (overridable)
        row_sp, col_sp = 2.0, 2.0   # grid units
        gs = _gs(self.canvas)
        
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Array rectangular")
        
        for r in range(rows):
            for c in range(cols):
                if r == 0 and c == 0:
                    continue  # skip original
                dx = c * col_sp * gs
                dy = r * row_sp * gs
                for item in selected:
                    clone = self._clone_item(item)
                    clone.moveBy(dx, dy)
                    self.canvas.add_item(clone)
        
        if us:
            us.endMacro()


class ArrayPolarTool(Tool):
    """Select items → specify center, count, total angle → polar array."""
    name = "array_polar"
    
    def _apply(self, items, center, count, total_angle):
        gs = _gs(self.canvas)
        us = self.canvas.undo_stack
        if us:
            us.beginMacro("Array polar")
        
        step = total_angle / count
        for i in range(1, count):
            angle = i * step
            for item in items:
                clone = self._clone_item(item)
                # Rotate clone around center by angle
                transform = QTransform()
                transform.translate(center.x(), center.y())
                transform.rotate(angle)
                transform.translate(-center.x(), -center.y())
                # Apply transform to clone's position
                old_pos = item.pos()
                new_pos = transform.map(old_pos)
                clone.setPos(new_pos)
                clone.setRotation(item.rotation() + angle)
                self.canvas.add_item(clone)
        
        if us:
            us.endMacro()
```

### D.6 Join Tool

```python
class JoinTool(Tool):
    """Click items to join into a single polyline/path."""
    name = "join"
    
    def on_press(self, p):
        # Find all selected items (or items near click)
        selected = self.canvas.scene().selectedItems()
        if len(selected) < 2:
            return
        
        # Extract all segments from selected items
        all_segs = []
        for item in selected:
            all_segs.extend(_item_segments(item))
        
        # Build a connected path by chaining segments endpoint-to-endpoint
        # (tolerance = snap distance)
        tolerance = _gs(self.canvas) * 0.1
        path = self._chain_segments(all_segs, tolerance)
        
        if path is not None:
            us = self.canvas.undo_stack
            if us:
                us.beginMacro("Join")
            # Remove originals
            for item in selected:
                self.canvas.remove_item(item)
            # Add joined path
            joined = QGraphicsPathItem(path)
            self._commit(joined)
            if us:
                us.endMacro()
    
    def _chain_segments(self, segs, tol) -> QPainterPath | None:
        # Greedy nearest-endpoint chaining
        # Start from first segment, repeatedly find the segment whose
        # endpoint is closest to the current chain's tail
        ...
```

### D.7 Eyedropper

```python
class EyedropperTool(Tool):
    """Click to sample color from the canvas."""
    name = "eyedropper"
    
    def on_press(self, p):
        # Method 1: Check if click hits a filled item
        items = self.canvas.scene().items(p)
        for item in items:
            if item.data(1) == "cell_fill":
                # Get the fill color from the pixmap or brush
                if hasattr(item, 'brush') and item.brush().style() != Qt.BrushStyle.NoBrush:
                    color = item.brush().color()
                    self.canvas.set_fill_color(color.name())
                    return
            if hasattr(item, 'pen'):
                color = item.pen().color()
                self.canvas.set_stroke_color(color.name())
                return
        
        # Method 2: Render scene to QImage at click point, sample pixel
        rect = QRectF(p.x() - 1, p.y() - 1, 2, 2)
        img = QImage(2, 2, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        self.canvas.scene().render(painter, QRectF(0, 0, 2, 2), rect)
        painter.end()
        
        pixel = img.pixelColor(1, 1)
        if pixel.alpha() > 0:
            self.canvas.set_fill_color(pixel.name())
```

### D.8 Construction Lines

```python
class ConstructionLineTool(Tool):
    """Click two points → infinite reference line (clipped to viewport)."""
    name = "xline"
    
    def reset(self):
        self._start = None
        self._drawing = False
    
    def on_press(self, p):
        if not self._drawing:
            self._start = QPointF(p)
            self._drawing = True
        else:
            self._create_xline(self._start, QPointF(p))
            self.reset()
    
    def _create_xline(self, p1, p2):
        # Create a very long line through both points
        line = QLineF(p1, p2)
        if line.length() < 1e-6:
            return
        
        # Extend in both directions by a large factor
        EXTENT = 100000  # scene units (effectively infinite)
        line.setLength(EXTENT)
        extended_p2 = line.p2()
        line.setP1(p2)
        line.setP2(p1)
        line.setLength(EXTENT)
        extended_p1 = line.p2()
        
        item = QGraphicsLineItem(QLineF(extended_p1, extended_p2))
        pen = QPen(QColor("#2464E5"))  # blue construction line
        pen.setWidthF(0.5)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.DashDotLine)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, {"zip": "", "note": ""})
        item.setData(1, "construction")
        self.canvas.add_item(item)
```

### D.9 Property Match

```python
class MatchPropTool(Tool):
    """Click source → click targets. Copies pen/brush/properties."""
    name = "matchprop"
    
    def reset(self):
        self._source = None
        self._phase = 0
    
    def on_press(self, p):
        item = self._pick_item(p)
        if item is None:
            return
        
        if self._phase == 0:
            # Store source properties
            self._source = item
            self._src_pen = item.pen() if hasattr(item, 'pen') else None
            self._src_brush = item.brush() if hasattr(item, 'brush') else None
            self._phase = 1
        else:
            # Apply to target
            if self._src_pen and hasattr(item, 'setPen'):
                item.setPen(QPen(self._src_pen))
            if self._src_brush and hasattr(item, 'setBrush'):
                item.setBrush(QBrush(self._src_brush))
            # Stay in phase 1 to keep applying (click more targets)
            # Right-click or Escape to exit
```

### D.10 Polyline Edit (PEDIT)

```python
class PEditTool(Tool):
    """Select a polyline → show vertex handles → drag to edit."""
    name = "pedit"
    
    def activate(self):
        # Show handles on any selected QGraphicsPathItem
        selected = [i for i in self.canvas.scene().selectedItems()
                    if isinstance(i, QGraphicsPathItem)]
        if selected:
            self._target = selected[0]
            self._show_handles()
    
    def _show_handles(self):
        """Place draggable handle items at each vertex of the path."""
        path = self._target.path()
        self._handles = []
        for i in range(path.elementCount()):
            el = path.elementAt(i)
            pt = self._target.mapToScene(QPointF(el.x, el.y))
            handle = QGraphicsEllipseItem(-3, -3, 6, 6)
            handle.setBrush(QBrush(QColor("#2464E5")))
            handle.setPos(pt)
            handle.setData(2, i)  # vertex index
            handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.canvas.scene().addItem(handle)
            self._handles.append(handle)
    
    def on_release(self, p):
        # After dragging a handle, rebuild the path with the new vertex position
        for handle in self._handles:
            idx = handle.data(2)
            new_pos = self._target.mapFromScene(handle.pos())
            # Rebuild QPainterPath with updated vertex
            ...
    
    def _insert_vertex(self, after_idx, point):
        """Insert a new vertex after the given index."""
        ...
    
    def _delete_vertex(self, idx):
        """Remove the vertex at the given index."""
        ...
```

---

## Section E: Architecture Implications

### E.1 Hatch Engine (NEW SUBSYSTEM)

**What it needs:**
- `hatch_engine.py` — pattern definitions + boundary detection + line clipping
- Pattern preset library (ANSI standard + architectural materials)
- Boundary detection: reuse PaintTool's barrier-rendering approach, then trace the flood-filled region back to a `QPainterPath`
- UI: pattern picker (dropdown or palette), angle + spacing controls
- `.parti` save/load: serialize pattern name + boundary path

**Key Qt6 capabilities:**
- `QPainterPath.intersected()` for shape boolean ops (boundary clipping)
- `QPainterPath.contains(QPointF)` for parametric line-in-boundary testing
- `QPainterPathStroker` for converting stroked paths to filled shapes

**Risk:** `QPainterPath.intersected()` operates on closed shapes, not open lines. Line clipping needs a parametric walk (sample points along line, test containment, emit "in" segments). This is the most complex new subsystem.

### E.2 Dimension System (NEW SUBSYSTEM)

**What it needs:**
- `dimensions.py` — `DimStyle` configuration + dimension tool classes
- `LinearDimTool`, `AlignedDimTool`, `AngularDimTool`, `RadiusDimTool`, `LeaderTool`
- Each dimension = a compound `QGraphicsItemGroup` (lines + arrowheads + text)
- Dimensions should be **associative** (if the geometry moves, the dimension updates) — this requires watching item position changes via signals

**Key Qt6 capabilities:**
- `QGraphicsItemGroup` for compound annotation items
- `QGraphicsItem.ItemPositionHasChanged` flag for associative updates
- `QGraphicsTextItem` for dimension text

**Risk:** Associative dimensions (auto-updating when geometry moves) require a signal/slot connection between the dimensioned items and the dimension annotation. Non-associative (static) dimensions are much simpler and may be the right v1.

### E.3 Spline/Bezier System

**What it needs:**
- `SplineTool` for drawing curves (click control points, double-click to finish)
- Catmull-Rom → cubic Bezier conversion (curve passes through all clicked points)
- Control point editing after creation (draggable handles showing tangent direction)
- Integration with trim, extend, offset (these all need to handle curved segments)

**Key Qt6 capabilities:**
- `QPainterPath.cubicTo(cp1, cp2, end)` — native cubic Bezier
- `QPainterPath.quadTo(cp, end)` — native quadratic Bezier
- All existing segment-extraction (`_item_segments()`) needs updating to handle curves

**Risk:** Trim and offset on curved segments are significantly more complex than on line segments. Offset of a Bezier is not itself a Bezier (it's an approximation). This will require `_item_segments()` to either approximate curves as polylines (for trim/offset) or implement true curve-curve intersection.

### E.4 Layer System Upgrade (FUTURE)

**What it needs:**
- User-created named layers beyond the fixed parti/trace/book
- Layer visibility, lock, color override
- Layer panel in the UI

**Key Qt6 capabilities:**
- `QGraphicsItem.setVisible()`, `setEnabled()`, `setOpacity()`
- Items are already added to the scene with layer metadata; extending to N layers is straightforward

**Complexity:** Medium. The `Document` class currently hardcodes 3 layers. Needs refactoring to a dynamic layer list, but the per-item scene model doesn't change.

### E.5 Line Type System

**What it needs:**
- `QPen.setDashPattern([dash, gap, dash, gap, ...])` for custom dash patterns
- Preset line types: continuous, dashed, center, hidden, phantom, section-cut
- Per-item line type stored in item data, saved to `.parti`
- Line type picker in toolbar or properties panel

**Key Qt6 capabilities:**
- `QPen.setDashPattern()` accepts arbitrary `list[float]` dash/gap sequences
- `QPen.setDashOffset()` for pattern alignment
- Cosmetic pens (`setCosmetic(True)`) ensure pattern is screen-constant

**Complexity:** Low-medium. The pen infrastructure exists; this is adding a picker and pattern definitions.

### E.6 Perspective Assistants (FUTURE)

**What it needs:**
- Vanishing point placement (1-point, 2-point, 3-point perspective)
- Lines drawn while assistant is active snap toward vanishing points
- Visual guide lines radiating from each VP

**Key Qt6 capabilities:**
- The snap system (`_resolve_snap` in `canvas_view.py`) already prioritizes osnap > grid snap. A perspective snap would be a third tier: project the cursor onto the nearest VP-line.

**Complexity:** Large. Requires new snap mode, VP management UI, and visual guide rendering. But high value for the architect (perspective drawing is fundamental to architecture).

---

## Summary: Recommended Build Order

### Wave 1 — Daily Workflow Unblocked
1. **Copy at Origin** (trivial — clone + single move)
2. **Eyedropper** (trivial — sample color at click)
3. **Construction Lines** (trivial — long dashed line through two points)
4. **Property Match** (trivial — read pen/brush from source, apply to target)
5. **Polygon** (trivial — N-point circle subdivision)
6. **Array Rectangular** (trivial — clone + translate in loop)
7. **Array Polar** (trivial — clone + rotate in loop)

### Wave 2 — Modify Vocabulary Complete
8. **Join** (medium — endpoint chaining into QPainterPath)
9. **Fillet** (medium — tangent arc computation)
10. **Chamfer** (medium — similar to fillet, simpler geometry)
11. **PEDIT / Polyline Edit** (medium — vertex handle system)
12. **Break** (medium — point-on-curve + split)

### Wave 3 — Annotation + Render
13. **Dimension System** (linear + aligned + leader) (medium — compound items)
14. **Hatch Engine** (large — boundary detection + pattern clipping)
15. **Line Types** (medium — dash patterns + picker)
16. **Line Weights** (medium — weight picker + ISO presets)

### Wave 4 — Curves + Advanced
17. **Spline/Bezier** (medium-large — Catmull-Rom + control handles + trim integration)
18. **Crossing Select** (medium — selection mode that picks touching items)
19. **Stretch** (medium — vertex-subset move)
20. **Area/Distance Inquiry** (trivial — shoelace formula + two-click measurement)

### Wave 5 — Future / DLC
21. Perspective assistants, vanishing points
22. Multiple named layers
23. Raster paint layer (Krita-style freehand brush)
24. Blocks/symbols library (reusable component stamps)
25. Gradient fills (watercolor wash renderer)
26. Animation support (re-render per frame)

---

`∑ built = 17 tools + 12 operations · critical-missing = 20 · full-map-rows = 120+ · pseudocode-sketches = 10 · new-subsystems = 6 · waves = 5`
