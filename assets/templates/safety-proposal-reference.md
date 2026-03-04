# Ichita Safety Proposal Template Reference

This file documents the `safety-proposal.docx` template in full detail. Read this before any safety proposal work — it is the single source of truth for template structure, styles, XML patterns, and what must never be modified.

The safety proposal template differs significantly from `word-template.docx` (the general letterhead template). Key differences are covered in their own section below.

---

## Quick Start

```
1. cp assets/ichita/templates/safety-proposal.docx ./output/working.docx
2. python .claude/skills/docx/ooxml/scripts/unpack.py ./output/working.docx ./output/unpacked/
3. Edit word/document.xml (content) and optionally word/header1.xml (customer name only)
4. python .claude/skills/docx/ooxml/scripts/pack.py ./output/unpacked/ ./output/final.docx
```

---

## How It Differs from the General Template

| Feature | General Template (`word-template.docx`) | Safety Proposal (`safety-proposal.docx`) |
|---------|------------------------------------------|-------------------------------------------|
| Margins | Tight (top 0.33cm, etc.) | Standard 1 inch all around |
| Title page | `<w:titlePg/>` YES | NO title page mode |
| Headers | 3 headers (even/default/first) | 1 header only |
| Footers | 2 footers (default/first) | NONE (no footer files) |
| Fonts | Arial 12pt default, Aeonik embedded | No custom fonts, Angsana New headings |
| Comments | No comments infrastructure | Full comments system |
| customXml | Yes | No |
| Embedded fonts | Yes (.odttf) | No |

---

## Page Setup

Source: `word/document.xml` `<w:sectPr>`

- Paper size: A4 — w=11906, h=16838 twips
- Margins: top=1440, right=1440, bottom=1440, left=1440 (all 1.0 inch)
- Header distance from edge: 708 twips
- Footer distance from edge: 708 twips
- Gutter: 0
- No `<w:titlePg/>` — single header/footer applies to ALL pages

---

## Files in Template

```
[Content_Types].xml
_rels/.rels
docProps/app.xml
docProps/core.xml
word/_rels/comments.xml.rels
word/_rels/document.xml.rels
word/_rels/header1.xml.rels
word/comments.xml
word/commentsExtended.xml
word/commentsExtensible.xml
word/commentsIds.xml
word/document.xml
word/endnotes.xml
word/fontTable.xml
word/footnotes.xml
word/header1.xml
word/media/image1.png
word/media/image2.png
word/numbering.xml
word/people.xml
word/settings.xml
word/styles.xml
word/theme/theme1.xml
word/webSettings.xml
```

---

## Relationship Map

Source: `word/_rels/document.xml.rels`

| rId | Target | Type |
|-----|--------|------|
| rId1 | numbering.xml | numbering |
| rId2 | styles.xml | styles |
| rId3 | settings.xml | settings |
| rId4 | webSettings.xml | webSettings |
| rId5 | footnotes.xml | footnotes |
| rId6 | endnotes.xml | endnotes |
| rId7 | media/image1.png | image (inline in document body) |
| rId8 | comments.xml | comments |
| rId9 | commentsExtended.xml | commentsExtended |
| rId10 | commentsIds.xml | commentsIds |
| rId11 | commentsExtensible.xml | commentsExtensible |
| rId12 | header1.xml | header |
| rId13 | fontTable.xml | fontTable |
| rId14 | people.xml | people |
| rId15 | theme/theme1.xml | theme |

---

## Header Structure

File: `word/header1.xml`
Relationships: `word/_rels/header1.xml.rels` — rId1 maps to `media/image2.png`

- Single header used for ALL pages (no title page / even page variants)
- Contains the Ichita logo (image2.png)
  - Logo extent: cx=1041149 cy=158721 EMU (approximately 1.14 x 0.17 inches — smaller than the general template logo)
- Header text: `SAFETY PROPOSAL | Prepared by ICHITA Co., Ltd. | Submitted to Energy China`

### Changing the Customer Name

The "Submitted to [Customer]" text is the only acceptable header modification. Find the relevant `<w:t>` node in `word/header1.xml` and update:

```xml
<!-- Replace "Energy China" with the actual customer name -->
<w:t> to [NEW CUSTOMER NAME]</w:t>
```

Do NOT change the logo, font, or any other part of the header structure.

---

## Comments Infrastructure

This template includes a full comments system — unique compared to the general template.

| File | Purpose |
|------|---------|
| `word/comments.xml` | Actual comment text. Example: id=0, author="Jantarathip GTP Sriwikit" |
| `word/commentsExtended.xml` | Extended comment properties |
| `word/commentsExtensible.xml` | Additional extensibility data |
| `word/commentsIds.xml` | Comment ID tracking |
| `word/people.xml` | Author information |
| `word/_rels/comments.xml.rels` | Comment relationships |

If you add new comments, you must update ALL comment files consistently. If you do not need comments, leave all comment files as-is — they do not affect document output.

---

## Style Catalog

Source: `word/styles.xml`

### Paragraph Styles

| styleId | Name | Font | Size | Properties |
|---------|------|------|------|------------|
| Normal | Normal | (default) | (default) | Base style |
| Heading1 | heading 1 | Angsana New | 24pt | Bold, based on Normal |
| Heading2 | heading 2 | Angsana New | 18pt | Bold, based on Normal |
| Heading3 | heading 3 | Angsana New | 13.5pt | Bold, based on Normal |
| NormalWeb | Normal (Web) | Angsana New | 14pt | based on Normal |
| Style1 | Style1 | Aeonik | 14pt | Bold — custom Ichita branded style |
| Header | header | (inherit) | (inherit) | based on Normal |
| Footer | footer | (inherit) | (inherit) | based on Normal |
| CommentText | annotation text | (inherit) | 10pt | based on Normal |
| CommentSubject | annotation subject | (inherit) | (inherit) | Bold, based on CommentText |

### Character Styles

| styleId | Name | Font | Size | Properties |
|---------|------|------|------|------------|
| DefaultParagraphFont | Default Paragraph Font | — | — | Base character style |
| Heading1Char | Heading 1 Char | Angsana New | 24pt | Bold |
| Heading2Char | Heading 2 Char | Angsana New | 18pt | Bold |
| Heading3Char | Heading 3 Char | Angsana New | 13.5pt | Bold |
| Style1Char | Style1 Char | Aeonik | 14pt | Bold |
| CommentReference | annotation reference | — | 8pt | |
| Hyperlink | Hyperlink | — | — | color #0563C1 |
| UnresolvedMention | Unresolved Mention | — | — | color #605E5C |

### Table Style

| styleId | Name |
|---------|------|
| TableNormal | Normal Table |

---

## Media Files

| File | Usage | Notes |
|------|-------|-------|
| `word/media/image1.png` | Inline image in document body (rId7) | Referenced directly in document.xml |
| `word/media/image2.png` | Header logo | Referenced in header1.xml via rId1 |

---

## Required Proposal Sections

Source: `ψ/memory/learnings/ichita-proposal.instructions.md`

When creating a safety proposal, include these sections in order:

1. Cover Page (project name, customer, date, revision)
2. Executive Summary
3. Scope of Work
4. Safety Standards and Regulations
   - Thai laws (พ.ร.บ. ความปลอดภัย, กฎกระทรวง)
   - International standards (OSHA, ISO 45001)
5. Risk Assessment Matrix
6. Safety Equipment and Systems
7. Emergency Response Plan
8. Training Program
9. Implementation Timeline
10. Budget Summary
11. Appendices (drawings, certificates, references)

---

## Content Patterns — Copy-Paste Ready XML

### Section Heading (Heading1 — Angsana New 24pt Bold)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading1"/>
  </w:pPr>
  <w:r>
    <w:t>1. Scope of Work</w:t>
  </w:r>
</w:p>
```

### Subsection (Heading2 — Angsana New 18pt Bold)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading2"/>
  </w:pPr>
  <w:r>
    <w:t>1.1 Project Overview</w:t>
  </w:r>
</w:p>
```

### Sub-subsection (Heading3 — Angsana New 13.5pt Bold)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading3"/>
  </w:pPr>
  <w:r>
    <w:t>1.1.1 Site Description</w:t>
  </w:r>
</w:p>
```

### Body Text (Normal style)

```xml
<w:p>
  <w:r>
    <w:t>Body text content here. Uses default Normal style.</w:t>
  </w:r>
</w:p>
```

### Ichita Branded Text (Style1 — Aeonik 14pt Bold)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Style1"/>
  </w:pPr>
  <w:r>
    <w:t>Key branded text</w:t>
  </w:r>
</w:p>
```

### Page Break

```xml
<w:p>
  <w:r>
    <w:br w:type="page"/>
  </w:r>
</w:p>
```

### Simple Table (two-column with borders)

```xml
<w:tbl>
  <w:tblPr>
    <w:tblStyle w:val="TableNormal"/>
    <w:tblW w:w="0" w:type="auto"/>
    <w:tblBorders>
      <w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>
    </w:tblBorders>
  </w:tblPr>
  <w:tblGrid>
    <w:gridCol w:w="4500"/>
    <w:gridCol w:w="4500"/>
  </w:tblGrid>
  <w:tr>
    <w:tc>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Header 1</w:t></w:r></w:p>
    </w:tc>
    <w:tc>
      <w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Header 2</w:t></w:r></w:p>
    </w:tc>
  </w:tr>
  <w:tr>
    <w:tc>
      <w:p><w:r><w:t>Cell 1</w:t></w:r></w:p>
    </w:tc>
    <w:tc>
      <w:p><w:r><w:t>Cell 2</w:t></w:r></w:p>
    </w:tc>
  </w:tr>
</w:tbl>
```

---

## Protected Elements — NEVER Modify

### Files — Never touch (exception: header customer name only)

| File | Reason |
|------|--------|
| `word/media/image1.png` | Inline image — do not replace |
| `word/media/image2.png` | Ichita header logo — do not replace |
| `word/settings.xml` | Document settings |
| `word/theme/theme1.xml` | Theme definitions |
| `word/fontTable.xml` | Font table |
| `word/_rels/document.xml.rels` | Relationship map |
| `[Content_Types].xml` | Content type definitions |
| `_rels/.rels` | Package relationships |
| `docProps/*` | Document properties |

### Comment files — Leave as-is unless intentionally adding comments

- `word/comments.xml`
- `word/commentsExtended.xml`
- `word/commentsExtensible.xml`
- `word/commentsIds.xml`
- `word/people.xml`

### XML elements in document.xml — Never modify

- `<w:sectPr>` — Section properties (page size, margins, header link)
- `<w:headerReference>` — Header linkage
- `<w:pgSz>` — Page size
- `<w:pgMar>` — Page margins

---

## Editable Files Summary

| File | What You Can Edit |
|------|-------------------|
| `word/document.xml` | All body content — paragraphs, headings, tables, page breaks |
| `word/header1.xml` | Customer name in the "Submitted to [Customer]" text only |

Everything else is protected.
