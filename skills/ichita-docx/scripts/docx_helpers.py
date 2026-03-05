#!/usr/bin/env python3
"""
Ichita brand helpers for python-docx — generic XML functions + brand config.

All functions are brand-agnostic (receive config as parameter).
ICHITA_BRAND dict is the single source of truth for brand values.
"""

import copy
import os
import re
import subprocess
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


# ── Brand Config (values from docx-standard.md) ──────────────────────────

ICHITA_BRAND = {
    "colors": {
        "accent": "2978FF",
        "accent_light": "82B0FF",
        "dark": "263338",
        "muted": "788F9C",
        "canvas": "CFD9DB",
        "blue_black": "171C21",
        "table_header": "263338",
        "table_alt": "EFF2F3",
        "border": "A0B0B8",
        "off_white": "F8FAFB",
        "code_bg": "F2F2F2",
        "code_text": "333333",
        "green": "34A853",
        "red": "E83E3E",
    },
    "fonts": {
        "latin": "Aeonik",
        "thai": "Bai Jamjuree",
        "fallback": "Calibri",
        "display": "Betatron",
        "thai_fallback": "TH Sarabun New",
        "thai_scale": 0.9,
        "code": "Courier New",
    },
    "typography": {
        "title": {"size": 26, "bold": True, "color": "dark"},
        "h1": {"size": 20, "bold": True, "color": "dark", "before": 18, "after": 8, "accent_bar": True},
        "h2": {"size": 16, "bold": True, "color": "dark", "before": 14, "after": 6, "accent_bar": True},
        "h3": {"size": 14, "bold": True, "color": "accent", "before": 10, "after": 6},
        "h4": {"size": 12, "bold": True, "color": "accent", "before": 8, "after": 4},
        "body": {"size": 12, "bold": False, "color": "dark", "before": 3, "after": 6},
        "caption": {"size": 10.5, "bold": False, "color": "muted", "before": 6, "after": 3},
        "bullet": {"size": 12, "bold": False, "color": "dark", "before": 2, "after": 2},
        "code": {"size": 9, "bold": False, "color": "code_text"},
    },
    "table": {
        "header_font_size": 10,
        "data_font_size": 10,
        "wide_font_size": 8,
        "wide_threshold": 10,
        "wide_row_height": 320,
        "cell_spacing_before": 2,
        "cell_spacing_after": 2,
        "gap_before_after": 8,
    },
    "header": {
        "logo_width_inches": 1.5,
        "border_sz": 6,
        "space_after_pt": 4,
    },
    "title_page": {
        "space_before_pt": 80,
        "title_size": 26,
        "subtitle_size": 16,
        "space_after_subtitle_pt": 36,
    },
    "margins": {"portrait": 2.0, "landscape": 1.0},
    "blockquote": {
        "left_indent_inches": 0.5,
        "right_indent_inches": 0.3,
        "before_pt": 8,
        "after_pt": 8,
        "border_sz": 18,
    },
    "code_block": {
        "indent_inches": 0.3,
        "before_pt": 6,
        "after_pt": 6,
    },
    "list": {
        "left_indent_inches": 0.5,
        "hanging_indent_inches": 0.25,
        "nested_step_inches": 0.25,
        "before_pt": 2,
        "after_pt": 2,
    },
    "hr": {
        "sz": 6,
    },
}


# ── Font Detection ──────────────────────────────────────────────────────────

def _scan_font_dirs(font_name):
    """Scan font directories for a font. Returns (found, location) tuple.

    Location is 'linux', 'macos', 'windows', or None.
    """
    needle = font_name.lower().replace(" ", "")

    # Platform-grouped font directories
    platform_dirs = {
        "linux": [
            os.path.expanduser("~/.local/share/fonts"),
            os.path.expanduser("~/.fonts"),
            "/usr/share/fonts",
            "/usr/local/share/fonts",
        ],
        "macos": [
            os.path.expanduser("~/Library/Fonts"),
            "/Library/Fonts",
        ],
        "windows": [
            "/mnt/c/Windows/Fonts",
            # WSL: Windows user fonts
            *_glob_windows_user_font_dirs(),
        ],
    }

    for platform, dirs in platform_dirs.items():
        for fd in dirs:
            if not os.path.isdir(fd):
                continue
            try:
                for f in os.listdir(fd):
                    if needle in f.lower().replace(" ", ""):
                        return True, platform
                # Check one level of subdirectories
                for sub in os.listdir(fd):
                    subpath = os.path.join(fd, sub)
                    if os.path.isdir(subpath):
                        for f in os.listdir(subpath):
                            if needle in f.lower().replace(" ", ""):
                                return True, platform
            except OSError:
                continue
    return False, None


def _glob_windows_user_font_dirs():
    """Find Windows user font directories accessible from WSL."""
    dirs = []
    users_path = "/mnt/c/Users"
    if not os.path.isdir(users_path):
        return dirs
    try:
        for user in os.listdir(users_path):
            if user in ("Public", "Default", "Default User", "All Users"):
                continue
            font_dir = os.path.join(
                users_path, user,
                "AppData/Local/Microsoft/Windows/Fonts",
            )
            if os.path.isdir(font_dir):
                dirs.append(font_dir)
    except OSError:
        pass
    return dirs


def _check_font_installed(font_name):
    """Check if a font is installed. Returns (found, location).

    Checks fc-list (Linux font cache) first, then scans font directories
    across Linux, macOS, and Windows (via WSL mount points).
    """
    # Try fc-list first (fast, covers Linux-registered fonts)
    try:
        result = subprocess.run(
            ["fc-list", "--format=%{family}\n"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and font_name.lower() in result.stdout.lower():
            return True, "linux"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Scan font directories (Linux + macOS + Windows via WSL)
    return _scan_font_dirs(font_name)


def resolve_font(brand=None):
    """Check system for brand fonts, return best available name.

    Returns (font_name, warnings) where warnings is a list of messages
    for the user about missing/misplaced fonts.
    """
    if brand is None:
        brand = ICHITA_BRAND
    fonts = brand["fonts"]
    preferred = fonts["latin"]
    fallback = fonts["fallback"]
    warnings = []

    found, location = _check_font_installed(preferred)

    if found and location == "linux":
        # Best case: font registered in Linux — soffice preview will work
        return preferred, warnings

    if found and location == "windows":
        # Font on Windows but not in Linux font cache
        # DOCX will render correctly in Word on Windows
        # soffice preview in WSL might not render the font
        warnings.append(
            f"'{preferred}' found on Windows but not registered in Linux. "
            f"DOCX will look correct in Word. "
            f"LibreOffice preview may fall back to a substitute font."
        )
        warnings.append(
            f"To fix: copy font files to ~/.local/share/fonts/ and run fc-cache -f"
        )
        return preferred, warnings

    if found and location == "macos":
        return preferred, warnings

    # Not found anywhere
    warnings.append(
        f"Font '{preferred}' not found on this system. "
        f"Using '{fallback}' as fallback."
    )
    warnings.append(
        f"For best results, install {preferred} — "
        f"see brand guidelines or ask OhYeaH! for font files."
    )
    return fallback, warnings


# ── XML Helpers (brand-agnostic) ────────────────────────────────────────────

def set_font(run_elem, font_name=None, size_pt=None, color_hex=None,
             bold=None, brand=None):
    """Set font properties on a w:r element at the XML level.

    Detects Thai text and sets Bai Jamjuree font with scaled size.
    For Latin text, uses font_name at the specified size.
    Mixed runs are handled later by split_run_thai_latin().
    """
    if brand is None:
        brand = ICHITA_BRAND
    fonts = brand["fonts"]
    thai_font = fonts["thai"]
    thai_scale = fonts["thai_scale"]

    rPr = run_elem.find(qn('w:rPr'))
    if rPr is None:
        rPr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        run_elem.insert(0, rPr)

    # Detect if this run's text is Thai
    t_elem = run_elem.find(qn('w:t'))
    run_text = t_elem.text if t_elem is not None and t_elem.text else ""
    is_thai = _text_is_thai(run_text) and not _text_is_mixed(run_text)

    # Font name — Thai gets Bai Jamjuree, Latin gets font_name
    actual_font = thai_font if is_thai else font_name
    if actual_font is not None:
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.insert(0, rf)
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(attr), actual_font)

    # Size (half-points) — Thai scaled down for visual balance
    if size_pt is not None:
        if is_thai:
            hp = str(int(size_pt * thai_scale * 2))
        else:
            hp = str(int(size_pt * 2))
        for tag in ('w:sz', 'w:szCs'):
            el = rPr.find(qn(tag))
            if el is not None:
                el.set(qn('w:val'), hp)
            else:
                rPr.append(parse_xml(f'<{tag} {nsdecls("w")} w:val="{hp}"/>'))

    # Color
    if color_hex is not None:
        el = rPr.find(qn('w:color'))
        if el is not None:
            el.set(qn('w:val'), color_hex)
        else:
            rPr.append(parse_xml(
                f'<w:color {nsdecls("w")} w:val="{color_hex}"/>'))

    # Bold
    if bold is not None:
        for tag in ('w:b', 'w:bCs'):
            el = rPr.find(qn(tag))
            if bold:
                if el is None:
                    rPr.append(parse_xml(f'<{tag} {nsdecls("w")}/>'))
            else:
                if el is not None:
                    rPr.remove(el)


def set_cell_shading(tc_elem, color_hex):
    """Apply background shading to a table cell XML element (w:tc)."""
    tcPr = tc_elem.find(qn('w:tcPr'))
    if tcPr is None:
        tcPr = parse_xml(f'<w:tcPr {nsdecls("w")}/>')
        tc_elem.insert(0, tcPr)
    existing = tcPr.find(qn('w:shd'))
    if existing is not None:
        tcPr.remove(existing)
    tcPr.append(parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))


def set_cell_shading_docx(cell, color_hex):
    """Apply background shading to a python-docx Cell object."""
    shading = parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table, color_hex="A0B0B8"):
    """Apply borders to a python-docx Table object."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(
        f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color_hex}"/>'
        f'</w:tblBorders>')
    tblPr.append(borders)


def style_table_xml(tbl_elem, header_bg="263338", alt_bg="EFF2F3",
                    border_color="A0B0B8", font_name=None, brand=None):
    """Apply brand styling to a table XML element (w:tbl).

    Dark header rows with white bold text, alternating data row shading,
    brand borders. Handles multi-row headers and image-only tables.
    """
    if brand is None:
        brand = ICHITA_BRAND
    # Table-level borders
    tblPr = tbl_elem.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        tbl_elem.insert(0, tblPr)

    old_borders = tblPr.find(qn('w:tblBorders'))
    if old_borders is not None:
        tblPr.remove(old_borders)

    tblPr.append(parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'</w:tblBorders>'))

    rows = tbl_elem.findall(qn('w:tr'))
    if not rows:
        return

    # Detect image-only table (photo grid)
    r0_cells = rows[0].findall(qn('w:tc'))
    is_image_table = r0_cells and all(_has_images(tc) for tc in r0_cells)

    # Detect multi-row header (vMerge=restart in row 0)
    header_rows = 1
    if not is_image_table:
        for tc in r0_cells:
            tcPr = tc.find(qn('w:tcPr'))
            if tcPr is not None:
                vm = tcPr.find(qn('w:vMerge'))
                if vm is not None and vm.get(qn('w:val')) == 'restart':
                    header_rows = 2
                    break

    # Wide tables (>10 cols) use smaller font
    num_cols = len(r0_cells) if r0_cells else 0
    font_sz = 8 if num_cols > 10 else 10

    for ri, tr in enumerate(rows):
        # Wide table row height
        if num_cols > 10:
            trPr = tr.find(qn('w:trPr'))
            if trPr is None:
                trPr = parse_xml(f'<w:trPr {nsdecls("w")}/>')
                tr.insert(0, trPr)
            th = trPr.find(qn('w:trHeight'))
            if th is not None:
                th.set(qn('w:hRule'), 'atLeast')
                if int(th.get(qn('w:val'), '0')) < 320:
                    th.set(qn('w:val'), '320')
            else:
                trPr.append(parse_xml(
                    f'<w:trHeight {nsdecls("w")} w:val="320" w:hRule="atLeast"/>'))

        for tc in tr.findall(qn('w:tc')):
            if is_image_table:
                for run in tc.findall('.//' + qn('w:r')):
                    if not _has_images(run):
                        set_font(run, font_name=font_name, size_pt=font_sz,
                                 color_hex=header_bg, brand=brand)
            elif ri < header_rows:
                set_cell_shading(tc, header_bg)
                for run in tc.findall('.//' + qn('w:r')):
                    if not _has_images(run):
                        set_font(run, font_name=font_name, size_pt=font_sz,
                                 color_hex="FFFFFF", bold=True, brand=brand)
            else:
                data_idx = ri - header_rows
                set_cell_shading(tc, alt_bg if data_idx % 2 == 1 else "FFFFFF")
                for run in tc.findall('.//' + qn('w:r')):
                    if not _has_images(run):
                        set_font(run, font_name=font_name, size_pt=font_sz,
                                 color_hex=header_bg, brand=brand)


def add_header_footer(doc, logo_path=None, accent_color="2978FF",
                      font_name=None, dark_color="263338"):
    """Add logo header with accent line and clean footer to all sections."""
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        for p in header.paragraphs:
            p.clear()

        hp = (header.paragraphs[0]
              if header.paragraphs else header.add_paragraph())
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hp.paragraph_format.space_after = Pt(4)

        if logo_path and os.path.exists(logo_path):
            run = hp.add_run()
            run.add_picture(logo_path, width=Inches(1.5))
        else:
            run = hp.add_run("ICHITA\u2122")
            fn = font_name or "Calibri"
            run.font.name = fn
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor.from_string(dark_color)

        # Blue accent line under header
        pPr = hp._p.get_or_add_pPr()
        pPr.append(parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="4"'
            f'            w:color="{accent_color}"/>'
            f'</w:pBdr>'))

        # Clean footer
        footer = section.footer
        footer.is_linked_to_previous = False
        for p in footer.paragraphs:
            p.clear()


def add_formatted_text(paragraph, text, base_font="Calibri", base_size=Pt(11),
                       is_blockquote=False):
    """Parse inline markdown (bold, italic, bold+italic, links) and add runs."""
    pattern = re.compile(
        r'(\*\*\*(.+?)\*\*\*)'
        r'|(\*\*(.+?)\*\*)'
        r'|(\*(.+?)\*)'
        r'|(\[([^\]]+)\]\(([^)]+)\))'
    )

    last_end = 0
    for match in pattern.finditer(text):
        before = text[last_end:match.start()]
        if before:
            run = paragraph.add_run(before)
            run.font.name = base_font
            run.font.size = base_size
            if is_blockquote:
                run.font.italic = True
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        if match.group(2):  # ***bold+italic***
            run = paragraph.add_run(match.group(2))
            run.font.bold = True
            run.font.italic = True
        elif match.group(4):  # **bold**
            run = paragraph.add_run(match.group(4))
            run.font.bold = True
            if is_blockquote:
                run.font.italic = True
                run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        elif match.group(6):  # *italic*
            run = paragraph.add_run(match.group(6))
            run.font.italic = True
        elif match.group(8):  # [link](url)
            run = paragraph.add_run(match.group(9))
            run.font.color.rgb = RGBColor(0x29, 0x78, 0xFF)
            run.font.underline = True

        run.font.name = base_font
        run.font.size = base_size
        last_end = match.end()

    remaining = text[last_end:]
    if remaining:
        run = paragraph.add_run(remaining)
        run.font.name = base_font
        run.font.size = base_size
        if is_blockquote:
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


# ── Internal Helpers ────────────────────────────────────────────────────────

def _has_images(elem):
    """Check if element contains embedded images (a:blip)."""
    return bool(elem.findall('.//' + qn('a:blip')))


def _is_thai(c):
    """Check if a character is Thai (U+0E00-U+0E7F)."""
    return '\u0e00' <= c <= '\u0e7f'


def _split_thai_latin(text):
    """Split text into segments of (text, is_thai) tuples.

    Groups consecutive Thai chars together, and consecutive non-Thai chars
    together.
    """
    if not text:
        return []
    segments = []
    current = text[0]
    current_thai = _is_thai(text[0])
    for c in text[1:]:
        c_thai = _is_thai(c)
        if c_thai == current_thai:
            current += c
        else:
            segments.append((current, current_thai))
            current = c
            current_thai = c_thai
    segments.append((current, current_thai))
    return segments


def _text_is_thai(text):
    """Check if text contains any Thai characters."""
    return any(_is_thai(c) for c in text)


def _text_is_mixed(text):
    """Check if text contains both Thai and non-Thai alpha characters."""
    has_thai = False
    has_latin = False
    for c in text:
        if _is_thai(c):
            has_thai = True
        elif c.isalpha():
            has_latin = True
        if has_thai and has_latin:
            return True
    return False


def split_run_thai_latin(run_elem, parent_elem, brand=None):
    """Split a mixed Thai/Latin w:r element into separate runs.

    Thai segments get Bai Jamjuree at size * thai_scale.
    Latin segments get BRAND_FONT at original size.
    """
    if brand is None:
        brand = ICHITA_BRAND
    fonts = brand["fonts"]
    thai_font = fonts["thai"]
    thai_scale = fonts["thai_scale"]

    t_elem = run_elem.find(qn('w:t'))
    if t_elem is None or not t_elem.text:
        return

    text = t_elem.text
    segments = _split_thai_latin(text)

    if len(segments) <= 1:
        return

    rPr_orig = run_elem.find(qn('w:rPr'))

    # Get current size from rPr
    current_sz = None
    if rPr_orig is not None:
        sz_el = rPr_orig.find(qn('w:sz'))
        if sz_el is not None:
            current_sz = int(sz_el.get(qn('w:val'), '0'))

    # Insert new runs after the original, then remove the original
    insert_after = run_elem
    for seg_text, is_thai in segments:
        new_run = parse_xml(f'<w:r {nsdecls("w")}/>')

        if rPr_orig is not None:
            new_rPr = copy.deepcopy(rPr_orig)
        else:
            new_rPr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        new_run.insert(0, new_rPr)

        # Set font name
        rf = new_rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            new_rPr.insert(0, rf)
        font = thai_font if is_thai else fonts.get("_resolved", fonts["latin"])
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(attr), font)

        # Thai gets scaled down
        if is_thai and current_sz:
            thai_hp = str(int(current_sz * thai_scale))
            for tag in ('w:sz', 'w:szCs'):
                el = new_rPr.find(qn(tag))
                if el is not None:
                    el.set(qn('w:val'), thai_hp)
                else:
                    new_rPr.append(parse_xml(
                        f'<{tag} {nsdecls("w")} w:val="{thai_hp}"/>'))

        # Add text element
        new_t = parse_xml(f'<w:t {nsdecls("w")}/>')
        new_t.text = seg_text
        new_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        new_run.append(new_t)

        insert_after.addnext(new_run)
        insert_after = new_run

    parent_elem.remove(run_elem)


def ensure_pPr(p_elem):
    """Ensure paragraph has a pPr element; return it."""
    pPr = p_elem.find(qn('w:pPr'))
    if pPr is None:
        pPr = parse_xml(f'<w:pPr {nsdecls("w")}/>')
        p_elem.insert(0, pPr)
    return pPr


def get_style_id(p_elem):
    """Get the w:pStyle val from a paragraph element."""
    pPr = p_elem.find(qn('w:pPr'))
    if pPr is not None:
        ps = pPr.find(qn('w:pStyle'))
        if ps is not None:
            return ps.get(qn('w:val'), '')
    return ''


def get_text(p_elem):
    """Get visible text from direct-child w:r/w:t only (avoids MC duplication)."""
    texts = []
    for r in p_elem.findall(qn('w:r')):
        for t in r.findall(qn('w:t')):
            if t.text:
                texts.append(t.text)
    return ''.join(texts)


def add_left_accent(p_elem, color="2978FF", sz="24", space="6"):
    """Add a left accent bar to a paragraph."""
    pPr = ensure_pPr(p_elem)
    old = pPr.find(qn('w:pBdr'))
    if old is not None:
        pPr.remove(old)
    pPr.append(parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:left w:val="single" w:sz="{sz}" w:space="{space}"'
        f'         w:color="{color}"/>'
        f'</w:pBdr>'))


def add_bottom_band(p_elem, color="2978FF", sz="24"):
    """Add a thick bottom band below a paragraph (title decoration)."""
    pPr = ensure_pPr(p_elem)
    old = pPr.find(qn('w:pBdr'))
    if old is not None:
        pPr.remove(old)
    pPr.append(parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="1"'
        f'            w:color="{color}"/>'
        f'</w:pBdr>'))


def set_alignment(p_elem, val='center'):
    """Set paragraph alignment (center, left, right, both)."""
    pPr = ensure_pPr(p_elem)
    jc = pPr.find(qn('w:jc'))
    if jc is None:
        jc = parse_xml(f'<w:jc {nsdecls("w")}/>')
        pPr.append(jc)
    jc.set(qn('w:val'), val)


def copy_image_rels(src_part, dst_part, elem):
    """Copy image relationships from source to destination for all blips."""
    for blip in elem.findall('.//' + qn('a:blip')):
        rId = blip.get(qn('r:embed'))
        if rId and rId in src_part.rels:
            rel = src_part.rels[rId]
            new_rId = dst_part.relate_to(rel.target_part, rel.reltype)
            blip.set(qn('r:embed'), new_rId)


def make_para(text="", size_pt=12, color_hex="263338", bold=False,
              align='left', space_before=0, space_after=0,
              font_name=None, brand=None):
    """Create a new w:p element with formatted text and spacing.

    Splits mixed Thai/Latin text into separate runs with appropriate fonts.
    """
    if brand is None:
        brand = ICHITA_BRAND
    fonts = brand["fonts"]
    thai_font = fonts["thai"]
    thai_scale = fonts["thai_scale"]

    p = parse_xml(f'<w:p {nsdecls("w")}/>')

    if text:
        segments = _split_thai_latin(text)
        for seg_text, is_thai in segments:
            r = parse_xml(f'<w:r {nsdecls("w")}/>')
            t = parse_xml(f'<w:t {nsdecls("w")}/>')
            t.text = seg_text
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            r.append(t)
            seg_font = thai_font if is_thai else (font_name or fonts["latin"])
            seg_sz = size_pt * thai_scale if is_thai else size_pt
            set_font(r, font_name=seg_font, size_pt=seg_sz,
                     color_hex=color_hex, bold=bold, brand=brand)
            p.append(r)

    pPr = ensure_pPr(p)
    if align != 'left':
        pPr.append(parse_xml(
            f'<w:jc {nsdecls("w")} w:val="{align}"/>'))
    sb = str(int(space_before * 20))
    sa = str(int(space_after * 20))
    pPr.append(parse_xml(
        f'<w:spacing {nsdecls("w")} w:before="{sb}" w:after="{sa}"/>'))
    return p


def create_meta_table(items, brand=None):
    """Build a clean 2-column metadata table (label | value).

    Horizontal dividers only, no vertical lines — modern, professional look.
    Uses Bai Jamjuree for Thai labels, brand font for Latin values.
    """
    if brand is None:
        brand = ICHITA_BRAND
    fonts = brand["fonts"]
    colors = brand["colors"]
    thai_font = fonts["thai"]
    thai_scale = fonts["thai_scale"]
    latin_font = fonts.get("_resolved", fonts["latin"])

    label_sz = str(int(11 * thai_scale * 2))  # Thai scaled in half-points
    value_sz = "22"                             # 11pt in half-points

    rows_xml = ""
    for label, value in items:
        label_font = thai_font if _text_is_thai(label) else latin_font
        label_hp = label_sz if _text_is_thai(label) else value_sz
        value_font = thai_font if _text_is_thai(value) else latin_font
        value_hp = label_sz if _text_is_thai(value) else value_sz

        rows_xml += (
            '<w:tr>'
            '  <w:tc>'
            '    <w:tcPr><w:tcW w:w="2600" w:type="dxa"/></w:tcPr>'
            '    <w:p><w:pPr>'
            '      <w:spacing w:before="50" w:after="50"/>'
            '    </w:pPr>'
            '    <w:r><w:rPr>'
            f'      <w:rFonts w:ascii="{label_font}" w:hAnsi="{label_font}"'
            f'               w:cs="{label_font}" w:eastAsia="{label_font}"/>'
            f'      <w:sz w:val="{label_hp}"/><w:szCs w:val="{label_hp}"/>'
            f'      <w:color w:val="{colors["accent"]}"/>'
            '      <w:b/><w:bCs/>'
            f'    </w:rPr><w:t xml:space="preserve">{label}</w:t></w:r>'
            '    </w:p>'
            '  </w:tc>'
            '  <w:tc>'
            '    <w:tcPr><w:tcW w:w="7400" w:type="dxa"/></w:tcPr>'
            '    <w:p><w:pPr>'
            '      <w:spacing w:before="50" w:after="50"/>'
            '    </w:pPr>'
            '    <w:r><w:rPr>'
            f'      <w:rFonts w:ascii="{value_font}" w:hAnsi="{value_font}"'
            f'               w:cs="{value_font}" w:eastAsia="{value_font}"/>'
            f'      <w:sz w:val="{value_hp}"/><w:szCs w:val="{value_hp}"/>'
            f'      <w:color w:val="{colors["dark"]}"/>'
            f'    </w:rPr><w:t xml:space="preserve">{value}</w:t></w:r>'
            '    </w:p>'
            '  </w:tc>'
            '</w:tr>'
        )

    tbl_xml = (
        f'<w:tbl {nsdecls("w")}>'
        '  <w:tblPr>'
        '    <w:tblW w:w="5000" w:type="pct"/>'
        '    <w:jc w:val="center"/>'
        '    <w:tblBorders>'
        f'      <w:top w:val="single" w:sz="6" w:space="0"'
        f'            w:color="{colors["accent"]}"/>'
        f'      <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'      <w:bottom w:val="single" w:sz="6" w:space="0"'
        f'               w:color="{colors["accent"]}"/>'
        f'      <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'      <w:insideH w:val="single" w:sz="2" w:space="0"'
        f'                 w:color="{colors["border"]}"/>'
        f'      <w:insideV w:val="none" w:sz="0" w:space="0"'
        f'                 w:color="auto"/>'
        '    </w:tblBorders>'
        '    <w:tblCellMar>'
        '      <w:top w:w="60" w:type="dxa"/>'
        '      <w:left w:w="120" w:type="dxa"/>'
        '      <w:bottom w:w="60" w:type="dxa"/>'
        '      <w:right w:w="120" w:type="dxa"/>'
        '    </w:tblCellMar>'
        '  </w:tblPr>'
        '  <w:tblGrid>'
        '    <w:gridCol w:w="2600"/>'
        '    <w:gridCol w:w="7400"/>'
        '  </w:tblGrid>'
        f'  {rows_xml}'
        '</w:tbl>'
    )
    return parse_xml(tbl_xml)


def squeeze_wide_tables(body, usable_twips):
    """Scale tables that exceed usable_twips to fit within page width."""
    for tbl in body.iter(qn('w:tbl')):
        grid = tbl.find(qn('w:tblGrid'))
        if grid is None:
            continue
        grid_cols = grid.findall(qn('w:gridCol'))
        gc_widths = [int(gc.get(qn('w:w'), '0')) for gc in grid_cols]
        total = sum(gc_widths)
        if total <= usable_twips or total == 0:
            continue

        factor = usable_twips / total

        # Scale grid columns
        for gc, old_w in zip(grid_cols, gc_widths):
            gc.set(qn('w:w'), str(int(old_w * factor)))

        # Scale tblW if absolute
        tblPr = tbl.find(qn('w:tblPr'))
        if tblPr is not None:
            tblW = tblPr.find(qn('w:tblW'))
            if tblW is not None and tblW.get(qn('w:type'), 'auto') == 'dxa':
                tblW.set(qn('w:w'), str(int(int(tblW.get(qn('w:w'), '0')) * factor)))

        # Scale cell widths in every row
        for tr in tbl.findall(qn('w:tr')):
            for tc in tr.findall(qn('w:tc')):
                tcPr = tc.find(qn('w:tcPr'))
                if tcPr is None:
                    continue
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None and tcW.get(qn('w:type'), 'dxa') == 'dxa':
                    tcW.set(qn('w:w'), str(int(int(tcW.get(qn('w:w'), '0')) * factor)))
