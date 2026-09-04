---
name: powerpoint-ignores-font-metrics
description: "PowerPoint's single line spacing is a fixed 1.2 em for every font, so no font metric can fix Thai line collisions in a deck."
metadata: 
  node_type: memory
  type: reference
  originSessionId: d621eeea-d5db-4286-bdb0-2b6325663e10
  modified: 2026-08-05T09:47:10.115Z
---

Measured 2026-08-05 via PowerPoint COM, five installed families whose line boxes
span 1200–1697 units:

```
font            box    Word    PowerPoint
Aeonik         1200    1197          1200
Bai Jamjuree   1250    1250          1200
Segoe UI       1330    1329          1200
Slussen        1596    1598          1200
Gabriola       1697    1697          1200
```

Word tracks every box. PowerPoint returns 13.200 pt at 11 pt for all five —
exactly 1.2 × the point size. `TextRange.BoundHeight` is 13.200 / 26.400 / 79.200
for 1 / 2 / 6 lines in every font: perfectly linear, no font-dependent term.

**Bound on the claim:** this proves `BoundHeight` carries no font-dependent term.
Strong evidence that layout is 1.2 em, not proof — proof needs a rendered slide
measured in pixels. Not done.

Consequences for [[one-font-one-line-height]] work:

- A mixed-language deck does **not** inherit TH Aeonik's +28% leading. The cost of
  a tall line box is Word and Excel only.
- **Thai in a deck at single spacing will collide.** 1.2 em is 1200 units against
  the 1537 the Thai measured out at — the same 337-unit shortfall that produced
  the 2026-08-04 defect in Word. The font cannot fix it; a Thai deck needs
  explicit line spacing set on the text.

This is the one place where [[thai-line-clearance-is-a-document-setting]] is
genuinely true, and it is not a choice — PowerPoint leaves no font-side lever.

Excel is a third rule again: autofit row height was Aeonik 14.50 pt vs Slussen
21.00 pt, a 1.448 ratio against a 1.330 box ratio. There is a padding term no
metric field accounts for, so `scripts/win_office_pitch.py` reports Excel rather
than asserting a derived number.

Measure with `scripts/win_office_pitch.py`, which drives all three via COM from
WSL — see [[windows-text-measurement-from-wsl]].
