---
name: thai-mark-clearance-vs-pixel-grid
description: Thai upper marks need ~70/1000 em of clearance or they fuse into the consonant at Word text sizes; scaling and emboldening both eat that gap
metadata:
  type: project
---

A Thai font can shape perfectly and still read as broken, because the gap between a
consonant and the vowel or tone above it is a **pixel-grid** problem, not a shaping
one. One em is 14.7 px at 11 pt on a 96 dpi screen, so **68/1000 em is one pixel**.
Below that the gap rounds away and Word draws the mark fused into the consonant.

Measured minimum clearance, 10th percentile over 46 bases:
Sarabun 73, Bai Jamjuree 66, TH-Aeonik Regular 58, Bold 5, Black 0.

**Why:** the ICHITA pipeline scales Thai to the Latin x-height and then emboldens it
to the Latin stem. The first shrinks the gap proportionally, the second closes it from
both sides, so clearance degrades monotonically along the weight ladder. The defect is
invisible in an exported PDF — it rasterises finer — which makes it read as a Word
rendering bug when it is a font-metrics one.

**How to apply:** measure clearance in 2-D against the consonant *body* (excluding
ascender ink) and respect mark classes — a mark attaches only to
`BaseAnchor[MarkRecord.Class]`. Corrections must iterate, because the nearest point is
usually diagonal so lifting an anchor by d buys less than d of distance. Separately,
FontForge `changeWeight` silently deforms small Thai marks; screen for bounding-box
drift, never for contour count, since thinning legitimately closes the loop of ข ค ง.
Related: [[ichita-thai-latin-pairing-rule]], [[harfbuzz-cannot-validate-word]].
