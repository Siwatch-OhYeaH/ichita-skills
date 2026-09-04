---
name: word-pdf-export-drops-cff
description: "Word's PDF export substitutes per-user-installed CFF/.otf fonts to Calibri while embedding .ttf fine — screen layout is unaffected, so only the PDF deliverable is wrong"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9a53e104-c414-4086-8afa-b77c1ac8fb8a
  modified: 2026-08-04T09:49:45.505Z
---

Measured 2026-08-04 on Siwatch's machine, all fonts installed per-user in
`%LOCALAPPDATA%\Microsoft\Windows\Fonts`. Word COM `ExportAsFixedFormat`
embedded by format, not by family:

    Aeonik        .otf CFF    substituted -> Calibri/Cambria
    TH Aeonik     .otf CFF    substituted
    Bai Jamjuree  .ttf glyf   embedded
    TH Slussen    .ttf glyf   embedded

**Screen layout is NOT affected.** Same string, `Range.Information(5)` end-x in Word:
Calibri 198.00, Aeonik 206.75, TH Aeonik 206.75, Bai Jamjuree 208.90. Aeonik is
laid out with its own metrics, so Word resolves and uses the `.otf` normally —
only the PDF embed step falls back. `Aeonik` fails too, so this predates the
2026-08-04 TrueType->CFF conversion and is not caused by it.

**Why:** it splits "the font is broken" from "the PDF pipeline is broken". A
Calibri-only `pdffonts`/`get_fonts` listing after a Word export is NOT evidence
that the font failed to install or resolve — I nearly reported a working font as
still-defective on exactly that basis.

**How to apply:** never accept a Word-exported PDF's embedded-font list as the
acceptance measurement for a font fix. Measure layout instead —
`Range.Information(5)` on an identical string across candidate fonts separates
real layout from substitution in one run, and it works headless. Confirm any
format-shaped hypothesis against a second font of each format before believing
it. Related: [[font-format-is-the-rasteriser]],
[[windows-text-measurement-from-wsl]], [[verify-the-premise-against-the-artifact]].

**Open:** root cause of the embed failure is not established, and it affects every
branded PDF deliverable that routes through Word.
