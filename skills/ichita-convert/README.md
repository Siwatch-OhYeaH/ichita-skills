# ichita-convert

Moving documents between Word, Markdown, PDF and HTML without losing the brand
or the edits.

**If you read nothing else, read these two rules.**

---

## 1. Print to PDF. Never Save as PDF.

Word's *Save as PDF* cannot embed our fonts. Microsoft's own PDF writer refuses
OpenType-CFF, which is the format every ICHITA face ships in, so it quietly
swaps Aeonik and TH Aeonik for **Calibri** — and the file still claims our
fonts are embedded.

Nothing looks wrong. The document opens, the text is there, the layout is
close. It is simply not our typeface, and it goes out to a client that way.

Use **File → Print → Microsoft Print to PDF** instead. That is a print driver
and it never touches the part of Office that gets this wrong.

If you are generating the PDF from a script rather than from Word, use
LibreOffice — the numbers are in `reference/pdf-delivery.md`.

> One caveat for Thai documents: the `md → HTML → PDF` route produces a PDF
> that *looks* perfect but whose text layer has the Thai wrong, so searching
> and copy-paste return nonsense. For Thai, go through LibreOffice.

---

## 2. Hand your file back if you want the change kept.

The Markdown file is the record. The DOCX is a rendering of it — the way a
printout is a rendering of a spreadsheet.

Edit the DOCX all you like. Send it back when you are done:

```bash
python3 scripts/convert.py reconcile your-edited.docx the-record.md
```

It shows you exactly what changed on each side and asks what to keep. It never
overwrites anything on its own.

**A DOCX edited and left on someone's desktop is not the record.** The next
time anyone regenerates the document, those edits are gone, and nobody will
know they existed.

---

## Everyday use

```bash
# Read a client's document without it costing a fortune in context
python3 scripts/convert.py client-rfp.docx rfp.md
python3 scripts/convert.py supplier-datasheet.pdf datasheet.md

# Produce something branded
python3 scripts/convert.py proposal.md proposal.docx
python3 scripts/convert.py proposal.md proposal.pdf
python3 scripts/convert.py proposal.md proposal.html
```

The file extensions decide the route. Anything that is not a direct conversion
goes through Markdown automatically.

A 49 KB Word file becomes 2.4 KB of Markdown; a 129 KB PDF becomes 2.4 KB. The
command prints the ratio, because that saving is the reason this exists.

## Setup

```bash
bash install.sh
```

It will tell you if `pandoc`, `libreoffice` or `poppler-utils` are missing.
Those three are not Python packages and have to come from your package manager.

## For Claude, or whoever maintains this

`SKILL.md` is the entry point. `reference/` has one file per leg — inbound,
outbound, reconcile, PDF delivery — and each records what was measured, not
what was assumed. Every rule in `scripts/md_clean.py` came from a defect
observed on a real round trip and has a test in `tests/`.
