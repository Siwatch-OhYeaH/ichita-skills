# ICHITA — Design Specification

**Source of record:** *ICHITA Visual Identity Guidelines V1.0* — `uploads/Ichita_Brand_Guidelines_V1.0.pdf`, 41 pages, ©2022 ICHITA. All rights reserved.

This document converts that PDF, page by page, into the specification this design system
implements. The guidelines are the **main information**: where this system adds something
the PDF does not cover, it is marked **[EXTENSION]** and needs ICHITA sign-off. Where the
PDF contains an error, it is marked **[ERRATUM]** with the correction and the evidence.

Brand contact for identity questions (p.41): `wathaipan@srithepgroup.com`.

---

## 0. What the guidelines are

> "This document provides guidance on how best to use our visual identity. It details our
> core identity assets of logo, colour, typography, graphic devices, illustration and the
> ways in which these assets can be combined to create a cohesive but flexible brand
> system." — p.2

**The tool kit (p.3)** — the nine assets the identity is built from, in the order the PDF
lists them:

| # | Asset | Section | Implemented as |
|---|---|---|---|
| 01 | Wordmark | 1.2 | `IchitaLogo variant="wordmark"` |
| 02 | Symbol | 1.4 | `IchitaLogo variant="symbol"` |
| 03 | Colour | 2.0 | `tokens/colors.css` |
| 04 | Type | 3.0 | `tokens/fonts.css`, `tokens/typography.css` |
| 05 | Numerals | 3.3 | `SectionNumber` (Betatron) |
| 06 | Pattern | 4.0 | `tokens/patterns.css`, `BrandPattern` |
| 07 | Illustration | 5.0 — **TBC in the PDF** | `ProcessGlyph`, `ProcessFlow` **[EXTENSION]** |
| 08 | Photography (People) | 6.1 | `assets/imagery/` |
| 09 | Photography (Operational) | 6.1 | `assets/imagery/` |

The identity has **no UI layer**. Nothing in the 41 pages describes a button, a form, a
table or a chart. Every such component in this system is an extension.

---

## 1.0 Logo

### 1.1 Overview (p.5)

Two marks, one system.

- **Wordmark** — "our main identifier and will appear as a sign-off or endorsement on all
  of our communication to reinforce the authority of our brand."
- **Symbol** — "made up of arrow devices taken from the angle of the 'A' in our Wordmark
  and built around the concept of 'Process' & 'Innovation'. They act as a representation
  of the Ichita brand in its most reduced and simplified form."

**The symbol's usage rule is a constraint, not a preference:** it "can be used as an
endorsing mark or as a sign-off but should only be used when the Ichita context is already
evident." The symbol never introduces the brand — it signs off on something already
identified.

### 1.2 Wordmark (p.6)

> "This is your primary logo. To maintain it's integrity it should always appear in this
> fixed format and never be altered, redrawn or modified in any way."

Fixed format means: no re-typesetting in Aeonik, no re-tracing in SVG, no outline version,
no stretching, no re-spacing. **Always place the supplied file.** This system ships the
full approved set in `assets/logos/`; `IchitaLogo` places those files and nothing else.

### 1.3 Wordmark clearspace (p.7)

> "The 'clear zone' is the area that surrounds the logos… nothing should ever appear
> inside this area. It equals to **50% of the height of the word mark**."

`clearspace = 0.5 × wordmark height`, applied on all four sides. Scales with the mark —
it is a ratio, never a fixed pixel value.

### 1.4 Symbol (p.8)

> "This is our symbol. To maintain it's integrity it should always appear in this fixed
> format and never be altered, redrawn or modified in any way."

Same rule as the wordmark. **Never approximate the X-mark in SVG or CSS.**

### 1.5 Symbol clearspace (p.9)

> "It equals to **50% of the height of one arrow device**."

Note the difference from 1.3: the symbol's clearspace is measured against **one arrow**,
not the whole symbol — a tighter zone than the wordmark's.

### 1.6 Colourways (p.10)

> "The logo should only ever be used in these colourways. The Ichita logo uses **Blue Grey
> 03** across most colours. When the logo is placed over a **darker background colour use
> White**. The same rules apply to the Symbol."

| Background | Logo colour |
|---|---|
| White | Blue Grey 03 |
| Blue Grey 01 | Blue Grey 03 |
| Blue | Blue Grey 03 |
| Blue Grey 02 | Blue Grey 03 |
| Blue Grey 03 | White |
| Blue Black | White |

Two consequences worth stating plainly, because both are commonly got wrong:

1. **On Ichita Blue the logo is Blue Grey 03, not white.** Blue is not a "dark background".
2. There is no black logo, no single-colour blue logo, and no reversed-out-of-photo logo
   beyond these six cases. On imagery, place the logo on a solid colour band.

**Implemented:** `IchitaLogo` takes `on="white|greylight|blue|steel|dark|black"` and
resolves the colourway from this table; it cannot be given an arbitrary colour.

---

## 2.0 Colour

> "Colour is a vital component of our visual identity that drives brand attribution and
> awareness. Our colour palette is unified by a strong blue supported by a series of
> neutral colours." — p.11

### 2.1 Overview (p.12)

> "The vibrant **Ichita Blue accent** is one of our most recognizable colours. For the most
> part, the brand's backdrop is made up of the **White and harmonious range of lighter
> neutrals**. When combined with the **darker colours, which are used more sparingly**,
> this palette creates a dynamic and recognizable mix."

That sentence is the whole colour strategy and it sets the proportions:

- **Backdrop** — White and Blue Grey 01. The majority of every surface.
- **Accent** — Ichita Blue. One vibrant note, used for emphasis, never as the field.
- **Anchors** — Blue Grey 03 and Blue Black. Sparingly, for depth.

Seven colours listed on p.12, in the PDF's own order: White, Blue Light, Blue Grey 02,
Blue, Blue Grey 01, Blue Grey 03, Blue Black.

### 2.1 Primary colours (p.13)

> "These are our core colours that work across all communications. For ease and consistency
> these colour codes and values should be used at all times for both print and digital
> assets."

| Name | HEX | RGB | CMYK | PMS |
|---|---|---|---|---|
| White | `#FFFFFF` **[ERRATUM]** | 255 255 255 | 0 0 0 0 | — |
| Blue Light | `#82B0FF` | 130 176 255 | C51 M26 Y0 K0 | 2381 |
| Blue Grey 02 | `#788F9C` | 120 143 156 | C57 M36 Y31 K0 | 2544 C |
| Blue | `#2978FF` | 40 119 255 | C80 M56 Y0 K0 | 2132 |
| Blue Grey 01 | `#CFD9DB` | 207 217 219 | C18 M9 Y10 K0 | 427 C |
| Blue Grey 03 | `#263338` | 38 51 56 | C80 M64 Y58 K56 | 432 C |
| Blue Black | `#171C21` | 23 28 33 | C78 M69 Y61 K75 | Black 6 C |

> **[ERRATUM] — "White" on p.13.** The page gives White as `R19 G27 B55 / HEX 131A35 /
> C100 M78 Y12 K70 / PMS 289 C`. That is a dark navy, and the RGB values do not match the
> stated hex either (`#131A35` is R19 G26 B53). The swatch printed on p.12 is white, every
> application spread (pp.27–40) uses white paper and white type, and 1.6 requires a
> White logo on dark grounds — so the intended value is `#FFFFFF`. Recorded in
> `tokens/colors.css` as `--ich-white: #fff`, with the PDF's values retained in a comment.
> **Blue Light's RGB is also mistyped** on p.13 as `R130 G176 B55`; `#82B0FF` is
> R130 G176 **B255**. The hex is authoritative. All other values on p.13 are used as printed.

### 2.2 Contrast — the one place the palette needs help **[EXTENSION]**

The palette was specified for print and carries no accessibility guidance. Measured
against white: Ichita Blue **4.02:1**, Blue Grey 02 **3.38:1** — both below the 4.5:1 body-text
threshold. Only Blue Grey 03 (**13.02:1**) and Blue Black are safe for body copy.

The fix splits **fills** from **text** and leaves the brand untouched:

- **Fills, bars, chart series, patterns, graphics** — the seven brand colours exactly as
  specified above. The bar there is 3:1 and they clear it.
- **Text** — a darkened tint of the same hue: `--ich-blue-text #1A56C4` (6.64:1),
  `--ich-steel-text #4F6472` (6.18:1).

Blue Grey 02 remains valid for **uppercase eyebrows and labels at 12 px Medium or larger**
(`--text-muted-decorative`), where the 3:1 large-text bar applies. On dark grounds use
Blue Grey 01 (9.05:1) for muted text; never Blue Grey 02, which is 3.85:1 on Blue Grey 03.

Surface utilities (Off White `#F8FAFB`, Alt Row `#F0F4F5`, Rule `#A0B0B8`) are **[EXTENSION]**
from ICHITA's document tooling. They are never decorative and never brand colours.

### 2.4 Functional palette — branded, not borrowed **[EXTENSION — settled 4 Aug 2026]**

The system originally carried the stock Material triad — `#34A853` / `#E83E3E` / `#FFA000` —
three screaming, unrelated hues that made every ICHITA table look like a Google console.
They are replaced by four states drawn through slate: calmer, cooler, of a piece with Blue
Grey, and **each more legible than the colour it replaces**.

| Role | Tint | Core | Text | Light | Was |
|---|---|---|---|---|---|
| **Success** Process Green 169 | #DEF9EE | #2EA885 | #07765B | #6FD0AF | #34A853 |
| **Warning** Technical Amber 78 | #FEF0DA | #E6A100 | #855C01 | #E0B26A | #FFA000 |
| **Error** Oxide Red 25 | #FFEDEB | #D64545 | #A43E3C | #F7A099 | #E83E3E |
| **Attention** Signal Orange 45 | #FFEEE6 | #E87033 | #A14512 | #F3A582 | *new* |

Oxide Red measures **4.38:1** on white against the old 4.05; Technical Amber **2.22** against
2.04. **Attention is not a status** — it is the "look here" marker for callouts, timeline
milestones and action items. It sits 20° from Error, so it may never appear in the same
legend, table or status key as Error.

### 2.5 Secondary palette — four families, four hues **[EXTENSION — settled 4 Aug 2026]**

V1.0 specifies seven colours and no way to distinguish one subject from another; on a Blue
Grey page ICHITA's four technology families all come out the same colour. `tokens/secondary.css`
adds four category hues. They share **no hue** with the functional set, so a category can
never be read as a verdict.

| Hue | Tint | Light | Core (fill) | Text | Deep | Codes |
|---|---|---|---|---|---|---|
| Cyan 204 | #DDFAFD | #32C5D2 | #02919C | #01676F | #023D42 | Membrane · water treatment · brine recovery |
| Bronze 69 | #FCF0E5 | #C5AC93 | #8D7B68 | #6A5743 | #3F301F | Ion exchange · resin · equipment · raw material |
| Rose 350 | #FFECF4 | #E697BC | #CE6D9E | #973F6E | #59213E | Adsorbent · decolorization |
| Violet 292 | #F2F0FF | #B1A3F0 | #8370C7 | #6552A3 | #392C60 | Chromatography / SMB · Pilot Center · R&D |

**Core is a fill, text step is type.** Cores clear the 3:1 graphics bar; every hue has a
text step at 5.6:1 or better on white. Never set type in a core. This split replaces an
earlier proposal that pinned every core to one lightness — correct on paper, muddy and
unusable in practice.

**Subordination.** Ichita Blue is oklch chroma 0.215; no secondary exceeds 0.135, and
Bronze — the system's only warm neutral, every ICHITA grey being cool at hue 233 — is 0.036.

**Proportion — 85 / 15.** Primary neutrals and Ichita Blue hold ~85% of any layout;
everything else together stays under ~15%.

The **product stream** (liquid sugar, syrup, sweetener) has no colour of its own: it is the
output of all four families, so colouring it sets it competing with them. Ichita Blue or
Blue Grey. "Other / unclassified" is Blue Grey 02.

Each tint and deep is a ground (`cyan-tint` … `bronze-deep`); there is no mid-tone ground.
Not permitted on the cover, closing slide, letterhead or logo, in a status position, or as
ICHITA scope in a process flow.

### 2.3 Grounds — background and text are chosen together **[EXTENSION]**

A coloured block never gets a hand-picked text colour. It gets a `data-ground`
(`tokens/grounds.css`), which paints the field and rebinds `--text-primary`,
`--text-muted`, `--text-accent` and the border tokens for everything inside it:
`white` · `off-white` · `grey-01` · `steel` · `dark` · `darkest` · `accent`.

Light grounds (White, Off White, Blue Grey 01, Blue Grey 02) take **Blue Grey 03** type;
dark grounds (Blue Grey 03, Blue Black) take **White**. On Ichita Blue, white is 3.37:1 —
display type at 24 px+ Bold only, never body copy. On Blue Grey 02 there is no accent text
colour at all: emphasis is Blue Grey 03 Bold.

**Banned:** white on White, white on Blue Grey 01 (1.4:1), white on Blue Grey 02 (3.0:1),
Blue Grey 03 on Ichita Blue (2.5:1). `color:#fff` is legal only inside a `dark`, `darkest`
or `accent` ground.

---

## 3.0 Typography

> "Our typeface provides a distinct voice for the Ichita brand. The application of
> typography can scale from impactful through to functional depending on the content and
> communication requirement." — p.14

### 3.1 Overview (p.15)

> "Our primary font, **Aeonik**, is used across all communications. The typeface has a
> timeless and modern aesthetic and is a **structural workhorse** that was meticulously
> engineered. Flexibility is guaranteed with a range of weights. Ligatures, fractions,
> case-sensitive punctuation, symbols, forms, and arrows are among the features of Aeonik."

**Aeonik is used across all communications** — one face, not a pairing. Betatron (3.3) is
a numeral face, not a second text face.

### 3.2 Primary font (p.16)

> "Headlines, body copy, and supporting typographic detail are all taken into account
> thanks to the **three weights'** distinct functions and applications."

Three weights, three jobs — **Regular, Medium, Bold** — shown on pp.3 and 15 and specimened
on p.16 with full upper case, lower case and **123456789**.

| Weight | Job |
|---|---|
| Regular 400 | Body copy |
| Medium 500 | Supporting typographic detail — eyebrows, labels, captions, table headers |
| Bold 700 | Headlines, and **all data figures** (p.16 specimens Aeonik's numerals) |

**Applied in this system:** headings Bold, tracking −0.02em; body Regular, line-height 1.5;
eyebrows and labels Medium, uppercase, 0.14em tracking; data figures Aeonik Bold, tracking
−0.035em, `font-variant-numeric: tabular-nums`.

**Thai — not covered by the guidelines. [EXTENSION]** ICHITA produces bilingual Thai/English
documents; the PDF is English-only and names no Thai face. This system uses **TH Aeonik**,
ICHITA's in-house merge of Aeonik + Bai Jamjuree, as the single specified face — for Thai
and for Latin alike:

```css
font-family: "TH Aeonik", "Aeonik", "Bai Jamjuree", "Trebuchet MS", system-ui, sans-serif;
```

TH Aeonik carries **both scripts**, and its Latin is CoType's Aeonik byte for byte — measured
0.000% width difference against Aeonik Regular on the final build, so nothing reflows
horizontally when a Latin-only file moves onto it. The line box is one consistent **1.536 em**
across all ten weights (`hhea` and `sTypo` alike) against Aeonik's 1.200, so always set an
explicit line-height. Aeonik remains installed as a fallback for machines without TH Aeonik.
History of the fixed build defects in `README.md`. **TH Sarabun New and Slussen / TH Slussen
are retired** — they appear in older ICHITA files and are not part of this system.

**Document weight selection. [EXTENSION]** Settled 10 Aug 2026 on the final 22-face build,
superseding the 6 Aug face-selection rule. One family everywhere; what the document chooses
is its **default weight**, once per document, never per paragraph:

| The document contains | Default | Emphasis | Headings | Attribute | Word family |
|---|---|---|---|---|---|
| English only | **Regular 400** | SemiBold 600 | Bold 700 | `data-typeset="en"` | TH Aeonik |
| Thai, or Thai + English | **Book 350** | SemiBold 600 | SemiBold 600 | `data-typeset="mixed"` | TH Aeonik Book |

Book 350 is the bilingual default because Thai sets ~10% more ink per line than the Latin
beside it and its bold is capped at Bai Jamjuree Bold; Book takes ~11% of the ink out of the
Latin so the two scripts hold one page grey. SemiBold 600 is what Word itself gives Book on
Ctrl+B — the "Book Bold" 650 face carries the SemiBold outlines, measured identical.

**Audit of the final build. [EXTENSION]** 10 Aug 2026, all 22 files: vertical metrics agree
across `hhea`/`sTypo`/`usWin`, Thai marks carry zero advance, GPOS `mark`/`mkmk` are registered
under the `thai` script, `tnum` is present everywhere, `fsType` is 0. Three limits to design
around: **no NBSP** in the family (use a normal space inside `.ich-nowrap`), **Greek is
Δ Σ Ω μ π only**, and **Thai colour is capped above 700**. Full record in `fonts.md`.

**Ten weights. [EXTENSION]** Air 100 · Thin 200 · Light 300 · Book 350 · Regular 400 ·
Medium 500 · SemiBold 600 · Bold 700 · ExtraBold 800 · Black 900, each with an italic.
Declared for documents: 300–900. Air and Thin are held as assets only. Thai does not follow
the Latin above 700 — 800 and 900 are Latin display weights.

### 3.3 Numbers (p.17)

> "The display typeface **Betatron**, which represents a futuristic ideology, is used for
> our numerals. The **distinctly mechanical and industrial aesthetic** supports the notion
> that our engineering and technology company places innovation at the heart of its
> operations."

The page specimens `12345 67890` at display size, and p.39 shows the real use: the
case-study markers **01 02 03**.

**"Display typeface" is the operative constraint.** Read together with p.16 — which
specimens Aeonik's own `123456789` — the division is:

- **Betatron** — **the chapter or section divider numeral, and nothing else.** One large
  numeral opening a section: 48 px minimum, in practice 120 px and up. Never for words.
- **Aeonik Bold** — everything else, including every number the reader must read and
  compare: KPIs, table figures, measurements, percentages, prices, dates, agenda and list
  numbers, page numbers. Note p.40's own KPI, **"15-20%"**, is set in Aeonik, not Betatron.

**ICHITA has tightened this beyond the PDF:** Betatron is hard to read, so its use is
restricted to chapter markers. Agenda numbers and case-study list numbers — treated as
Betatron in earlier drafts — are Aeonik Bold, because a number the reader scans in a list
is information, not a graphic marker.

**Implemented:** `SectionNumber` is the only Betatron component; it clamps to a 48 px floor
and takes a bare chapter number.

---

## 4.0 Pattern

> "Our brand pattern options may be used to add versatility and interest. The designs draw
> inspiration from our process. These patterns may be used at a variety of scale, and
> colour within our brand palette." — p.18

### 4.1 Overview (p.19)

> "With the capacity to evolve and expand with the brand over time **through motion and
> 3D**, our pattern is built with a graphic language that can stay consistent and
> interesting across different applications.
>
> The pattern graphic is based on the concept of **"process"** and currently works in
> **four different ways**… A sense of **depth and dimension** is produced by these four
> styles. It conveys a sense of **movement and dynamism** and has a tangible feel to it."

The four styles, all built on the same idea — something diminishing, separating or being
reduced across the frame, which is *separation* rendered as graphics:

| # | Pattern | Construction | Class |
|---|---|---|---|
| 1 | Horizontal bars | Thick at the top, diminishing to hairlines | `.ich-pattern--h-bars` |
| 2 | Vertical bars | Grouped stripes of varying width | `.ich-pattern--v-bars` |
| 3 | Wide blocks | Bold to subtle | `.ich-pattern--blocks` |
| 4 | Dots | A grid diminishing top to bottom | `.ich-pattern--dots` |

**Colour rule:** shapes are always **Blue Grey 03**; the ground is **only Blue Grey 01 or
Ichita Blue**. This is the reading of "colour within our brand palette" that matches every
application spread in the PDF, and it is enforced in `tokens/patterns.css`.

### 4.1 Usage (p.20)

The page shows the pattern in application under the line **"Separation Technologies"** —
the pattern occupying the upper field with the type sitting below it, which is the layout
formula this system standardises:

- Pattern fills the **top 40–60%** of the surface; breathing room below; wordmark or a
  short line of text at the bottom.
- **Never mix two pattern types** on one layout.
- **Never rotate** a pattern.
- Scale is free ("a variety of scale") — density is the variable, not colour or angle.

Motion: the PDF explicitly anticipates it ("evolve… through motion and 3D"), so pattern
bands may animate their **scale**, slowly. UI chrome does not animate.

---

## 5.0 Illustration — **TBC in the source**

> "The technical illustration section provides specific guidelines and standards for
> creating technical illustrations, such as **diagrams, charts, and graphs**, that are used
> to represent or explain the Ichita product, process and services." — p.21, marked **TBC**

> "This section is important because it ensures that all technical illustrations created
> are **consistent in terms of style, formatting, and content**, which improves the clarity
> and effectiveness of the illustrations." — p.22, marked **TBC**

Both pages state the requirement and leave it unfilled. **This is the single largest gap in
V1.0**, and it is the gap that matters most for an OEM whose deliverables are pilot reports
and process proposals. This system fills it **[EXTENSION]** — new work, needing sign-off.

### 5.1 Process glyphs **[EXTENSION]**

`ProcessGlyph` — **28 unit operations** as flat schematic line drawings: vessel, IX column,
carbon column, sand filter, RO skid, UF and NF modules, pump, dosing pump, blower, heat
exchanger, plate exchanger, leaf filter, filter press, clarifier, evaporator, tank, silo,
mixer, degasser, cooling tower, valve, control valve, check valve, flowmeter, instrument
bubble, CIP skid, resin trap. (p.37 of the PDF already labels "Leaf Filter" and "Reactor"
in an application mock-up — the vocabulary is ICHITA's, the drawing is ours.)

One hand throughout: a **64×64 box, 6 px inset, uniform 2.5 stroke, square caps, miter
joins, Blue Grey 03, no fills, no perspective.** Simplified schematics — never P&ID detail.

### 5.2 Process flow **[EXTENSION]**

`ProcessFlow` assembles glyphs into a train with labelled stream arrows. **ICHITA's own
scope is marked in Ichita Blue** (`scope: "ichita"`); third-party scope stays Blue Grey 03.
That one distinction is what makes an ICHITA diagram legible to a client. Six steps maximum
per row; split into named stages rather than crowding a line.

Use equipment glyphs, not labelled rectangles — boxes-and-arrows reads as a consultant's
slide, equipment glyphs read as an equipment maker's.

### 5.3 Charts **[EXTENSION]**

p.40 lists "● Infographic ● Data visualisation" as deliverables without specifying them.
The chart language here is deliberately plain: a 2 px Blue Grey 03 baseline, `#DFE6E8`
gridlines, no plot fill, no border, no chart junk, unit printed above the y-axis rather than
repeated in every label, spec/target limits as dashed `--chart-target` lines labelled at the
right. Built with the `Chart` component — never hand-rolled from divs.

Two palettes, not interchangeable:

- **Categorical** `--chart-1…7` for unrelated series — Ichita Blue → amber `#F08C00` → Blue
  Grey 03 → Blue Light → violet `#7A5AF8` → teal `#00857A` → Blue Grey 02. Built on the
  blue/amber axis, which survives deuteranopia, protanopia and greyscale printing.
- **Sequential** `--chart-seq-1…5` for one variable's intensity — a light-to-dark blue ramp.

**Semantic red and green are excluded from the categorical sequence on purpose:** in a
technical chart red means off-spec and green means within spec, so using them as "series 5"
tells the reader something false. Seven series is the hard maximum.

### 5.4 Icons **[EXTENSION]**

The guidelines define no icon set — the tool kit on p.3 stops at photography. `Icon`
provides **36 UI glyphs on a 24 box**, drawn in the same hand as `ProcessGlyph`: **1.75
stroke, square caps, miter joins, no rounded corners, no fills**, inheriting `currentColor`.
Never below 1.5 stroke. 16 px in buttons, 20 px in body text, 24 px standalone.

**No emoji, no unicode dingbats, no icon font, and no third-party set** (Lucide, Feather,
Material). Bullets are plain discs. The X-mark symbol is not an icon — it is the logo, and
1.1's context rule governs it.

---

## 6.0 Photography

> "Our photography focuses around the use of **two defined image types, People and
> Operational**, with each reflecting different aspects of the Ichita offering, process and
> values." — p.23

### 6.1 People (p.24)

> "Our people images help position us as company that focuses our customers, our work force
> and the close relationship between them. We want to communicate and emphasis that we're
> **personal, relatable, and reliable, as well as assertive and confident** in our industry."

Engineers in blue cleanroom suits, operators at control panels, technicians with face
shields. Natural light, candid, working — never posed to camera.

### 6.1 Operational (p.25)

> "Our operational imagery helps communicates and contextualize the **scale** of the Ichita
> process. **Wider shots show the factory**, while **more detailed close up shots visualize
> our attention to detail and expertise**."

The wide/close pairing is the instruction: a facility shot establishes scale, a close-up
(beaker of clear water, resin in a gloved hand, an instrument reading, stainless piping)
proves the detail. Use them together.

**Treatment.** Cool and clean — blues from uniforms and equipment, greys from stainless,
clear water. No warm filters, no grain, no oversaturation, no generic stock. Images are
full-bleed or in a hard-edged rectangle; **never rounded, never with a drop shadow**, and
never with a protection gradient — type over imagery sits on a solid colour band.

---

## 7.0 Identity applied (pp.26–40)

> "The following pages demonstrate how our visual identity assets when applied correctly can
> flex across various applications creating a cohesive visual identity." — p.26

Fifteen application spreads. What they establish, as rules:

- **Covers and title pages** carry a headline with **one word emphasised**, the wordmark,
  and a pattern or photograph — e.g. "Liquid **Separation** Technologies" (pp.37, 40),
  "Separation Technologies" over pattern (pp.20, 34), "Minimize wastewater from decoloring
  resin with brine recovery technology" with `V1.0` and the URL (p.38).
- **Keyword emphasis is the brand's one rhetorical device.** Exactly one word in Ichita
  Blue; the rest Blue Grey 03 or White. Once per surface, never twice.
- **Case studies are numbered** — `01 02 03` against "Case Study:" labels and
  short outcome lines (p.39): "Ecosorb helping refinery to increase yield", "Capture market
  demand with Liquid Sugar".
- **Section/topic words stack** — "Sweetner Development", "Liquid Sugar Development",
  "Water Treatment", "Brine recovery system" (p.39): short noun phrases, sentence case.
- **The boilerplate is fixed** (pp.37, 40): "Ichita is an original equipment manufacturer
  company and experts in all separation technologies. We are the water treatment and process
  solution provider Company. Our services are as follows:"
- **The URL is the sign-off** — repeated at the foot of each application (p.37). The PDF
  prints `Ichitaglobal.com`; **the live and current URL is `www.ichita.co.th`** and it is
  what every surface must carry. **[ERRATUM — superseded by ICHITA]**
- **KPI treatment** (p.40): a short label above a large figure — "Efficiency gains" /
  **"15-20%"** — set in Aeonik, hyphenated range, unit attached. This is the pattern every
  `StatCard` follows.
- **Type is left-aligned and generous.** Composure comes from empty space, not ornament.

### Layout constants derived from the spreads **[EXTENSION where numeric]**

The PDF shows proportions, not measurements; these are this system's fixed values.

- **4 px base step** for all spacing.
- **A4 documents** — 2 cm margins on all four sides; wordmark + reference in the header
  above a **6 pt Ichita Blue rule**; page number bottom-right.
- **Slides** — 1280×720 with a 64 px margin. Wordmark bottom-left on covers, top-right on
  KPI slides. **Slide type floor [EXTENSION]:** title 36 px (32 px absolute minimum),
  sub-title 26–28 px, body and table cells 24–26 px, captions and footers 17–18 px.
  Content that will not fit at those sizes gets cut or split, never shrunk.
- **Square corners.** ICHITA is print-first: radius 2 px on interactive controls so they
  don't look unfinished, 18 px only on the master content-frame device, nothing else. No
  pills, no 12 px card radii.
- **Borders carry hierarchy** — 1 px `#A0B0B8` hairlines in tables, a 2 px rule between
  sections, a **4 px Ichita Blue left bar** on document H1/H2 and across the top of an
  accented card, a **6 pt Ichita Blue band** under the document header and along the top
  edge of a cover slide, an 18 pt blue left border on a blockquote.
- **Shadows are almost absent.** Cards are flat; depth comes from colour (Off White or Blue
  Grey 01 on White), not elevation. `--shadow-card` / `--shadow-raised` exist for genuine
  overlays only. Transparency and blur are not part of the language — the single exception
  is the focus ring `rgba(41,120,255,.28)`.

---

## 8. Voice **[EXTENSION, drawn from the PDF's own copy]**

The guidelines never state a tone of voice, but they demonstrate one across pp.5–40.

- **Declarative and quantified.** State what was done, under what conditions, and what
  resulted. p.40's "Efficiency gains 15-20%" is the model: a claim is a figure.
- **Person.** Third person and impersonal for technical material; first-person plural
  ("our", "we") only in brand and corporate statements, exactly as the PDF uses it ("Our
  colour palette is unified by a strong blue"); second person only in instructional
  documents like the guidelines themselves.
- **Casing.** Sentence case for headings and titles. UPPERCASE at 0.14em tracking for
  eyebrows, labels, table headers and captions — never for headlines. The wordmark is the
  only place ICHITA is set as an all-caps word.
- **Bilingual.** Thai leads, English follows, in the same field: "ตารางที่ 1. ขั้นตอนการฟื้นฟู /
  Table 1. Regeneration sequence". Switch at the clause or caption, never mid-sentence.
- **One takeaway per surface.** A single insight bar or blockquote closes a slide or a
  report section.
- **Length.** Slide titles ≤ 50 characters, card headings ≤ 30, stat labels ≤ 20; body
  paragraphs of 2–4 sentences; bullets of one line, four to six per list.
- **No emoji, no exclamation marks, no "revolutionary" / "cutting-edge" /
  "game-changing".** Technical nouns are allowed to be technical — regeneration, space
  velocity, decolorisation. The audience is process engineers.

---

## 9. Interaction and motion **[EXTENSION — nothing in the PDF covers screens]**

**Motion.** 120 ms for control state changes, 180 ms for component transitions, 320 ms
maximum for anything larger, all on `cubic-bezier(.2,0,.2,1)`. Fades and short translations
only — no bounce, no spring, no parallax. Consistent with p.19's "motion and 3D" note for
patterns, which may animate their scale slowly; UI chrome should not.

**States.**

| State | Behaviour |
|---|---|
| Hover | Primary button `#2978FF → #1F63DB`; secondary inverts to Blue Grey 03 fill, white text; ghost picks up a 10% blue wash; links Ichita Blue → Blue Grey 03 |
| Press | 1 px downward nudge plus `#1A55BF`. No scale change |
| Focus | 2 px Ichita Blue outline at 2 px offset, or the soft blue ring on fields |
| Disabled | 40% opacity, `not-allowed` cursor. No greying of the fill |

---

## 10. Page index

| Page | Section | Content |
|---|---|---|
| 1 | — | Cover — Brand Identity Guidelines V1.0 |
| 2 | — | Introduction |
| 3 | — | Tool kit — the nine assets |
| 4 | 1.0 | Logo — divider |
| 5 | 1.1 | Overview — wordmark and symbol, the 'A'-angle arrow devices |
| 6 | 1.2 | Wordmark — fixed format, never altered |
| 7 | 1.3 | Clearspace — 50% of wordmark height |
| 8 | 1.4 | Symbol — fixed format, never altered |
| 9 | 1.5 | Clearspace — 50% of one arrow device |
| 10 | 1.6 | Colourways — Blue Grey 03 on most, White on dark |
| 11 | 2.0 | Colour — divider |
| 12 | 2.1 | Overview — seven colours, accent + neutrals |
| 13 | 2.1 | Primary colours — HEX / RGB / CMYK / PMS **[ERRATUM: White, Blue Light RGB]** |
| 14 | 3.0 | Typography — divider |
| 15 | 3.1 | Overview — Aeonik, three weights |
| 16 | 3.2 | Primary font — Regular / Bold specimens with numerals |
| 17 | 3.3 | Numbers — Betatron, display use |
| 18 | 4.0 | Pattern — divider |
| 19 | 4.1 | Overview — four styles, "process", motion and 3D |
| 20 | 4.1 | Usage — pattern with "Separation Technologies" |
| 21 | 5.0 | Illustration — divider, **TBC** |
| 22 | 5.1 | Overview — **TBC** |
| 23 | 6.0 | Photography — divider, two image types |
| 24 | 6.1 | People |
| 25 | 6.1 | Operational |
| 26 | 7.0 | Identity applied — divider |
| 27–36 | 7.0 | Application spreads — stationery, collateral, pattern covers |
| 37 | 7.0 | Brochure/report spread — boilerplate, "Leaf Filter / Reactor", URL sign-off **[ERRATUM: use www.ichita.co.th]** |
| 38 | 7.0 | Report covers — "Minimize wastewater…", V1.0, URL |
| 39 | 7.0 | Case studies — Betatron 01/02/03, topic stacks |
| 40 | 7.0 | Presentation spread — "Liquid Separation Technologies", KPI "15-20%" |
| 41 | — | Contact — wathaipan@srithepgroup.com |

---

## 11. Open questions for ICHITA

1. **§5.0 Illustration is still TBC.** `ProcessGlyph`, `ProcessFlow`, `Chart` and `Icon`
   are this system's proposal for it and need review — ideally a designer pass on the glyph
   drawing before client-facing use.
2. **Confirm the p.13 White erratum** and reissue the page, and the Blue Light RGB typo.
3. **No Thai typography is specified** anywhere in V1.0, despite ICHITA's output being
   bilingual. TH Aeonik is the working answer; V1.1 should state it.
4. **TH Aeonik should be named in V1.1** as the bilingual face — ten weights as of the
   2026-08-09 final build, with Regular 400 the English default and Book 350 the bilingual one. The build defect that once
   forced a `unicode-range` workaround was fixed on 2026-08-05. The one open item is
   licensing: the merged **web** cut (woff2) is built but **held** pending CoType's written
   answer, so this system serves the desktop OTFs.
5. **Photography is the largest asset gap** — the direction on pp.24–25 is documented but
   supported by only two lab images here.
6. **No screen or product guidance exists.** Buttons, forms, tables and states in this
   system are reasonable extrapolation, not approved brand assets.
7. **Betatron licensing** for web deployment is unconfirmed. Aeonik / TH Aeonik are
   licensed from CoType (`uploads/CoType EULA WebFonts.pdf`); Bai Jamjuree is SIL OFL.
