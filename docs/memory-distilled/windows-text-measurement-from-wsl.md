---
name: windows-text-measurement-from-wsl
description: "WSL can drive Windows' own text stack — GDI, DirectWrite and Word COM — so the target renderer IS measurable locally; stop treating Windows as unreachable"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 63f4921f-6c62-49b0-921e-98c108550946
  modified: 2026-08-03T18:27:35.287Z
---

`powershell.exe` is on PATH from WSL, which makes the shipping renderer directly
measurable. This partially retires the "measure locally, verify on Windows later"
split in [[harfbuzz-cannot-validate-word]] — three probes, all used on 2026-08-04:

**1. Render through GDI/Uniscribe and DirectWrite to PNG**, then Read the PNG.
`System.Drawing` (GDI) and `System.Windows.Media.DrawingVisual` +
`RenderTargetBitmap` (DirectWrite). Build Thai from codepoints
(`-join ($cps|%{[char]$_})`) — never literal Thai in the .ps1, PowerShell 5.1
mangles it without a BOM.

**2. Measure shaped advances.** `TextRenderer.MeasureText` (GDI) and
`FormattedText(...).WidthIncludingTrailingWhitespace` (DirectWrite). The
`FormattedText` overload is the **6-arg** one — passing `pixelsPerDip` throws on
.NET Framework. Ratio of x5 to x1 width is a clean drop/collapse test.

**3. Word's own layout via COM.** Read back what Word accepted
(`Font.NameAscii` / `NameBi` / `Size` / `SizeBi`) before trusting a result, then
`ExportAsFixedFormat(path, 17)` and measure baselines with PyMuPDF
(`span["origin"][1]`). `Range.Information(6)` returns **0** when
`Visible=$false` — no window means no layout — so export, do not query.

Two traps that cost a cycle each:
- **Word substitutes the font in the PDF while laying out with the real one.**
  Aeonik came back embedded as "Calibri" yet the pitch was 13.20 pt = exactly its
  1200 hhea box (Calibri's would be 13.43). Trust the metric, not the embedded name.
- **`SizeBi` is independent of `Size`.** His document had Size 11 / SizeBi 14, so
  every mixed-line measurement was inflated until it was pinned.

**Why:** four sessions were lost to defects invisible under HarfBuzz. They were
never actually unreachable — the acceptance renderer was one `powershell.exe`
away. Cross-checked: Word reported 13.20/16.92 pt and `qc_check_th_font_doc.py`
independently predicted 13.20/16.94.

**How to apply:** for shaping, line-height or font-resolution questions, measure
on Windows in the same session rather than deferring to Siwatch. Note the fonts
installed on Windows are a THIRD artifact layer and go stale silently — hash-compare
before believing any Windows result ([[rebuild-before-trusting-qc]]).
