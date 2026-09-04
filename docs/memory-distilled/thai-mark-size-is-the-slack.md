---
name: thai-mark-size-is-the-slack
description: "FALSIFIED 2026-08-04 — mark size is NOT usable slack; shrinking marks 25% buys only 35 units, and Aeonik's 1200 box is unreachable for Thai at any mark size"
metadata: 
  node_type: memory
  type: project
  originSessionId: 63f4921f-6c62-49b0-921e-98c108550946
  modified: 2026-08-04T09:24:35.680Z
---

**FALSIFIED BY MEASUREMENT, 2026-08-04 (evening). The title is wrong.** The
mark-SIZE figures below are still right — Bai's marks really are 26–45% larger
than Leelawadee's. What is wrong is the conclusion that shrinking them is a usable
lever. Swept through the real builder, `scripts/solve_mark_scale.py`:

```
mark scale   top   bottom   need   required(+75)   vs 1200
   1.00     1139    -323    1462       1537         -337
   0.80     1096    -258    1354       1429         -229
   0.70     1078    -258    1336       1411         -211
   0.60     1061    -258    1319       1394         -194
```

A 25% mark reduction buys **35 units**. Two floors, neither of them a mark:

1. `th_mark_clearance.raise_upper_marks()` re-settles — a smaller mark is a
   smaller obstacle, so the pass lifts it higher to hold its 72-unit (1 px)
   target, cancelling most of the height saved. Dropping that target re-fuses the
   marks it exists to separate.
2. `bottom` bottoms out at **-258 on `ฐ`, a CONSONANT TAIL**. No mark scale can
   move it.

Floor is ~1383 with the margin, ~1308 without, against 1200: **unreachable at any
mark size worth shipping.** MARK_SCALE stays 1.000 — shrinking would cost
tone-mark legibility (่ ้ ๊ ๋ differ by small strokes) for nothing. Siwatch took
box 1200 regardless, accepting that worst Thai-over-Thai stacks overlap 262 units
/ 3.9 px at 11 pt.

The projection below was wrong because it was pure geometry: it ignored the
clearance pass re-settling and assumed the lower extreme was a below-vowel rather
than a consonant tail. **Never re-derive a mark scale from a static stack
decomposition — build it and measure.** The transform in
`scripts/th_mark_scale.py` (scale each mark about its own GPOS anchor, which is
then a fixed point and needs no edit) is correct and reusable; it is just not
worth using here. See [[one-font-one-line-height]].

---

*Original note, kept for the mark-size figures and the decomposition method:*

To fit Thai inside Aeonik's 1200 line box, something has to shrink. Measured
2026-08-04 on TH-Aeonik-Black, decomposing the worst shaped stack `ปื้`:

```
base ป          1..701
upper vowel ื 590..867     gap to base  +65   (short bases: 65, at the 1px floor)
tone ้.small  905..1139    gap to vowel +38   (BELOW the 68/1000 = 1px floor)
worst lower ุ      -323
need = 1139 + 323 + 75 margin = 1537   vs Aeonik's 1200
```

**Placement is already maxed out** — the inter-level gaps are 65 and 38 units, at and
under one pixel. Nothing can be reclaimed by lowering marks. The height is in the marks
themselves. At the SAME consonant height (ข top 510 both), against Leelawadee UI:

```
          ื     ึ     ิ     ้     ุ/ู
ours    248   267   212   226   266/264
Leelawadee 197   201   167   201   182     <- ours are +26% to +45%
Sarabun    290   285   234   268   270/272 <- Sarabun is BIGGER than ours
```

Projected worst-case Thai-over-Thai overlap at a 1200 box, by mark scale:

```
1.00 +262u (3.85px)   0.85 +142 (2.09)   0.80 +102 (1.51)   0.75 +62 (0.92)   0.70 +23 (0.33)
```

0.80 lands marks at 198 units — within 1 unit of Leelawadee's 197, so it is a referenced
size rather than an invented one. For scale: Leelawadee UI itself is +55 over 1200, and
**Sarabun ships -282 and Bai -314 with no margin**, so 0.80 or below beats every
reference measured, including the one Siwatch nominated.

**Why:** four sessions treated the tall line box as a fact of Thai and spent the argument
on where to put the extra leading. It is not a fact of Thai — Leelawadee fits the same
consonant size into 1255. Bai simply draws large marks, and the ICHITA pipeline inherited
them unquestioned while scaling and emboldening everything else.

**How to apply:** measure the stack's decomposition before concluding a Thai font needs a
tall box — separate mark SIZE from mark PLACEMENT, because only one of them may have
slack. Shrinking marks preserves the clearance floor (the gap is held, the mark's top
comes down) so it composes with [[thai-mark-clearance-vs-pixel-grid]], but it does risk
the four tone marks ่ ้ ๊ ๋ becoming hard to distinguish at 11 pt — that is a
brand-visual call for Siwatch, not a measurement. **Not yet implemented or approved:** he
declined the scale question pending clarification, and flagged three things I had not
checked — contextual short-mark variants (Bai already has `.small`/`.narrow`, so a font
can substitute shorter marks only when they stack, buying height without shrinking
isolated marks), how OFTEN the worst pairing actually occurs in real Thai text, and
whether shrinking Thai marks is an acceptable price for identical Latin at all.
Related: [[one-font-one-line-height]], [[thai-line-clearance-is-a-document-setting]].
