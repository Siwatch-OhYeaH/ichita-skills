---
name: ichita-pdf
description: "Use when creating Ichita-branded PDF documents from HTML templates — executive briefs, memos, one-pagers. Renders HTML with weasyprint at print quality (300 DPI). For general PDF processing (merge, split, OCR, watermark), use the base pdf skill instead."
---

# Ichita PDF — Branded HTML→PDF Generation

> This skill creates print-quality branded PDFs from HTML templates using weasyprint.
> For general PDF processing (merge, split, extract, OCR), use the base `document-skills:pdf` skill.

## Quick Reference

| Task | Action |
|------|--------|
| Build PDF from HTML | `python scripts/html2pdf.py INPUT.html OUTPUT.pdf` |
| Build with font dir | `python scripts/html2pdf.py INPUT.html OUTPUT.pdf --fonts ../../assets/fonts` |
| General PDF editing | Use base `document-skills:pdf` skill |

> **Script paths** are relative to this skill directory (`skills/ichita-pdf/`).

---

## How It Works

```
HTML template (content + CSS)
        |
    weasyprint (300 DPI, A4)
        |
    Branded PDF
```

The HTML template IS the design — CSS handles all layout, colors, typography, and page breaks. No external template engine needed.

---

## Writing HTML Templates

### Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  /* Brand CSS variables — from ichita-defaults.md */
  :root {
    --blue: #2978FF; --blue-light: #82B0FF;
    --grey1: #CFD9DB; --grey2: #788F9C; --grey3: #263338;
    --blue-black: #171C21; --green: #34A853; --red: #E83E3E;
    --white: #FFFFFF; --alt-row: #F0F4F5;
    --mx: 18mm;  /* page margin */
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }
  @page { size: 210mm 297mm; margin: 0; }

  body {
    font-family: 'Aeonik', 'TH Aeonik', sans-serif;
    font-size: 10.5pt; color: var(--grey3);
    line-height: 1.6;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .page {
    width: 210mm; height: 297mm;
    position: relative; overflow: hidden;
    page-break-after: always;
  }
</style>
</head>
<body>
  <div class="page">
    <!-- Page 1 content -->
  </div>
  <div class="page">
    <!-- Page 2 content -->
  </div>
</body>
</html>
```

### Key CSS Patterns

**Hero section** (dark header):
```css
.hero {
  height: 52mm; background: var(--blue-black);
  display: flex; align-items: center;
  padding: 0 var(--mx);
}
```

**Section with icon badge**:
```css
.section { padding: 3mm var(--mx); }
.section-header {
  display: flex; align-items: center; gap: 2mm;
  font-size: 8pt; font-weight: 700; color: var(--grey3);
  text-transform: uppercase; letter-spacing: 1.5px;
  border-bottom: 0.5pt solid var(--grey1);
  padding-bottom: 1.5mm; margin-bottom: 2mm;
}
```

**Data table**:
```css
table { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
th { background: var(--grey3); color: white; padding: 1.5mm 2mm; text-align: left; }
td { padding: 1.2mm 2mm; border-bottom: 0.3pt solid var(--grey1); }
tr:nth-child(even) td { background: var(--alt-row); }
```

**Footer**:
```css
.footer {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 10mm; background: var(--grey3);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 var(--mx); color: rgba(255,255,255,0.5);
  font-size: 6.5pt;
}
```

### Font Handling

**Option A: System fonts** (recommended for dev):
```css
body { font-family: 'Aeonik', 'Calibri', sans-serif; }
```

**Option B: Embedded fonts** (for portable HTML):
```css
@font-face {
  font-family: 'Aeonik';
  src: url('fonts/AeonikTH-Regular.ttf') format('truetype');
  font-weight: 400;
}
@font-face {
  font-family: 'Aeonik';
  src: url('fonts/AeonikTH-Bold.ttf') format('truetype');
  font-weight: 700;
}
```

The `html2pdf.py` script supports `--fonts` flag to inject font directory, so templates can use relative paths.

> **Avoid base64 font embedding** — it bloats HTML to 1MB+. Use file paths instead.

---

## Brand Reference

All colors, typography, and visual identity: [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md)

| Element | Value |
|---------|-------|
| Primary accent | `#2978FF` (blue) |
| Dark background | `#171C21` (blue-black) |
| Text color | `#263338` (grey3) |
| Page size | A4 (210mm × 297mm) |
| Margins | 18mm left/right |
| Body font | Aeonik / AeonikTH 10.5pt |
| Heading font | Aeonik Bold |
| Thai text | AeonikTH (same family) |

---

## Document Types

### Executive Brief
- 2-3 pages, formal tone
- Hero section with title + subtitle
- Numbered sections with icon badges
- Data tables, KPI highlights
- Footer with ICHITA logo + page number

### Memo
- 1-2 pages, internal communication
- Header with To/From/Date/Subject
- Clean body text, bullet points
- ICHITA letterhead

### One-Pager
- Single A4 page
- Dense layout, multiple sections
- Charts/tables as HTML
- Marketing or technical focus

---

## Dependencies

```bash
pip install weasyprint
# System deps (Ubuntu):
sudo apt-get install libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Fonts not rendering | Use `--fonts` flag or install to system |
| Content overflows page | Reduce font-size or split into more pages |
| Colors missing in PDF | Ensure `print-color-adjust: exact` in CSS |
| Thai bold not working | Register bold weight in `@font-face` with `font-weight: 700` |
| Page break in wrong place | Use `page-break-inside: avoid` on sections |
