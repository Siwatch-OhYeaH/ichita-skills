#!/usr/bin/env python3
"""
Convert HTML documents to Ichita-branded .docx files.

Applies Ichita Brand Identity styling:
- Colors: Blue #2978FF (accent), Blue Grey 03 #263338 (headings/body),
          Blue Light #82B0FF, Blue Grey 01 #CFD9DB (backgrounds)
- Font: TH Aeonik / Aeonik (with Calibri fallback)
- Logo: ICHITA wordmark in header
- Footer: www.ichita.co.th

Handles: h1-h4, p, table, ul/ol/li, strong, em, a, img, br, hr,
         blockquote, code, pre, and nested inline tags.

Usage:
    python3 html_to_docx.py input.html
    python3 html_to_docx.py input.html output.docx
    python3 html_to_docx.py input.html output.docx --logo logo.png
    python3 html_to_docx.py input.html output.docx --no-logo --footer "my footer"
    cat input.html | python3 html_to_docx.py - output.docx
"""

import argparse
import os
import sys
from html.parser import HTMLParser
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
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
WHITE             = RGBColor(0xFF, 0xFF, 0xFF)

# Hex strings for cell shading (no # prefix)
HEX_BLUE         = "2978FF"
HEX_BLUE_GREY3   = "263338"
HEX_TABLE_HDR    = "263338"
HEX_TABLE_ALT    = "EFF2F3"
HEX_CODE_BG      = "EFF2F3"
HEX_QUOTE_BG     = "EBF0F7"


# ── Script directory ─────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Font Configuration ────────────────────────────────────────────────────────

BRAND_FONT = "Calibri"
THAI_FONT  = "Bai Jamjuree"
THAI_SCALE = 0.9
MONO_FONT  = "Courier New"
TH_AEONIK_MODE = False

# Thai block, U+0E00-U+0E7F.
THAI_BLOCK = ('\u0e00', '\u0e7f')


def _font_files(font_dir, max_depth=2):
    """Font filenames under `font_dir`, RECURSIVELY — see the md_to_docx twin.

    Font directories nest in practice: this repo installs to
    ~/.local/share/fonts/th-current/, which a flat os.listdir() of the parent
    cannot see.
    """
    out = []
    base_depth = font_dir.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(font_dir):
        if root.count(os.sep) - base_depth >= max_depth:
            dirs[:] = []
        out.extend(f.lower() for f in files)
    return out


_font_dirs = [
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
    os.path.expanduser("~/.local/share/fonts"),
    os.path.join(SCRIPT_DIR, "Aeonik-Essentials-Web"),
    os.path.expanduser("~/.fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
]

# THE FONT IS A FUNCTION OF THE DOCUMENT'S LANGUAGE — Siwatch, 2026-08-05.
#
# This block used to be INSTALLATION-driven: if TH Aeonik was found anywhere, it
# became the font for every document. That is a defect under the two-font rule,
# and a silent one — an English-only brief would have picked up TH Aeonik's 1537
# box and led 28% loose purely because the font happened to be installed, with
# nothing in the output saying so.
#
# Availability is now recorded here and the CHOICE is made per document, from the
# source content, by select_fonts_for_source() below.
_TH_AEONIK_AVAILABLE = False
for _fd in _font_dirs:
    try:
        if any("th-aeonik" in f.lower() or "thaeonik" in f.lower()
               for f in _font_files(_fd)):
            _TH_AEONIK_AVAILABLE = True
            break
    except OSError:
        pass

if True:
    _AEONIK_FOUND = False
    for _fd in _font_dirs:
        try:
            if any("aeonik" in f.lower() for f in os.listdir(_fd)):
                BRAND_FONT = "Aeonik"
                _AEONIK_FOUND = True
                break
        except OSError:
            pass
    if not _AEONIK_FOUND:
        print(
            "WARNING: Aeonik font family not detected on system — falling back to "
            "Calibri. DOCX will not be brand-compliant. Install fonts via "
            "assets/fonts/install-fonts.sh in the ichita-skills repo.",
            file=sys.stderr,
        )


def document_has_thai(text):
    """True if `text` contains any Thai codepoint."""
    lo, hi = THAI_BLOCK
    return any(lo <= c <= hi for c in text)


def select_fonts_for_source(text, mode="auto", quiet=False):
    """Choose the font for this document from its content. Twin of md_to_docx's.

    Sets BRAND_FONT / THAI_FONT / THAI_SCALE / TH_AEONIK_MODE and LOGS the choice.
    The log line is not optional: an unlogged font decision is how the previous
    installation-driven behaviour went unnoticed.
    """
    global BRAND_FONT, THAI_FONT, THAI_SCALE, TH_AEONIK_MODE

    thai = document_has_thai(text)
    if mode == "aeonik":
        want = False
        why = "forced by --font-mode aeonik"
    elif mode == "th-aeonik":
        want = True
        why = "forced by --font-mode th-aeonik"
    else:
        want = thai
        why = "source contains Thai" if thai else "source is Latin-only"

    if want and not _TH_AEONIK_AVAILABLE and mode == "auto":
        # Availability downgrades AUTO only. An explicit --font-mode th-aeonik is
        # a person's decision and is honoured even if the font is absent here —
        # the document may well be opened on a machine that has it.
        TH_AEONIK_MODE = False
        THAI_FONT = "Bai Jamjuree"
        THAI_SCALE = 0.9
        if not quiet:
            print(f"  font: {BRAND_FONT} + {THAI_FONT} (split) — source contains "
                  f"Thai but TH Aeonik is not installed here, so the merged face "
                  f"could not be used. Install it and regenerate.")
        return BRAND_FONT

    TH_AEONIK_MODE = want
    if want:
        BRAND_FONT = THAI_FONT = "TH Aeonik"
        THAI_SCALE = 1.0
        detail = "TH Aeonik for both scripts, line box 1537"
    else:
        THAI_FONT = "Bai Jamjuree"
        THAI_SCALE = 0.9
        detail = f"{BRAND_FONT} for Latin + {THAI_FONT} for Thai, line box 1200"
        if thai:
            detail += "  (source HAS Thai — split fonts were forced)"
    if not quiet:
        print(f"  font: {detail}  [{why}]")
    return BRAND_FONT


# ── Import shared header/footer helpers ─────────────────────────────────────

try:
    from docx_helpers import add_ichita_header, add_ichita_footer, ICHITA_BRAND
    _HAS_BRANDED_HEADER_FOOTER = True
except ImportError:
    _HAS_BRANDED_HEADER_FOOTER = False

    def add_ichita_header(doc, logo_path=None, **kwargs):
        """Fallback: inline header implementation."""
        for section in doc.sections:
            header = section.header
            header.is_linked_to_previous = False
            for p in header.paragraphs:
                p.clear()
            hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            hp.paragraph_format.space_after = Pt(4)
            if logo_path and os.path.exists(logo_path):
                run = hp.add_run()
                run.add_picture(logo_path, width=Emu(1371600), height=Emu(381000))
            else:
                run = hp.add_run("ICHITA\u2122")
                run.font.name = BRAND_FONT
                run.font.size = Pt(16)
                run.font.bold = True
                run.font.color.rgb = ICHITA_BLUE_GREY3
            pPr = hp._p.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:bottom w:val="single" w:sz="6" w:space="4" w:color="2978FF"/>'
                f'</w:pBdr>'
            )
            pPr.append(pBdr)

    def add_ichita_footer(doc, footer_text="www.ichita.co.th", **kwargs):
        """Fallback: inline footer implementation."""
        for section in doc.sections:
            footer = section.footer
            footer.is_linked_to_previous = False
            fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            fp.clear()
            fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            fr = fp.add_run(footer_text)
            fr.font.size = Pt(9)
            fr.font.color.rgb = ICHITA_BLUE_GREY2
            fr.font.name = BRAND_FONT


# ── Default Logo Path ─────────────────────────────────────────────────────────

_LOGO_ASSET = os.path.join(SCRIPT_DIR, "assets", "ichita-wordmark-dark-on-white.png")
# Repo-relative fallback: skills/ichita-docx/scripts/ → repo root is three "..".
_LOGO_REPO_ASSETS = os.path.normpath(os.path.join(
    SCRIPT_DIR, "..", "..", "..", "assets", "logos", "ichita-wordmark-dark-on-white.png"))
DEFAULT_LOGO = (
    _LOGO_ASSET if os.path.exists(_LOGO_ASSET)
    else _LOGO_REPO_ASSETS if os.path.exists(_LOGO_REPO_ASSETS)
    else None
)


# ── Thai/Latin text helpers ────────────────────────────────────────────────────

def _is_thai(c):
    """Check if a character is Thai (U+0E00–U+0E7F)."""
    return '\u0e00' <= c <= '\u0e7f'


def _split_thai_latin(text):
    """Split text into (segment, is_thai) tuples."""
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


def _add_split_run(paragraph, text, font_name, base_size, color,
                   bold=False, italic=False, underline=False):
    """Add text as split Thai/Latin runs with correct fonts and sizes."""
    if not text:
        return None

    if TH_AEONIK_MODE:
        run = paragraph.add_run(text)
        run.font.name = font_name
        run.font.size = base_size
        run.font.color.rgb = color
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rPr.insert(0, rFonts)
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        if underline:
            run.font.underline = True
        return run

    # base_size is Pt() object; compute scaled Thai size
    if hasattr(base_size, 'pt'):
        size_pt = base_size.pt
    else:
        size_pt = float(base_size) / 12700
    thai_size = Pt(round(size_pt * THAI_SCALE * 2) / 2)

    last_run = None
    for segment, is_thai in _split_thai_latin(text):
        run = paragraph.add_run(segment)
        run.font.name = THAI_FONT if is_thai else font_name
        run.font.size = thai_size if is_thai else base_size
        run.font.color.rgb = color
        rPr = run._r.get_or_add_rPr()
        lang = rPr.find(qn('w:lang'))
        if lang is None:
            lang = parse_xml(f'<w:lang {nsdecls("w")}/>')
            rPr.append(lang)
        if is_thai:
            lang.set(qn('w:bidi'), 'th-TH')
        else:
            lang.set(qn('w:val'), 'en-US')
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        if underline:
            run.font.underline = True
        last_run = run
    return last_run


def _set_cell_shading(cell, color_hex):
    """Apply background shading to a table cell."""
    shading = parse_xml(
        f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_table_borders(table, color="A0B0B8"):
    """Apply borders to every cell in the table."""
    tbl = table._tbl
    tblPr = (tbl.tblPr if tbl.tblPr is not None
             else parse_xml(f'<w:tblPr {nsdecls("w")}/>'))
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


# ── HTML Parser ───────────────────────────────────────────────────────────────

class IchitaHTMLParser(HTMLParser):
    """Parse HTML and build a DOCX document with Ichita brand styling.

    Maintains a tag stack to handle nested inline formatting correctly.
    Block-level elements (headings, p, table, ul, ol, blockquote, pre, hr)
    flush/create DOCX paragraphs. Inline elements (strong, em, a, code)
    modify run properties on the current paragraph.
    """

    def __init__(self, doc, font_name=None, input_dir=None):
        super().__init__()
        self.doc = doc
        self.font_name = font_name or BRAND_FONT
        self.input_dir = input_dir or os.getcwd()

        # Current paragraph and run state
        self._para = None
        self._bold = False
        self._italic = False
        self._code_inline = False
        self._link_href = None

        # Block context
        self._heading_level = 0      # 1–4 when inside a heading
        self._in_pre = False         # <pre> block
        self._in_blockquote = False
        self._in_code_block = False  # <pre><code> combination
        self._pre_lines = []         # accumulates text inside <pre>

        # List context
        self._list_stack = []        # stack of 'ul'/'ol' for nesting
        self._list_counters = []     # counters for each <ol> level
        self._in_li = False

        # Table context
        self._table = None
        self._table_rows = []        # list of lists: [[cell_text, is_header], ...]
        self._current_row = []
        self._current_cell_parts = []  # (text, bold, italic) tuples in cell
        self._in_th = False
        self._in_td = False
        self._table_depth = 0        # nested table guard

        # Stats
        self.headings_added = 0
        self.tables_added = 0
        self.images_added = 0
        self.lists_added = 0

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _flush_para(self):
        """Close current paragraph; following content starts a new one."""
        self._para = None

    def _ensure_para(self, style=None):
        """Return current paragraph, creating one if needed."""
        if self._para is None:
            if style:
                self._para = self.doc.add_paragraph(style=style)
            else:
                self._para = self.doc.add_paragraph()
                self._para.paragraph_format.space_before = Pt(2)
                self._para.paragraph_format.space_after = Pt(5)
        return self._para

    def _add_text_to_para(self, text, para=None):
        """Add text to paragraph with current inline formatting state."""
        if para is None:
            para = self._ensure_para()
        if not text:
            return

        if self._code_inline:
            run = para.add_run(text)
            run.font.name = MONO_FONT
            run.font.size = Pt(9)
            run.font.color.rgb = ICHITA_BLUE_GREY3
            return

        color = ICHITA_BLUE_GREY3
        if self._link_href:
            color = ICHITA_BLUE

        _add_split_run(
            para, text,
            self.font_name, Pt(10), color,
            bold=self._bold,
            italic=self._italic,
            underline=bool(self._link_href),
        )

    def _add_heading(self, level, text):
        """Add an Ichita-branded heading paragraph."""
        sizes = {1: Pt(22), 2: Pt(15), 3: Pt(12), 4: Pt(10)}
        colors = {
            1: ICHITA_BLUE_GREY3,
            2: ICHITA_BLUE_GREY3,
            3: ICHITA_BLUE,
            4: ICHITA_BLUE,
        }
        size = sizes.get(level, Pt(10))
        color = colors.get(level, ICHITA_BLUE_GREY3)

        p = self.doc.add_heading('', level=level)

        if level == 2:
            pPr = p._p.get_or_add_pPr()
            pBdr = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:left w:val="single" w:sz="24" w:space="6" w:color="2978FF"/>'
                f'</w:pBdr>'
            )
            pPr.append(pBdr)

        # Italic heading level 4
        italic = (level == 4)
        _add_split_run(p, text, self.font_name, size, color,
                       bold=True, italic=italic)
        self.headings_added += 1
        return p

    def _add_hr(self):
        """Add a horizontal rule (thin blue line)."""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="2978FF"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)

    def _add_code_block(self, lines):
        """Add a code block with monospace font and grey background."""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.right_indent = Inches(0.3)
        p.paragraph_format.keep_together = True

        pPr = p._p.get_or_add_pPr()
        shading = parse_xml(
            f'<w:shd {nsdecls("w")} w:fill="{HEX_CODE_BG}" w:val="clear"/>')
        pPr.append(shading)

        code_text = '\n'.join(lines)
        run = p.add_run(code_text)
        run.font.name = MONO_FONT
        run.font.size = Pt(8.5)
        run.font.color.rgb = ICHITA_BLUE_GREY3

    def _flush_table(self):
        """Build and style the accumulated HTML table into DOCX.

        VS-5 (Sibyl QA PR4): preview-B-3 reportedly degrades table borders /
        column structure. Suspected root causes (unverified — needs side-by-side
        path-A vs path-B-3 inspection): (a) _table_depth nesting interaction
        when an inner element triggers a premature flush; (b) HEX border colour
        "A0B0B8" too light to render visibly under pandoc-roundtripped DOCX
        styles; (c) header detection fallback (line 463-465) misclassifying a
        body row as header when path-B HTML omits <th>. Audit recommended in a
        follow-up PR.
        """
        if not self._table_rows:
            return

        # Determine column count from widest row
        num_cols = max(len(row) for row in self._table_rows) if self._table_rows else 1

        # Normalise rows to same width
        def normalise(row):
            while len(row) < num_cols:
                row.append(("", False))
            return row[:num_cols]

        rows = [normalise(r) for r in self._table_rows]

        # Find header rows (all cells are th)
        header_count = 0
        for row in rows:
            if all(is_hdr for _, is_hdr in row):
                header_count += 1
            else:
                break
        if header_count == 0 and rows:
            # Treat first row as header if no <th> was used
            header_count = 1

        table = self.doc.add_table(rows=len(rows), cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        _set_table_borders(table, color="A0B0B8")

        for ri, row_data in enumerate(rows):
            tbl_row = table.rows[ri]
            is_header_row = (ri < header_count)
            is_alt = (not is_header_row) and ((ri - header_count) % 2 == 1)

            for ci, (cell_text, _is_th) in enumerate(row_data):
                cell = tbl_row.cells[ci]
                cell_para = cell.paragraphs[0]
                cell_para.paragraph_format.space_before = Pt(2)
                cell_para.paragraph_format.space_after = Pt(2)

                if is_header_row:
                    _set_cell_shading(cell, HEX_TABLE_HDR)
                    _add_split_run(cell_para, cell_text, self.font_name,
                                   Pt(10), WHITE, bold=True)
                else:
                    if is_alt:
                        _set_cell_shading(cell, HEX_TABLE_ALT)
                    _add_split_run(cell_para, cell_text, self.font_name,
                                   Pt(10), ICHITA_BLUE_GREY3)

            # Keep rows together
            for tbl_cell in tbl_row.cells:
                for cp in tbl_cell.paragraphs:
                    cp.paragraph_format.keep_together = True
                    if ri < len(rows) - 1:
                        cp.paragraph_format.keep_with_next = True

        # Spacer after table
        sp = self.doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(2)
        sp.paragraph_format.space_after = Pt(4)

        self.tables_added += 1
        self._table_rows = []
        self._current_row = []

    # ── HTMLParser callbacks ─────────────────────────────────────────────────

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()

        # ── Headings ──────────────────────────────────────────────────────────
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self._flush_para()
            self._heading_level = int(tag[1])
            self._para = self._add_heading(self._heading_level, "")
            # We'll fill text via handle_data; need empty para reference
            # Actually clear the para so _add_text_to_para fills it
            return

        # ── Paragraph ─────────────────────────────────────────────────────────
        if tag == 'p':
            self._flush_para()
            if self._in_blockquote:
                p = self.doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.right_indent = Inches(0.3)
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(8)
                pPr = p._p.get_or_add_pPr()
                pBdr = parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'  <w:left w:val="single" w:sz="18" w:space="8" w:color="2978FF"/>'
                    f'</w:pBdr>'
                )
                pPr.append(pBdr)
                shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:fill="{HEX_QUOTE_BG}" w:val="clear"/>')
                pPr.append(shading)
                self._para = p
            return

        # ── Lists ─────────────────────────────────────────────────────────────
        if tag in ('ul', 'ol'):
            self._list_stack.append(tag)
            self._list_counters.append(0)
            return

        if tag == 'li':
            self._flush_para()
            self._in_li = True
            depth = len(self._list_stack)
            list_type = self._list_stack[-1] if self._list_stack else 'ul'

            if list_type == 'ol':
                self._list_counters[-1] += 1
                counter = self._list_counters[-1]
                p = self.doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.5 + (depth - 1) * 0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                # Number in Ichita Blue
                num_run = p.add_run(f"{counter}. ")
                num_run.font.name = self.font_name
                num_run.font.size = Pt(10)
                num_run.font.bold = True
                num_run.font.color.rgb = ICHITA_BLUE
                self._para = p
            else:
                p = self.doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                if depth > 1:
                    p.paragraph_format.left_indent = Inches(
                        0.5 + (depth - 1) * 0.25)
                self._para = p
            self.lists_added += 1
            return

        # ── Table ─────────────────────────────────────────────────────────────
        if tag == 'table':
            self._flush_para()
            self._table_depth += 1
            if self._table_depth == 1:
                self._table_rows = []
                self._current_row = []
            return

        if tag == 'tr':
            if self._table_depth == 1:
                self._current_row = []
            return

        if tag == 'th':
            if self._table_depth == 1:
                self._current_cell_parts = []
                self._in_th = True
            return

        if tag == 'td':
            if self._table_depth == 1:
                self._current_cell_parts = []
                self._in_td = True
            return

        # ── Inline formatting ──────────────────────────────────────────────────
        if tag in ('strong', 'b'):
            self._bold = True
            return

        if tag in ('em', 'i'):
            self._italic = True
            return

        if tag == 'a':
            self._link_href = attrs_dict.get('href', '')
            return

        if tag == 'code':
            if not self._in_pre:
                self._code_inline = True
            return

        # ── Block elements ─────────────────────────────────────────────────────
        if tag == 'blockquote':
            self._flush_para()
            self._in_blockquote = True
            return

        if tag == 'pre':
            self._flush_para()
            self._in_pre = True
            self._pre_lines = []
            return

        if tag == 'hr':
            self._flush_para()
            self._add_hr()
            return

        if tag == 'br':
            if self._para is not None:
                run = self._para.add_run()
                run.add_break()
            return

        if tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            if src:
                # Resolve relative paths against input file dir
                if not os.path.isabs(src):
                    src = os.path.join(self.input_dir, src)
                if os.path.exists(src):
                    para = self._ensure_para()
                    run = para.add_run()
                    try:
                        run.add_picture(src, width=Inches(4))
                        self.images_added += 1
                    except Exception:
                        # If image fails, fall back to alt text
                        if alt:
                            run.text = f"[image: {alt}]"
                elif alt:
                    para = self._ensure_para()
                    para.add_run(f"[image: {alt}]")
            return

        # ── Body/html/head/title — ignore ──────────────────────────────────────
        # (just let content flow through)

    def handle_endtag(self, tag):
        tag = tag.lower()

        # ── Headings ──────────────────────────────────────────────────────────
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self._heading_level = 0
            self._flush_para()
            return

        # ── Paragraph ─────────────────────────────────────────────────────────
        if tag == 'p':
            self._flush_para()
            return

        # ── Lists ─────────────────────────────────────────────────────────────
        if tag in ('ul', 'ol'):
            if self._list_stack:
                self._list_stack.pop()
            if self._list_counters:
                self._list_counters.pop()
            return

        if tag == 'li':
            self._in_li = False
            self._flush_para()
            return

        # ── Table ─────────────────────────────────────────────────────────────
        if tag == 'table':
            if self._table_depth == 1:
                self._flush_table()
            self._table_depth = max(0, self._table_depth - 1)
            return

        if tag == 'tr':
            if self._table_depth == 1 and self._current_row is not None:
                self._table_rows.append(self._current_row)
                self._current_row = []
            return

        if tag in ('th', 'td'):
            if self._table_depth == 1:
                # Join all collected text parts for this cell
                cell_text = ''.join(t for t, _, _ in self._current_cell_parts)
                is_header = (tag == 'th') or self._in_th
                self._current_row.append((cell_text, is_header))
                self._current_cell_parts = []
                self._in_th = False
                self._in_td = False
            return

        # ── Inline formatting ──────────────────────────────────────────────────
        if tag in ('strong', 'b'):
            self._bold = False
            return

        if tag in ('em', 'i'):
            self._italic = False
            return

        if tag == 'a':
            self._link_href = None
            return

        if tag == 'code':
            self._code_inline = False
            return

        # ── Block elements ─────────────────────────────────────────────────────
        if tag == 'blockquote':
            self._in_blockquote = False
            self._flush_para()
            return

        if tag == 'pre':
            self._in_pre = False
            self._in_code_block = False
            if self._pre_lines:
                # Strip leading/trailing blank lines
                lines = self._pre_lines
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                self._add_code_block(lines)
                self._pre_lines = []
            return

    def handle_data(self, data):
        # Inside <pre>, collect raw lines
        if self._in_pre:
            self._pre_lines.extend(data.split('\n'))
            return

        # Inside a table cell, collect text
        if self._in_th or self._in_td:
            if self._table_depth == 1:
                self._current_cell_parts.append(
                    (data, self._bold, self._italic))
            return

        # Skip whitespace-only text between block elements (avoid spurious paragraphs)
        if not data.strip() and self._para is None:
            return

        # Heading: route text directly to heading paragraph
        if self._heading_level > 0 and self._para is not None:
            sizes = {1: Pt(22), 2: Pt(15), 3: Pt(12), 4: Pt(10)}
            colors = {
                1: ICHITA_BLUE_GREY3, 2: ICHITA_BLUE_GREY3,
                3: ICHITA_BLUE, 4: ICHITA_BLUE,
            }
            size = sizes.get(self._heading_level, Pt(10))
            color = colors.get(self._heading_level, ICHITA_BLUE_GREY3)
            _add_split_run(self._para, data, self.font_name, size, color,
                           bold=True, italic=(self._heading_level == 4))
            return

        self._add_text_to_para(data)


# ── Document setup ────────────────────────────────────────────────────────────

def _setup_document_styles(doc, font_name, margin_cm=2.0):
    """Apply Ichita brand to default document styles."""
    from docx.oxml import OxmlElement

    # Normal style
    style = doc.styles['Normal']
    style.font.name = font_name
    style.font.size = Pt(10)
    style.font.color.rgb = ICHITA_BLUE_GREY3
    style.paragraph_format.space_after = Pt(5)
    style.paragraph_format.space_before = Pt(2)

    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    if TH_AEONIK_MODE:
        for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
            rFonts.set(qn(attr), font_name)
        scaled_hp = str(round(10 * 2))
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

    # Heading styles
    heading_configs = [
        (1, 22, ICHITA_BLUE_GREY3),
        (2, 15, ICHITA_BLUE_GREY3),
        (3, 12, ICHITA_BLUE),
        (4, 10.5, ICHITA_BLUE),
    ]
    spacing = {1: (20, 8), 2: (16, 6), 3: (12, 5), 4: (8, 4)}
    for level, size, color in heading_configs:
        hs = doc.styles[f'Heading {level}']
        hs.font.name = font_name
        hs.font.size = Pt(size)
        hs.font.color.rgb = color
        hs.font.bold = True
        h_rPr = hs.element.get_or_add_rPr()
        h_rFonts = h_rPr.find(qn('w:rFonts'))
        if h_rFonts is None:
            h_rFonts = OxmlElement('w:rFonts')
            h_rPr.insert(0, h_rFonts)
        if TH_AEONIK_MODE:
            for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
                h_rFonts.set(qn(attr), font_name)
            h_scaled_hp = str(round(size * 2))
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
        before, after = spacing[level]
        hs.paragraph_format.space_before = Pt(before)
        hs.paragraph_format.space_after = Pt(after)

    # List Bullet style
    if 'List Bullet' in doc.styles:
        lb = doc.styles['List Bullet']
        lb.font.name = font_name
        lb.font.size = Pt(10)
        lb.font.color.rgb = ICHITA_BLUE_GREY3

    # Margins
    for section in doc.sections:
        section.top_margin = Cm(margin_cm)
        section.bottom_margin = Cm(margin_cm)
        section.left_margin = Cm(margin_cm)
        section.right_margin = Cm(margin_cm)


# ── Main Conversion ───────────────────────────────────────────────────────────

def convert_html_to_docx(html_path, output_path, logo=None, footer_text=None,
                         font_name=None, no_logo=False, margin=2.5,
                         font_mode="auto"):
    """Convert an HTML file (or '-' for stdin) to an Ichita-branded DOCX.

    Args:
        html_path:   Path to source .html file, or '-' for stdin.
        output_path: Path to write .docx output.
        logo:        Path to logo PNG for header (optional).
        footer_text: Footer text (default: www.ichita.co.th).
        font_name:   Override detected font.
        no_logo:     If True, skip logo in header.
        margin:      Page margin in cm (default 2.5).
        font_mode:   "auto" (Thai in the source -> TH Aeonik), "aeonik",
                     "th-aeonik".
    """
    # Read HTML
    if html_path == '-':
        html_content = sys.stdin.read()
        input_dir = os.getcwd()
    else:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        input_dir = os.path.dirname(os.path.abspath(html_path))

    # Font — chosen from the CONTENT, before any style is built from it. The HTML
    # is scanned as text, so Thai anywhere in it counts: body copy, a table cell,
    # a heading, an alt attribute.
    select_fonts_for_source(html_content, font_mode)
    effective_font = font_name or BRAND_FONT

    # Logo
    if no_logo:
        logo_path = None
    elif logo:
        logo_path = logo
    else:
        logo_path = DEFAULT_LOGO

    # Footer
    if footer_text is None:
        footer_text = "www.ichita.co.th"

    # Build document
    doc = Document()
    _setup_document_styles(doc, effective_font, margin_cm=margin)

    # Parse HTML into document
    parser = IchitaHTMLParser(doc, font_name=effective_font, input_dir=input_dir)
    parser.feed(html_content)

    # Header
    if _HAS_BRANDED_HEADER_FOOTER:
        add_ichita_header(doc, logo_path=logo_path)
        add_ichita_footer(doc)
    else:
        add_ichita_header(doc, logo_path=logo_path)
        # Custom footer text
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _WD
        for section in doc.sections:
            footer = section.footer
            footer.is_linked_to_previous = False
            fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            fp.clear()
            fp.alignment = _WD.RIGHT
            fr = fp.add_run(footer_text)
            fr.font.size = Pt(9)
            fr.font.color.rgb = ICHITA_BLUE_GREY2
            fr.font.name = effective_font

    doc.save(output_path)

    # ── Summary ──
    size = os.path.getsize(output_path)
    para_count = len(doc.paragraphs)
    table_count = len(doc.tables)
    print(f"Saved: {output_path}")
    print(f"  Size: {size:,} bytes ({size / 1024:.1f} KB)")
    print(f"  Paragraphs: {para_count}, Tables: {table_count}")
    print(f"  Headings: {parser.headings_added}, "
          f"Lists: {parser.lists_added}, "
          f"Images: {parser.images_added}")
    if TH_AEONIK_MODE:
        print(f"  Font: {effective_font} (unified Latin+Thai)")
    else:
        print(f"  Font: {effective_font} + {THAI_FONT} (Thai, {THAI_SCALE}x)")
    print(f"  Brand: ICHITA — Separation Technologies")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML to Ichita-branded DOCX.",
        epilog=(
            "Examples:\n"
            "  python3 html_to_docx.py report.html\n"
            "  python3 html_to_docx.py report.html output.docx\n"
            "  python3 html_to_docx.py report.html output.docx --logo logo.png\n"
            "  python3 html_to_docx.py report.html output.docx --no-logo\n"
            "  cat report.html | python3 html_to_docx.py - output.docx\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input",
                        help="Source HTML file (use '-' for stdin)")
    parser.add_argument("output", nargs="?", default=None,
                        help="Output DOCX path (default: <input>.docx)")
    parser.add_argument("--logo", default=None,
                        help="Custom logo image for header (PNG)")
    parser.add_argument("--footer", default=None,
                        help="Footer text (default: www.ichita.co.th)")
    parser.add_argument("--font", default=None,
                        help="Override font name (default: auto-detect TH Aeonik → Aeonik → Calibri)")
    parser.add_argument("--no-logo", action="store_true",
                        help="Skip logo in header")
    parser.add_argument("--font-mode", default="auto",
                        choices=["auto", "aeonik", "th-aeonik"],
                        help="auto (default): any Thai in the source selects "
                             "TH Aeonik, otherwise Aeonik. The choice is printed.")
    parser.add_argument("--margin", type=float, default=2.0,
                        help="Page margin in cm (default: 2.0)")
    args = parser.parse_args()

    # Validate input
    if args.input != '-' and not os.path.exists(args.input):
        print(f"Error: source file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    output = args.output
    if output is None:
        if args.input == '-':
            print("Error: output path required when reading from stdin",
                  file=sys.stderr)
            sys.exit(1)
        output = os.path.splitext(args.input)[0] + ".docx"

    # Warn if logo not found
    if args.logo and not os.path.exists(args.logo):
        print(f"Warning: logo file not found: {args.logo} — will use text fallback",
              file=sys.stderr)

    src_label = args.input if args.input != '-' else '<stdin>'
    print(f"Converting: {os.path.basename(src_label)}")
    print(f"Brand style: ICHITA")

    convert_html_to_docx(
        html_path=args.input,
        output_path=output,
        logo=args.logo,
        footer_text=args.footer,
        font_name=args.font,
        no_logo=args.no_logo,
        margin=args.margin,
        font_mode=args.font_mode,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
