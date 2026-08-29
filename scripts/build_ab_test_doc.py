#!/usr/bin/env python3
"""build_ab_test_doc.py — a Word A/B sheet for merged-vs-source font QC.

WHY THIS EXISTS

The 2026-08-02 manual QC compared a paragraph labelled "[Aeonik]" against one
labelled "[TH Aeonik]" and concluded the merged face led far too loosely. The
conclusion was right, but the control was not Aeonik: every run in that block
was Calibri. Word had substituted silently, and nothing on screen said so — the
only evidence was that no Aeonik was embedded in the exported PDF.

A font QC whose control can substitute without saying so cannot be trusted in
either direction. This generator closes that hole two ways:

  1. Every run hard-sets w:rFonts ascii/hAnsi/cs to the literal family name and
     DELETES the w:*Theme attributes. A theme attribute silently outranks the
     adjacent w:ascii, which is how a document ends up rendering Calibri while
     the font box reads something else.

  2. Each pair prints the family name it asked for. After exporting to PDF, run
     scripts/check_ab_test_pdf.py — it reads the embedded fonts and fails if a
     requested family is missing, so a substitution is caught mechanically
     rather than by eye.

     All chrome (title, headers, specimen labels) is set in CHROME_FONT, which
     is deliberately NOT a brand font. The checker measures line pitch per
     embedded font, so a brand face used for a label as well as a specimen
     would blend two different pitches into one number.

WHAT IT TESTS

Paired blocks of identical text, same point size, single line spacing:

  Aeonik        vs  TH Aeonik      — Latin leading and letterform must match
  Slussen       vs  TH Slussen     — same, for the second brand family
  Bai Jamjuree  vs  TH Aeonik      — Thai size, weight and stack clearance

The acceptance criterion is the one from the manual QC: switching a paragraph
between a source face and its merged face must not change the leading, the
letterforms or the line breaks.

USAGE
    python3 scripts/build_ab_test_doc.py
    # open test-output/th-font-ab-test.docx in Word, export to PDF, then:
    python3 scripts/check_ab_test_pdf.py <exported.pdf>
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "test-output" / "th-font-ab-test.docx"

BODY_PT = 11.0

# Chrome must never be a font under test — see the note in the docstring.
CHROME_FONT = "Arial"

# English and Thai specimens. The Thai is the paragraph from the resin report
# the manual QC was run against, so the comparison stays like-for-like, and it
# is dense in the two- and three-level stacks that expose clearance problems:
# ที่ / ครั้ง / ซึ่ง / น้ำ / เชื่อม / ปนเปื้อน / ประสิทธิภาพ.
EN = ("This is a test English paragraph. Switching it between the source face "
      "and the merged face must not change the leading, the letterforms or "
      "where the lines break. Handgloves 0123456789 quick brown fox.")

TH = ("จากการตรวจสอบกระบวนการผลิต ณ โรงงานน้ำตาลไทยรุ่งเรือง ศรีเทพ เมื่อวันที่ 28 พฤษภาคม 2569 "
      "เพื่อหาสาเหตุปัญหากลิ่นแปลกปลอมในน้ำเชื่อม พบว่ากลิ่นดังกล่าวเกิดขึ้นที่กระบวนการลดค่าสีด้วยเรซิน "
      "โดยคาดว่ามีสาเหตุจากน้ำเกลือใน Brine Recovery System ที่พักไว้นานจนเกิดการเน่าเสีย "
      "เมื่อนำไปใช้ล้างเรซินจึงทำให้กลิ่นสะสมในเม็ดเรซินและปนเปื้อนไปกับน้ำเชื่อมที่ผลิตได้")

# Isolated marks and a repeated spacing vowel. These need GDEF classes and a
# U+25CC in the font; without them Uniscribe refuses to compose the run at all.
UNISCRIBE = "าาาาาาา   ิ   ่   ์   ก็   สิทธิ์   ครั้ง   ขึ้น   กู่   จึ๊ง"

# (label, latin family, thai family) — one row per comparison.
PAIRS = [
    ("Latin leading and letterform", "Aeonik", "TH Aeonik"),
    ("Latin leading and letterform", "Slussen", "TH Slussen"),
    ("Thai size, weight and stacks", "Bai Jamjuree", "TH Aeonik"),
    ("Thai size, weight and stacks", "Bai Jamjuree", "TH Slussen"),
]


def _hard_font(run, family, pt=BODY_PT, bold=False, italic=False):
    """Pin a run to one family, leaving Word no room to substitute quietly.

    ascii/hAnsi cover Latin, cs covers the complex script (Thai) — Word tracks
    those separately, and setting only ascii leaves Thai on whatever the style
    says. The w:*Theme attributes are deleted rather than overwritten: a theme
    attribute outranks the w:ascii sitting beside it, so leaving one in place
    renders Calibri no matter what the font box shows.
    """
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rFonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme",
                 "w:cstheme"):
        if rFonts.get(qn(attr)) is not None:
            del rFonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), family)

    run.font.size = Pt(pt)
    run.font.bold = bold
    run.font.italic = italic
    # Word sizes complex-script runs off szCs/bCs/iCs, not sz/b/i. Without
    # these the Thai in a mixed paragraph ignores the point size entirely.
    for tag, val in (("w:szCs", str(int(pt * 2))),
                     ("w:bCs", "1" if bold else "0"),
                     ("w:iCs", "1" if italic else "0")):
        for old in rPr.findall(qn(tag)):
            rPr.remove(old)
        el = rPr.makeelement(qn(tag), {})
        el.set(qn("w:val"), val)
        rPr.append(el)


def _para(doc, text, family, pt=BODY_PT, bold=False, italic=False,
          space_after=0, colour=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    # Single spacing on purpose: this sheet measures what the FONT does. Any
    # explicit line rule would mask the metric being tested.
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    run = p.add_run(text)
    _hard_font(run, family, pt, bold, italic)
    if colour is not None:
        run.font.color.rgb = colour
    return p


def main():
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Pt(54)
        section.top_margin = section.bottom_margin = Pt(54)

    grey = RGBColor(0x88, 0x88, 0x88)

    _para(doc, "TH font A/B sheet", CHROME_FONT, pt=16, bold=True, space_after=2)
    _para(doc,
          "Each pair is the same text at the same size with single line "
          "spacing. The merged face must match its source: same leading, same "
          "letterforms, same line breaks. Export to PDF and run "
          "scripts/check_ab_test_pdf.py — if a family below is missing from "
          "the PDF, Word substituted it and that pair proves nothing.",
          CHROME_FONT, pt=9, space_after=14, colour=grey)

    for what, src, merged in PAIRS:
        thai_row = "Thai" in what
        body = TH if thai_row else EN
        _para(doc, f"{src}  ->  {merged}    ({what})", CHROME_FONT,
              pt=9, bold=True, space_after=4, colour=grey)
        for family in (src, merged):
            _para(doc, body, family, space_after=1)
            _para(doc, f"^ {family}", CHROME_FONT, pt=8, space_after=8,
                  colour=grey)

    _para(doc, "Uniscribe composition (needs GDEF classes + U+25CC)",
          CHROME_FONT, pt=9, bold=True, space_after=4, colour=grey)
    _para(doc,
          "Repeated and isolated vowels must type and show a dotted circle, "
          "not vanish or refuse input.",
          CHROME_FONT, pt=8, space_after=4, colour=grey)
    for family in ("TH Aeonik", "TH Slussen", "Bai Jamjuree"):
        _para(doc, UNISCRIBE, family, pt=14, space_after=1)
        _para(doc, f"^ {family}", CHROME_FONT, pt=8, space_after=8, colour=grey)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  families under test: "
          f"{', '.join(sorted({f for _, a, b in PAIRS for f in (a, b)}))}")
    print(f"  chrome (not under test): {CHROME_FONT}")
    print("\n  open in Word, export to PDF, then:")
    print("    python3 scripts/check_ab_test_pdf.py <exported.pdf>")


if __name__ == "__main__":
    main()
