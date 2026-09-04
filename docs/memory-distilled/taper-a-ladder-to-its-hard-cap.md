---
name: taper-a-ladder-to-its-hard-cap
description: "A weight ladder whose top is hard-capped must taper toward the cap, not hold a flat ratio and cliff-drop — and a ratio borrowed from another family is only valid against the Latin it was drawn for"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9884d45d-ea2f-47ee-9f6a-c1e96026a93a
  modified: 2026-08-03T16:58:44.597Z
---

Two mistakes in one constant, both found on 2026-08-03 by Siwatch's eye, not by a
test.

**1. A borrowed ratio is only meaningful against the Latin it was drawn for.**
`WEIGHT_RATIO` tracked Sarabun's Thai/Latin stem ratios (.915 at Regular). But
Sarabun's .915 pairs its Thai with *Sarabun's* Latin. Aeonik's Latin is a much
heavier Regular — 85.9 against Bai's 74.2, +15.8%, and +20.4% at Medium — so
applying Sarabun's number to Aeonik drove our Thai to +13.9% over Bai's own
Regular. Siwatch: *"if you look at regular font between TH aeonik and
baijamjuree, ours TH aeonik is more bold than original one."*

**2. A capped top turns a flat ladder into a cliff.** Black is hard-capped at
.745 by the counter floor and cannot move (Bai's heaviest Thai *is* Bold). A
ladder holding .915 → .895 and then dropping to .745 left Thai Bold and Black
5.8 units apart — 0.09 px at 11 pt — against 33.2 units in the Latin. Tapering
the whole ladder toward the cap (.93 → .745, the shape Tahoma has for the same
reason: .959 Regular → .774 Bold) opened the pair to 21.5 units / 0.32 px.

**Why:** the cap is a property of the source, so it is the *fixed* end of the
ladder. Treating the light end as fixed and letting the top absorb the whole
error puts the entire discrepancy in the one gap users read as "same weight".

**How to apply:** find the hard constraint first, state it in the constant itself,
and shape everything else toward it. Then the exemption tables empty out — pinning
Black's shortfall in a separate `CAPPED_STEM_RATIO` was recording a lie the main
constant told, and one of those pins was stale while still passing
([[verify-what-the-test-asserts]]). Two free wins came with the taper: twelve of
fourteen faces now *thin* Bai instead of emboldening it, and thinning opens
counters where emboldening closes them ([[thai-weight-is-two-constraints]]) — so
the aperture and mark-clearance floors both stopped binding. Watch the
second-order effect: a thinner consonant is a smaller obstacle, so the
mark-clearance lift settles *higher* and the line box has to grow, not shrink
([[thai-line-clearance-is-a-document-setting]]). Also measured and rejected —
FontForge `changeWeight(counter_type="retain")` is no better than the default, and
Sarabun as the Thai source is *worse* than Bai because its ExtraBold already sits
on the aperture floor with no headroom. See [[ichita-thai-latin-pairing-rule]].
