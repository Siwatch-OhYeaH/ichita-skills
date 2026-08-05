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

---

## md → pdf

Chains `md → html → weasyprint`, reusing `skills/ichita-exe-brief/scripts/html2pdf.py`.

Keeping the HTML step separate and inspectable is deliberate: when a PDF comes
out wrong you open the intermediate in a browser and see whether the problem is
the content or the renderer. `--keep-intermediate` keeps it.

**This route is not automatically the right one for delivery.** weasyprint
gives full brand control and embeds only brand fonts, but it produces a PDF
whose Thai *text layer* is wrong — the glyphs render correctly and the
extracted text does not. Read `pdf-delivery.md` before sending a Thai PDF to a
client.

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
