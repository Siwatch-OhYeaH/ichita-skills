# PDF delivery — which engine, and why

Measured 2026-08-06 on `tests/fixtures/mixed.md` → branded DOCX → PDF. Thai and
Latin, a five-row table, a bullet list, a numbered list, tone marks over
ascenders.

Re-run with:

```bash
python3 scripts/pdf_bakeoff.py FIXTURE.docx OUTDIR --source FIXTURE.md --png
```

---

## Results

| | LibreOffice headless | md→html→weasyprint | Word Save-as-PDF | Word Print-to-PDF |
|---|---|---|---|---|
| No non-brand font | **PASS** | **PASS** | **fails by design** | not measured |
| Thai NFC-identical | **PASS** 311/311 | **FAIL** 309/311 | not measured | not measured |
| Measured line pitch | 15.4 pt at 10 pt = **1.54 em** | 16.23 pt | — | — |
| Pages | 2 | 1 | — | — |
| File size | 123 KB | 48 KB | — | — |
| Keeps Word's layout | re-lays out | discards | yes | yes |
| Scriptable | yes | yes | yes | **no, see below** |

**Use LibreOffice headless for a Thai delivery PDF.** It is the only engine
measured here that gets both the fonts and the text layer right.

---

## The finding that decides it

### Word's Save-as-PDF cannot embed CFF

Microsoft policy, not a bug. Office refuses to embed OpenType-CFF, so our
`.otf` faces are silently replaced with Calibri — **and the file still lists
them as embedded**. Nothing about the result looks wrong until you compare it
to the source.

Documented at `docs/THAI-LATIN-FONT-ENGINEERING.md:339`. It is not run as an
engine here because the answer is known and the measurement would only confirm
it.

**Microsoft Print to PDF is a different path.** It is a print driver, so it
never touches Office's font-embedding subsystem, and it is the path the font
work hardened.

### weasyprint's Thai text layer is wrong

The serious one, and it is invisible in the render.

Every `า` (U+0E32) extracts from a weasyprint PDF as `ำ` (U+0E33). **The
glyphs are correct** — the page reads perfectly and a crop at 160 dpi shows
`ระบบนี้ออกแบบสำหรับน้ำตาลทรายดิบ` exactly right. Only the `ToUnicode` map is
wrong, so search, copy-paste and any downstream extraction return corrupted
Thai.

The mechanism: HarfBuzz decomposes ำ into ํ + า for shaping, so the า glyph is
reached from two source codepoints. The `ToUnicode` CMap is keyed by glyph id,
and the last write wins — the whole subset ends up with a single entry,
`<02c1> <0e33>`.

Not the font's fault: TH Aeonik's cmap has exactly one codepoint per glyph,
checked with fontTools, and zero Thai glyphs reachable from more than one.

**Pre-decomposing ำ into ํ + า in the source does not fix it.** Tried: the
extracted text then comes back decomposed, and NFC will not recompose it
because U+0E33 has no canonical decomposition. 319 characters out for 311 in.

Consequence: weasyprint is fine for an English-only delivery PDF and for any
Thai document where the PDF only has to be *looked at*. It is not acceptable
where the Thai has to be searchable, copyable, or read back into the record.

### Word COM is not automatable unattended from WSL

Two attempts on 2026-08-06, both from a `powershell.exe` COM session with
`Visible = false`. Both hung past a 100-second timeout with no output, and
both left a **windowless `WINWORD.EXE`** behind — invisible in the taskbar and
Alt-Tab while holding font files open. Almost certainly a modal dialog that
cannot be seen because the automation hid the window.

That is precisely the §9 failure: an orphan blocks a font install while the
applications look closed. Both were cleaned up:

```bash
# Before every attempt, and after every failure:
powershell.exe -NoProfile -Command "Get-Process WINWORD,POWERPNT,EXCEL \
  -ErrorAction SilentlyContinue | Select Name,Id,MainWindowHandle"
# MainWindowHandle 0 = orphan, safe to kill:
powershell.exe -NoProfile -Command "Get-Process WINWORD | \
  Where-Object { \$_.MainWindowHandle -eq 0 } | Stop-Process -Force"
```

`pdf_bakeoff.py` therefore skips the Word engine and says why. **Run it
attended, with Word visible**, if the Word-layout PDF has to be measured.

---

## Engine notes

### LibreOffice re-resolves the Latin font slot

The DOCX sets `w:ascii`, `w:hAnsi` and `w:cs` to `TH Aeonik` on every run —
verified in the XML — but the resulting PDF embeds `Aeonik-Regular` for the
Latin runs and `TH-Aeonik-*` for the Thai. TH Aeonik is installed and
`fc-match "TH Aeonik"` resolves correctly, so this is LibreOffice's own
script-slot handling, not a missing font.

Both are brand fonts, so it passes the substitution check, and the **measured
pitch stays a uniform 1.54 em across the whole document** — the paragraph
pitch came from TH Aeonik even on the Latin lines. Noted rather than fixed:
Word on Windows is the acceptance renderer, not LibreOffice.

### The pitch number is a useful cross-check

1.54 em measured out of the PDF against TH Aeonik's declared 1537/1000 line
box is an independent confirmation that the font's own metrics are driving the
layout. Read it from the PDF, never from a metric field — which field a
renderer uses depends on the outline format (§2 and §7 of the font doc).

---

## What to tell a colleague

> Print to PDF. Never Save as PDF. Save-as-PDF silently swaps the ICHITA fonts
> for Calibri and the file still looks fine.

If they are producing the PDF from a script rather than from Word, LibreOffice
headless is the answer:

```bash
soffice --headless --convert-to pdf --outdir OUT document.docx
python3 scripts/pdf_bakeoff.py document.docx OUT --source document.md
```
