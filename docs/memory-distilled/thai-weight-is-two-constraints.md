---
name: thai-weight-is-two-constraints
description: "Matching Thai stems to the Latin 1:1 is wrong and destroys the counters — Thai runs ~0.89-0.93 of the Latin, and stem and counter aperture must both be measured"
metadata: 
  node_type: memory
  type: project
  originSessionId: d53cf7f9-f6b3-498c-b3de-1083b5f85c67
  modified: 2026-08-03T16:59:15.624Z
---

Two independent numbers decide whether a merged Thai weight is usable, and
measuring only the first is how TH-Aeonik-Bold shipped unreadable on
2026-08-02.

**1. Thai stem runs LIGHTER than the Latin, and the gap widens with weight.**
Thai carries enclosed loops (ก ถ ภ ศ ฃ ธ ฮ) where Latin carries none. Measured
2026-08-03 at 512 px/em on families whose Thai and Latin were drawn together:

```
Sarabun      ExtraLight .931  Regular .915  Bold .897  ExtraBold .890
Leelawadee   Regular    .921  Bold    .887
Tahoma       Regular    .959  Bold    .774
```

Not one is at 1.0. Targeting 1.0 makes Thai read heavier than the Latin *and*
spends the counter budget on stem width.

**2. Counter aperture — the widest circle fitting the tightest enclosed
counter.** `changeWeight` grows outlines in every direction, so a counter
bounded by two strokes loses ~1.2x the stem gain, then falls off a cliff when a
tighter glyph crosses below the previous minimum. On Bai Bold: +10 → 54.7,
+20 → 46.9, +31.7 → **11.0**. The floor is 46.5, which is what Sarabun
ExtraBold and Leelawadee Bold hold. 1 px at 11 pt is 68 units.

The two are independent: Bold measured a healthy 0.974 stem ratio while its
counters sat at 7.8 units — 0.11 px. `scripts/th_metrics.py` measures both;
`qc_th_fonts.py` checks 2 and 10 assert them.

**Why:** stem width is the obvious quantity and the wrong one on its own. Every
unit of synthetic embolden buys stem and spends aperture, so a face can match
the Latin perfectly and still render as solid ink.

**How to apply:** when a source ladder cannot reach the Latin, cap on the
aperture and let the stem fall short — light Thai beats blobs, and Tahoma Bold
at 0.774 shows even respected families make that trade. Watch for two traps:
Bai has nothing heavier than Bold, so Aeonik Bold and Black end up ~4 units
apart and can silently collapse into the same weight; and a counter can survive
emboldening and survive scaling but die under the combination, when rounding
lands two edges within a unit — invisible to bbox, contour-count and area
screens, so it has to be rendered and measured after scaling. See
[[ichita-thai-latin-pairing-rule]] and [[thai-mark-clearance-vs-pixel-grid]].

**Resolved 2026-08-03 (evening), and the resolution reverses the advice above
about pinning.** The Bold/Black collapse did happen — Siwatch reported it — and
it is not fixable from the Black end. It is fixed by tapering the whole ladder
toward the cap, at which point the cap stops being a shortfall to pin and
becomes the constant's stated value. Do NOT record a capped ratio in a side
table when the main constant can just say it; that side pin went stale and kept
passing. Full account in [[taper-a-ladder-to-its-hard-cap]], which also records
that the ratios here (Sarabun's .915 etc.) are only valid against the Latin they
were drawn for — Aeonik's Latin is 15.8% heavier than Bai's at Regular, so
borrowing the number directly over-weights our Thai.
