# Unified DOCX Architecture — Design Document

> All three use cases produce visually identical branded documents.

**Date**: 2026-03-06
**Status**: Approved
**Branch**: TBD (will be created during implementation)

---

## Problem

Two separate code paths (`md_to_docx.py` and `rebrand_docx.py`) produce visually different output for the same content. 12+ feature gaps between them (blockquotes, code blocks, inline markdown, title pages, page breaks, etc.). Fixing one path doesn't fix the other.

## Goal

Three use cases, identical visual output:

1. **Markdown to Word** — write markdown, get branded DOCX
2. **Word to Word** — rebrand existing DOCX to Ichita style
3. **Write from scratch** — open template in Word, type directly

## Architecture: Template + Shared Builder via IR

```
Case 1:  MD text  --> parse_markdown() --> IR --> build_docx(ir, template) --> DOCX
Case 2:  DOCX     --> parse_docx()     --> IR --> build_docx(ir, template) --> DOCX
Case 3:  template.docx --> user writes in Word directly (styles pre-configured)
```

Cases 1+2 share the same builder and template = guaranteed identical output.
Case 3 uses the same template = same styles, fonts, margins.

---

## 1. Intermediate Representation (IR)

All input is converted to a flat list of typed nodes before building.

### Node Types

| Type | Key Fields | Source: MD | Source: DOCX |
|------|-----------|-----------|-------------|
| `title_page` | title, subtitle, metadata{} | First H1 + metadata block | Title style or first Heading1 |
| `heading` | level (1-4), runs[] | `#`-`####` | Heading N style or detected |
| `paragraph` | runs[] | Plain text | Normal style |
| `table` | headers[], rows[][], wide? | Pipe table | `w:tbl` element |
| `list` | style (numbered/bullet), items[], level | `1.` or `-` | `numPr` in pPr |
| `blockquote` | runs[] | `>` prefix | Quote style or indent pattern |
| `code` | text, language? | Triple backtick | SourceCode style or Courier |
| `hr` | (none) | `---` | Border-only paragraph |
| `image` | data (bytes), width, caption? | Not supported from MD | `w:drawing` extraction |
| `page_break` | (none) | Explicit marker | `w:br type="page"` |

### Run (inline formatting unit)

```python
@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    url: str | None = None      # hyperlink
    code: bool = False          # inline code
```

Every paragraph/heading/list-item/blockquote contains a list of runs.
Inline markdown (`**bold**`, `*italic*`, `[link](url)`) is parsed into runs at the parser level, not the builder level.

---

## 2. Parsers

### parse_markdown(text) -> list[Node]

- Line-by-line state machine
- Extracts from current `md_to_docx.py` parsing logic
- Handles: headings, paragraphs, tables, lists (numbered + bullet + nested), blockquotes, code blocks, horizontal rules, inline formatting
- Does NOT handle: images (markdown image syntax not supported yet)

### parse_docx(doc_path) -> list[Node]

- Iterates body children (paragraphs + tables)
- Detection rules:

| Element | Detection Method |
|---------|-----------------|
| Heading | style = "Heading N" or regex `^[A-Z]\.\s+` + short text |
| List | `numPr` in pPr or style = ListParagraph/Compact |
| Blockquote | left indent >= 0.5" + not list, or style contains "Quote" |
| Code | style = "SourceCode" or font = Courier/monospace |
| Table | `w:tbl` element (direct child of body) |
| Image | `w:drawing` or `w:pict` in any run |
| HR | bottom border only + no text content |
| Title page | style = "Title" or first Heading1 in document |

- Extracts inline formatting from existing runs (bold, italic, hyperlinks)
- Preserves image binary data for re-embedding
- Does NOT preserve: custom XML, macros, tracked changes

---

## 3. Builder

### build_docx(ir, template_path, options?) -> Document

Single builder for all cases. Loads template as base document.

```python
def build_docx(ir: list[dict], template_path: str, options: dict = None) -> Document:
    doc = Document(template_path)
    clear_body(doc)  # remove sample content, keep styles + header/footer

    for node in ir:
        BUILD_MAP[node["type"]](doc, node)

    # post-process
    apply_thai_dual_font(doc)
    cleanup_empty_paragraphs(doc)
    enforce_table_spacing(doc)

    return doc
```

### Builder Functions (per node type)

| Function | What it does | Style source |
|----------|-------------|-------------|
| `build_title_page()` | Title + accent band + subtitle + metadata table + page break | Template Title style + brand colors |
| `build_heading()` | Heading paragraph + accent bar (H1/H2) + keepNext | Template Heading N style |
| `build_paragraph()` | Paragraph with runs (bold/italic/link formatting) | Template Normal style |
| `build_table()` | Header row (dark bg, white text) + alternating rows + borders | Brand colors from ICHITA_BRAND |
| `build_list()` | Numbered or bullet list with proper numPr + indentation | Template List Bullet/Number style |
| `build_blockquote()` | Left border + background + italic | Brand spec (18pt border, #F8FAFB bg) |
| `build_code()` | Courier New + background + indentation | Brand spec (9pt, #F2F2F2 bg) |
| `build_hr()` | Bottom border paragraph | Brand spec (6pt, #A0B0B8) |
| `build_image()` | Embedded image + optional caption | Image data from IR |
| `build_page_break()` | Page break run | N/A |

### Post-Processing

| Step | Purpose |
|------|---------|
| `apply_thai_dual_font()` | Set cs=Bai Jamjuree + szCs on every run |
| `cleanup_empty_paragraphs()` | Remove consecutive empty paragraphs |
| `enforce_table_spacing()` | Ensure 8pt gap before/after every table |

---

## 4. Template

### Generation

```
ICHITA_BRAND dict --> create_template.py --> ichita-template.docx
```

Script-generated, but OhYeaH! can adjust in Word afterward. Future: friend's Python add-on can modify template programmatically.

### Template Contents

| Component | Details |
|-----------|---------|
| **Page setup** | A4 portrait, 2cm margins all sides |
| **Header** | Ichita logo (1.5") + 6pt blue accent line |
| **Footer** | None |
| **Normal** | Aeonik 10pt, Bai Jamjuree cs, #263338, 3pt/6pt spacing |
| **Heading 1** | 22pt bold #263338, 18pt/8pt, keepNext, accent bar |
| **Heading 2** | 15pt bold #263338, 14pt/6pt, keepNext, accent bar |
| **Heading 3** | 12pt bold #2978FF, 10pt/6pt, keepNext |
| **Heading 4** | 10.5pt bold #2978FF, 8pt/4pt, keepNext |
| **Title** | 26pt bold #263338, centered |
| **Caption** | 9pt #788F9C, 6pt/3pt |
| **List Bullet** | 10pt, 0.5" indent |
| **List Number** | 10pt, 0.5" indent, -0.25" hanging |
| **Sample content** | Removed by builder at runtime (only for Word preview) |

---

## 5. File Structure

```
skills/ichita-docx/scripts/
  ir.py              # IR type definitions (dataclasses) + validation
  parse_markdown.py  # MD text --> IR
  parse_docx.py      # DOCX file --> IR
  build_docx.py      # IR + template --> branded DOCX
  docx_helpers.py    # ICHITA_BRAND, font utils, XML helpers (existing)
  cli.py             # Unified CLI entry point

  md_to_docx.py      # Legacy wrapper (calls parse_markdown + build_docx)
  rebrand_docx.py    # Legacy wrapper (calls parse_docx + build_docx)
```

### CLI

```bash
# Case 1: Markdown to Word
python cli.py --from-md proposal.md -o output.docx

# Case 2: Word to Word (rebrand)
python cli.py --from-docx original.docx -o rebranded.docx

# Options
  --template PATH     # custom template (default: ichita-template.docx)
  --no-logo           # skip header logo
  --no-title-page     # skip title page generation
  --landscape         # use landscape orientation
```

---

## 6. Migration Strategy

1. Build new system alongside existing code (no breaking changes)
2. Legacy `md_to_docx.py` and `rebrand_docx.py` become thin wrappers
3. ichita-docx skill updated to call new CLI
4. Old code removed after validation

---

## 7. Verification

### Identity Test

```bash
# Same markdown, both paths
python cli.py --from-md test.md -o a.docx
pandoc test.md -o test-pandoc.docx && python cli.py --from-docx test-pandoc.docx -o b.docx

# Compare: a.docx and b.docx must be visually identical
# Automated: extract XML, compare paragraph count, styles, fonts, spacing
```

### Checklist

- [ ] Same heading sizes, colors, accent bars
- [ ] Same body font, size, spacing
- [ ] Same table styling (header, alternating rows, borders)
- [ ] Same list numbering and bullet formatting
- [ ] Same blockquote styling (border, background, italic)
- [ ] Same code block styling (font, background, indentation)
- [ ] Same horizontal rule appearance
- [ ] Same header (logo + accent line)
- [ ] Same margins and page setup
- [ ] Same title page layout
- [ ] Thai dual-font correct on all runs
- [ ] Visual QA: PDF export from both, overlay comparison
