---
name: pptx
description: "Presentation creation, editing, and analysis. When Claude needs to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks"
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

> **Note**: Script paths like `scripts/thumbnail.py` and `scripts/rearrange.py` are relative to the
> skill directory (`skills/pptx/`). Run from there, or prefix with the full path from the plugin root.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit from template | Read [editing.md](editing.md) (Anthropic workflow) or use Oracle [ooxml.md](ooxml.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |
| Create with ICHITA branding | Read [ichita-defaults.md](../../assets/brand/ichita-defaults.md) + [pptxgenjs.md](pptxgenjs.md) |
| Process diagrams | Read [process-diagrams.md](process-diagrams.md) |
| Advanced HTML workflow | Read [html2pptx.md](html2pptx.md) |
| Layout pattern reference | See [layout-patterns.json](layout-patterns.json) |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview (thumbnail grid)
python scripts/thumbnail.py presentation.pptx

# Raw XML access (for comments, speaker notes, animations, complex formatting)
python ooxml/scripts/unpack.py presentation.pptx unpacked/
```

### Key XML file structures
* `ppt/presentation.xml` - Main presentation metadata and slide references
* `ppt/slides/slide{N}.xml` - Individual slide contents
* `ppt/notesSlides/notesSlide{N}.xml` - Speaker notes
* `ppt/comments/modernComment_*.xml` - Comments
* `ppt/slideLayouts/` - Layout templates
* `ppt/slideMasters/` - Master slide templates
* `ppt/theme/` - Theme and styling information
* `ppt/media/` - Images and other media files

### Typography and color extraction from existing files
When given an example design to emulate:
1. Read theme file: `ppt/theme/theme1.xml` for colors (`<a:clrScheme>`) and fonts (`<a:fontScheme>`)
2. Sample slide content: Examine `ppt/slides/slide1.xml` for actual font usage
3. Search for patterns: Use grep to find color and font references across XML files

---

## Editing Workflow

Two editing approaches available:

### Approach A: Anthropic-style (editing.md)

Best for: template-based workflows with slide duplication and reordering.

1. Analyze template with `thumbnail.py` + `markitdown`
2. Unpack -> manipulate slides -> edit content -> clean -> pack

**Read [editing.md](editing.md) for full details.**

### Approach B: Oracle-style (ooxml.md + scripts)

Best for: precise XML editing with validation, text replacement workflows.

1. **MANDATORY**: Read [`ooxml.md`](ooxml.md) completely
2. Unpack: `python ooxml/scripts/unpack.py <file> <dir>`
3. Edit XML files
4. **CRITICAL**: Validate after each edit: `python ooxml/scripts/validate.py <dir> --original <file>`
5. Pack: `python ooxml/scripts/pack.py <dir> <file>`

### Template-Based Creation (Oracle extended workflow)

For creating presentations from existing templates with text replacement:

1. Extract text + thumbnails
2. Analyze template and save inventory
3. Create outline with template mapping
4. Rearrange slides: `python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52`
5. Extract text inventory: `python scripts/inventory.py working.pptx text-inventory.json`
6. Generate replacement JSON
7. Apply replacements: `python scripts/replace.py working.pptx replacement-text.json output.pptx`

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.** It contains design philosophy, color palettes, layout patterns with diagrams, full API reference, critical pitfalls, and working code examples.

### Workflow A: PptxGenJS Direct (RECOMMENDED)

1. **MANDATORY - READ ENTIRE FILE**: Read [`pptxgenjs.md`](pptxgenjs.md) completely. **NEVER set any range limits.**
2. Write a single `.js` file that generates the presentation
   - Apply design philosophy: bold palette, dark/light sandwich, visual motif
   - Vary layouts across slides
   - Every slide needs a visual element -- no text-only slides
3. **Visual validation**: Generate thumbnails and inspect for layout issues

> **When creating for ICHITA**: also read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) for brand colors, fonts, and patterns.

### Workflow A+: Process Diagrams

For process flow diagrams, block diagrams, and simplified P&IDs:

1. **MANDATORY**: Read [`process-diagrams.md`](process-diagrams.md) for modes, unit operations, stream routing, and layout patterns
2. Use [`process-diagram-lib.cjs`](scripts/process-diagram-lib.cjs) with PptxGenJS
3. Combine with [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) for ICHITA branding

### Workflow B: html2pptx (Advanced)

Convert HTML slides to PowerPoint via Playwright rendering. Use for layouts that benefit from CSS flexbox/grid.

1. **MANDATORY**: Read [`html2pptx.md`](html2pptx.md) completely
2. Create HTML slides with proper dimensions (720pt x 405pt for 16:9)
   - Use `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` for ALL text — text directly in `<div>` is silently ignored
   - Use `class="placeholder"` for chart/table areas
   - **CRITICAL**: Rasterize gradients and icons as PNG via Sharp FIRST, then reference in HTML
3. Use [`html2pptx.js`](scripts/html2pptx.js) to convert HTML to PowerPoint
4. **Visual validation**: Generate thumbnails and inspect

#### html2pptx Sizing Guidelines (16:9 = 720pt x 405pt)

| Element | Size | Notes |
|---------|------|-------|
| Main title | 32-36pt (up to 40pt for title slides) | Bold |
| Section header | 18-22pt | Bold |
| Body text | 14-16pt | Regular |
| Secondary text | 12-14pt | Regular |
| Captions/labels | 11-13pt | |
| Top content padding | 18-25pt below header | |
| Bottom content padding | 40pt minimum | Validation requires 0.5" = 36pt |
| Between sections | 12-18pt | |
| Line-height (headers) | 1.1-1.3 | |
| Line-height (body) | 1.2-1.35 | |
| Line-height (dense) | 1.1-1.25 | |

#### Common Fitting Patterns

**5-item list**: `padding: 12-16pt 40pt 40pt 40pt`, items `margin-bottom: 6-8pt`, headers 14-16pt, body 12-14pt

**4-column boxes**: `gap: 16-20pt`, box `padding: 13-15pt`, text 13-14pt

**Two-column comparison**: `padding: 20-25pt 40pt 40pt 40pt`, headers 18-20pt, list items 15-16pt

#### Overflow Handling Strategy

| Overflow | Action |
|----------|--------|
| **> 100pt** | Reduce content padding 5-10pt, item margins 3-5pt, font sizes 1-2pt |
| **50-100pt** | Reduce padding 3-5pt, margins 2-3pt, spacing 2pt |
| **20-50pt** | Fine-tune padding 2-3pt, margins 1-2pt |
| **< 20pt** | 1pt adjustments, reduce margin-bottom on last items |
| **< 5pt** | Reduce content padding first, then final element bottom margin |

#### html2pptx Checklist

- [ ] All text wrapped in `<p>`, `<h1>`-`<h6>`, `<ul>`, or `<ol>` (NOT bare text in `<div>`)
- [ ] Bottom content padding >= 40pt
- [ ] Font sizes follow sizing guidelines above
- [ ] Estimated total height ~350-365pt for content (leaving room for header)
- [ ] Emojis and numbers also wrapped in `<p>` tags

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it -- colored circles for icons, left accent bars, card-based layouts with colored headers, dark bottom summary bars. Carry it across every slide.

### Color Palettes

Choose colors that match your topic -- don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent | Dark | Light |
|-------|---------|-----------|--------|------|-------|
| **Teal Trust** | `065A60` | `0E7C86` | `14B8A6` | `042F2E` | `F0FDFA` |
| **Midnight Executive** | `1E2761` | `408EC6` | `CADCFC` | `1E2761` | `F8F9FC` |
| **Forest & Moss** | `2C5F2D` | `97BC62` | `4E9525` | `1A3A1C` | `F5F7F0` |
| **Coral Energy** | `F96167` | `F9E795` | `2F3C7E` | `2F3C7E` | `FFF8F0` |
| **Warm Terracotta** | `B85042` | `E7E8D1` | `A7BEAE` | `6B2E24` | `FAF8F0` |
| **Ocean Gradient** | `065A82` | `1C7293` | `21295C` | `0A2E42` | `F0F7FA` |
| **Charcoal Minimal** | `36454F` | `F2F2F2` | `212121` | `1A2228` | `F8F8F8` |
| **Berry & Cream** | `6D2E46` | `A26769` | `ECE2D0` | `3D1A28` | `FBF5F0` |
| **Cherry Bold** | `990011` | `FCF6F5` | `2F3C7E` | `4D0009` | `FFF8F7` |
| **Purple Tech** | `5B2C6F` | `7D3C98` | `AF7AC5` | `2C1338` | `F8F0FC` |

#### Extended Palette Reference (for non-brand work)

| # | Theme | Colors |
|---|-------|--------|
| 1 | Classic Blue | `#1C2833` `#2E4053` `#AAB7B8` `#F4F6F6` |
| 2 | Teal & Coral | `#5EA8A7` `#277884` `#FE4447` `#FFFFFF` |
| 3 | Bold Red | `#C0392B` `#E74C3C` `#F39C12` `#F1C40F` `#2ECC71` |
| 4 | Warm Blush | `#A49393` `#EED6D3` `#E8B4B8` `#FAF7F2` |
| 5 | Burgundy Luxury | `#5D1D2E` `#951233` `#C15937` `#997929` |
| 6 | Deep Purple & Emerald | `#B165FB` `#181B24` `#40695B` `#FFFFFF` |
| 7 | Cream & Forest | `#FFE1C7` `#40695B` `#FCFCFC` |
| 8 | Pink & Purple | `#F8275B` `#FF574A` `#FF737D` `#3D2F68` |
| 9 | Lime & Plum | `#C5DE82` `#7C3A5F` `#FD8C6E` `#98ACB5` |
| 10 | Black & Gold | `#BF9A4A` `#000000` `#F4F6F6` |
| 11 | Sage & Terracotta | `#87A96B` `#E07A5F` `#F4F1DE` `#2C2C2C` |
| 12 | Charcoal & Red | `#292929` `#E33737` `#CCCBCB` |
| 13 | Vibrant Orange | `#F96D00` `#F2F2F2` `#222831` |
| 14 | Forest Green | `#191A19` `#4E9F3D` `#1E5128` `#FFFFFF` |
| 15 | Retro Rainbow | `#722880` `#D72D51` `#EB5C18` `#F08800` `#DEB600` |
| 16 | Vintage Earthy | `#E3B448` `#CBD18F` `#3A6B35` `#F4F1DE` |
| 17 | Coastal Rose | `#AD7670` `#B49886` `#F3ECDC` `#BFD5BE` |
| 18 | Orange & Turquoise | `#FC993E` `#667C6F` `#FCFCFC` |

> Note: For ICHITA work, always use brand colors from [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) instead.

#### Supporting Colors (use across all palettes)

| Role | Color | Hex |
|------|-------|-----|
| Body text gray | Slate gray | `64748B` |
| Light gray border | Soft border | `E2E8F0` |
| White card background | Clean white | `FFFFFF` |
| Off-white page background | Warm neutral | `F8FAFB` |
| Error/warning red | Alert red | `DC2626` |
| Success green | Positive green | `059669` |
| Amber/caution | Warm amber | `D97706` |

### Typography

**Choose an interesting font pairing** -- don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font | Feel |
|-------------|-----------|------|
| **Trebuchet MS** | **Calibri** | Modern, clean (recommended) |
| Georgia | Calibri | Classic, trustworthy |
| Arial Black | Arial | Bold, corporate |
| Cambria | Calibri | Academic, formal |
| Impact | Arial | High-impact, punchy |
| Palatino | Garamond | Elegant, editorial |
| Consolas | Calibri | Technical, developer |

| Element | Size | Weight |
|---------|------|--------|
| Slide title | 28-44pt | Bold |
| Subtitle / tagline | 10-12pt | Italic, muted color |
| Section header | 14-24pt | Bold |
| Body text | 8.5-16pt | Regular |
| Card content | 8-9pt | Regular |
| Caption/footnote | 7-8pt | Muted color |
| Big stat number | 48-72pt | Bold |

### Layout Options

Refer to [layout-patterns.json](layout-patterns.json) for structured layout definitions with slot constraints.

**Every slide needs a visual element** -- image, chart, icon, or shape. Text-only slides are forgettable.

**Layout types:**
- **Two-column** (text left, illustration right)
- **Icon + text rows** (icon in colored circle, bold header, description below)
- **Card grid** (2x2, 2x3, 3-4 cards with colored headers and shadows)
- **Half-bleed image** with content overlay
- **Process flow** (numbered steps with arrows)
- **Timeline** (phase columns with progressive arrows)
- **Big stat callouts** (60-72pt numbers with small labels)
- **Comparison columns** (before/after, pros/cons)
- **Dark title slide** with accent bar

**Intent-to-layout mapping** (from layout-patterns.json):
- Problem statement -> grid_2x2, comparison
- Solution/features -> hero_split, content_left, grid_3col, feature_list
- Data/stats -> data_highlight, grid_3col, grid_4col
- Timeline -> timeline
- Quote -> quote_center, quote_side
- Opening/closing -> hero_center, cta

### Visual Details & Treatments

**Geometric Patterns**: Diagonal section dividers, asymmetric column widths (30/70, 40/60), rotated text headers, circular/hexagonal frames, triangular corner accents, overlapping shapes for depth

**Border & Frame**: Thick single-color borders (10-20pt) on one side only, double-line contrasting borders, corner brackets instead of full frames, L-shaped borders (top+left or bottom+right), underline accents beneath headers (3-5pt)

**Typography**: Extreme size contrast (72pt headlines vs 11pt body), all-caps headers with wide letter spacing, oversized numbered sections, monospace (Courier New) for data/stats, condensed fonts (Arial Narrow) for dense info, outlined text for emphasis

**Charts & Data**: Monochrome charts with single accent for key data, horizontal bar charts, dot plots, minimal/no gridlines, data labels directly on elements (no legends), oversized numbers for key metrics

**Backgrounds**: Solid color blocks (40-60% of slide), gradient fills (vertical/diagonal only), split backgrounds (two colors), edge-to-edge color bands, negative space as design element

### Spacing

- 0.5" minimum margins from slide edges
- 0.15-0.3" between content blocks
- Leave breathing room -- don't fill every inch
- Use consistent gaps (pick 0.15" or 0.3" and stick with it)

### Avoid (Common Mistakes)

- **Don't repeat the same layout** -- vary cards, columns, and callouts across slides
- **Don't center body text** -- left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** -- titles need 28pt+ to stand out from body text
- **Don't default to blue** -- pick colors that reflect the specific topic
- **Don't mix spacing randomly** -- choose a gap size and use consistently
- **Don't style one slide and leave the rest plain** -- commit fully or keep it simple throughout
- **Don't create text-only slides** -- add images, icons, charts, or visual elements
- **Don't forget text box padding** -- set `margin: 0` when aligning text with shapes
- **Don't use low-contrast elements** -- icons AND text need strong contrast against background
- **NEVER use accent lines under titles** -- hallmark of AI-generated slides
- **Don't use more than 7 bullet points per slide** -- break into multiple slides or use cards
- **Don't use full sentences as bullets** -- use keywords and short phrases, under 7 words each
- **Don't put titles touching the edge** -- center titles or give them breathing room

---

## Brand Mode: ICHITA

When creating presentations for ICHITA, switch from generic palettes to brand-specific defaults:

1. **Read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md)** for the complete brand guide
2. Override all generic color palettes, typography, and slide structure with ICHITA brand rules
3. Brand colors, fonts, and patterns take priority over the Design Ideas section above
4. Process diagrams use ICHITA-specific equipment colors and styling

ICHITA mode is activated when:
- The user mentions ICHITA, Ichita, or related brand names
- The presentation is for Ichita Co., Ltd. or its customers
- Brand templates are referenced

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**USE SUBAGENTS** -- even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues -- find them.

Look for:
- Overlapping elements (text through shapes, lines through words)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text or icons
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides -> Convert to images -> Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** -- one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

### Visual Tuning (Position Feedback from User)

**When the user says "almost", "not quite", or gives visual position feedback — STOP guessing coordinates.**

Visual positioning is perceptual. Do NOT iterate by guessing numbers in code. Instead:

1. **Generate** the first draft from code (best effort)
2. **User adjusts** in PowerPoint/LibreOffice (the right tool for visual work)
3. **User saves** the adjusted file
4. **Delegate extraction to a Sonnet/Haiku subagent** (NOT Opus — this is mechanical work):

```
Subagent prompt:
"Unpack this PPTX and extract element positions from content slides.

1. Run: python skills/pptx/ooxml/scripts/unpack.py <file> /tmp/unpack
2. Run: python skills/pptx/scripts/extract_positions.py /tmp/unpack [slide_range]
3. Return the position table. Note any consistent patterns (e.g., all titles share same x+w)."
```

Or if doing it yourself (small job), use the script directly:

```bash
python skills/pptx/ooxml/scripts/unpack.py adjusted.pptx /tmp/unpack
python skills/pptx/scripts/extract_positions.py /tmp/unpack 2-7
```

5. **Update code** with extracted values
6. **Update brand defaults** if it's a reusable pattern
7. **Regenerate + verify** once — done

**Anti-patterns**:
- Iterating position values in code based on verbal feedback ("move it up", "almost"). Leads to 5-6 frustrating rounds.
- Writing inline Python to extract XML instead of using `extract_positions.py`.
- Using Opus for mechanical extraction work — delegate to Sonnet/Haiku.

---

## Creating Thumbnail Grids

```bash
python scripts/thumbnail.py presentation.pptx [output_prefix] [--cols N]
```

- Default: 5 columns, max 30 slides per grid (5x6)
- Custom prefix: `python scripts/thumbnail.py template.pptx workspace/my-grid`
- Adjust columns: `--cols 4` (range: 3-6)
- Grid limits: 3 cols = 12, 4 cols = 20, 5 cols = 30, 6 cols = 42 slides/grid
- Slides are zero-indexed

---

## Converting to Images

```bash
# Linux:
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide

# macOS:
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

Creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:
```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Code Style Guidelines

**IMPORTANT**: When generating code for PPTX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

---

## Dependencies

- **pptxgenjs**: `npm install -g pptxgenjs` (creating presentations)
- **markitdown**: `pip install "markitdown[pptx]"` (text extraction)
- **playwright**: `npm install -g playwright` (HTML rendering -- Workflow B only)
- **react-icons**: `npm install -g react-icons react react-dom` (icons)
- **sharp**: `npm install -g sharp` (SVG rasterization and image processing)
- **Pillow**: `pip install Pillow` (thumbnail grids)
- **LibreOffice**: `soffice` command for PDF conversion
- **Poppler**: `pdftoppm` for PDF to images
- **defusedxml**: `pip install defusedxml` (secure XML parsing)
