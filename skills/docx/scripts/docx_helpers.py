#!/usr/bin/env python3
"""
Ichita brand helpers for python-docx — generic XML functions + brand config.

All functions are brand-agnostic (receive config as parameter).
ICHITA_BRAND dict is the single source of truth for brand values.
"""

import os
import re
import subprocess
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


# ── Brand Config (values from ichita-defaults.md) ───────────────────────────

ICHITA_BRAND = {
    "colors": {
        "accent": "2978FF",
        "accent_light": "82B0FF",
        "dark": "263338",
        "muted": "788F9C",
        "canvas": "CFD9DB",
        "table_header": "263338",
        "table_alt": "EFF2F3",
        "border": "A0B0B8",
        "off_white": "F8FAFB",
        "green": "34A853",
        "red": "E83E3E",
    },
    "fonts": {
        "latin": "Aeonik",
        "thai": "Bai Jamjuree",
        "fallback": "Calibri",
        "display": "Betatron",
        "thai_fallback": "TH Sarabun New",
        "latin_offset": 1.5,
    },
    "typography": {
        "title": {"size": 36, "bold": True, "color": "dark"},
        "h1": {"size": 15, "bold": True, "color": "dark"},
        "h2": {"size": 14, "bold": True, "color": "accent"},
        "h3": {"size": 12, "bold": True, "color": "accent"},
        "body": {"size": 12, "bold": False, "color": "dark"},
        "caption": {"size": 10.5, "bold": False, "color": "muted"},
    },
    "margins": {"portrait": 2.5, "landscape": 1.0},
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
             bold=None, latin_offset=1.5):
    """Set font properties on a w:r element at the XML level.

    Latin text renders visually larger than Thai at same pt size,
    so w:sz is reduced by latin_offset to balance them.
    """
    rPr = run_elem.find(qn('w:rPr'))
    if rPr is None:
        rPr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        run_elem.insert(0, rPr)

    # Font name
    if font_name is not None:
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.insert(0, rf)
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rf.set(qn(attr), font_name)

    # Size (half-points, with latin offset)
    if size_pt is not None:
        hp_latin = str(int((size_pt - latin_offset) * 2))
        hp_cs = str(int(size_pt * 2))
        for tag, hp in (('w:sz', hp_latin), ('w:szCs', hp_cs)):
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
                    border_color="A0B0B8", font_name=None, latin_offset=1.5):
    """Apply brand styling to a table XML element (w:tbl).

    Dark header rows with white bold text, alternating data row shading,
    brand borders. Handles multi-row headers and image-only tables.
    """
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
                                 color_hex=header_bg, latin_offset=latin_offset)
            elif ri < header_rows:
                set_cell_shading(tc, header_bg)
                for run in tc.findall('.//' + qn('w:r')):
                    if not _has_images(run):
                        set_font(run, font_name=font_name, size_pt=font_sz,
                                 color_hex="FFFFFF", bold=True,
                                 latin_offset=latin_offset)
            else:
                data_idx = ri - header_rows
                set_cell_shading(tc, alt_bg if data_idx % 2 == 1 else "FFFFFF")
                for run in tc.findall('.//' + qn('w:r')):
                    if not _has_images(run):
                        set_font(run, font_name=font_name, size_pt=font_sz,
                                 color_hex=header_bg, latin_offset=latin_offset)


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
              font_name=None, latin_offset=1.5):
    """Create a new w:p element with formatted text and spacing."""
    p = parse_xml(f'<w:p {nsdecls("w")}/>')

    if text:
        r = parse_xml(f'<w:r {nsdecls("w")}/>')
        t = parse_xml(f'<w:t {nsdecls("w")}/>')
        t.text = text
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        set_font(r, font_name=font_name, size_pt=size_pt,
                 color_hex=color_hex, bold=bold, latin_offset=latin_offset)
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
