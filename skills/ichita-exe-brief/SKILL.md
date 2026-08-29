---
name: ichita-exe-brief
description: "Use when creating Ichita-branded executive briefs — the workflow from content ideation through HTML design to print-ready PDF. Covers strategic briefs, board memos, government submissions. Trigger when user mentions 'executive brief', 'brief', 'board memo', or wants a formal branded document for executives/officials."
---

# Ichita Executive Brief

> Workflow skill: content → branded HTML layout → print-ready PDF.
> For general PDF processing (merge, split, OCR), use `document-skills:pdf`.
> For general DOCX creation, use `ichita-docx`.

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
    html2pdf.py --engine auto
        |
        +-- scripted, or any Thai  ->  chromium
        +-- static and English     ->  weasyprint (300 DPI, A4)
        |
    Branded PDF
```

The HTML template IS the design — CSS handles all layout, colors, typography, and page breaks. No external template engine needed.

**The engine is chosen from the document, not configured.** weasyprint cannot
execute JavaScript, so it renders a script-built page as its loading
placeholder and exits 0; and its Thai text layer is wrong even when the glyphs
look right. Both are measured in
`skills/ichita-convert/reference/pdf-delivery.md`. Override with
`--engine weasyprint|chromium` only with a reason.

---

## Writing HTML Templates

### Page Structure

```html
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  /* Brand CSS variables — from ichita-defaults.md */
  :root {
    --blue: #2978FF; --blue-light: #82B0FF;
    --grey1: #CFD9DB; --grey2: #788F9C; --grey3: #263338;
    --blue-black: #171C21; --green: #34A853; --red: #E83E3E;
    --white: #FFFFFF; --alt-row: #F0F4F5;
    --mx: 28px;  /* page padding */
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }
  @page { size: 210mm 297mm; margin: 0; }

  body {
    font-family: 'Aeonik', 'AeonikTH', sans-serif;
    background: #e8e8e8; color: var(--grey3);
    font-size: 13px; line-height: 1.6;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .print-btn {
    position: fixed; top: 16px; right: 16px;
    background: var(--blue); color: #fff; border: none;
    padding: 8px 20px; border-radius: 4px;
    font-family: 'Aeonik', 'AeonikTH', sans-serif;
    font-size: 13px; font-weight: 600; cursor: pointer; z-index: 999;
  }
  .print-btn:hover { background: #1a5fd6; }

  .page {
    width: 210mm; min-height: 297mm;
    background: #fff; margin: 24px auto;
    position: relative; overflow: hidden;
    page-break-after: always;
  }

  @media print {
    body { background: #fff; }
    .print-btn { display: none; }
    .page { margin: 0; box-shadow: none; page-break-after: always; }
  }
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">Print / Save PDF</button>
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

**Header** (dark bar with title left, logo right):
```css
.header {
  background: var(--blue-black);
  padding: 18px var(--mx) 14px;
  display: flex; justify-content: space-between; align-items: flex-start;
}
.header-tag {
  font-size: 8px; font-weight: 600; letter-spacing: 2px;
  color: var(--blue); text-transform: uppercase; margin-bottom: 4px;
}
.header-title {
  font-size: 18px; font-weight: 700; color: #fff; line-height: 1.25;
}
.header-title span { color: var(--blue); }
.header-subtitle {
  font-size: 10px; color: var(--grey2); margin-top: 5px; line-height: 1.5;
}
.logo-block {
  display: flex; align-items: center; gap: 8px;
  justify-content: flex-end; margin-bottom: 4px;
}
.logo-block img { height: 20px; }  /* ICHITA wordmark — use ichita-wordmark-white-on-dark.png */
.header-meta {
  font-size: 8.5px; color: var(--grey2); text-align: right;
}
.accent-line { height: 2px; background: var(--blue); }
```

**Header HTML example:**
```html
<div class="header">
  <div>
    <div class="header-tag">Executive Brief · March 2026 · Confidential</div>
    <div class="header-title">Main Title<br><span>Subtitle in Accent</span></div>
    <div class="header-subtitle">Prepared by ICHITA Thailand</div>
  </div>
  <div style="text-align:right;">
    <div class="logo-block">
      <img src="../../assets/logos/ichita-wordmark-white-on-dark.png" alt="ICHITA">
    </div>
    <div class="header-meta">ICHITA Co., Ltd.</div>
  </div>
</div>
<div class="accent-line"></div>
```

**Body content area**:
```css
.body { padding: 18px var(--mx) 24px; }
```

**Section with numbered badge**:
```css
.section { margin-bottom: 15px; }
.section-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid #e8e0cc; padding-bottom: 4px;
}
.section-num {
  background: var(--blue-black); color: var(--blue);
  font-size: 8px; font-weight: 700;
  padding: 2px 6px; border-radius: 2px; letter-spacing: 1px;
}
.section-title {
  font-size: 12px; font-weight: 700; color: var(--blue-black);
  letter-spacing: 0.3px;
}
```

**Stat cards row** (top-of-page KPIs):
```css
.stat-row { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-bottom: 16px; }
.stat-card { background: var(--blue-black); border-radius: 4px; padding: 10px 12px; text-align: center; }
.stat-num { font-size: 22px; font-weight: 700; color: var(--blue); line-height: 1.1; }
.stat-unit { font-size: 9px; color: var(--blue); font-weight: 500; }
.stat-label { font-size: 10px; color: #aab8cc; margin-top: 4px; line-height: 1.4; }
```

**Info boxes** (two-column layout):
```css
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-box {
  background: var(--alt-row); border-left: 3px solid var(--blue);
  border-radius: 0 4px 4px 0; padding: 10px 12px;
}
.info-box-title { font-size: 11px; font-weight: 700; color: var(--blue-black); margin-bottom: 5px; }
.info-text { font-size: 11.5px; color: #333; line-height: 1.65; }
```

**Highlight box** (dark emphasis):
```css
.highlight-box { background: var(--blue-black); border-radius: 4px; padding: 10px 14px; }
.highlight-box .info-text { color: #dde4f0; }
.highlight-box .info-box-title { color: var(--blue); }
```

**Data table**:
```css
.roadmap-table { width: 100%; border-collapse: collapse; font-size: 10.5px; }
.roadmap-table th {
  background: var(--blue-black); color: var(--blue);
  font-weight: 600; padding: 5px 8px; text-align: left;
  font-size: 9px; letter-spacing: 0.5px; text-transform: uppercase;
}
.roadmap-table td { padding: 6px 8px; border-bottom: 0.5px solid #e8e0cc; vertical-align: top; color: #222; }
.roadmap-table tr:nth-child(even) td { background: #faf8f2; }
```

**Vision / Call-to-action box**:
```css
.vision {
  background: var(--blue-black); border-radius: 4px;
  padding: 12px 16px; margin-top: 14px;
  border-left: 4px solid var(--blue);
}
.vision-label {
  font-size: 8px; font-weight: 700; letter-spacing: 2px;
  color: var(--blue); text-transform: uppercase; margin-bottom: 6px;
}
.vision-text { font-size: 11.5px; color: #dde4f0; font-style: italic; line-height: 1.7; }
```

**Footer**:
```css
.footer {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: var(--blue-black);
  padding: 6px var(--mx);
  display: flex; align-items: center; justify-content: space-between;
}
.footer-text {
  font-size: 8px; color: rgba(255,255,255,0.4);
  letter-spacing: 1px; text-transform: uppercase;
}
.footer-page { font-size: 9px; color: var(--blue); font-weight: 600; }
```

### Font Handling

**Link the brand stylesheet. Do not declare `@font-face` in a document.**

```html
<link rel="stylesheet" href="../../assets/brand/ichita.css">
```

`assets/brand/ichita.css` already declares the full ten-weight ladder for both
families — `Aeonik` 100–900 and `TH Aeonik` 100–900 — pointing at the `.otf` files in
`assets/fonts/`. Re-declaring a face in the document is how a brief ends up loading a
filename that no longer exists and silently rendering in a fallback.

Pick the family by the **document's language**, not per paragraph:

| Document | `font-family` |
|---|---|
| English only | `'Aeonik'` |
| Thai, or mixed TH/EN | `'TH Aeonik'` |

Never add a system fallback (`'Calibri'`, `sans-serif`) to the stack. A fallback turns a
missing font into a silent substitution instead of a visible failure — and
`html2pdf.py` reports the fonts Chromium actually used precisely so that failure is
visible. Read that line in its output.

> **Avoid base64 font embedding** — it bloats HTML to 1MB+. Link the stylesheet instead.

---

## Brand Reference

All colors, typography, and visual identity: [`ichita-defaults.md`](../../assets/brand/ichita-defaults.md)

| Element | Value |
|---------|-------|
| Primary accent | `#2978FF` (blue) |
| Dark background | `#171C21` (blue-black) |
| Text color | `#263338` (grey3) |
| Page size | A4 (210mm × 297mm) |
| Padding | 28px left/right |
| Body font | Aeonik / AeonikTH 13px |
| Heading font | Aeonik Bold 18px |
| Thai text | AeonikTH (same family) |
| Logo (dark bg) | `ichita-wordmark-white-on-dark.png` |
| Logo (light bg) | `ichita-wordmark-dark-on-white.png` |
| Accent line | 2px solid `#2978FF` below header |

---

## Workflow

```
1. IDEATION    — Chat/co-work to solidify idea, scope, key messages
2. CONTENT     — Draft text, data points, key figures (human/Oda)
3. DESIGN      — Build HTML template with branded CSS layout
4. RENDER      — html2pdf.py → print-ready PDF
```

This skill handles steps 3-4. Steps 1-2 happen in conversation.

## Executive Brief Anatomy

A typical 2-3 page executive brief:

### Every Page Has
- **Header**: Dark bar — tag line (top-left), title + subtitle (left), ICHITA logo (right)
- **Accent line**: 2px blue line below header
- **Footer**: Dark bar — classification text (left), page number in blue (right)

### Page 1 — Hook
- **Header**: Document type tag + main title with accent subtitle + ICHITA logo
- **Stat cards**: 3 key metrics in dark cards with blue numbers
- **Section 01**: Context / problem statement (two-column info boxes)
- **Section 02**: Evidence cards (three-column)

### Page 2 — Evidence & Ask
- **Header**: Continuation tag + section title + ICHITA logo
- **Section 03**: Solution / approach (arrow flow diagrams + highlight box)
- **Section 04**: Discussion points (three-column cards)
- **Section 05**: Roadmap table (dark header, badge labels)
- **Section 06**: Requests / next steps (dark numbered cards)
- **Vision box**: Closing statement with blue left border

### Page 3+ — Additional (if needed)
- **Section 07+**: Supporting data, appendices
- **Call-to-action box**: Clear next steps
- **Footer**: ICHITA branding + classification + page count

## Use Cases

| Type | Pages | Audience | Tone |
|------|-------|----------|------|
| Board memo | 2-3 | C-suite, board | Formal, data-driven |
| Government submission | 2-3 | Officials, regulators | ทางการ, anti-AI |
| Investor brief | 1-2 | Investors, partners | Confident, metrics-focused |
| Project proposal | 2-4 | Internal stakeholders | Technical, practical |

---

## Dependencies

```bash
pip install weasyprint playwright pymupdf
python3 -m playwright install chromium   # ~150 MB, separate from the package
# System deps (Ubuntu):
sudo apt-get install libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev
```

All three are required, not optional:

| Package | Without it |
|---|---|
| `weasyprint` | no engine for static English pages |
| `playwright` + chromium | scripted and Thai documents exit 1 |
| `pymupdf` | the weasyprint path exits 1 — it is what reads the output back to check the render is not an empty shell, and a check that cannot run must not pass |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Fonts not rendering | Use `--fonts` flag or install to system |
| Content overflows page | Reduce font-size or split into more pages |
| Colors missing in PDF | Ensure `print-color-adjust: exact` in CSS |
| Thai bold not working | Register bold weight in `@font-face` with `font-weight: 700` |
| Page break in wrong place | Use `page-break-inside: avoid` on sections |
