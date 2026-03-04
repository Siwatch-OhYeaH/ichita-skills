# ICHITA Brand Defaults

> Source of truth: `Ichita_Brand_Guidelines_V1.0.pdf` (©2022 ICHITA). All hex codes are PptxGenJS format (**NO `#` prefix**).

---

## 1. Logo System

### Two forms — Wordmark + Symbol

| Form | Description | When to use |
|------|-------------|-------------|
| **Wordmark** | `ICHITA™` custom lettering | Primary identifier — all communications, sign-off, endorsement |
| **Symbol** | X-mark (two arrow devices from the 'A' angle) | Endorsing mark, sign-off, favicon — ONLY when ICHITA context is already evident |

### Logo Rules
- **NEVER** alter, redraw, or modify the logo in any way
- Use the provided logo files, never recreate from text
- **Clearspace**: 50% of the wordmark height (or 50% of one arrow device for Symbol) — nothing inside this zone

### Logo Colourways

| Background | Logo Color | Hex |
|------------|-----------|-----|
| White / light | Blue Grey 03 | `263338` |
| Blue Grey 01 (light grey) | Blue Grey 03 | `263338` |
| Blue (`2978FF`) | Blue Grey 03 | `263338` |
| Blue Grey 03 (dark) | White | `FFFFFF` |
| Blue Grey 02 (medium grey) | Blue Grey 03 | `263338` |

> **Rule**: Logo uses Blue Grey 03 on most backgrounds. Switch to White ONLY on dark backgrounds (Blue Grey 03, Blue Black).

### Logo Assets

| Variant | File | Dimensions |
|---------|------|-----------|
| Wordmark (black on transparent) | `assets/ichita/logos/ichita-logo-black.png` | 1705x260 |
| Wordmark (gray/light) | `assets/ichita/logos/ichita-logo-white.png` | 1705x260 |
| X-mark (white on dark blue, square) | `assets/ichita/logos/ichita-xmark-white-on-blue.png` | 2251x2251 |
| X-mark (dark on transparent, square) | `assets/ichita/logos/ichita-xmark-dark.png` | 2251x2251 |
| Wordmark on dark bg (JPEG) | `assets/ichita/logos/ichita-logo-white-on-dark.jpeg` | template bg |

---

## 2. Color Palette

### Primary Colors (from Brand Guidelines p.13)

| Name | Hex | RGB | CMYK | PMS | Usage |
|------|-----|-----|------|-----|-------|
| **White** | `FFFFFF` | — | — | — | Light backgrounds, text on dark |
| **Blue** | `2978FF` | R40 G119 B255 | C80 M56 Y0 K0 | 2132 | **Primary accent** — vibrant, recognizable. Buttons, highlights, links, pattern fills |
| **Blue Light** | `82B0FF` | R130 G176 B255 | C51 M26 Y0 K0 | 2381 | Secondary accent — subtitles, hover states, lighter pattern |
| **Blue Grey 01** | `CFD9DB` | R207 G217 B219 | C18 M9 Y10 K0 | 427 C | Main backdrop — light content backgrounds, the brand's "canvas" |
| **Blue Grey 02** | `788F9C` | R120 G143 B156 | C57 M36 Y31 K0 | 2544 C | Muted text, captions, borders |
| **Blue Grey 03** | `263338` | R38 G51 B56 | C80 M64 Y58 K56 | 432 C | **Primary text**, dark backgrounds, logo default color |
| **Blue Black** | `171C21` | R23 G28 B33 | C78 M69 Y61 K75 | Black 6 C | Darkest background, deepest anchor |

> **Palette philosophy**: "A strong blue supported by a series of neutral colours." The vibrant Blue is the **accent** — Blue Grey 01 + White form the backdrop. Darker colours (Grey 03, Blue Black) used sparingly for impact.

### Functional Colors (ICHITA-extended)

| Name | Hex | Usage |
|------|-----|-------|
| **Success Green** | `34A853` | Positive indicators, growth |
| **Warning Red** | `E83E3E` | Negative indicators, alerts |
| **Emphasis Orange** | `FFA000` | Sparingly for emphasis |
| **Off White** | `F8FAFB` | Card backgrounds, subtle contrast |
| **Alt Row** | `F0F4F5` | Table alternating row background |

### Chart Color Sequence

```javascript
const ICHITA_CHART_COLORS = ["2978FF", "263338", "82B0FF", "788F9C", "34A853", "E83E3E"];
```

---

## 3. Typography

### Font Family: Aeonik

| Weight | Role | Usage |
|--------|------|-------|
| **Aeonik Regular** | Body | Body copy, bullets, labels, table cells |
| **Aeonik Medium** | Emphasis | Subheadings, card headers, medium-weight labels |
| **Aeonik Bold** | Heading | Titles, section headers, strong emphasis |

> Aeonik: "timeless and modern aesthetic... a structural workhorse that was meticulously engineered." Features: ligatures, fractions, case-sensitive punctuation, symbols, forms, arrows.

### Display Numerals: Betatron

| Font | Role | Character |
|------|------|-----------|
| **Betatron** | Display numbers ONLY | "Futuristic ideology... distinctly mechanical and industrial aesthetic" |

> Use Betatron for: KPI stats, large numbers, year displays, capacity figures. NEVER for body text or labels.

### Font Assignment

| Role | Font | Fallback | Notes |
|------|------|----------|-------|
| **Heading** | Aeonik Bold | Trebuchet MS | Titles, section headers |
| **Body** | Aeonik Regular | Calibri | Body copy, bullets, labels |
| **Subhead** | Aeonik Medium | Trebuchet MS | Card headers, emphasis |
| **Display/KPI** | Betatron | Georgia | Large numbers only |
| **Thai** | TH Sarabun New | Tahoma | Thai language text |

> Aeonik fonts are installed at `D:/Doccument/New Identity/Aeonik-font-download/` on OhYeaH!'s machine. Fallbacks are for RENDERING only — never set as primary in code.

---

## 4. Pattern System

ICHITA has 4 brand patterns based on the concept of "process" — conveying movement, depth, and dynamism.

### Pattern Types

| # | Name | Description | Visual |
|---|------|-------------|--------|
| 1 | **Horizontal Bars** | Thick bars at top, diminishing width toward bottom | ████████ → ═══ → ─── |
| 2 | **Vertical Bars** | Grid of vertical stripes, varying widths + gaps | ▌▌▌▌ ▌▌▌▌ (membrane-like) |
| 3 | **Wide Blocks** | Wide horizontal blocks, diminishing to thin lines | █████ → ███ → ── |
| 4 | **Dots** | Circles diminishing in size from top to bottom | ●●● → ●●● → ··· |

### Pattern Usage Rules
- **Color**: Blue Grey 03 (`263338`) shapes on Blue Grey 01 (`CFD9DB`) background — OR — Blue Grey 03 shapes on Blue (`2978FF`) background
- **Scale**: Patterns work at any scale — full slide background, card accent, strip decoration
- **Placement**: Top portion of slide/page — pattern fills 40-60% of area, logo/text anchored at bottom
- **Cover slides**: Pattern at top → wordmark at bottom-left (see Identity Applied examples p.32-34)
- **DO NOT**: Mix pattern types on one slide, use off-brand colors, rotate patterns

### Pattern in PptxGenJS (Horizontal Bars Example)

```javascript
// Horizontal bar pattern — thick bars diminishing
// Use as decorative element, not full coverage
function addHorizontalBarPattern(slide, x, y, w, barColor = "263338") {
  const bars = [
    { h: 0.50, gap: 0.06 },  // thick
    { h: 0.45, gap: 0.06 },
    { h: 0.35, gap: 0.08 },
    { h: 0.20, gap: 0.10 },
    { h: 0.10, gap: 0.12 },
    { h: 0.04, gap: 0.14 },  // thin
  ];
  let cy = y;
  for (const bar of bars) {
    slide.addShape("rect", { x, y: cy, w, h: bar.h, fill: { color: barColor } });
    cy += bar.h + bar.gap;
  }
}
```

---

## 5. Illustration Style

> Section marked "TBC" in brand guidelines — style direction established but details pending.

### Direction
- **Technical line drawings** of equipment (vessels, tanks, pumps, piping)
- Clean outline style, thin consistent stroke weight
- On Blue Grey 01 (`CFD9DB`) background
- No fills — just outlines (stroke in Blue Grey 03 `263338`)
- Purpose: represent and explain ICHITA products, processes, and services

### When to Use
- Process flow diagrams (simplified, not P&ID-level detail)
- Equipment overview slides (schematic, not photo)
- Decorative technical elements (background watermarks)

---

## 6. Photography Direction

Two defined image types, each reflecting different aspects of ICHITA.

### People Photography
- **Purpose**: Position ICHITA as personal, relatable, reliable, assertive, and confident
- **Subjects**: Engineers in blue cleanroom suits, operators at control panels, professionals in meeting settings, technicians with face shields
- **Tone**: Natural light, professional settings, candid work moments (not staged poses)
- **Color treatment**: Cool/neutral — blues from uniforms + stainless steel environments naturally align with brand palette

### Operational Photography
- **Purpose**: Communicate scale of process + attention to detail + expertise
- **Subjects**:
  - **Wide shots**: Factory interiors, stainless steel piping, full system installations
  - **Close-ups**: Beakers of clear water, membrane samples, microscope work, instrument readings
- **Tone**: Clean, precise, technical — emphasize the quality of work
- **Color treatment**: Cool metallics, blue accents from equipment, clear water imagery

### Photography Rules
- **DO**: Show real equipment, real people, real facilities
- **DO NOT**: Use generic stock photos, oversaturated colors, or cluttered compositions
- Prefer images that naturally contain ICHITA's blue + grey palette

---

## 7. Identity Applied (Examples from Brand Guidelines)

These examples from the brand guidelines (p.26-35) show how visual assets combine:

### Hard Hat (p.28)
- Light grey helmet, Blue Grey 03 wordmark on side, X-mark symbol on front
- Blue accent on helmet brim — subtle brand touch on safety equipment

### Building Signage (p.29-30)
- Dark facade → White illuminated wordmark (right-justified, lower third)
- Building corner → White 3D X-mark symbol, Blue Grey 03 facade

### Equipment Branding (p.31)
- White tank/vessel → Blue Grey 03 X-mark symbol above, wordmark below
- Clean, minimal — no extra graphics, just logo on white

### Printed Materials (p.32-34)
- **Layout formula**: Pattern fills top 50-60% → white space below → wordmark bottom-left
- Three colorways:
  - Blue bg + horizontal bars (Blue Grey 03 bars on Blue) + Blue Grey 03 wordmark
  - White bg + vertical bars (Blue Grey 03) + Blue Grey 03 wordmark
  - Blue Grey 01 bg + horizontal bars (Blue Grey 03) + text "Separation Technologies" + X-mark symbol bottom-right
- **Key pattern**: Logo is ALWAYS at bottom, pattern is ALWAYS at top

### Packaging (p.35)
- Acrylic box with diagonal brand pattern visible through clear material
- Blue spine with oversized wordmark rotated vertically

---

## Slide Structure

### Dark/Light Pattern

- **Dark slides** (Blue Grey 03 `263338` or Blue Black `171C21`): title, section dividers, closing
- **Light slides** (White `FFFFFF` or Blue Grey 01 `CFD9DB`): content, data, tables

### Content Area Constants

```javascript
const ICHITA = {
  // Colors (NO # prefix)
  colors: {
    white: "FFFFFF",
    blue: "2978FF",
    blueLight: "82B0FF",
    grey1: "CFD9DB",
    grey2: "788F9C",
    grey3: "263338",
    blueBlack: "171C21",
    green: "34A853",
    red: "E83E3E",
  },
  // Fonts (with fallbacks)
  fonts: {
    heading: "Aeonik",       // fallback: "Trebuchet MS"
    body: "Aeonik",          // fallback: "Calibri"
    display: "Betatron",     // fallback: "Georgia"
    thai: "TH Sarabun New",  // fallback: "Tahoma"
  },
  // Standard slide margins (10" x 5.625" at LAYOUT_16x9)
  margin: { left: 0.5, top: 0.5, right: 0.5, bottom: 0.5 },
};
```

### Logo & Footer Placement

- **Logo**: bottom-right corner on light slides, centered bottom on dark slides
- **Footer text**: `www.ichita.co.th` — right-aligned, 9pt, White on dark / Blue Grey 02 on light
- **Logo clear zone**: 50% of logo height — no content inside this area

---

## ICHITA Title Slide Example

```javascript
let s = pres.addSlide();
s.background = { color: "263338" };

// Top accent line
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "2978FF" } });

// Left accent bar
s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 0.08, h: 2.2, fill: { color: "2978FF" } });

// Title — white on dark
s.addText("Presentation Title", {
  x: 1.0, y: 1.3, w: 8, h: 1.8,
  fontSize: 40, fontFace: "Aeonik", color: "FFFFFF", bold: true, margin: 0,
});

// Subtitle — Ichita Blue
s.addText("Subtitle or tagline here", {
  x: 1.0, y: 3.3, w: 8, h: 0.4,
  fontSize: 14, fontFace: "Aeonik", color: "2978FF", margin: 0,
});

// Footer
s.addText("www.ichita.co.th", {
  x: 0.5, y: 5.1, w: 9, h: 0.3,
  fontSize: 9, fontFace: "Aeonik", color: "788F9C", align: "right", margin: 0,
});
```

## ICHITA Content Slide Example (with bg-content.png frame)

```javascript
// Reusable content slide — title in header, right of ICHITA logo
function contentSlide(pres, title) {
  const s = pres.addSlide();
  s.background = { path: "bg-content.png" }; // Frame BG with logo in top-left
  if (title) s.addText(title, {
    x: 2.7, y: 0.1, w: 6.95, h: 0.45,
    fontSize: 22, fontFace: "Aeonik", color: "263338", bold: true, align: "center", margin: 0,
  });
  // NO topic label, NO footer — template BG already has ICHITA branding
  return s;
}

// Content starts at y: 1.2 minimum
// Use insightBar at y: 4.15 for bottom callouts
```

---

## Presentation Rules (MUST FOLLOW)

Every time you create or edit a presentation, follow these rules:

### 1. Font Rules — ALWAYS use brand fonts, NEVER fallbacks
| Role | Use This | NEVER This |
|------|----------|------------|
| Heading | `Aeonik` | Trebuchet MS, Arial, Calibri |
| Body | `Aeonik` | Calibri, Arial |
| Display/KPI | `Betatron` | Georgia, Times |
| Thai text | `TH Sarabun New` | Tahoma, Angsana |

> Fallback fonts are for RENDERING on machines without Aeonik — never set them as the primary font in code.

### 2. Font Size Minimums
| Element | Minimum | Recommended |
|---------|---------|-------------|
| Slide title | 22pt | 24pt |
| Section/card header | 12pt | 14pt |
| Body text / bullets | 11pt | 12pt |
| Table cells | 10pt | 11pt |
| Stat card values | 28pt | 32pt |
| Labels / captions | 10pt | 10-11pt |
| Footnotes (only) | 9pt | 9pt |

> **Rule: NO text below 9pt.** If it doesn't fit, redesign the layout — don't shrink the font.

### 3. Title Position (Content Slides with Frame BG)
- Title sits in header area, RIGHT of ICHITA logo: `x: 2.7`, `y: 0.1`, `w: 6.95`, `h: 0.45`
- Right edge anchored at 9.65" (x + w = 9.65)
- `align: "center"`, `fontSize: 22`, `color: grey3`, `bold: true`
- NO topic label, NO footer on content slides (template BG already has logo)
- Content starts at `y: 1.2` minimum

### 4. Layout Principles
- Use ICHITA color palette — no arbitrary colors
- Dark slides for: cover, section dividers, closing
- Light slides (content frame) for: data, tables, content
- Content must stay within safe zones (inside the white frame)
- Accent bar under title: `2978FF`, 0.04" height
- Every content slide should have an insight box at bottom if space allows

### 5. Pre-Build Checklist
Before generating any PPTX:
- [ ] Fonts set to `Aeonik` / `Betatron` (NOT fallbacks)
- [ ] All text >= 9pt minimum
- [ ] Title at correct y-position
- [ ] Colors from ICHITA palette only
- [ ] Content within safe zones
- [ ] Logo/footer not overlapped

---

## Related Assets

| Asset | Path |
|-------|------|
| **Brand Guidelines PDF** | `assets/ichita/brand/Ichita_Brand_Guidelines_V1.0.pdf` |
| **Aeonik Font Files** | `D:/Doccument/New Identity/Aeonik-font-download/` |
| ICHITA Dark BG | `assets/ichita/brand/ichita-dark-bg.jpg` |
| ICHITA Content Frame | `assets/ichita/brand/ichita-content-frame.png` |
| ICHITA Logos | `assets/ichita/logos/` (5 variants) |
| ICHITA Icons | `assets/ichita/icons/` (water-drop, gear, engineer, thai-flag) |
| Partner Logos | `assets/ichita/partner-logos/` (DuPont, Toray, CSM, etc.) |
| Equipment Photos | `assets/ichita/equipment-photos/` (8 photos) |
| PowerPoint Template | `assets/ichita/templates/powerpoint-template.pptx` |
| Word Template | `assets/ichita/templates/word-template.docx` |
| Safety Proposal Template | `assets/ichita/templates/safety-proposal.docx` |
