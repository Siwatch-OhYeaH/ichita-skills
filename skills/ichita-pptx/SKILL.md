---
name: ichita-pptx
description: "Use when creating Ichita-branded presentations, process diagrams, html2pptx conversions, or applying Ichita visual identity to slides. For general PPTX editing, reading, or creating non-branded presentations, use the base pptx skill instead."
---

# Ichita PPTX — Branded Presentation Creation

> This skill extends the base `pptx` skill with Ichita brand identity.
> For general PPTX editing, reading, template workflows, and PptxGenJS reference, use the base `document-skills:pptx` skill.

## Quick Reference

| Task | Action |
|------|--------|
| Create Ichita-branded PPTX | Read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) + base `pptx` skill |
| Process flow diagrams | Read [process-diagrams.md](process-diagrams.md) |
| HTML to PPTX conversion | Read [html2pptx.md](html2pptx.md) |
| Edit existing template | Use `replace.py` / `rearrange.py` / `inventory.py` |
| Extract element positions | `python scripts/extract_positions.py <unpacked_dir> [slide_range]` |
| Layout pattern reference | See [layout-patterns.json](layout-patterns.json) |
| General PPTX reading/editing | Use base `document-skills:pptx` skill |

> **Script paths** are relative to this skill directory (`skills/ichita-pptx/`). Run from there, or prefix with the full path from the plugin root.

---

## Brand Mode: ICHITA

When creating presentations for ICHITA, switch from generic palettes to brand-specific defaults:

1. **Read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md)** for the complete brand guide
2. Override all generic color palettes, typography, and slide structure with ICHITA brand rules
3. Brand colors, fonts, and patterns take priority over the base skill's Design Ideas section
4. Process diagrams use ICHITA-specific equipment colors and styling

ICHITA mode is activated when:
- The user mentions ICHITA, Ichita, or related brand names
- The presentation is for Ichita Co., Ltd. or its customers
- Brand templates are referenced

### ICHITA Constants (from ichita-defaults.md)

```javascript
const ICHITA = {
  colors: {
    white: "FFFFFF", blue: "2978FF", blueLight: "82B0FF",
    grey1: "CFD9DB", grey2: "788F9C", grey3: "263338",
    blueBlack: "171C21", green: "34A853", red: "E83E3E",
  },
  fonts: {
    heading: "Aeonik", body: "Aeonik",
    display: "Betatron", thai: "TH Sarabun New",
  },
  margin: { left: 0.5, top: 0.5, right: 0.5, bottom: 0.5 },
};
```

---

## Process Diagrams

For process flow diagrams, block diagrams, and simplified P&IDs:

1. **MANDATORY**: Read [`process-diagrams.md`](process-diagrams.md) for modes, unit operations, stream routing, and layout patterns
2. Use [`process-diagram-lib.cjs`](scripts/process-diagram-lib.cjs) with PptxGenJS
3. Apply ICHITA branding from `ichita-defaults.md`

### Pre-flight math
For linear flow diagrams, calculate: `X0 + N*(BW+GAP) + BW + labelW <= 10"`. Don't eyeball — compute.

---

## HTML to PPTX (html2pptx)

Convert HTML slides to PowerPoint via Playwright rendering. Best for layouts that benefit from CSS flexbox/grid.

1. **MANDATORY**: Read [`html2pptx.md`](html2pptx.md) completely
2. Create HTML slides with proper dimensions (720pt x 405pt for 16:9)
3. Use [`html2pptx.js`](scripts/html2pptx.js) to convert

**Critical rules:**
- All text in `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` — NOT bare text in `<div>`
- Rasterize gradients and icons as PNG via Sharp FIRST, then reference in HTML
- Bottom content padding >= 40pt

---

## Template Editing (Replace/Rearrange)

For creating presentations from existing Ichita templates:

1. Extract text + thumbnails:
   ```bash
   python scripts/thumbnail.py template.pptx
   ```
2. Create slide inventory:
   ```bash
   python scripts/inventory.py template.pptx text-inventory.json
   ```
3. Rearrange slides:
   ```bash
   python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52
   ```
4. Apply text replacements:
   ```bash
   python scripts/replace.py working.pptx replacement-text.json output.pptx
   ```

---

## Visual Tuning (Position Feedback)

**When the user says "almost" or "not quite" about layout — STOP guessing coordinates.**

1. **Generate** first draft from code
2. **User adjusts** in PowerPoint/LibreOffice
3. **User saves** the adjusted file
4. **Extract positions**:
   ```bash
   python scripts/extract_positions.py <unpacked_dir> [slide_range]
   ```
   EMU / 914400 = inches
5. **Update code** with extracted values
6. **Update brand defaults** if it's a reusable pattern

**Anti-patterns**: Iterating position values in code based on verbal feedback. Use extract_positions.py instead.

---

## Layout Patterns

See [`layout-patterns.json`](layout-patterns.json) for structured layout definitions with slot constraints.

Intent-to-layout mapping:
- Problem statement -> grid_2x2, comparison
- Solution/features -> hero_split, content_left, grid_3col, feature_list
- Data/stats -> data_highlight, grid_3col, grid_4col
- Timeline -> timeline
- Opening/closing -> hero_center, cta

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `process-diagram-lib.cjs` | PptxGenJS library for process flow diagrams |
| `html2pptx.js` | HTML to PPTX conversion via Playwright |
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
