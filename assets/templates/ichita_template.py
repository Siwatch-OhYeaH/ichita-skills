"""ICHITA Standard Document Template Module

Reusable module for producing brand-compliant ICHITA documents.
Header: doc code + "ICHITA Co., Ltd." with blue underline
Footer: doc code + Page X / Y centered
Fonts: Aeonik (EN), Browallia New (TH), Calibri (fallback)
Colors: ICHITA brand palette

Usage:
    from ichita_template import *
    doc = create_document("SKT-PILOT-OPR")
    add_title(doc, "My Report Title")
    add_section_heading(doc, "Section 1")
    doc.save("output.docx")
"""

import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# === Paths ===
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_MODULE_DIR, "assets")
BASE_TEMPLATE = os.path.join(ASSETS_DIR, "ichita-base-template.docx")

# === Colors ===
ICHITA_BLUE = RGBColor(0x1F, 0x4E, 0x79)
ICHITA_LIGHT = RGBColor(0xD6, 0xE4, 0xF0)
BRAND_BLUE = RGBColor(0x29, 0x78, 0xFF)
BRAND_DARK = RGBColor(0x26, 0x33, 0x38)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
GRAY = RGBColor(0x80, 0x80, 0x80)
ZEBRA = RGBColor(0xF2, 0xF2, 0xF2)

# Color hex strings (for XML operations)
ICHITA_BLUE_HEX = "1F4E79"
ICHITA_LIGHT_HEX = "D6E4F0"
ZEBRA_HEX = "F2F2F2"

# Chart colors
CHART_FEED = "#1F4E79"
CHART_STAGE1 = "#C00000"
CHART_STAGE2 = "#D06B28"

# === Fonts ===
FONT_EN = "Aeonik"
FONT_TH = "Browallia New"
FONT_FALLBACK = "Calibri"

# Footer info
ICHITA_ADDRESS = "399/75 Phongpetnivet, Prachacheun Rd., Jatujak, Bangkok 10900"
ICHITA_TEL = "Tel: 66 2585 1337, 66 2585 2123 / Fax: 66 2585 3213"


# === Document Creation ===

def create_document(doc_code="", version="v1", orientation="portrait"):
    """Create a new ICHITA-branded document from the base template.

    The base template uses the SMS Technical Proposal standard:
    - Header: ICHITA wordmark + X symbol image (full width)
    - Footer: QR code + address + tel/fax + page number
    - different_first_page: True (both identical)

    Args:
        doc_code: Document code (not used in header — image-based)
        version: Version string (not used in footer — standard format)
        orientation: "portrait" or "landscape"

    Returns:
        Document with ICHITA header/footer, A4 page, proper margins
    """
    doc = Document(BASE_TEMPLATE)

    # Clear any leftover body content from template
    body = doc.element.body
    children_to_remove = []
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag != "sectPr":
            children_to_remove.append(child)
    for child in children_to_remove:
        body.remove(child)

    # Set page dimensions (A4) — keep template margins which match SMS standard
    for section in doc.sections:
        if orientation == "landscape":
            section.page_width = Cm(29.7)
            section.page_height = Cm(21.0)
        else:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)

    return doc


# === Styling Helpers ===

def set_cell_shading(cell, color_hex):
    """Set cell background color.

    Args:
        cell: Table cell
        color_hex: Hex color string without '#' (e.g., "1F4E79")
    """
    tcPr = cell._element.get_or_add_tcPr()
    shading_elm = tcPr.find(qn("w:shd"))
    if shading_elm is None:
        shading_elm = tcPr.makeelement(qn("w:shd"), {})
        tcPr.append(shading_elm)
    shading_elm.set(qn("w:fill"), color_hex)
    shading_elm.set(qn("w:val"), "clear")


def format_header_cell(cell, text, font_size=8):
    """Format a table header cell with ICHITA blue background and white text."""
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(font_size)
    run.font.color.rgb = WHITE
    run.font.bold = True
    run.font.name = FONT_FALLBACK
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    set_cell_shading(cell, ICHITA_BLUE_HEX)


def format_data_cell(cell, text="", font_size=8, bold=False, align="center"):
    """Format a table data cell."""
    cell.text = ""
    p = cell.paragraphs[0]
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(str(text))
    run.font.size = Pt(font_size)
    run.font.name = FONT_FALLBACK
    run.font.bold = bold
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)


def remove_table_borders(table):
    """Remove all borders from a table."""
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = tbl.makeelement(qn("w:tblPr"), {})
        tbl.insert(0, tblPr)
    borders = tblPr.find(qn("w:tblBorders"))
    if borders is None:
        borders = tbl.makeelement(qn("w:tblBorders"), {})
        tblPr.append(borders)
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        el = tbl.makeelement(qn(f"w:{side}"), {})
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")
        existing = borders.find(qn(f"w:{side}"))
        if existing is not None:
            borders.remove(existing)
        borders.append(el)


def add_zebra_shading(table, start_row=1):
    """Add alternating row shading (zebra stripes) to a table.

    Args:
        table: Table object
        start_row: First data row index (skip header rows)
    """
    for i, row in enumerate(table.rows):
        if i < start_row:
            continue
        if (i - start_row) % 2 == 1:
            for cell in row.cells:
                set_cell_shading(cell, ZEBRA_HEX)


# === Content Helpers ===

def add_title(doc, text):
    """Add a centered title in 18pt bold ICHITA blue."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = ICHITA_BLUE
    run.font.name = FONT_FALLBACK
    return p


def add_subtitle(doc, text):
    """Add a centered subtitle in 14pt ICHITA blue."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(14)
    run.font.color.rgb = ICHITA_BLUE
    run.font.name = FONT_FALLBACK
    return p


def add_section_heading(doc, text):
    """Add a section heading in 12pt bold ICHITA blue."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = ICHITA_BLUE
    return p


def add_note(doc, text):
    """Add a small italic gray note."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(8)
    run.font.italic = True
    run.font.color.rgb = GRAY
    return p


def add_info_table(doc, pairs):
    """Add a borderless key-value info table.

    Args:
        doc: Document
        pairs: List of (key, value) tuples
    """
    table = doc.add_table(rows=len(pairs), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (key, val) in enumerate(pairs):
        cell_k = table.cell(i, 0)
        cell_k.text = ""
        p = cell_k.paragraphs[0]
        run = p.add_run(key)
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.name = FONT_FALLBACK
        run.font.color.rgb = ICHITA_BLUE
        cell_k.width = Cm(5)

        cell_v = table.cell(i, 1)
        cell_v.text = ""
        p = cell_v.paragraphs[0]
        run = p.add_run(str(val))
        run.font.size = Pt(10)
        run.font.name = FONT_FALLBACK
    remove_table_borders(table)
    return table


# === PDF Conversion ===

def to_pdf(docx_path, output_path=None):
    """Convert DOCX to PDF using docx2pdf (Windows COM automation).

    Args:
        docx_path: Path to the DOCX file
        output_path: Optional output path (defaults to same name with .pdf)

    Returns:
        Path to the generated PDF
    """
    from docx2pdf import convert

    docx_path = os.path.abspath(docx_path)
    if output_path is None:
        output_path = os.path.splitext(docx_path)[0] + ".pdf"
    else:
        output_path = os.path.abspath(output_path)

    convert(docx_path, output_path)
    return output_path
