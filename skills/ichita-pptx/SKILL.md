---
name: ichita-pptx
description: "Use when creating Ichita-branded presentations, process diagrams, html2pptx conversions, or applying Ichita visual identity to slides — in JavaScript (PptxGenJS) or Python (python-pptx). For general PPTX editing, reading, or creating non-branded presentations, use the base pptx skill instead."
---

# Ichita PPTX — Branded Presentation Creation

> This skill extends the base `pptx` skill with Ichita brand identity.
> For general PPTX editing, reading, template workflows, and PptxGenJS reference, use the base `document-skills:pptx` skill.

## Language Choice

| Language | Library | When to use |
|----------|---------|-------------|
| **JavaScript** | `ichita-slide-lib.cjs` (PptxGenJS) | Default. Full slide catalog (cover, section, content, kpi, grid, comparison, timeline, closing). |
| **Python** | `ichita_slide_lib.py` (python-pptx) | When integrating with existing Python tooling (proposal generators, QA pipelines, batch processors). Master-level backgrounds, OhYeaH title style, numbered cards, scope tables, process flows. |
| **HTML→PNG** | `assets/html-template/` chrome image | When each slide is a full-bleed custom composition (diagram-heavy decks): slides authored as HTML, rendered to PNG, assembled to PPTX. |

**Iron rule (all three paths):** The Ichita slide chrome — dark navy `#263338` field, white floating content card, top-left ICHITA logo notch, bottom-left chamfer — is a **fixed asset, never hand-drawn.** PptxGenJS/python-pptx: set it at the MASTER/LAYOUT level, never as per-slide pictures. HTML→PNG: use `assets/html-template/ichita-content-bg.png` as the slide background — see [`assets/html-template/README.md`](assets/html-template/README.md). Do not reconstruct the chrome in CSS from a screenshot; that inverts to a white-background slide and deletes the Ichita identity (TNCC sweetener incident, 2026-05-22).

## Setup

Before generating PPTX:

1. **Install PptxGenJS** (in caller's project): `npm install pptxgenjs` — or globally: `npm install -g pptxgenjs`
2. **Install Ichita brand fonts** (one-time, system-wide):
   - Run `bash assets/fonts/install-fonts.sh` from this repo's root, OR
   - Manually copy `assets/fonts/th-aeonik/*.otf` and `assets/fonts/aeonik/*.otf` to `~/.local/share/fonts/` (Linux), `~/Library/Fonts/` (macOS), or `%LOCALAPPDATA%\Microsoft\Windows\Fonts\` (Windows), then run `fc-cache -fv` (Linux/macOS).
   - Verify with: `fc-list | grep -i "TH Aeonik"` — must list TH-Aeonik-Regular/Bold OTFs.

Without fonts installed, PowerPoint/LibreOffice will fall back to system defaults and the deck will not be brand-compliant.

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
| Full-bleed html→png slides | Use [`assets/html-template/`](assets/html-template/) — real chrome as background image, never redrawn |
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

Two labeled columns with vertical divider. Default colors: blueGrey02 (left/before — muted), blue (right/after — brand).

```javascript
slides.comparison(pres, {
  title: "Before vs After",
  leftLabel: "Current", rightLabel: "Proposed",
  leftContent: (s, z) => blocks.featureList(s, { items: [...], ...z, dotColor: COLORS.blueGrey02 }),
  rightContent: (s, z) => blocks.featureList(s, { items: [...], ...z, dotColor: COLORS.blue }),
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
| **`ichita-slide-lib.cjs`** | **JS slide builder library — layouts, blocks, brand constants (PptxGenJS)** |
| **`ichita_slide_lib.py`** | **Python slide builder — master/layout BG, title, cards, scope tables, process flows (python-pptx)** |
| `process-diagram-lib.cjs` | Process flow diagram library (unit operations, streams) |
| `html2pptx.js` | HTML to PPTX via Playwright |
| `extract_positions.py` | Extract element positions from unpacked PPTX (EMU) |
| `inventory.py` | Create text inventory JSON from PPTX |
| `replace.py` | Replace text in PPTX from JSON |
| `rearrange.py` | Rearrange/duplicate slides |
| `thumbnail.py` | Generate slide thumbnail grids |

---

## Python (`ichita_slide_lib.py`) — Quick Start

```python
import sys, os
sys.path.insert(0, "/path/to/ichita-skills/skills/ichita-pptx/scripts")
from ichita_slide_lib import (
    create_ichita_presentation, add_content_slide, add_dark_slide,
    add_slide_title, numbered_card, scope_table, process_flow_arrows,
    COLORS, FONTS, SIZES, CONTENT_LAYOUT, DARK_LAYOUT,
)

# BG applied to layouts — every slide inherits, no per-slide picture management
prs = create_ichita_presentation()

# Dark cover (cover/closing use DARK_LAYOUT)
cover = add_dark_slide(prs)
# ... position title text on cover ...

# Content slide — frame BG inherited from CONTENT_LAYOUT
s = add_content_slide(prs, "Project Background & Requirements")
# add cards / tables / etc. — body content starts at y=1.35

# Numbered card with rich text body
numbered_card(s, x=Inches(0.6), y=Inches(1.35),
              w=Inches(6.05), h=Inches(1.83),
              num="1", title="The Guarantee",
              body_runs=[
                  {"text": "ICHITA warrants the supplied system shall meet "},
                  {"text": "production capacity and quality", "bold": True},
                  {"text": " during the Acceptance Test."},
              ])

# Scope table — left column auto-bold, ICHITA Supplies column auto-tinted
scope_table(s, x=Inches(0.6), y=Inches(3.2),
            w=Inches(12.13), h=Inches(3.55),
            headers=["Category", "ICHITA Supplies", "SMS Supplies"],
            rows=[
                ["Equipment Supply", "Complete set", "Spray Dryer"],
                # ...
            ])

prs.save("deck.pptx")
```

### Python API at a glance

| Function | Purpose |
|----------|---------|
| `create_ichita_presentation(frame_bg=None, dark_bg=None)` | Build a Presentation with master-level BGs |
| `add_content_slide(prs, title, section_num=None)` | Frame BG slide + OhYeaH title style |
| `add_dark_slide(prs)` | Dark BG slide (cover/closing) |
| `add_slide_title(slide, text, section_num=None, size=None)` | Title only (if you build the slide manually) |
| `numbered_card(slide, x, y, w, h, num, title, body_runs, accent=None, highlight=False)` | Card with number tag |
| `scope_table(slide, x, y, w, h, headers, rows, ichita_col=1)` | Two/three-column scope table with proven emphasis |
| `process_flow_arrows(slide, steps, ...)` | Numbered boxes + chunky gray arrows |
| `set_layout_bg_picture(layout, image_path)` | Low-level: set a layout's BG (use sparingly) |

**`section_num` rule:** Drop it when the meeting may skip slides — visible "01 → 03" numbers expose the gap. Keep numbers for structured walkthroughs.

**Title style** (proven on SMS R2 deck, confirmed by OhYeaH!):
- 32pt Aeonik Bold #263338 (auto-drops to 24pt for titles > ~45 chars)
- Positioned at x=4.14" y=0.30 (clears the frame's top-left ICHITA notch)
- Blue accent line UNDER the title (x=3.80, y=1.05, 8.47" wide, 0.05" tall)

---

## Dependencies

- **pptxgenjs**: `npm install -g pptxgenjs` (creating presentations)
- **playwright**: `npm install -g playwright` (HTML rendering — html2pptx only)
- **sharp**: `npm install -g sharp` (SVG rasterization)
- **Pillow**: `pip install Pillow` (thumbnail grids)
- **LibreOffice**: `soffice` for PDF conversion
- **Poppler**: `pdftoppm` for PDF to images
