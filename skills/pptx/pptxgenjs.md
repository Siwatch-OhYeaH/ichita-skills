# PowerPoint Skill — Complete Reference

This file is your complete guide to creating beautiful, professional PowerPoint presentations using `pptxgenjs`. Read this BEFORE writing any code.

---

## Table of Contents

1. [Workflow: Draft First, Design Second](#workflow-draft-first-design-second)
2. [Storytelling & Narrative Structure](#storytelling--narrative-structure)
3. [Design Philosophy](#design-philosophy)
4. [Color Palettes](#color-palettes)
5. [Typography](#typography)
6. [Layout Patterns](#layout-patterns)
7. [Layout Fitting & Overflow Prevention](#layout-fitting--overflow-prevention)
8. [PptxGenJS API Reference](#pptxgenjs-api-reference)
9. [Common Pitfalls](#common-pitfalls)
10. [QA Process](#qa-process)
11. [Example Patterns](#example-patterns)

---

## Workflow: Draft First, Design Second

**NEVER jump straight into code.** The biggest mistake is opening pptxgenjs and starting to write `addText()` calls immediately. Instead, follow this 4-phase workflow:

### Phase 1: Understand the Content (2 minutes)

Before anything else, ask yourself:
- **Who is the audience?** (Executive = high-level, Technical = detailed, Customer = persuasive)
- **What is the ONE key message?** (If the audience remembers only one thing, what should it be?)
- **What action should they take after seeing this?** (Approve? Invest? Understand? Decide?)
- **How many slides?** (Rule of thumb: 1-2 minutes per slide. 20-minute presentation = 10-15 slides)

### Phase 2: Create the Outline (3 minutes)

Write a plain-text outline of EVERY slide before writing any code. Each slide gets:

```
Slide 1: [Title Slide] — "Our Engineering Capability for Allulose"
Slide 2: [Process Flow] — Complete 6-step production process, shows we can design every unit
Slide 3: [Deep Dive] — SMB Chromatography detail, two-panel: how it works + what we design
Slide 4: [Card Grid] — 5 purification steps with icons, shows core competency
Slide 5: [Data Flow] — Mass balance with real numbers, shows we do the math
Slide 6: [Product Cards] — 3 product forms with specs & pricing
Slide 7: [Timeline] — 4-phase scope of work, shows professionalism
```

For each slide, note:
- **The slide's ONE message** (in plain English)
- **The layout pattern** that best fits the content (card grid? process flow? two-panel? stats?)
- **How much content** is going on this slide (this determines if it's a "dense" or "light" slide)

### Phase 3: Check the Outline (1 minute)

Before writing code, review your outline for these problems:

**Narrative flow:**
- Does slide 1 hook the audience? (Don't start with boring background — start with why they should care)
- Does each slide logically lead to the next? (Could you remove a slide and the story still works? If yes, remove it.)
- Does the final slide deliver a clear conclusion or call to action?
- Is the "so what?" clear on every slide?

**Layout variety:**
- Are you using at least 3 DIFFERENT layout patterns across the deck?
- Are any 3 slides in a row using the same layout? (If yes, redesign the middle one)
- Does the dense/light rhythm feel balanced? (Don't stack 5 dense slides in a row)

**Content volume:**
- Does any slide have more than 6 content groups? (Split it)
- Is any slide trying to make more than ONE key point? (Split it)
- Will any text need to be smaller than 8pt to fit? (Split it or cut content)

### Phase 4: Build with Code

NOW you can start writing pptxgenjs code. Build one slide at a time, following the outline exactly.

---

## Storytelling & Narrative Structure

A presentation is NOT a document — it's a story told one frame at a time. The audience sees one slide at a time and can't scroll back. Structure matters.

### The 3-Act Structure for Business Presentations

**Act 1: Setup (Slides 1-2)** — Hook the audience
- Slide 1: Title slide with compelling framing (NOT just a title — make them curious)
- Slide 2: The problem, opportunity, or context. Why should they care RIGHT NOW?

**Act 2: Evidence (Slides 3-N)** — Build your case
- Each slide presents one piece of evidence, one insight, or one component
- Vary the intensity: alternate between dense data slides and lighter visual slides
- Use transitions in your titles to show progression: "The Challenge" → "Our Approach" → "The Solution" → "The Economics"

**Act 3: Resolution (Final 1-2 slides)** — Drive to action
- Second-to-last: Summary or verdict (the "so what?")
- Last slide: Clear next steps or call to action. Never end on "Thank you" — end on "Here's what we should do next"

### Storytelling Techniques for Slides

**1. Front-load the insight**
Put the conclusion in the slide TITLE, not buried in the body. Bad: "Market Analysis". Good: "Price Dropped 80% But Recovery is Starting".

**2. Create tension and resolution**
- Slide: "Here's the risk" (erythritol crash precedent)
- Next slide: "Here's why we're different" (our advantages)
- Next slide: "Here's the verdict" (conditional GO)

**3. Use the "newspaper headline" test**
Every slide title should work as a newspaper headline — it should tell you the conclusion, not just the topic. The audience should be able to read ONLY the titles and understand the full story.

Bad titles (topics): "Price Analysis", "Competition", "Technology", "Recommendation"
Good titles (insights): "Price Crashed 80% Since 2021", "Chinese Producers Adding 30,000 t/y", "SMB Chromatography is the Critical Unit", "Conditional GO at 2,000-3,000 t/y"

**4. Progressive disclosure**
Don't dump everything at once. Build up:
- Slide 3: "Here's the opportunity" (positive)
- Slide 4: "But here's the risk" (tension)
- Slide 5: "Here's how the numbers actually work" (evidence)
- Slide 6: "And here's our verdict" (resolution)

**5. One message per slide**
If you find yourself saying "this slide also shows..." — you need two slides. Splitting costs nothing but improves comprehension dramatically.

### Slide Transition Logic

Each slide should connect to the next. Use these transition patterns:

| From → To | Transition Logic |
|-----------|-----------------|
| Problem → Solution | "So what do we do about it?" |
| Overview → Deep Dive | "Let's look closer at the most critical part" |
| Data → Insight | "What does this mean for us?" |
| Risk → Mitigation | "Here's how we protect against this" |
| Analysis → Recommendation | "Based on all of this, our verdict is..." |
| Features → Benefits | "What does this mean for the customer?" |
| Past → Future | "Where do we go from here?" |

### Presentation Types & Their Story Arcs

**Investment/Business Case:**
Hook (opportunity) → Market evidence → Risk analysis → Economics → Competitive advantage → Verdict → Next steps

**Technical Capability:**
Title (what we do) → Process overview → Deep dive on critical unit → Supporting capabilities → Product portfolio → Scope of work → Timeline

**Problem-Solution:**
Pain point → Why it matters → Current approaches (and why they fail) → Our solution → Evidence it works → How to get started

**Status Update / Review:**
Key metric summary → What went well → What needs attention → Root cause → Action plan → Timeline

---

## Design Philosophy

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Your goal is to create presentations that look like they came from a professional design agency, not from an AI.

### The 5 Core Design Principles

These are the principles that make tools like Gamma AI, Beautiful.ai, and top design agencies produce stunning results. Apply ALL of them to every presentation.

#### 1. Visual Hierarchy — Guide the Eye

Every slide must have a clear reading order: what should the viewer see FIRST, SECOND, THIRD?

- **Size creates importance**: The most important element should be the largest. Title 28-40pt, body 8-10pt — the gap must be dramatic, not subtle.
- **Placement directs attention**: Most important info goes top-left or center. The eye naturally starts there.
- **Color draws focus**: Use your accent color ONLY on the one thing you want people to notice first. Everything else stays neutral.
- **Weight signals priority**: Bold for headlines and labels. Regular for descriptions. Never bold entire paragraphs.

**Test**: Squint at your slide. Can you still tell what's most important? If everything blurs together equally, your hierarchy has failed.

#### 2. Whitespace — Let It Breathe

Whitespace is NOT wasted space — it's the single most powerful design tool. The space between elements is as important as the elements themselves.

- **More space = more importance**: To make something stand out, add space around it, not decorations.
- **Group related items**: Minimize space between related elements (title + subtitle), maximize space between groups (section A vs section B).
- **Never fill every corner**: Leave 15-20% of the slide empty. This signals confidence and professionalism.
- **Margins matter**: 0.5" minimum from all slide edges. Content touching the edge looks cramped and amateur.
- **Breathing room inside cards**: Leave generous padding inside boxes and cards (0.1-0.15" internal margin). Don't pack text edge-to-edge.

**The #1 amateur mistake is filling all available space.** Resist the urge.

#### 3. Consistency — Build Trust Through Repetition

Inconsistency is what makes presentations look "AI-generated" or amateur.

- **One visual motif**: Pick ONE distinctive element and repeat it on every slide — colored circles for icons, left accent bars, card-based layouts with colored headers, dark bottom summary bars.
- **Same font pairing everywhere**: Header font + body font, never mix more.
- **Same color roles everywhere**: If teal is for headers, it's ALWAYS for headers. If gray is for body text, it's ALWAYS for body text.
- **Same spacing**: Pick your gap size (0.15" or 0.3") and use it consistently between all similar elements.
- **Same element sizes**: If card width is 3.0" on slide 3, it's 3.0" on slide 6 too.

#### 4. Contrast — Make Things Pop

Without contrast, everything looks flat and lifeless.

- **Dark vs light backgrounds**: Use dark backgrounds (title + conclusion = "sandwich") with light for content slides. Or commit to full-dark for premium feel.
- **Text must be readable**: Light text on dark backgrounds, dark text on light backgrounds. Test: is there enough contrast to read at a distance?
- **Size contrast between levels**: Don't use 14pt and 16pt for title vs body — the difference is invisible. Use 28pt vs 10pt — THAT creates hierarchy.
- **Color contrast for callouts**: Use your accent color against neutral backgrounds to make key stats or labels pop.

#### 5. Content-Driven Design — Match Layout to Message

This is what Gamma AI does well: it analyzes content type and picks the right layout. You should do the same.

- **Comparison content** → side-by-side columns or cards with colored headers
- **Process/workflow** → numbered steps with arrows, horizontal flow
- **Key statistics** → big stat callouts (48-72pt numbers with small labels)
- **Lists of items** → card grid (3-4 cards with icons/colored headers)
- **Narrative/explanation** → two-panel layout (text left, visual right)
- **Timeline** → phase columns with progressive arrows
- **Summary/verdict** → dark background with categorized sections (GO/NO-GO, Pros/Cons)

**Every slide needs at least one visual element** — shapes, icons, colored boxes, charts. Text-only slides are forgettable.

### Before Starting Any Presentation

1. **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
2. **Define 5 color roles**: Primary (60%), Secondary (20%), Accent (10%), Dark (backgrounds), Light (backgrounds). Plus supporting neutrals (gray for body text, white for cards).
3. **Choose your font pairing**: One header font with personality + one clean body font.
4. **Commit to a visual motif**: Pick ONE and carry it through EVERY slide.
5. **Plan layout variety**: Sketch which layout pattern fits each slide's content. NEVER repeat the same layout 3 times in a row.

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary cards, columns, flows across slides
- **Don't center body text** — left-align paragraphs; center only titles and short labels
- **Don't skimp on size contrast** — titles 28-40pt, body 8-10pt on dense slides
- **Don't default to blue** — pick colors that match the topic
- **Don't create text-only slides** — add shapes, icons, colored boxes
- **NEVER use accent lines under titles** — hallmark of AI-generated slides
- **Don't forget `margin: 0`** on text boxes when aligning with shapes
- **Don't use more than 7 bullet points per slide** — break into multiple slides or use cards instead
- **Don't use full sentences as bullets** — use keywords and short phrases, under 7 words each
- **Don't put titles in the top-left corner touching the edge** — center titles or give them breathing room
- **Don't use generic stock imagery** — colored shapes, icons, and data visualizations are stronger than clip art

---

## Color Palettes

Choose colors that match your topic. Use these as inspiration:

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

### Supporting Colors (use across all palettes)

| Role | Color | Hex |
|------|-------|-----|
| Body text gray | Slate gray | `64748B` |
| Light gray border | Soft border | `E2E8F0` |
| White card background | Clean white | `FFFFFF` |
| Off-white page background | Warm neutral | `F8FAFB` |
| Error/warning red | Alert red | `DC2626` |
| Success green | Positive green | `059669` |
| Amber/caution | Warm amber | `D97706` |

---

## Typography

### Font Pairing

| Header Font | Body Font | Feel |
|-------------|-----------|------|
| **Trebuchet MS** | **Calibri** | Modern, clean (recommended) |
| Georgia | Calibri | Classic, trustworthy |
| Arial Black | Arial | Bold, corporate |
| Cambria | Calibri | Academic, formal |
| Impact | Arial | High-impact, punchy |

### Size Guide

| Element | Size | Weight |
|---------|------|--------|
| Slide title | 24-40pt | Bold |
| Subtitle / tagline | 10-12pt | Italic, muted color |
| Section header | 12-14pt | Bold |
| Body text | 8.5-10pt | Regular |
| Card content | 8-9pt | Regular |
| Caption/footnote | 7-8pt | Muted color |
| Big stat number | 48-72pt | Bold |

### Spacing

- 0.5" minimum margins from slide edges
- 0.15-0.3" between content blocks
- Leave breathing room — don't fill every inch
- Use consistent gaps (pick 0.15" or 0.3" and stick with it)

---

## Advanced Design Techniques

### The "Gamma Effect" — What Makes AI Presentations Look Professional

These techniques are what separates mediocre AI slides from presentations that look like they came from a design agency:

#### 1. Colored Header Bars on Cards
Don't just use white cards — give each card a colored header strip (0.3-0.45" tall) that immediately signals the card's topic. Use different colors from your palette for different categories.

#### 2. Dark Summary Bars
Add a dark background rectangle at the bottom of content slides (about 20-25% of slide height) containing the key takeaway, summary, or call to action. This creates a visual anchor and ensures the most important message is always visible.

#### 3. Number Badges in Circles
For process flows and numbered items, put numbers inside colored circles (0.5-0.6" diameter). This is 10× more visually appealing than plain numbered text.

#### 4. Accent Bars on Panel Edges
For two-panel layouts, add a thin colored bar (0.05-0.08" wide) on the left edge of one panel. This subtle detail signals visual grouping and adds a splash of color without being heavy.

#### 5. Color-Coded Tags/Labels
For categorized content (GO/NO-GO, Status, Priority), use small colored rectangles (0.6" × 0.2") as labels with white text inside. Much more visual than plain text labels.

#### 6. Consistent Card Shadows
Add subtle shadows to all cards/panels: `shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 }`. This lifts elements off the background and creates depth.

#### 7. Top Accent Line
Add a thin colored bar (full width, 0.06" tall) at the very top of every slide. This creates continuity and polish across the entire deck. Match the color to slide content (e.g., purple for chromatography slides, green for product slides).

#### 8. Breathing Room Between Sections
Use a light-colored background rectangle (e.g., light green `ECFDF5`) as a "callout bar" between main content and the dark bottom bar. Perfect for recycle streams, connections, footnotes, or secondary info.

### Content Architecture Rules

Apply these rules from professional presentation designers:

- **One core message per slide**: If you can't summarize the slide in one sentence, split it into two slides.
- **6×6 rule maximum**: No more than 6 groups of content per slide, no more than 6 words per label.
- **Tell a story across slides**: Each slide should logically flow to the next. Use consistent motifs (same card style, same bottom bar) to create narrative continuity.
- **Front-load the insight**: Put the conclusion/recommendation at the TOP of the slide (in the title or subtitle), then show the evidence below. Don't make the audience wait.
- **Use the "squint test"**: If you squint at the slide and can't tell what's most important, the visual hierarchy needs work.

---

## Layout Patterns

### Pattern 1: Card Grid

Best for: comparisons, feature lists, team members, options

```
┌─────────────────────────────────────────┐
│ Title (24-28pt bold)                     │
│ Subtitle (10pt gray italic)              │
├───────────┬───────────┬───────────┬──────┤
│ [Colored  │ [Colored  │ [Colored  │      │
│  Header]  │  Header]  │  Header]  │      │
│           │           │           │      │
│ Body text │ Body text │ Body text │      │
│           │           │           │      │
└───────────┴───────────┴───────────┘      │
│ [Dark bottom bar with key takeaway]      │
└─────────────────────────────────────────┘
```

### Pattern 2: Process Flow

Best for: workflows, timelines, step-by-step

```
┌─────────────────────────────────────────┐
│ Title                                    │
│                                          │
│  (01)  →  (02)  →  (03)  →  (04)       │
│  Name     Name     Name     Name        │
│  Detail   Detail   Detail   Detail      │
│                                          │
│ [Recycle/connection stream bar]          │
│                                          │
│ [Dark bottom bar with deliverables]     │
└─────────────────────────────────────────┘
```

### Pattern 3: Two-Panel (Left/Right)

Best for: explanation + specification, before/after

```
┌──────────────────┬──────────────────────┐
│ Title             │ Title                │
│                   │                      │
│ Paragraph text    │ • Item with title    │
│ explaining the    │   and description    │
│ concept in        │ • Item with title    │
│ readable prose    │   and description    │
│                   │ • Item with title    │
│                   │   and description    │
├──────────────────┴──────────────────────┤
│ [Dark bottom bar with key insight]      │
└─────────────────────────────────────────┘
```

### Pattern 4: Big Stat Callouts

Best for: KPIs, financial results, impact numbers

```
┌─────────────────────────────────────────┐
│ Title                                    │
│                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │ $4.8 │  │ 80%  │  │ 600t │          │
│  │ /kg  │  │ drop │  │ /yr  │          │
│  │ label│  │ label│  │ label│          │
│  └──────┘  └──────┘  └──────┘          │
│                                          │
│ [Context or explanation below]          │
└─────────────────────────────────────────┘
```

### Pattern 5: Dark Title Slide

Best for: opening, closing, section dividers

```
┌─────────────────────────────────────────┐
│ [Dark background]                        │
│                                          │
│ │ Title Text (36-44pt white bold)       │
│ │ with accent bar on left               │
│                                          │
│   Subtitle (14pt accent color)          │
│                                          │
│   Tagline (12pt gray italic)            │
│                                          │
└─────────────────────────────────────────┘
```

---

## Layout Fitting & Overflow Prevention

This is the most common problem with programmatic slide generation: **text overflows its box, elements overlap, or content gets cut off.** Follow these rules to prevent it.

### The Slide is 10" × 5.625" — Know Your Budget

Every element competes for the same 10" × 5.625" space. Before coding, calculate your layout budget:

```
Total slide height:    5.625"
- Top accent line:     0.06"
- Title area:          0.65" (title + subtitle)
- Gap after title:     0.1"
- Content zone:        3.0" - 3.5" (this is ALL you have for main content)
- Gap before footer:   0.1"
- Bottom bar:          1.0" - 1.2" (dark summary bar)
= Total:               ~5.6"
```

**Content zone is only 3.0-3.5" tall.** Everything must fit in this band. Plan accordingly.

### Width Budget for Cards & Columns

For N cards side by side with gaps:
```
Available width:     10" - 0.5" left margin - 0.5" right margin = 9.0"
Card width:          (9.0" - (N-1) × gap) / N

3 cards, 0.15" gap:  (9.0 - 0.30) / 3 = 2.9" each
4 cards, 0.15" gap:  (9.0 - 0.45) / 4 = 2.14" each
5 cards, 0.1" gap:   (9.0 - 0.40) / 5 = 1.72" each
6 cards, 0.1" gap:   (9.0 - 0.50) / 6 = 1.42" each
```

**Rule: Card width < 1.5" means text will be too cramped.** If you need 6+ items, use two rows or a different layout.

### Text Overflow Prevention Rules

#### Rule 1: Estimate Lines BEFORE Coding

For a text box of width W inches at font size S:
- **Characters per line ≈ W × 12 for 8pt, W × 10 for 10pt, W × 7 for 14pt**
- Count your characters, divide by chars-per-line, multiply by line height
- Line height ≈ font size × 1.4 (e.g., 10pt text → ~14pt line height → ~0.19" per line)

Example: "SMB Chromatography: The Heart of the Process" = 46 characters
- In a 4" wide box at 13pt: ~28 chars/line → 2 lines → needs ~0.45" height
- In a 2" wide box at 10pt: ~20 chars/line → 3 lines → needs ~0.45" height

**Always add 20% buffer to your height estimate.** Text wraps unpredictably with different fonts.

#### Rule 2: Use Fixed Heights, Not Wishful Thinking

Don't set text box height to exactly what you think the text needs. Set it 20-30% larger to prevent clipping:

```javascript
// ❌ RISKY: height exactly matches expected content
s.addText(longTitle, { x: 0.5, y: 0.15, w: 9, h: 0.3, fontSize: 24 });

// ✅ SAFE: generous height allows for wrapping
s.addText(longTitle, { x: 0.5, y: 0.15, w: 9, h: 0.55, fontSize: 24 });
```

#### Rule 3: Shrink Font Before Shrinking Space

When content doesn't fit, reduce font size first (down to 7.5pt minimum), then reduce content. Never squish elements together with < 0.05" gaps.

**Minimum readable font sizes:**
- Body text: 8pt minimum (7.5pt for dense technical slides)
- Labels inside small shapes: 7pt minimum
- Never go below 7pt for any text

#### Rule 4: Test Long Content Variants

When generating slides programmatically with variable content, test with the LONGEST possible text:
- Longest title you might have
- Most items in a list
- Longest label names

Build your layout to accommodate the worst case, not the average case.

#### Rule 5: The Overlap Checklist

Before finalizing any slide, verify these element-by-element:

```
For every text box and shape, check:
  y_position + height ≤ y_position of the element below it
  x_position + width  ≤ x_position of the element to its right
  No element extends beyond x=10" (right edge) or y=5.625" (bottom edge)
  No element starts before x=0" or y=0"
```

### Safe Zone Map for 16:9 Slides

```
┌──────────────────────────────────────────────────────────┐ y=0"
│░░░░░░░░░░░░░░░░ TOP ACCENT LINE ░░░░░░░░░░░░░░░░░░░░░░│ y=0.06"
│                                                          │
│  ┌─TITLE ZONE─────────────────────────────────────────┐  │ y=0.15"
│  │ Title (24-40pt) + Subtitle (10-12pt)               │  │
│  └────────────────────────────────────────────────────┘  │ y=0.8"
│                                                          │
│  ┌─CONTENT ZONE──────────────────────────────────────┐  │ y=0.9"
│  │                                                    │  │
│  │  Main content area: cards, charts, text, images    │  │
│  │  Maximum usable area: 9.0" wide × 3.0-3.2" tall   │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │ y=3.9-4.1"
│                                                          │
│  ┌─FOOTER ZONE────────────────────────────────────────┐  │ y=4.0-4.2"
│  │ Dark summary bar / Key takeaway / Next steps       │  │
│  │ Height: 1.0-1.3"                                   │  │
│  └────────────────────────────────────────────────────┘  │ y=5.2-5.4"
│                                                          │
└──────────────────────────────────────────────────────────┘ y=5.625"
  x=0"  x=0.3"                                  x=9.7" x=10"
        └── content starts here     content ends here ──┘
```

### When Content Doesn't Fit — Decision Tree

```
Content too tall for the slide?
├── Can you split into 2 slides? → YES → Split (best option)
├── Can you reduce font by 1-2pt? → YES → Reduce (still readable?)
├── Can you cut words? → YES → Tighten language
├── Can you remove the bottom bar? → YES → Gain 1.0-1.2" height
├── Can you shrink title area? → YES → Reduce title font from 24→20pt
└── None work? → Use a DIFFERENT layout pattern (e.g., switch from cards to two-panel)

Content too wide for cards?
├── Reduce number of cards (5→3 + second row)
├── Reduce card gap from 0.15"→0.1"
├── Reduce font size by 1pt
├── Abbreviate labels
└── Switch to vertical stacking instead of horizontal
```

### The Golden Rule of Layout

**When in doubt, give LESS content MORE space.** A slide with 3 well-spaced cards looks 10× better than 5 cramped cards. It's always better to split into two clean slides than cram everything into one messy slide.

---

## PptxGenJS API Reference

### Setup

```javascript
// CommonJS (.cjs files, or package.json without "type": "module")
const pptxgen = require("pptxgenjs");

// ESM (.mjs files, or package.json with "type": "module")
// import pptxgen from "pptxgenjs";

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";  // 10" × 5.625"
pres.author = "Author Name";
pres.title = "Presentation Title";

let slide = pres.addSlide();
// ... add content ...

pres.writeFile({ fileName: "output.pptx" });
```

> **ESM projects**: If your `package.json` has `"type": "module"`, save the
> script with `.cjs` extension (e.g., `slides.cjs`) or use `import` syntax instead.

### Slide Dimensions

- `LAYOUT_16x9`: 10" wide × 5.625" tall (recommended)
- `LAYOUT_16x10`: 10" × 6.25"
- `LAYOUT_4x3`: 10" × 7.5"

### Text

```javascript
// Basic text
slide.addText("Hello", {
  x: 0.5, y: 0.5, w: 9, h: 0.5,
  fontSize: 24, fontFace: "Trebuchet MS",
  color: "042F2E", bold: true,
  align: "left", valign: "middle",
  margin: 0  // IMPORTANT: set 0 when aligning with shapes
});

// Rich text (mixed styles in one box)
slide.addText([
  { text: "Bold part ", options: { bold: true, color: "042F2E", fontSize: 12 } },
  { text: "normal part", options: { color: "64748B", fontSize: 12 } },
], { x: 0.5, y: 1, w: 9, h: 0.3, fontFace: "Calibri", margin: 0 });

// Multi-line with breakLine
slide.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2", options: { breakLine: true } },
  { text: "Line 3" }
], { x: 0.5, y: 1, w: 8, h: 2 });

// Character spacing (NOT letterSpacing — that's silently ignored)
slide.addText("SPACED", { charSpacing: 6 });
```

### Shapes

```javascript
// Rectangle (most common — cards, bars, backgrounds)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 9, h: 1.2,
  fill: { color: "042F2E" },  // NO # prefix!
  shadow: shadow()  // use factory function (see below)
});

// Circle (for icons, number badges)
slide.addShape(pres.shapes.OVAL, {
  x: 1, y: 1, w: 0.5, h: 0.5,  // equal w/h = circle
  fill: { color: "065A60" }
});

// Line
slide.addShape(pres.shapes.LINE, {
  x: 0.5, y: 2, w: 9, h: 0,
  line: { color: "E2E8F0", width: 1 }
});

// Shadow factory function (MUST use factory — never reuse objects)
const shadow = () => ({
  type: "outer", blur: 6, offset: 2,
  angle: 135, color: "000000", opacity: 0.12
});
```

### Shadow Options

| Property | Type | Range | Notes |
|----------|------|-------|-------|
| `type` | string | `"outer"`, `"inner"` | |
| `color` | string | 6-char hex (e.g. `"000000"`) | No `#` prefix, no 8-char hex -- see Common Pitfalls |
| `blur` | number | 0-100 pt | |
| `offset` | number | 0-200 pt | **Must be non-negative** -- negative values corrupt the file |
| `angle` | number | 0-359 degrees | Direction the shadow falls (135 = bottom-right, 270 = upward) |
| `opacity` | number | 0.0-1.0 | Use this for transparency, never encode in color string |

To cast a shadow upward (e.g. on a footer bar), use `angle: 270` with a positive offset -- do **not** use a negative offset.

**Note**: Gradient fills are not natively supported by PptxGenJS. Use a gradient image as a background instead.

### Backgrounds

```javascript
// Solid color
slide.background = { color: "F8FAFB" };  // light
slide.background = { color: "042F2E" };  // dark

// Image
slide.background = { path: "image.jpg" };
slide.background = { data: "image/png;base64,..." };
```

### Images

```javascript
// From file
slide.addImage({ path: "chart.png", x: 1, y: 1, w: 5, h: 3 });

// From base64
slide.addImage({ data: "image/png;base64,...", x: 1, y: 1, w: 5, h: 3 });

// Sizing modes
slide.addImage({ path: "img.png", x: 1, y: 1, w: 5, h: 3,
  sizing: { type: "contain", w: 5, h: 3 }  // fit inside, keep ratio
});
```

### Tables

```javascript
// Simple table
slide.addTable([
  [{ text: "Header", options: { fill: { color: "065A60" }, color: "FFFFFF", bold: true } }, "Value"],
  ["Row 1", "Data"],
], { x: 0.5, y: 1, w: 9, colW: [3, 6], border: { pt: 0.5, color: "E2E8F0" } });
```

### Charts

```javascript
slide.addChart(pres.charts.BAR, [{
  name: "Sales", labels: ["Q1", "Q2", "Q3"], values: [45, 55, 62]
}], {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd",
  showLegend: false,
});
// Chart types: BAR, LINE, PIE, DOUGHNUT, SCATTER
```

### Better-Looking Charts

Default charts look dated. Apply these options for a modern, clean appearance:

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",

  // Custom colors (match your presentation palette)
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],

  // Clean background
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },

  // Muted axis labels
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",

  // Subtle grid (value axis only)
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },

  // Data labels on bars
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "1E293B",

  // Hide legend for single series
  showLegend: false,
});
```

**Key styling options:**
- `chartColors: [...]` - hex colors for series/segments
- `chartArea: { fill, border, roundedCorners }` - chart background
- `catGridLine/valGridLine: { color, style, size }` - grid lines (`style: "none"` to hide)
- `lineSmooth: true` - curved lines (line charts)
- `legendPos: "r"` - legend position: "b", "t", "l", "r", "tr"

### Lists & Bullets

```javascript
// CORRECT way to do bullets
slide.addText([
  { text: "First item", options: { bullet: true, breakLine: true } },
  { text: "Second item", options: { bullet: true, breakLine: true } },
  { text: "Third item", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });

// NEVER use unicode bullets like "•" — causes double bullets
```

---

## Common Pitfalls

These cause file corruption, visual bugs, or broken output. **Memorize these.**

### 1. NEVER use `#` with hex colors

```javascript
color: "FF0000"      // ✅ CORRECT
color: "#FF0000"     // ❌ CORRUPTS FILE
```

### 2. NEVER encode opacity in hex color strings

```javascript
shadow: { color: "00000020" }                    // ❌ CORRUPTS FILE
shadow: { color: "000000", opacity: 0.12 }       // ✅ CORRECT
```

### 3. NEVER reuse option objects

PptxGenJS mutates objects in-place. Sharing one object between calls corrupts the second shape.

```javascript
// ❌ WRONG
const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... }); // BROKEN

// ✅ CORRECT — use factory function
const shadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
slide.addShape(pres.shapes.RECTANGLE, { shadow: shadow(), ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow: shadow(), ... });
```

### 4. NEVER use unicode bullets

```javascript
slide.addText("• Item", { ... });  // ❌ Creates double bullets
{ text: "Item", options: { bullet: true } }  // ✅ CORRECT
```

### 5. Shadow offset must be non-negative

Negative offset values corrupt the file. To cast shadow upward, use `angle: 270` with positive offset.

### 6. Don't use ROUNDED_RECTANGLE with accent bars

Rectangular overlay bars won't cover rounded corners. Use RECTANGLE instead.

### 7. Don't use `lineSpacing` with bullets

Causes excessive gaps. Use `paraSpaceAfter` instead.

### 8. Set `margin: 0` on text boxes

When aligning text with shapes or icons at the same position, text has default internal padding. Set `margin: 0` to align precisely.

### 9. Use `breakLine: true` between array items

Without `breakLine: true`, text runs together on the same line instead of creating separate lines.

```javascript
// ❌ WRONG — all text on one line
slide.addText([
  { text: "Line 1", options: {} },
  { text: "Line 2", options: {} }
], { ... });

// ✅ CORRECT
slide.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2" }  // last item doesn't need breakLine
], { ... });
```

### 10. Each presentation needs a fresh instance

Don't reuse `pptxgen()` objects across presentations. Create a new `new pptxgen()` for each presentation file.

---

## QA Process

### REQUIRED: Visual inspection of every slide

```bash
# Convert to images
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
# Creates slide-1.jpg, slide-2.jpg, etc.
```

**On macOS, the LibreOffice command may be:**
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf output.pptx
```

### What to look for

- Overlapping elements (text through shapes)
- Text overflow or cut off at edges
- Elements too close (< 0.15" gaps)
- Uneven spacing (large empty area vs cramped area)
- Insufficient margin from slide edges (< 0.5")
- Low-contrast text (light on light, dark on dark)
- Text boxes too narrow causing excessive wrapping
- Misaligned columns or cards

### Fix and re-verify

1. Generate → convert to images → inspect
2. List issues found
3. Fix issues in the code
4. Re-generate → re-inspect affected slides
5. Repeat until clean

**Your first render is almost never correct. Assume there are problems.**

---

## Example Patterns

### Dark Title Slide with Accent Bar

```javascript
let s = pres.addSlide();
s.background = { color: "042F2E" };
// Top accent line
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "14B8A6" } });
// Left accent bar
s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.3, w: 0.08, h: 2.2, fill: { color: "14B8A6" } });
// Title
s.addText("Your Title\nGoes Here", {
  x: 1.0, y: 1.3, w: 8, h: 1.8,
  fontSize: 40, fontFace: "Trebuchet MS", color: "FFFFFF", bold: true, margin: 0,
});
// Subtitle
s.addText("Subtitle text in accent color", {
  x: 1.0, y: 3.3, w: 8, h: 0.4,
  fontSize: 14, fontFace: "Calibri", color: "14B8A6", margin: 0,
});
```

### Card-Based Content Slide

```javascript
let s = pres.addSlide();
s.background = { color: "F8FAFB" };
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: "14B8A6" } });
s.addText("Slide Title", {
  x: 0.5, y: 0.15, w: 9, h: 0.5,
  fontSize: 24, fontFace: "Trebuchet MS", color: "042F2E", bold: true, margin: 0,
});

// Three cards
const cards = [
  { title: "Card One", detail: "Description here", color: "065A60" },
  { title: "Card Two", detail: "Description here", color: "0E7C86" },
  { title: "Card Three", detail: "Description here", color: "14B8A6" },
];
cards.forEach((c, i) => {
  const x = 0.3 + i * 3.2;
  const shadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });
  // Card background
  s.addShape(pres.shapes.RECTANGLE, { x, y: 0.9, w: 3.0, h: 2.5, fill: { color: "FFFFFF" }, shadow: shadow() });
  // Colored header bar
  s.addShape(pres.shapes.RECTANGLE, { x, y: 0.9, w: 3.0, h: 0.4, fill: { color: c.color } });
  s.addText(c.title, { x: x + 0.1, y: 0.92, w: 2.8, h: 0.36, fontSize: 12, fontFace: "Calibri", color: "FFFFFF", bold: true, margin: 0 });
  s.addText(c.detail, { x: x + 0.1, y: 1.4, w: 2.8, h: 1.8, fontSize: 9, fontFace: "Calibri", color: "64748B", margin: 0 });
});

// Dark bottom bar with key takeaway
s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.8, w: 9.2, h: 1.0, fill: { color: "042F2E" } });
s.addText("Key Takeaway", { x: 0.7, y: 3.85, w: 8.8, h: 0.25, fontSize: 12, fontFace: "Calibri", color: "14B8A6", bold: true, margin: 0 });
s.addText("Summary text goes here.", { x: 0.7, y: 4.15, w: 8.8, h: 0.55, fontSize: 9.5, fontFace: "Calibri", color: "E2E8F0", margin: 0 });
```

### Process Flow with Numbered Steps

```javascript
let s = pres.addSlide();
s.background = { color: "F8FAFB" };

const steps = [
  { num: "01", name: "Step One", detail: "Details...", color: "065A60" },
  { num: "02", name: "Step Two", detail: "Details...", color: "0E7C86" },
  { num: "03", name: "Step Three", detail: "Details...", color: "14B8A6" },
  { num: "04", name: "Step Four", detail: "Details...", color: "059669" },
];
steps.forEach((st, i) => {
  const x = 0.3 + i * 2.4;
  const shadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });
  s.addShape(pres.shapes.RECTANGLE, { x, y: 0.9, w: 2.2, h: 2.5, fill: { color: "FFFFFF" }, shadow: shadow() });
  // Number circle
  s.addShape(pres.shapes.OVAL, { x: x + 0.8, y: 1.0, w: 0.6, h: 0.6, fill: { color: st.color } });
  s.addText(st.num, { x: x + 0.8, y: 1.0, w: 0.6, h: 0.6, fontSize: 16, fontFace: "Trebuchet MS", color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0 });
  // Name
  s.addText(st.name, { x: x + 0.1, y: 1.7, w: 2.0, h: 0.3, fontSize: 11, fontFace: "Calibri", color: "042F2E", bold: true, align: "center", margin: 0 });
  // Detail
  s.addText(st.detail, { x: x + 0.1, y: 2.05, w: 2.0, h: 1.2, fontSize: 8.5, fontFace: "Calibri", color: "64748B", align: "center", margin: 0 });
  // Arrow between steps
  if (i < steps.length - 1) {
    s.addText("\u2192", { x: x + 2.2, y: 1.8, w: 0.2, h: 0.5, fontSize: 18, color: "14B8A6", bold: true, align: "center", valign: "middle", margin: 0 });
  }
});
```

### Two-Panel with Colored Sidebar

```javascript
let s = pres.addSlide();
s.background = { color: "F8FAFB" };

// Left panel (white card)
const shadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });
s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.9, w: 4.4, h: 3.0, fill: { color: "FFFFFF" }, shadow: shadow() });
s.addText("Left Panel Title", { x: 0.7, y: 0.95, w: 4.0, h: 0.3, fontSize: 13, fontFace: "Trebuchet MS", color: "042F2E", bold: true, margin: 0 });
s.addText("Paragraph content here...", { x: 0.7, y: 1.3, w: 4.0, h: 2.4, fontSize: 9, fontFace: "Calibri", color: "64748B", margin: 0 });

// Right panel (colored background with accent bar)
s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 0.9, w: 4.5, h: 3.0, fill: { color: "F0FDFA" }, shadow: shadow() });
s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 0.9, w: 0.06, h: 3.0, fill: { color: "065A60" } });
s.addText("Right Panel Title", { x: 5.4, y: 0.95, w: 4.0, h: 0.3, fontSize: 13, fontFace: "Trebuchet MS", color: "042F2E", bold: true, margin: 0 });
```

### Scope / Phase Timeline

```javascript
let s = pres.addSlide();
s.background = { color: "042F2E" };  // Full dark slide

const phases = [
  { phase: "Phase 1", title: "Discovery", time: "2-3 months", items: ["Item 1", "Item 2", "Item 3"] },
  { phase: "Phase 2", title: "Design", time: "3-4 months", items: ["Item 1", "Item 2", "Item 3"] },
  { phase: "Phase 3", title: "Build", time: "4-6 months", items: ["Item 1", "Item 2", "Item 3"] },
  { phase: "Phase 4", title: "Launch", time: "2-3 months", items: ["Item 1", "Item 2", "Item 3"] },
];
phases.forEach((ph, i) => {
  const x = 0.35 + i * 2.4;
  s.addShape(pres.shapes.RECTANGLE, { x, y: 0.9, w: 2.2, h: 3.5, fill: { color: "0A2F2D" } });
  // Phase header bar
  s.addShape(pres.shapes.RECTANGLE, { x, y: 0.9, w: 2.2, h: 0.28, fill: { color: "14B8A6" } });
  s.addText(ph.phase, { x, y: 0.9, w: 2.2, h: 0.28, fontSize: 10, fontFace: "Calibri", color: "042F2E", bold: true, align: "center", valign: "middle", margin: 0 });
  s.addText(ph.title, { x: x + 0.1, y: 1.25, w: 2.0, h: 0.3, fontSize: 13, fontFace: "Calibri", color: "FFFFFF", bold: true, margin: 0 });
  s.addText(ph.time, { x: x + 0.1, y: 1.55, w: 2.0, h: 0.2, fontSize: 9, fontFace: "Calibri", color: "14B8A6", margin: 0 });
  ph.items.forEach((item, j) => {
    s.addText("\u2022 " + item, { x: x + 0.15, y: 1.85 + j * 0.3, w: 1.9, h: 0.28, fontSize: 8.5, fontFace: "Calibri", color: "E2E8F0", margin: 0 });
  });
  if (i < phases.length - 1) {
    s.addText("\u2192", { x: x + 2.2, y: 2.3, w: 0.2, h: 0.5, fontSize: 18, color: "14B8A6", bold: true, align: "center", valign: "middle", margin: 0 });
  }
});
```

---

## Reading Existing PPTX Files

```bash
# Extract text content
pip install "markitdown[pptx]" --break-system-packages
python -m markitdown presentation.pptx
```

---

## Dependencies Checklist

- [ ] `npm install pptxgenjs` — slide generation
- [ ] `pip install "markitdown[pptx]"` — text extraction
- [ ] LibreOffice installed (`soffice` command available) — PDF conversion
- [ ] Poppler installed (`pdftoppm` command available) — PDF to images
- [ ] Optional: `npm install react-icons react react-dom sharp` — for icons

---

## Slide-by-Slide Design Checklist

Run through this checklist for EVERY slide before delivery:

### Visual Quality
- [ ] Does the slide have a clear visual hierarchy? (Can you tell what's most important at a glance?)
- [ ] Is there at least one visual element? (No text-only slides)
- [ ] Is there enough whitespace? (15-20% of slide should be empty)
- [ ] Are margins adequate? (0.5" minimum from slide edges)
- [ ] Is text readable? (Sufficient contrast against background)
- [ ] Are all similar elements the same size? (Cards, circles, fonts consistent)

### Color & Typography
- [ ] Are colors from the chosen palette? (No random colors)
- [ ] Is the accent color used sparingly? (Only on what needs attention)
- [ ] Is there dramatic size contrast? (Title 2-4× larger than body text)
- [ ] Is body text left-aligned? (Only center titles and short labels)
- [ ] Are fonts consistent? (Same header + body fonts across all slides)

### Layout & Structure
- [ ] Does this slide use a DIFFERENT layout from the previous slide?
- [ ] Is there a top accent line? (Thin colored bar for continuity)
- [ ] Is the one-message-per-slide rule followed?
- [ ] Would a dark summary bar at the bottom improve this slide?
- [ ] Are related items grouped with minimal gaps, unrelated items separated?

### Polish
- [ ] No overlapping elements?
- [ ] No text cut off or overflowing?
- [ ] All cards have consistent shadows?
- [ ] Color-coded labels/tags for categorized content?
- [ ] Number badges in circles for sequential items?

---

## Design Quality Tiers

**Tier 1 — Basic** (don't deliver this):
White background, black text, bullet points, no visual elements.

**Tier 2 — Decent** (minimum acceptable):
Color palette applied, title/body hierarchy, some shapes/cards, but repetitive layouts.

**Tier 3 — Professional** (target this):
Bold color palette, varied layouts per slide, card-based designs with shadows and colored headers, dark bottom summary bars, number badges, accent lines, consistent visual motif, clear hierarchy.

**Tier 4 — Exceptional** (the Gamma standard):
Everything in Tier 3 plus: content-driven layout selection (each slide's layout matches its content type), color-coded categorization, recycle/connection callout bars, dramatic size contrast, breathing room everywhere, the presentation tells a visual story from start to finish.

**Always aim for Tier 3 minimum. Push for Tier 4 when the content allows it.**
