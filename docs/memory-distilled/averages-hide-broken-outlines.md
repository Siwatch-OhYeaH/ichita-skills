---
name: averages-hide-broken-outlines
description: A median stem and a total-ink check both passed a glyph with hairline stems and an 8x-heavy bowl; only within-glyph spread caught it.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d621eeea-d5db-4286-bdb0-2b6325663e10
  modified: 2026-08-05T09:47:19.026Z
---

2026-08-05, building `scripts/th_greek.py`: extrapolating `μ` backwards past its
masters produced four faces (Air, Thin, AirItalic, ThinItalic) whose glyph had
**hairline stems and a bowl 8× heavier**, plus a truncated right stem. Visibly
broken on the specimen. Two measured checks passed it:

- **median stem** — the 0.4–0.6 sample band crosses the bowl, so the median landed
  on target;
- **total ink** — a too-heavy bowl and too-light stems cancel; Air measured 1.041
  of the twin's ink.

**Why:** both are averages. What was wrong was not the glyph's average weight but
that its weight was not *consistent within* the glyph. No average can see that.

**How to apply:** when checking a derived, interpolated or extrapolated outline,
measure a **distribution**, not a central tendency. `_stroke_spread()` takes
p90/p10 of every horizontal ink run in the whole glyph and compares it against the
reference glyph's own ratio. Kept faces scored 0.93–1.38, rejected ones 2.12–12.67
— a 3× gap, so the threshold is not delicately placed.

Two follow-ons worth keeping:

- The spread check then found **two more defects nobody had spotted** — `Ω` at Air
  and AirItalic. The eye reviewing the specimen went to the four broken `μ` and
  missed them. A check that only confirms what a human already saw is not doing
  work.
- Simple shapes survive long extrapolation; complex ones do not. `Δ` (9 points, all
  corners, three masters) was clean at every weight. `μ` has a bowl and only a
  two-master basis, and that is where bowl and stems part company.

Same family as [[verify-what-the-test-asserts]] and
[[verify-the-premise-against-the-artifact]]: the check was green, the artifact was
broken, and looking at the artifact is what found it.
