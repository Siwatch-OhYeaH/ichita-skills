#!/usr/bin/env python3
"""
Rebrand an existing DOCX to Ichita brand identity.

Based on P'Schirapong's rebrand_skt_ichita.py — adapted as reusable CLI tool.
Removes source-specific styling, applies Ichita brand fonts/colors/tables,
adds logo header, optional title page redesign.

Usage:
    python rebrand_docx.py INPUT.docx OUTPUT.docx [--no-title-page] [--font NAME] [--logo PATH]
"""

import argparse
import copy
import os
import re
import sys

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# Allow importing from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_helpers import (
    ICHITA_BRAND, resolve_font,
    set_font, set_cell_shading, ensure_pPr, get_style_id, get_text,
    add_left_accent, add_bottom_band, set_alignment, copy_image_rels,
    make_para, style_table_xml, add_header_footer, squeeze_wide_tables,
    _has_images,
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


# ── Heading Detection (generic — no SKT-specific checks) ───────────────────

def detect_heading(text):
    """Detect heading type from Normal-styled paragraph text.

    Returns 'section', 'subsection', 'caption', or None.
    """
    text = text.strip()
    if not text:
        return None

    # Check Word built-in heading style patterns
    # Section headings: "1. Title", "2. Title", "Appendix"
    if re.match(r'^\d+\.\s+\S', text) and len(text) < 80:
        return 'section'
    if text.lower() == 'appendix':
        return 'section'

    # Subsection: "3.1 Title", "A. Title", "B. Title"
    if re.match(r'^\d+\.\d+\s+\S', text) and len(text) < 80:
        return 'subsection'
    if re.match(r'^[A-Z]\.?\s*\S', text) and len(text) < 80:
        return 'subsection'

    # Figure/table captions (Thai and English patterns)
    caption_patterns = [
        r'^(รูปที่|ตารางที่|Figure|Table|Fig\.)\s*\d',
    ]
    for pat in caption_patterns:
        if re.match(pat, text, re.IGNORECASE):
            return 'caption'

    return None


# ── Paragraph Styling ──────────────────────────────────────────────────────

def _style_runs(p_elem, font_name, size_pt, color_hex, bold=None,
                latin_offset=1.5):
    """Apply brand font to all text runs in a paragraph (skip image runs)."""
    for run in p_elem.findall('.//' + qn('w:r')):
        if _has_images(run):
            continue
        set_font(run, font_name=font_name, size_pt=size_pt,
                 color_hex=color_hex, bold=bold, latin_offset=latin_offset)


def style_paragraph(p_elem, text, font_name, colors, latin_offset=1.5):
    """Apply Ichita brand styling to a paragraph based on heading detection."""
    style_id = get_style_id(p_elem)

    # Check for Word built-in heading styles
    style_lower = style_id.lower()
    if 'heading1' in style_lower or style_id == 'Heading1':
        _style_runs(p_elem, font_name, 20, colors["dark"], bold=True,
                     latin_offset=latin_offset)
        add_left_accent(p_elem, colors["accent"])
        return
    if 'heading2' in style_lower or style_id == 'Heading2':
        _style_runs(p_elem, font_name, 16, colors["dark"], bold=True,
                     latin_offset=latin_offset)
        add_left_accent(p_elem, colors["accent"])
        return
    if 'heading3' in style_lower or style_id == 'Heading3':
        _style_runs(p_elem, font_name, 14, colors["accent"], bold=True,
                     latin_offset=latin_offset)
        return

    # Detect heading from text content (for Normal-styled headings)
    heading = detect_heading(text)

    if heading == 'section':
        _style_runs(p_elem, font_name, 14, colors["dark"], bold=True,
                     latin_offset=latin_offset)
        add_left_accent(p_elem, colors["accent"])
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
    elif heading == 'subsection':
        _style_runs(p_elem, font_name, 12, colors["accent"], bold=True,
                     latin_offset=latin_offset)
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
    elif heading == 'caption':
        _style_runs(p_elem, font_name, 10.5, colors["muted"],
                     latin_offset=latin_offset)
        set_alignment(p_elem, 'center')
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
    else:
        # Normal body text
        _style_runs(p_elem, font_name, 12, colors["dark"],
                     latin_offset=latin_offset)


# ── Cleanup ────────────────────────────────────────────────────────────────

def cleanup_empty_space(body):
    """Collapse consecutive empty paragraphs (keep max 1).

    Generic cleanup — no source-specific text checks.
    """
    children = list(body)
    prev_was_empty = False
    removed = 0

    for elem in children:
        tag = elem.tag.split('}')[-1]
        if tag != 'p':
            prev_was_empty = False
            continue

        text = get_text(elem).strip()
        has_img = _has_images(elem)
        is_empty = not text and not has_img

        # Don't remove paragraphs with section breaks
        pPr = elem.find(qn('w:pPr'))
        if pPr is not None and pPr.find(qn('w:sectPr')) is not None:
            prev_was_empty = False
            continue

        if is_empty:
            if prev_was_empty:
                body.remove(elem)
                removed += 1
                continue
            prev_was_empty = True
        else:
            prev_was_empty = False

    return removed


# ── Title Page Redesign ────────────────────────────────────────────────────

def redesign_title_page(body, font_name, colors, latin_offset=1.5):
    """Extract title/subtitle from first heading-styled paragraphs.

    Build a clean cover: Title → blue band → subtitle → page break.
    Works generically — looks for Heading 1/2 styles or large/bold text.
    """
    title_text = ""
    subtitle_text = ""
    to_remove = []
    sect_break_xml = None

    # Find title and subtitle from first few elements
    for elem in list(body):
        tag = elem.tag.split('}')[-1]
        if tag != 'p':
            continue

        text = get_text(elem).strip()
        style_id = get_style_id(elem)
        style_lower = style_id.lower()

        # Detect title (first prominent heading)
        if not title_text and (
            'title' in style_lower
            or 'heading1' in style_lower
            or style_id == 'Heading1'
        ):
            title_text = text
            # Preserve section break
            pPr = elem.find(qn('w:pPr'))
            if pPr is not None:
                sect = pPr.find(qn('w:sectPr'))
                if sect is not None:
                    sect_break_xml = copy.deepcopy(sect)
            to_remove.append(elem)
            continue

        # Detect subtitle (right after title)
        if title_text and not subtitle_text and (
            'subtitle' in style_lower
            or 'heading2' in style_lower
            or style_id == 'Heading2'
        ):
            subtitle_text = text
            to_remove.append(elem)
            continue

        # Stop scanning after finding real content
        if title_text and text and 'heading' not in style_lower:
            break

    if not title_text:
        return  # No title found, skip redesign

    # Remove old title elements
    for elem in to_remove:
        if elem.getparent() is body:
            body.remove(elem)

    # Find insertion point
    insert_before = None
    for child in body:
        if child.tag != qn('w:sectPr'):
            insert_before = child
            break

    def insert(elem):
        if insert_before is not None:
            insert_before.addprevious(elem)
        else:
            final = body.find(qn('w:sectPr'))
            if final is not None:
                final.addprevious(elem)
            else:
                body.append(elem)

    # Build new title page
    insert(make_para(space_after=80, font_name=font_name,
                     latin_offset=latin_offset))

    insert(make_para(title_text, size_pt=36, color_hex=colors["dark"],
                     bold=True, align='center', space_after=10,
                     font_name=font_name, latin_offset=latin_offset))

    band = make_para(space_before=0, space_after=14, font_name=font_name,
                     latin_offset=latin_offset)
    add_bottom_band(band, color=colors["accent"], sz="24")
    insert(band)

    if subtitle_text:
        insert(make_para(subtitle_text, size_pt=16, color_hex=colors["muted"],
                         align='center', space_before=8, space_after=36,
                         font_name=font_name, latin_offset=latin_offset))

    # Section break
    sect_para = make_para(space_before=0, space_after=0, font_name=font_name,
                          latin_offset=latin_offset)
    if sect_break_xml is not None:
        pPr = ensure_pPr(sect_para)
        pPr.append(sect_break_xml)
    insert(sect_para)


# ── Main Rebranding ────────────────────────────────────────────────────────

def rebrand_docx(input_path, output_path, font_name=None, logo_path=None,
                 no_title_page=False):
    """Open source DOCX, create Ichita-branded copy."""
    brand = ICHITA_BRAND
    colors = brand["colors"]
    latin_offset = brand["fonts"]["latin_offset"]

    # Resolve font
    if font_name is None:
        font_name, warnings = resolve_font(brand)
        for w in warnings:
            print(f"  [font] {w}")

    print(f"Source: {os.path.basename(input_path)}")
    print(f"Font:   {font_name}")

    src_doc = Document(input_path)
    dst_doc = Document()

    src_body = src_doc.element.body
    dst_body = dst_doc.element.body

    # Clear destination body (keep final sectPr)
    for child in list(dst_body):
        if child.tag != qn('w:sectPr'):
            dst_body.remove(child)

    # Deep-copy all source body children
    src_part = src_doc.part
    dst_part = dst_doc.part

    for child in src_body:
        tag = child.tag.split('}')[-1]
        new_elem = copy.deepcopy(child)
        copy_image_rels(src_part, dst_part, new_elem)

        if tag == 'sectPr':
            old = dst_body.find(qn('w:sectPr'))
            if old is not None:
                dst_body.remove(old)
            dst_body.append(new_elem)
        else:
            final = dst_body.find(qn('w:sectPr'))
            if final is not None:
                final.addprevious(new_elem)
            else:
                dst_body.append(new_elem)

    # Remove source header/footer references
    for sectPr in dst_body.iter(qn('w:sectPr')):
        for ref in list(sectPr.findall(qn('w:headerReference'))):
            sectPr.remove(ref)
        for ref in list(sectPr.findall(qn('w:footerReference'))):
            sectPr.remove(ref)

    # Cleanup empty space
    removed = cleanup_empty_space(dst_body)
    print(f"  Cleanup: removed {removed} empty paragraphs")

    # Restyle paragraphs
    para_count = 0
    for p in dst_body.iter(qn('w:p')):
        text = get_text(p)
        style_paragraph(p, text, font_name, colors, latin_offset)
        para_count += 1

    # Restyle tables
    tbl_count = 0
    for tbl in dst_body.iter(qn('w:tbl')):
        style_table_xml(tbl, header_bg=colors["table_header"],
                        alt_bg=colors["table_alt"],
                        border_color=colors["border"],
                        font_name=font_name, latin_offset=latin_offset)
        tbl_count += 1

    # Title page redesign (optional)
    if not no_title_page:
        redesign_title_page(dst_body, font_name, colors, latin_offset)

    # Set page margins
    portrait_margin = Cm(brand["margins"]["portrait"])
    landscape_margin = Cm(brand["margins"]["landscape"])
    for section in dst_doc.sections:
        if section.orientation:  # Landscape
            section.top_margin = landscape_margin
            section.bottom_margin = landscape_margin
            section.left_margin = landscape_margin
            section.right_margin = landscape_margin
        else:
            section.top_margin = portrait_margin
            section.bottom_margin = portrait_margin
            section.left_margin = portrait_margin
            section.right_margin = portrait_margin

    # Squeeze wide tables
    landscape_usable = int(
        (Cm(29.7) - 2 * landscape_margin) / 914400 * 1440)
    squeeze_wide_tables(dst_body, landscape_usable)

    # Document default style
    style = dst_doc.styles['Normal']
    style.font.name = font_name
    style.font.size = Pt(12)
    style.font.color.rgb = RGBColor.from_string(colors["dark"])

    # Logo header
    logo = logo_path or DEFAULT_LOGO
    add_header_footer(dst_doc, logo_path=logo,
                      accent_color=colors["accent"],
                      font_name=font_name,
                      dark_color=colors["dark"])

    dst_doc.save(output_path)

    # Report
    size = os.path.getsize(output_path)
    img_count = sum(1 for _ in dst_body.iter(qn('a:blip')))
    print(f"\n{'='*60}")
    print(f"  Saved:      {output_path}")
    print(f"  Size:       {size:,} bytes ({size/1024/1024:.1f} MB)")
    print(f"  Paragraphs: {para_count}")
    print(f"  Tables:     {tbl_count}")
    print(f"  Images:     {img_count} blip references")
    print(f"  Sections:   {len(dst_doc.sections)}")
    print(f"  Font:       {font_name}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Rebrand existing DOCX to Ichita brand identity")
    parser.add_argument("input", help="Source DOCX file")
    parser.add_argument("output", help="Output DOCX file")
    parser.add_argument("--no-title-page", action="store_true",
                        help="Skip title page redesign")
    parser.add_argument("--font", default=None,
                        help="Override font name (default: auto-detect)")
    parser.add_argument("--logo", default=None,
                        help="Custom logo path (default: Ichita wordmark)")
    args = parser.parse_args()

    rebrand_docx(
        args.input, args.output,
        font_name=args.font,
        logo_path=args.logo,
        no_title_page=args.no_title_page,
    )


if __name__ == "__main__":
    main()
