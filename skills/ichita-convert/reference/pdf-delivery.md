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

| | LibreOffice headless | headless Chromium | md→html→weasyprint | Word Save-as-PDF | Word Print-to-PDF |
|---|---|---|---|---|---|
| Source route | DOCX | HTML | HTML | DOCX | DOCX |
| No non-brand font | **PASS** | **PASS** | **PASS** | **fails by design** | not measured |
| Thai NFC-identical | **PASS** 311/311 | **PASS** 132/132 | **FAIL** 135/132 | not measured | not measured |
| Renders scripted HTML | n/a | **PASS** | **FAIL, exit 0** | n/a | n/a |
| Measured line pitch | 15.4 pt at 10 pt = **1.54 em** | — | 16.23 pt | — | — |
| Font embedding | Type1C (CFF) | **Type 3** | CID Type 0C (CFF) | — | — |
| File size, same fixture | 123 KB | 93 KB | 48 KB | — | — |
| Keeps Word's layout | re-lays out | n/a | discards | yes | yes |
| Scriptable | yes | yes | yes | yes | **no, see below** |

**From DOCX: LibreOffice headless.** **From HTML: Chromium**, except for static
English-only pages where weasyprint is still better. Word's Save-as-PDF is
never acceptable.

The HTML route now picks its own engine — `html2pdf.py --engine auto`, the
default:

```
the HTML builds its DOM with script  ->  chromium    (weasyprint renders nothing)
the document contains Thai           ->  chromium    (weasyprint corrupts the text layer)
otherwise: static, English-only      ->  weasyprint  (real CID-CFF font program, smaller file)
```

Plus a behavioural backstop: after a weasyprint render, if the extracted text
is under 200 characters or contains a `noscript` string, the page is
re-rendered with Chromium and the substitution is reported. That catches shells
the marker list has not seen.

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

### weasyprint cannot render JavaScript, and says nothing

Reported by Miipan, 2026-08-06, from three real client deliverables. This is
the worst failure mode in the skill because it is completely silent.

A Claude-designed standalone HTML is a thin shell: the static markup is a
loading placeholder, and the real document — plus the brand CSS, the fonts and
a React runtime — arrives gzip+base64 encoded and is mounted by script on
`DOMContentLoaded`. There is no static markup to render.

weasyprint does not execute JavaScript. Measured on `js-shell.html`:

```
weasyprint 68.1
  exit code   : 0
  output      : 1 page, A4, 4,233 bytes
  text layer  : "This page requires JavaScript to display."
  key figures : 1,000.00 -> 0   805.71 -> 0   928.94 -> 0
                6,318.37 -> 0   Beer Thai -> 0
chromium
  key figures : all 5 present, placeholder gone
```

A valid, well-formed, brand-sized PDF containing none of the document, and
nothing in the exit status, the page count or the file type reveals it. **Same
species as Word's Save-as-PDF above** — nothing looks wrong until you compare
it to the source.

### weasyprint's Thai text layer is wrong

Invisible in the render, same as the above.

Every `า` (U+0E32) extracts from a weasyprint PDF as `ำ` (U+0E33). **The
glyphs are correct** — the page reads perfectly and a crop at 160 dpi shows
`ระบบนี้ออกแบบสำหรับน้ำตาลทรายดิบ` exactly right. Only the `ToUnicode` map is
wrong, so search, copy-paste and any downstream extraction return corrupted
Thai.

**It is worse than a substitution.** Measured on `thai-static.html`, 132
source characters:

```
             chars     า        ำ        U+0E49
source        132      6        5        6
weasyprint    135      0       11        4        FAIL
chromium      132      6        5        6        PASS
```

The `U+0E49` tone mark is **dropped**, not remapped — and `U+02D7` appears in
its place, which is the same artifact class as the corrupted May 2026 PDF
(`น˗˓าตาล`). The character count goes *up* while information is lost.

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
