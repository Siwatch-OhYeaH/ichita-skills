#!/usr/bin/env python3
"""
Convert Markdown to a professionally formatted Ichita-branded DOCX.

Based on P'Schirapong's md_to_docx.py — adapted as reusable CLI tool.
Handles: headings, tables, code blocks, bold/italic, bullet/numbered lists,
blockquotes, horizontal rules, links, and regular paragraphs.

Usage:
    python md_to_docx.py INPUT.md OUTPUT.docx [--no-logo] [--font NAME] [--margin CM]
"""

import argparse
import os
import re
import sys

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

# Allow importing from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_helpers import (
    ICHITA_BRAND, resolve_font, set_cell_shading_docx, set_table_borders,
    add_formatted_text, add_header_footer,
)


# ── Logo path (auto-detect repo root) ──────────────────────────────────────
def _find_repo_root():
    """Walk up from script dir to find repo root (has assets/ dir)."""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(d, "assets")):
            return d
        d = os.path.dirname(d)
    return os.path.dirname(os.path.abspath(__file__))

def _find_logo(repo_root):
    """Find Ichita logo in known asset locations."""
    candidates = [
        os.path.join(repo_root, "assets/logos/ichita-logo-black.png"),
        os.path.join(repo_root, "assets/ichita/logos/ichita-logo-black.png"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

REPO_ROOT = _find_repo_root()
DEFAULT_LOGO = _find_logo(REPO_ROOT)


# ── Table Helpers ───────────────────────────────────────────────────────────

def _parse_table_line(line):
    cells = line.strip().strip('|').split('|')
    return [c.strip() for c in cells]


def _is_separator_line(line):
    stripped = line.strip().strip('|')
    return all(re.match(r'^[\s\-:]+$', p) for p in stripped.split('|'))


def _add_cell_text(cell, text, bold_header=False, font_name="Calibri",
                   font_size=Pt(10)):
    """Add formatted text to a table cell, preserving bold markdown."""
    para = cell.paragraphs[0]
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(2)

    if bold_header:
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        run = para.add_run(clean)
        run.font.bold = True
        run.font.name = font_name
        run.font.size = font_size
        run.font.color.rgb = RGBColor.from_string(ICHITA_BRAND["colors"]["dark"])
    else:
        pattern = re.compile(r'\*\*(.+?)\*\*')
        last_end = 0
        for match in pattern.finditer(text):
            before = text[last_end:match.start()]
            if before:
                run = para.add_run(before)
                run.font.name = font_name
                run.font.size = font_size
            run = para.add_run(match.group(1))
            run.font.bold = True
            run.font.name = font_name
            run.font.size = font_size
            last_end = match.end()
        remaining = text[last_end:]
        if remaining:
            run = para.add_run(remaining)
            run.font.name = font_name
            run.font.size = font_size


def _add_table(doc, header_cells, data_rows, font_name, colors):
    """Create a formatted table from parsed markdown rows."""
    num_cols = len(header_cells)
    normalized = []
    for row in data_rows:
        while len(row) < num_cols:
            row.append("")
        normalized.append(row[:num_cols])

    table = doc.add_table(rows=1 + len(normalized), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    set_table_borders(table, colors["border"])

    # Header row
    for j, cell_text in enumerate(header_cells):
        if j < num_cols:
            _add_cell_text(table.rows[0].cells[j], cell_text,
                           bold_header=True, font_name=font_name)
            set_cell_shading_docx(table.rows[0].cells[j], colors["table_header"])

    # Data rows
    for ri, row_data in enumerate(normalized):
        row = table.rows[ri + 1]
        for j, cell_text in enumerate(row_data):
            if j < num_cols:
                _add_cell_text(row.cells[j], cell_text, font_name=font_name)
                if ri % 2 == 1:
                    set_cell_shading_docx(row.cells[j], colors["table_alt"])

    # Spacer after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(2)
    sp.paragraph_format.space_after = Pt(2)


def _add_code_block(doc, code_lines):
    """Add a code block with monospace font and grey background."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.right_indent = Inches(0.3)

    pPr = p._p.get_or_add_pPr()
    pPr.append(parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="F2F2F2" w:val="clear"/>'))

    run = p.add_run('\n'.join(code_lines))
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)


# ── Main Conversion ────────────────────────────────────────────────────────

def convert_md_to_docx(input_path, output_path, font_name=None,
                       margin_cm=None, logo_path=None, no_logo=False):
    """Convert a Markdown file to a branded DOCX."""
    brand = ICHITA_BRAND
    colors = brand["colors"]
    typo = brand["typography"]

    # Resolve font
    if font_name is None:
        font_name, warnings = resolve_font(brand)
        for w in warnings:
            print(f"  [font] {w}")
    else:
        warnings = []

    # Resolve margin
    if margin_cm is None:
        margin_cm = brand["margins"]["portrait"]

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = Document()

    # Default style
    style = doc.styles['Normal']
    style.font.name = font_name
    style.font.size = Pt(typo["body"]["size"])
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.space_before = Pt(3)

    # Heading styles from brand typography
    heading_map = {
        1: ("h1", RGBColor.from_string(colors["dark"])),
        2: ("h2", RGBColor.from_string(colors["dark"])),
        3: ("h3", RGBColor.from_string(colors["accent"])),
        4: ("h3", RGBColor.from_string(colors["accent"])),
    }
    heading_sizes = {1: 20, 2: 16, 3: 13, 4: 11}
    heading_spacing = {
        1: (18, 8), 2: (14, 6), 3: (10, 6), 4: (8, 4),
    }

    for level in range(1, 5):
        hs = doc.styles[f'Heading {level}']
        hs.font.name = font_name
        hs.font.size = Pt(heading_sizes[level])
        hs.font.color.rgb = heading_map[level][1]
        hs.font.bold = True
        sb, sa = heading_spacing[level]
        hs.paragraph_format.space_before = Pt(sb)
        hs.paragraph_format.space_after = Pt(sa)

    # List style
    if 'List Bullet' in doc.styles:
        lb = doc.styles['List Bullet']
        lb.font.name = font_name
        lb.font.size = Pt(typo["body"]["size"])

    # Margins
    for section in doc.sections:
        section.top_margin = Cm(margin_cm)
        section.bottom_margin = Cm(margin_cm)
        section.left_margin = Cm(margin_cm)
        section.right_margin = Cm(margin_cm)

    # Parse and convert
    i = 0
    first_h1 = True
    base_size = Pt(typo["body"]["size"])

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n')

        # Horizontal rule
        if re.match(r'^---+\s*$', stripped):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            pPr = p._p.get_or_add_pPr()
            pPr.append(parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:bottom w:val="single" w:sz="6" w:space="1"'
                f'            w:color="{colors["border"]}"/>'
                f'</w:pBdr>'))
            i += 1
            continue

        # Code block
        if stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].rstrip('\n').startswith('```'):
                code_lines.append(lines[i].rstrip('\n'))
                i += 1
            if i < len(lines):
                i += 1
            _add_code_block(doc, code_lines)
            continue

        # Table
        if stripped.startswith('|') and '|' in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].rstrip('\n').strip().startswith('|'):
                table_lines.append(lines[i].rstrip('\n'))
                i += 1
            if len(table_lines) < 2:
                for tl in table_lines:
                    p = doc.add_paragraph()
                    add_formatted_text(p, tl.strip(), font_name, base_size)
                continue
            header_cells = _parse_table_line(table_lines[0])
            data_start = 2 if len(table_lines) > 1 and _is_separator_line(table_lines[1]) else 1
            data_rows = [_parse_table_line(tl) for tl in table_lines[data_start:]
                         if not _is_separator_line(tl)]
            _add_table(doc, header_cells, data_rows, font_name, colors)
            continue

        # Headings
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if level == 1 and first_h1:
                p = doc.add_heading('', level=1)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', heading_text)
                run = p.add_run(clean)
                run.font.name = font_name
                run.font.size = Pt(typo["title"]["size"])
                run.font.color.rgb = RGBColor.from_string(colors["dark"])
                run.font.bold = True
                first_h1 = False
            else:
                p = doc.add_heading('', level=level)
                size = Pt(heading_sizes[level])
                add_formatted_text(p, heading_text, font_name, size)
                for run in p.runs:
                    run.font.color.rgb = heading_map[level][1]
                    run.font.bold = True
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            quote_text = stripped.lstrip('>').strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            pPr = p._p.get_or_add_pPr()
            pPr.append(parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:left w:val="single" w:sz="18" w:space="8"'
                f'          w:color="{colors["accent"]}"/>'
                f'</w:pBdr>'))
            pPr.append(parse_xml(
                f'<w:shd {nsdecls("w")} w:fill="{colors["off_white"]}" w:val="clear"/>'))
            add_formatted_text(p, quote_text, font_name, base_size, is_blockquote=True)
            i += 1
            continue

        # Numbered list
        numbered_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if numbered_match:
            num = numbered_match.group(1)
            item_text = numbered_match.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(f"{num}. ")
            run.font.name = font_name
            run.font.size = base_size
            run.font.bold = True
            add_formatted_text(p, item_text, font_name, base_size)
            i += 1
            continue

        # Bullet point
        bullet_match = re.match(r'^(\s*)([-*+])\s+(.+)$', stripped)
        if bullet_match:
            indent_spaces = len(bullet_match.group(1))
            bullet_text = bullet_match.group(3)
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if indent_spaces >= 2:
                p.paragraph_format.left_indent = Inches(
                    0.6 + (indent_spaces // 2) * 0.25)
            p.clear()
            add_formatted_text(p, bullet_text, font_name, base_size)
            i += 1
            continue

        # Empty line
        if not stripped.strip():
            i += 1
            continue

        # Regular paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(6)
        add_formatted_text(p, stripped, font_name, base_size)
        i += 1

    # Logo header (optional)
    if not no_logo:
        logo = logo_path or DEFAULT_LOGO
        add_header_footer(doc, logo_path=logo,
                          accent_color=colors["accent"],
                          font_name=font_name,
                          dark_color=colors["dark"])

    doc.save(output_path)

    # Report
    size = os.path.getsize(output_path)
    print(f"Saved: {output_path}")
    print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"  Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}")
    print(f"  Font: {font_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown to Ichita-branded DOCX")
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument("output", help="Output DOCX file")
    parser.add_argument("--no-logo", action="store_true",
                        help="Skip logo header")
    parser.add_argument("--font", default=None,
                        help="Override font name (default: auto-detect)")
    parser.add_argument("--margin", type=float, default=None,
                        help="Page margin in cm (default: 2.5)")
    args = parser.parse_args()

    convert_md_to_docx(
        args.input, args.output,
        font_name=args.font,
        margin_cm=args.margin,
        no_logo=args.no_logo,
    )


if __name__ == "__main__":
    main()
