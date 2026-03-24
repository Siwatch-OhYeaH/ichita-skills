---
name: ichita-docx
description: "Use when creating Ichita-branded documents, converting Markdown to branded DOCX, or rebranding existing documents to Ichita style. For general DOCX editing, tracked changes, or creating non-branded documents, use the base docx skill instead."
---

# Ichita DOCX — Branded Document Creation

> This skill extends the base `docx` skill with Ichita brand identity.
> For general DOCX editing, tracked changes, comments, and OOXML manipulation, use the base `document-skills:docx` skill.

## Prerequisites

```bash
bash skills/ichita-docx/install.sh
# or: pip install -r skills/ichita-docx/requirements.txt
```

**Required**: `python-docx` (DOCX creation/editing)
**Optional**: `LibreOffice` (PDF conversion), `Poppler` (PDF→images)

---

## Quick Reference

| Task | Action |
|------|--------|
| Create branded DOCX from Markdown | `python scripts/md_to_docx.py INPUT.md OUTPUT.docx` |
| Create branded DOCX from HTML | `python scripts/html_to_docx.py INPUT.html OUTPUT.docx` |
| Rebrand existing DOCX to Ichita | `python scripts/rebrand_docx.py INPUT.docx OUTPUT.docx` |
| Edit DOCX XML directly | Use `document.py` + `utilities.py` (see below) |
| General DOCX editing/creation | Use base `document-skills:docx` skill |

> **Script paths** are relative to this skill directory (`skills/ichita-docx/`). Run from there, or prefix with the full path from the plugin root.

---

## Brand Architecture

```
ichita-defaults.md       <- source of truth (human-readable)
        |
    ICHITA_BRAND dict    <- data only (docx_helpers.py)
        | passed to
    docx_helpers.py      <- generic functions, brand-agnostic
        | used by
    md_to_docx.py        <- markdown -> branded docx
    rebrand_docx.py      <- transform existing docx -> branded
```

**Brand config**: Read [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md) for full color palette, typography, and visual identity.

---

## Workflow A: Markdown to Branded DOCX

Convert Markdown content to a professional Ichita-branded document.

```bash
python scripts/md_to_docx.py INPUT.md OUTPUT.docx
```

### Options
- `--no-logo` — skip the Ichita logo header
- `--font NAME` — override font (default: auto-detects Aeonik -> Calibri)
- `--margin CM` — page margin in cm (default: 2.5)

### What it does
- Applies Ichita brand colors and typography from `ichita-defaults.md`
- Auto-detects Aeonik font (checks Linux, macOS, and Windows via WSL)
- Handles: headings (H1-H4), tables, code blocks, bold/italic, bullet/numbered lists, blockquotes, horizontal rules, links
- Adds Ichita logo + blue accent line in header

### Font detection
The script checks for Aeonik across all platforms:
- **Linux/Ubuntu**: `fc-list`, `~/.local/share/fonts/`, system font dirs
- **macOS**: `~/Library/Fonts/`, `/Library/Fonts/`
- **Windows via WSL**: `/mnt/c/Windows/Fonts/`, user AppData font dirs

If Aeonik is found on Windows but not registered in Linux, it will:
- Use "Aeonik" in the DOCX (renders correctly when opened in Word on Windows/Mac)
- Warn that LibreOffice preview may substitute the font
- Suggest: `cp fonts/*.otf ~/.local/share/fonts/ && fc-cache -f`

---

## Workflow A2: HTML to Branded DOCX

Convert HTML content to an Ichita-branded document. Supports custom logos and footers.

```bash
python scripts/html_to_docx.py INPUT.html OUTPUT.docx
```

### Options
- `--logo PATH` — custom logo image for header (default: Ichita wordmark)
- `--footer TEXT` — footer text (default: "www.ichita.co.th")
- `--font NAME` — override font (default: auto-detects TH Aeonik → Aeonik → Calibri)
- `--no-logo` — skip logo in header
- `--margin CM` — page margin in cm (default: 2.5)

### What it does
- Parses HTML elements: headings (h1-h4), tables, lists, bold/italic, links, images, code blocks, blockquotes
- Applies Ichita brand colors and typography
- Tables: dark header (#263338), alternating rows (#EFF2F3)
- Header: logo + blue accent line (customizable via --logo)
- No external HTML parsing dependency (uses stdlib html.parser)

---

## Workflow B: Rebrand Existing DOCX

Transform documents from other companies/templates into Ichita brand identity. Handles any DOCX — no source-specific assumptions.

```bash
python scripts/rebrand_docx.py INPUT.docx OUTPUT.docx
```

### Options
- `--no-title-page` — skip title page redesign (keep original cover)
- `--font NAME` — override font
- `--logo PATH` — custom logo path (default: Ichita wordmark)

### What it does
- Deep-copies source document (preserves all content, tables, merged cells, images)
- Restyles all paragraphs: section headings get left accent bar, body gets brand font
- Restyles all tables: dark header rows, alternating row shading, brand borders
- Detects heading levels from text patterns (numbered sections, subsections, captions)
- Redesigns title page with centered title + blue accent band
- Sets proper margins (2.5cm portrait, 1.0cm landscape)
- Squeezes wide tables to fit page width
- Adds Ichita logo header with blue accent line
- Removes source header/footer references

### Visual check
```bash
soffice --headless --convert-to pdf OUTPUT.docx
pdftoppm -jpeg -r 150 OUTPUT.pdf page
```

---

## Direct XML Editing (document.py + utilities.py)

For advanced edits beyond what md_to_docx or rebrand_docx provide, use the Document library:

- **`document.py`** — OOXML Document API (load, manipulate, save XML)
- **`utilities.py`** — XML utility functions (namespace handling, element creation)

These are lower-level tools for when you need direct XML control over Ichita-branded documents. For general OOXML editing workflows (unpack/pack/validate), use the base `document-skills:docx` skill.

---

## Dependencies

```bash
pip install python-docx defusedxml
```

- **python-docx**: Document creation and rebranding
- **defusedxml**: Secure XML parsing
- **LibreOffice**: `soffice --headless` for PDF conversion (visual check)
- **Poppler**: `pdftoppm` for PDF to images
