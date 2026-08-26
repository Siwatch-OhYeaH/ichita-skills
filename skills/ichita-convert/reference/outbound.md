# Outbound — rendering the record

Three targets, one source. The DOCX is for internal work and hand-editing, the
HTML is for Claude-designed layouts and is also the route to PDF, and the PDF
is what leaves the building.

---

## The language rule

**English-only → Aeonik (line box 1200). Any Thai → TH Aeonik (1537).**
Siwatch, 2026-08-05.

Both emitters decide from the source text and log the choice. They have to
agree, or one source produces a DOCX and a PDF that lay out differently:

```
md_to_docx.py   select_fonts_for_source()   ->  "font: TH Aeonik for both scripts, line box 1537"
emit_html.py    has_thai()                  ->  class="doc-th", --ichita-font: 'TH Aeonik'
```

Never mix the two faces in one document. They have different line boxes, so
the text reflows at the boundary.

The accepted cost: **English-only paragraphs inside a Thai document lead ~28%
wider.** Do not "fix" it — fixing it is what produced the 2026-08-04 defect.
`docs/THAI-LATIN-FONT-ENGINEERING.md` §1 has the argument.

`--font-mode unified|split` exists for the case where the answer is genuinely
a person's call. It is not for making a mixed document look tidier.

---

## md → docx

Wires `skills/ichita-docx/scripts/md_to_docx.py` in. Two changes were made to
it while building this skill, both because the round trip exposed a defect in
the document rather than in the conversion:

1. **Soft-wrapped source lines are one paragraph.** It used to emit one Word
   paragraph per source line, baking the author's 90-column wrapping in as
   hard paragraph breaks mid-sentence.
2. **List bullets are drawn in the brand font.** python-docx's template sets
   every bullet to U+F0B7 in `Symbol` — a Private Use Area codepoint that only
   means "bullet" if that exact font resolves. LibreOffice substitutes
   OpenSymbol and *embeds it*, so a delivered PDF carried a non-brand font for
   nothing but the bullets. Now U+2022 in TH Aeonik / Aeonik, which both have
   it.

Everything else about that generator, especially `select_fonts_for_source()`,
is untouched.

A `.ichita-convert.json` sidecar is written next to every DOCX. See
`reconcile.md`.

---

## md → html

`emit_html.py`, against `assets/brand/ichita.css`.

**There is no styling in `emit_html.py`.** The two hand-built executive briefs
each carried their own copy of the brand, both declared
`font-family: 'AeonikTH'` — a family that has never existed, verified against
the files with fontTools — and both rendered in a fallback font for months
because nothing pointed at a single source of truth. `ichita.css` is that
source now.

The stylesheet is **inlined by default**, with `url()` rewritten to absolute
paths. A relative `@font-face` src resolves against the stylesheet's location,
so an inlined copy in a file somewhere else silently points at nothing — and a
missing `@font-face` does not raise, it falls back. `--link-css` keeps the
file small if it will only ever be opened in place.

`ichita.css` carries **no generic fallback** in any font stack. A trailing
`sans-serif` is how off-brand output ships unnoticed: the page still renders,
so nobody looks. Missing glyphs should show as tofu.

The one exception is monospace, for `code` and `pre`. Aeonik has no
fixed-pitch cut, and misaligned code is worse than off-brand code.

### Page geometry

A converted document flows; the hand-designed briefs do not. `ichita.css` sets
`@page { margin: 0 }` for the fixed-layout case, where a `.page` div carries
its own geometry. `@page` cannot be scoped by class, so `emit_html.py` injects
the flowing variant — A4 with 18/16/16 mm margins and a page number in the
bottom-right margin box.

> The margin box needs its own `font-family`. It does not inherit from `body`,
> and without it weasyprint set the page number in FreeSerif and embedded an
> entire extra font into the PDF for one digit.

**A table breaks between rows, never inside one.** `@media print` used to say
`page-break-inside: avoid` on `.prose table`. A table taller than the page
cannot honour it, and weasyprint does not merely ignore the request — it pushes
the table onto a fresh page, leaves the gap behind, and breaks it mid-row
anyway, stranding one cell's text at the top of the next page with no row
number beside it. It reads as a dropped row. The rule now sits on `tr`, where
it is satisfiable; `thead` already repeats on its own.

> The fixture that proves this is the real 20-row table it was found in
> (`tests/fixtures/long-reference-table.md`). A synthetic table of the same
> height, row count and column count does not reproduce it — which is why the
> test carries 6 KB of citations instead of a generated one.

---

## md → pdf, and html → pdf

Chains `md → html → PDF`, reusing `skills/ichita-exe-brief/scripts/html2pdf.py`.

Keeping the HTML step separate and inspectable is deliberate: when a PDF comes
out wrong you open the intermediate in a browser and see whether the problem is
the content or the renderer. `--keep-intermediate` keeps it.

### The engine is chosen from the document

`html2pdf.py --engine auto` is the default:

```
the HTML builds its DOM with script  ->  chromium
the document contains Thai           ->  chromium
otherwise: static, English-only      ->  weasyprint
```

Both branches were measured — `pdf-delivery.md` has the numbers. Briefly:
weasyprint does not execute JavaScript, so it renders a Claude-designed
standalone HTML as its loading placeholder and **exits 0**; and its Thai text
layer is wrong even when the glyphs are right, so search and copy-paste return
nonsense from a page that looks perfect.

weasyprint stays the default for what it is good at. On static English-only
pages it embeds a real CID-CFF font program and produces roughly half the file
size. Chromium's Skia backend emits **Type 3** fonts instead — pure vector
CharProcs, fully scalable, no rasterisation, but not a reusable font program.
That trade is deliberate: a slightly awkward font container that extracts
correctly beats a clean one that corrupts the text. If a client demands
CID-CFF for a Thai document, the answer is the DOCX → LibreOffice route.

Force it with `--engine weasyprint|chromium` when you have a reason.

### Two things the Chromium path checks that weasyprint cannot

- **Which fonts were actually used.** Type 3 fonts carry no name, so a
  PDF-side brand-font check is impossible on that path. `html2pdf.py` asks
  Chromium directly (`CSS.getPlatformFontsForNode`), which is the better
  question anyway: it reports the font that was *used*, so an `@font-face`
  that silently failed to load shows up.
- **Content wider than the page.** A 1700 px diagram on A4 portrait loses its
  right-hand columns, silently, at exit 0. The overflow is measured and
  reported with both ways out.

  Two things about *how* it is measured, both of which were wrong first:

  **It runs after the print, against the page that was produced** — not
  against the page we asked for. `@page size`, `prefer_css_page_size`,
  `--width` and `--landscape` all move the real page, so the width is read
  back from the PDF.

  **Declaring `@page` is not a promise that the content fits.** The check used
  to skip any document with a `@page` rule, on the reasoning that the author
  had handled page geometry. `ichita.css` declares one and `emit_html.py`
  inlines it by default, so *every branded document exempted itself* — the
  check was inert exactly where the pipeline puts it. The page is now measured
  either way, and the document is re-laid-out at the printable width to ask
  it: comparing `scrollWidth` in the 1700 px design viewport against a page
  width would report every document as overflowing.

  The `@page` margin is resolved in three states — declared, absent, or
  unreadable — because a `<link>`ed `file://` stylesheet throws SecurityError
  on `cssRules`. Unknown is treated as a zero margin, which can only
  under-report clipping. Assuming our own 6 mm there invented 46 px of
  clipping in `designed.html` that does not exist.

---

## Brand tokens

`assets/brand/ichita.css` is generated from nothing — it is hand-maintained
against `assets/brand/ichita-defaults.md`, which is the reading of
`Ichita_Brand_Guidelines_V1.0.pdf`. Change values there first, then here.

| Token | Value | Role |
|---|---|---|
| `--ichita-blue` | `#2978FF` | **accent only** — never a page background |
| `--ichita-grey-01` | `#CFD9DB` | the canvas |
| `--ichita-grey-02` | `#788F9C` | muted text, captions, borders |
| `--ichita-grey-03` | `#263338` | primary text, dark backgrounds, logo default |
| `--ichita-blue-black` | `#171C21` | deepest anchor |
| `--ichita-alt-row` | `#F0F4F5` | table zebra, soft fill |

Hex here carries the `#`. The copies in `ichita-defaults.md` do not, because
those are PptxGenJS format.

Betatron is bound to `.stat-num.betatron` and nothing else. It is a display
numeral face — never body text, labels or sentences.

The white logo colourway is permitted on Blue Grey 03 and Blue Black only,
which in this stylesheet means inside `.header` and `.footer`.
