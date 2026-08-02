# TH fonts — the line box was sized to contain ink it never needed to contain

**Date:** 2026-08-02 (evening)
**Branch:** `docs/ichita-proposal-design`
**Follows:** [`2026-08-02-th-font-thai-latin-harmonisation.md`](2026-08-02-th-font-thai-latin-harmonisation.md)

## Summary

The morning's fix for Thai mark clipping raised the merged fonts' `hhea` line box
until it contained the full mark stack — TH-Aeonik to 1710 units against Aeonik's
1200, TH-Slussen to 1870 against Slussen's 1512. That added 42% and 24% of leading
to every paragraph set in the merged faces, including pure-Latin ones. It was an
over-correction: **Word does not clip at `hhea` in body text, and no Thai font sizes
its line box to the mark stack.** Fixed by separating the two boxes — `hhea`/`sTypo`
now equal the Latin source's exactly, and `usWin` alone is sized to the ink. Found
by Siwatch's manual QC in Word (`QC fonts.pdf`).

## Symptom

Same English paragraph, same point size, single line spacing, in a Word document:

| block | font | line pitch @ 11 pt | em |
|---|---|---|---|
| control | Aeonik | 13.20 pt | 1.200 |
| test | TH-Aeonik | 18.75 pt | 1.710 |

The specimen's own text stated the acceptance criterion: *"…between Aeonik TH and the
original one which should be identical."* They were 42% apart.

## Root cause

`build_th_aeonik.py::set_vertical_metrics` and its Slussen twin held one box for all
three metric sets and asserted it contained the ink:

```python
ASCENT, DESCENT, LINEGAP = 1160, -550, 0
WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT

lo, hi = _ink_bounds(font)
if hi > ASCENT or lo < DESCENT:
    raise SystemExit("ink escapes the line box")
```

Two different quantities were being answered with one number:

- **`hhea` / `sTypo`** — how far apart consecutive baselines sit. Word leads off
  `hhea`; LibreOffice and browsers off `sTypo` when `USE_TYPO_METRICS` is on.
- **`usWin`** — the bound outside which GDI declines to draw.

The line box has no obligation to contain the ink. Thai above-vowels and tone marks
are drawn to overflow it into the leading of the line above, where Latin ascenders
leave the space empty. Measured on this machine:

| font | line box | worst shaped stack needs | overflow |
|---|---|---|---|
| Bai Jamjuree | 1250 | 1552 | 302 |
| Leelawadee UI | 1330 | — | — |
| Tahoma | 1207 | — | — |
| Leelawadee | 1196 | — | — |

Requiring containment forced the box to the tallest three-level stack in the family
(`อึ๋ม` at +1088, `ทุก` at −331) and dragged Latin-only text along with it.

## Why the morning's reasoning was wrong

The morning post-mortem argued: *"`usWin` was already 1250/570 and did contain the
ink, yet marks still clipped — so the clip is taken against `hhea`."*

The premise about the symptom was never verified against the artifact. `printpdf4.pdf`
is the build that section describes as clipping: `hhea` 1300, unscaled Thai with
shaped ink needing 1552, so 252 units outside the line box. Rendering page 2 at 200
dpi shows `น้ำเชื่อม`, `ทั้งนี้`, `ซึ่งระบุ`, `ประสิทธิภาพ` and `เกี๊ยะ`-class stacks
**all complete** — no clipped marks, and no collision with the line above.

So the clipping the manual QC warned about was not happening in body text at all. The
original report was phrased as a precaution — *"the top/bottom **may** get cut off, so
during font engineer you should put something to prevent this"* — and was read as an
observation of a present defect. Where clipping does bite is fixed-height table rows
and `w:lineRule="Exactly"`, both of which are document settings, not font metrics.

The other half of the morning's finding survives intact: Word does lead off `hhea`,
and `old_hhea/new_hhea` = 1.6238 against a measured pitch ratio of 1.6218 remains the
evidence for it.

## Why it produced the symptom

`hhea.ascender − hhea.descender + hhea.lineGap` is the single-spaced line pitch in
Word. 1710 vs Aeonik's 1200 is 1.425×, so at 11 pt: 18.81 predicted, 18.75 measured.
Every document set in TH-Aeonik gained 42% of leading against the same document set
in Aeonik — which is exactly the "layout I try to make go wrong" complaint, in the
opposite direction from the morning's 1300-unit build.

## Fix

Two boxes, two purposes.

**`scripts/build_th_aeonik.py`**

```python
ASCENT, DESCENT, LINEGAP = 1000, -200, 0        # == Aeonik-Regular.otf hhea
WIN_ASCENT, WIN_DESCENT = 1240, 560             # == measured ink + headroom
```

**`scripts/build_th_slussen.py`**

```python
ASCENT, DESCENT, LINEGAP = 1074, -272, 166      # == Slussen-Regular.otf hhea
WIN_ASCENT, WIN_DESCENT = 1390, 590
```

(The `usWin` figures include the extra room taken by the mark-clearance fix in the
addendum below; before it they were 1160/560 and 1310/590.)

`assert_line_box_matches_latin()` reads the Latin source's `hhea` before the merge and
fails the build if it disagrees with the constants, so a font update cannot drift the
two apart silently. The ink assertion in `set_vertical_metrics()` now tests `usWin`
instead of `hhea`.

This addresses the root cause rather than the symptom because the line box is no
longer derived from the ink at all — it is copied from the face being merged into,
which is the same ICHITA pairing rule already applied to size and stem weight.

**Clearance is strictly better than the build already proven safe.** Worst shaped
overflow is now 87 up / 131 down = 218 units, against `printpdf4.pdf`'s 252, which
renders clean.

## How it was found

The reproducer was `QC fonts.pdf` — a Word document with the same paragraph set twice,
once per font. `pdftotext -bbox-layout` gave the pitch directly.

Hypotheses tried and rejected:

- *The merged Latin outlines differ from Aeonik's.* Rejected — a 600 dpi crop of the
  same word from both blocks shows identical letterforms and widths.
- *The merged font is being rendered at a different point size.* Rejected — poppler
  word heights are 11.04 pt and 18.88 pt for the same 11 pt runs, which is
  `(asc+desc)/upem × size` for each font's own metrics, not a size difference.
- *Thai ink genuinely requires the taller box.* Rejected by `printpdf4.pdf`: 252 units
  of overflow, nothing clipped.
- *Aeonik cannot be matched because Thai needs more room.* Rejected — Bai Jamjuree,
  Leelawadee UI, Tahoma and Leelawadee all ship 1.20–1.33 em with the same overflow.

The single experiment that settled it: render page 2 of `printpdf4.pdf` — the build
whose line box was *smaller* than the ink by 252 units — and look for a clipped mark.
There are none.

## A second finding: the control block was Calibri

The QC document's `[Aeonik]` block was not Aeonik. `pdffonts` lists no Aeonik in the
file at all; every run in that block is `BCDIEE+Calibri`, `BCDKEE+Calibri-Bold` and
`BCDLEE+Calibri-Italic`. Aeonik is installed (per-user, `%LOCALAPPDATA%\Microsoft\
Windows\Fonts`), so this was a silent substitution or an unapplied font, not a missing
one.

The 1.20 em figure the fix targets was therefore taken from the font file, not from
that block. The conclusion was right and the control was not — which is luck, not
method, and worth closing. `scripts/build_ab_test_doc.py` now generates an A/B sheet
that hard-sets `w:rFonts` `ascii`/`hAnsi`/`cs` and deletes the `w:*Theme` attributes
that outrank them, and `scripts/check_ab_test_pdf.py` fails if any requested family is
absent from the exported PDF.

## Why it slipped through

**Incomplete prior fix, built on an unverified premise.** The morning fix inferred the
clipping mechanism from two facts (`usWin` contained the ink; marks were reported cut
off) without ever opening the PDF that was supposed to show the clipping. The
inference was sound given the premise; the premise was never checked.

**The test encoded the same assumption.** `qc_th_fonts.py` check 3 demanded
`hhea == sTypo == usWin` and that the box contain the ink — so it passed the
over-corrected font and would have failed the correct one. This is the third inverted
assertion in this codebase in two days, and the second in a test written the same day
to replace an inverted one.

**Nothing measured the merged face against its Latin source for leading.** Every check
compared the merged font to itself or to the Thai source. The one quantity the user
cares about — does a paragraph reflow when I switch fonts — had no test.

## Validation

Measured on Linux (fontTools, uharfbuzz, LibreOffice rendering). **Figures below are
the state at this fix**; the addenda that follow move some of them — `qc_th_fonts.py`
grows to 16 checks and `usWin` grows to 1240/560 and 1390/590.

- `scripts/qc_th_fonts.py` — **14/14** across 18 faces. Check 3 now asserts line box
  == Latin source's; check 5 bounds shaped stacks against `usWin`.
- `scripts/qc_check_th_font_doc.py` — **4/4**. Measured pitch at 11 pt: TH Aeonik
  13.20 pt vs Aeonik 13.20 pt; TH Slussen 16.65 pt vs Slussen's 1.512 em. The line-box
  comparison against the Latin source is now a hard assertion, not informational.
- `scripts/check_ab_test_pdf.py` on a LibreOffice-exported A/B sheet — **2/2**.
  TH-Aeonik 13.20 vs Aeonik 13.20 (+0.00); TH-Slussen 16.65 vs Slussen 16.65 (+0.00).
- Ink containment: TH-Aeonik static −503..+1106 inside `usWin` −560..+1160;
  TH-Slussen −535..+1255 inside −590..+1310.
- Thai size and stem unchanged: `ก` height == Latin x-height at ratio 1.000 on all 18
  faces; stems 0.93–1.00.

**Not validated in Word.** Windows still carries the previous build — Word and
PowerPoint were open, so `--apply-system` was not run. Specifically unverified:
the 13.20 pt pitch under Uniscribe, and that no stack clips at the new box in a real
ICHITA document. The Linux figures predict both, and the overflow is smaller than a
build already observed clean, but that is inference, not measurement.

## Action items

- **Reinstall on Windows and re-measure.** `./scripts/fix-th-fonts.sh --apply-system
  --restart` with Office closed, then export the A/B sheet from Word and run
  `check_ab_test_pdf.py`. (Siwatch.)
- **Stale TH-Slussen on Windows.** `%LOCALAPPDATA%\Microsoft\Windows\Fonts` holds 10
  `.otf` faces from the old build (including Light and a full italic set) alongside 4
  current `.ttf` in `C:\Windows\Fonts`. Both declare "TH Slussen". `--apply-system`
  removes them. (Siwatch.)
- **Pin line spacing in the ICHITA template** with `w:lineRule="atLeast"` — `Exactly`
  is where clipping genuinely occurs. Now lower priority: the font no longer imposes
  unusual leading. (Open.)
- **`docx_helpers.py:208` still disables unified-font mode**, so the generator splits
  Aeonik + Bai and does not use these fonts. (Open.)
- **Full Slussen source is still missing** — 4 faces available, the old build had 10.
  Do not synthesise italics by shearing. (Open.)

---

# Addendum — Thai upper marks fused into the consonant in Word

**Same day, after the line box was corrected.**

## Summary

Siwatch's next QC pass reported the Latin was now close but "Thai is broken along
with Bai Jamjuree itself", pointing at Sarabun as correctly engineered. It was a
clearance defect: the gap between a consonant and the vowel or tone above it was
under one screen pixel at text sizes, so Word fused them. Fixed by measuring every
base/mark pair and lifting the short anchors to a 72/1000 em floor, plus rejecting
glyphs that FontForge deformed during the weight match. All 18 faces now measure
71–72 against Sarabun's 73.

## Symptom

At 11 pt in Word, `กลิ่น`, `เพื่อ` and `สิทธิ์` render as dark blobs — the vowel and
tone merge into the consonant below. Sarabun at the same size stays legible. The
exported PDF looks better than the screen, which is what made it read as a Word
rendering bug.

## Root cause

Minimum clearance between consonant ink and upper-mark ink, in 1/1000 em, measured
against the consonant body (10th percentile across 46 bases):

| font | p10 | median |
|---|---|---|
| Sarabun (reference) | 73.0 | 86.3 |
| Bai Jamjuree | 65.7 | 80.0 |
| TH-Aeonik Regular | 58.5 | 67.1 |
| TH-Aeonik Medium | 31.1 | 48.3 |
| TH-Aeonik Bold | 5.4 | 24.0 |
| TH-Aeonik Black | 0.0 | 0.6 |

One em is 14.7 px at 11 pt on a 96 dpi screen, so **68/1000 em is one pixel**. Bai
starts tight — 66 is under a pixel already, which is why Siwatch saw the same fault
in Bai — and this pipeline makes it worse in two ways:

1. **Scale then embolden.** Thai is scaled to the Latin x-height (~0.87 for Aeonik),
   which shrinks the gap proportionally, then emboldened to match the Latin stem,
   which grows the consonant and the mark toward each other. Clearance tracks the
   embolden monotonically across the whole ladder.

2. **FontForge deformation.** `changeWeight(-9.5)` on `BaiJamjuree-ExtraLightItalic`
   returned `๊` stretched from y659 down to y418 — 241 units, below its own anchor.
   `TH-Aeonik-ThinItalic` shipped with it and measured a p10 of 2.4 where the upright
   `Thin` measured 87.

## Fix

`scripts/th_mark_clearance.py`. For every base/mark pair the shaper can actually
produce, measure the true 2-D distance between outlines and lift each short anchor
to `TARGET = 72`.

Three details that were each wrong on the first attempt:

- **Mark classes.** A mark attaches only to the `BaseAnchor` at its own
  `MarkRecord.Class`. Pairing every mark with every anchor reported collisions the
  shaper never produces.
- **The metric.** A column-wise vertical measure reads `ป` + `ํ` as a deep collision
  because the mark shares columns with the ascender while actually sitting in the
  open space beside it — Sarabun scores the same false negative, which is the tell.
  Clearance is measured in 2-D and against the consonant *body*, excluding ascender
  ink, which is also the only distance raising the anchor changes.
- **Iteration.** The nearest point is often diagonal, so lifting by `d` buys less
  than `d` of distance. A single pass computed from the shortfall stalled
  TH-Slussen-Bold at 60 against a target of 72; raising the per-anchor cap changed
  nothing, which proved the cap was never the constraint.

`th_thai_prep._graft_outlines` now rejects Thai glyphs whose bounding box moved
further than the weight change can account for, keeping the source outline.
Contour count was tried as a second signal and dropped: thinning legitimately
closes the loop of `ข` `ค` `ง` from two contours to one, and screening on it
rejected ~100 Thai glyphs per weight, leaving the consonants at source weight and
undoing the stem match.

## Scope of "identical to the source"

Siwatch narrowed this explicitly: **identical means the Latin outlines and the line
box.** Thai is deliberately not identical to Bai Jamjuree — it is rescaled,
reweighted, and now its marks are lifted. Recorded at the top of `qc_th_fonts.py`
so the next person does not restore the old invariant.

## Validation

Measured on Linux.

- `qc_th_fonts.py` — **16/16**, including new check 8 (clearance floor 60/1000 em,
  38 for Black/BlackItalic which are source-limited).
- All 18 faces measure worst 71.3–71.4, p10 72.0, median 72.0. Sarabun 56/73/86,
  Bai 57/66/80.
- Rendered at 15 px/em (11 pt @ 96 dpi): `เพื่อ`, `กลิ่น`, `ครั้ง` show separated
  marks where they previously fused.
- `qc_check_th_font_doc.py` — 4/4. Line box unchanged, still equal to the Latin's.
- Only three glyphs rejected by the deformation guard across 18 faces:
  `uni0E5B` (Air), `uni0E14` (Regular), `uni0E4A` (ThinItalic).

**Not validated in Word.** Windows still carries an older build; Office was open so
`--apply-system` was not run. The screen-ppem render predicts the fix but is
FreeType, not the Windows rasteriser.

## Action items

- Reinstall on Windows with Office closed and re-check `กลิ่น` / `เพื่อ` / `สิทธิ์`
  at 11 pt on screen, not only in the PDF. (Siwatch.)
- The correction levels every face to exactly the 72 floor, where Sarabun's
  distribution runs up to 86. If the Thai reads mechanically even at text sizes,
  the lever is `TARGET`, not per-glyph edits. (Open.)

---

# Addendum 2 — two consecutive Thai lines collided, and the font could not fix it

**2026-08-03, after the mark-clearance fix shipped.**

## Summary

Siwatch set the acceptance test: `สูง` on one line, `ซึ่ง` directly below,
*"สระอู กับ อึ่ง จะต้องไม่ชนกัน ต้องเว้นวรรคมากพอแบบชัดเจน"*. TH-Aeonik failed it —
at 11 pt the below-vowel of the first line fused with the vowel + tone of the second.
So did Bai, and so did **Sarabun**, the font nominated as the correct reference. The
clearance cannot come from the font without reopening a defect we had just closed, so
it comes from the document: `md_to_docx.py` now sets `w:lineRule="atLeast"` at a pitch
computed from the fonts by `scripts/thai_line_pitch.py`.

## Symptom

At 11 pt in Word, consecutive Thai lines touch. A row projection of Siwatch's own
screenshot finds no white scanline between lines 2–4 of the TH-Aeonik paragraph — the
block is one connected mass of ink.

## Root cause

Baseline-to-baseline pitch against the worst stack the shaper can produce, in
1/1000 em. `need` is the tallest upper stack plus the deepest below-baseline tail:

| font | line box | need | spare |
|---|---|---|---|
| Leelawadee UI | 1330 | 1255 | **+75** |
| TH-Slussen | 1512 | 1522 | −10 |
| TH-Aeonik | 1200 | 1459 | −259 |
| Sarabun | 1300 | 1582 | −282 |
| Bai Jamjuree | 1250 | 1564 | −314 |

**Only one font in the table clears its own line box, and it is not the reference.**
Sarabun is geometrically the worst of the five; it survives casual inspection only
because `ส` and `ซ` differ in width, so the marks miss each other sideways rather
than by design. Leelawadee UI clears by drawing markedly smaller marks — upper vowel
201 units tall against TH-Aeonik's 273, tone 129 against 158, below-vowel 182 deep
against 269 — not by a taller box.

TH-Aeonik is worse than Bai in *spare* because it inherited Bai's mark proportions
and then took Aeonik's 1.20 em line box, which is 50 units tighter than Bai's own.

## Why the font could not fix it

Three levers, all previously spent:

- **Raise the line box.** That is the 42% leading defect this post-mortem is about.
  Clearing at Word's Single spacing needs ~1.55 em, +29% over Aeonik on every
  paragraph including pure-Latin ones.
- **Shrink the marks.** Toward Leelawadee proportions this reaches ~1220 units —
  still short of 1200 — and walks back the clearance the addendum above just bought.
- **Scale the Thai down.** Fixed by the pairing rule: `ก` matches the Latin x-height.

The vertical budget is genuinely oversubscribed. A Latin line box cannot hold a Thai
three-level stack over a below-vowel, which is why no Thai text font in the table
attempts it.

## Fix

`scripts/thai_line_pitch.py` measures each family and emits the ratio:

```
required_pitch = worst_upper_stack + |worst_lower_tail| + MARGIN
MARGIN = 75          # Leelawadee UI's own spare, and ~1 px at 11 pt / 96 dpi
```

| family | worst face | ratio × Thai pt |
|---|---|---|
| TH-Aeonik | Black | 1.534 |
| TH-Slussen | SemiBold | 1.597 |
| Bai Jamjuree | Bold | 1.639 |

`md_to_docx.py` carries 1.60 for unified mode and 1.64 for split mode, applied
through `thai_line_pt(latin_pt)` at every call site. Body text at 10 pt Latin moves
from `Exactly 13 pt` to `atLeast 15 pt`.

Two things changed, and the rule change matters as much as the number:

- **`Exactly` → `atLeast` everywhere.** `Exactly` is a fixed box and is where Word
  genuinely clips marks — the mechanism this post-mortem identified in its opening
  section and then left in place in the generator. `atLeast` lets a line grow.
- **The old 1.46 ratio was derived from one stack in isolation** (`ขึ้` plus an
  assumed descent), not from a shaped worst case over the whole script, and it never
  accounted for the *lower* line's below-vowel at all. It was ~2 pt too tight.

## Why it slipped through

**Nothing tested two lines.** Every clearance measure in this codebase — check 8,
`th_mark_clearance.py`, the whole of the addendum above — measures *within* a
syllable: base to mark, mark to mark. The interaction that Siwatch's benchmark
targets is between adjacent lines, and no test, font-side or document-side, had ever
looked at it. The font QC suite was 16/16 green throughout.

**The reference was trusted past the property it was verified for.** Sarabun was
correctly nominated for within-syllable engineering, where it measures p10 73 against
Bai's 66, and correctly used to set the 72-unit target. Carrying that authority over
to line spacing was never checked, and it does not survive the check.

## Validation

Measured on Linux.

- `scripts/thai_line_pitch.py --check` — OK, all three families fit the ratios
  compiled into `md_to_docx.py`.
- Generated a mixed Thai/Latin document and rendered the LibreOffice PDF export at
  200 dpi: every consecutive line pair separated by white scanlines, where the same
  content previously projected as one connected band.
- `scripts/qc_th_fonts.py` 16/16, `scripts/qc_check_th_font_doc.py` 4/4 — the fonts
  are untouched by this change, and the line box still equals the Latin source's.
- Latin-only and `--compact` generator paths both build clean.

**Not validated in Word.** Windows still carries the current TH-Aeonik build (verified
by hash) but a stale TH-Slussen, and LibreOffice's `atLeast` handling is not Word's.

## Action items

- Confirm in Word that `สูง` over `ซึ่ง` clears at 11 pt on screen. (Siwatch.)
- **Documents get ~15% taller** where Thai body text dominates — 13 pt to 15 pt at
  10 pt body. Expected and necessary; flag if it breaks a fixed-page layout. (Open.)
- KPI card unit and label lines also take the ratio, so cards grow a few points.
  They rarely wrap, but sizing them below the ratio would collide if they ever did.
  (Open.)
- `thai_line_pitch.py` needs `uharfbuzz`, so it runs under `venv_fonts/bin/python`,
  not the system python3 the other QC scripts use. (Open.)
