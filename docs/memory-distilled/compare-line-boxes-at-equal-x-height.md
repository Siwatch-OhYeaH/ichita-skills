---
name: compare-line-boxes-at-equal-x-height
description: "A font's line box is meaningless without the x-height it is drawn against — TH Baijam's 1200 beat TH Aeonik's 1537 and was the worse font."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b6369690-31d0-429f-9d4e-cf366f216521
  modified: 2026-08-06T08:34:50.555Z
---

TH Baijam was offered as a Thai font that fixes the leading problem: Word box
**1200**, identical to Aeonik, against TH Aeonik's 1537. The number is real and
the conclusion is backwards. Its Latin x-height is **339** against Aeonik's
**510** — the whole typeface is drawn at ~2/3 scale inside the em. Set so the
Thai matches TH Aeonik's Thai it leads 17.00 pt against 16.91, a wash; set so
the Latin matches Aeonik's, 19.86 pt against 16.91. Its Thai stack needs
**2.950** of its own x-heights where TH Aeonik's needs **2.820** — the harder
font to fit, ranked best by the raw box.

**Why:** a line box is a count of font units, and units are only comparable
between fonts drawn at the same scale. Our faces are comparable to each other
because they all carry Aeonik's or Slussen's Latin. A third-party font shares
none of that, so its box number carries no information until it is divided by
something physical — x-height, or the size you would actually set it at.

**How to apply:** never compare two fonts' boxes, stacks or mark clearances
without normalising by x-height first, and never accept "smaller box" as
"tighter leading" from a font outside the family. The size-invariant quantities
are `box / x-height` and `stack / x-height`; compute both before forming a view.
The same error in other coats: [[name-the-benchmark-before-the-ratio]] (bolder
than *what*), [[ichita-thai-latin-pairing-rule]] (Thai sized to the Latin
x-height, not to the em). Related: [[thai-mark-clearance-vs-pixel-grid]], where
the physical quantity is pixels rather than units, for the same reason.
