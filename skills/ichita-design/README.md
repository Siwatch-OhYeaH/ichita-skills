# ICHITA Design System

**ICHITA Technology Co., Ltd.** is a Thai original-equipment manufacturer and process
engineering house specialising in **liquid separation technologies** — ion exchange,
membranes, adsorption and filtration for water treatment and industrial purification
(sugar refining, food and beverage, fine chemicals). ICHITA positions itself as a
"process design and engineering expert": it does not sell boxes, it designs the process
and then builds the equipment that runs it.

The brand promise is **Innovative. Professional. Precise.** Every visual decision traces
back to the idea of *process* — the X-mark symbol is two arrow devices lifted from the
angle of the "A" in the wordmark; the four brand patterns all show something diminishing,
separating or being reduced.

## Where the brand actually lives

ICHITA has no consumer product UI. Its brand surfaces are **documents and presentations**:
Thai/English technical reports, pilot-test reports, proposals, and PowerPoint decks. This
design system is therefore document- and deck-first, with a small set of screen primitives
so consuming projects can prototype web and dashboard views on-brand.

## Sources used to build this system

| Source | What it gave us |
|---|---|
| `uploads/Ichita_Brand_Guidelines_V1.0.pdf` — *ICHITA Visual Identity Guidelines V1.0*, ©2022, 41 pp | Logo system, clearspace, colourways, primary palette with CMYK/PMS, Aeonik + Betatron typography, the four patterns, illustration and photography direction |
| GitHub — **https://github.com/Siwatch-OhYeaH/ichita-skills** (private) | `assets/brand/ichita-defaults.md` (the operational brand spec), `assets/brand/docx-standard.md` (the A4 document standard), `skills/ichita-pptx/layout-patterns.json` (deck layout inventory), the logo set and font binaries |
| `uploads/ICHITA-Report_Template.docx` | A real bilingual pilot-test report — heading rhythm, table style, caption conventions, and two lab photographs |
| `uploads/ICHITA Company Profile 260624.pdf` · `ICHITA Company Profile_28Mar.pdf` · `Sugar derivatives opportunity - TSMC seminar v2.pdf` | Company facts, the full reference list, the pilot-centre inventory and the sugar-derivatives argument — written up in `company.md`. Also **49 real ICHITA photographs**, now in `assets/imagery/` |
| **13 real ICHITA presentations and reports** (`uploads/*.pptx`, `*.pdf`) — pilot results, proposals, technical training and webinar decks for SKT, UBE, SMS, TNCC, KSL, ThaiBev, KBS | The layouts ICHITA actually builds, and the drift this system exists to correct |
| `uploads/master_bg_image.png`, `uploads/slide_cover_image.jpg` | The master slide content frame and the dark cover artwork |
| `uploads/Ichita_Logo-01…11.png`, `ichita-logo.png`, `ichita-header-logo.png` | The full approved logo set (wordmark and symbol, five colourways each) |
| Font binaries — TH Aeonik (**22 otf**, ten weights + italics, final build 2026-08-09), Aeonik (8 otf, fallback), Betatron, Bai Jamjuree | Fonts shipped with this system |
| `uploads/CoType EULA WebFonts.pdf` | Aeonik's web licence — see Licensing below |

The GitHub repository is worth exploring directly if you have access — it contains the
PptxGenJS and python-docx generators that produce real ICHITA deliverables, and its
`ichita-defaults.md` is the single most complete written statement of the brand.

---

## CONTENT FUNDAMENTALS

**Voice: the engineer who has actually run the test.** ICHITA copy is declarative,
quantified and unhurried. It states what was done, under what conditions, and what
resulted. It does not sell in adjectives.

- **Person.** Third person and impersonal for technical material ("Colour removal held
  above 80% across all three service cycles"). First-person plural — "our", "we" — only
  in brand and corporate statements ("Our colour palette is unified by a strong blue").
  Second person ("you") appears only in instructional documents like these guidelines.
- **Casing.** Sentence case for headings and titles. UPPERCASE with wide letterspacing
  (0.14em) for eyebrows, topic labels, table headers and captions — never for headlines.
  The wordmark is the only place ICHITA is set in all caps as a word.
- **Numbers carry the argument.** Where a claim can be a figure, it is a figure, and the
  figure is set large in TH Aeonik Bold, tabular (`.ich-figure`): `80%`, `15-20%`, `2.4 BV/h`.
  Units stay in TH Aeonik beside the numeral; Betatron is only the chapter numeral (`02`). Ranges use an en-dash-style hyphen as in the source: `15-20%`.
- **Bilingual by default.** Thai leads, English follows, in the same field:
  "ตารางที่ 1. ขั้นตอนการฟื้นฟู / Table 1. Regeneration sequence". Never machine-mix
  inside a sentence — switch at the clause or the caption.
- **Keyword emphasis is the one rhetorical device.** In a headline, exactly one word is
  set in Ichita Blue while the rest stays Blue Grey 03 or White:
  "Liquid **Separation** Technologies". Use it once per slide, never twice.
- **One takeaway per surface.** Slides and report sections end with a single insight bar
  or blockquote: "Colour removal held above 80% across all three service cycles, with no
  brine wastewater generated during regeneration."
- **Length.** Slide titles ≤ 50 characters. Card headings ≤ 30. Stat labels ≤ 20. Body
  paragraphs of 2–4 sentences; bullets of one line each, four to six per list.
- **No emoji. Ever.** No exclamation marks. No "revolutionary", "cutting-edge",
  "game-changing". Technical nouns are allowed to be technical — "regeneration",
  "space velocity", "decolorisation" — the audience is process engineers.
- **Footer voice.** The website is `www.ichita.co.th` — the only URL used, on every surface, Thai and international alike. 9 pt, right-aligned, Blue Grey 02 on light or White on dark.

---

## NARRATIVE — how an ICHITA deck is built

The layouts are the vocabulary; this is the sentence. Derived from ICHITA's own
presentations. Two specimens: the *Overcome Challenges in Sugar Decolorization with
Ecosorb Technologies* webinar (44 pp, a product sell) and *Liquid Sugar &
Derivatives Technology* (57 pp, technical training). Specimen cards: **Deck narrative
arc**, **The carried diagram**, **The technical teaching deck**.

**The arc.** Not every deck uses all fifteen acts; the order never changes.

1. **Hook — a question.** One question over a full-bleed photograph, keywords in accent
   colour. No agenda, no logo wall. *"If fine liquor colour held at 100–150 IU all the
   time, what would the refinery gain?"*
2. **Answer it — benefits first.** The question repeated small at the top, then five lines
   of what the audience gains, marked in Success green. The subject is still unnamed.
3. **Topics.** A plain short list plus how long the session runs. A signpost, not a chapter.
4. **Common ground.** The standard process the room already runs, drawn end to end with the
   figure under each stage and the target outcome in green. Agreement before argument.
5. **Name the challenges.** Same diagram, and beside it the numbered list of what goes
   wrong — four is the working number. This list is a contract; act 12 answers it item for
   item.
6. **One slide per challenge.** Same diagram again, degraded figures in Error red at the
   failing stage, with the consequence spelled out: *yield decreases · higher operating cost*.
7. **Divider.** Dark full field, the section title as a spoken line. One before each major
   act — solution, technique, application, references.
8. **Credibility.** Parent group, manufacturing sites, certifications and compliance.
   Before the technical claim, never after it.
9. **What it is.** The product in two plain sentences with the media photographed.
   Composition and principle only.
10. **A benefit per slide.** *The headline is the benefit, not the feature* — "Improved
    filterability", "No carbon leakage" — with the mechanism diagram, photograph or curve
    as its evidence. A feature list alone reads as selling.
11. **Operating technique.** Numbered modes, each a schematic plus its dosing profile, the
    active mode in Attention orange; close with a three-up "which one for your case".
12. **Application — close the loop.** One case per challenge from act 5, in the same order,
    plus one they did not ask for. Same diagram, the change at a different position, before
    in red and after in green.
13. **References.** A real plant per slide: photograph, duty and capacity, the flow as
    built, an operating table reading before → after, and the payback line — *"benefit is
    2× cost, ~375,000 USD/year"*.
14. **Bookend.** Full-bleed plant photograph and the opening question turned on the
    audience: *"How would you like to improve your refinery?"*
15. **Thanks and Q&A.** Dark field, one line, the marks, then a quiet Q&A slide. No recap.

**The carried diagram.** Acts 4, 5, 6, 11 and 12 are *the same drawing*, changed in exactly
one place each time, with the figures underneath carrying the argument. Position, size and
glyph set are fixed for the whole deck. Annotation colour is the entire vocabulary:
**Blue Grey 03** baseline and third-party scope · **Ichita Blue** ICHITA scope · **Error
red** the problem and its cost · **Success green** the achieved figure · **Attention orange**
the mode or keyword in focus. Figures sit under the glyph they describe, TH Aeonik Bold
tabular, never in a legend. Two changes on one slide and the audience cannot tell which one
is the point.

**The teaching deck.** When the subject is a capability rather than a product, the same
skeleton takes five further moves. **The map grows** — one plant-wide flow map is shown,
then re-shown with the new branch grafted on, then a third time to close the section;
never redrawn. **Specifications travel with the streams** — the same five-line block
(colour · ash · brix · pH · invert) at both ends of the train, so before → after is read
off the drawing and not out of a table; the output block gains lines as the deck goes
deeper, the input block never changes. **Benefits accumulate** — consecutive slides on
one identical drawing, one check added per slide and nothing removed, with the money
derived on screen from figures already shown rather than asserted. **Analogy before
schematic** — the one mechanism the room cannot picture gets a plain-world analogy on its
own slide first; one per deck. **Motion by repetition** — a cycle is animated by
duplicating the slide and advancing one element per copy, which survives PDF and print.
Evidence is the unedited pilot table with its test dates, then a single line underneath
reading it against the spec. Comparisons run two symmetric columns and declare no winner.
A confidentiality mark sits on the slides carrying unpublished data, not on the deck.
Covers of a training deck carry the presenter's name and role. Close on the ask.

**Co-presentation.** A partner's mark may sit beside ICHITA's, as `ICHITA ✕ Partner`, on
the cover, dividers and closing slide when a deck is genuinely co-presented. On an
ICHITA-only deck it does not appear.

---

## VISUAL FOUNDATIONS

### Colour

Seven colours, and that is the whole brand. **White** and **Blue Grey 01 (#CFD9DB)** are
the dominant backdrop; **Ichita Blue (#2978FF)** is the single vibrant accent;
**Blue Grey 03 (#263338)** and **Blue Black (#171C21)** are anchors used sparingly for
depth; **Blue Light (#82B0FF)** is the secondary accent and **Blue Grey 02 (#788F9C)** the
utility grey for muted text and KPI grounds.

Approved background → text pairings are fixed: on White, Blue Grey 01, Blue and Blue Grey
02 the text and logo are Blue Grey 03; on Blue Grey 03 and Blue Black they are White. The
logo turns white in exactly one situation — a dark ground. No gradients, no tints outside
the seven, no colour introduced for decoration.

#### Grounds — never hand-pair a background and a text colour

The recurring failure in real ICHITA files is white type on a light field — white on
White, white on Blue Grey 01 — which is invisible. The system removes the chance to make
it: **any block that carries a background colour carries a `data-ground` instead.**

```html
<div data-ground="grey-01">…</div>   <!-- not background:#CFD9DB + a guessed text colour -->
```

Each ground paints its background *and* rebinds `--text-primary`, `--text-muted`,
`--text-accent` and the border tokens inside it, so children written against the semantic
tokens flip automatically.

| `data-ground` | Field | Primary text | Muted | Accent text |
|---|---|---|---|---|
| `white` | #FFFFFF | Blue Grey 03 | #4F6472 | #1A56C4 |
| `off-white` | #F8FAFB | Blue Grey 03 | #4F6472 | #1A56C4 |
| `grey-01` | #CFD9DB | Blue Grey 03 | #3F5360 | #1A56C4 |
| `steel` | #788F9C | Blue Grey 03 | Blue Grey 03 | none — emphasis is **Bold** |
| `dark` | #263338 | White | Blue Grey 01 | #82B0FF |
| `darkest` | #171C21 | White | Blue Grey 01 | #82B0FF |
| `accent` | #2978FF | White — **display only, 24 px+ Bold** | #E4EDFF | White |

**Banned, without exception:** white on White, white on Blue Grey 01 (1.4:1), white on
Blue Grey 02 (3.0:1), Blue Grey 03 on Ichita Blue (2.5:1), and body copy of any colour on
an Ichita Blue field. `color:#fff` is legal only inside a `dark`, `darkest` or `accent`
ground. See the **Grounds and pairings** card.

> **Note on the PDF.** Page 13 lists "White" as `#131A35` with PMS 289 C — a dark navy.
> This is an error in the printed guidelines; the White used everywhere in practice is
> `#FFFFFF`. All other CMYK/PMS values on that page are authoritative and are recorded in
> `tokens/colors.css`.

Functional colours (Success #2EA885, Warning #E6A100, Error #D64545, Attention #E87033) and surface
utilities (Off White #F8FAFB, Alt Row #F0F4F5, Rule #A0B0B8) come from ICHITA's document
tooling rather than the printed guidelines; they exist to make tables and status states
work and should never be used decoratively.

#### Functional and secondary palettes **[EXTENSION — settled 4 Aug 2026]**

Two sets, two jobs, **no shared hue**. Functional colour says what *state* something is in;
secondary colour says which *technology family* it belongs to. Confusing the two is what
makes a data slide unreadable, so they are built and named separately.

**Functional** replaced the stock Material triad (`#34A853`/`#E83E3E`/`#FFA000`) — three
screaming, unrelated hues that made every ICHITA table look like a Google console. The
replacements are drawn through slate and each is *more* legible than what it replaced.

| Role | Core | Text |
|---|---|---|
| **Success** Process Green 169 | #2EA885 | #07765B |
| **Warning** Technical Amber 78 | #E6A100 | #855C01 |
| **Error** Oxide Red 25 | #D64545 | #A43E3C |
| **Attention** Signal Orange 45 | #E87033 | #A14512 |

Attention is **not a status** — it is the "look here" marker for callouts and milestones,
and it may never sit in the same legend as Error.

**Secondary** codes the four technology families:

| Hue | Core (fill) | Text | Codes |
|---|---|---|---|
| **Cyan** 204 | #02919C | #01676F | Membrane · water treatment |
| **Bronze** 69 | #8D7B68 | #6A5743 | Ion exchange · resin · equipment |
| **Rose** 350 | #CE6D9E | #973F6E | Adsorbent · decolorization |
| **Violet** 292 | #8370C7 | #6552A3 | Chromatography / SMB · R&D |

**Core is a fill; the text step is type.** Cores clear the 3:1 graphics bar, text steps
5.6:1+ on white. Never set type in a core — that split is what makes the set usable.
Each hue carries `-tint` `-light` `-text` `-deep` and two grounds (`data-ground="cyan-tint"`
… `"bronze-deep"`); there is no mid-tone ground. Ichita Blue is chroma 0.215 and no
secondary exceeds 0.135, so the accent always wins the page. **85 / 15:** primary neutrals
and Ichita Blue hold ~85% of any layout.

**The palette is closed.** No additional blues (nothing within 40° of hue 262), no fourth
grey, no second red/green/orange, no hue outside these eight. See the single
**Secondary & functional palette — FINAL** card for the full specification, the fixed
mapping, the guardrails and the closed questions.

#### Accessible text colours — read this before setting any coloured type

The brand palette was drawn for print, and most of it **fails WCAG AA at body size**.
Measured against white: Ichita Blue **4.02:1**, Blue Grey 02 **3.38:1**, Success
**3.06:1**, Error **4.05:1**, Warning **2.04:1** — all below the 4.5:1 threshold. Only
Blue Grey 03 (13.02:1) and Blue Black are safe for body copy.

The fix keeps the brand intact by splitting fills from text. **Brand colours stay exactly
as they are for fills, bars, chart series and graphics**, where the bar is 3:1. For
**text**, use the darkened tint of the same hue:

| Role | Text token | Hex | On white |
|---|---|---|---|
| Accent, links, H3, primary button | `--ich-blue-text` | #1A56C4 | 6.64:1 |
| Muted text, captions | `--ich-steel-text` | #4F6472 | 6.18:1 |
| Success | `--ich-success-text` | #07765B | 5.60:1 |
| Error | `--ich-error-text` | #A43E3C | 6.30:1 |
| Warning | `--ich-warning-text` | #855C01 | 5.95:1 |

`--text-muted`, `--link` and `--action-bg` already point at these, so anything using the
semantic tokens is compliant by default. Blue Grey 02 survives as
`--text-muted-decorative` for **uppercase eyebrows and labels at 12px Medium or larger**,
where the large-text 3:1 bar applies. On dark grounds use Blue Grey 01 (9.05:1) for muted
text — never Blue Grey 02, which is only 3.85:1 on Blue Grey 03.

### Typography

**TH Aeonik is the only face.** TH Aeonik is ICHITA's merged Latin + Thai build of Aeonik:
one family, both scripts, every document. Settled 10 Aug 2026 on the final 22-face build.

```css
font-family: "TH Aeonik", "Aeonik", "Bai Jamjuree", "Trebuchet MS", system-ui, sans-serif;
```

- **TH Aeonik** — everything. Its Latin is CoType's Aeonik byte for byte.
- **Aeonik** — fallback only, for a machine without TH Aeonik installed. No document is set
  in it any more.
- **Bai Jamjuree** — split mode only, at 0.9×.

**The document does not choose a FACE any more. It chooses a WEIGHT.**

| The document contains | Default weight | Emphasis | Headings | Attribute |
|---|---|---|---|---|
| English only | **Regular 400** | SemiBold 600 | Bold 700 | `data-typeset="en"` |
| Thai, or Thai + English | **Book 350** | SemiBold 600 | SemiBold 600 | `data-typeset="mixed"` |

Book is the bilingual default because Thai carries about 10% more ink per line than the
Latin beside it and its bold is capped (Bold, ExtraBold and Black all take Bai Jamjuree
Bold). Book removes ~11% of the ink from the Latin, so the two scripts sit at one page
grey, and holding emphasis at SemiBold keeps the step readable in Thai without shouting.
600 is exactly what Word gives Book on **Ctrl+B** — its "Book Bold" 650 face carries the
SemiBold outlines, measured identical.

In Word and PowerPoint this is a family choice, because Windows splits the weights into
dropdown families the way it splits Arial: **TH Aeonik** (Regular + a real Bold) for
English, **TH Aeonik Book** for bilingual. Everything else is one plain face per family.

**Ten weights, all real outlines.** Air 100, Thin 200, Light 300, Book 350, Regular 400,
Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900, each with an italic — 22
files in `assets/fonts/`. This system **declares** 300–900; Air and Thin are held as assets
for backdrop / footage / poster work that has no rule set yet. Book, SemiBold and ExtraBold
are ICHITA interpolations of the Latin (CoType never drew them) and say so in their own
nameID5. Never synthesise a weight in CSS.

**Thai stops following the Latin above 700.** Bold, ExtraBold and Black all carry Bai
Jamjuree Bold at three embolden amounts: measured, they separate 2.3% in the Thai against
11% in the Latin, and at Black the Thai stem is 0.76 of the Latin where the text weights
hold 0.87–0.91. **800 and 900 are Latin display weights** — covers, statements, posters.
Do not set a Thai line in them beside Latin and expect a match.

**Thai sizing — same size as the Latin.** Inside TH Aeonik the Thai is matched to the Latin
x-height and weight-matched by measured stem, with Aeonik as the benchmark. Thai and Latin
sit at the **same font-size**; `--doc-thai-scale: 0.9` applies **only** in split mode.

**Leading is the one thing you must set by hand.** Measured on the final build, the
worst-case Thai stack (ปั๊ญฐฎ) occupies 1.315 em of ink at Regular and 1.350 em at Black;
Latin alone occupies 0.915 em. So marks begin to collide at **1.35**, the hard floor with
air in it is **1.40** (`--leading-thai-floor`), Thai headings run **1.55**
(`--leading-thai-tight`) and Thai body runs **1.75** (`--leading-thai`). The declared line
box is **1.536**, unchanged across all ten weights and written to `hhea` and `sTypo` alike:
in Word, Single already gives that 1.536 box (Multiple *m* = *m* × 1.536 em, so the 1.75 em
Thai body is Multiple 1.14); PowerPoint ignores the font and uses 1.2 em, so Thai there needs
Multiple 1.3 or more. Never "Exactly" below 1.536 × the size — it clips the tone marks. Never inherit `line-height: normal` — it
resolves to 1.536 where TH Aeonik is installed and 1.20 where it is not. `tokens/base.css`
applies the right leading to `:lang(th)` and `.ich-th` automatically, and deliberately does
**not** set `font-family` there.

**Figures.** `tnum` is present in all 22 faces and holds a digit at ~0.600 em in *every*
weight, so a figure column keeps its width when the weight changes. Any figure the reader
reads or compares is `.ich-figure` — Bold, `tabular-nums`, tracking −0.035em. Betatron is
the chapter numeral and nothing else.

**Embedding.** TH Aeonik is `fsType 0` — installable embedding, no restriction, so DOCX,
PPTX and PDF exports are safe. Betatron is `fsType 4` (preview & print only): an Office file
that embeds it opens read-only on a machine without the font, which is fine for a PDF export
and worth knowing before shipping an editable deck built on Betatron covers.

**Audited 10 Aug 2026 — what to design around.** Full record in `fonts.md` §5.

- **The family has no NBSP** — U+00A0 is absent, as are thin, figure and narrow spaces, ZWSP,
  soft hyphen and the non-breaking hyphen. A `&nbsp;` renders from a fallback font, so that one
  word space is a different width. Use a normal space inside `.ich-nowrap`. (True minus U+2212
  is present.)
- **Greek is Δ Σ Ω μ π only.** α β γ λ σ fall back mid-word — relevant to α-amylase, Δp and the
  like. The one gap worth closing in the next build.
- **Thai is complete**, 87/87 in all 22 faces, digits ๐–๙ and ฿ included. No Vietnamese.
- **SemiBold 600 and Book Bold 650 are the same file's outlines** — byte-identical, by design.
- **Every face reads `Version 1.000; build 2026-08-10`**, not bumped from the previous build,
  so Windows cannot tell them apart: **delete all installed TH-Aeonik files before installing**,
  and check `%LOCALAPPDATA%\Microsoft\Windows\Fonts` as well as `C:\Windows\Fonts`.
- **0.038 em of vertical slack.** Deepest rendered ink is 0.330 em (sara-u) against a declared
  0.368 em descent. Nothing clips today; do not tighten the box.
- **PowerPoint reaches Book by FAMILY, not weight** — a bilingual deck sets its theme fonts to
  *TH Aeonik Book*. And `font-weight: 350` is rounded by some PPTX/PDF conversion paths, so
  check a bilingual export once before relying on Book in a template.
- `body` now carries `font-synthesis: none`: a face that fails to load shows as the wrong weight
  instead of a faked bold.

> **History.** The first merged build (July 2026) rendered every Thai glyph 578 units too
> wide — CFF charstring widths written against Bai Jamjuree's `nominalWidthX` while the
> output Private DICT kept Aeonik's — and carried three disagreeing vertical-metric sets
> (`hhea` 1550/−561, `sTypo` 700/−200/300), which forced a `unicode-range` workaround.
> Both were fixed in the 2026-08-05 build; the 2026-08-09 final build added the six weights
> that had been filler faces. Zero-advance marks, GPOS `mark`/`mkmk` under the `thai` script
> and one consistent line box are all re-verified on the final files. **Do not reintroduce
> `unicode-range` scoping.**

### The document standard

The A4 style below is the standard for every ICHITA document. It is fixed — **the typeface
is fixed; the only variable is the default WEIGHT**, chosen by the table above. Specimen: the **Document standard** card
(`guidelines/type-document.card.html`); reference implementation: `templates/report/`.

| Element | Spec |
|---|---|
| Page | A4, **25 mm** margins all round |
| Header | Wordmark 38 mm wide over a 0.75 pt Ichita Blue rule, repeating on every page |
| Title | 26 pt Bold, centred, Blue Grey 03, over a 3 pt Ichita Blue rule |
| H1 | 15 pt Bold, Blue Grey 03, 3 pt Ichita Blue left bar, 6 pt inset — 34 pt above / 10 pt below, no rule above it (design.md §9.5) |
| H2 | 12 pt Bold, Ichita Blue text step #1A56C4 — 24 pt above / 8 pt below |
| H3 | 10.5 pt Bold Italic, Ichita Blue text step #1A56C4 — 18 pt above / 6 pt below |
| Body | 10 pt — **Regular 400** in an English file, **Book 350** in a bilingual one — Blue Grey 03, 8 pt after (the §9.5 rhythm ladder), line-height 1.5 (Thai 1.75) |
| Lists | 10 pt, indent 18 pt, hanging 9 pt |
| Table | 9 pt · header row Blue Grey 03 with white Bold type · banding #F0F4F5 · 0.5 pt #A0B0B8 hairlines · cell padding 2 pt / 5.4 pt |
| Caption | 9 pt Blue Grey 02, under the table |
| Callout | Off White field, 4 pt Ichita Blue left bar, 10 pt italic |

**Betatron is a display face, and that limits it sharply.** Guidelines 3.3 calls it "the
display typeface… used for our numerals", and its "distinctly mechanical and industrial
aesthetic" is the brand's signal that innovation is core. *Display* is the operative word:

- **Use it in exactly one place: the chapter or section divider numeral.** One large
  numeral opening a section — 48px minimum, in practice 120px and up.
- **Nothing else.** Not KPIs, not table figures, not measurements, percentages, prices,
  dates, agenda or list numbers, page numbers or references. Betatron is hard to read at
  working sizes and its digits are not easily distinguished at a glance.
- **Never** for words, labels or sentences.
- Agenda and case-study numbers are **TH Aeonik Bold** — they sit in a list the reader scans,
  which makes them information, not a chapter marker.

**Data figures are TH Aeonik Bold** with tracking −0.035em and `font-variant-numeric:
tabular-nums`. Aeonik's own numerals are specified in the guidelines (p.16) and are what
every KPI, stat and table figure in this system uses.

**Retired.** TH Sarabun New (still named as the Thai face in `ichita-defaults.md` and set
as the theme font in several existing decks) and Slussen / TH Slussen are **not** part of
this system. Replace them with TH Aeonik.

### Layout and space

A 4 px base step. A4 documents use 25 mm margins on all four sides; slides use a 64 px
margin on a 1280×720 frame. Layouts are left-aligned, gridded and generous — the brand's
composure comes from empty space, not from ornament. Fixed elements: the wordmark sits
bottom-left on covers and top-right on KPI slides; the 6 pt blue rule sits under every
document header; the page number sits bottom-right.

**Pattern layout formula:** pattern fills the top 40–60% of the surface, breathing room
below, wordmark or short line of text at the bottom. Never mix two pattern types on one
layout, never rotate a pattern, and only ever use Blue Grey 03 shapes on a Blue Grey 01 or
Blue ground.

### Data visualisation

Charts are built with the `Chart` component — never hand-rolled from divs. The chart
language is deliberately plain: a 2 px Blue Grey 03 baseline, #DFE6E8 gridlines, no plot
fill, no border, no chart junk, and the unit printed above the y-axis rather than repeated
in every label. Spec and target limits are dashed `--chart-target` lines with the value
labelled at the right, not annotated by hand.

**Two palettes, and they are not interchangeable.**

- **Categorical** (`--chart-1`…`--chart-7`) for unrelated series: Ichita Blue → amber
  #F08C00 → Blue Grey 03 → Blue Light → violet #7A5AF8 → teal #00857A → Blue Grey 02. Built
  on the blue/amber axis, which stays distinguishable under deuteranopia and protanopia,
  and separated by lightness as well as hue so it survives greyscale printing.
- **Sequential** (`--chart-seq-1`…`5`) for one variable's intensity — colour IU,
  concentration, load. A light-to-dark blue ramp.

**Semantic red and green are excluded from the categorical sequence on purpose.** In a
technical chart red means off-spec and green means within spec; using them as "series 5"
and "series 6" tells the reader something false. Seven series is the hard maximum — beyond
that, split the chart.

### Shape, borders and elevation

**Square corners.** ICHITA is a print-first brand and radius is close to zero: 2 px on
interactive controls so they don't look unfinished, 18 px only on the master content-frame
device, and nothing else. No pills, no 12 px card radii.

Borders carry the hierarchy: 1 px #A0B0B8 hairlines in tables, a 2 px rule between
sections, a **4 px Ichita Blue left bar** on document H1/H2 and across the top edge of an
accented card, and a **6 pt Ichita Blue band** under the document header and along the top
edge of a cover slide. An 18 pt blue left border marks a blockquote.

**Shadows are almost absent.** Cards are flat — depth comes from colour (Off White or Blue
Grey 01 on White), not elevation. `--shadow-card` and `--shadow-raised` exist for genuine
overlays (dialogs, menus) and nothing else. There are no protection gradients; text on
imagery sits on a solid colour band rather than a fade. Transparency and blur are not part
of the visual language — the one exception is the soft blue focus ring
(`rgba(41,120,255,.28)`).

### Motion

Restrained and functional. 120 ms for control state changes, 180 ms for component
transitions, 320 ms at most for anything larger, all on `cubic-bezier(.2,0,.2,1)`. Fades
and short translations only — no bounce, no spring, no parallax. The guidelines note the
pattern system "can evolve through motion and 3D", so pattern bands may animate their
scale slowly; UI chrome should not.

### Interaction states

- **Hover** — primary buttons darken (#2978FF → #1F63DB); secondary buttons invert to a
  Blue Grey 03 fill with white text; ghost buttons pick up a 10% blue wash; links move
  from Ichita Blue to Blue Grey 03.
- **Press** — 1 px downward nudge plus a further darkening (#1A55BF). No scale change.
- **Focus** — 2 px Ichita Blue outline at 2 px offset, or the soft blue ring on fields.
- **Disabled** — 40% opacity, `not-allowed` cursor. No greying-out of the fill colour.

### Imagery

Two defined image types. **People** — engineers in blue cleanroom suits, operators at
control panels, technicians with face shields; natural light, candid, never posed.
**Operational** — factory interiors, stainless piping, chromatography columns; and
close-ups of beakers of clear water, resin samples in gloved hands, instrument readings.

The colour vibe is **cool and clean**: blues from uniforms and equipment, greys from
stainless steel, clear water. No warm filters, no grain, no oversaturation, no generic
stock photography. Images are placed full-bleed or in a hard-edged rectangle — never
rounded, never with a drop shadow.

### Technical illustration

Marked "TBC" in the guidelines; this system defines it. `ProcessGlyph` provides **28 unit
operations** as flat schematic line drawings — vessel, IX column, carbon column, sand
filter, RO skid, UF and NF modules, pump, dosing pump, blower, heat exchanger, plate
exchanger, leaf filter, filter press, clarifier, evaporator, tank, silo, mixer, degasser,
cooling tower, valve, control valve, check valve, flowmeter, instrument bubble, CIP skid,
resin trap.

All are drawn in one hand: a 64×64 box with 6 px inset, uniform **2.5 stroke**, square
caps, miter joins, Blue Grey 03, no fills and no perspective. Simplified schematics — never
P&ID-level detail.

`StreamSpec` pins a stream's parameters (flow, conductivity, colour, TDS) beside the point
in the diagram where that stream exists — the same rows at both ends of a train, so before →
after is read off the drawing rather than out of a separate table. This is the single most
repeated device in ICHITA's own technical decks.

`ProcessFlow` assembles them into a process train with labelled stream arrows. **Mark
ICHITA's own scope in Ichita Blue** (`scope: "ichita"`) and leave third-party scope in
Blue Grey 03 — that single distinction is what makes an ICHITA diagram legible to a client.
Six steps maximum per row; split into named stages rather than crowding one line.

Use these instead of labelled rectangles in every diagram. A boxes-and-arrows flow reads as
a consultant's slide; equipment glyphs read as an equipment maker's.

---

## SCHEMATIC DRAWING **[EXTENSION]**

`ProcessFlow` draws one row in one direction. A real figure branches, recycles, carries
zones and has to be read from the back of a room. `components/schematics/` is the grammar
for those: **Figure** (the 1280×720 frame — heading, drawing, hairline legend strip),
**Zone** (a labelled plant area), **Unit** (a `ProcessGlyph` placed in figure coordinates
with its name and duty), **Block** (anything not physical — system, role, document,
decision, scope owner), **Connector** (an orthogonal line with r=8 quarter-arc bends and a
masked label), and four data-driven figures — **Sankey**, **Timeline**, **Matrix** and
**OrgChart**. **Geometry** carries the routing helpers: `port`, `ink`, `edge`, `fan`,
`elbow`, `route`.

The connector grammar is adapted from the editorial diagram discipline in
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) and re-set
in ICHITA type sizes, ICHITA scope colour and ICHITA's square-cornered geometry. Full
specimen: the **Schematic drawing** card, plus nine worked figures in the *Schematics* group.

**Six connector rules. Each one is an automatic fail.**

1. **Orthogonal only, r=8 quarter-arc bends.** A diagonal between nodes that share neither
   x nor y is a fail. `Connector` will not draw one.
2. **The label never sits on its stroke.** 6–10px of visible gap between the opaque mask
   and the line; 8px is the default.
3. **No overlapping runs.** Two connectors never share a path; parallel runs stay ≥12px
   apart end to end.
4. **Fan the attach points.** Several connectors on one edge each get their own point,
   ≥12px apart — `port(cell, side, clear, i, n)`.
5. **Never transit behind a node that is not an endpoint.** Reroute. Where a crossing is
   geometrically unavoidable the stroke is dashed and the label sits at the visible end.
6. **A label mask never lands under a node drawn later.** Nodes paint after labels, so the
   node fill clips the text. Draw connectors first, then zones, then nodes.

**Type on the frame.** Figure title 36, sub-title 26, node name 24–26/600, sublabel 20,
arrow label and legend and zone label 18/500 tracked 0.14em, quantity 20/700 tabular at
−0.035em. Nothing below 18px. If it will not fit, cut a node or split the figure — never
shrink the type.

**Budget.** Twelve nodes at full treatment; up to 24 only as chips inside 2–4 labelled
zones, and then only with an overview figure beside it. Sixteen connectors. **One**
secondary hue per canvas, and only where it encodes a technology family. Betatron never
appears in a figure.

**Colour does one job per figure.** Ichita Blue marks ICHITA scope; a secondary marks a
technology family; functional colour marks state. Never mix the vocabularies, never set
type in a core, and never colour the product stream.

---

## ICONOGRAPHY

Neither the brand guidelines nor the `ichita-skills` repository defines an icon set — the
guidelines cover logo, colour, type, numerals, pattern, illustration and photography and
stop there. This system therefore **draws one**, in the same hand as the process glyphs so
interface and diagrams share one construction.

`Icon` provides **36 UI glyphs** on a 24 box: arrows and chevrons, check, close, plus,
minus, search, download, upload, document, table, chart, mail, phone, location, calendar,
clock, user, settings, filter, external link, info, alert, warning, lock, globe, menu,
more, droplet, flask, gauge, print. **1.75 stroke, square caps, miter joins, no rounded
corners, no fills** — geometric rather than friendly, matching `ProcessGlyph`'s 2.5 stroke
optically at the smaller size. They inherit `currentColor`. Never go below 1.5 stroke.

Sizes: 16 px inside buttons, 20 px in body text, 24 px standalone. One size per context.

Alongside them the brand still uses:

- **The X-mark symbol** as an endorsing mark, sign-off or favicon — only where the ICHITA
  context is already established. Never approximate it in SVG; always use
  `assets/logos/ichita-symbol-*.png`.
- **Betatron numerals** as the chapter/section divider numeral — nothing else.
- **The four patterns** as texture and wayfinding.
- **`ProcessGlyph`** for anything depicting equipment.
- **No emoji, no unicode dingbats, no icon font.** Bullets are plain discs.

Do not add Lucide, Feather, Material or any other third-party set — `Icon` exists so the
system has one consistent hand.

---

## Index

### Root
| File | What it is |
|---|---|
| `styles.css` | Global entry point — `@import` list only. Link this one file. |
| `README.md` | This document. |
| `SKILL.md` | Agent-Skills front matter for use in Claude Code. |
| `github.md` | Upstream source association for `Siwatch-OhYeaH/ichita-skills`. |
| `company.md` | Company facts, references, pilot-centre capability and the sugar-derivatives narrative, from ICHITA's own profile and seminar decks. **The factual source for deck and proposal copy.** |
| `deck-audit.md` | Eleven real ICHITA decks measured — embedded fonts and fill colours read out of the PDFs — with the colour and type conversion maps, the engineering-seminar arc, and the recurring slide types. |
| `thumbnail.html` | Homepage tile. |

### `tokens/`
`fonts.css` (@font-face) · `colors.css` · `secondary.css` (the four category hues + their grounds) · `typography.css` · `spacing.css` · `shape.css` ·
`motion.css` · `patterns.css` (the four brand patterns as CSS classes) · `base.css`
(element defaults) · `grounds.css` (the `data-ground` background/text pairings).

### `assets/`
`logos/` — wordmark and symbol in all five approved colourways plus transparent versions ·
`brand/` — the master content frame and the dark cover artwork ·
`fonts/` — TH Aeonik (22 otf: ten weights + italics, final build 2026-08-09), Aeonik (8 otf, v1.001 desktop), Betatron, Bai Jamjuree ·
`imagery/` — **65 images**: 49 real ICHITA photographs extracted from the company profile and the TSMC seminar (reference installations, pilot centre, people, samples, corporate) plus the earlier generic set. See the **Photo library** card.

### Components
Grouped by concern under `components/`. Every component is a named export on
`window.ICHITADesignSystem_106280`.

| Group | Components |
|---|---|
| `components/brand/` | **IchitaLogo**, **BrandPattern**, **SectionNumber** |
| `components/core/` | **Button**, **Tag**, **Card**, **Divider**, **Callout** |
| `components/data/` | **StatCard**, **DataTable** |
| `components/charts/` | **Chart** |
| `components/diagrams/` | **ProcessGlyph**, **ProcessFlow**, **StreamSpec** |
| `components/schematics/` | **Figure**, **Zone**, **Unit**, **Block**, **Connector**, **Sankey**, **Timeline**, **Matrix**, **OrgChart**, **Geometry** |
| `components/icons/` | **Icon** |
| `components/forms/` | **Input**, **Select** |

**Intentional additions.** The sources define a document and presentation system, not a UI
library, so there is no upstream component inventory to mirror.

- **Direct translations of the sources** — `IchitaLogo`, `BrandPattern`, `SectionNumber`,
  `Card`, `Callout`, `StatCard`, `DataTable`, `Divider`.
- **Defined by this system where the guidelines say "TBC" or say nothing** —
  `ProcessGlyph` and `ProcessFlow` (illustration is marked TBC), the `components/schematics/`
  set — `Figure`, `Zone`, `Unit`, `Block`, `Connector`, `Sankey`, `Timeline`, `Matrix`,
  `OrgChart`, `Geometry` — `Icon` (no icon set exists), `Chart` (no chart language exists).
  These follow the brand's stroke, colour and
  geometry rules, but they are **new work and need ICHITA's sign-off**.
- **No counterpart in the source material at all** — `Button`, `Tag`, `Input`, `Select`,
  added so consuming projects can prototype interactive views. Reasonable extrapolation,
  not approved brand assets.

### `guidelines/`
Twenty-four foundation specimen cards (Colors, Type, Spacing, Brand) that render in the Design
System tab — including **Accessible text colours** (the contrast audit above as a table)
and **Bilingual layout** (the three sanctioned Thai/English patterns), and **Photo library**
(the 49 real photographs, sorted by the job they do).

Plus the *Schematics* group: **Schematic drawing** (the six connector rules, the node
vocabulary, the type ramp and the budget) and nine worked figures — branching process flow,
plant block diagram, mass balance, Sankey, scope, org chart, timeline, decision flowchart
and comparison matrix.

### `slides/` — the standard deck kit
Thirty layouts at 1280×720. These are the standardisation of what ICHITA already builds:
every one is derived from a real deck in `uploads/`, cleaned up to the palette, type and
spacing rules above.

`slides/ICHITA deck mockup.html` runs the first twenty-two as one navigable presentation
(`deck-stage.js`) — arrow-key nav, thumbnail rail, print-to-PDF. Use it to review the kit
end to end, or as the reference when checking a real deck against the standard.

| File | Layout | Use it for |
|---|---|---|
| `01-title.html` | Blue Grey 03 dark cover with keyword emphasis | **The cover.** Every deck opens on this |
| `07-agenda.html` | Numbered contents, TH Aeonik Bold 01–04 | Slide 2 of every deck |
| `02-divider.html` | Blue Grey 01 with oversized Betatron number | Between sections |
| `03-content.html` | Master frame, body + figure, insight bar | General content |
| `08-process-flow.html` | Equipment glyphs + stream arrows, blue = ICHITA scope | **The signature ICHITA slide** — every proposal has one |
| `09-data.html` | `Chart` with target line, stat column, insight | Pilot results, performance data |
| `10-comparison.html` | Current vs proposed, verdict bar | Proposals, technology selection |
| `04-kpi.html` | Blue Grey 02 ground, three Aeonik Bold figures | Headline numbers |
| `05-case-cover.html` | Pattern band, TH Aeonik Bold number, photo | Case studies |
| `06-closing.html` | Dark cover artwork with contact line | Last slide |
| `11-dense.html` | Two-column high-density technical layout | Appendices, design basis, spec dumps |
| `12-statement.html` | Blue Grey 03 field, one sentence, keyword in Ichita Blue | The position, the argument, a pivot moment |
| `13-image-full.html` | Full-bleed photograph, dark caption panel | Site references, chapter openers with imagery |
| `14-quote.html` | Blue Grey 01 ground, portrait + testimonial + three figures | Customer voice, references |
| `15-timeline.html` | Phase bars on a month grid, critical-path insight bar | Implementation schedules, project plans |
| `16-capability-grid.html` | Six cards with a 4 px blue top rule | Scope of services, product range, capabilities |
| `17-team.html` | Master frame, four greyscale portraits with role and responsibility | Project organisation, who is on the account |
| `18-photo-grid.html` | Three-up imagery with FIG. captions | As-built scope, equipment, site photography |
| `19-scope-commercial.html` | Line-item table + Blue Grey 01 investment panel | Proposals, quotations, the commercial slide |
| `20-risk.html` | Risk table with severity tags and owners | Proposals, project reviews, HAZOP summaries |
| `21-before-after.html` | Master frame, paired photographs with the measured delta | Pilot results, sample comparisons |
| `22-bilingual.html` | Thai leads, English follows in the same field | Any slide for a Thai operating audience |

**The technical-seminar eight.** Added from the `deck-audit.md` study of eight real
engineering decks — these are the slides ICHITA rebuilds from scratch every time.

| File | Layout | Use it for |
|---|---|---|
| `23-mass-balance.html` | Process train, four `StreamSpec` blocks, recovery figure | **The technical hero slide** — any water or brine balance |
| `24-cost-breakdown.html` | Operating-cost split bar, THB/day and THB/m³ | Cost of the problem, cost of the alternative |
| `25-investment-payback.html` | Saving derived on screen, then divided into the investment | The commercial close. Never a bare "ROI 3.3 years" |
| `26-option-matrix.html` | Priced options against two variables, one recommended | Proposals with a choice to make |
| `27-design-basis.html` | Train plus inlet-sampled and outlet-guaranteed tables | Proposals, TOR responses, design reviews |
| `28-method-rail.html` | Five-step method rail with step N active | A method explained over consecutive slides |
| `29-small-multiples.html` | Six trend panels, identical axes | Water-quality history, long-run monitoring |
| `30-reference-plants.html` | Four plants with photograph, duty and year | The credibility act |

**Deck type scale — the floor, on a 1280×720 frame**

Slides are read from across a room, not from a laptop. Nothing on a slide is set below
**18 px**, and running text never below **24 px**.

| Role | Size | Weight |
|---|---|---|
| Cover / statement headline | 60–76 px | Bold |
| Section divider title | 46–48 px | Bold |
| Slide title (topic) | **36 px** (32 px absolute floor) | Bold |
| Sub-title / deck under-line (subtopic) | **26–28 px** | Regular or Bold |
| Card and column heading | 28–30 px | Bold |
| Body, bullets, table cells, insight bar | **24–26 px** | Regular |
| Captions, footers, eyebrow labels, units | 17–18 px | Medium |

If the content does not fit at these sizes, **cut the content** — do not shrink the type.
A slide that needs 15 px body text is two slides.

**Deck rules**

*Master grammar — every framed content slide obeys this, no exceptions:*
- Frame: `assets/brand/ichita-content-frame.png` at full bleed.
- Title block: `left:340px; top:20px; right:64px`, centred. Title **34 px Bold**, tracking
  −0.022em, leading 1.15. Optional descriptive line under it: 25 px, `--ich-steel-text`.
- Content area: `left/right:88px`; `top:138px` with a title alone, `top:146px` with a
  descriptive line.
- Insight bar: `left/right:88px; bottom:96px`, Off White, 6 px Ichita Blue left border.
- Footer when there is no insight bar: `left/right:88px; bottom:52px`, 13 px muted,
  `www.ichita.co.th` right, 18 px.
- Full-field slides (cover, divider, KPI, statement, quote, case cover, closing, full-bleed
  image) sit on a 64 px margin with the footer at `bottom:34px`.
- The cover is **Blue Grey 03 dark** — white title, one keyword in Ichita Blue, 6 px blue
  band along the top edge. There is no blue-ground cover; Ichita Blue is an accent on the
  cover, not the field.
- Slide 2 is always the numbered agenda.
- Content slides use the master frame (`assets/brand/ichita-content-frame.png`); the title
  sits centred in the header band to the right of the logo, 36 px Bold.
- One insight bar per content slide, at the bottom, Off White with a 6 px blue left border.
- Process-flow boxes: white with a 2 px Blue Grey 03 outline for third-party scope, solid
  Ichita Blue for ICHITA scope, solid Blue Grey 03 for the finished product.
- Data figures are **TH Aeonik Bold**, not Betatron. Betatron appears **only** as the large
  section numeral on a divider slide — including on the agenda, whose numbers are TH Aeonik Bold.

### What the existing decks get wrong
Measured, not eyeballed — the full study with the conversion tables is `deck-audit.md`,
and the same tables render as the **Converting an existing deck** card.

- **No deck uses the brand typeface.** Aeonik and TH Aeonik appear zero times across eleven
  real decks; Calibri appears in all of them. Four different Thai faces are in circulation
  (TH Sarabun New, Angsana New, Browallia UPC, Calibri's Thai fallback).
- **Twenty-four distinct non-brand hexes**, against exactly one brand hex in the whole
  corpus — `#2978FF`, in *Derivative Production Technology*. Start conversions from that deck.
- **Wingdings and Symbol** supply the ✓ and ➢ glyphs in the proposal decks. Use `Icon`.

Also recorded:

- **Off-brand greys.** `#64748B` (Tailwind slate-500) appears throughout the SKT deck.
  Use **Blue Grey 02 `#788F9C`**.
- **Off-brand theme.** Several decks still carry the stock Office theme (`accent1 #4472C4`,
  `accent2 #ED7D31`, `dk1 #44546A`). Nothing should reference theme colours.
- **Mixed fonts.** Calibri, Aptos Narrow and TH Sarabun New appear alongside Aeonik in the
  same deck. One face: TH Aeonik.
- **Inconsistent covers.** Blue, dark and white covers are all in use across decks. The
  dark Blue Grey 03 cover is the standard; convert the others.
- **Betatron used for data.** Several decks set KPI figures and table numbers in Betatron,
  where it is hard to read. Betatron is a display face — **chapter dividers only**.

### `ui_kits/` — document kits
Every one is A4 with the standard header (wordmark + reference + 6 pt blue rule) and a
bottom-right page number. **They still sit at 20 mm margins and predate the document
standard above** — reissue them at 25 mm with the standard paragraph ladder when they are
next touched.

| Kit | What it is |
|---|---|
| `report/` | Two-page bilingual technical report — the reference implementation. See its README for the element-by-element spec. |
| `datasheet/` | One-page equipment specification sheet: min/nominal/max table, materials, regeneration sequence, performance figures, scope of supply. **The highest-value document for an OEM.** |
| `quotation/` | Bilingual commercial quotation — line items, VAT total, terms table, dual signature blocks. |
| `certificate/` | Test certificate with requirement/measured/result table and a conclusion panel. |
| `stationery/index.html` | A4 letterhead — first page with the 6 pt blue band and address block, continuation page with the symbol and a hairline rule. |
| `stationery/business-card.html` | Virtual (digital) business card for sharing by link or QR, plus the printed 91 × 55 mm faces. |
| `stationery/email-signature.html` | Outlook-safe table-based email signature — standard and short reply forms. |

### `office/` — Word and PowerPoint templates
`ICHITA-Presentation-Template.pptx` (one master, seven ICHITA layouts, each with a populated
sample slide) and `ICHITA-Report-Template.docx` (A4, repeating header, the full ICHITA paragraph
and table styles). Generated from the same tokens as everything else, so a document made in
Office matches one made in HTML. See `office/README.md`.

### `templates/`
Copy-and-edit starting points: `templates/deck/` (six-slide presentation),
`templates/report/` (A4 report page) and `templates/datasheet/` (one-page equipment
specification sheet). Each loads the system through its own `ds-base.js`, and each exposes
its variable content — deck title, client, reference number, contact address, section
numbering — as tweakable props rather than requiring edits to the markup.

---

## Licensing

**Aeonik and TH Aeonik are commercial fonts** licensed from CoType Foundry; the web
licence is `uploads/CoType EULA WebFonts.pdf`. Before deploying anything built with this
system to a public domain, confirm the licence covers that domain and its pageview
volume. **Bai Jamjuree is SIL OFL** and free to use and redistribute. **Betatron** is
licensed separately — check its terms before web deployment. Do not commit the Aeonik or
TH Aeonik binaries to a public repository.

## Gaps and open questions

- **Three component families are new work, not brand canon** — `ProcessGlyph`/
  `ProcessFlow`, `Icon` and `Chart` fill genuine holes in the guidelines (illustration is
  "TBC"; icons and charts are undefined). They need ICHITA sign-off before client-facing
  use, and ideally a designer pass on the glyph drawing.
- **No web or app product exists** in the supplied material, so no marketing-site or
  dashboard UI kit was built. Building one would mean inventing a design, which this
  system deliberately does not do.
- **Photography — largely closed.** 49 real ICHITA photographs (reference installations,
  the pilot centre, ICHITA people, syrup and media samples, headquarters and seminars) are
  now in `assets/imagery/`, extracted from the company profile and the TSMC seminar deck.
  What is still missing: high-resolution originals. Most are 300–700 px on the long edge,
  which is fine for a column or half-slide but thin for a full-bleed 1280 cover or an A4
  page. Ask for the camera originals.
- **The web licence for the merged TH Aeonik is unresolved.** A woff2 cut exists upstream
  but is marked *do not serve* pending CoType's written answer, and this system serves the
  desktop `.otf` files over the web — which is the same redistribution in a different
  container. This is a licensing decision, not a technical gap: get the answer in writing
  before anything ships publicly. `uploads/CoType EULA WebFonts.pdf` is the licence.
- **Fonts ship as `.otf`, not woff2** — correct while the web cut is held, but 5–8× heavier
  per face than woff2 would be. Once the licence clears, converting both families is the
  single biggest performance win available to this system.
- **`tokens/fonts.css` declares fourteen of the 22 faces** (Light 300 to Black 900; no
  italics above Bold). A style asking for Air 100 or Thin 200 gets a browser-synthesised weight — don't.
- **The 1.55 Thai leading floor is documented, not enforced.** `tokens/base.css` applies it
  to `:lang(th)`, `.ich-th` and `.th`, but any element rule with its own `line-height`
  outranks that hook and must restate it. This caused three separate regressions on
  6 Aug 2026. An adherence rule flagging a Thai-bearing selector below 1.54 would close it.
- **The `ui_kits/` documents predate the document standard** — 20 mm margins, their own
  heading sizes. `templates/report/` is the conforming reference; the kits need reissuing
  against it.
- **Partner logos, equipment photography and the PowerPoint/Word template binaries**
  referenced in `ichita-defaults.md` live in a separate "oracle" repository that was not
  attached.
