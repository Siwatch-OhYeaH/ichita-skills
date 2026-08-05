# Ichita DOCX Standard

> Single source of truth for all Ichita Word documents.
> Maps to `ICHITA_BRAND` dict sections in `docx_helpers.py`.

**Last Updated**: 2026-03-06

---

## Page Setup

| Property        | Value            |
|-----------------|------------------|
| Paper size      | A4 (210 x 297mm) |
| Orientation     | Portrait (default) |
| Top margin      | 2.0 cm           |
| Bottom margin   | 2.0 cm           |
| Left margin     | 2.0 cm           |
| Right margin    | 2.0 cm           |
| Header distance | 1.27 cm from edge |
| Footer          | None             |

---

## Fonts

**The face is chosen by the document's language** — brand policy, Siwatch
2026-08-05. See `ichita-defaults.md` §4 for the reasoning; this is the DOCX side.

### English-only documents — split fonts

| Role            | Font              | Fallback            | Notes              |
|-----------------|-------------------|----------------------|--------------------|
| Latin           | Aeonik            | Calibri             | line box 1200      |
| Thai            | Bai Jamjuree      | TH Sarabun New      | Scale 0.9x         |
| Display numbers | Betatron          | —                   | Headlines, callouts |
| Code            | Courier New       | —                   | Monospaced         |

Line spacing: `w:lineRule="atLeast"` at `ceil(1.476 × Latin pt)`. Bai Jamjuree's
own box (1250) is 314 units short of what its Thai needs, and this repo does not
build Bai — so in split mode the paragraph property is the *only* thing holding
two Thai lines apart. Keep it.

### Thai or mixed documents — one unified font

| Role            | Font              | Fallback            | Notes              |
|-----------------|-------------------|----------------------|--------------------|
| Latin **and** Thai | **TH Aeonik**  | Aeonik + Bai split  | line box **1537**, scale 1.0 |
| Display numbers | Betatron          | —                   | Headlines, callouts |
| Code            | Courier New       | —                   | Monospaced         |

Line spacing: `atLeast` at `1.537 × Latin pt`, which is **exactly the font's own
box and therefore a deliberate no-op**. It costs nothing and fails safe if the font
is missing and Word substitutes. Do *not* raise it — the font already carries the
clearance, and anything above 1.537 adds leading nobody asked for.

Set `w:ascii`, `w:hAnsi`, `w:cs` and `w:eastAsia` all to `TH Aeonik`: one font for
every script slot, so no run can pick up a different line height.

**Selection is automatic.** `md_to_docx.py`, `html_to_docx.py` and
`docx_helpers.resolve_font()` scan the source for Thai (U+0E00–U+0E7F) and log the
face they chose. `--font-mode {auto,aeonik,th-aeonik}` overrides it.

---

## Text Styles

Sizes from Mitrphol UF Technical Proposal (production reference). Thai uses `szCs` at 0.9× scale.

| Style   | Latin (sz) | Thai (szCs) | Weight  | Color   | Before | After | Accent                  |
|---------|-----------|-------------|---------|---------|--------|-------|-------------------------|
| Title   | 26pt      | 23.4pt      | Bold    | #263338 | 0pt    | 12pt  | Blue band               |
| H1      | 22pt      | 20pt        | Bold    | #263338 | 18pt   | 8pt   | Left bar 4pt #2978FF    |
| H2      | 15pt      | 13.5pt      | Bold    | #263338 | 14pt   | 6pt   | Left bar 4pt #2978FF    |
| H3      | 12pt      | 11pt        | Bold    | #2978FF | 10pt   | 6pt   | None                    |
| H4      | 10.5pt    | 9.5pt       | Bold    | #2978FF | 8pt    | 4pt   | None                    |
| Body    | 10pt      | 9pt         | Regular | #263338 | 3pt    | 6pt   | —                       |
| Caption | 9pt       | 9pt         | Regular | #788F9C | 6pt    | 3pt   | —                       |
| Lists   | 10pt      | 9pt         | Regular | #263338 | 2pt    | 2pt   | —                       |

**Rules**: Minimum font size 8pt. `keepNext` on all headings.

---

## Header

| Property      | Value                     |
|---------------|---------------------------|
| Logo          | Ichita logo black, 1.5"   |
| Border        | Bottom border 6pt #2978FF |
| Space below   | 4pt                       |
| Scope         | Same on all pages         |

---

## Footer

None.

---

## Colors

| Name          | Hex       | Usage                    |
|---------------|-----------|--------------------------|
| Ichita Blue   | #2978FF   | Primary accent, links    |
| Blue Light    | #82B0FF   | Secondary accent         |
| Blue Grey 03  | #263338   | Primary text, headings   |
| Blue Grey 02  | #788F9C   | Captions, muted text     |
| Blue Grey 01  | #CFD9DB   | Borders, dividers        |
| Blue Black    | #171C21   | Extra-dark text          |
| Off White     | #F8FAFB   | Blockquote background    |
| Alt Row       | #EFF2F3   | Table alternate rows     |
| Border        | #A0B0B8   | Table borders            |
| White         | #FFFFFF   | Default background       |
| Code BG       | #F2F2F2   | Code block background    |
| Code Text     | #333333   | Code block text          |
| Success       | #34A853   | Positive indicators      |
| Error         | #E83E3E   | Negative indicators      |

---

## Table Style

| Property       | Value                                   |
|----------------|-----------------------------------------|
| Header row     | Background #263338, text White, Bold 10pt |
| Data rows      | Text #263338, Regular 10pt              |
| Alternate rows | Odd #EFF2F3 / Even #FFFFFF             |
| Borders        | Single, 4tw, #A0B0B8                   |
| Cell padding   | 2pt                                     |
| Wide tables    | >10 columns: use 8pt font              |
| Gap            | 8pt space before and after table        |

---

## Special Elements

### Blockquote

| Property       | Value              |
|----------------|--------------------|
| Left border    | 18pt #2978FF       |
| Background     | #F8FAFB            |
| Left indent    | 0.5"               |
| Right indent   | 0.3"               |
| Spacing        | 8pt before/after   |
| Style          | Italic             |

### Code Block

| Property       | Value              |
|----------------|--------------------|
| Font           | Courier New 9pt    |
| Text color     | #333333            |
| Background     | #F2F2F2            |
| Left indent    | 0.3"               |
| Spacing        | 6pt before/after   |

### Horizontal Rule

| Property       | Value              |
|----------------|--------------------|
| Weight         | 6pt                |
| Color          | #A0B0B8            |

### Links

| Property       | Value              |
|----------------|--------------------|
| Color          | #2978FF            |
| Decoration     | Underline          |

---

## Title Page

| Property       | Value                        |
|----------------|------------------------------|
| Space before   | 80pt                         |
| Title          | 26pt Bold #263338, centered  |
| Accent         | Blue accent                  |
| Subtitle       | 16pt #788F9C                 |
| Space after    | 36pt                         |
| Page break     | Always page break after      |

---

## Lists

| Property        | Value              |
|-----------------|--------------------|
| Indent          | 0.5"               |
| Numbered hang   | -0.25" hanging     |
| Nested step     | +0.25" per level   |
| Spacing         | 2pt between items  |

---

## Page Breaks

| Rule                          | Behavior                      |
|-------------------------------|-------------------------------|
| Title page                    | Page break after              |
| H1                            | NO forced page break          |
| Headings                      | `keepNext` (avoid orphans)    |
| Landscape sections            | Section breaks (new section)  |

---

## Implementation Notes

- All values map to `ICHITA_BRAND` dict sections in `docx_helpers.py`.
- **Font attributes on EVERY run**: `ascii`/`hAnsi` = Aeonik (Latin), `cs` = Bai Jamjuree (Thai).
- **Size attributes on EVERY run**: `sz` = Latin pt size, `szCs` = Thai pt size (0.9× scale).
  - Word/LibreOffice picks `sz` for Latin chars and `szCs` for Thai chars automatically.
  - This means runs do NOT need to be split by language for font sizing to work.
- `split_run_thai_latin()` is still used in `rebrand_docx.py` for existing documents where runs may have mixed content with wrong fonts.
- Templates live in `assets/ichita/templates/` in the main oracle repo.
- Always copy original template and edit XML; never generate DOCX from scratch.
