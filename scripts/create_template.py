#!/usr/bin/env python3
"""Generate Ichita DOCX template (.dotx) from ICHITA_BRAND spec.

Run: python scripts/create_template.py
Output: assets/templates/ichita-document.dotx
"""

import os
import sys

# Add skills scripts to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'skills', 'ichita-docx', 'scripts'))

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from docx_helpers import ICHITA_BRAND, resolve_font, add_header_footer


def _find_logo():
    """Find Ichita logo."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base, "assets/logos/ichita-logo-black.png"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def create_template():
    brand = ICHITA_BRAND
    colors = brand["colors"]
    typo = brand["typography"]
    fonts = brand["fonts"]

    font_name, warnings = resolve_font(brand)
    for w in warnings:
        print(f"  [font] {w}")

    doc = Document()

    # -- Page setup --
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    margin = Cm(brand["margins"]["portrait"])
    section.top_margin = margin
    section.bottom_margin = margin
    section.left_margin = margin
    section.right_margin = margin
    section.header_distance = Cm(1.27)

    # -- Normal style --
    style = doc.styles['Normal']
    style.font.name = font_name
    style.font.size = Pt(typo["body"]["size"])
    style.font.color.rgb = RGBColor.from_string(colors[typo["body"]["color"]])
    style.paragraph_format.space_before = Pt(typo["body"]["before"])
    style.paragraph_format.space_after = Pt(typo["body"]["after"])
    # Set Thai font on complex script / east asia
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:cs'), fonts["thai"])
    rFonts.set(qn('w:eastAsia'), fonts["thai"])

    # -- Heading styles --
    for level, key in [(1, "h1"), (2, "h2"), (3, "h3"), (4, "h4")]:
        h = typo[key]
        hs = doc.styles[f'Heading {level}']
        hs.font.name = font_name
        hs.font.size = Pt(h["size"])
        hs.font.bold = h["bold"]
        hs.font.color.rgb = RGBColor.from_string(colors[h["color"]])
        hs.paragraph_format.space_before = Pt(h["before"])
        hs.paragraph_format.space_after = Pt(h["after"])
        hs.paragraph_format.keep_with_next = True
        # Set Thai font
        h_rPr = hs.element.get_or_add_rPr()
        h_rFonts = h_rPr.find(qn('w:rFonts'))
        if h_rFonts is None:
            h_rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            h_rPr.insert(0, h_rFonts)
        h_rFonts.set(qn('w:cs'), fonts["thai"])
        h_rFonts.set(qn('w:eastAsia'), fonts["thai"])

    # -- Title style --
    t = typo["title"]
    ts = doc.styles['Title']
    ts.font.name = font_name
    ts.font.size = Pt(t["size"])
    ts.font.bold = t["bold"]
    ts.font.color.rgb = RGBColor.from_string(colors[t["color"]])
    ts.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # -- Caption style --
    c = typo["caption"]
    cs = doc.styles['Caption']
    cs.font.name = font_name
    cs.font.size = Pt(c["size"])
    cs.font.color.rgb = RGBColor.from_string(colors[c["color"]])
    cs.paragraph_format.space_before = Pt(c["before"])
    cs.paragraph_format.space_after = Pt(c["after"])

    # -- List Bullet style --
    if 'List Bullet' in doc.styles:
        lb = doc.styles['List Bullet']
        lb.font.name = font_name
        lb.font.size = Pt(typo["bullet"]["size"])

    # -- Add sample content to show styles --
    # Title
    p = doc.add_paragraph("Document Title", style='Title')

    # Page break after title
    run = p.runs[0] if p.runs else p.add_run()
    run.add_break()

    # Heading examples
    doc.add_heading("Heading 1 — Section Title", level=1)
    doc.add_paragraph(
        "Body text example. Ichita standard document template with "
        "Aeonik font and professional formatting.")

    doc.add_heading("Heading 2 — Subsection", level=2)
    doc.add_paragraph(
        "More body text demonstrating the standard paragraph formatting.")

    doc.add_heading("Heading 3 — Detail", level=3)
    doc.add_paragraph("Detail level content with standard spacing.")

    doc.add_heading("Heading 4 — Minor", level=4)
    doc.add_paragraph("Minor heading content.")

    # Sample table
    table = doc.add_table(rows=4, cols=3)
    headers = ["Property", "Value", "Notes"]
    for j, h_text in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = h_text
        # Dark header styling
        shading = parse_xml(
            f'<w:shd {nsdecls("w")} w:fill="{colors["table_header"]}"'
            f' w:val="clear"/>')
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.paragraphs[0].runs[0].font.bold = True
        cell._tc.get_or_add_tcPr().append(shading)

    sample_data = [
        ["Font", "Aeonik", "Latin text"],
        ["Thai Font", "Bai Jamjuree", "Scale 0.9x"],
        ["Body Size", "12pt", "Standard"],
    ]
    for ri, row_data in enumerate(sample_data):
        for j, cell_text in enumerate(row_data):
            table.rows[ri + 1].cells[j].text = cell_text
            if ri % 2 == 1:
                shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:fill="{colors["table_alt"]}"'
                    f' w:val="clear"/>')
                table.rows[ri + 1].cells[j]._tc.get_or_add_tcPr().append(
                    shading)

    # -- Header with logo --
    logo = _find_logo()
    add_header_footer(doc, logo_path=logo,
                      accent_color=colors["accent"],
                      font_name=font_name,
                      dark_color=colors["dark"])

    # -- Save as .dotx --
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets', 'templates')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'ichita-document.dotx')
    doc.save(out_path)

    size = os.path.getsize(out_path)
    print(f"\n  Template saved: {out_path}")
    print(f"  Size: {size:,} bytes")
    print(f"  Font: {font_name} + {fonts['thai']} (Thai)")
    print(f"  Margins: {brand['margins']['portrait']}cm")
    print(f"  Styles: Title, Heading 1-4, Normal, Caption, List Bullet")


if __name__ == "__main__":
    create_template()
