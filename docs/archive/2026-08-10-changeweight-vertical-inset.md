# `changeWeight` insets every edge — the defect that shipped in Book

**2026-08-10. Distilled into [`../THAI-LATIN-FONT-ENGINEERING.md`](../THAI-LATIN-FONT-ENGINEERING.md)
§4c. Read that first — this file carries the falsified hypotheses and the
measurement trail, which the consolidated document compresses to a paragraph.**

Fixed in `18fb976`, branch `feat/th-aeonik-ten-weight-deck`.

---

## Summary

FontForge's `changeWeight` insets an outline by roughly half the requested amount on
**every** edge, horizontal ones included, so a thinned synthetic Latin ships shorter
than its base and lifted off the baseline. `Aeonik-Book.otf` had been shipping 2.7%
short and 7 units high since 2026-08-07. It surfaced only when it blocked the new
`Aeonik-ExtraBold.otf` merge outright. Fixed by `restore_vertical()`, which maps the
derived face's baseline and x-height back onto its base's, plus a `--check` assertion
comparing every synthetic face's vertical band to the face it was derived from.

## Symptom

Two, and only the second was visible.

```
ERROR: Thai tracking correction is 1.0834, past the 8% bound. That is not a
spacing problem — the scale or the Bai pairing is wrong upstream.
```

`build_th_aeonik.py --weights ExtraBold` aborted in
`th_thai_prep.normalise_thai_tracking()`.

The silent one, present for three days: `Aeonik-Book.otf` measured x ink 496 against
`Aeonik-Regular.otf`'s 510, with `x`, `n` and `H` all sitting at `yMin = 7` instead
of `0`.

## Root cause

`th_thai_prep._embolden()` shells out to
`f.changeWeight(amount, "auto", 0, 0, counter_type)`. On a negative amount it does not
only thin vertical stems — it moves every edge inward by ~`|amount|/2`, including the
horizontal ones that define the baseline and the x-height. Measured on
`Aeonik-Black.otf` at −18.4:

```
glyph   Black          thinned      drift
x         0..516         9..507     baseline +9, x-height −9
H         0..700         9..691     baseline +9, cap      −9
```

`build_face()` in `build_aeonik_semibold.py` grafted those outlines verbatim. Nothing
downstream restored the vertical dimension, and `_name_face()` re-measured
`sxHeight`/`sCapHeight` from the shrunken ink — so the OS/2 fields agreed with the
defect.

## Why it produced the symptom

`th_thai_prep` sizes the Thai to the Latin's x-height:

```python
xh = _glyph_height(latin_font, 'x')
kh = _glyph_height(font, 'ก')
scale = xh / kh
```

`_glyph_height` returns `yMax − yMin`, so the inset enters the scale **twice** — once
from the lowered top, once from the raised bottom. For ExtraBold that gave
`498 / 570 = 0.8737` against a nominal `0.914`, a 2.4% under-scale of the Thai.

`normalise_thai_tracking()` then computes `k = (THAI_ADV_RATIO * lat) / thai` to put
the Thai advance ladder in weight order. An under-scaled Thai needs a proportionally
larger correction, which pushed `k` to 1.0834 past `TRACKING_MAX = 0.08`. The bound
fired exactly as designed — it says "the scale is wrong upstream", and it was.

For Book on 08-07 the same chain ran 2.4% smaller and stayed inside the bound, so it
shipped: scale `0.8889`, merged Thai stem 64.0 where the weight is *defined* by 66.4.

## Fix

`restore_vertical(font, base_band)` in `build_aeonik_semibold.py`, called in
`build_face()` between `graft()` and `scale_advances()`.

`_vertical_band()` measures `(baseline, x-height)` as the median `yMin`/`yMax` over
`FLAT_GLYPHS = ("x","n","u","m","H","I")` — round letters are excluded because their
overshoot would fold into the correction. The map is `y' = base_low + (y - low) * k`,
applied to `glyf` coordinates in place; composites scale only their `y` offset, since
their base glyph already carries the map.

This addresses the cause rather than the symptom because the x-height band is what the
merge keys on. Cap and descender scale with it and land within ~2% rather than exactly
— a constant inset is not an affine transform, so no single map restores every extreme.
That trade is stated in the docstring rather than hidden.

### The prior fix attempt is part of the cause

§4c on 2026-08-07 recorded half of this ("thinning shrinks the x-height") and responded
by moving `SYNTH["Book"]["stem"]` from 74.0 down to 71.9 with advances re-interpolated.
That restored the **ratio** and preserved the **shrink**.

`18fb976` reverts it. Book's target goes back to the derived 74.0, because 74.0 is
`66.4 / WEIGHT_RATIO[350]` and 66.4 is Bai Jamjuree Regular undistorted — which is what
the weight means.

## How it was found

The ExtraBold merge aborted on the tracking bound. Rather than widen it — the error
text explicitly forbids that — the scale was traced back through
`[0b] Scale solved from ink: x-height 498 / ก 570`, then `_glyph_height` (498) compared
against a `BoundsPen` `yMax` (507), which exposed the 9-unit `yMin`.

Hypotheses, in order, all falsified:

1. **The `glyf` intermediate loses the CFF blue zones.** Confirmed absent — but passing
   `custom_zones=(516, 522, -6, 0)` explicitly produced a byte-identical 9-unit inset.
2. **`type="auto"` ignores zones where `"LCG"` honours them.** Both modes, identical
   output.
3. **cu2qu rounding at `max_err=0.5`.** The inset is 9 units at −18.4 and 7 at −14.5 —
   it scales with the amount, so it is not rounding.

**The experiment that settled it:** run `changeWeight` directly on the pristine
`Aeonik-Black.otf`, whose `BlueValues` are present and correct
(`-6, 0, 516, 522, 699, 706`, `OtherBlues (-200, -200)`). Same 9-unit inset. The zones
are irrelevant; the behaviour is inherent to the tool, so the correction has to be ours.

## Why it slipped through

Every check compared the two scripts **inside one font**, and both had moved together.

* QC check 1 asserts merged Thai ก height against that same font's Latin x-height —
  both shrunk, ratio 1.000, pass.
* QC check 9 asserts the Thai baseline against that same font's Latin baseline — both
  lifted 7, drift 0.0, pass.
* QC check 2's stem ratio passed because the 08-07 target had been lowered to match.

**Nothing compared a derived Latin face to the base face it was derived from**, and
`_name_face()` re-measuring `sxHeight` from the shrunken ink removed the last field
that could have disagreed. The gap is a missing cross-artifact comparison, not a
missing assertion.

## Validation

* `build_aeonik_semibold.py --check`: all six synthetic faces report baseline `0` and
  x-height equal to their base — `Book`/`BookItalic` 516, `SemiBold`/`SemiBoldItalic`
  518, `ExtraBold`/`ExtraBoldItalic` 522 — bounded by `VERTICAL_TOL = 2.0`.
* **The falsifiable half held.** `SemiBold` and `SemiBoldItalic` are *grown*, not
  thinned, and both logged `vertical band 0..518 already matches the base — no
  correction`. The fix is a genuine no-op where it should be.
* Book re-merged: scale solves at `0.9140`, exactly the nominal `THAI_SCALE`; Thai stem
  66.4; ratio .895 against a .8975 target — **−0.2 units, the tightest face in the
  family**.
* ExtraBold merge completes: scale `0.9053`, tracking `×1.0463`, inside the bound that
  had aborted it at `1.0834`.
* `qc_th_fonts.py` 22/22 across all 22 shipped faces; `verify-fonts.py`,
  `th_style_link.py --check`, `fc_family_probe.py` 0 faults.

**Coverage, stated honestly:** this is Linux-side outline geometry only. Word on
Windows has not seen these faces — §0 rule 1 — and the acceptance sheet is still
outstanding. TH-Slussen has no synthetic Latin and was not rebuilt.

## Action items

* **Confirm the Thai half is genuinely unaffected.** Twelve of fourteen faces run their
  Bai source through the same `th_thai_prep._embolden()`, so the same inset applies to
  the Thai outlines. It *should* be absorbed — `[0b]` solves the scale from the
  emboldened ก, and `[3c]` re-seats the Thai baseline against the Latin — but that is
  an argument, not a measurement, and QC 1 and 9 are exactly the checks that proved
  unable to see this class of defect. Measure a prepared Thai against its pristine Bai
  source directly.
* **Word acceptance for the rebuilt faces** — `test-output/th-style-link-acceptance.docx`.
  Standing gate, not new to this bug.

No third item. The `--check` band assertion closes the class of bug at the seam where
it occurs, and no refactor is warranted.
