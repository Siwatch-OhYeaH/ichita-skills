# Process Diagram Drawing — Complete Reference

Draw process flow diagrams, block diagrams, and simplified P&IDs as native editable PowerPoint shapes using PptxGenJS + `process-diagram-lib.cjs`.

**Read this ENTIRE file before drawing any process diagram.**

> For ICHITA work: also read [ichita-defaults.md](../../assets/brand/ichita-defaults.md) for brand colors, fonts, and patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Mode A: Block Diagram](#mode-a-block-diagram)
4. [Mode B: Process Diagram](#mode-b-process-diagram)
5. [Unit Operation Catalog](#unit-operation-catalog)
6. [Layout Patterns & Stream Routing](#layout-patterns--stream-routing)
7. [Stream Annotation Conventions](#stream-annotation-conventions)
8. [Multi-Slide Strategy](#multi-slide-strategy)
9. [Complete Examples](#complete-examples)

---

## Overview

- **Two modes**: Block Diagram (simple rectangles) and Process Diagram (equipment symbols)
- **Native shapes**: all output is editable in PowerPoint — no images, no external tools
- **Helper library**: `scripts/process-diagram-lib.cjs` provides unit operations, stream routing, layout, and annotations
- **Connection points**: every unit returns `{ in, out, top, bottom }` positions for stream routing
- **ICHITA integration**: use ICHITA colors from [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) for branded diagrams

---

## Workflow

Follow these steps for every process diagram:

### 1. Understand the Process

List **all** unit operations and **all** streams (feed, product, recycle, waste). Identify:
- What goes in and what comes out of each unit
- Process conditions at key points (temperature, Brix, pH, flow rate)
- Any recycle loops or bypass streams

### 2. Classify the Topology

| Topology | Description | When to Use |
|----------|-------------|-------------|
| **Linear** | A → B → C → D | Simple sequential processes |
| **Branching** | A → B → [C, D] | Extract/raffinate splits, product diversification |
| **Recycle** | A → B → C, C.bottom → A | Chromatography recycle, mother liquor return |
| **Tree** | A → [B, C, D] → [E, F, G, ...] | Product portfolio, multi-product plants |
| **Parallel** | [A1, A2] → B | Duplicate trains, multi-column systems |

### 3. Choose Mode

- **Block Diagram** — overview slides, proposals, first-pass design
- **Process Diagram** — technical discussions, engineering presentations

### 4. Plan Grid Layout (ASCII First!)

**Always** sketch the layout in ASCII before writing code. This catches routing problems early.

```
Example ASCII sketch:
  Feed → [Tank] → [Reactor] → [Filter] → [Evaporator] → Product
                                  ↓
                              [Waste]
```

### 5. Write JS

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, layout, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

// Draw units, connect with streams, add annotations
// ... (see examples below)

pres.writeFile({ fileName: "process-diagram.pptx" });
```

### 6. Visual QA

Generate thumbnails and verify:
- No overlapping shapes
- Stream arrows point correct direction
- Labels are readable (not overlapping streams)
- Recycle loops route cleanly below/above main flow
- Adequate spacing between all elements (min 0.3")

```bash
python scripts/thumbnail.py process-diagram.pptx workspace/thumbnails --cols 4
```

---

## Mode A: Block Diagram

Every unit is a colored rectangle with label + optional conditions. Streams are arrow lines with optional labels.

### When to Use

- Overview slides in proposals
- First-pass process design
- Non-technical audiences
- Quick visualization of material flow

### Design Guidelines

- All blocks same height, width varies by label length
- Main flow: left-to-right
- Color scheme: use 2-3 colors max to categorize units (e.g., blue for separation, green for thermal)
- Stream labels: concise, above or beside the arrow
- Title at top, legend at bottom-right if using color categories

### Block Diagram Code Pattern

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

// Title
annotations.title(slide, pres, "Sweetener Production — Block Diagram");

// Units: position manually or use layout.linear()
const W = 1.3, H = 0.8, Y = 2.0, GAP = 0.5;
const dissolution = units.block(slide, pres, 0.4, Y, { w: W, h: H, label: "Dissolution", color: "2978FF" });
const filtration  = units.block(slide, pres, 0.4 + (W + GAP), Y, { w: W, h: H, label: "Filtration", color: "2978FF" });
const decolor     = units.block(slide, pres, 0.4 + 2 * (W + GAP), Y, { w: W, h: H, label: "Decolorization", color: "82B0FF" });
const ixPurif     = units.block(slide, pres, 0.4 + 3 * (W + GAP), Y, { w: W, h: H, label: "IX Purification", color: "82B0FF" });
const evaporation = units.block(slide, pres, 0.4 + 4 * (W + GAP), Y, { w: W, h: H, label: "Evaporation", color: "34A853" });

// Streams
streams.connect(slide, pres, dissolution.out, filtration.in);
streams.connect(slide, pres, filtration.out, decolor.in);
streams.connect(slide, pres, decolor.out, ixPurif.in);
streams.connect(slide, pres, ixPurif.out, evaporation.in, { label: "Brix 15%" });

pres.writeFile({ fileName: "sweetener-block.pptx" });
```

---

## Mode B: Process Diagram

Units drawn with recognizable equipment symbols. Streams are pipe lines with arrowheads and labels. Process conditions annotated at key points.

### When to Use

- Technical presentations
- Engineering discussions
- Detailed proposals with process conditions
- Equipment sizing discussions

### Design Guidelines

- Use appropriate unit symbols from the catalog below
- Annotate key streams with conditions (Brix, purity, flow, temperature)
- Show recycle loops explicitly with routed return lines
- Use `annotations.conditions()` for boxed process data
- Equipment labels below or inside the symbol
- Pumps shown inline between units where relevant

### Process Diagram Code Pattern

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

annotations.title(slide, pres, "Purification Train — Process Diagram");

// Equipment
const feedTank = units.tank(slide, pres, 0.3, 1.5, { label: "Feed\nTank", color: "2978FF" });
const saFilter = units.filter(slide, pres, 2.0, 1.6, { label: "Safety\nFilter", color: "82B0FF" });
const ixCol1   = units.column(slide, pres, 3.8, 1.2, { label: "SAC", color: "2978FF" });
const ixCol2   = units.column(slide, pres, 5.0, 1.2, { label: "WBA", color: "2978FF" });
const evap     = units.evaporator(slide, pres, 6.8, 1.2, { label: "Evaporator", color: "34A853" });

// Streams
streams.connect(slide, pres, feedTank.out, saFilter.in, { label: "Brix 50%" });
streams.connect(slide, pres, saFilter.out, ixCol1.in);
streams.connect(slide, pres, ixCol1.out, ixCol2.in);
streams.connect(slide, pres, ixCol2.out, evap.in, { label: "Brix 15%\nPurity 98%" });

// Process conditions annotation
annotations.conditions(slide, pres, 7.0, 3.0, [
  "Feed: 50 Brix", "Product: 72 Brix", "Temp: 60-80 C"
]);

pres.writeFile({ fileName: "purification-process.pptx" });
```

---

## Unit Operation Catalog

Every unit function signature: `units.NAME(slide, pres, x, y, opts)`

Returns: `{ x, y, w, h, in, out, top, bottom, ...extras }`

### Vessels & Tanks

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.tank` | Rectangle + dashed level line | 1.2 x 1.0 | Feed, product, buffer, precoat tanks |
| `units.block` | Simple colored rectangle | 1.2 x 0.9 | Generic block diagram unit |

### Reactors

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.reactor` | Rectangle + agitator shaft + motor | 1.2 x 1.0 | Enzyme reactor, inversion tank, jet cooker |

### Separation

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.filter` | Rectangle + dashed midline | 1.2 x 0.9 | Filter press, leaf filter, safety filter, RVF |
| `units.membrane` | Rectangle + vertical dashed line | 1.2 x 0.9 | UF, NF, RO. Extra points: `.permeate`, `.retentate` |

### Ion Exchange & Chromatography

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.column` | Tall thin rectangle + bed dividers | 0.7 x 1.4 | SAC, WBA, SBA, mixed bed |
| `units.smbSystem` | Dashed box + multiple columns | 2.0 x 1.4 | SMB chromatography. Extra points: `.extract`, `.raffinate`, `.feed`, `.eluent` |
| `units.carbonColumn` | Rectangle + carbon dots | 0.8 x 1.2 | GAC/PAC columns |

### Thermal

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.evaporator` | Rectangle + steam "~ ~ ~" | 1.0 x 1.2 | Extra point: `.vapor` |
| `units.crystallizer` | Rectangle + diamond symbols | 1.2 x 1.0 | Sugar crystallizer, cooling crystallizer |
| `units.dryer` | Rectangle + heat arrows | 1.2 x 0.9 | Spray dryer, rotary dryer |
| `units.heatExchanger` | Circle + cross lines | 0.7 x 0.7 | Shell-and-tube, plate HX |

### Transfer & Mixing

| Function | Visual | Default Size | Notes |
|----------|--------|--------------|-------|
| `units.pump` | Circle + triangle arrow | 0.45 x 0.45 | Centrifugal, positive displacement |
| `units.mixer` | Square + X cross | 0.5 x 0.5 | Static mixer, blending point |

### Common Options (all units)

```javascript
{
  w: 1.2,              // width (inches)
  h: 0.9,              // height (inches)
  color: "2978FF",     // fill color (NO # prefix)
  textColor: "FFFFFF", // label text color
  label: "Unit Name",  // multi-line with \n
  labelSize: 8,        // font size (pt)
  fontFace: "Calibri", // font family
  borderColor: "263338",
  borderWidth: 1.5,
}
```

### Connection Points

Every unit returns these connection points (all are `{ x, y }` objects):

```
        top
         |
  in --- [UNIT] --- out
         |
       bottom
```

Special units have additional points:
- **membrane**: `.permeate`, `.retentate` (right side, upper/lower)
- **smbSystem**: `.extract`, `.raffinate` (right), `.feed`, `.eluent` (left)
- **evaporator**: `.vapor` (top center)
- **reactor**: `.top` adjusted for motor position

---

## Layout Patterns & Stream Routing

### Pattern 1: Linear Flow

Left-to-right, single row. Best for simple sequential processes.

```
  Feed → [A] → [B] → [C] → [D] → Product
```

Use `layout.linear()` for auto-positioning:

```javascript
const defs = [{ w: 1.2 }, { w: 1.2 }, { w: 1.2 }, { w: 1.2 }];
const pos = layout.linear(defs, 10, 0.5, 1.8, 0.6);
// pos[0] = { x: 0.5, y: 1.8 }, pos[1] = { x: 2.3, y: 1.8 }, ...
```

### Pattern 2: Multi-Row (Wrap)

When slide width is exceeded, wrap to next row. Use `layout.multiRow()`.

```
  [A] → [B] → [C] → [D]
  [E] → [F] → [G] → Product
```

Connect end of row 1 to start of row 2 with an L-bend:

```javascript
// Connect last unit of row 1 to first of row 2
streams.connect(slide, pres, unitD.out, unitE.in, { bendDirection: "vertical-first" });
```

### Pattern 3: Branching

Main flow splits at a point (e.g., chromatography extract/raffinate).

```
                    → [Extract processing] → Extract product
  Feed → [Chromo] <
                    → [Raffinate processing] → Raffinate product
```

Use `streams.branch()` or two separate `streams.connect()` calls:

```javascript
streams.connect(slide, pres, chromo.extract, extractTank.in, { label: "Extract" });
streams.connect(slide, pres, chromo.raffinate, raffinateTank.in, { label: "Raffinate" });
```

### Pattern 4: Recycle Streams

Return lines routed BELOW the main flow (or ABOVE if below is occupied).

```
  Feed → [Reactor] → [Chromo] → Product
              ↑           |
              └───────────┘  Recycle (routed below)
```

Use `streams.recycle()`:

```javascript
streams.recycle(slide, pres, chromo.bottom, reactor.in, {
  label: "Fructose recycle",
  routeY: 4.2,  // Y position for horizontal segment
});
```

### Pattern 5: Parallel Trains

Duplicate units side by side, merging into a common downstream.

```
  Feed → [Train A] →
                      → [Merge] → Product
  Feed → [Train B] →
```

Use `streams.branch()` in reverse or manual L-bends.

### Pattern 6: Process Tree

One feed produces multiple products (branching downward).

```
         [Starch]
        /    |    \
  [Glucose] [Fructose] [Maltodextrin]
```

### Routing Rules

1. **Main flow**: always left-to-right
2. **Recycle lines**: route BELOW main flow (use `routeY` > max unit Y). Route ABOVE only if below is occupied.
3. **By-product streams**: exit downward from unit `.bottom`
4. **Feed enters**: from left edge of slide
5. **Products exit**: right edge or bottom-right
6. **Minimum gap**: 0.3" between all elements
7. **Stream labels**: positioned above or beside the line, never overlapping units
8. **Recycle labels**: placed on the horizontal return segment

### Stream Connection Functions

```javascript
// Straight or L-bend connection
streams.connect(slide, pres, from, to, {
  label: "Stream name",      // optional label at midpoint
  color: "263338",            // line color
  width: 1.5,                // line width (pt)
  bendDirection: "horizontal-first", // or "vertical-first"
});

// U-shaped recycle return
streams.recycle(slide, pres, from, to, {
  label: "Recycle",
  routeY: 4.5,              // Y for horizontal routing segment
  routeAbove: false,         // true = route above units
});

// One-to-many split
streams.branch(slide, pres, from, [target1, target2], {
  labels: ["Extract", "Raffinate"],
  branchX: 5.0,             // X position of branch backbone
});
```

---

## Stream Annotation Conventions

### Format

```
"Stream Name\nCondition1 | Condition2"
```

Or use `annotations.conditions()` for a boxed multi-line annotation:

```javascript
annotations.conditions(slide, pres, 3.5, 3.8, [
  "Brix: 42%",
  "Purity: 95% DS",
  "Flow: 12 Ton DS/day",
  "Temp: 60 C",
]);
```

### Common Process Conditions

| Parameter | Format | Example |
|-----------|--------|---------|
| Concentration | Brix % | `Brix: 42%` |
| Purity | % on DS | `Purity: 95% DS` |
| Flow rate | Ton DS/day or m3/h | `Flow: 12 Ton DS/day` |
| Temperature | C | `Temp: 60 C` |
| pH | dimensionless | `pH: 5.0` |
| Pressure | bar or kPa | `Press: 3.5 bar` |
| Color | IU or ICUMSA | `Color: 45 IU` |

### Mass Balance Annotation

```javascript
annotations.massBalance(slide, pres, 6.0, 3.5, {
  stream: "Product",
  flow: "8.5 Ton DS/day",
  brix: "72%",
  purity: "99.5% DS",
  temp: "45 C",
});
```

### Style

- Font: 7pt, muted color (`788F9C`)
- Background: light box (`F8FAFB`) with thin border
- Position: near the stream midpoint or beside the unit

---

## Multi-Slide Strategy

### Slide 1: Overview Block Diagram

Full process from raw material to product as a simplified block diagram. Shows the big picture.

```javascript
// Use units.block() for all units
// Simple left-to-right or multi-row layout
// Color-code by section (purification = blue, thermal = green, etc.)
```

### Slide 2+: Detail Sections

Zoom into each section of the process with full equipment symbols and annotations.

```javascript
// Use specific unit types (reactor, column, evaporator, etc.)
// Add process conditions at key points
// Show recycle loops in detail
```

### Mass Balance Slide

Annotated diagram with quantities at each stage.

```javascript
// Use the overview block diagram layout
// Add annotations.massBalance() at every stream
// Include a summary table below the diagram
```

### Recommended Slide Sequence

1. **Title slide** — project name, customer, date
2. **Overview** — full process block diagram
3. **Section details** — one slide per major section
4. **Mass balance** — annotated with flow rates
5. **Equipment list** — table of major equipment (optional)

---

## Complete Examples

### Example 1: Simple Linear Block Diagram (5 units)

A basic sweetener purification process.

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

// Top accent line
slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "2978FF" } });
annotations.title(slide, pres, "Sugar Syrup Purification — Overview");

const Y = 2.2, W = 1.4, H = 0.85;
const colors = { prep: "2978FF", sep: "82B0FF", thermal: "34A853" };

const dissolve = units.block(slide, pres, 0.3, Y, { w: W, h: H, label: "Dissolution", color: colors.prep });
const filt     = units.block(slide, pres, 2.1, Y, { w: W, h: H, label: "Filtration", color: colors.sep });
const decolor  = units.block(slide, pres, 3.9, Y, { w: W, h: H, label: "Decolorization", color: colors.sep });
const ionex    = units.block(slide, pres, 5.7, Y, { w: W, h: H, label: "Ion Exchange", color: colors.sep });
const evap     = units.block(slide, pres, 7.5, Y, { w: W, h: H, label: "Evaporation", color: colors.thermal });

streams.connect(slide, pres, dissolve.out, filt.in);
streams.connect(slide, pres, filt.out, decolor.in);
streams.connect(slide, pres, decolor.out, ionex.in, { label: "Brix 42%" });
streams.connect(slide, pres, ionex.out, evap.in, { label: "Brix 15%" });

// Feed and product labels
streams.label(slide, pres, 0.0, Y + H / 2, "Raw Sugar", { labelSize: 8 });
streams.label(slide, pres, 9.2, Y + H / 2, "Syrup 72 Bx", { labelSize: 8 });

// Legend
annotations.legend(slide, pres, 7.5, 4.0, [
  { label: "Preparation", color: colors.prep },
  { label: "Separation", color: colors.sep },
  { label: "Thermal", color: colors.thermal },
]);

pres.writeFile({ fileName: "sweetener-overview.pptx" });
```

### Example 2: Sugar Decolorization with Regeneration Loop

Medium complexity — includes a recycle/regeneration stream.

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "2978FF" } });
annotations.title(slide, pres, "GAC Decolorization with Regeneration");

// Main flow
const feedTank = units.tank(slide, pres, 0.3, 1.5, { label: "Feed\nTank", color: "2978FF" });
const gac1     = units.carbonColumn(slide, pres, 2.3, 1.3, { label: "GAC-1" });
const gac2     = units.carbonColumn(slide, pres, 3.8, 1.3, { label: "GAC-2" });
const saFilter = units.filter(slide, pres, 5.5, 1.6, { label: "Safety\nFilter", color: "82B0FF" });
const product  = units.tank(slide, pres, 7.5, 1.5, { label: "Product\nTank", color: "34A853" });

// Regeneration unit (below main flow)
const regen = units.block(slide, pres, 3.0, 3.8, { w: 1.5, h: 0.7, label: "GAC Regen\n(Kiln)", color: "FFA000" });

// Main flow streams
streams.connect(slide, pres, feedTank.out, gac1.in, { label: "50 Bx" });
streams.connect(slide, pres, gac1.out, gac2.in);
streams.connect(slide, pres, gac2.out, saFilter.in, { label: "< 100 IU" });
streams.connect(slide, pres, saFilter.out, product.in);

// Regeneration loop
streams.connect(slide, pres, gac1.bottom, regen.top, { label: "Spent GAC" });
streams.recycle(slide, pres, regen.out, gac1.top, {
  label: "Regenerated GAC",
  routeY: 4.8,
});

pres.writeFile({ fileName: "decolorization-regen.pptx" });
```

### Example 3: Allulose Process with Chromatography + Recycles

Complex topology — two chromatography systems, recycle loops, multiple product streams.

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "2978FF" } });
annotations.title(slide, pres, "Allulose Production — Full Process");

// Row 1: Reaction + first chromatography
const Y1 = 1.2;
const enzReactor = units.reactor(slide, pres, 0.3, Y1, { w: 1.0, h: 0.9, label: "Enzyme\nReactor", color: "2978FF" });
const decolor    = units.block(slide, pres, 1.8, Y1, { w: 1.0, h: 0.9, label: "Decolor", color: "82B0FF" });
const smb1       = units.smbSystem(slide, pres, 3.3, Y1 - 0.15, { w: 1.8, h: 1.2, label: "SMB-1", numCols: 4, color: "2978FF" });
const evap1      = units.evaporator(slide, pres, 5.8, Y1 - 0.1, { w: 0.9, h: 1.1, label: "Evap-1", color: "34A853" });

// Row 1 continued: second chromatography + final
const smb2       = units.smbSystem(slide, pres, 7.2, Y1 - 0.15, { w: 1.6, h: 1.2, label: "SMB-2", numCols: 3, color: "2978FF" });

// Row 2: Product finishing
const Y2 = 3.3;
const evap2      = units.evaporator(slide, pres, 7.5, Y2, { w: 0.9, h: 1.0, label: "Evap-2", color: "34A853" });
const product    = units.tank(slide, pres, 9.0, Y2 + 0.1, { w: 0.8, h: 0.8, label: "Product", color: "34A853" });

// Main flow
streams.connect(slide, pres, enzReactor.out, decolor.in, { label: "Conv. 30%" });
streams.connect(slide, pres, decolor.out, smb1.feed);
streams.connect(slide, pres, smb1.extract, evap1.in, { label: "Allulose\nrich" });
streams.connect(slide, pres, evap1.out, smb2.feed);
streams.connect(slide, pres, smb2.extract, evap2.top, { label: "High purity" });
streams.connect(slide, pres, evap2.out, product.in);

// Recycle 1: SMB-1 raffinate back to reactor
streams.recycle(slide, pres, smb1.raffinate, enzReactor.in, {
  label: "Fructose recycle",
  routeY: 4.8,
});

// Recycle 2: SMB-2 raffinate back to SMB-1
streams.recycle(slide, pres, smb2.raffinate, smb1.feed, {
  label: "Allulose-lean recycle",
  routeY: 5.0,
});

// Conditions
annotations.conditions(slide, pres, 0.3, 3.5, [
  "Feed: Fructose syrup",
  "Enzyme: D-psicose 3-epimerase",
  "Temp: 55-60 C",
  "pH: 7.5-8.0",
]);

annotations.massBalance(slide, pres, 9.0, 4.3, {
  stream: "Final Product",
  brix: "72%",
  purity: ">95% Allulose",
});

pres.writeFile({ fileName: "allulose-full-process.pptx" });
```

### Example 4: Product Tree (Starch Derivatives)

Branching downward from one feed to multiple products.

```javascript
const pptxgen = require("pptxgenjs");
const { units, streams, annotations } = require("./process-diagram-lib");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "2978FF" } });
annotations.title(slide, pres, "Starch Derivatives — Product Portfolio");

// Root
const starch = units.block(slide, pres, 4.0, 0.8, { w: 2.0, h: 0.7, label: "Corn Starch\nSlurry", color: "263338" });

// Level 1 — primary processes
const liquefaction = units.block(slide, pres, 1.0, 2.0, { w: 1.6, h: 0.65, label: "Liquefaction", color: "2978FF" });
const maltodex     = units.block(slide, pres, 4.0, 2.0, { w: 1.6, h: 0.65, label: "Partial\nHydrolysis", color: "2978FF" });
const cyclodex     = units.block(slide, pres, 7.0, 2.0, { w: 1.6, h: 0.65, label: "Cyclization", color: "82B0FF" });

// Level 2 — products
const glucose  = units.block(slide, pres, 0.2, 3.5, { w: 1.3, h: 0.6, label: "Glucose\nSyrup", color: "34A853" });
const fructose = units.block(slide, pres, 1.8, 3.5, { w: 1.3, h: 0.6, label: "Fructose\nSyrup", color: "34A853" });
const malto    = units.block(slide, pres, 4.0, 3.5, { w: 1.3, h: 0.6, label: "Maltodextrin", color: "34A853" });
const cyclo    = units.block(slide, pres, 7.0, 3.5, { w: 1.3, h: 0.6, label: "Cyclodextrin", color: "34A853" });

// Branch from starch to level 1
streams.branch(slide, pres, starch.bottom, [liquefaction.top, maltodex.top, cyclodex.top]);

// Level 1 → Level 2
streams.branch(slide, pres, liquefaction.bottom, [glucose.top, fructose.top], {
  labels: ["Saccharification", "Isomerization"],
});
streams.connect(slide, pres, maltodex.bottom, malto.top);
streams.connect(slide, pres, cyclodex.bottom, cyclo.top);

pres.writeFile({ fileName: "starch-product-tree.pptx" });
```

---

## Tips & Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Overlapping labels | Increase gap between units, shorten labels, reduce `labelSize` |
| Stream arrows wrong direction | Check `from` and `to` order — arrow always points toward `to` |
| Recycle line overlaps units | Increase `routeY` value to push routing further below |
| Too many units for one slide | Use `layout.multiRow()` or split into multiple detail slides |
| Labels cut off | Increase unit `w` or use `\n` to wrap label text |
| Colors look wrong | Remember: NO `#` prefix on hex colors |

### Performance

- Keep to 15-20 units max per slide for readability
- Use block diagrams for >10 units on overview slides
- Detailed equipment symbols work best with 5-8 units per slide

### Customizing Unit Shapes

You can create custom units by combining basic PptxGenJS shapes and returning connection points:

```javascript
function customUnit(slide, pres, x, y, opts) {
  // Draw your shapes...
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: opts.w, h: opts.h, fill: { color: opts.color } });
  // Add decorations...
  // Return connection points
  return {
    x, y, w: opts.w, h: opts.h,
    in:     { x: x,           y: y + opts.h / 2 },
    out:    { x: x + opts.w,  y: y + opts.h / 2 },
    top:    { x: x + opts.w / 2, y: y },
    bottom: { x: x + opts.w / 2, y: y + opts.h },
  };
}
```

---

## Dependencies

- **pptxgenjs**: `npm install pptxgenjs`
- **process-diagram-lib.cjs**: `scripts/process-diagram-lib.cjs` (this skill)
- **thumbnail.py**: `scripts/thumbnail.py` (for visual QA)
