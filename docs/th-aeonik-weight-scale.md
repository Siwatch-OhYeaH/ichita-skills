# TH Aeonik — ten-step weight scale

TH Aeonik pairs Aeonik (Latin) with Bai Jamjuree (Thai) across ten weights,
in both upright and italic — 20 faces.

| Style     | Weight | Latin source           | Thai source              |
|-----------|--------|------------------------|--------------------------|
| Air       | 100    | Aeonik Air             | Bai Jamjuree ExtraLight † |
| Thin      | 200    | Aeonik Thin            | Bai Jamjuree ExtraLight  |
| Light     | 300    | Aeonik Light           | Bai Jamjuree Light       |
| Book      | 350    | *generated* (300→400)  | *generated* (300→400)    |
| Regular   | 400    | Aeonik Regular         | Bai Jamjuree Regular     |
| Medium    | 500    | Aeonik Medium          | Bai Jamjuree Medium      |
| SemiBold  | 600    | *generated* (500→700)  | Bai Jamjuree SemiBold    |
| Bold      | 700    | Aeonik Bold            | Bai Jamjuree Bold        |
| ExtraBold | 800    | *generated* (700→900)  | *generated*, damped ‡    |
| Black     | 900    | Aeonik Black           | *generated*, damped ‡    |

† The Thai does not go below 200 — see limitations.
‡ Drawn at ~710 / ~720 rather than 800 / 900 — see limitations.

Specimen sheets: [specimens/](specimens/) (`python3 scripts/make_specimens.py`).
Measurements, defects found, and the reasoning behind the limits:
[th-aeonik-findings.md](th-aeonik-findings.md).

## Using the fonts in Word and PowerPoint

**Pick the weight by name from the font dropdown and leave the B button off.**

Only **TH Aeonik** has a real Bold — Regular and Bold 700 are style-linked as a
RIBBI pair, so Ctrl+B there is correct. The other eight weights each form their
own two-style family (Regular + Italic), so Ctrl+B finds no Bold slot and Word
fakes one by smearing the outline. Italic is real everywhere.

Want bold-looking text? Choose *TH Aeonik ExtraBold*; do not press Ctrl+B on
*TH Aeonik Medium*. See
[the Word specimen](specimens/word-bold-italic.png) and
[findings §7](th-aeonik-findings.md#7-bold-and-italic-in-word--powerpoint) for
the cause.

InDesign, Illustrator and Figma read the typographic family names and show all
ten weights under a single "TH Aeonik", so this does not apply there.

## Building

```sh
python3 scripts/generate_masters.py    # fills the gaps neither family ships
python3 scripts/build_th_aeonik.py     # merges Latin + Thai into 20 faces
python3 scripts/verify-fonts.py        # production checks
```

`generate_masters.py` writes to `assets/fonts/aeonik-ext/` and
`assets/fonts/bai-jamjuree-ext/`; `build_th_aeonik.py` consumes those plus the
original masters and writes `assets/fonts/aeonik-th/`.

## How the missing weights are made

Neither source family ships all ten weights, and neither ships an
interpolatable master set — they are static instances whose per-weight curve
optimisation dropped different points from each. Straight point-wise
interpolation is therefore impossible: across Bai Jamjuree's six weights only
7 of 87 Thai glyphs agree on their point counts.

They do agree on *topology* — contour counts match almost everywhere — so
`interpolate_masters.py` reconciles them:

1. **Match contours by geometry**, not by index. Masters do not always store
   contours in the same order; in Aeonik's `oe` the two counters are swapped
   between Light and Regular.
2. **Align nodes by position** with an order-preserving (Needleman-Wunsch
   style) pass. Arc-length matching drifts on a heavier master, and while
   interpolation hides that, extrapolation doubles every mis-pairing.
3. **Split segments to a shared node set** using de Casteljau subdivision.
   Subdividing a Bézier is exact, so this raises point counts without moving
   the outline at all — `--self-test` asserts it, and measures the residual at
   0.002–0.17 units on a 1000-unit em.
4. **Verify the blend actually blends.** Structural compatibility is not the
   same as correct correspondence: pair a round counter with a rotated copy of
   itself and every node lines up, yet the midpoint interpolates smaller. The
   midpoint's enclosed area is checked against what a faithful blend would
   enclose, and a pairing that fails is rejected so the glyph keeps a master's
   outline instead of shipping distorted. (Area is quadratic in the
   coordinates, so the expectation is the midpoint of the square roots, not
   the mean of the areas.)

Glyphs that fail step 4 fall back to the master **nearest in weight**, so a
fallback in the damped heavy Thai comes from Bold rather than from Medium.

Run `python3 scripts/interpolate_masters.py --self-test` to check the
subdivision is still lossless.

## Limitations

**The Thai cannot span the full scale.** Bai Jamjuree ships 200–700, and
measuring where its outlines begin to self-intersect shows the design does not
survive being pushed outside that range:

| Target | Factor | Thai glyphs that self-intersect |
|--------|--------|---------------------------------|
| 900    | +2.00  | 40 of 86                        |
| 800    | +1.50  | 8 of 86                         |
| 730    | +1.15  | 0 — last clean step above Bold   |
| 200    | —      | 0 — lightest clean weight        |
| 150    | −0.25  | 11 of 87                        |
| 100    | −0.50  | 33 of 87                        |

Thai letters are built from small loops that close up and cross before the
Latin is anywhere near its limit. So Air 100 uses ExtraLight outlines
unchanged, and ExtraBold/Black are damped to a verified-clean ~710/~720. The
Thai flattens at both ends of the scale while the Latin runs the full 100–900.
Widening it would need a Thai face with masters beyond 200–700, not a change
to this pipeline.

**Some glyphs sit one master-step off.** Where correspondence cannot be
trusted a glyph keeps its nearest master's outline. In the shipped character
set that is roughly 9–15% of Latin glyphs in the generated weights (mostly
accented forms and punctuation, one master step light) and 19 of 87 Thai
glyphs in ExtraBold/Black — those come from Bold 700 against a ~710/720
target, so they are visually seamless. `generate_masters.py` reports the count
per face.

## Vertical metrics

`sTypo*` and `hhea` are inherited from Aeonik untouched, so line spacing
matches the Latin original (USE_TYPO_METRICS is set). Only
`usWinAscent`/`usWinDescent` — the Windows clipping box — are adjusted, to
`max(floor, measured ink)` with floors of 1550/561.

Both halves matter. Measured ink alone is too small: GPOS stacks a tone mark
above a vowel, so a cluster reaches higher than any single glyph's bounding
box and no per-glyph measurement can discover the space it needs. The floors
alone are too small at the heavy end: Black's descenders reach −570, past the
historic 561.
