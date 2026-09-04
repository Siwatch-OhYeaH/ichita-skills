---
name: two-aeonik-cuts
description: "ICHITA holds two different Aeonik cuts — desktop v1.000 (box 1200, what Word uses and TH-Aeonik pins to) and web v2.000 WOFF (box 1140, different digit widths, adds Greek mu/Delta/Omega)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9a53e104-c414-4086-8afa-b77c1ac8fb8a
  modified: 2026-08-05T09:48:27.266Z
---

`assets/fonts/aeonik/` and `assets/fonts/aeonik-wolf/` are NOT the same font.
Measured 2026-08-05 ("wolf" is Siwatch's reading of WOFF, the web format):

                        desktop v1.000      web v2.000 (woff/woff2)
    hhea/sTypo/usWin    1000/-200/0 = 1200  930/-210/0 = 1140
    glyphs              656                 703
    faces               14 (Air..Black)     6 (Light/Regular/Bold + italics)

The Aeonik installed in Windows is **v1.000, box 1200** — so that is what Word
renders and what `build_th_aeonik.py` pins `LATIN_PITCH` to and asserts. The web
cut changes nothing about the TH build and must not be built from: wrong format,
6 faces short, and a 1140 box that would move every TH-Aeonik line box by -5%.

Outlines are mostly identical (`n o e g a A O M . ,` match to the unit) but v2
revises spacing: `x` 505->493, digit `1` 324->318, digit `5` 588->568. The two
cuts do not set numbers identically, which matters for spec tables, and if the
website serves the woff2 it leads 5.3% tighter than Word documents.

**v1 lacks the Greek-codepoint forms that ICHITA's technical writing hits.** v1
has µ U+00B5, ∆ U+2206, Ω U+2126 but NOT μ U+03BC, Δ U+0394, Ω U+03A9; v2 has
all six. They look identical, so a ΔP or μS/cm pasted from a lab report or Excel
carries the Greek codepoint, finds no glyph, and Word substitutes another font
mid-word — a silent brand break in the most technical documents we produce.

**CLOSED 2026-08-05 — the Greek gap is fixed, by harvesting.** Siwatch chose to
harvest the web cut's outlines rather than alias inside v1, and `scripts/th_greek.py`
now does it for both TH-Aeonik and Aeonik itself (`scripts/build_aeonik.py` →
`assets/fonts/aeonik-fixed/`, nameID5 `Version 1.001; ICHITA Greek/math coverage`).
Σ U+03A3 and ⌀ U+2300 are absent from *every* cut and are aliased to ∑ and Ø as
acknowledged shape compromises.

Measurement worth keeping: **in the web cut, `uni0394` is point-identical to
`uni2206`, and `uni03BC` to `uni00B5`** — CoType draws one glyph per pair, so the
Greek letter and the maths sign are the same shape by design. `uni03A9` and `uni2126`
genuinely differ (19 vs 32 segments) but render indistinguishably (ink within 0.4%).
Consequence: `∆` and `µ` now carry the v2 drawing in the harvested faces, so two
glyphs that already shipped changed appearance.

**Still true, and still the reason not to migrate wholesale:** the v2 box is 1140
against v1's 1200, and v2 respaces `x`, `1`, `5`, `S`, `3`, `4`, `8`, `@`, `€`. Only
the five missing codepoints were taken; every vertical metric and all Latin spacing
stayed v1, asserted by `build_aeonik.assert_untouched()`. Importing v2 spacing would
also split the family — it covers only 6 of the 14 faces.

Related: [[ichita-thai-latin-pairing-rule]], [[word-leads-off-uswin]],
[[font-follows-the-document-language]], [[averages-hide-broken-outlines]].
