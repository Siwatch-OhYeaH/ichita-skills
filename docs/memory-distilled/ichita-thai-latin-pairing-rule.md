---
name: ichita-thai-latin-pairing-rule
description: "ICHITA brand rule for merged Thai/Latin fonts — Thai is sized to the Latin x-height and weight-matched by measured stem, with Latin as the reference in both"
metadata: 
  node_type: memory
  type: project
  originSessionId: d53cf7f9-f6b3-498c-b3de-1083b5f85c67
  modified: 2026-08-03T16:59:24.292Z
---

Siwatch's stated rule for combining Thai with the brand's Latin faces: **use the Latin
size as the standard, and scale Thai so `ก` matches the height of `a`.** Their phrasing
— "type Aeonik English at 10, Thai Bai Jamjuree must be 9" — measures out at 0.914 for
Aeonik (x-height 510 vs `ก` 558) and 0.968 for Slussen (540).

The corollary they raised separately, and which follows from the same principle:
**stroke weight is also matched against the Latin, not inherited from the Thai source.**
Bai's weight ladder does not align with Aeonik's or Slussen's, so pairing by matching
weight *name* is wrong — Aeonik Regular needs Bai **Medium** beside it.

**Amended 2026-08-03 (evening):** the *size* half of the rule is unchanged, but
"matched against the Latin" does not mean matched at a constant fraction. Siwatch
asked for the whole Thai ladder a step lighter — *"we may not need to make it as
light as the original to balance with the latin thickness"* — so the weight match
is now a taper running .93 at Air to .745 at Black, not a flat ~.915. Aeonik
Regular still takes Bai Medium; it now takes it thinned. See
[[taper-a-ladder-to-its-hard-cap]].

**But weight is matched at ~0.89-0.93 of the Latin stem, NOT 1:1.** Corrected
2026-08-03 after Siwatch reported Bold "too bold, too thick, hard to read". Thai has
loops where Latin has none, and a second constraint — counter aperture — binds before
the stem target on the heavy faces. See [[thai-weight-is-two-constraints]] for the
reference figures and the failure mode.

**Leading is the exception: it is NOT the Latin's.** This was the rule until
2026-08-03 and it turned out to be wrong. Aeonik's 1.20 em line box cannot hold two
consecutive Thai lines apart at Word's Single spacing — it is 334 units short — so
TH-Aeonik leads 1540 (+28.3%) and TH-Slussen 1600 (+5.8%), the measured minimum.
Siwatch accepted the trade: **set pure-Latin documents in Aeonik, not in the merged
face.** Size, weight and outlines still follow the Latin exactly. See
[[thai-line-clearance-is-a-document-setting]] for the measurements and for the wrong
turn taken first.

**Why:** Bai Jamjuree's Thai is drawn to sit beside Bai's own Latin. Transplanted
unchanged it is 9% oversized and 18–25% too light next to Aeonik or Slussen. The rule
exists so mixed Thai/Latin runs read as one typeface at one point size.

**Scope of "identical", stated by Siwatch 2026-08-02:** identical means the **Latin
outlines and the line box** — nothing else. Thai is deliberately not identical to Bai
Jamjuree, because Bai is itself a defective reference: *"Thai is broken along with Bai
Jamjuree itself."* Thai may be freely rescaled, reweighted and its marks repositioned.
**Sarabun is the nominated reference for correct Thai engineering** (`C:\Users\OhYeaH\
Downloads\Sarabun`) — compare against it, not against Bai. **But only for clearance
*within* a syllable.** For line-to-line clearance Sarabun is the worst font measured,
worse than Bai and worse than the merged faces; use Leelawadee UI there. See
[[thai-line-clearance-is-a-document-setting]].

**How to apply:** treat the Latin face being merged into as the reference for every
dimension — size, weight, and the line box. Never validate merged Thai against the
Thai source; that comparison is what [[verify-what-the-test-asserts]] is about. The
scale must be solved from the actual outline per weight, since emboldening changes the
glyph height. Bai cannot reach Aeonik's extremes (Air, Black) and that gap is a
documented limitation, not a bug to grind on.
