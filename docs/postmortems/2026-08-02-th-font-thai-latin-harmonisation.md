# TH font Thai/Latin harmonisation — four defects from one wrong invariant

**Date:** 2026-08-02
**Branch:** `docs/ichita-proposal-design`
**Scope:** `TH-Aeonik` (14 faces), `TH-Slussen` (4 faces)

## Summary

The merged TH families shipped Thai that was 9% too large, 18–25% too light, clipped
at top and bottom, and collapsed document line spacing by 38%. All four trace to a
single wrong acceptance criterion: `compare_th_aeonik.py` and `compare_th_slussen.py`
asserted that merged Thai must be **pixel-identical to Bai Jamjuree**, and passed.
That is the wrong reference — Bai's Thai is drawn to sit beside Bai's *own* Latin — so
the test could only pass while the font was wrong, and it was cited in two prior
post-mortems as proof the merge was correct. A fifth defect, unrelated to that
invariant, was found in the same pass: isolated or repeated spacing vowels (`าาาาาาา`)
would not type in Word, because Bai omits both GDEF classes on spacing vowels and a
U+25CC dotted circle.

Fixed by `scripts/th_thai_prep.py` (new), which scales and weight-matches Bai against
the specific Latin weight it is being merged into, plus vertical-metric and GDEF
corrections in both build scripts. New acceptance test: `scripts/qc_th_fonts.py`,
14/14 across all 18 faces.

## Symptom

Four separate reports from a manual QC pass, plus one measurement:

1. Thai read visibly larger than the Latin beside it at the same point size.
2. `printpdf4.pdf` (new fonts) vs `printpdf0.pdf` (old fonts), same document, page 2:
   line pitch **25.30 pt → 15.60 pt**, 11 pages → 10. Layout collapsed.
3. Words with stacked vowels and tone marks — `ที่ ครั้ง ทุก สิ่ง ซึ่ง กู่ น้ำ ต่ำ ลิ้น ขึ้น
   ทื่อ จึ๊ง สิทธิ์` — cut off at top and bottom.
4. Thai stroke weight looked lighter than the Latin.
5. `าาาาาาา` could not be typed in Word, isolated or repeated.

## Root cause

### 1. No scale applied (`copy_thai_glyphs`)

Bai's `ก` is 558 units tall. Aeonik's x-height is 510, Slussen's 540. Glyphs were
copied verbatim, so `ก` rendered at **109.4%** of Aeonik's x-height and 103.3% of
Slussen's.

### 2. Weight paired by name, not by measurement (`WEIGHTS`)

`WEIGHTS` mapped `Aeonik-Regular.otf → BaiJamjuree-Regular.ttf` and equivalents.
Bai's ladder does not align with Aeonik's. Measured stems (median horizontal ink run
across a mid-height band, 512 px/em):

| | Latin | Thai | ratio |
|---|---|---|---|
| TH-Aeonik Regular | 85.9 | 70.3 | **0.818** |
| TH-Slussen Regular | 95.7 | 70.3 | **0.750** |

The correct source for Aeonik Regular is Bai **Medium** (91.8), not Regular.

### 3. `hhea` left at 1000/−300 (`set_vertical_metrics`)

The 2026-08-02 morning build set `ASCENT, DESCENT, LINEGAP = 1000, -300, 0` on the
reasoning recorded in the source comment: *"Raising these does not change line
spacing: USE_TYPO_METRICS is set below, so consumers take spacing from the sTypo
set."* **That assumption is false for Word, which leads off `hhea`.**

`usWinAscent/usWinDescent` had already been correctly raised to 1250/570 and did
contain the ink — yet marks still clipped. So the clip is taken against the
`hhea` line box, and raising `usWin` alone could never have fixed it.

`TH-Slussen` had the same defect via a different route: it preserved Slussen's
original 1074/−272/166 on the theory that document line spacing must never change,
while the merged ink runs −564..1255.

### 4. Uniscribe prerequisites absent (inherited from Bai)

Bai leaves spacing vowels `า ะ ำ เ แ โ ใ ไ ๆ` at GDEF class **0 (unassigned)** and
ships **no U+25CC**. Every shipping Thai font checked — Leelawadee, Leelawadee UI,
Tahoma, Noto Looped Thai — declares them `BASE` and carries a dotted circle.

### 5. The inverted acceptance test

`compare_th_*.py` asserted merged-Thai == Bai-Thai, pixel for pixel, and reported
"0.00% differing". Under defect 1 that equality is *definitionally* the bug.

## Why it produced the symptom

**Pitch collapse.** Old `.otf`: `hhea` 1550/−561 = 2111. New: 1000/−300 = 1300.
2111/1300 = 1.6238. Measured 25.30/15.60 = 1.6218 — predicted to within 0.1%. At
12 pt body text: 2.111 × 12 = 25.33 (measured 25.30); 1.300 × 12 = 15.60 (measured
15.60). The old 2111 was **not** sloppiness — 1550/−561 deliberately contained ink of
+1206/−488. The rebuild discarded that correction, which is why one change produced
both the squeeze and the clipping.

**Vowels not typing.** Uniscribe reads GDEF to decide what may act as a base when
validating a Thai syllable. A spacing vowel at class 0 is not a base, so an isolated
or repeated `า` is rejected. HarfBuzz infers the class from Unicode and shapes it
correctly, which is why every Linux-side test passed.

## Fix

**`scripts/th_thai_prep.py`** (new) — `prepare_bai(family, weight, latin_font)`:

- `BUILD_TABLE` pairs each output weight with the Bai weight whose stem, after
  scaling, matches that Latin weight, plus a FontForge `changeWeight` delta for the
  residual.
- The scale is **solved from the emboldened outline**, not from a constant.
  Emboldening grows the glyph box, so a fixed 0.914 overshot on Bold (`ก` at 105% of
  x-height) while landing correctly on lighter weights.
- Scaling uses `scaleUpem(font, round(1000*scale))` then re-declares
  `head.unitsPerEm = 1000`, so GPOS anchors and mark-attachment points move with the
  outlines. Scaling glyphs alone would leave every tone mark anchored at its original
  height.
- `fix_thai_gdef()` assigns GDEF class from the Unicode general category —
  `Mn`/`Me` → MARK, everything else in the Thai block → BASE.
- `add_dotted_circle()` synthesises U+25CC. Drawn, not copied: the only local U+25CC
  are in licensed Windows system fonts.

**Both build scripts** — `hhea`, `sTypo` and `usWin` set to one box per family
(TH-Aeonik 1160/−550/0, TH-Slussen 1280/−590/0), with a build-time assertion that
the box contains the ink. The build now **fails** rather than shipping a font that
clips.

**`scripts/qc_th_fonts.py`** (new) replaces the inverted test, measuring Thai against
the Latin it shares a line with. `compare_th_*.py` are marked deprecated in-file with
the reasoning, not deleted — the raster-diff plumbing is still useful.

**Coverage** — `TH-Aeonik` extended 6 → 14 faces to match Aeonik's full range.

## How it was found

Reproducer was the user's own printed PDFs, which made the pitch defect deterministic
and measurable rather than subjective.

Hypotheses tried and rejected:

- *Word uses typo metrics.* Rejected — under typo metrics TH-Slussen is byte-identical
  to source Slussen and cannot regress, yet both families were reported loose.
- *Word uses `usWin`.* Rejected — 2111 → 1820 is −14%, but measurement showed −38%.
- *Word uses `hhea`.* Confirmed. 2111 → 1300 predicts −38.4%; measured −38.3%.
- *The vowel bug is a regression from the rebuild.* Rejected — the old `.otf` has
  identical GDEF classes and also lacks U+25CC. Inherited from Bai.
- *Scaling alone fixes weight.* Rejected — scaling down thins stems further, taking
  Thai from 18% to ~25% light. Scale and weight must be solved together.

The experiment that nailed the metrics: computing `old_hhea/new_hhea` and comparing it
to `old_pitch/new_pitch` from `pdftotext -bbox-layout`. 1.6238 vs 1.6218.

## Why it slipped through

**The acceptance test asserted the defect.** This is the whole story. `compare_th_*.py`
measured merged Thai against the wrong reference, so the tighter it passed, the more
wrong the font was. Two post-mortems cite its "0 differing pixels" as evidence of
correctness.

Secondary: **every test ran on Linux under HarfBuzz**, which infers GDEF classes from
Unicode and tolerates a missing U+25CC. The Uniscribe defect is structurally invisible
to a HarfBuzz-only test suite.

## Validation

Measured, on Linux:

- `scripts/qc_th_fonts.py` — **14/14 checks across all 18 faces.**
  - `ก` height == Latin x-height, **ratio 1.000 on every face**.
  - Thai/Latin stem ratio 0.93–1.00 (was 0.818/0.750).
  - `hhea` == `sTypo` == `usWin`, identical across every weight in a family,
    asserted to contain the ink.
  - All 18 reported words shaped via uharfbuzz — including the GSUB-only `.small`
    mark variants — stay inside the box at every weight.
  - Weight ladder monotonic and distinct, Air → Black.
  - GDEF: 71 BASE + 16 MARK per face, zero mismatches. U+25CC present, class BASE.
- `scripts/qc_check_th_font_doc.py` — 4/4 on the generated QC document. Line pitch
  measured from glyph positions matches prediction from the font's own metrics to
  within 0.02 pt on all four measured fonts.

**Not validated:**

- **The Uniscribe fix is unverified in Word.** GDEF classes and U+25CC are confirmed
  present in the binaries, and the dotted circle renders correctly beside Leelawadee,
  but that `าาาาาาา` now types is *not* confirmed — it requires Uniscribe, which is
  Windows-only. Windows still has the previous fonts installed.
- **The line-pitch fix is unverified in Word** for the same reason. Predicted pitch
  is 1.71 em (TH-Aeonik) / 1.87 em (TH-Slussen).
- Documents built against the old 2.111 em box **will reflow**. This was an accepted
  trade, not an oversight.

## Known limitations

Bai's weight ladder (ExtraLight 35.2 → Bold 132.8) is narrower than Aeonik's
(7.8 → 183.6) at both ends. Four faces are reached by pushing past the source:

| face | delta | cost |
|---|---|---|
| Thin | −9.5u | none — contour count unchanged |
| Air | −26.6u | hairline; Thai very faint at text sizes |
| Black | +68.1u | **Thai ~10% light, and unfixable.** Aeonik Black's stroke-to-height ratio is 0.356; Bai Bold's is 0.238. Correcting for the embolden/rescale feedback demands +102u, which closes the counters of `ครั้ง` and `สิทธิ์` outright. |

Encoded as per-face tolerance overrides in `qc_th_fonts.py::STEM_TOL_OVERRIDE` with the
reasoning inline. The test still fails if a face drifts beyond its documented limit.

## Action items

- **Reinstall on Windows and confirm defects 3 and 5 in Word.**
  `./scripts/fix-th-fonts.sh --apply-system --restart`, then test `าาาาาาา`, an
  isolated `ิ`, and `่`, and re-measure line pitch on the resin report.
- **Pin line spacing in the ICHITA template.** The font box is deliberately loose
  because it must contain Thai ink; documents should not inherit it. Use
  `w:lineRule="atLeast"` — `Exactly` re-clips tall stacks, reintroducing defect 3.
- **`docx_helpers.py:208` still disables unified-font mode**, so the generator splits
  Aeonik + Bai rather than using these fonts at all.
- **Locate the full Slussen source.** The old build on `D:` has 10 TH-Slussen faces
  including Light and a full italic set; neither source directory contains them.
  Italics must not be synthesised by shearing the uprights.
- **Amend the two 2026-08-01 merge post-mortems**, which cite the inverted test as
  proof of correctness.
