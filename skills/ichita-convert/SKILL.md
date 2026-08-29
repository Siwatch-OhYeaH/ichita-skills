---
name: ichita-convert
description: Convert documents between Word, Markdown, PDF and HTML with ICHITA branding intact, and merge a hand-edited DOCX back into the Markdown record. Use when reading a client RFP, a returned DOCX or a supplier PDF into context cheaply, when producing a branded DOCX/HTML/PDF from Markdown, or when a colleague has edited a document in Word and the change needs to come back.
---

# ichita-convert

**Markdown is the record.** Everything inbound becomes Markdown; everything
outbound is rendered from it. A DOCX edited and left on someone's desktop is
not the record — hand it back and reconcile it.

```bash
python3 scripts/convert.py IN OUT [options]
python3 scripts/convert.py reconcile EDITED.docx CURRENT.md [--accept theirs|ours|interactive]
```

The extension pair picks the route; anything else chains through Markdown.

| from ↓ / to → | md | docx | html | pdf |
|---|---|---|---|---|
| **md** | — | branded DOCX | branded HTML | via HTML |
| **docx** | pandoc | rebrand | chain | chain |
| **html** | markdownify | branded DOCX | — | chromium / weasyprint |
| **pdf** | pymupdf + figures | chain | chain | — |

## The three rules colleagues get wrong

All three are the same species: **a silent substitution that produces a file
which looks fine.**

1. **Print to PDF, never Save as PDF.** Office refuses to embed OpenType-CFF,
   so Save-as-PDF silently swaps our `.otf` faces for Calibri — and still
   lists them as embedded. Use LibreOffice headless or Microsoft Print to PDF;
   numbers in `reference/pdf-delivery.md`.
2. **Never render a Claude-designed HTML with weasyprint.** It does not execute
   JavaScript, and those documents build themselves with it. You get a valid
   A4 PDF of the loading placeholder, at exit code 0. `html2pdf.py --engine
   auto` (the default) routes those to Chromium — don't force `weasyprint`.
3. **Hand your file back if you want the change kept.** `reconcile` shows the
   difference and makes you choose. It never overwrites silently.

## What is worth knowing before you read further

- **Inbound is where the token saving is.** A 49 KB DOCX reads as 2.4 KB of
  Markdown, a 129 KB PDF as 2.4 KB. `convert.py` prints the ratio.
- **The face follows the document's language** — English-only → Aeonik
  (line box 1200), any Thai → TH Aeonik (1537). Both the DOCX and the HTML
  emitters decide from the content and log it. Do not override without a
  reason; `docs/THAI-LATIN-FONT-ENGINEERING.md` §1.
- **Every rule in `md_clean.py` came from a measured defect** and has a test.
  Adding one without a measurement is guessing.
- **Born-digital PDFs only.** No OCR. And do not hand a PDF to a model to
  "read" — pymupdf returns the exact character stream; a model paraphrases and
  re-types numbers.
- Brand CSS lives in `assets/brand/ichita.css`. Import it. Never re-declare
  `@font-face`, colours or page geometry in a document.

## Reference

Read only the one you need.

| File | When |
|---|---|
| `reference/inbound.md` | docx/html/pdf → md, figure extraction, what each leg loses |
| `reference/outbound.md` | md → docx/html/pdf, the language rule, brand CSS |
| `reference/reconcile.md` | the sidecar, three-way merge, conflict handling |
| `reference/pdf-delivery.md` | engine bake-off numbers, and why Save-as-PDF is banned |

## Verify

```bash
python3 tests/test_md_clean.py     # 27 unit tests, one per cleaning rule
python3 tests/test_roundtrip.py    # 23 end-to-end, needs pandoc + LibreOffice + chromium
```

The round-trip test converts twice on purpose. Every defect this pipeline has
had compounds, so pass one proves nothing.
