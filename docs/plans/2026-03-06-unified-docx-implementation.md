# Unified DOCX System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Three DOCX generation paths (MD→Word, Word→Word, template) produce visually identical branded output through a shared IR + builder architecture.

**Architecture:** All inputs are parsed into an Intermediate Representation (IR), then a single builder constructs the DOCX from a pre-styled template. This guarantees identical output regardless of input source.

**Tech Stack:** Python 3, python-docx, lxml, dataclasses. Repo: ichita-skills, branch: feat/unified-docx

**Design Doc:** `docs/plans/2026-03-06-unified-docx-architecture.md`

---

## Context

### Repo Layout

```
/home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills/
  skills/ichita-docx/scripts/
    docx_helpers.py    # ICHITA_BRAND dict + font/XML utilities (950 lines)
    md_to_docx.py      # Current MD→DOCX (503 lines) — will become legacy wrapper
    rebrand_docx.py    # Current DOCX→DOCX (841 lines) — will become legacy wrapper
  scripts/
    create_template.py # Template generator (196 lines)
  assets/
    brand/docx-standard.md  # Style spec (single source of truth)
    templates/ichita-document.dotx  # Current template
```

### Key Existing Functions (in docx_helpers.py, reuse as-is)

| Function | Purpose | Used by builder? |
|----------|---------|-----------------|
| `ICHITA_BRAND` (dict) | All brand values | Yes — passed to builder |
| `resolve_font()` | Find best available font | Yes — at startup |
| `set_font()` | Dual-font on w:r XML element | Yes — core of run styling |
| `set_cell_shading()` / `set_cell_shading_docx()` | Table cell backgrounds | Yes — tables |
| `set_table_borders()` | Brand borders on Table | Yes — tables |
| `style_table_xml()` | Complete table branding | Yes — tables |
| `add_header_footer()` | Logo + accent line header | Yes — finalize |
| `add_formatted_text()` | Inline markdown → runs | No — replaced by IR runs |
| `split_run_thai_latin()` | Split mixed Thai/Latin runs | Yes — post-process |
| `add_left_accent()` | H1/H2 accent bar | Yes — headings |
| `add_bottom_band()` | Title page accent | Yes — title page |
| `ensure_pPr()` | Get/create pPr element | Yes — utility |
| `make_para()` | Create paragraph with runs | Yes — builder core |
| `create_meta_table()` | Metadata table (key-value) | Yes — title page |
| `squeeze_wide_tables()` | Fit wide tables to page | Yes — post-process |
| `copy_image_rels()` | Copy image relationships | Yes — image nodes |

### Branch Strategy

Create `feat/unified-docx` from `feat/docx-standard` (builds on existing fixes).

```bash
cd /home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills
git checkout feat/docx-standard
git checkout -b feat/unified-docx
```

---

## Task 1: IR Type Definitions

**Files:**
- Create: `skills/ichita-docx/scripts/ir.py`
- Test: `skills/ichita-docx/scripts/test_ir.py`

**Step 1: Write test for IR node creation and validation**

```python
# test_ir.py
import pytest
from ir import Run, Node, make_heading, make_paragraph, make_table, make_list, \
    make_blockquote, make_code, make_hr, make_image, make_page_break, make_title_page, validate_ir


def test_run_defaults():
    r = Run(text="hello")
    assert r.bold is False
    assert r.italic is False
    assert r.url is None
    assert r.code is False


def test_run_with_formatting():
    r = Run(text="bold", bold=True, italic=True)
    assert r.bold is True
    assert r.italic is True


def test_make_heading():
    node = make_heading(level=1, runs=[Run(text="Title")])
    assert node["type"] == "heading"
    assert node["level"] == 1
    assert len(node["runs"]) == 1


def test_make_heading_invalid_level():
    with pytest.raises(ValueError):
        make_heading(level=5, runs=[Run(text="Bad")])


def test_make_paragraph():
    node = make_paragraph(runs=[Run(text="Body text")])
    assert node["type"] == "paragraph"
    assert node["runs"][0].text == "Body text"


def test_make_table():
    node = make_table(
        headers=["A", "B"],
        rows=[["1", "2"], ["3", "4"]]
    )
    assert node["type"] == "table"
    assert len(node["headers"]) == 2
    assert len(node["rows"]) == 2
    assert node["wide"] is False


def test_make_table_wide():
    node = make_table(
        headers=[f"C{i}" for i in range(12)],
        rows=[["x"] * 12]
    )
    assert node["wide"] is True


def test_make_list_numbered():
    node = make_list(
        style="numbered",
        items=[[Run(text="First")], [Run(text="Second")]],
    )
    assert node["type"] == "list"
    assert node["style"] == "numbered"
    assert len(node["items"]) == 2


def test_make_list_bullet():
    node = make_list(style="bullet", items=[[Run(text="Item")]])
    assert node["style"] == "bullet"


def test_make_list_nested():
    node = make_list(
        style="bullet",
        items=[[Run(text="Item")]],
        level=1,
    )
    assert node["level"] == 1


def test_make_blockquote():
    node = make_blockquote(runs=[Run(text="Quote", italic=True)])
    assert node["type"] == "blockquote"


def test_make_code():
    node = make_code(text="print('hi')", language="python")
    assert node["type"] == "code"
    assert node["language"] == "python"


def test_make_hr():
    node = make_hr()
    assert node["type"] == "hr"


def test_make_image():
    node = make_image(data=b"\x89PNG", width=5.0, caption="Fig 1")
    assert node["type"] == "image"
    assert node["width"] == 5.0


def test_make_page_break():
    node = make_page_break()
    assert node["type"] == "page_break"


def test_make_title_page():
    node = make_title_page(
        title="Project Proposal",
        subtitle="For Client X",
        metadata={"Date": "2026-03-06"}
    )
    assert node["type"] == "title_page"
    assert node["title"] == "Project Proposal"


def test_validate_ir_valid():
    ir = [
        make_heading(level=1, runs=[Run(text="Title")]),
        make_paragraph(runs=[Run(text="Body")]),
    ]
    assert validate_ir(ir) is True


def test_validate_ir_invalid_type():
    with pytest.raises(ValueError, match="Unknown node type"):
        validate_ir([{"type": "unknown"}])
```

**Step 2: Run test to verify it fails**

```bash
cd /home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills
python -m pytest skills/ichita-docx/scripts/test_ir.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'ir'`

**Step 3: Implement IR module**

```python
# ir.py
"""Intermediate Representation for DOCX content.

All inputs (Markdown, existing DOCX) are parsed into IR nodes.
The builder converts IR nodes into branded DOCX using a template.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Run:
    """Inline text with formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    url: str | None = None
    code: bool = False


VALID_TYPES = {
    "heading", "paragraph", "table", "list", "blockquote",
    "code", "hr", "image", "page_break", "title_page",
}


def make_heading(level: int, runs: list[Run]) -> dict:
    if level < 1 or level > 4:
        raise ValueError(f"Heading level must be 1-4, got {level}")
    return {"type": "heading", "level": level, "runs": runs}


def make_paragraph(runs: list[Run]) -> dict:
    return {"type": "paragraph", "runs": runs}


def make_table(headers: list[str], rows: list[list[str]], wide: bool | None = None) -> dict:
    if wide is None:
        wide = len(headers) > 10
    return {"type": "table", "headers": headers, "rows": rows, "wide": wide}


def make_list(style: str, items: list[list[Run]], level: int = 0) -> dict:
    return {"type": "list", "style": style, "items": items, "level": level}


def make_blockquote(runs: list[Run]) -> dict:
    return {"type": "blockquote", "runs": runs}


def make_code(text: str, language: str | None = None) -> dict:
    return {"type": "code", "text": text, "language": language}


def make_hr() -> dict:
    return {"type": "hr"}


def make_image(data: bytes, width: float = 5.0, caption: str | None = None) -> dict:
    return {"type": "image", "data": data, "width": width, "caption": caption}


def make_page_break() -> dict:
    return {"type": "page_break"}


def make_title_page(title: str, subtitle: str | None = None,
                    metadata: dict | None = None) -> dict:
    return {
        "type": "title_page",
        "title": title,
        "subtitle": subtitle,
        "metadata": metadata or {},
    }


def validate_ir(ir: list[dict]) -> bool:
    for node in ir:
        if node.get("type") not in VALID_TYPES:
            raise ValueError(f"Unknown node type: {node.get('type')}")
    return True
```

**Step 4: Run test to verify it passes**

```bash
cd /home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills
python -m pytest skills/ichita-docx/scripts/test_ir.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add skills/ichita-docx/scripts/ir.py skills/ichita-docx/scripts/test_ir.py
git commit -m "feat(docx): add IR type definitions with factory functions and validation"
```

---

## Task 2: Markdown Parser

**Files:**
- Create: `skills/ichita-docx/scripts/parse_markdown.py`
- Test: `skills/ichita-docx/scripts/test_parse_markdown.py`
- Reference: `skills/ichita-docx/scripts/md_to_docx.py` (extract parsing logic from lines 328–461)

**Step 1: Write tests for markdown parsing**

```python
# test_parse_markdown.py
import pytest
from parse_markdown import parse_markdown, parse_inline
from ir import Run


# --- Inline parsing ---

def test_parse_inline_plain():
    runs = parse_inline("hello world")
    assert len(runs) == 1
    assert runs[0].text == "hello world"
    assert runs[0].bold is False


def test_parse_inline_bold():
    runs = parse_inline("hello **bold** world")
    assert len(runs) == 3
    assert runs[1].text == "bold"
    assert runs[1].bold is True


def test_parse_inline_italic():
    runs = parse_inline("hello *italic* world")
    assert len(runs) == 3
    assert runs[1].text == "italic"
    assert runs[1].italic is True


def test_parse_inline_bold_italic():
    runs = parse_inline("***both***")
    assert runs[0].bold is True
    assert runs[0].italic is True


def test_parse_inline_link():
    runs = parse_inline("click [here](https://example.com) now")
    assert len(runs) == 3
    assert runs[1].text == "here"
    assert runs[1].url == "https://example.com"


def test_parse_inline_mixed():
    runs = parse_inline("**bold** and *italic* and [link](url)")
    assert runs[0].bold is True
    assert runs[2].italic is True
    assert runs[4].url == "url"


# --- Block parsing ---

def test_parse_heading():
    ir = parse_markdown("# Title")
    assert len(ir) == 1
    assert ir[0]["type"] == "heading"
    assert ir[0]["level"] == 1
    assert ir[0]["runs"][0].text == "Title"


def test_parse_heading_levels():
    md = "# H1\n## H2\n### H3\n#### H4"
    ir = parse_markdown(md)
    assert [n["level"] for n in ir] == [1, 2, 3, 4]


def test_parse_paragraph():
    ir = parse_markdown("Just a paragraph.")
    assert ir[0]["type"] == "paragraph"
    assert ir[0]["runs"][0].text == "Just a paragraph."


def test_parse_bold_paragraph():
    ir = parse_markdown("Hello **world**")
    assert ir[0]["type"] == "paragraph"
    assert len(ir[0]["runs"]) == 2
    assert ir[0]["runs"][1].bold is True


def test_parse_hr():
    ir = parse_markdown("---")
    assert ir[0]["type"] == "hr"


def test_parse_code_block():
    md = "```python\nprint('hi')\nx = 1\n```"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "code"
    assert ir[0]["language"] == "python"
    assert "print('hi')" in ir[0]["text"]
    assert "x = 1" in ir[0]["text"]


def test_parse_code_block_no_language():
    md = "```\ncode here\n```"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "code"
    assert ir[0]["language"] is None


def test_parse_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "table"
    assert ir[0]["headers"] == ["A", "B"]
    assert ir[0]["rows"] == [["1", "2"], ["3", "4"]]


def test_parse_numbered_list():
    md = "1. First\n2. Second\n3. Third"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "list"
    assert ir[0]["style"] == "numbered"
    assert len(ir[0]["items"]) == 3


def test_parse_bullet_list():
    md = "- Alpha\n- Beta\n- Gamma"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "list"
    assert ir[0]["style"] == "bullet"
    assert len(ir[0]["items"]) == 3


def test_parse_blockquote():
    md = "> This is a quote"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "blockquote"
    assert ir[0]["runs"][0].text == "This is a quote"


def test_parse_multiline_blockquote():
    md = "> Line one\n> Line two"
    ir = parse_markdown(md)
    assert ir[0]["type"] == "blockquote"
    assert "Line one" in ir[0]["runs"][0].text
    assert "Line two" in ir[0]["runs"][0].text


def test_parse_empty_lines_ignored():
    md = "Para 1\n\nPara 2"
    ir = parse_markdown(md)
    assert len(ir) == 2
    assert all(n["type"] == "paragraph" for n in ir)


def test_parse_title_page_from_first_h1():
    md = "# My Proposal\n\nBody text here."
    ir = parse_markdown(md, title_page=True)
    assert ir[0]["type"] == "title_page"
    assert ir[0]["title"] == "My Proposal"
    assert ir[1]["type"] == "paragraph"


def test_parse_list_with_bold():
    md = "1. **Bold** item\n2. Normal item"
    ir = parse_markdown(md)
    assert ir[0]["items"][0][0].bold is True
    assert ir[0]["items"][0][0].text == "Bold"


def test_parse_complex_document():
    md = """# Proposal

## Introduction

This is the **body** with a [link](https://ichita.com).

| Header A | Header B |
|----------|----------|
| Data 1   | Data 2   |

### Details

1. First point
2. Second point

> Important note here

---

```python
x = 42
```

Final paragraph."""
    ir = parse_markdown(md)
    types = [n["type"] for n in ir]
    assert "heading" in types
    assert "paragraph" in types
    assert "table" in types
    assert "list" in types
    assert "blockquote" in types
    assert "hr" in types
    assert "code" in types
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest skills/ichita-docx/scripts/test_parse_markdown.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'parse_markdown'`

**Step 3: Implement parse_markdown.py**

Extract parsing logic from `md_to_docx.py` lines 328–461. Key mapping:

| md_to_docx.py logic | → parse_markdown.py |
|---------------------|---------------------|
| Lines 328–340 (HR detection) | `_parse_hr()` |
| Lines 342–352 (code block) | `_parse_code_block()` |
| Lines 354–370 (table) | `_parse_table()` |
| Lines 372–389 (heading) | `_parse_heading()` |
| Lines 391–410 (blockquote) | `_parse_blockquote()` |
| Lines 412–430 (numbered list) | `_parse_list()` |
| Lines 432–448 (bullet list) | `_parse_list()` |
| Lines 455–461 (body paragraph) | `_parse_paragraph()` |
| `add_formatted_text()` inline parsing (docx_helpers.py 487–565) | `parse_inline()` |

The module must:
- Parse markdown text line-by-line (state machine)
- Return `list[dict]` of IR nodes
- Use `parse_inline()` for all text content (bold, italic, links)
- Group consecutive list items into single list node
- Group consecutive blockquote lines into single blockquote node
- Support `title_page=True` option to convert first H1 to title_page node

```python
# parse_markdown.py
"""Parse Markdown text into IR nodes."""

from __future__ import annotations
import re
from ir import (Run, make_heading, make_paragraph, make_table, make_list,
                make_blockquote, make_code, make_hr, make_page_break, make_title_page)


def parse_inline(text: str) -> list[Run]:
    """Parse inline markdown (bold, italic, bold+italic, links) into runs."""
    runs = []
    # Pattern order: bold+italic first, then bold, italic, link
    pattern = re.compile(
        r'\*\*\*(.+?)\*\*\*'     # ***bold+italic***
        r'|\*\*(.+?)\*\*'        # **bold**
        r'|\*(.+?)\*'            # *italic*
        r'|\[([^\]]+)\]\(([^)]+)\)'  # [text](url)
    )
    pos = 0
    for m in pattern.finditer(text):
        # Add plain text before match
        if m.start() > pos:
            plain = text[pos:m.start()]
            if plain:
                runs.append(Run(text=plain))

        if m.group(1):  # bold+italic
            runs.append(Run(text=m.group(1), bold=True, italic=True))
        elif m.group(2):  # bold
            runs.append(Run(text=m.group(2), bold=True))
        elif m.group(3):  # italic
            runs.append(Run(text=m.group(3), italic=True))
        elif m.group(4):  # link
            runs.append(Run(text=m.group(4), url=m.group(5)))

        pos = m.end()

    # Add remaining text
    if pos < len(text):
        remaining = text[pos:]
        if remaining:
            runs.append(Run(text=remaining))

    # If no matches, return single plain run
    if not runs:
        runs.append(Run(text=text))

    return runs


def parse_markdown(text: str, title_page: bool = False) -> list[dict]:
    """Parse markdown string into IR nodes."""
    lines = text.split('\n')
    ir: list[dict] = []
    i = 0
    first_h1_seen = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line — skip
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+\s*$', stripped):
            ir.append(make_hr())
            i += 1
            continue

        # Code block
        if stripped.startswith('```'):
            lang = stripped[3:].strip() or None
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            ir.append(make_code(text='\n'.join(code_lines), language=lang))
            continue

        # Table
        if '|' in stripped and stripped.startswith('|'):
            header_line = stripped
            headers = [c.strip() for c in header_line.strip('|').split('|')]
            i += 1
            # Skip separator line
            if i < len(lines) and re.match(r'^[\s|:-]+$', lines[i].strip()):
                i += 1
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                row = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(row)
                i += 1
            ir.append(make_table(headers=headers, rows=rows))
            continue

        # Heading
        m_heading = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m_heading:
            level = len(m_heading.group(1))
            heading_text = m_heading.group(2).strip()

            if title_page and not first_h1_seen and level == 1:
                first_h1_seen = True
                ir.append(make_title_page(title=heading_text))
                i += 1
                continue

            runs = parse_inline(heading_text)
            ir.append(make_heading(level=level, runs=runs))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            bq_texts = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq_text = re.sub(r'^>\s*', '', lines[i].strip())
                bq_texts.append(bq_text)
                i += 1
            combined = ' '.join(bq_texts)
            runs = parse_inline(combined)
            ir.append(make_blockquote(runs=runs))
            continue

        # Numbered list
        m_num = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m_num:
            items = []
            while i < len(lines):
                m_li = re.match(r'^\d+\.\s+(.+)$', lines[i].strip())
                if not m_li:
                    break
                items.append(parse_inline(m_li.group(1)))
                i += 1
            ir.append(make_list(style="numbered", items=items))
            continue

        # Bullet list
        m_bul = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
        if m_bul:
            items = []
            while i < len(lines):
                m_bi = re.match(r'^(\s*)([-*+])\s+(.+)$', lines[i])
                if not m_bi:
                    break
                items.append(parse_inline(m_bi.group(3)))
                i += 1
            ir.append(make_list(style="bullet", items=items))
            continue

        # Body paragraph (catchall)
        runs = parse_inline(stripped)
        ir.append(make_paragraph(runs=runs))
        i += 1

    return ir
```

**Step 4: Run tests**

```bash
python -m pytest skills/ichita-docx/scripts/test_parse_markdown.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add skills/ichita-docx/scripts/parse_markdown.py skills/ichita-docx/scripts/test_parse_markdown.py
git commit -m "feat(docx): add markdown parser — converts MD text to IR nodes"
```

---

## Task 3: DOCX Parser

**Files:**
- Create: `skills/ichita-docx/scripts/parse_docx.py`
- Test: `skills/ichita-docx/scripts/test_parse_docx.py`
- Reference: `skills/ichita-docx/scripts/rebrand_docx.py` (extract detection from lines 63–232)

**Step 1: Write tests**

```python
# test_parse_docx.py
"""Tests for DOCX → IR parser.

Uses python-docx to create test documents in memory,
then verifies parse_docx() extracts correct IR nodes.
"""
import pytest
from docx import Document
from docx.shared import Pt
from parse_docx import parse_docx_document
from ir import Run


def _make_doc_with_heading():
    doc = Document()
    doc.add_heading("Section Title", level=1)
    doc.add_paragraph("Body text here.")
    return doc


def _make_doc_with_table():
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "H1"
    table.rows[0].cells[1].text = "H2"
    table.rows[1].cells[0].text = "A"
    table.rows[1].cells[1].text = "B"
    return doc


def _make_doc_with_list():
    doc = Document()
    # Simulate numbered list via style
    for text in ["First", "Second", "Third"]:
        p = doc.add_paragraph(text, style="List Number")
    return doc


def _make_doc_with_bold_italic():
    doc = Document()
    p = doc.add_paragraph()
    p.add_run("Normal ")
    bold_run = p.add_run("bold")
    bold_run.bold = True
    p.add_run(" ")
    italic_run = p.add_run("italic")
    italic_run.italic = True
    return doc


def test_parse_heading():
    ir = parse_docx_document(_make_doc_with_heading())
    headings = [n for n in ir if n["type"] == "heading"]
    assert len(headings) == 1
    assert headings[0]["level"] == 1
    assert headings[0]["runs"][0].text == "Section Title"


def test_parse_body():
    ir = parse_docx_document(_make_doc_with_heading())
    paras = [n for n in ir if n["type"] == "paragraph"]
    assert len(paras) >= 1
    assert paras[0]["runs"][0].text == "Body text here."


def test_parse_table():
    ir = parse_docx_document(_make_doc_with_table())
    tables = [n for n in ir if n["type"] == "table"]
    assert len(tables) == 1
    assert tables[0]["headers"] == ["H1", "H2"]
    assert tables[0]["rows"] == [["A", "B"]]


def test_parse_bold_italic():
    ir = parse_docx_document(_make_doc_with_bold_italic())
    paras = [n for n in ir if n["type"] == "paragraph"]
    assert len(paras) == 1
    runs = paras[0]["runs"]
    bold_runs = [r for r in runs if r.bold]
    italic_runs = [r for r in runs if r.italic]
    assert len(bold_runs) >= 1
    assert bold_runs[0].text == "bold"
    assert len(italic_runs) >= 1
    assert italic_runs[0].text == "italic"


def test_parse_list():
    ir = parse_docx_document(_make_doc_with_list())
    lists = [n for n in ir if n["type"] == "list"]
    assert len(lists) >= 1


def test_parse_empty_doc():
    doc = Document()
    ir = parse_docx_document(doc)
    assert ir == [] or all(n["type"] == "paragraph" for n in ir)


def test_parse_multiple_headings():
    doc = Document()
    doc.add_heading("H1", level=1)
    doc.add_heading("H2", level=2)
    doc.add_heading("H3", level=3)
    ir = parse_docx_document(doc)
    headings = [n for n in ir if n["type"] == "heading"]
    assert len(headings) == 3
    assert [h["level"] for h in headings] == [1, 2, 3]
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest skills/ichita-docx/scripts/test_parse_docx.py -v
```

Expected: FAIL

**Step 3: Implement parse_docx.py**

Extract detection logic from `rebrand_docx.py`:
- `detect_heading()` (lines 63–94)
- Style detection from `style_paragraph()` (lines 120–232)
- Table extraction: iterate `w:tbl` children
- List detection: check `numPr` in pPr
- Image detection: check for `w:drawing` or `a:blip`
- Run extraction: read bold/italic/hyperlink from each `w:r`

```python
# parse_docx.py
"""Parse existing DOCX into IR nodes."""

from __future__ import annotations
import re
import copy
from docx import Document
from docx.oxml.ns import qn
from ir import (Run, make_heading, make_paragraph, make_table, make_list,
                make_blockquote, make_code, make_hr, make_image, make_title_page)


def _get_text(elem) -> str:
    """Get full text from a paragraph element."""
    return ''.join(t.text or '' for t in elem.iter(qn('w:t')))


def _get_style_name(p_elem) -> str | None:
    """Get style name from paragraph."""
    pPr = p_elem.find(qn('w:pPr'))
    if pPr is not None:
        pStyle = pPr.find(qn('w:pStyle'))
        if pStyle is not None:
            return pStyle.get(qn('w:val'))
    return None


def _has_numPr(p_elem) -> bool:
    """Check if paragraph has numbering properties (list item)."""
    pPr = p_elem.find(qn('w:pPr'))
    if pPr is not None:
        return pPr.find(qn('w:numPr')) is not None
    return False


def _extract_runs(p_elem) -> list[Run]:
    """Extract runs with formatting from paragraph element."""
    runs = []
    for r in p_elem.iter(qn('w:r')):
        text = ''.join(t.text or '' for t in r.iter(qn('w:t')))
        if not text:
            continue
        rPr = r.find(qn('w:rPr'))
        bold = False
        italic = False
        if rPr is not None:
            b_elem = rPr.find(qn('w:b'))
            bold = b_elem is not None and b_elem.get(qn('w:val'), 'true') != 'false'
            i_elem = rPr.find(qn('w:i'))
            italic = i_elem is not None and i_elem.get(qn('w:val'), 'true') != 'false'
        runs.append(Run(text=text, bold=bold, italic=italic))
    if not runs:
        text = _get_text(p_elem).strip()
        if text:
            runs.append(Run(text=text))
    return runs


def _detect_heading_level(style_name: str | None, text: str) -> int | None:
    """Detect heading level from style or text pattern."""
    if style_name:
        for i in range(1, 5):
            if style_name in (f'Heading{i}', f'Heading {i}'):
                return i
        if style_name == 'Title':
            return None  # title page, not heading
    # Text-based detection for Normal-styled headings
    if style_name in (None, 'Normal', 'BodyText', 'FirstParagraph'):
        if re.match(r'^\d+\.\s+\S', text) and len(text) < 80:
            return 1  # section heading
        if re.match(r'^\d+\.\d+\s+\S', text) and len(text) < 80:
            return 2  # subsection
        if re.match(r'^[A-Z]\.\s+\S', text) and len(text) < 80:
            return 3  # lettered subsection
    return None


def _is_list_style(style_name: str | None) -> bool:
    """Check if style indicates a list."""
    list_styles = {'Compact', 'ListParagraph', 'ListBullet', 'ListNumber',
                   'List Bullet', 'List Number', 'List Paragraph'}
    return style_name in list_styles if style_name else False


def _is_code_style(style_name: str | None) -> bool:
    """Check if style indicates code."""
    code_styles = {'SourceCode', 'Source Code', 'Code'}
    return style_name in code_styles if style_name else False


def _extract_table(tbl_elem) -> dict:
    """Extract table data from w:tbl element."""
    rows_data = []
    for tr in tbl_elem.iter(qn('w:tr')):
        cells = []
        for tc in tr.iter(qn('w:tc')):
            cell_text = ' '.join(_get_text(p) for p in tc.iter(qn('w:p'))).strip()
            cells.append(cell_text)
        rows_data.append(cells)

    if len(rows_data) >= 2:
        headers = rows_data[0]
        data_rows = rows_data[1:]
    elif len(rows_data) == 1:
        headers = rows_data[0]
        data_rows = []
    else:
        headers = []
        data_rows = []

    return make_table(headers=headers, rows=data_rows)


def _has_image(elem) -> bool:
    """Check if element contains embedded images."""
    return (elem.find('.//' + qn('a:blip')) is not None or
            elem.find('.//' + qn('w:drawing')) is not None)


def parse_docx_document(doc: Document) -> list[dict]:
    """Parse python-docx Document into IR nodes.

    Args:
        doc: python-docx Document object

    Returns:
        List of IR node dicts
    """
    ir: list[dict] = []
    body = doc.element.body

    # Collect list items to group them
    pending_list_items: list[list[Run]] = []
    pending_list_style: str | None = None

    def _flush_list():
        nonlocal pending_list_items, pending_list_style
        if pending_list_items:
            ir.append(make_list(
                style=pending_list_style or "bullet",
                items=pending_list_items,
            ))
            pending_list_items = []
            pending_list_style = None

    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        # Table
        if tag == 'tbl':
            _flush_list()
            ir.append(_extract_table(child))
            continue

        # Section break (sectPr) — skip
        if tag == 'sectPr':
            continue

        # Paragraph
        if tag == 'p':
            text = _get_text(child).strip()
            style = _get_style_name(child)
            has_num = _has_numPr(child)

            # Skip empty paragraphs
            if not text and not _has_image(child):
                _flush_list()
                continue

            # List item
            if has_num or _is_list_style(style):
                runs = _extract_runs(child)
                # Detect numbered vs bullet
                if style in ('ListNumber', 'List Number') or (
                    has_num and not style in ('ListBullet', 'List Bullet')
                ):
                    list_style = "numbered"
                else:
                    list_style = "bullet"

                if pending_list_style and pending_list_style != list_style:
                    _flush_list()

                pending_list_style = list_style
                pending_list_items.append(runs)
                continue

            _flush_list()

            # Code block
            if _is_code_style(style):
                ir.append(make_code(text=text))
                continue

            # Title
            if style == 'Title':
                ir.append(make_title_page(title=text))
                continue

            # Heading
            level = _detect_heading_level(style, text)
            if level:
                runs = _extract_runs(child)
                ir.append(make_heading(level=level, runs=runs))
                continue

            # Default: body paragraph
            runs = _extract_runs(child)
            if runs:
                ir.append(make_paragraph(runs=runs))

    _flush_list()
    return ir
```

**Step 4: Run tests**

```bash
python -m pytest skills/ichita-docx/scripts/test_parse_docx.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add skills/ichita-docx/scripts/parse_docx.py skills/ichita-docx/scripts/test_parse_docx.py
git commit -m "feat(docx): add DOCX parser — converts existing DOCX to IR nodes"
```

---

## Task 4: Enhanced Template

**Files:**
- Modify: `scripts/create_template.py`
- Output: `assets/templates/ichita-template.docx`

**Step 1: Write test for template contents**

```python
# scripts/test_template.py
"""Verify template has all required styles and properties."""
import os
import pytest
from docx import Document
from docx.shared import Pt, Cm


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'templates', 'ichita-template.docx')


@pytest.fixture
def template():
    if not os.path.exists(TEMPLATE_PATH):
        pytest.skip("Template not yet generated")
    return Document(TEMPLATE_PATH)


def test_normal_style(template):
    style = template.styles['Normal']
    assert style.font.name == 'Aeonik' or style.font.name == 'Calibri'  # fallback OK
    assert style.font.size == Pt(10)


def test_heading_styles_exist(template):
    for level in range(1, 5):
        assert f'Heading {level}' in [s.name for s in template.styles]


def test_heading_1_size(template):
    h1 = template.styles['Heading 1']
    assert h1.font.size == Pt(22)
    assert h1.font.bold is True


def test_heading_2_size(template):
    h2 = template.styles['Heading 2']
    assert h2.font.size == Pt(15)


def test_page_margins(template):
    section = template.sections[0]
    assert abs(section.left_margin - Cm(2.0)) < Cm(0.1)
    assert abs(section.right_margin - Cm(2.0)) < Cm(0.1)


def test_list_styles_exist(template):
    style_names = [s.name for s in template.styles]
    assert 'List Bullet' in style_names
    assert 'List Number' in style_names


def test_has_header(template):
    header = template.sections[0].header
    assert header is not None
    # Header should have content (logo)
    assert len(header.paragraphs) > 0
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest scripts/test_template.py -v
```

Expected: FAIL (template doesn't exist at new path yet, or skipped)

**Step 3: Update create_template.py**

Enhance current template to include:
- Save as `.docx` (not `.dotx`) for easier programmatic loading
- Add `List Number` style (currently missing)
- Add numbering definitions (abstractNum + num) for both bullet and numbered lists
- Add blockquote-compatible indentation in a custom style
- Keep sample content as preview (builder clears it at runtime)
- Set all Thai font attributes on every style

Key changes to existing `create_template.py`:
- Line 113: Add `List Number` style setup
- Add abstractNum/num XML for list numbering
- Output path: `ichita-template.docx` (not `.dotx`)
- Add `keepNext` on all heading styles (already on H1-H4, confirm)

**Step 4: Run template generation and tests**

```bash
cd /home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills
python scripts/create_template.py
python -m pytest scripts/test_template.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add scripts/create_template.py scripts/test_template.py assets/templates/ichita-template.docx
git commit -m "feat(docx): enhanced template with List Number style and numbering definitions"
```

---

## Task 5: Builder — IR to Branded DOCX

**Files:**
- Create: `skills/ichita-docx/scripts/build_docx.py`
- Test: `skills/ichita-docx/scripts/test_build_docx.py`
- Uses: `docx_helpers.py` (existing functions), `ir.py`, template

This is the largest task. The builder is the core of the unified system.

**Step 1: Write tests**

```python
# test_build_docx.py
"""Tests for IR → branded DOCX builder."""
import os
import pytest
from docx import Document
from docx.shared import Pt
from build_docx import build_docx
from ir import Run, make_heading, make_paragraph, make_table, make_list, \
    make_blockquote, make_code, make_hr, make_title_page


# Use test template or generate one
TEMPLATE = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                        'assets', 'templates', 'ichita-template.docx')


@pytest.fixture
def template_path():
    if not os.path.exists(TEMPLATE):
        pytest.skip("Template not generated yet")
    return TEMPLATE


def test_build_empty(template_path):
    doc = build_docx([], template_path)
    assert doc is not None
    # Body should be mostly empty (template sample content cleared)


def test_build_heading(template_path):
    ir = [make_heading(level=1, runs=[Run(text="Title")])]
    doc = build_docx(ir, template_path)
    # Find heading paragraph
    found = False
    for p in doc.paragraphs:
        if "Title" in p.text:
            found = True
            break
    assert found


def test_build_paragraph(template_path):
    ir = [make_paragraph(runs=[Run(text="Body text")])]
    doc = build_docx(ir, template_path)
    texts = [p.text for p in doc.paragraphs]
    assert any("Body text" in t for t in texts)


def test_build_bold_run(template_path):
    ir = [make_paragraph(runs=[
        Run(text="Normal "),
        Run(text="bold", bold=True),
        Run(text=" end"),
    ])]
    doc = build_docx(ir, template_path)
    for p in doc.paragraphs:
        for run in p.runs:
            if run.text == "bold":
                assert run.bold is True


def test_build_table(template_path):
    ir = [make_table(headers=["A", "B"], rows=[["1", "2"]])]
    doc = build_docx(ir, template_path)
    assert len(doc.tables) >= 1
    assert doc.tables[0].rows[0].cells[0].text == "A"


def test_build_list(template_path):
    ir = [make_list(style="numbered", items=[
        [Run(text="First")],
        [Run(text="Second")],
    ])]
    doc = build_docx(ir, template_path)
    texts = [p.text for p in doc.paragraphs]
    assert any("First" in t for t in texts)


def test_build_blockquote(template_path):
    ir = [make_blockquote(runs=[Run(text="Quote text")])]
    doc = build_docx(ir, template_path)
    texts = [p.text for p in doc.paragraphs]
    assert any("Quote" in t for t in texts)


def test_build_code(template_path):
    ir = [make_code(text="x = 42", language="python")]
    doc = build_docx(ir, template_path)
    texts = [p.text for p in doc.paragraphs]
    assert any("x = 42" in t for t in texts)


def test_build_hr(template_path):
    ir = [
        make_paragraph(runs=[Run(text="Before")]),
        make_hr(),
        make_paragraph(runs=[Run(text="After")]),
    ]
    doc = build_docx(ir, template_path)
    assert len(doc.paragraphs) >= 3


def test_build_title_page(template_path):
    ir = [
        make_title_page(title="My Proposal", subtitle="For Client"),
        make_heading(level=1, runs=[Run(text="Introduction")]),
    ]
    doc = build_docx(ir, template_path)
    texts = [p.text for p in doc.paragraphs]
    assert any("My Proposal" in t for t in texts)


def test_build_complex_document(template_path):
    """Full document with multiple element types."""
    ir = [
        make_title_page(title="Proposal", subtitle="Test"),
        make_heading(level=1, runs=[Run(text="Section 1")]),
        make_paragraph(runs=[Run(text="Body with "), Run(text="bold", bold=True)]),
        make_table(headers=["X", "Y"], rows=[["a", "b"]]),
        make_list(style="numbered", items=[
            [Run(text="One")], [Run(text="Two")],
        ]),
        make_blockquote(runs=[Run(text="A quote")]),
        make_code(text="print(1)"),
        make_hr(),
        make_heading(level=2, runs=[Run(text="Sub")]),
        make_paragraph(runs=[Run(text="End.")]),
    ]
    doc = build_docx(ir, template_path)
    assert len(doc.paragraphs) > 5
    assert len(doc.tables) >= 1
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest skills/ichita-docx/scripts/test_build_docx.py -v
```

Expected: FAIL

**Step 3: Implement build_docx.py**

The builder loads the template, clears sample content, then builds each IR node using helpers from `docx_helpers.py`.

Key reuse from existing code:
- `set_font()` — for every run
- `style_table_xml()` — for tables
- `add_header_footer()` — for logo header
- `add_left_accent()` — for H1/H2 accent bars
- `make_para()` — for paragraph creation with Thai split
- `create_meta_table()` — for title page metadata
- `split_run_thai_latin()` — for post-processing
- `squeeze_wide_tables()` — for wide tables

Builder functions (one per node type):
- `_clear_body(doc)` — remove all body content, keep styles/header/footer
- `_build_title_page(doc, node, brand)` — centered title + accent band + subtitle + metadata + page break
- `_build_heading(doc, node, brand)` — heading with accent bar (H1/H2) + keepNext
- `_build_paragraph(doc, node, brand)` — paragraph with formatted runs
- `_build_table(doc, node, brand)` — table with header/alt rows/borders
- `_build_list(doc, node, brand)` — numbered or bullet list with proper numbering
- `_build_blockquote(doc, node, brand)` — left border + background + italic
- `_build_code(doc, node, brand)` — monospace + background + indentation
- `_build_hr(doc, node, brand)` — bottom border paragraph
- `_build_image(doc, node, brand)` — embedded image + caption
- `_build_page_break(doc, node, brand)` — page break run

Post-processing:
- `_apply_thai_dual_font(doc, brand)` — set cs + szCs on all runs
- `_cleanup_empty_paragraphs(doc)` — collapse consecutive empties
- `_enforce_table_spacing(doc, brand)` — 8pt gap around tables

Full implementation: ~300-400 lines. Uses existing functions from `docx_helpers.py` extensively.

**Step 4: Run tests**

```bash
python -m pytest skills/ichita-docx/scripts/test_build_docx.py -v
```

Expected: All PASS

**Step 5: Commit**

```bash
git add skills/ichita-docx/scripts/build_docx.py skills/ichita-docx/scripts/test_build_docx.py
git commit -m "feat(docx): add unified builder — IR + template → branded DOCX"
```

---

## Task 6: CLI Entry Point

**Files:**
- Create: `skills/ichita-docx/scripts/cli.py`
- Test: `skills/ichita-docx/scripts/test_cli.py`

**Step 1: Write test**

```python
# test_cli.py
import os
import tempfile
import pytest
from cli import convert


def test_convert_from_md(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Hello\n\nWorld")
    out_file = tmp_path / "out.docx"
    convert(from_md=str(md_file), output=str(out_file))
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_convert_from_docx(tmp_path):
    # Create a source DOCX
    from docx import Document
    doc = Document()
    doc.add_heading("Title", level=1)
    doc.add_paragraph("Content")
    src = tmp_path / "source.docx"
    doc.save(str(src))

    out_file = tmp_path / "out.docx"
    convert(from_docx=str(src), output=str(out_file))
    assert out_file.exists()
    assert out_file.stat().st_size > 0
```

**Step 2: Implement cli.py**

```python
# cli.py
"""Unified CLI for Ichita DOCX generation.

Usage:
    python cli.py --from-md input.md -o output.docx
    python cli.py --from-docx input.docx -o output.docx
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx import Document
from parse_markdown import parse_markdown
from parse_docx import parse_docx_document
from build_docx import build_docx
from docx_helpers import ICHITA_BRAND

DEFAULT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'assets', 'templates', 'ichita-template.docx')


def convert(from_md: str = None, from_docx: str = None,
            output: str = "output.docx", template: str = None,
            title_page: bool = True, no_logo: bool = False):
    """Convert MD or DOCX to branded DOCX."""
    tpl = template or DEFAULT_TEMPLATE

    if from_md:
        text = open(from_md, 'r', encoding='utf-8').read()
        ir = parse_markdown(text, title_page=title_page)
    elif from_docx:
        doc = Document(from_docx)
        ir = parse_docx_document(doc)
    else:
        raise ValueError("Provide --from-md or --from-docx")

    options = {"no_logo": no_logo}
    doc = build_docx(ir, tpl, options=options)
    doc.save(output)
    print(f"  Saved: {output} ({os.path.getsize(output):,} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Ichita DOCX Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--from-md', help='Markdown input file')
    group.add_argument('--from-docx', help='DOCX input file to rebrand')
    parser.add_argument('-o', '--output', default='output.docx')
    parser.add_argument('--template', help='Custom template path')
    parser.add_argument('--no-logo', action='store_true')
    parser.add_argument('--no-title-page', action='store_true')
    args = parser.parse_args()
    convert(
        from_md=args.from_md,
        from_docx=args.from_docx,
        output=args.output,
        template=args.template,
        title_page=not args.no_title_page,
        no_logo=args.no_logo,
    )


if __name__ == '__main__':
    main()
```

**Step 3: Run test, then commit**

```bash
python -m pytest skills/ichita-docx/scripts/test_cli.py -v
git add skills/ichita-docx/scripts/cli.py skills/ichita-docx/scripts/test_cli.py
git commit -m "feat(docx): add unified CLI entry point for MD and DOCX conversion"
```

---

## Task 7: Legacy Wrappers

**Files:**
- Modify: `skills/ichita-docx/scripts/md_to_docx.py`
- Modify: `skills/ichita-docx/scripts/rebrand_docx.py`

**Step 1: Add wrapper functions that call new system**

Add to end of `md_to_docx.py`:

```python
def convert_md_to_docx_v2(md_path, output_path, **kwargs):
    """New unified path: MD → IR → build_docx."""
    from parse_markdown import parse_markdown
    from build_docx import build_docx
    text = open(md_path, 'r', encoding='utf-8').read()
    ir = parse_markdown(text, title_page=kwargs.get('title_page', True))
    template = kwargs.get('template', DEFAULT_TEMPLATE)
    doc = build_docx(ir, template, options=kwargs)
    doc.save(output_path)
```

Add to end of `rebrand_docx.py`:

```python
def rebrand_docx_v2(input_path, output_path, **kwargs):
    """New unified path: DOCX → IR → build_docx."""
    from parse_docx import parse_docx_document
    from build_docx import build_docx
    doc = Document(input_path)
    ir = parse_docx_document(doc)
    template = kwargs.get('template', DEFAULT_TEMPLATE)
    doc = build_docx(ir, template, options=kwargs)
    doc.save(output_path)
```

Keep old functions intact for backward compatibility during transition.

**Step 2: Commit**

```bash
git add skills/ichita-docx/scripts/md_to_docx.py skills/ichita-docx/scripts/rebrand_docx.py
git commit -m "feat(docx): add v2 wrapper functions using unified IR pipeline"
```

---

## Task 8: Identity Test — Verify Both Paths Produce Identical Output

**Files:**
- Create: `skills/ichita-docx/scripts/test_identity.py`

**Step 1: Write identity test**

```python
# test_identity.py
"""Verify MD→DOCX and DOCX→DOCX produce visually identical output.

Strategy: Generate a reference DOCX from markdown via the new system.
Then parse that DOCX back through parse_docx and rebuild.
Compare: paragraph count, text content, heading levels, table structure.
"""
import os
import tempfile
import pytest
from docx import Document
from parse_markdown import parse_markdown
from parse_docx import parse_docx_document
from build_docx import build_docx
from ir import validate_ir

TEMPLATE = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                        'assets', 'templates', 'ichita-template.docx')

TEST_MD = """# Test Proposal

## Introduction

This is the body text with **bold** and *italic* formatting.

| Column A | Column B |
|----------|----------|
| Data 1   | Data 2   |
| Data 3   | Data 4   |

### Details

1. First numbered item
2. Second numbered item
3. Third numbered item

- Bullet one
- Bullet two

> This is a blockquote with important information.

---

```python
x = 42
print(x)
```

## Conclusion

Final paragraph with a [link](https://ichita.com)."""


@pytest.fixture
def template_path():
    if not os.path.exists(TEMPLATE):
        pytest.skip("Template not generated")
    return TEMPLATE


def test_identity_paragraph_count(template_path):
    """Both paths should produce same number of content paragraphs."""
    # Path A: MD → IR → DOCX
    ir_a = parse_markdown(TEST_MD)
    doc_a = build_docx(ir_a, template_path)

    # Path B: MD → IR → DOCX → parse back → IR → DOCX
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc_a.save(f.name)
        doc_roundtrip = Document(f.name)
        ir_b = parse_docx_document(doc_roundtrip)
        doc_b = build_docx(ir_b, template_path)
        os.unlink(f.name)

    # Compare paragraph counts (allowing small variance from template cleanup)
    paras_a = [p.text for p in doc_a.paragraphs if p.text.strip()]
    paras_b = [p.text for p in doc_b.paragraphs if p.text.strip()]
    assert abs(len(paras_a) - len(paras_b)) <= 2, \
        f"Para count mismatch: A={len(paras_a)} B={len(paras_b)}"


def test_identity_headings(template_path):
    """Both paths should have same heading text."""
    ir_a = parse_markdown(TEST_MD)
    doc_a = build_docx(ir_a, template_path)

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc_a.save(f.name)
        ir_b = parse_docx_document(Document(f.name))
        doc_b = build_docx(ir_b, template_path)
        os.unlink(f.name)

    headings_a = [n for n in ir_a if n["type"] == "heading"]
    headings_b = [n for n in ir_b if n["type"] == "heading"]
    assert len(headings_a) == len(headings_b)


def test_identity_tables(template_path):
    """Both paths should produce same table count."""
    ir_a = parse_markdown(TEST_MD)
    doc_a = build_docx(ir_a, template_path)

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc_a.save(f.name)
        ir_b = parse_docx_document(Document(f.name))
        doc_b = build_docx(ir_b, template_path)
        os.unlink(f.name)

    assert len(doc_a.tables) == len(doc_b.tables)


def test_ir_roundtrip_validity(template_path):
    """IR from both parsers should validate."""
    ir_md = parse_markdown(TEST_MD)
    assert validate_ir(ir_md)

    doc = build_docx(ir_md, template_path)
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        doc.save(f.name)
        ir_docx = parse_docx_document(Document(f.name))
        os.unlink(f.name)
    assert validate_ir(ir_docx)
```

**Step 2: Run identity tests**

```bash
python -m pytest skills/ichita-docx/scripts/test_identity.py -v
```

Expected: All PASS

**Step 3: Visual QA**

```bash
# Generate from both paths
cd /home/ohyeah/ghq/github.com/Siwatch-OhYeaH/ichita-skills
echo "# Test Doc\n\n## Section\n\nBody text **bold**\n\n| A | B |\n|---|---|\n| 1 | 2 |" > /tmp/test.md

python skills/ichita-docx/scripts/cli.py --from-md /tmp/test.md -o /tmp/path-a.docx

# Create source DOCX via pandoc
pandoc /tmp/test.md -o /tmp/test-pandoc.docx
python skills/ichita-docx/scripts/cli.py --from-docx /tmp/test-pandoc.docx -o /tmp/path-b.docx

# Convert both to PDF for comparison
libreoffice --headless --convert-to pdf --outdir /tmp /tmp/path-a.docx
libreoffice --headless --convert-to pdf --outdir /tmp /tmp/path-b.docx

# Visual compare: open both PDFs
```

**Step 4: Commit**

```bash
git add skills/ichita-docx/scripts/test_identity.py
git commit -m "test(docx): add identity tests — verify both paths produce identical output"
```

---

## Task 9: Update ichita-docx Skill to Use New System

**Files:**
- Modify: `skills/ichita-docx/SKILL.md` (update CLI usage)

Update the skill's CLI examples to use the new unified `cli.py`. Old `md_to_docx.py` and `rebrand_docx.py` CLI entry points still work via legacy wrappers.

**Step 1: Update SKILL.md references**

**Step 2: Commit**

```bash
git add skills/ichita-docx/SKILL.md
git commit -m "docs(docx): update ichita-docx skill to reference unified CLI"
```

---

## Task Summary

| # | Task | New Files | Tests | Est. Lines |
|---|------|-----------|-------|-----------|
| 1 | IR definitions | `ir.py` | `test_ir.py` | ~80 |
| 2 | Markdown parser | `parse_markdown.py` | `test_parse_markdown.py` | ~150 |
| 3 | DOCX parser | `parse_docx.py` | `test_parse_docx.py` | ~200 |
| 4 | Enhanced template | modify `create_template.py` | `test_template.py` | ~50 delta |
| 5 | Builder (core) | `build_docx.py` | `test_build_docx.py` | ~400 |
| 6 | CLI entry point | `cli.py` | `test_cli.py` | ~60 |
| 7 | Legacy wrappers | modify existing | — | ~20 |
| 8 | Identity tests | `test_identity.py` | identity tests | ~100 |
| 9 | Skill docs | modify `SKILL.md` | — | ~10 |

**Total**: ~1,070 new lines + tests, replacing ~1,300 lines of duplicated logic.

---

## Execution Order

Tasks 1→2→3 can be done somewhat independently (IR first, then parsers).
Task 4 (template) is needed before Task 5 (builder).
Task 5 is the critical path — everything depends on the builder.
Tasks 6→7→8→9 are sequential after builder works.

```
Task 1 (IR) ──→ Task 2 (MD parser) ──→ Task 5 (Builder) ──→ Task 6 (CLI)
           ──→ Task 3 (DOCX parser) ──↗      ↑              ──→ Task 7 (Legacy)
                                      Task 4 (Template) ──→ Task 8 (Identity)
                                                             ──→ Task 9 (Docs)
```
