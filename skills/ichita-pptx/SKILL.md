---
name: ichita-pptx
description: "Use when creating Ichita-branded presentations, process diagrams, html2pptx conversions, or applying Ichita visual identity to slides. For general PPTX editing, reading, or creating non-branded presentations, use the base pptx skill instead."
---

# Ichita PPTX — Branded Presentation Creation

> This skill extends the base `pptx` skill with Ichita brand identity.
> For general PPTX editing, reading, template workflows, and PptxGenJS reference, use the base `document-skills:pptx` skill.

## Quick Start

```javascript
const { createPresentation, slides, blocks, COLORS } = require("./scripts/ichita-slide-lib.cjs");

const pres = createPresentation({ title: "My Presentation" });

slides.cover(pres, { title: "Project Proposal", subtitle: "Liquid Sugar Plant", date: "April 2026" });
slides.sectionDivider(pres, { number: "01", title: "Overview" });

const s = slides.content(pres, { title: "Key Metrics" });
blocks.statCard(s, { value: "99.5%", label: "Purity", x: 0.5, y: 1.3, w: 4, h: 2 });
blocks.insightBar(s, { text: "Exceeds industry standard of 99.0%" });

slides.closing(pres, { title: "Thank You", subtitle: "Innovative · Reliable · Partnership" });

pres.writeFile({ fileName: "output.pptx" });
```

---

## Quick Reference

| Task | Action |
|------|--------|
| **Create branded PPTX** | Use `ichita-slide-lib.cjs` (see API below) |
| Process flow diagrams | Read [process-diagrams.md](process-diagrams.md) + use `process-diagram-lib.cjs` |
| HTML to PPTX | Read [html2pptx.md](html2pptx.md) + use `html2pptx.js` |
| Edit existing PPTX | Use `replace.py` / `rearrange.py` / `inventory.py` |
| Brand reference | Read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) |
| Layout patterns | See [layout-patterns.json](layout-patterns.json) |
| Test all layouts | Run `node examples/test-all-layouts.cjs output.pptx` |

---

## Slide Builder Library API

### `createPresentation(opts?)`

Creates a PptxGenJS instance pre-configured for Ichita (16:9, 10"x5.625").

```javascript
const pres = createPresentation({ title: "...", subject: "...", author: "..." });
```

### Slide Layouts (`slides.*`)

All return the PptxGenJS slide object. Content slides use the Ichita content frame background.

#### `slides.cover(pres, { title, subtitle?, date? })`

Dark background with blue accent bars (top + left). ICHITA brand mark from bg image.

#### `slides.sectionDivider(pres, { number, title, subtitle? })`

Blue Grey 01 background. Large Betatron number (72pt, Blue) right-aligned. Title left.

#### `slides.content(pres, { title })`

White content frame background. Title centered in header area. Returns slide for custom content — add elements starting at **y: 1.2** minimum.

```javascript
const s = slides.content(pres, { title: "Analysis Results" });
s.addText("Body text here", { x: 0.5, y: 1.3, w: 9, h: 1, fontSize: 12, fontFace: "Aeonik", color: "263338" });
```

#### `slides.twoColumn(pres, { title, leftContent, rightContent })`

Two equal zones. Callbacks receive `(slide, { x, y, w, h })`.

```javascript
slides.twoColumn(pres, {
  title: "Comparison",
  leftContent: (s, z) => blocks.featureList(s, { items: [...], ...z }),
  rightContent: (s, z) => blocks.statCard(s, { value: "99%", label: "Purity", ...z }),
});
```

#### `slides.grid(pres, { title, cols?, cards })`

N-column grid (default 3). Multi-row if cards > cols. Cards are callbacks.

```javascript
slides.grid(pres, {
  title: "Our Solutions",
  cols: 3,
  cards: [
    (s, z) => blocks.statCard(s, { value: "500+", label: "Projects", ...z }),
    (s, z) => blocks.statCard(s, { value: "23yr", label: "Experience", ...z }),
    (s, z) => blocks.statCard(s, { value: "99%", label: "Uptime", ...z }),
  ],
});
```

#### `slides.grid2x2(pres, { title, cards })`

4 cards in 2x2 arrangement. Same callback pattern.

#### `slides.kpi(pres, { value, label, context? })`

Blue Grey 01 background. Large Betatron number centered. Label + optional context below.

#### `slides.comparison(pres, { title, leftLabel, rightLabel, leftColor?, rightColor?, leftContent, rightContent })`

Two labeled columns with vertical divider. Default colors: red (left/before), green (right/after).

```javascript
slides.comparison(pres, {
  title: "Before vs After",
  leftLabel: "Current", rightLabel: "Proposed",
  leftContent: (s, z) => blocks.featureList(s, { items: [...], ...z, dotColor: COLORS.red }),
  rightContent: (s, z) => blocks.featureList(s, { items: [...], ...z, dotColor: COLORS.green }),
});
```

#### `slides.timeline(pres, { title, steps })`

Horizontal timeline with numbered circles and connecting line.

```javascript
slides.timeline(pres, {
  title: "Project Phases",
  steps: [
    { number: "1", title: "Assessment", description: "Site survey" },
    { number: "2", title: "Design", description: "P&ID + sizing" },
    { number: "3", title: "Build", description: "Fabrication" },
  ],
});
```

#### `slides.closing(pres, { title, subtitle?, contact? })`

Dark background with centered title. Same bg image as cover.

---

### Block Components (`blocks.*`)

Reusable elements for custom slides. All take `(slide, opts)`.

#### `blocks.statCard(slide, { value, label, x, y, w, h, valueColor? })`

Rounded card with big Betatron number + Aeonik label. Off-white background.

#### `blocks.featureList(slide, { items, x, y, w, h, dotColor? })`

Vertical list of items with colored dot + bold title + description.

```javascript
blocks.featureList(s, {
  items: [
    { title: "Membrane Filtration", description: "UF/NF/RO systems" },
    { title: "Ion Exchange", description: "DuPont Amberlite resin" },
  ],
  x: 0.5, y: 1.3, w: 4, h: 3,
});
```

#### `blocks.insightBar(slide, { text, y? })`

Bottom callout strip with blue accent line. Italic text. Default y near bottom.

#### `blocks.table(slide, { headers, rows, x, y, w, colWidths? })`

Branded table with dark header row, alternating light rows. `colWidths` are fractional (sum to 1.0).

```javascript
blocks.table(s, {
  headers: ["Parameter", "Spec", "Guaranteed"],
  rows: [
    ["Purity", "> 99.5%", "99.5%"],
    ["Recovery", "> 95%", "94%"],
  ],
  x: 0.5, y: 1.3, w: 9,
  colWidths: [0.4, 0.3, 0.3],
});
```

#### `blocks.processFlow(slide, { steps, x, y, w, h?, color? })`

Horizontal boxes connected by arrows.

```javascript
blocks.processFlow(s, {
  steps: ["Raw Water", "UF", "NF", "RO", "EDI", "UPW"],
  x: 0.5, y: 2.0, w: 9, h: 0.7,
});
```

---

### Brand Constants

Available as named exports: `COLORS`, `CHART_COLORS`, `FONTS`, `SIZES`, `SLIDE`, `MARGIN`, `CONTENT_AREA`, `TITLE_POS`, `ASSETS`.

```javascript
const { COLORS, FONTS, SIZES } = require("./scripts/ichita-slide-lib.cjs");

// COLORS.blue = "2978FF", COLORS.blueGrey03 = "263338", etc.
// FONTS.heading = "Aeonik", FONTS.display = "Betatron"
// SIZES.slideTitle = 24, SIZES.body = 12, SIZES.statValue = 32
// CONTENT_AREA = { x: 0.5, y: 1.2, w: 9, h: 3.575 }
```

---

## Workflow

### Standard Presentation

1. **Outline** — Define story arc: PURPOSE → AUDIENCE → MESSAGE → SLIDES
2. **Build** — Use `ichita-slide-lib.cjs` layout functions
3. **QA** — Convert to images, visually inspect (see QA section)
4. **Fix** — Adjust positioning, re-render, verify

### Process Diagrams

1. **MANDATORY**: Read [process-diagrams.md](process-diagrams.md) for unit operations & routing
2. Use `process-diagram-lib.cjs` with brand colors from `ichita-slide-lib.cjs`
3. Pre-flight math: `X0 + N*(BW+GAP) + BW + labelW <= 10"`

### HTML to PPTX

1. **MANDATORY**: Read [html2pptx.md](html2pptx.md) for rules & API
2. All text in `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` — NOT bare `<div>`
3. Dimensions: 720pt x 405pt for 16:9
4. No CSS gradients — pre-render as PNG

### Template Editing

```bash
python scripts/thumbnail.py template.pptx            # Visual overview
python scripts/inventory.py template.pptx inv.json     # Text inventory
python scripts/rearrange.py template.pptx out.pptx 0,3,5   # Reorder slides
python scripts/replace.py out.pptx replacements.json final.pptx  # Replace text
```

### Visual Tuning

When layout is "almost right" — **STOP guessing coordinates:**

1. Generate → user adjusts in PowerPoint → user saves
2. `python scripts/extract_positions.py <unpacked_dir>` (EMU / 914400 = inches)
3. Update code with extracted values

---

## QA (Required)

```bash
# Convert to images
soffice --headless --convert-to pdf --outdir . output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# Then visually inspect each slide-*.jpg
```

Check for:
- Overlapping elements, text overflow, cut-off content
- Logo visibility and correct variant (white on dark, dark on light)
- Font rendering (Aeonik, Betatron — not system fallbacks)
- Color accuracy (Blue #2978FF, not washed out)
- Title alignment on content slides
- Margins (>= 0.5" from edges)
- No text below 9pt

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| **`ichita-slide-lib.cjs`** | **Slide builder library — layouts, blocks, brand constants** |
| `process-diagram-lib.cjs` | Process flow diagram library (unit operations, streams) |
| `html2pptx.js` | HTML to PPTX via Playwright |
| `extract_positions.py` | Extract element positions from unpacked PPTX (EMU) |
| `inventory.py` | Create text inventory JSON from PPTX |
| `replace.py` | Replace text in PPTX from JSON |
| `rearrange.py` | Rearrange/duplicate slides |
| `thumbnail.py` | Generate slide thumbnail grids |

---

## Dependencies

- **pptxgenjs**: `npm install -g pptxgenjs` (creating presentations)
- **playwright**: `npm install -g playwright` (HTML rendering — html2pptx only)
- **sharp**: `npm install -g sharp` (SVG rasterization)
- **Pillow**: `pip install Pillow` (thumbnail grids)
- **LibreOffice**: `soffice` for PDF conversion
- **Poppler**: `pdftoppm` for PDF to images
