"""
ichita_slide_lib.py — python-pptx companion for the Ichita PPTX skill.
Template-aware edition: open OhYeaH's reference Powerpoint Template.pptx
as the base and add slides via its real slide layouts, inheriting the master
BG (content-frame chrome image1.png) from the slide master.

Cover slides use the Title Slide layout + a full-slide picture overlay (dark
bg image2.jpeg) drawn exactly as the template author did in the original
three sample slides.

RULES (from production lessons — DO NOT VIOLATE):
  1. Backgrounds NEVER as per-slide pictures EXCEPT the cover dark overlay.
     Master BG (content-frame chrome) is inherited from slide master — never
     replicate it on individual slides.
  2. Titles: Aeonik Bold #263338, blue accent line UNDERNEATH.
     Positioned at x=2.7" to clear the logo notch. Long titles (>45 chars)
     drop to 24pt. The title zone is y=0.20..0.90; blue line at y=0.92.
  3. Content area starts at y=1.40 (below title+line). Ends at y=6.70
     (above bottom chrome chamfer). insightBar sits at y≈6.50.
  4. Tables: dark header, alternating rows, bold left column, tinted
     "Ichita Supplies" column.
  5. Process flow: substantial gray RIGHT_ARROW shapes between step boxes.
  6. Stat values (multi-digit, values-with-units): Aeonik Bold NOT Betatron.
"""

import io
import os

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt


# ─── BRAND CONSTANTS ──────────────────────────────────────────────────────────
SLIDE_W = 13.333   # inches, widescreen 16:9
SLIDE_H = 7.5      # inches

ICHITA_DARK   = RGBColor(0x26, 0x33, 0x38)
ICHITA_BLUE   = RGBColor(0x29, 0x78, 0xFF)
ICHITA_GREY   = RGBColor(0x78, 0x8F, 0x9C)
ICHITA_GREY01 = RGBColor(0xCF, 0xD9, 0xDB)
OFF_WHITE     = RGBColor(0xF8, 0xFA, 0xFB)
WHITE         = RGBColor(0xFF, 0xFF, 0xFF)
CARD_BG       = RGBColor(0xEF, 0xF2, 0xF6)
CARD_BG_ALT   = RGBColor(0xF6, 0xF8, 0xFA)
HIGHLIGHT_WARM = RGBColor(0xFF, 0xF5, 0xE0)
BLUE_LIGHT    = RGBColor(0x82, 0xB0, 0xFF)

FONT_AEONIK   = "Aeonik"
FONT_AEONIK_TH = "TH Aeonik"
FONT_BETATRON = "Betatron"   # single-digit hero ONLY

# Alias dict for old-style code
COLORS = {
    "blue":           ICHITA_BLUE,
    "blue_light":     BLUE_LIGHT,
    "blue_grey_01":   ICHITA_GREY01,
    "blue_grey_02":   ICHITA_GREY,
    "blue_grey_03":   ICHITA_DARK,
    "white":          WHITE,
    "card_bg":        CARD_BG,
    "card_bg_alt":    CARD_BG_ALT,
    "highlight_warm": HIGHLIGHT_WARM,
}
FONTS = {"heading": FONT_AEONIK, "display": FONT_BETATRON, "fallback": "Calibri"}
SIZES = {
    "slide_title": 32, "slide_title_long": 24,
    "section_header": 20, "card_title": 14,
    "body": 12, "small": 10,
    "stat_value": 32, "stat_label": 12,
}

# Safe content zone (inside the chrome card, below title+line, above footer)
CONTENT_AREA = {"x": 0.92, "y": 1.40, "w": 11.50, "h": 5.30}

# Layout names → indices in the reference template
_LAYOUT_NAMES = {
    "Title Slide": 0,
    "Title and Content": 1,
    "Section Header": 2,
    "Two Content": 3,
    "Comparison": 4,
    "Title Only": 5,
    "Blank": 6,
}


# ─── TEMPLATE FACTORY ─────────────────────────────────────────────────────────
def create_from_template(template_path: str) -> tuple:
    """Open OhYeaH's reference template, delete all sample slides, and return
    a clean (Presentation, dark_blob) tuple ready for building.

    The slide master already carries the Ichita content-frame chrome as its
    blipFill background; every new slide inherits it automatically — no per-
    slide image work required.

    The dark cover JPEG (image2.jpeg in the template) is only referenced from
    the sample slides. We extract its bytes BEFORE deleting those slides so
    that add_cover() can re-embed it on new cover slides.

    Parameters
    ----------
    template_path : str
        Absolute path to "Powerpoint Template.pptx".

    Returns
    -------
    (Presentation, bytes | None)
        prs   — zero slides; master BG intact; all standard layouts available.
        blob  — raw bytes of the dark-cover JPEG, or None if not found.

    Example
    -------
        prs, dark_blob = create_from_template(TEMPLATE_PATH)
        add_cover(prs, "Title", _dark_blob=dark_blob)
    """
    prs = Presentation(template_path)

    # Verify canvas matches expected 16:9 dimensions
    assert abs(prs.slide_width.inches - SLIDE_W) < 0.01, \
        f"Template width mismatch: {prs.slide_width.inches}"
    assert abs(prs.slide_height.inches - SLIDE_H) < 0.01, \
        f"Template height mismatch: {prs.slide_height.inches}"

    # Extract dark-cover JPEG BEFORE deleting slides (it becomes orphaned after)
    # image2.jpeg (~40 kB) is the dark bg; image1.png (~20 kB) is the chrome
    dark_blob = None
    for part in prs.part.package.iter_parts():
        ct = getattr(part, "content_type", "")
        if ("jpeg" in ct or "jpg" in ct) and len(part.blob) > 30000:
            dark_blob = part.blob
            break

    # Delete all sample slides (reverse order to keep indices stable)
    # The r:id attribute uses the full relationship namespace URI, not "r:id"
    _R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    xml_slides = prs.slides._sldIdLst
    slide_ids = list(xml_slides)
    for sld_id in reversed(slide_ids):
        rId = sld_id.get(_R_ID)
        prs.part.drop_rel(rId)
        xml_slides.remove(sld_id)

    assert len(prs.slides) == 0, "Failed to clear template slides"
    return prs, dark_blob


def _get_layout(prs: Presentation, name: str):
    """Return a slide layout by its name string."""
    for lay in prs.slide_layouts:
        if lay.name == name:
            return lay
    raise ValueError(f"Layout '{name}' not found in presentation.")


def _dark_cover_blob(prs: Presentation) -> bytes | None:
    """DEPRECATED: use create_from_template() which now returns the blob directly.

    Kept for backwards compatibility. After sample slides are deleted, the
    JPEG is no longer reachable via iter_parts(), so this will return None
    on a post-deletion Presentation. Call it BEFORE deleting slides, or use
    the (prs, dark_blob) return value from create_from_template().
    """
    for part in prs.part.package.iter_parts():
        ct = getattr(part, "content_type", "")
        if "jpeg" in ct or "jpg" in ct:
            blob = part.blob
            if len(blob) > 30000:
                return blob
    return None


# ─── PRIMITIVES ───────────────────────────────────────────────────────────────
def _force_align(p, align):
    code = {PP_ALIGN.LEFT: "l", PP_ALIGN.RIGHT: "r",
            PP_ALIGN.CENTER: "ctr"}.get(align, "l")
    pPr = p._pPr if p._pPr is not None else p._p.get_or_add_pPr()
    pPr.set("algn", code)


def add_rect(slide, x, y, w, h, fill, line=None, line_width=0.75):
    """Filled rectangle, no shadow. x/y/w/h in inches."""
    s = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
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
    """Filled rounded rectangle, no shadow. x/y/w/h in inches."""
    s = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
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


def add_text(slide, x, y, w, h, text, *, size=14, color=None, bold=False,
             italic=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             font=None, margin=0.05):
    """Add a single-paragraph textbox. x/y/w/h in inches."""
    if color is None:
        color = ICHITA_DARK
    if font is None:
        font = FONT_AEONIK
    tb = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h))
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
    """Multi-paragraph textbox. x/y/w/h in inches.

    Each item in `paragraphs` is a dict:
        text, size?, color?, bold?, italic?, font?,
        align?, space_after?, space_before?,
        runs?: [{text, size?, color?, bold?, italic?, font?}, ...]
    """
    tb = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h))
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
            r.font.name = run_spec.get("font", FONT_AEONIK)
            r.font.size = Pt(run_spec.get("size", 12))
            r.font.color.rgb = run_spec.get("color", ICHITA_DARK)
            r.font.bold = run_spec.get("bold", False)
            r.font.italic = run_spec.get("italic", False)
        _force_align(p, p_align)
    return tb


# ─── TITLE HELPER ─────────────────────────────────────────────────────────────
def _add_title(slide, title_text, *, size=None):
    """Place the Ichita-style title on a slide.

    Positioned at x=2.7" to clear the top-left logo notch. Blue accent
    underline at y=0.92". Long titles (>45 chars) auto-scale to 24pt.
    """
    if size is None:
        size = 24 if len(title_text) > 45 else 32
    tb = slide.shapes.add_textbox(
        Inches(2.7), Inches(0.20), Inches(10.0), Inches(0.70))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.0); tf.margin_right = Inches(0.0)
    tf.margin_top = Inches(0.0); tf.margin_bottom = Inches(0.0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = title_text
    r.font.name = FONT_AEONIK
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = ICHITA_DARK
    _force_align(p, PP_ALIGN.LEFT)
    # Blue underline
    add_rect(slide, 2.7, 0.92, 10.0, 0.05, ICHITA_BLUE)
    return tb


# ─── SLIDE FACTORIES ──────────────────────────────────────────────────────────
def add_cover(prs: Presentation, title: str,
              subtitle: str = None, date: str = None,
              _dark_blob: bytes = None) -> object:
    """Add a cover slide using the Title Slide layout.

    The dark background (ICHITA wordmark cover image) is embedded as a
    full-slide picture shape placed BEFORE the text, matching the template
    author's approach on the original sample slides.

    Parameters
    ----------
    prs : Presentation
    title : str
    subtitle : str | None
    date : str | None
    _dark_blob : bytes | None
        Pass the dark-cover JPEG blob (extracted once via
        _dark_cover_blob()). If None, the cover will inherit the chrome BG
        from the master (light style).

    Returns
    -------
    slide
    """
    layout = _get_layout(prs, "Title Slide")
    slide = prs.slides.add_slide(layout)

    # Remove inherited placeholder shapes so we control all text ourselves
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    # Dark BG overlay as full-slide picture (matches template approach)
    if _dark_blob is not None:
        img_stream = io.BytesIO(_dark_blob)
        pic = slide.shapes.add_picture(
            img_stream, Inches(0), Inches(0),
            Inches(SLIDE_W), Inches(SLIDE_H))
        # Send it to the back
        slide.shapes._spTree.remove(pic._element)
        slide.shapes._spTree.insert(2, pic._element)

    # Title — center of slide, large, white
    title_size = 36 if len(title) <= 50 else 28
    add_text(slide, 1.0, 2.8, 11.33, 1.2, title,
             size=title_size, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
             font=FONT_AEONIK, margin=0.0)

    if subtitle:
        add_text(slide, 1.0, 4.1, 11.33, 0.60, subtitle,
                 size=14, color=ICHITA_GREY01,
                 align=PP_ALIGN.CENTER, font=FONT_AEONIK, margin=0.0)
    if date:
        add_text(slide, 1.0, 4.75, 11.33, 0.45, date,
                 size=11, color=ICHITA_GREY, italic=True,
                 align=PP_ALIGN.CENTER, font=FONT_AEONIK, margin=0.0)
    return slide


def add_content(prs: Presentation, title: str) -> object:
    """Add a content slide with the title styled to Ichita brand.

    Uses the 'Title and Content' layout so master BG is inherited. The body
    content placeholder is removed — callers add custom shapes into the
    white card area defined by CONTENT_AREA.

    Returns the slide; add shapes to it freely.
    """
    layout = _get_layout(prs, "Title and Content")
    slide = prs.slides.add_slide(layout)

    # Clear all placeholders (title + content) — we place everything manually
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    _add_title(slide, title)
    return slide


def add_two_column(prs: Presentation, title: str,
                   left_fn, right_fn) -> object:
    """Add a two-column content slide.

    Uses 'Two Content' layout. Calls left_fn(slide, zone) and right_fn(slide,
    zone) where zone = {x, y, w, h} in inches for each column.

    Column zones match the layout's native placeholder positions:
      left:  x=0.92, y=1.40, w=5.67, h=5.30
      right: x=6.75, y=1.40, w=5.67, h=5.30
    """
    layout = _get_layout(prs, "Two Content")
    slide = prs.slides.add_slide(layout)
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    _add_title(slide, title)

    left_zone  = {"x": 0.92, "y": 1.40, "w": 5.67, "h": 5.30}
    right_zone = {"x": 6.75, "y": 1.40, "w": 5.67, "h": 5.30}

    if left_fn:
        left_fn(slide, left_zone)
    if right_fn:
        right_fn(slide, right_zone)
    return slide


def add_comparison(prs: Presentation, title: str,
                   left_label: str, right_label: str,
                   left_fn, right_fn) -> object:
    """Add a comparison (two-column with header labels) slide.

    Uses 'Comparison' layout. Column label headers are placed at y=1.40
    (~0.35" tall), then content zone starts at y=1.80.

    Content zones (passed to callbacks):
      left:  x=0.92, y=1.80, w=5.64, h=4.80
      right: x=6.75, y=1.80, w=5.67, h=4.80
    """
    layout = _get_layout(prs, "Comparison")
    slide = prs.slides.add_slide(layout)
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    _add_title(slide, title)

    # Column header labels
    for lbl, col_x, col_w in [
        (left_label,  0.92, 5.64),
        (right_label, 6.75, 5.67),
    ]:
        hdr = add_rect(slide, col_x, 1.40, col_w, 0.35, ICHITA_DARK)
        add_text(slide, col_x + 0.10, 1.40, col_w - 0.20, 0.35,
                 lbl, size=13, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                 font=FONT_AEONIK, margin=0.0)

    left_zone  = {"x": 0.92, "y": 1.80, "w": 5.64, "h": 4.80}
    right_zone = {"x": 6.75, "y": 1.80, "w": 5.67, "h": 4.80}

    if left_fn:
        left_fn(slide, left_zone)
    if right_fn:
        right_fn(slide, right_zone)
    return slide


def add_grid(prs: Presentation, title: str,
             cols: int, cards: list) -> object:
    """Add a grid-of-cards slide using 'Title Only' layout.

    Parameters
    ----------
    cols : int
        Number of columns (2 or 3).
    cards : list of (header, subheader, body) tuples.
        - header: bold card title (str)
        - subheader: smaller subtitle or standard name (str or None)
        - body: description text (str)

    Layout math (3-col example):
        Content area: x=0.92, y=1.40, w=11.50, h=5.20
        card_w = (11.50 - (cols-1)*0.20) / cols
        card_h = split evenly for rows
    """
    layout = _get_layout(prs, "Title Only")
    slide = prs.slides.add_slide(layout)
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)

    _add_title(slide, title)

    rows = (len(cards) + cols - 1) // cols
    gap = 0.18   # gap between cards in inches
    total_w = 11.50
    total_h = 5.10
    card_w = (total_w - gap * (cols - 1)) / cols
    card_h = (total_h - gap * (rows - 1)) / rows
    x0 = 0.92
    y0 = 1.45

    for idx, card in enumerate(cards):
        row = idx // cols
        col = idx % cols
        cx = x0 + col * (card_w + gap)
        cy = y0 + row * (card_h + gap)

        header, subheader, body = card[0], card[1] if len(card) > 2 else None, card[-1]

        # Card background
        add_rounded_rect(slide, cx, cy, card_w, card_h, CARD_BG,
                         line=ICHITA_GREY01, corner=0.03)

        # Blue accent bar at card top
        add_rect(slide, cx, cy, card_w, 0.06, ICHITA_BLUE)

        # Header text
        add_text(slide, cx + 0.15, cy + 0.12, card_w - 0.30, 0.40,
                 header, size=13, bold=True, color=ICHITA_DARK,
                 font=FONT_AEONIK)

        # Subheader (standard / spec label)
        text_y = cy + 0.55
        if subheader:
            add_text(slide, cx + 0.15, text_y, card_w - 0.30, 0.30,
                     subheader, size=10, color=ICHITA_BLUE, bold=False,
                     italic=True, font=FONT_AEONIK)
            text_y += 0.30

        # Body text
        body_h = cy + card_h - 0.10 - text_y
        if body_h > 0.20:
            add_text(slide, cx + 0.15, text_y, card_w - 0.30, body_h,
                     body, size=11, color=ICHITA_GREY,
                     font=FONT_AEONIK)

    return slide


def add_closing(prs: Presentation, title: str,
                subtitle: str = None,
                _dark_blob: bytes = None) -> object:
    """Add a closing slide. Mirrors add_cover styling."""
    return add_cover(prs, title, subtitle=subtitle, _dark_blob=_dark_blob)


# ─── BLOCK COMPONENTS ─────────────────────────────────────────────────────────
def feature_list(slide, items, x, y, w, h,
                 dot_color=None):
    """Render a feature list: colored dot + bold title + description.

    Parameters
    ----------
    items : list of (title, description) tuples.
    x, y, w, h : float (inches) — bounding box for the whole list.
    dot_color : RGBColor | None — defaults to ICHITA_BLUE.

    Items are spaced evenly within the bounding box. Returns nothing.
    """
    if dot_color is None:
        dot_color = ICHITA_BLUE

    n = len(items)
    if n == 0:
        return

    item_h = h / n
    dot_r  = 0.10   # dot radius approximation (drawn as small square)
    label_x = x + 0.25
    label_w = w - 0.30

    for i, item in enumerate(items):
        # Support both 2-tuple (title, desc) and 1-tuple / plain str
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            ftitle, fdesc = item[0], item[1]
        else:
            ftitle = str(item)
            fdesc = ""

        iy = y + i * item_h

        # Dot
        add_rect(slide, x + 0.05, iy + 0.13, dot_r, dot_r, dot_color)

        # Title + desc as rich text paragraphs
        paras = [
            {"text": ftitle, "size": 13, "bold": True,
             "color": ICHITA_DARK, "space_after": 1},
        ]
        if fdesc:
            paras.append(
                {"text": fdesc, "size": 11, "bold": False,
                 "color": ICHITA_GREY, "space_after": 2}
            )
        add_rich_text(slide, label_x, iy + 0.04, label_w,
                      item_h - 0.06, paras, margin=0.0)


def insight_bar(slide, text, y=None):
    """Bottom-of-slide insight strip: thin blue accent line + italic text.

    Parameters
    ----------
    text : str
    y : float | None — top of the bar in inches; defaults to 6.38 which
        places the bar just above the template's bottom chrome chamfer.
    """
    if y is None:
        y = 6.38
    bar_h = 0.52
    # Thin blue accent line
    add_rect(slide, 0.92, y, 11.50, 0.04, ICHITA_BLUE)
    # Background strip (subtle)
    add_rect(slide, 0.92, y + 0.04, 11.50, bar_h - 0.04, CARD_BG)
    # Text
    add_text(slide, 1.0, y + 0.06, 11.30, bar_h - 0.10,
             text, size=11, color=ICHITA_GREY, italic=True,
             font=FONT_AEONIK, anchor=MSO_ANCHOR.MIDDLE)


def process_flow(slide, steps, x, y, w, h=0.70, color=None):
    """Horizontal process-flow boxes connected by substantial gray arrows.

    Parameters
    ----------
    steps : list of str — label for each box.
    x, y, w, h : float (inches) — bounding box for the whole flow.
    color : RGBColor | None — box fill color; defaults to ICHITA_BLUE.
    """
    if color is None:
        color = ICHITA_BLUE
    n = len(steps)
    if n == 0:
        return
    arrow_w = 0.22
    box_w = (w - arrow_w * (n - 1)) / n

    for i, label in enumerate(steps):
        bx = x + i * (box_w + arrow_w)
        # Box
        add_rounded_rect(slide, bx, y, box_w, h, color,
                         line=None, corner=0.08)
        # Label
        add_text(slide, bx, y, box_w, h, label,
                 size=11, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                 font=FONT_AEONIK, margin=0.02)
        # Arrow
        if i < n - 1:
            ar = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                Inches(bx + box_w), Inches(y + h / 2 - 0.13),
                Inches(arrow_w), Inches(0.26))
            ar.fill.solid()
            ar.fill.fore_color.rgb = ICHITA_GREY
            ar.line.fill.background()
            ar.shadow.inherit = False


def table_branded(slide, headers, rows, x, y, w, h, col_widths=None):
    """Ichita-branded data table.

    Dark header row + alternating body rows. Numbers right-aligned,
    text left-aligned. Headers and left column bold.

    Parameters
    ----------
    headers : list[str]
    rows    : list[list[str]]
    col_widths : list[float] | None
        Fractions summing to 1.0. If None, equal distribution.
    """
    n_cols = len(headers)
    n_rows = len(rows) + 1

    tshape = slide.shapes.add_table(
        n_rows, n_cols,
        Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = tshape.table

    # Set column widths
    if col_widths:
        total = sum(col_widths)
        for j, frac in enumerate(col_widths):
            tbl.columns[j].width = Inches(w * frac / total)

    def _cell(cell, text, *, size=12, bold=False, color=None,
               fill=None, align=PP_ALIGN.LEFT):
        if color is None:
            color = ICHITA_DARK
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = text
        r.font.name = FONT_AEONIK
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        cell.text_frame.word_wrap = True
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.10)
        cell.margin_right = Inches(0.10)
        cell.margin_top = Inches(0.04)
        cell.margin_bottom = Inches(0.04)
        if fill is not None:
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill

    # Header row
    for j, h_text in enumerate(headers):
        _cell(tbl.cell(0, j), h_text, size=12, bold=True,
              color=WHITE, fill=ICHITA_DARK)

    # Data rows
    for i, row in enumerate(rows):
        alt = CARD_BG_ALT if i % 2 == 0 else WHITE
        for j, val in enumerate(row):
            # Numbers right-aligned (heuristic: if not first col, check if numeric)
            is_numeric = j > 0 and val and val[0] in "0123456789≤≥~<>-+"
            a = PP_ALIGN.RIGHT if is_numeric else PP_ALIGN.LEFT
            _cell(tbl.cell(i + 1, j), str(val), size=11,
                  bold=(j == 0), fill=alt, align=a)

    return tbl


def stat_card(slide, value, label, x, y, w, h):
    """Stat card with large Aeonik Bold value and a label underneath.

    NOTE: Use Aeonik Bold for ALL stat values (including multi-digit and
    values-with-units). Betatron is ONLY for genuinely single-digit heroes —
    and even then only ~5 instances per deck maximum.
    """
    add_rounded_rect(slide, x, y, w, h, CARD_BG,
                     line=ICHITA_GREY01, corner=0.05)
    add_rect(slide, x, y, w, 0.06, ICHITA_BLUE)
    # Value
    value_size = 32 if len(str(value)) <= 6 else 24
    add_text(slide, x + 0.10, y + 0.12, w - 0.20, h * 0.60,
             str(value), size=value_size, bold=True, color=ICHITA_DARK,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
             font=FONT_AEONIK, margin=0.0)
    # Label
    add_text(slide, x + 0.10, y + h * 0.65, w - 0.20, h * 0.30,
             label, size=11, color=ICHITA_GREY,
             align=PP_ALIGN.CENTER, font=FONT_AEONIK, margin=0.0)


def highlight_card(slide, title, body, x, y, w, h):
    """Bordered emphasis card — blue left border + card fill."""
    # Main card bg
    add_rounded_rect(slide, x, y, w, h, CARD_BG,
                     line=ICHITA_GREY01, corner=0.03)
    # Blue left accent bar
    add_rect(slide, x, y, 0.06, h, ICHITA_BLUE)
    # Title
    add_text(slide, x + 0.15, y + 0.08, w - 0.25, 0.35,
             title, size=13, bold=True, color=ICHITA_DARK,
             font=FONT_AEONIK)
    # Body
    body_y = y + 0.45
    body_h = h - 0.50
    if body_h > 0.10:
        add_text(slide, x + 0.15, body_y, w - 0.25, body_h,
                 body, size=11, color=ICHITA_GREY,
                 font=FONT_AEONIK)


# ─── BACKWARDS-COMPATIBLE WRAPPERS ────────────────────────────────────────────
def create_ichita_presentation(frame_bg_path=None, dark_bg_path=None):
    """Legacy factory: create a blank presentation and apply BGs via layout.

    Kept for backwards compatibility with old build scripts. For new decks,
    prefer `create_from_template()`.
    """
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from lxml import etree

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)

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
        package = layout.part.package
        image_part = package.get_or_add_image_part(image_path)
        rId = layout.part.relate_to(image_part, RT.IMAGE)
        cSld = layout._element.find(qn('p:cSld'))
        existing_bg = cSld.find(qn('p:bg'))
        if existing_bg is not None:
            cSld.remove(existing_bg)
        cSld.insert(0, _build_blipfill_bg(rId))

    if frame_bg_path and os.path.exists(frame_bg_path):
        set_layout_bg_picture(prs.slide_layouts[6], frame_bg_path)   # Blank
    if dark_bg_path and os.path.exists(dark_bg_path):
        set_layout_bg_picture(prs.slide_layouts[5], dark_bg_path)    # Title Only
    return prs


def add_content_slide(prs, title, *, section_num=None):
    """Legacy wrapper → add_content(). `section_num` silently ignored."""
    return add_content(prs, title)


def add_dark_slide(prs):
    """Legacy wrapper: add a slide using Blank layout (inherits master BG)."""
    layout = _get_layout(prs, "Blank")
    return prs.slides.add_slide(layout)


def add_slide_title(slide, title_text, *, section_num=None, size=None):
    """Legacy wrapper → _add_title()."""
    return _add_title(slide, title_text, size=size)


def numbered_card(slide, x, y, w, h, num, title, body_runs, *,
                  accent=None, highlight=False):
    """Legacy numbered card block. Kept for old build scripts."""
    if accent is None:
        accent = ICHITA_BLUE
    bg = HIGHLIGHT_WARM if highlight else CARD_BG
    border = ICHITA_BLUE if highlight else ICHITA_GREY01
    add_rect(slide, x, y, w, h, bg, line=border)
    tag_w = 0.55; tag_h = 0.55
    add_rect(slide, x + 0.18, y + 0.18, tag_w, tag_h, accent)
    add_text(slide, x + 0.18, y + 0.18, tag_w, tag_h, num,
             size=18, bold=True, color=WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0.0)
    add_text(slide, x + 0.88, y + 0.22, w - 1.05, 0.40, title,
             size=14, bold=True, color=ICHITA_DARK)
    tb = slide.shapes.add_textbox(
        Inches(x + 0.30), Inches(y + 0.85),
        Inches(w - 0.5), Inches(h - 0.95))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.0); tf.margin_right = Inches(0.0)
    tf.margin_top = Inches(0.0); tf.margin_bottom = Inches(0.0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    for spec in body_runs:
        r = p.add_run()
        r.text = spec["text"]
        r.font.name = FONT_AEONIK
        r.font.size = Pt(spec.get("size", 11))
        r.font.color.rgb = spec.get("color", ICHITA_DARK)
        r.font.bold = spec.get("bold", False)
        r.font.italic = spec.get("italic", False)
    _force_align(p, PP_ALIGN.LEFT)


def scope_table(slide, x, y, w, h, headers, rows, *,
                ichita_col=1, highlight_col_fill=None):
    """Legacy scope table wrapper → table_branded with ichita_col tinting."""
    if highlight_col_fill is None:
        highlight_col_fill = BLUE_LIGHT
    n_cols = len(headers)
    n_rows = len(rows) + 1
    tshape = slide.shapes.add_table(
        n_rows, n_cols, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = tshape.table

    def _cell(cell, text, *, size=12, bold=False, color=None, fill=None,
               align=PP_ALIGN.LEFT):
        if color is None:
            color = ICHITA_DARK
        cell.text = ""
        p = cell.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run(); r.text = text
        r.font.name = FONT_AEONIK; r.font.size = Pt(size)
        r.font.bold = bold; r.font.color.rgb = color
        cell.text_frame.word_wrap = True
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.12)
        cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
        if fill is not None:
            cell.fill.solid(); cell.fill.fore_color.rgb = fill

    for j, h_text in enumerate(headers):
        _cell(tbl.cell(0, j), h_text, size=13, bold=True,
              color=WHITE, fill=ICHITA_DARK)
    for i, row in enumerate(rows):
        alt = CARD_BG_ALT if i % 2 == 0 else WHITE
        for j, val in enumerate(row):
            if j == ichita_col:
                _cell(tbl.cell(i+1, j), val, size=12, bold=True,
                      fill=highlight_col_fill, color=ICHITA_DARK)
            else:
                _cell(tbl.cell(i+1, j), val, size=12,
                      bold=(j == 0), fill=alt, color=ICHITA_DARK)
    return tbl


def process_flow_arrows(slide, steps, *, x_start=None, y=None,
                        step_w=None, step_h=None, gap=None,
                        step_colors=None):
    """Legacy process-flow wrapper using Inches-based args.

    Kept for old build scripts. New code: use process_flow().
    """
    if x_start is None: x_start = Inches(0.92)
    if y is None: y = Inches(1.45)
    if step_h is None: step_h = Inches(1.40)
    if gap is None: gap = Inches(0.22)
    n = len(steps)
    if step_w is None:
        step_w = Inches((SLIDE_W - 0.92 - 0.50 - (n - 1) * 0.22) / n)

    if step_colors is None:
        cyc = [ICHITA_BLUE, BLUE_LIGHT, ICHITA_GREY]
        step_colors = [cyc[i % 3] for i in range(n)]

    for i, (num, l1, l2) in enumerate(steps):
        x_emu = x_start + i * (step_w + gap)
        color = step_colors[i]
        text_col = WHITE if color != BLUE_LIGHT else ICHITA_DARK
        # Use EMU directly since this is the legacy API
        s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x_emu, y, step_w, step_h)
        s.fill.solid(); s.fill.fore_color.rgb = color
        s.line.fill.background(); s.shadow.inherit = False
        # Number text
        tb = slide.shapes.add_textbox(x_emu, y + Inches(0.12), step_w, Inches(0.55))
        tf = tb.text_frame; tf.word_wrap = False
        tf.margin_left = Inches(0); tf.margin_right = Inches(0)
        tf.margin_top = Inches(0); tf.margin_bottom = Inches(0)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = num
        r.font.name = FONT_AEONIK; r.font.size = Pt(26)
        r.font.bold = True; r.font.color.rgb = text_col
        _force_align(p, PP_ALIGN.CENTER)
        # Line texts
        add_rich_text(
            slide,
            (x_emu / 914400),
            (y + Inches(0.72)) / 914400,
            step_w / 914400, Inches(0.65) / 914400,
            [
                {"text": l1, "size": 12, "color": text_col,
                 "align": PP_ALIGN.CENTER, "space_after": 1},
                {"text": l2, "size": 12, "color": text_col,
                 "align": PP_ALIGN.CENTER},
            ], margin=0.0)
        if i < n - 1:
            ar = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                x_emu + step_w, y + step_h // 2 - Inches(0.13),
                gap, Inches(0.26))
            ar.fill.solid(); ar.fill.fore_color.rgb = ICHITA_GREY
            ar.line.fill.background(); ar.shadow.inherit = False


# ─── EXPORT ALL ───────────────────────────────────────────────────────────────
__all__ = [
    # Constants
    "SLIDE_W", "SLIDE_H",
    "ICHITA_DARK", "ICHITA_BLUE", "ICHITA_GREY", "ICHITA_GREY01",
    "OFF_WHITE", "WHITE", "CARD_BG", "CARD_BG_ALT", "HIGHLIGHT_WARM",
    "BLUE_LIGHT", "FONT_AEONIK", "FONT_AEONIK_TH", "FONT_BETATRON",
    "COLORS", "FONTS", "SIZES", "CONTENT_AREA",
    # Template factory (new primary API)
    "create_from_template",
    # Slide factories (new API)
    "add_cover", "add_content", "add_two_column",
    "add_comparison", "add_grid", "add_closing",
    # Block components (new API)
    "feature_list", "insight_bar", "process_flow",
    "table_branded", "stat_card", "highlight_card",
    # Primitives
    "add_rect", "add_rounded_rect", "add_text", "add_rich_text",
    # Internal title helper (exported for advanced callers)
    "_add_title",
    # Template utilities
    "_get_layout", "_dark_cover_blob",
    # Legacy API (backwards compatible)
    "create_ichita_presentation", "set_layout_bg_picture",
    "add_content_slide", "add_dark_slide", "add_slide_title",
    "numbered_card", "scope_table", "process_flow_arrows",
]
