# Ichita Word Template Reference

**File**: `assets/ichita/templates/word-template.docx`
**Read this before**: any DOCX editing work using the Ichita general letterhead template.

This is the single source of truth for the Ichita general Word template. It covers page setup, styles, header/footer structure, protected elements, and copy-paste ready XML. If you are working on a Safety Proposal, use `safety-proposal.docx` instead (see `assets/ichita/brand/ichita-defaults.md`).

---

## Workflow (Always Follow This)

```
1. cp assets/ichita/templates/word-template.docx ./output/working.docx
2. python .claude/skills/docx/ooxml/scripts/unpack.py ./output/working.docx ./output/unpacked/
3. Edit ONLY word/document.xml in unpacked directory
4. python .claude/skills/docx/ooxml/scripts/pack.py ./output/unpacked/ ./output/final.docx
```

NEVER generate a DOCX from scratch. Always copy the template and edit XML.

---

## Page Setup

Source: `word/document.xml` — `<w:sectPr>`

| Property | Value (twips) | Value (cm/mm) |
|----------|--------------|---------------|
| Paper size | A4: w=11906, h=16838 | 210 × 297 mm |
| Margin top | 471 | ≈ 0.83 cm |
| Margin right | 737 | ≈ 1.3 cm (13 mm) |
| Margin bottom | 1134 | ≈ 2.0 cm (20 mm) |
| Margin left | 1418 | ≈ 2.5 cm (25 mm) |
| Header distance | 709 | ≈ 1.25 cm |
| Footer distance | 709 | ≈ 1.25 cm |
| Gutter | 0 | — |

Additional sectPr flags:
- `<w:pgNumType w:start="1"/>` — page numbering starts at 1
- `<w:cols w:space="708"/>` — single column
- `<w:titlePg/>` — FIRST PAGE HAS A DIFFERENT HEADER/FOOTER (header3/footer2)
- `<w:docGrid w:linePitch="360"/>` — line grid

---

## Document Body Rules

- The template body is essentially empty — just one blank paragraph with `<w:lang w:val="en-US"/>`
- All content paragraphs and tables go **BEFORE** the `<w:sectPr>` element
- The `<w:sectPr>` contains headerReference/footerReference links — **NEVER modify** it

---

## Relationship Map

Source: `word/_rels/document.xml.rels`

| rId | Target | Type |
|-----|--------|------|
| rId1 | ../customXml/item1.xml | customXml |
| rId2 | numbering.xml | numbering |
| rId3 | styles.xml | styles |
| rId4 | settings.xml | settings |
| rId5 | webSettings.xml | webSettings |
| rId6 | footnotes.xml | footnotes |
| rId7 | endnotes.xml | endnotes |
| rId8 | header1.xml | header (EVEN pages) |
| rId9 | header2.xml | header (DEFAULT) |
| rId10 | footer1.xml | footer (DEFAULT) |
| rId11 | header3.xml | header (FIRST page) |
| rId12 | footer2.xml | footer (FIRST page) |
| rId13 | fontTable.xml | fontTable |
| rId14 | theme/theme1.xml | theme |

---

## Header/Footer Structure

### header2.xml (rId9 — DEFAULT header)
- Ichita logo anchored right
- Font: Aeonik 9pt (18 half-pt)
- Image: `media/image1.jpg`
- Dimensions: cx=2063750, cy=314325 EMU (≈ 2.26 × 0.34 inches)
- Relationship: `word/_rels/header2.xml.rels` → rId1 → `media/image1.jpg`

### header3.xml (rId11 — FIRST page header)
- Same Ichita logo, same dimensions as header2
- Different layout: 3 extra empty paragraphs
- Relationship: `word/_rels/header3.xml.rels` → rId1 → `media/image1.jpg`

### header1.xml (rId8 — EVEN pages header)
- Page number field, centered
- Style: PageNumber

### footer1.xml (rId10 — DEFAULT footer)
- Top border: single line, 4pt, auto color
- QR code image: `media/image2.png`, cx=647700, cy=647700 EMU (≈ 0.71 × 0.71 inches)
- Relationship: `word/_rels/footer1.xml.rels` → rId1 → `media/image2.png`
- Text line 1: "Visit our website & LinkedIn page" — Aeonik 11pt, color #808080
- Text line 2: "399/75 Phongpetnivet, Prachacheun Rd., Jatujak, Bangkok 10900" — Aeonik 10pt, color #666666
- Text line 3: "Tel: 66 2585 1337, 66 2585 2123" — Aeonik 10pt, color #666666
- Text line 4: "Fax: 66 2585 3213" — Aeonik 10pt, color #666666
- Page number: centered, framed, Calibri/Arial 10pt

### footer2.xml (rId12 — FIRST page footer)
- Same content as footer1, slightly different text wrapping

---

## Style Catalog

Source: `word/styles.xml`

### Key Styles — Use These for Content

| styleId | Name | Font | Size | Notes |
|---------|------|------|------|-------|
| Normal | Normal | Arial | 12pt | Default paragraph |
| Heading1 | heading 1 | Arial (inherit) | 14pt | BOLD |
| Heading2 | heading 2 | Arial (inherit) | 12pt | BOLD |
| Heading3 | heading 3 | Arial (inherit) | 12pt | BOLD |
| Heading4 | heading 4 | Arial (inherit) | 12pt | — |
| Heading5 | heading 5 | Arial (inherit) | 10pt | BOLD |
| TEXT | TEXT | Arial (inherit) | 10pt | **Primary body text style — use this** |
| Titelblatt | Titelblatt | Arial | 22pt | BOLD — cover page title |
| TitelblattUntertitel | Titelblatt Untertitel | (inherit) | 18pt | Cover subtitle, based on Titelblatt |
| Zwischenberschrift | Zwischenüberschrift | (inherit) | 10pt | BOLD — section subheading |
| SymbolischeAufzhlung | Symbolische Aufzählung | (inherit) | (inherit) | Bullet list (uses numbering.xml) |
| SymbolischeAufzhlung2 | Symbolische Aufzählung 2 | (inherit) | (inherit) | Nested bullet |
| AlphabetischeAufzhlung | Alphabetische Aufzählung | (inherit) | (inherit) | Numbered/lettered list |
| Leerzeile | Leerzeile | (inherit) | 8pt | Empty line spacer |
| Body | Body | Helvetica Neue Light | (inherit) | Color #000000 — alternative body |
| Subheading | Subheading | Helvetica Neue | 11pt | BOLD, color #367DA2 — blue subheading |
| FreeForm | Free Form | Helvetica Neue Light | (inherit) | Color #000000 |
| Inhaltsverzeichnis | Inhaltsverzeichnis | (inherit) | 14pt | BOLD — table of contents title |
| ListParagraph | List Paragraph | (inherit) | (inherit) | Generic list |
| Abbildung | Abbildung | (inherit) | (inherit) | BOLD — figure caption |
| Caption | caption | (inherit) | 10pt | BOLD — generic caption |

Note: Style names are German-origin (Titelblatt = cover page, Zwischenüberschrift = subheading, Leerzeile = empty line, etc.). Content should be in the target language (Thai/English). Use `<w:lang w:val="en-US"/>` or `<w:lang w:val="th-TH"/>` in rPr for language-specific text.

### Table Styles

| styleId | Name | Notes |
|---------|------|-------|
| TableNormal | Normal Table | Base table style |
| TableGrid | Table Grid | Standard bordered table, based on TableNormal |
| GridTable4-Accent6 | Grid Table 4 Accent 6 | Colored table, BOLD white header |

### System/Utility Styles (Do Not Use Directly)

ZentriertFett, PageNumber, BalloonText, CommentReference, CommentText, CommentSubject, E-MailFormatvorlage231, Header, Footer, DocumentMap, TOC1, TOC2, TOC3, Bibliography, FootnoteText, FootnoteReference, NormalWeb, DefaultText, BodyText, BodyText2, z-TopofForm, z-BottomofForm, Strong, Hyperlink, hps, atn, comtext1, cirtext1 (plus all Char companion styles)

---

## Numbering Definitions

Source: `word/numbering.xml`

- abstractNum id=0: Multilevel bullet list cycling Symbol → Courier New → Wingdings
- Indent: 720 twips per level
- Used by: `SymbolischeAufzhlung` and `AlphabetischeAufzhlung` styles

---

## Embedded Fonts

Located in `word/fonts/`:
- `font1.odttf` — Aeonik (weight/style 1)
- `font2.odttf` — Aeonik (weight/style 2)

These are in `.odttf` (obfuscated OpenType) format. Do not modify.

---

## Media Files

Located in `word/media/`:

| File | Usage | Dimensions (EMU) | Dimensions (inches) |
|------|-------|-----------------|---------------------|
| image1.jpg | Ichita logo (headers) | cx=2063750, cy=314325 | ≈ 2.26 × 0.34 |
| image2.png | QR code (footers) | cx=647700, cy=647700 | ≈ 0.71 × 0.71 |

---

## Copy-Paste Ready XML Snippets

Use these verbatim when building document content in `word/document.xml`.

### Basic Paragraph (TEXT style — primary body text)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="TEXT"/>
  </w:pPr>
  <w:r>
    <w:t>Your text here</w:t>
  </w:r>
</w:p>
```

### Heading 1

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading1"/>
  </w:pPr>
  <w:r>
    <w:t>Section Title</w:t>
  </w:r>
</w:p>
```

### Heading 2

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading2"/>
  </w:pPr>
  <w:r>
    <w:t>Subsection Title</w:t>
  </w:r>
</w:p>
```

### Subheading — Zwischenberschrift (bold, styled)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Zwischenberschrift"/>
  </w:pPr>
  <w:r>
    <w:t>Subheading Text</w:t>
  </w:r>
</w:p>
```

### Bullet List Item

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="SymbolischeAufzhlung"/>
  </w:pPr>
  <w:r>
    <w:t>Bullet point text</w:t>
  </w:r>
</w:p>
```

### Nested Bullet

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="SymbolischeAufzhlung2"/>
  </w:pPr>
  <w:r>
    <w:t>Nested bullet text</w:t>
  </w:r>
</w:p>
```

### Numbered/Lettered List Item

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="AlphabetischeAufzhlung"/>
  </w:pPr>
  <w:r>
    <w:t>Numbered item text</w:t>
  </w:r>
</w:p>
```

### Cover Page Title (Titelblatt)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Titelblatt"/>
  </w:pPr>
  <w:r>
    <w:t>Document Title</w:t>
  </w:r>
</w:p>
```

### Cover Page Subtitle (TitelblattUntertitel)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="TitelblattUntertitel"/>
  </w:pPr>
  <w:r>
    <w:t>Subtitle or Project Name</w:t>
  </w:r>
</w:p>
```

### Empty Line Spacer (Leerzeile — 8pt)

```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Leerzeile"/>
  </w:pPr>
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

### Bold and/or Italic Run

```xml
<w:r>
  <w:rPr>
    <w:b/>
    <w:i/>
  </w:rPr>
  <w:t>Bold and italic text</w:t>
</w:r>
```

### Text with Leading/Trailing Spaces (IMPORTANT)

When a text run has leading or trailing spaces, you MUST use `xml:space="preserve"` or Word will strip them.

```xml
<w:r>
  <w:t xml:space="preserve"> text with spaces </w:t>
</w:r>
```

### Simple Table (TableGrid — 2 columns, header row)

Adjust `w:gridCol w:w` values as needed. Total should equal usable page width (approx 9000 twips for this template).

```xml
<w:tbl>
  <w:tblPr>
    <w:tblStyle w:val="TableGrid"/>
    <w:tblW w:w="0" w:type="auto"/>
    <w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>
  </w:tblPr>
  <w:tblGrid>
    <w:gridCol w:w="4500"/>
    <w:gridCol w:w="4500"/>
  </w:tblGrid>
  <w:tr>
    <w:tc>
      <w:p>
        <w:pPr><w:pStyle w:val="TEXT"/></w:pPr>
        <w:r><w:rPr><w:b/></w:rPr><w:t>Header 1</w:t></w:r>
      </w:p>
    </w:tc>
    <w:tc>
      <w:p>
        <w:pPr><w:pStyle w:val="TEXT"/></w:pPr>
        <w:r><w:rPr><w:b/></w:rPr><w:t>Header 2</w:t></w:r>
      </w:p>
    </w:tc>
  </w:tr>
  <w:tr>
    <w:tc>
      <w:p>
        <w:pPr><w:pStyle w:val="TEXT"/></w:pPr>
        <w:r><w:t>Cell 1</w:t></w:r>
      </w:p>
    </w:tc>
    <w:tc>
      <w:p>
        <w:pPr><w:pStyle w:val="TEXT"/></w:pPr>
        <w:r><w:t>Cell 2</w:t></w:r>
      </w:p>
    </w:tc>
  </w:tr>
</w:tbl>
```

---

## Protected Elements — NEVER Modify

### Files — Do Not Touch

| File | Reason |
|------|--------|
| `word/header1.xml` | Even-page header |
| `word/header2.xml` | Default header with Ichita logo |
| `word/header3.xml` | First-page header with Ichita logo |
| `word/footer1.xml` | Default footer with QR code and address |
| `word/footer2.xml` | First-page footer |
| `word/media/image1.jpg` | Ichita logo |
| `word/media/image2.png` | QR code |
| `word/fonts/font1.odttf` | Aeonik font |
| `word/fonts/font2.odttf` | Aeonik font |
| `word/settings.xml` | Document settings |
| `word/theme/theme1.xml` | Theme definitions |
| `word/fontTable.xml` | Font table |
| `word/_rels/document.xml.rels` | Relationship map |
| `[Content_Types].xml` | Content type definitions |
| `_rels/.rels` | Package relationships |
| `customXml/*` | Custom XML data |
| `docProps/*` | Document properties |

### XML Elements Inside document.xml — Do Not Modify

| Element | Reason |
|---------|--------|
| `<w:sectPr>` | Section properties — margins, page size, header/footer refs |
| `<w:headerReference>` | Links to header XML files |
| `<w:footerReference>` | Links to footer XML files |
| `<w:pgSz>` | Page size definition |
| `<w:pgMar>` | Page margin definition |
| `<w:titlePg/>` | Enables first-page different header/footer |

### What You CAN Modify

- Add/edit `<w:p>` paragraphs before `<w:sectPr>`
- Add/edit `<w:tbl>` tables before `<w:sectPr>`
- Modify text content inside `<w:t>` nodes
- Add new runs `<w:r>` within existing paragraphs

---

## Language Notes

- Default language in settings.xml is `de-DE` (German) — the template has German-origin style names
- For English content, add `<w:lang w:val="en-US"/>` inside `<w:rPr>`
- For Thai content, add `<w:lang w:val="th-TH"/>` inside `<w:rPr>`

Example with language tag:

```xml
<w:r>
  <w:rPr>
    <w:lang w:val="th-TH"/>
  </w:rPr>
  <w:t>ข้อความภาษาไทย</w:t>
</w:r>
```
