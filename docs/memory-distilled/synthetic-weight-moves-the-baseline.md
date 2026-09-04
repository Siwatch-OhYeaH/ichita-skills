---
name: synthetic-weight-moves-the-baseline
description: "FontForge changeWeight grows an outline in every direction, so synthetic emboldening silently pushes a script off the baseline in proportion to the weight change"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d53cf7f9-f6b3-498c-b3de-1083b5f85c67
  modified: 2026-08-03T06:35:49.742Z
---

`changeWeight(delta)` thickens strokes by moving every edge outward — including the
bottom one. A glyph whose flat bottom sat at y=0 lands at y≈−delta/2. In a merged font
where the other script is copied unmodified, the two drift apart in proportion to the
weight change:

```
TH-Aeonik   Air +8   Thin 0   Regular -1   Medium -6   Bold -14   Black -28
```

**Why:** the sign flip is the diagnostic. Thinned weights float *above* the baseline
and emboldened ones sink below it, monotonically. Nothing else in a scale → embolden →
mark-adjust pipeline produces that signature, so it identifies `changeWeight` as the
cause without bisecting the build.

**How to apply:** after any synthetic weight change, re-seat the modified script by
measuring flat-bottomed glyphs only — round ones overshoot ~10 units and bias the
median. Translate the **bases and their GPOS base anchors** rigidly; do **not**
translate the marks, because a mark renders at `base_origin + base_anchor −
mark_anchor` and so already follows the base. Moving marks too moves them twice. A
rigid base+anchor translation leaves mark clearance mathematically unchanged, so it
composes safely with [[thai-mark-clearance-vs-pixel-grid]].

The defect scales with weight *and* point size, so body-text QC will not show it —
look at heavy weights at heading sizes. It survived five QC rounds here because every
check compared each script against its own source and nothing measured position
*across* scripts; see [[verify-what-the-test-asserts]].
