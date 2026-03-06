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
    create_meta_table, split_run_thai_latin,
    _has_images, _text_is_mixed,
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
                brand=None):
    """Apply brand font to all text runs in a paragraph (skip image runs).

    After setting fonts, splits mixed Thai/Latin runs into separate elements.
    """
    for run in p_elem.findall('.//' + qn('w:r')):
        if _has_images(run):
            continue
        set_font(run, font_name=font_name, size_pt=size_pt,
                 color_hex=color_hex, bold=bold, brand=brand)

    # Second pass: split any mixed Thai/Latin runs
    for run in list(p_elem.findall('.//' + qn('w:r'))):
        if _has_images(run):
            continue
        t_elem = run.find(qn('w:t'))
        if t_elem is not None and t_elem.text and _text_is_mixed(t_elem.text):
            split_run_thai_latin(run, p_elem, brand=brand)


def style_paragraph(p_elem, text, font_name, colors, brand=None):
    """Apply Ichita brand styling to a paragraph based on heading detection."""
    typo = brand["typography"] if brand else {}
    style_id = get_style_id(p_elem)

    # Check for Word built-in heading styles
    style_lower = style_id.lower()
    if 'heading1' in style_lower or style_id == 'Heading1':
        h1 = typo.get("h1", {"size": 22, "color": "dark"})
        _style_runs(p_elem, font_name, h1["size"], colors[h1.get("color", "dark")], bold=True, brand=brand)
        add_left_accent(p_elem, colors["accent"])
        return
    if 'heading2' in style_lower or style_id == 'Heading2':
        h2 = typo.get("h2", {"size": 15, "color": "dark"})
        _style_runs(p_elem, font_name, h2["size"], colors[h2.get("color", "dark")], bold=True, brand=brand)
        add_left_accent(p_elem, colors["accent"])
        return
    if 'heading3' in style_lower or style_id == 'Heading3':
        h3 = typo.get("h3", {"size": 12, "color": "accent"})
        _style_runs(p_elem, font_name, h3["size"], colors[h3.get("color", "accent")], bold=True, brand=brand)
        return

    # List items (pandoc: Compact/ListParagraph with numPr, or bullet styles)
    pPr = p_elem.find(qn('w:pPr'))
    has_numPr = pPr is not None and pPr.find(qn('w:numPr')) is not None
    is_list_style = style_lower in ('compact', 'listparagraph', 'list bullet',
                                     'list number', 'listbullet', 'listnumber')
    if has_numPr or is_list_style:
        bod = typo.get("body", {"size": 10, "color": "dark", "before": 2, "after": 2})
        _style_runs(p_elem, font_name, bod["size"], colors[bod.get("color", "dark")], brand=brand)
        return

    # Pandoc-specific styles → treat as body
    if style_lower in ('firstparagraph', 'bodytext', 'body text'):
        bod = typo.get("body", {"size": 10, "color": "dark", "before": 3, "after": 6})
        _style_runs(p_elem, font_name, bod["size"], colors[bod.get("color", "dark")], brand=brand)
        return

    # Pandoc blockquote
    if style_lower == 'blocktext':
        bod = typo.get("body", {"size": 10, "color": "dark"})
        _style_runs(p_elem, font_name, bod["size"], colors[bod.get("color", "dark")], brand=brand)
        return

    # Pandoc code block
    if style_lower == 'sourcecode':
        code = typo.get("code", {"size": 9, "color": "code_text"})
        _style_runs(p_elem, font_name, code["size"], colors.get(code.get("color", "code_text"), "333333"), brand=brand)
        return

    # Detect heading from text content (for Normal-styled headings)
    heading = detect_heading(text)

    if heading == 'section':
        sec = typo.get("h3", {"size": 14, "color": "dark", "before": 10, "after": 6})
        _style_runs(p_elem, font_name, sec["size"], colors[sec.get("color", "dark")], bold=True, brand=brand)
        add_left_accent(p_elem, colors["accent"])
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
        sp = pPr.find(qn('w:spacing'))
        if sp is None:
            sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
            pPr.append(sp)
        sp.set(qn('w:before'), str(sec.get("before", 10) * 20))
        sp.set(qn('w:after'), str(sec.get("after", 6) * 20))
    elif heading == 'subsection':
        sub = typo.get("h4", {"size": 12, "color": "accent", "before": 8, "after": 4})
        _style_runs(p_elem, font_name, sub["size"], colors[sub.get("color", "accent")], bold=True, brand=brand)
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
        sp = pPr.find(qn('w:spacing'))
        if sp is None:
            sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
            pPr.append(sp)
        sp.set(qn('w:before'), str(sub.get("before", 8) * 20))
        sp.set(qn('w:after'), str(sub.get("after", 4) * 20))
    elif heading == 'caption':
        cap = typo.get("caption", {"size": 10.5, "color": "muted", "before": 6, "after": 3})
        _style_runs(p_elem, font_name, cap["size"], colors[cap.get("color", "muted")], brand=brand)
        set_alignment(p_elem, 'center')
        pPr = ensure_pPr(p_elem)
        pPr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
        sp = pPr.find(qn('w:spacing'))
        if sp is None:
            sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
            pPr.append(sp)
        sp.set(qn('w:before'), str(cap.get("before", 6) * 20))
        sp.set(qn('w:after'), str(cap.get("after", 3) * 20))
    else:
        # Normal body text
        bod = typo.get("body", {"size": 12, "color": "dark", "before": 3, "after": 6})
        _style_runs(p_elem, font_name, bod["size"], colors[bod.get("color", "dark")], brand=brand)
        pPr = ensure_pPr(p_elem)
        sp = pPr.find(qn('w:spacing'))
        if sp is None:
            sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
            pPr.append(sp)
        sp.set(qn('w:before'), str(bod.get("before", 3) * 20))
        sp.set(qn('w:after'), str(bod.get("after", 6) * 20))


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


# ── Image Caption Reorder ──────────────────────────────────────────────────

def reorder_image_captions(body):
    """Move 'รูปที่...' captions above their image tables.

    Original order:  text → img table → caption
    New order:       caption → img table → text
    """
    children = list(body)
    moved = 0
    for i, child in enumerate(children):
        if child.tag.split('}')[-1] != 'tbl':
            continue
        if not child.findall('.//' + qn('w:drawing')):
            continue
        # Check next sibling is a caption
        if i + 1 < len(children) and children[i + 1].tag == qn('w:p'):
            nxt = children[i + 1]
            cap_text = get_text(nxt).strip()
            if cap_text.startswith('รูปที่'):
                child.addprevious(nxt)
                moved += 1
    if moved:
        print(f"  Reordered {moved} image caption(s)")


# ── Table Spacing ─────────────────────────────────────────────────────────

def enforce_table_spacing(body, brand=None):
    """Ensure gap before and after every table."""
    gap_pt = 8
    if brand and "table" in brand:
        gap_pt = brand["table"].get("gap_before_after", 8)
    SPACE_AROUND = str(gap_pt * 20)  # pt to twips
    children = list(body)
    for i, child in enumerate(children):
        if child.tag.split('}')[-1] != 'tbl':
            continue

        # Paragraph BEFORE table: ensure space_after
        if i > 0 and children[i - 1].tag == qn('w:p'):
            prev_p = children[i - 1]
            pPr = ensure_pPr(prev_p)
            sp = pPr.find(qn('w:spacing'))
            if sp is None:
                sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
                pPr.append(sp)
            cur_after = int(sp.get(qn('w:after'), '0'))
            if cur_after < int(SPACE_AROUND):
                sp.set(qn('w:after'), SPACE_AROUND)

        # Paragraph AFTER table: ensure space_before
        if i + 1 < len(children) and children[i + 1].tag == qn('w:p'):
            next_p = children[i + 1]
            pPr = ensure_pPr(next_p)
            sp = pPr.find(qn('w:spacing'))
            if sp is None:
                sp = parse_xml(f'<w:spacing {nsdecls("w")}/>')
                pPr.append(sp)
            cur_before = int(sp.get(qn('w:before'), '0'))
            if cur_before < int(SPACE_AROUND):
                sp.set(qn('w:before'), SPACE_AROUND)


# ── Smart Page Breaks ─────────────────────────────────────────────────────

def apply_page_breaks(body):
    """Strip all pageBreakBefore → add back for 'Appendix' → zero space_before
    on page-top paragraphs."""
    # Remove ALL pageBreakBefore first
    for p in body.iter(qn('w:p')):
        pPr = p.find(qn('w:pPr'))
        if pPr is not None:
            pb = pPr.find(qn('w:pageBreakBefore'))
            if pb is not None:
                pPr.remove(pb)

    # Add pageBreakBefore to "Appendix" heading
    children = list(body)
    for child in children:
        if child.tag != qn('w:p'):
            continue
        text = get_text(child).strip()
        if text.lower() == 'appendix':
            pPr = ensure_pPr(child)
            if pPr.find(qn('w:pageBreakBefore')) is None:
                pPr.append(parse_xml(
                    f'<w:pageBreakBefore {nsdecls("w")}/>'))

    # Zero space_before on page-top paragraphs
    children = list(body)
    for i, child in enumerate(children):
        if child.tag != qn('w:p'):
            continue
        pPr = child.find(qn('w:pPr'))
        if pPr is None:
            continue

        zero_it = False
        if pPr.find(qn('w:pageBreakBefore')) is not None:
            zero_it = True
        if i > 0 and children[i - 1].tag == qn('w:p'):
            prev_pPr = children[i - 1].find(qn('w:pPr'))
            if prev_pPr is not None and prev_pPr.find(qn('w:sectPr')) is not None:
                zero_it = True

        if zero_it:
            sp = pPr.find(qn('w:spacing'))
            if sp is not None:
                sp.set(qn('w:before'), '0')


# ── Trailing Empty Section Cleanup ────────────────────────────────────────

def cleanup_trailing_section(body):
    """If last inline sectPr creates a section with no content, merge it."""
    children = list(body)
    final_sect = body.find(qn('w:sectPr'))
    if final_sect is None:
        return

    last_sb = None
    last_sb_idx = None
    for i, child in enumerate(children):
        if child.tag == qn('w:p'):
            pPr = child.find(qn('w:pPr'))
            if pPr is not None and pPr.find(qn('w:sectPr')) is not None:
                last_sb = child
                last_sb_idx = i

    if last_sb is None:
        return

    has_content = False
    for sib in children[last_sb_idx + 1:]:
        if sib.tag == qn('w:sectPr'):
            continue
        if sib.tag == qn('w:tbl'):
            has_content = True
            break
        if sib.tag == qn('w:p'):
            t = get_text(sib).strip()
            if t or _has_images(sib):
                has_content = True
                break

    if not has_content:
        pPr = last_sb.find(qn('w:pPr'))
        inline_sect = pPr.find(qn('w:sectPr'))
        src_pgSz = inline_sect.find(qn('w:pgSz'))
        dst_pgSz = final_sect.find(qn('w:pgSz'))
        if src_pgSz is not None and dst_pgSz is not None:
            for attr in (qn('w:w'), qn('w:h'), qn('w:orient')):
                val = src_pgSz.get(attr)
                if val is not None:
                    dst_pgSz.set(attr, val)
                elif attr == qn('w:orient'):
                    if attr in dst_pgSz.attrib:
                        del dst_pgSz.attrib[attr]
        body.remove(last_sb)
        print("  Removed trailing empty section")


# ── Title Page Redesign ────────────────────────────────────────────────────

def _extract_metadata(body):
    """Scan body for Thai key patterns and extract metadata dict.

    Looks for patterns like 'ชื่อโครงการ : value' in paragraphs.
    Returns dict with keys: project, case, customer, date, notes.
    """
    metadata = {}
    meta_elems = []
    for elem in list(body):
        tag = elem.tag.split('}')[-1]
        if tag != 'p':
            continue
        text = get_text(elem).strip()
        for thai_key, dict_key in [
            ('ชื่อโครงการ', 'project'),
            ('ชื่องาน', 'case'),
            ('ลูกค้า', 'customer'),
            ('วันที่จัดทำ', 'date'),
            ('หมายเหตุ', 'notes'),
        ]:
            if thai_key in text:
                clean = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
                _, _, value = clean.partition(':')
                metadata[dict_key] = value.strip()
                meta_elems.append(elem)
                break
    return metadata, meta_elems


def redesign_title_page(body, font_name, colors, brand=None):
    """Extract title/subtitle from first heading-styled paragraphs.

    Build a clean cover: Title → blue band → subtitle → metadata table → page break.
    Works generically — looks for Heading 1/2 styles or large/bold text.
    Also extracts Thai metadata fields if present.
    """
    title_text = ""
    subtitle_text = ""
    to_remove = []
    sect_break_xml = None

    # Extract metadata
    metadata, meta_elems = _extract_metadata(body)
    to_remove.extend(meta_elems)

    # Preserve section break from metadata paragraphs
    for elem in meta_elems:
        pPr = elem.find(qn('w:pPr'))
        if pPr is not None:
            sect = pPr.find(qn('w:sectPr'))
            if sect is not None:
                sect_break_xml = copy.deepcopy(sect)

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

    # Remove old title elements (deduplicate)
    seen = set()
    for elem in to_remove:
        eid = id(elem)
        if eid in seen:
            continue
        seen.add(eid)
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
    tp = brand.get("title_page", {}) if brand else {}
    title_sz = tp.get("title_size", 26)
    subtitle_sz = tp.get("subtitle_size", 16)
    space_before = tp.get("space_before_pt", 80)
    space_after_sub = tp.get("space_after_subtitle_pt", 36)

    insert(make_para(space_after=space_before, font_name=font_name, brand=brand))

    insert(make_para(title_text, size_pt=title_sz, color_hex=colors["dark"],
                     bold=True, align='center', space_after=10,
                     font_name=font_name, brand=brand))

    band = make_para(space_before=0, space_after=14, font_name=font_name,
                     brand=brand)
    add_bottom_band(band, color=colors["accent"], sz="24")
    insert(band)

    if subtitle_text:
        insert(make_para(subtitle_text, size_pt=subtitle_sz, color_hex=colors["muted"],
                         align='center', space_before=8, space_after=space_after_sub,
                         font_name=font_name, brand=brand))

    # Metadata table
    if metadata:
        meta_items = [
            ('ชื่อโครงการ',       metadata.get('project', '')),
            ('ชื่องาน',           metadata.get('case', '')),
            ('ลูกค้า',            metadata.get('customer', '')),
            ('วันที่จัดทำ',        metadata.get('date', '')),
            ('หมายเหตุโครงการ',   metadata.get('notes', '')),
        ]
        # Filter out empty values
        meta_items = [(k, v) for k, v in meta_items if v]
        if meta_items:
            insert(create_meta_table(meta_items, brand=brand))
            print(f"  Title page: metadata table ({len(meta_items)} fields)")

    # Section break
    sect_para = make_para(space_before=0, space_after=0, font_name=font_name,
                          brand=brand)
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

    # Resolve font
    if font_name is None:
        font_name, warnings = resolve_font(brand)
        for w in warnings:
            print(f"  [font] {w}")

    # Store resolved font for helpers that need it
    brand["fonts"]["_resolved"] = font_name

    print(f"Source: {os.path.basename(input_path)}")
    print(f"Font:   {font_name} + {brand['fonts']['thai']} (Thai, {brand['fonts']['thai_scale']}x)")

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

    # Remove source header/footer references + titlePg
    for sectPr in dst_body.iter(qn('w:sectPr')):
        for ref in list(sectPr.findall(qn('w:headerReference'))):
            sectPr.remove(ref)
        for ref in list(sectPr.findall(qn('w:footerReference'))):
            sectPr.remove(ref)
        # Remove titlePg — "different first page" hides our header
        title_pg = sectPr.find(qn('w:titlePg'))
        if title_pg is not None:
            sectPr.remove(title_pg)

    # Cleanup empty space
    removed = cleanup_empty_space(dst_body)
    print(f"  Cleanup: removed {removed} empty paragraphs")

    # Restyle paragraphs (skip those inside tables — handled by style_table_xml)
    para_count = 0
    table_paras = set()
    for tbl in dst_body.iter(qn('w:tbl')):
        for tp in tbl.iter(qn('w:p')):
            table_paras.add(id(tp))
    for p in dst_body.iter(qn('w:p')):
        if id(p) in table_paras:
            continue
        text = get_text(p)
        style_paragraph(p, text, font_name, colors, brand=brand)
        para_count += 1

    # Restyle tables
    tbl_count = 0
    for tbl in dst_body.iter(qn('w:tbl')):
        style_table_xml(tbl, header_bg=colors["table_header"],
                        alt_bg=colors["table_alt"],
                        border_color=colors["border"],
                        font_name=font_name, brand=brand)
        tbl_count += 1

    # Reorder image captions (before table, not after)
    reorder_image_captions(dst_body)

    # Enforce table spacing (8pt gap)
    enforce_table_spacing(dst_body, brand=brand)

    # Title page redesign (optional)
    if not no_title_page:
        redesign_title_page(dst_body, font_name, colors, brand=brand)

    # Cleanup trailing empty section
    cleanup_trailing_section(dst_body)

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

    # Smart page breaks (after all content modifications)
    apply_page_breaks(dst_body)

    # Document default style — set Thai fonts on Normal style
    style = dst_doc.styles['Normal']
    style.font.name = font_name
    body_size = brand["typography"]["body"]["size"] if brand else 12
    style.font.size = Pt(body_size)
    style.font.color.rgb = RGBColor.from_string(colors["dark"])
    n_rPr = style.element.get_or_add_rPr()
    n_rFonts = n_rPr.find(qn('w:rFonts'))
    if n_rFonts is None:
        n_rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        n_rPr.insert(0, n_rFonts)
    n_rFonts.set(qn('w:cs'), brand["fonts"]["thai"])
    n_rFonts.set(qn('w:eastAsia'), brand["fonts"]["thai"])

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
    print(f"  Font:       {font_name} + {brand['fonts']['thai']} (Thai)")
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
