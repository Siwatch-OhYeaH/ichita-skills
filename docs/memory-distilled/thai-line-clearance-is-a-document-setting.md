---
name: thai-line-clearance-is-a-document-setting
description: "SUPERSEDED conclusion — two Thai lines colliding is fixed in the FONT's line box, not the document, because users type in plain Word where no template applies"
metadata: 
  node_type: memory
  type: project
  originSessionId: d53cf7f9-f6b3-498c-b3de-1083b5f85c67
  modified: 2026-08-03T07:14:06.523Z
---

A Thai three-level stack over the next line's below-vowel does not fit a Latin line
box, and does not fit most Thai ones either. Baseline-to-baseline need vs the font's
own `hhea` box, worst shaped stack over worst tail, 1/1000 em:

```
Leelawadee UI  1330 / 1255   +75    <- the only one that clears
TH-Slussen     1512 / 1522   -10
TH-Aeonik      1200 / 1459  -259
Sarabun        1300 / 1582  -282    <- the "perfect engineering" reference
Bai Jamjuree   1250 / 1564  -314
```

**The title of this memory was my wrong conclusion, kept here as the correction.** I
first fixed this in the document layer (`w:lineRule="atLeast"` in the DOCX generator).
It could not work: Siwatch's acceptance test is *typing in plain Word*, where no
template applies. The measurement was right and the layer was wrong. TH-Aeonik's line
box is now 1540 (+28.3% over Aeonik) and TH-Slussen's 1600 (+5.8%).

**Why:** at Word's Single spacing the line box *is* the inter-line room — there is no
other source of it. The tempting counter-argument, that Thai marks are designed to
overflow into the leading above "where the Latin ascenders leave the space empty," is
true only for Thai over Latin. A Thai paragraph is Thai over Thai. Evidence that marks
are not *clipped* when they overflow says nothing about whether they *collide*.

**How to apply:** before choosing a layer to fix in, check which layer the user
actually exercises — generated documents and hand-typed documents are different
products. Measure line clearance separately from within-syllable clearance; a font can
be excellent at one and worst-in-class at the other, which is how Sarabun behaved (see
[[ichita-thai-latin-pairing-rule]]). Size the box as `worst_upper_stack +
|worst_lower_tail| + 75`, where 75 is both Leelawadee UI's own spare and about one
pixel at 11 pt / 96 dpi — see [[thai-mark-clearance-vs-pixel-grid]].
`scripts/thai_line_pitch.py` computes it. The document-side `atLeast` still matters for
the *split*-font path, where the Thai font keeps its own box. And when raising the box
inverts existing assertions, pin a **number**, not a relationship — see
[[verify-what-the-test-asserts]].
