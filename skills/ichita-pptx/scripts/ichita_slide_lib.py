"""
ichita_slide_lib.py — python-pptx companion for the Ichita PPTX skill.

Use this when integrating with existing Python tooling (python-pptx-based
proposal/QA workflows). For new green-field decks, prefer the PptxGenJS
library `ichita-slide-lib.cjs` — it has the full slide catalog (cover,
section, content, kpi, grid, comparison, timeline, closing, etc.).

This Python module covers the proven patterns from production decks:
  * Master/Layout-level backgrounds (the right way — survives content changes)
  * OhYeaH-style title (centered/upper-right, blue accent line below)
  * Numbered cards, two-column cards, scope-style tables
  * Brand constants matching ichita-defaults.md

RULES (from production lessons — DO NOT VIOLATE):
  1. Backgrounds NEVER as per-slide pictures. Always via layout (see
     `create_ichita_presentation` / `set_layout_bg_picture`).
  2. Titles: 32pt Aeonik Bold #263338, blue accent line UNDERNEATH (not beside).
     For long titles (50+ chars) drop to 24pt to fit one line.
  3. Section numbers (01, 02, ...) on slide titles are OPTIONAL — drop them
     when the meeting may skip slides, so customer doesn't see gaps.
  4. Tables for scope/responsibility: bold left column + tint the "what we
     deliver" column (Blue Light #82B0FF on data cells).
  5. Process flow: substantial gray arrows (RIGHT_ARROW shape) between step
     boxes — not thin line connectors.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from lxml import etree


# ─── BRAND CONSTANTS ──────────────────────────────────────────────────────────
COLORS = {
    "blue":           RGBColor(0x29, 0x78, 0xFF),   # primary
    "blue_light":     RGBColor(0x82, 0xB0, 0xFF),
    "blue_grey_01":   RGBColor(0xCF, 0xD9, 0xDB),
    "blue_grey_02":   RGBColor(0x78, 0x8F, 0x9C),
    "blue_grey_03":   RGBColor(0x26, 0x33, 0x38),   # primary dark (titles, dark bg)
    "blue_black":     RGBColor(0x17, 0x1C, 0x21),
    "white":          RGBColor(0xFF, 0xFF, 0xFF),
    "card_bg":        RGBColor(0xEF, 0xF2, 0xF6),   # light grey-blue card fill
    "card_bg_alt":    RGBColor(0xF6, 0xF8, 0xFA),
    "highlight_warm": RGBColor(0xFF, 0xF5, 0xE0),   # for callout boxes
}

FONTS = {
    "heading": "Aeonik",        # all body, headings, labels
    "display": "Betatron",      # display numerals only — single-digit max
    "fallback": "Calibri",
}

SIZES = {
    "slide_title":     32,
    "slide_title_long": 24,     # for titles > ~50 chars
    "section_header":  20,
    "card_title":      14,
    "body":            12,
    "small":           10,
    "stat_value":      32,
    "stat_label":      12,
}

# 16:9 widescreen — matches Ichita brand assets (frame, dark bg)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Layout indices in the default python-pptx Office Theme
CONTENT_LAYOUT = 6   # Blank — apply frame BG here
DARK_LAYOUT    = 5   # Title Only — apply dark BG here


# ─── ASSET PATHS (resolve from repo root) ─────────────────────────────────────
def get_asset_path(name):
    """Resolve an asset path inside the ichita-skills repo.

    `name` is one of: "frame", "dark_bg", "logo_dark", "logo_white".
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.normpath(os.path.join(here, "..", "..", ".."))
    mapping = {
        "frame":      "assets/brand/ichita-content-frame.png",
        "dark_bg":    "assets/brand/ichita-dark-bg.jpg",
        "logo_dark":  "assets/logos/ichita-wordmark-dark-on-white.png",
        "logo_white": "assets/logos/ichita-wordmark-white-on-dark.png",
    }
    return os.path.join(repo_root, mapping[name])


# ─── MASTER / LAYOUT BACKGROUNDS ──────────────────────────────────────────────
def _build_blipfill_bg(rId):
    xml = (
        '<p:bg xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:bgPr><a:blipFill dpi="0" rotWithShape="1">'
        f'<a:blip r:embed="{rId}"/>'
        '<a:srcRect/><a:stretch><a:fillRect/></a:stretch>'
        '</a:blipFill><a:effectLst/></p:bgPr></p:bg>'
    )
    return etree.fromstring(xml)


def set_layout_bg_picture(layout, image_path):
    """Apply a stretched picture as the background of a slide LAYOUT.

    All slides that use this layout inherit the background — no per-slide
    BG management. Survives content changes (add/remove/reorder slides).
    THIS is the correct way to set Ichita brand backgrounds.
    """
    package = layout.part.package
    image_part = package.get_or_add_image_part(image_path)
    rId = layout.part.relate_to(image_part, RT.IMAGE)

    cSld = layout._element.find(qn('p:cSld'))
    existing_bg = cSld.find(qn('p:bg'))
    if existing_bg is not None:
        cSld.remove(existing_bg)
    cSld.insert(0, _build_blipfill_bg(rId))


def set_slide_bg_picture(slide, image_path):
    """Override a single slide's background. Prefer set_layout_bg_picture()."""
    package = slide.part.package
    image_part = package.get_or_add_image_part(image_path)
    rId = slide.part.relate_to(image_part, RT.IMAGE)

    cSld = slide._element.find(qn('p:cSld'))
    existing_bg = cSld.find(qn('p:bg'))
    if existing_bg is not None:
        cSld.remove(existing_bg)
    cSld.insert(0, _build_blipfill_bg(rId))


def create_ichita_presentation(frame_bg_path=None, dark_bg_path=None):
    """Create a 16:9 Ichita-themed presentation with master-level backgrounds.

    Defaults pull from this skill's asset folder. Pass None to skip a BG.

    Returns the Presentation object. Use:
        prs.slide_layouts[CONTENT_LAYOUT]  # frame BG, for content
        prs.slide_layouts[DARK_LAYOUT]     # dark BG, for cover/closing
    """
    if frame_bg_path is None:
        frame_bg_path = get_asset_path("frame")
    if dark_bg_path is None:
        dark_bg_path = get_asset_path("dark_bg")

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    if frame_bg_path and os.path.exists(frame_bg_path):
        set_layout_bg_picture(prs.slide_layouts[CONTENT_LAYOUT], frame_bg_path)
    if dark_bg_path and os.path.exists(dark_bg_path):
        set_layout_bg_picture(prs.slide_layouts[DARK_LAYOUT], dark_bg_path)

    return prs


# ─── PRIMITIVES ───────────────────────────────────────────────────────────────
def add_rect(slide, x, y, w, h, fill, line=None, line_width=0.75):
    """Filled rectangle, no shadow."""
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_width)
    s.shadow.inherit = False
    return s


def add_rounded_rect(slide, x, y, w, h, fill, line=None, corner=0.04,
                     line_width=0.75):
    """Filled rounded rectangle, no shadow."""
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.adjustments[0] = corner
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_width)
    s.shadow.inherit = False
    return s


def _force_align(p, align):
    """Force paragraph alignment via XML (PP_ALIGN sometimes inherits theme)."""
    code = {PP_ALIGN.LEFT: "l", PP_ALIGN.RIGHT: "r",
            PP_ALIGN.CENTER: "ctr"}.get(align, "l")
    pPr = p._pPr if p._pPr is not None else p._p.get_or_add_pPr()
    pPr.set("algn", code)


def add_text(slide, x, y, w, h, text, *, size=14, color=None, bold=False,
             italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             font=None, margin=0.05):
    """Add a single-paragraph textbox with full styling control."""
    if color is None:
        color = COLORS["blue_grey_03"]
    if font is None:
        font = FONTS["heading"]
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    _force_align(p, align)
    return tb


def add_rich_text(slide, x, y, w, h, paragraphs, *, anchor=MSO_ANCHOR.TOP,
                  align=PP_ALIGN.LEFT, margin=0.08):
    """Multi-paragraph textbox. Each paragraph is a dict with optional `runs`
    for inline-styled segments, or flat text/size/color/bold/italic keys.

    paragraph = {
        text: str,                # used if no `runs` key
        runs: [{text, size?, color?, bold?, italic?}, ...],  # rich inline
        size, color, bold, italic, align, space_after, space_before  # paragraph defaults
    }
    """
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin); tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = anchor
    for i, item in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p_align = item.get("align", align)
        p.alignment = p_align
        p.space_after = Pt(item.get("space_after", 4))
        p.space_before = Pt(item.get("space_before", 0))
        runs = item.get("runs")
        if runs is None:
            runs = [{k: v for k, v in item.items()
                     if k in ("text", "size", "color", "bold", "italic", "font")}]
        for run_spec in runs:
            r = p.add_run()
            r.text = run_spec.get("text", "")
            r.font.name = run_spec.get("font", FONTS["heading"])
            r.font.size = Pt(run_spec.get("size", 12))
            r.font.color.rgb = run_spec.get("color", COLORS["blue_grey_03"])
            r.font.bold = run_spec.get("bold", False)
            r.font.italic = run_spec.get("italic", False)
        _force_align(p, p_align)
    return tb


# ─── OHYEAH TITLE STYLE ───────────────────────────────────────────────────────
def add_slide_title(slide, title_text, *, section_num=None, size=None):
    """OhYeaH's proven title style for Ichita content slides:
    32pt Aeonik Bold Blue Grey 03, positioned to the right of the frame's
    top-left ICHITA notch, with a thin Ichita Blue accent line below.

    Parameters
    ----------
    title_text : str
        Title for the slide.
    section_num : str | None
        Optional "01" / "02" / ... prefix. OMIT when the meeting may skip
        slides (customer would see gaps).
    size : int | None
        Override font size. Defaults to 32pt for short titles, drops to 24pt
        if title text is longer than ~45 chars.
    """
    if size is None:
        size = SIZES["slide_title_long"] if len(title_text) > 45 \
               else SIZES["slide_title"]

    tb = slide.shapes.add_textbox(Inches(4.14), Inches(0.30),
                                  Inches(9.0), Inches(0.70))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.0); tf.margin_right = Inches(0.0)
    tf.margin_top = Inches(0.0); tf.margin_bottom = Inches(0.0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    if section_num:
        r1 = p.add_run(); r1.text = f"{section_num}   "
        r1.font.name = FONTS["heading"]; r1.font.size = Pt(size)
        r1.font.bold = True; r1.font.color.rgb = COLORS["blue"]
    r2 = p.add_run(); r2.text = title_text
    r2.font.name = FONTS["heading"]; r2.font.size = Pt(size)
    r2.font.bold = True; r2.font.color.rgb = COLORS["blue_grey_03"]
    _force_align(p, PP_ALIGN.LEFT)
    # Blue underline (matches OhYeaH's SMS R2 deck dimensions)
    add_rect(slide, Inches(3.80), Inches(1.05), Inches(8.47),
             Inches(0.05), COLORS["blue"])


# ─── SLIDE FACTORIES ──────────────────────────────────────────────────────────
def add_content_slide(prs, title, *, section_num=None):
    """Add a content slide (frame BG inherited from layout) with title."""
    slide = prs.slides.add_slide(prs.slide_layouts[CONTENT_LAYOUT])
    add_slide_title(slide, title, section_num=section_num)
    return slide


def add_dark_slide(prs):
    """Add a dark slide (dark BG inherited from layout) for cover/closing.
    Returns the slide without a title — caller positions text freely.
    """
    return prs.slides.add_slide(prs.slide_layouts[DARK_LAYOUT])


# ─── BLOCK COMPONENTS ─────────────────────────────────────────────────────────
def numbered_card(slide, x, y, w, h, num, title, body_runs, *,
                  accent=None, highlight=False):
    """Card with numbered colored tag + bold title + rich body text.

    body_runs = list of run dicts: [{text, bold?, italic?, color?, size?}]
    accent: tag fill color (defaults to Ichita Blue). For "fine print" cards,
            pass `COLORS["blue_grey_02"]` to indicate lower emphasis.
    highlight: True for the most important card on the slide — adds warm
               yellow tint + Ichita Blue border.
    """
    if accent is None:
        accent = COLORS["blue"]
    bg = COLORS["highlight_warm"] if highlight else COLORS["card_bg"]
    border = COLORS["blue"] if highlight else COLORS["blue_grey_01"]
    add_rect(slide, x, y, w, h, bg, line=border)
    # Number tag
    tag_w = Inches(0.55); tag_h = Inches(0.55)
    add_rect(slide, x + Inches(0.18), y + Inches(0.18), tag_w, tag_h, accent)
    add_text(slide, x + Inches(0.18), y + Inches(0.18), tag_w, tag_h,
             num, size=18, bold=True, color=COLORS["white"],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0.0)
    # Card title
    add_text(slide, x + Inches(0.88), y + Inches(0.22), w - Inches(1.05),
             Inches(0.40), title, size=SIZES["card_title"], bold=True,
             color=COLORS["blue_grey_03"])
    # Card body — single paragraph with rich runs
    tb = slide.shapes.add_textbox(x + Inches(0.30), y + Inches(0.85),
                                  w - Inches(0.5), h - Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.0); tf.margin_right = Inches(0.0)
    tf.margin_top = Inches(0.0); tf.margin_bottom = Inches(0.0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for spec in body_runs:
        r = p.add_run()
        r.text = spec["text"]
        r.font.name = FONTS["heading"]
        r.font.size = Pt(spec.get("size", 11))
        r.font.color.rgb = spec.get("color", COLORS["blue_grey_03"])
        r.font.bold = spec.get("bold", False)
        r.font.italic = spec.get("italic", False)
    _force_align(p, PP_ALIGN.LEFT)


def scope_table(slide, x, y, w, h, headers, rows, *,
                ichita_col=1, highlight_col_fill=None):
    """Two-/three-column scope table with Ichita emphasis rules:
    - Header row: dark fill, white text
    - Left (category) column: BOLD
    - "ICHITA Supplies" column (index `ichita_col`): tinted Blue Light fill
    - Other columns: plain alternating row

    headers : list[str]
    rows    : list[list[str]]
    """
    if highlight_col_fill is None:
        highlight_col_fill = COLORS["blue_light"]
    rows_count = len(rows) + 1
    cols_count = len(headers)
    tshape = slide.shapes.add_table(rows_count, cols_count, x, y, w, h)
    tbl = tshape.table

    def _cell(cell, text, *, size=12, bold=False, color=None, fill=None,
              align=PP_ALIGN.LEFT):
        if color is None:
            color = COLORS["blue_grey_03"]
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run(); r.text = text
        r.font.name = FONTS["heading"]; r.font.size = Pt(size)
        r.font.bold = bold; r.font.color.rgb = color
        cell.text_frame.word_wrap = True
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.12)
        cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
        if fill is not None:
            cell.fill.solid(); cell.fill.fore_color.rgb = fill

    # Header row
    for j, h_text in enumerate(headers):
        _cell(tbl.cell(0, j), h_text, size=13, bold=True,
              color=COLORS["white"], fill=COLORS["blue_grey_03"])
    # Data rows
    for i, row in enumerate(rows):
        alt = COLORS["card_bg_alt"] if i % 2 == 0 else COLORS["white"]
        for j, val in enumerate(row):
            if j == ichita_col:
                _cell(tbl.cell(i+1, j), val, size=12, bold=True,
                      fill=highlight_col_fill,
                      color=COLORS["blue_grey_03"])
            else:
                _cell(tbl.cell(i+1, j), val, size=12,
                      bold=(j == 0),
                      fill=alt, color=COLORS["blue_grey_03"])
    return tbl


def process_flow_arrows(slide, steps, *, x_start=Inches(0.6),
                        y=Inches(1.35), step_w=Inches(1.95),
                        step_h=Inches(1.5), gap=Inches(0.07),
                        step_colors=None):
    """Numbered process boxes connected by substantial gray arrows.

    steps = list of (number_str, line1_str, line2_str) tuples
    step_colors = list of RGBColor (one per step), defaults to blue/light/grey
    """
    if step_colors is None:
        cyc = [COLORS["blue"], COLORS["blue_light"], COLORS["blue_grey_02"]]
        step_colors = [cyc[i % 3] for i in range(len(steps))]
    for i, (num, l1, l2) in enumerate(steps):
        x = x_start + i * (step_w + gap)
        color = step_colors[i]
        text_col = COLORS["white"] if color != COLORS["blue_light"] \
                   else COLORS["blue_grey_03"]
        add_rect(slide, x, y, step_w, step_h, color)
        add_text(slide, x, y + Inches(0.18), step_w, Inches(0.6),
                 num, size=30, bold=True, color=text_col,
                 align=PP_ALIGN.CENTER)
        add_rich_text(slide, x, y + Inches(0.78), step_w, Inches(0.7), [
            {"text": l1, "size": 13, "color": text_col,
             "align": PP_ALIGN.CENTER, "space_after": 1},
            {"text": l2, "size": 13, "color": text_col,
             "align": PP_ALIGN.CENTER},
        ])
        if i < len(steps) - 1:
            ar = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                x + step_w, y + step_h/2 - Inches(0.14),
                gap, Inches(0.28))
            ar.fill.solid()
            ar.fill.fore_color.rgb = COLORS["blue_grey_02"]
            ar.line.fill.background()
            ar.shadow.inherit = False


# ─── EXPORT ALL ───────────────────────────────────────────────────────────────
__all__ = [
    # Constants
    "COLORS", "FONTS", "SIZES", "SLIDE_W", "SLIDE_H",
    "CONTENT_LAYOUT", "DARK_LAYOUT",
    # Asset helpers
    "get_asset_path",
    # Presentation factory
    "create_ichita_presentation",
    # Background helpers
    "set_layout_bg_picture", "set_slide_bg_picture",
    # Primitives
    "add_rect", "add_rounded_rect", "add_text", "add_rich_text",
    # Slide factories
    "add_content_slide", "add_dark_slide",
    # Title + blocks
    "add_slide_title", "numbered_card", "scope_table",
    "process_flow_arrows",
]
