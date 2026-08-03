#!/usr/bin/env python3
"""
Convert Markdown documents to Ichita-branded .docx files.

Applies Ichita Brand Identity styling:
- Colors: Blue #2978FF (accent), Blue Grey 03 #263338 (headings/body),
          Blue Light #82B0FF, Blue Grey 01 #CFD9DB (backgrounds)
- Font: Aeonik (with Arial Narrow / Calibri fallback if not installed)
- Logo: ICHITA wordmark in header
- Footer: ichitaglobal.com | Separation Technologies
- Professional, technical, innovative tone

Handles: headings (#-####), tables, code blocks, bold/italic, bullets,
numbered lists, blockquotes, horizontal rules, links, and regular paragraphs.


Usage:
    python3 md_to_docx.py input.md              # → input.docx
    python3 md_to_docx.py input.md output.docx  # custom output path
    python3 md_to_docx.py input.md --logo my.png # custom logo
"""

import argparse
import re
import os
import sys
import math
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# Allow importing from same directory (for add_ichita_header/footer)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Ichita Brand Colours ─────────────────────────────────────────────────────

ICHITA_BLUE       = RGBColor(0x29, 0x78, 0xFF)  # #2978FF — primary accent
ICHITA_BLUE_LIGHT = RGBColor(0x82, 0xB0, 0xFF)  # #82B0FF — light accent
ICHITA_BLUE_GREY1 = RGBColor(0xCF, 0xD9, 0xDB)  # #CFD9DB — light background
ICHITA_BLUE_GREY2 = RGBColor(0x78, 0x8F, 0x9C)  # #788F9C — medium grey
ICHITA_BLUE_GREY3 = RGBColor(0x26, 0x33, 0x38)  # #263338 — dark text, headings
ICHITA_BLUE_BLACK = RGBColor(0x17, 0x1C, 0x21)  # #171C21 — deepest dark
WHITE             = RGBColor(0xFF, 0xFF, 0xFF)

# Hex strings for cell shading (no # prefix)
HEX_BLUE         = "2978FF"
HEX_BLUE_LIGHT   = "82B0FF"
HEX_BLUE_GREY1   = "CFD9DB"
HEX_BLUE_GREY3   = "263338"
HEX_TABLE_HDR    = "263338"   # Dark header row
HEX_TABLE_ALT    = "EFF2F3"   # Very light alternating row (subtle Blue Grey 01 tint)
HEX_CODE_BG      = "EFF2F3"   # Code block background
HEX_QUOTE_BG     = "EBF0F7"   # Blockquote background


# ── Script directory (for resolving relative paths) ─────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Font Configuration ────────────────────────────────────────────────────────
# Priority: Aeonik (brand) → Avenir Next (closest geometric match) → Calibri (fallback)

BRAND_FONT = "Avenir Next"  # Closest system match to Aeonik
THAI_FONT  = "Bai Jamjuree" # Thai font with matched metrics to geometric sans-serif
THAI_SCALE = 0.9             # Thai 9pt / English 10pt — Bai Jamjuree one size down for visual balance

# ── Thai line spacing ────────────────────────────────────────────────────────
# Minimum baseline-to-baseline pitch, as a multiple of the *Thai* point size,
# that keeps the below-vowel of one line clear of the upper vowel + tone of the
# next. Siwatch's acceptance test, 2026-08-03: `สูง` on one line, `ซึ่ง` directly
# below, "ต้องเว้นวรรคมากพอแบบชัดเจน".
#
# No Thai font clears this at its own line box — not Bai, and not Sarabun, which
# needs 1.657 against a box of 1.300. The clearance has to come from the
# document, because the alternatives are to break the rule that the merged line
# box equals the Latin source's (that was the 42% leading defect) or to shrink
# the marks back toward the fusing th_mark_clearance.py just fixed.
#
# Regenerate after any font rebuild — the mark-clearance pass moves these:
#     python3 scripts/thai_line_pitch.py --check
THAI_LINE_RATIO = 1.64       # Bai Jamjuree worst face, × Thai pt (= 0.9 × Latin pt)
TH_LINE_RATIO   = 1.61       # TH-Aeonik 1.537 / TH-Slussen 1.603, × Latin pt

# `atLeast`, never `Exactly`. Exactly is a fixed box and is where Word genuinely
# clips marks; atLeast lets the line grow instead. The previous 1.46 ratio was
# derived from one stack in isolation and paired with Exactly, so it both sat
# ~2pt too tight and clipped when it was exceeded.
# docs/postmortems/2026-08-02-th-font-line-box-overcorrection.md
MONO_FONT  = "Courier New"
TH_AEONIK_MODE = False       # True when TH Aeonik (unified Latin+Thai) is installed

# Check system font dirs + bundled Aeonik-Essentials-Web for Aeonik
_font_dirs = [
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
    os.path.expanduser("~/.local/share/fonts"),
    os.path.join(SCRIPT_DIR, "Aeonik-Essentials-Web"),
    os.path.expanduser("~/.fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
]

# TH Aeonik unified-font mode disabled — always use split fonts
# (Aeonik for Latin + Bai Jamjuree for Thai). This preserves per-script
# language tagging so Word's spell checker uses the correct dictionary
# for each script (en-US for Latin, th-TH for Thai).
TH_AEONIK_MODE = False

# Aeonik detection for Latin script
for _fd in _font_dirs:
    if os.path.isdir(_fd):
        if any("aeonik" in f.lower() for f in os.listdir(_fd)):
            BRAND_FONT = "Aeonik"
            break


def thai_line_pt(latin_pt):
    """Smallest `atLeast` line spacing that keeps two Thai lines visibly apart.

    Takes the run's *Latin* size, since that is what every caller already has,
    and applies the ratio to whichever size the Thai actually renders at — the
    same size in unified mode, one step down in split mode.
    """
    if TH_AEONIK_MODE:
        return Pt(math.ceil(latin_pt * TH_LINE_RATIO))
    return Pt(math.ceil(latin_pt * THAI_SCALE * THAI_LINE_RATIO))

# ── Import shared header/footer helpers ─────────────────────────────────────
try:
    from docx_helpers import add_ichita_header, add_ichita_footer
    _HAS_BRANDED_HEADER_FOOTER = True
except ImportError:
    _HAS_BRANDED_HEADER_FOOTER = False


# ── Default Logo Path (resolved relative to script) ─────────────────────────

_LOGO_ASSET = os.path.join(SCRIPT_DIR, "assets", "ichita-wordmark-dark-on-white.png")
# Repo-relative fallback: skills/ichita-docx/scripts/ → repo root is three "..".
_LOGO_REPO_ASSETS = os.path.normpath(os.path.join(
    SCRIPT_DIR, "..", "..", "..", "assets", "logos", "ichita-wordmark-dark-on-white.png"))
DEFAULT_LOGO = (
    _LOGO_ASSET if os.path.exists(_LOGO_ASSET)
    else _LOGO_REPO_ASSETS if os.path.exists(_LOGO_REPO_ASSETS)
    else None
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_thai(c):
    """Check if a character is Thai (U+0E00-U+0E7F)."""
    return '\u0e00' <= c <= '\u0e7f'


def _split_thai_latin(text):
    """Split text into segments of (text, is_thai) tuples.
    Groups consecutive Thai chars together, and consecutive non-Thai chars together."""
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


def _add_split_run(paragraph, text, font_name, base_size, color, bold=False,
                   italic=False, underline=False, is_link=False):
    """Add text as split Thai/Latin runs with different fonts and sizes.
    Thai segments get Bai Jamjuree at scaled size, Latin gets Aeonik at base size.

    In TH_AEONIK_MODE: creates a single run with BRAND_FONT for all scripts.
    """
    if TH_AEONIK_MODE:
        # Single font handles both Latin and Thai — no splitting
        run = paragraph.add_run(text)
        run.font.name = BRAND_FONT
        run.font.size = base_size
        run.font.color.rgb = color
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:ascii'), BRAND_FONT)
        rFonts.set(qn('w:hAnsi'), BRAND_FONT)
        rFonts.set(qn('w:cs'), BRAND_FONT)
        rFonts.set(qn('w:eastAsia'), BRAND_FONT)
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        if underline:
            run.font.underline = True
        return run if text else None

    thai_size = Pt(round(base_size / 12700 * THAI_SCALE * 2) / 2)  # EMU → pt, scale, back to EMU
    for segment, is_thai in _split_thai_latin(text):
        run = paragraph.add_run(segment)
        run.font.name = THAI_FONT if is_thai else font_name
        run.font.size = thai_size if is_thai else base_size
        run.font.color.rgb = color
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        if underline:
            run.font.underline = True
        if is_thai:
            _mark_thai_run(run, THAI_FONT, thai_size, bold=bold, italic=italic)
        else:
            _set_run_lang(run, val='en-US')
    return run if text else None


def _set_run_lang(run, val=None, bidi=None):
    """Set <w:lang> on a run (created in schema-valid position — lang is among
    the last rPr children, so appending is correct)."""
    rPr = run._r.get_or_add_rPr()
    lang = rPr.find(qn('w:lang'))
    if lang is None:
        lang = parse_xml(f'<w:lang {nsdecls("w")}/>')
        rPr.append(lang)
    if val is not None:
        lang.set(qn('w:val'), val)
    if bidi is not None:
        lang.set(qn('w:bidi'), bidi)
    return lang


def _mark_thai_run(run, thai_font, thai_size, bold=False, italic=False):
    """Tag a run as Thai complex-script so Word proofs it with the Thai
    dictionary instead of English.

    A run carrying only Latin-category properties (w:rFonts ascii/hAnsi, w:b,
    w:sz) is spell-checked against the *default* (Latin / inherited en-US)
    language — which flags every Thai word. Thai is a complex script, so the run
    must also declare the complex-script font (w:cs), bold (w:bCs), size (w:szCs)
    and language (w:lang/@w:bidi). We also set w:lang/@w:val to th-TH so the
    run's default proofing language is Thai too. Child order follows the CT_RPr
    schema (rFonts → b → bCs → … → sz → szCs → … → lang)."""
    rPr = run._r.get_or_add_rPr()
    # complex-script font
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:cs'), thai_font)
    # complex-script bold (order-safe helper inserts right after <w:b>)
    if bold:
        rPr.get_or_add_bCs()
    # complex-script size — insert right after <w:sz> (no get_or_add helper)
    szCs = rPr.find(qn('w:szCs'))
    if szCs is None:
        szCs = parse_xml(f'<w:szCs {nsdecls("w")}/>')
        sz_el = rPr.find(qn('w:sz'))
        if sz_el is not None:
            sz_el.addnext(szCs)
        else:
            rPr.append(szCs)
    szCs.set(qn('w:val'), str(int(round(thai_size.pt * 2))))
    # proofing language: Thai for both the default and complex-script slots
    _set_run_lang(run, val='th-TH', bidi='th-TH')

def set_cell_shading(cell, color_hex):
    """Apply background shading to a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table, color="788F9C"):
    """Apply borders to every cell in the table."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def set_cell_top_border(cell, color_hex=HEX_BLUE, size=22):
    """Add only a top accent border to a cell (used by KPI stat cards)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="{size}" w:space="0" w:color="{color_hex}"/>'
        f'</w:tcBorders>'
    ))


def set_cell_margins(cell, top=120, bottom=100, left=160, right=160):
    """Set internal padding (twips) for a single table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:start w:w="{left}" w:type="dxa"/>'
        f'  <w:end w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    ))


def add_kpi_cards(doc, cards, content_width_in=6.3, number_size=26, compact=False):
    """Render a row of KPI 'stat cards' — a big Ichita-blue number with a grey
    label beneath, each card carrying a blue top accent rule and a light
    background. `cards` = list of (number, label) tuples.

    Numbers are Latin → BRAND_FONT (Aeonik). Labels go through _add_split_run so
    Thai segments keep Bai Jamjuree + th-TH language tagging (editable + spell-
    checkable, same as the rest of the document). SINGLE line spacing lets the
    number grow with its line box so it never clips the top accent rule.
    """
    n = len(cards)
    if n == 0:
        return
    if compact:
        number_size = min(number_size, 21)
    if n >= 3:                              # narrower columns → smaller number
        number_size = min(number_size, 17)
    cols = 2 * n - 1                        # cards interleaved with spacer gutters
    gutter_in = 0.18
    card_w = (content_width_in - gutter_in * (n - 1)) / n if n else content_width_in

    table = doc.add_table(rows=1, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    # Fixed layout so LibreOffice/Word honour the column widths
    tblPr = table._tbl.tblPr
    tblPr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))

    for idx, cell in enumerate(table.rows[0].cells):
        if idx % 2 == 1:                   # spacer column — empty gutter
            cell.width = Inches(gutter_in)
            continue
        value, unit, label = cards[idx // 2]
        cell.width = Inches(card_w)
        set_cell_shading(cell, "F8FAFB")
        set_cell_top_border(cell, HEX_BLUE, size=22)
        set_cell_margins(cell,
                         top=70 if compact else 120,
                         bottom=60 if compact else 100,
                         left=160, right=160)

        # Big number — Latin, never clips (SINGLE line spacing)
        pnum = cell.paragraphs[0]
        pnum.paragraph_format.space_before = Pt(1 if compact else 2)
        pnum.paragraph_format.space_after = Pt(0)
        pnum.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        rnum = pnum.add_run(value)
        rnum.font.name = BRAND_FONT
        rnum.font.size = Pt(number_size)
        rnum.font.bold = True
        rnum.font.color.rgb = ICHITA_BLUE
        if unit:
            # unit on its own small line beneath the value (Thai-aware, blue)
            punit = cell.add_paragraph()
            punit.paragraph_format.space_before = Pt(0)
            punit.paragraph_format.space_after = Pt(0)
            punit.paragraph_format.line_spacing = thai_line_pt(9.5)
            punit.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
            _add_split_run(punit, unit, BRAND_FONT, Pt(9.5), ICHITA_BLUE, bold=True)

        # Label — grey, Thai-aware (Bai Jamjuree + th-TH tag)
        plabel = cell.add_paragraph()
        plabel.paragraph_format.space_before = Pt(1)
        plabel.paragraph_format.space_after = Pt(2)
        plabel.paragraph_format.line_spacing = thai_line_pt(8.5)
        plabel.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST   # clears Thai marks at label size
        _add_split_run(plabel, label, BRAND_FONT, Pt(8.5), ICHITA_BLUE_GREY2)

    # Small spacing after the card row
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(1 if compact else 2)
    sp.paragraph_format.space_after = Pt(2 if compact else 4)


def add_formatted_text(paragraph, text, base_font=None, base_size=Pt(10),
                       base_color=None, is_blockquote=False):
    """Parse inline markdown (bold, italic, bold+italic, links) and add runs.
    Splits Thai/Latin into separate runs with matched visual sizes."""
    if base_font is None:
        base_font = BRAND_FONT
    if base_color is None:
        base_color = ICHITA_BLUE_GREY3

    pattern = re.compile(
        r'(\*\*\*(.+?)\*\*\*)'       # bold+italic
        r'|(\*\*(.+?)\*\*)'           # bold
        r'|(\*(.+?)\*)'               # italic
        r'|(\[([^\]]+)\]\(([^)]+)\))' # link
    )

    last_end = 0
    for match in pattern.finditer(text):
        before = text[last_end:match.start()]
        if before:
            _add_split_run(paragraph, before, base_font, base_size, base_color,
                           italic=is_blockquote)

        if match.group(2):  # ***bold+italic***
            _add_split_run(paragraph, match.group(2), base_font, base_size,
                           base_color, bold=True, italic=True)
        elif match.group(4):  # **bold**
            _add_split_run(paragraph, match.group(4), base_font, base_size,
                           base_color, bold=True, italic=is_blockquote)
        elif match.group(6):  # *italic*
            _add_split_run(paragraph, match.group(6), base_font, base_size,
                           base_color, italic=True)
        elif match.group(8):  # [link](url)
            _add_split_run(paragraph, match.group(9), base_font, base_size,
                           ICHITA_BLUE, underline=True)
        last_end = match.end()

    remaining = text[last_end:]
    if remaining:
        _add_split_run(paragraph, remaining, base_font, base_size, base_color,
                       italic=is_blockquote)


def add_cell_formatted_text(cell, text, is_header=False, font_name=None, font_size=Pt(9)):
    """Add formatted text to a table cell, preserving bold markdown."""
    if font_name is None:
        font_name = BRAND_FONT
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)

    if is_header:
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        _add_split_run(paragraph, clean, font_name, font_size, WHITE, bold=True)
    else:
        pattern = re.compile(r'\*\*(.+?)\*\*')
        last_end = 0
        for match in pattern.finditer(text):
            before = text[last_end:match.start()]
            if before:
                _add_split_run(paragraph, before, font_name, font_size, ICHITA_BLUE_GREY3)
            _add_split_run(paragraph, match.group(1), font_name, font_size,
                           ICHITA_BLUE_GREY3, bold=True)
            last_end = match.end()
        remaining = text[last_end:]
        if remaining:
            _add_split_run(paragraph, remaining, font_name, font_size, ICHITA_BLUE_GREY3)


def parse_table_line(line):
    """Parse a markdown table line into cell values."""
    cells = line.strip().strip('|').split('|')
    return [c.strip() for c in cells]


def is_separator_line(line):
    """Check if a line is a markdown table separator (|---|---|)."""
    stripped = line.strip().strip('|')
    parts = stripped.split('|')
    return all(re.match(r'^[\s\-:]+$', p) for p in parts)


def add_code_block(doc, code_lines):
    """Add a code block with monospace font and branded background.
    Uses keep_together to prevent page breaks within the block."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.right_indent = Inches(0.3)
    p.paragraph_format.keep_together = True

    pPr = p._p.get_or_add_pPr()
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_CODE_BG}" w:val="clear"/>')
    pPr.append(shading)

    code_text = '\n'.join(code_lines)
    run = p.add_run(code_text)
    run.font.name = MONO_FONT
    run.font.size = Pt(8.5)
    run.font.color.rgb = ICHITA_BLUE_GREY3


def add_table_from_rows(doc, header_cells, data_rows):
    """Create a branded table from parsed markdown table header and data rows."""
    num_cols = len(header_cells)

    normalized_data = []
    for row in data_rows:
        while len(row) < num_cols:
            row.append("")
        normalized_data.append(row[:num_cols])

    table = doc.add_table(rows=1 + len(normalized_data), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    set_table_borders(table, color="A0B0B8")

    # Prevent rows from splitting across pages and keep table together
    for row in table.rows:
        # cantSplit: prevents a single row from breaking across pages
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        # keep_together on each cell paragraph to keep table on one page
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_together = True
                paragraph.paragraph_format.keep_with_next = True
    # Remove keep_with_next from last row (nothing to keep with after table)
    last_row = table.rows[-1]
    for cell in last_row.cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_with_next = False

    # Header row — dark Ichita Blue Grey 03 background, white text
    hdr_row = table.rows[0]
    for j, cell_text in enumerate(header_cells):
        if j < num_cols:
            add_cell_formatted_text(hdr_row.cells[j], cell_text, is_header=True)
            set_cell_shading(hdr_row.cells[j], HEX_TABLE_HDR)

    # Data rows with subtle alternating shading
    for row_idx, row_data in enumerate(normalized_data):
        row = table.rows[row_idx + 1]
        for j, cell_text in enumerate(row_data):
            if j < num_cols:
                add_cell_formatted_text(row.cells[j], cell_text)
                if row_idx % 2 == 1:
                    set_cell_shading(row.cells[j], HEX_TABLE_ALT)

    # Small spacing after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(2)
    sp.paragraph_format.space_after = Pt(2)


def add_header_footer(doc, logo_path):
    """Add ICHITA logo to header and branded footer to all sections."""
    for section in doc.sections:
        # ── Header ──
        header = section.header
        header.is_linked_to_previous = False

        # Clear existing
        for p in header.paragraphs:
            p.clear()

        hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hp.paragraph_format.space_after = Pt(4)

        # Add logo image
        if os.path.exists(logo_path):
            run = hp.add_run()
            run.add_picture(logo_path, width=Emu(1371600), height=Emu(381000))
        else:
            # Fallback: text-based logo
            run = hp.add_run("ICHITA\u2122")
            run.font.name = BRAND_FONT
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = ICHITA_BLUE_GREY3

        # Add thin blue line under header
        pPr = hp._p.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="4" w:color="2978FF"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)

        # ── Footer — disabled ──
        footer = section.footer
        footer.is_linked_to_previous = False
        for p in footer.paragraphs:
            p.clear()


def add_title_page_band(doc):
    """Add a subtle Ichita Blue accent band (paragraph) after the title."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    pPr = p._p.get_or_add_pPr()
    # Thin blue bottom border as a decorative band
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="24" w:space="1" w:color="2978FF"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)


# ── Main Conversion ──────────────────────────────────────────────────────────

def convert_md_to_docx(input_path, output_path, logo_path=None, compact=False):
    """Convert a Markdown file to an Ichita-branded DOCX.

    Args:
        input_path: Path to source .md file
        output_path: Path to write .docx output
        logo_path: Path to logo PNG for header (default: bundled Ichita wordmark)
    """
    if logo_path is None:
        logo_path = DEFAULT_LOGO

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = Document()

    # ── Default document font ──
    style = doc.styles['Normal']
    font = style.font
    font.name = BRAND_FONT
    font.size = Pt(10)
    font.color.rgb = ICHITA_BLUE_GREY3
    style.paragraph_format.space_after = Pt(3 if compact else 5)
    style.paragraph_format.space_before = Pt(1 if compact else 2)
    # Line spacing: Thai stacks base + upper vowel + tone above the ascent, and
    # hangs a below-vowel under the baseline, so a Latin line box cannot hold two
    # consecutive Thai lines apart. Sized from the fonts by scripts/thai_line_pitch.py.
    # Per-size, so headings/labels/numbers set their own value below.
    style.paragraph_format.line_spacing = thai_line_pt(10)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
    # Set Complex Script font + scaled size on default style
    from docx.oxml import OxmlElement
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    if TH_AEONIK_MODE:
        # Single font for all scripts
        rFonts.set(qn('w:ascii'), BRAND_FONT)
        rFonts.set(qn('w:hAnsi'), BRAND_FONT)
        rFonts.set(qn('w:cs'), BRAND_FONT)
        rFonts.set(qn('w:eastAsia'), BRAND_FONT)
        scaled_hp = str(round(10 * 2))  # No scaling
    else:
        rFonts.set(qn('w:cs'), THAI_FONT)
        rFonts.set(qn('w:eastAsia'), THAI_FONT)
        scaled_hp = str(round(10 * 2 * THAI_SCALE))
    szCs_el = rPr.find(qn('w:szCs'))
    if szCs_el is not None:
        szCs_el.set(qn('w:val'), scaled_hp)
    else:
        szCs_el = OxmlElement('w:szCs')
        szCs_el.set(qn('w:val'), scaled_hp)
        rPr.append(szCs_el)
    # Default proofing language: English for Latin text, Thai for complex script.
    # Inherited by every run, so even untagged runs (KPI numbers, etc.) proof Thai
    # with the Thai dictionary instead of English.
    lang_el = rPr.find(qn('w:lang'))
    if lang_el is None:
        lang_el = OxmlElement('w:lang')
        rPr.append(lang_el)
    lang_el.set(qn('w:val'), 'en-US')
    lang_el.set(qn('w:bidi'), 'th-TH')

    # ── Heading styles (Ichita branding) ──
    heading_configs = [
        (1, 18 if compact else 22, ICHITA_BLUE_GREY3),   # H1: large, dark
        (2, 13 if compact else 15, ICHITA_BLUE_GREY3),   # H2: section headers
        (3, 11 if compact else 12, ICHITA_BLUE),         # H3: subsections in brand blue
        (4, 10.5, ICHITA_BLUE),                          # H4: minor subsections
    ]
    for level, size, color in heading_configs:
        hs = doc.styles[f'Heading {level}']
        hs.font.name = BRAND_FONT
        hs.font.size = Pt(size)
        hs.font.color.rgb = color
        # Measured Thai clearance ratio at this heading's actual size, so a
        # wrapped heading keeps its two lines apart.
        hs.paragraph_format.line_spacing = thai_line_pt(size)
        hs.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
        hs.font.bold = True
        # Set Complex Script font + scaled size on heading style
        h_rPr = hs.element.get_or_add_rPr()
        h_rFonts = h_rPr.find(qn('w:rFonts'))
        if h_rFonts is None:
            h_rFonts = OxmlElement('w:rFonts')
            h_rPr.insert(0, h_rFonts)
        if TH_AEONIK_MODE:
            h_rFonts.set(qn('w:ascii'), BRAND_FONT)
            h_rFonts.set(qn('w:hAnsi'), BRAND_FONT)
            h_rFonts.set(qn('w:cs'), BRAND_FONT)
            h_rFonts.set(qn('w:eastAsia'), BRAND_FONT)
            h_scaled_hp = str(round(size * 2))  # No scaling
        else:
            h_rFonts.set(qn('w:cs'), THAI_FONT)
            h_rFonts.set(qn('w:eastAsia'), THAI_FONT)
            h_scaled_hp = str(round(size * 2 * THAI_SCALE))
        h_szCs = h_rPr.find(qn('w:szCs'))
        if h_szCs is not None:
            h_szCs.set(qn('w:val'), h_scaled_hp)
        else:
            h_szCs = OxmlElement('w:szCs')
            h_szCs.set(qn('w:val'), h_scaled_hp)
            h_rPr.append(h_szCs)
        if level == 1:
            hs.paragraph_format.space_before = Pt(10 if compact else 20)
            hs.paragraph_format.space_after = Pt(5 if compact else 8)
        elif level == 2:
            hs.paragraph_format.space_before = Pt(9 if compact else 16)
            hs.paragraph_format.space_after = Pt(4 if compact else 6)
        elif level == 3:
            hs.paragraph_format.space_before = Pt(7 if compact else 12)
            hs.paragraph_format.space_after = Pt(3 if compact else 5)
        else:
            hs.paragraph_format.space_before = Pt(5 if compact else 8)
            hs.paragraph_format.space_after = Pt(3 if compact else 4)

    # ── List Bullet style ──
    if 'List Bullet' in doc.styles:
        lb = doc.styles['List Bullet']
        lb.font.name = BRAND_FONT
        lb.font.size = Pt(10)
        lb.font.color.rgb = ICHITA_BLUE_GREY3

    # ── Page margins ──
    v_margin = Cm(1.4) if compact else Cm(2.5)
    h_margin = Cm(1.6) if compact else Cm(2.5)
    for section in doc.sections:
        section.top_margin = v_margin
        section.bottom_margin = v_margin
        section.left_margin = h_margin
        section.right_margin = h_margin
    # Content width (inches) for full-bleed elements like KPI cards (A4 = 21cm wide)
    content_width_in = (21.0 - 2 * (1.6 if compact else 2.5)) / 2.54

    # ── Header and footer are added before doc.save() below ──

    i = 0
    first_h1 = True

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n')

        # ── Horizontal rule (---) ──
        if re.match(r'^---+\s*$', stripped):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="2978FF"/>'
                f'</w:pBdr>'
            )
            pPr.append(pBdr)
            i += 1
            continue

        # ── KPI stat-card block (::: kpi … :::) ──
        if re.match(r'^:::\s*kpi\b', stripped.strip(), re.I):
            i += 1
            cards = []
            while i < len(lines):
                row = lines[i].rstrip('\n').strip()
                if row.startswith(':::'):
                    i += 1
                    break
                if row and '|' in row:
                    number_part, label = row.split('|', 1)
                    # optional unit after "::" → "value :: unit | label"
                    if '::' in number_part:
                        value, unit = number_part.split('::', 1)
                    else:
                        value, unit = number_part, ''
                    cards.append((value.strip(), unit.strip(), label.strip()))
                i += 1
            if cards:
                add_kpi_cards(doc, cards, content_width_in=content_width_in, compact=compact)
            continue

        # ── Code block (```) ──
        if stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].rstrip('\n').startswith('```'):
                code_lines.append(lines[i].rstrip('\n'))
                i += 1
            if i < len(lines):
                i += 1
            add_code_block(doc, code_lines)
            continue

        # ── Table (| ... |) ──
        if stripped.startswith('|') and '|' in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].rstrip('\n').strip().startswith('|'):
                table_lines.append(lines[i].rstrip('\n'))
                i += 1

            if len(table_lines) < 2:
                for tl in table_lines:
                    p = doc.add_paragraph()
                    add_formatted_text(p, tl.strip())
                continue

            header_cells = parse_table_line(table_lines[0])
            data_start = 1
            if len(table_lines) > 1 and is_separator_line(table_lines[1]):
                data_start = 2

            data_rows = []
            for tl in table_lines[data_start:]:
                if not is_separator_line(tl):
                    data_rows.append(parse_table_line(tl))

            add_table_from_rows(doc, header_cells, data_rows)
            continue

        # ── Headings (#, ##, ###, ####) ──
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if level == 1 and first_h1:
                # ── Title: centered, large, Ichita brand ──
                p = doc.add_heading('', level=1)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', heading_text)
                _add_split_run(p, clean_text, BRAND_FONT, Pt(26),
                               ICHITA_BLUE_GREY3, bold=True)
                # Sized for the ACTUAL title size, so a wrapped title keeps its
                # two lines apart (e.g. ต้น over a below-vowel).
                p.paragraph_format.line_spacing = thai_line_pt(26)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
                first_h1 = False
                i += 1

                # Add decorative blue band below title
                add_title_page_band(doc)
                continue
            else:
                p = doc.add_heading('', level=level)
                sizes = {1: Pt(22), 2: Pt(15), 3: Pt(12), 4: Pt(10)}
                colors = {
                    1: ICHITA_BLUE_GREY3,
                    2: ICHITA_BLUE_GREY3,
                    3: ICHITA_BLUE,
                    4: ICHITA_BLUE,
                }

                # For H2, add a left accent bar
                if level == 2:
                    pPr = p._p.get_or_add_pPr()
                    pBdr = parse_xml(
                        f'<w:pBdr {nsdecls("w")}>'
                        f'  <w:left w:val="single" w:sz="24" w:space="6" w:color="2978FF"/>'
                        f'</w:pBdr>'
                    )
                    pPr.append(pBdr)

                add_formatted_text(p, heading_text, base_font=BRAND_FONT,
                                   base_size=sizes[level], base_color=colors[level])
                for run in p.runs:
                    run.font.color.rgb = colors[level]
                    run.font.bold = True
                # Matched to the heading's ACTUAL run size (sizes[level]) — the
                # Heading style default is computed from a different size.
                p.paragraph_format.line_spacing = thai_line_pt(sizes[level].pt)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.AT_LEAST

            i += 1
            continue

        # ── Blockquote (> text) ──
        if stripped.startswith('>'):
            quote_text = stripped.lstrip('>').strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.right_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)

            pPr = p._p.get_or_add_pPr()
            # Left border in Ichita Blue
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:left w:val="single" w:sz="18" w:space="8" w:color="2978FF"/>'
                f'</w:pBdr>'
            )
            pPr.append(pBdr)

            # Light background
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_QUOTE_BG}" w:val="clear"/>')
            pPr.append(shading)

            add_formatted_text(p, quote_text, is_blockquote=True,
                               base_color=ICHITA_BLUE_GREY2)
            i += 1
            continue

        # ── Numbered list (1. item) ──
        numbered_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if numbered_match:
            num = numbered_match.group(1)
            item_text = numbered_match.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)

            # Number in Ichita Blue
            run = p.add_run(f"{num}. ")
            run.font.name = BRAND_FONT
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = ICHITA_BLUE

            add_formatted_text(p, item_text)
            i += 1
            continue

        # ── Bullet point (- item or * item, including nested) ──
        bullet_match = re.match(r'^(\s*)([-*+])\s+(.+)$', stripped)
        if bullet_match:
            indent_spaces = len(bullet_match.group(1))
            bullet_text = bullet_match.group(3)
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)

            if indent_spaces >= 2:
                p.paragraph_format.left_indent = Inches(0.6 + (indent_spaces // 2) * 0.25)

            p.clear()
            add_formatted_text(p, bullet_text)
            i += 1
            continue

        # ── Empty line ──
        if not stripped.strip():
            i += 1
            continue

        # ── Regular paragraph ──
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        add_formatted_text(p, stripped)
        i += 1

    # ── ICHITA branded header + footer ──
    if _HAS_BRANDED_HEADER_FOOTER:
        add_ichita_header(doc, logo_path=logo_path)
        add_ichita_footer(doc)
    else:
        add_header_footer(doc, logo_path)

    doc.save(output_path)

    # ── Report ──
    size = os.path.getsize(output_path)
    para_count = len(doc.paragraphs)
    table_count = len(doc.tables)
    print(f"Saved: {output_path}")
    print(f"  Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"  Paragraphs: {para_count}, Tables: {table_count}")
    if TH_AEONIK_MODE:
        print(f"  Font: {BRAND_FONT} (unified Latin+Thai)")
    else:
        print(f"  Font: {BRAND_FONT} + {THAI_FONT} (Thai, {THAI_SCALE}x)")
    print(f"  Brand: ICHITA -- Separation Technologies")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown to Ichita-branded DOCX.",
        epilog="Examples:\n"
               "  python3 md_to_docx.py report.md\n"
               "  python3 md_to_docx.py report.md output.docx\n"
               "  python3 md_to_docx.py report.md --logo custom_logo.png\n",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Source Markdown file")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output DOCX path (default: <input>.docx)")
    parser.add_argument("--logo", default=None,
                        help="Path to logo PNG for header "
                             "(default: bundled Ichita wordmark)")
    parser.add_argument("--compact", action="store_true",
                        help="Tighter margins, spacing and heading sizes "
                             "(for dense one-page briefs)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: source file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output = args.output
    if output is None:
        output = os.path.splitext(args.input)[0] + ".docx"

    logo = args.logo
    if logo and not os.path.exists(logo):
        print(f"Warning: logo file not found: {logo} — will use text fallback",
              file=sys.stderr)

    print(f"Converting: {os.path.basename(args.input)}")
    print(f"Brand style: ICHITA")
    convert_md_to_docx(args.input, output, logo_path=logo, compact=args.compact)


if __name__ == "__main__":
    main()
