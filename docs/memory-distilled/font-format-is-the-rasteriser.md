---
name: font-format-is-the-rasteriser
description: "A merged font must ship in the SAME outline format as its Latin source — Windows renders CFF and TrueType through different engines, so identical outlines still render 16-20% lighter"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6df22ab0-8c6c-4b78-97e9-a0dbc4e3417f
  modified: 2026-08-04T09:23:55.834Z
---

Identical outlines are not enough. Windows rasterises CFF (`.otf`) and TrueType
(`.ttf`) through different engines, so a merged font in the other format cannot
render its Latin the way the source does. Measured 2026-08-04 in DirectWrite at
11 pt, same outlines, same advances, same cap height:

```
Aeonik      .otf/CFF    stems 2,1 px   ink 11,056
TH Aeonik   .ttf/glyf   stems 1,1 px   ink  9,310   -15.8%
Slussen     .otf/CFF    stems 2,2 px   ink 12,485
TH Slussen  .ttf/glyf   stems 2,2 px   ink  9,940   -20.4%
```

Siwatch read it as "TH Aeonik is slightly thinner than Aeonik, especially
Regular". It is worst at text sizes, so Regular shows it most. The CFF engine also
consults the Private dict's **BlueValues** (alignment zones), which a format flip
discards along with any charstring hint operators — Slussen carries 2712 of them,
Aeonik zero.

**Why:** four sessions of outline-level work could not see this, because every
check in the repo compared geometry and the geometry was never wrong. `TH-Aeonik`
shipped a 16% ink deficit that only a human eye caught.

**How to apply:** keep the merged font in the Latin source's format, and get the
Latin there by **taking the source's whole `CFF ` table and appending only the
other script's charstrings** — never by redrawing Latin through a pen, which
would discard hints and re-approximate the curves (0 of 656 Aeonik outlines
differ this way, against 656 of 656 for a redraw). Run the merge in `glyf` if the
pipeline needs it, then swap the CFF back last. Going back to CFF re-opens the
`hmtx`-vs-charstring advance divergence that once shredded every printed PDF, so
assert it instead: take every appended charstring's width from `hmtx`. Verify on
Windows — `scripts/win_latin_parity.py`; FreeType cannot see any of this. Related:
[[harfbuzz-cannot-validate-word]], [[windows-text-measurement-from-wsl]].
