---
name: changeweight-insets-every-edge
description: "FontForge changeWeight moves horizontal edges too, so a thinned face is short AND lifted off the baseline."
metadata: 
  node_type: memory
  type: project
  originSessionId: e3dcb374-3d51-4830-81a8-031f01bcf06b
  modified: 2026-08-09T10:18:45.848Z
---

FontForge's `changeWeight` insets the outline by roughly half the requested amount on
**every** edge, horizontal ones included. Thinning Aeonik Black by −18.4 moved `x` from
0..516 to 9..507 — baseline +9, x-height −9. Falsified first: the glyf intermediate
losing CFF blue zones (it does, but `custom_zones` changes nothing), `type="LCG"` vs
`"auto"` (identical), and cu2qu rounding (the inset scales with the amount).

**Why:** it shipped in Aeonik Book from 2026-08-07 to 2026-08-09 — 2.7% shorter than the
ladder, floating 7 units up — and went unseen because the merge scales the Thai to the
Latin's x-height, so both scripts agreed with each other inside the font while both were
wrong. Nothing measured the Latin against its own base. The 08-07 response was to lower
Book's Latin target 74.0 → 71.9, which fixed the ratio and preserved the shrink.

**How to apply:** for any synthesised weight, measure the vertical band against the base
face and restore it (`restore_vertical()` in `build_aeonik_semibold.py`); it is a no-op
on a grown face, which is worth asserting. Never re-target a weight to compensate for a
shrink — fix the shrink. Growing spends counter, thinning opens it, so thin from the
heavier neighbour when a target can be reached from either side. See
[[verify-what-the-test-asserts]] and [[synthetic-weight-moves-the-baseline]].
