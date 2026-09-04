---
name: one-font-one-line-height
description: "Per-script line spacing is impossible in a merged font — Word's Latin/Complex-Script font pair is the only mechanism, and it also makes the Latin literally identical"
metadata: 
  node_type: memory
  type: project
  originSessionId: 63f4921f-6c62-49b0-921e-98c108550946
  modified: 2026-08-05T09:48:16.778Z
---

Siwatch, 2026-08-04: TH-Aeonik must be a drop-in Aeonik replacement — *"any other thing
beside thai character should be identical"* — and then, sharpened: *"make sure it only
apply on Latin, and when we type both language in same line, it is allow to wider the
space so that thai characters all fit in line, no overlap."*

**A single font cannot do this.** One font has one `hhea`, so one line height for every
line it sets, Latin-only or not. TH-Aeonik's 1540 box gives Latin-only lines +28.3% over
Aeonik's 1200 — which is the defect he screenshotted (measured off the screenshot at
+30%, and the two blocks' pitch ratio matched 1540/1200 = 1.283).

**Word's two font slots are the mechanism.** Word takes line height from the fonts
actually used in the line, and resolves Latin and Thai through separate slots. Measured
in Word at 11 pt Single, baselines from its own PDF export:

```
Aeonik                                   Latin-only  13.20 pt (1.200 em)
TH Aeonik (merged, both slots)            every line  16.92 pt (+28.2%)
ascii=Aeonik + cs=TH Aeonik               Latin-only  13.20 pt   <- identical
ascii=Aeonik + cs=TH Aeonik               with Thai   16.92 pt   <- widens, fits
```

So the answer to his separate question — can Aeonik be the Latin fallback and a Thai font
the Thai fallback — is yes, and it is the same fix. It costs nothing in Thai quality:
TH-Aeonik still supplies all the Thai, only its unused Latin steps aside. It also retires
the open "TH-Aeonik Latin looks slightly different" item for free, because the Latin then
*is* Aeonik, hinting and all.

**His documents were not configured for it.** `testpage.docx` Normal style read
`Latin=TH Aeonik, CS=+Body CS, Size=11, SizeBi=14`, and the theme's CS font was empty —
so his Thai was rendering in a system fallback two points larger, bypassing every bit of
the harmonisation work. That, not the merged font, is why he saw the line widen when he
switched to Thai.

**Why:** the merged-font architecture was chosen to make Thai+Latin one selectable
typeface, and it does that — but it structurally cannot give two line heights, so
"identical to Aeonik on Latin" and "room for Thai" are only jointly satisfiable across
two fonts. Reaching for a font-side fix here wastes a build cycle.

**How to apply:** set the style's Latin font and Complex Script font separately (in
`Normal.dotm` for zero per-document work), and always pin `SizeBi` to `Size` — they are
independent and Word's default leaves them apart. Related:
[[ichita-thai-latin-pairing-rule]], [[thai-line-clearance-is-a-document-setting]],
[[windows-text-measurement-from-wsl]].

**Two operational traps found while implementing it:**
- **The ribbon font box cannot express the split.** It calls `Font.Name`, which
  overwrites the Latin AND the Complex Script slot at once (verified: after
  `Font.Name='TH Aeonik'` both `NameAscii` and `NameBi` read `TH Aeonik`). So
  "replace Aeonik with TH Aeonik" via the ribbon always returns to the wide pitch.
  Only the Ctrl+D Font dialog, a style, or COM can set the slots independently.
- **`NormalTemplate.OpenAsDocument()` hangs while Word is running** — no dialog, no
  error, blocks forever and has to be killed. Word holds `Normal.dotm` for the whole
  session. Use Ctrl+D > Set As Default from inside Word instead.
  `scripts/setup-word-th-fonts.ps1 -Template` now refuses when WINWORD is running.

**SUPERSEDED as the delivered answer, 2026-08-04.** Siwatch rejected the two-font
route outright: *"that's the exact situation, and I want you to solve it with the font
engineering, not by set up two separate fonts."* The physics above still hold — one
font is still one line height. Do not re-propose the Latin/Complex-Script split
*inside one document*; he has ruled on it.

**SUPERSEDED AGAIN, 2026-08-05, and this time the conflict is dissolved rather than
traded around.** The 08-04 conclusion drawn here — "set the box to Aeonik's 1200 and
make the Thai FIT inside it" — is **wrong and was measured to be impossible**
([[thai-mark-size-is-the-slack]] is FALSIFIED: 1200 is unreachable for Thai at any
mark size). It shipped a 262-unit Thai overlap.

The answer is neither of the two things considered here. **The face is chosen by the
document's language**: English-only documents use *actual Aeonik*, mixed ones use TH
Aeonik at a box sized to what the Thai needs (1537). Nothing then has to match
Aeonik's box, so nothing has to fit inside it. See
[[font-follows-the-document-language]].

What survives from this note: the physics (one font, one `hhea`), the measurement
table, and both operational traps — the ribbon font box collapsing the two slots, and
`NormalTemplate.OpenAsDocument()` hanging while Word runs. Those are still true and
still worth knowing.
