---
name: word-thai-sequence-check
description: "Repeated/invalid Thai vowels refusing to type in Word is Word's Options.SequenceCheck, not a font defect — check the setting before touching GDEF"
metadata: 
  node_type: memory
  type: project
  originSessionId: 63f4921f-6c62-49b0-921e-98c108550946
  modified: 2026-08-03T18:27:17.235Z
---

Siwatch reported 2026-08-04 that `าาาาา` / `เเเเเ` "has bug when I try to type them
more than one ... might be locked by some rules behind TH Aeonik font." The lock was
**Word**, not the font: `Application.Options.SequenceCheck = True` — Office's Thai Input
Sequence Checking, which *blocks the keystroke* for orthographically invalid Thai.
Repeated spacing vowels are exactly what it rejects. It is font-independent and on by
default once Thai is an editing language (his Kedmanee layout `0000041e` is installed).

Read/flip it via COM; there is no registry value until it is changed:

```powershell
$w=[Runtime.InteropServices.Marshal]::GetActiveObject("Word.Application")
$w.Options.SequenceCheck = $false     # Word Options > Advanced > Thai
```

**Why:** the same symptom has a real font-side cause that this project already fixed —
GDEF class 0 on spacing vowels ([[harfbuzz-cannot-validate-word]]) — so the report reads
as a regression of that fix. It is not. Measured on all 18 shipped faces AND on the
files installed on his PC: vowels 10/10 GDEF BASE, U+25CC present, OS/2 Thai bits and
`thai` script tags byte-equivalent to Sarabun, and DirectWrite returns **exactly 5.00x**
the single-glyph width for five repeated vowels. Build history pins it further:
`ea0dce2` was 0/10 BASE, `619d310` fixed it, every build since holds. Two distinct bugs,
one symptom.

**How to apply:** when Thai "will not type", separate *typing* from *rendering* first —
insert the same string programmatically or measure the shaped advance. If insertion works
and typing does not, it is input validation (a Word setting), and no font change can
reach it. Only if the glyphs are wrong once inserted is it the font. Check
`SequenceCheck` before re-deriving anything about GDEF. Related:
[[windows-text-measurement-from-wsl]], [[verify-the-premise-against-the-artifact]].
