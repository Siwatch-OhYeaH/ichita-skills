#!/usr/bin/env python3
"""build_book_body_proof.py — is Book 350 the right body weight for Thai?

THE DECISION THIS PROOF SETTLES

Siwatch, 2026-08-09: Thai and mixed documents set body copy at TH Aeonik Book
350; English-only documents stay at Aeonik Regular 400. He took it on the
argument below and asked to see it on paper before ichita-defaults.md changes.

THE ARGUMENT FOR BOOK

Book is the only face in the family whose Thai is Bai Jamjuree Regular
UNDISTORTED — embolden 0.0, the single such entry in th_thai_prep.BUILD_TABLE.
Every other weight bends Bai to fit a Latin; Book is the reverse, the Latin was
drawn to fit the Thai. Regular's Thai is Bai Medium thinned by 11.2 units, and
every FontForge round trip is a chance to deform a mark.

    Book     Thai = Bai Regular,  embolden  0.0,  Latin 74.2 synthesised
    Regular  Thai = Bai Medium,   embolden -11.2, Latin 85.9 CoType's own

THE ARGUMENT AGAINST

Book's Latin is synthesised and 14% lighter (74.2 against 85.9). On a screen
that reads as "cleaner"; on coated stock at 10 pt under office lighting it may
read as "faint", and faint body copy in a tender document is a real cost. That
is a paper judgement and this script does not pretend to make it.

WHY IT MUST BE PRINTED, NOT SCREENSHOTTED

Stem 74.2/1000 em at 10 pt is 0.10 px on a 96 dpi screen and 0.031 mm on paper.
Screen antialiasing rounds it to the same grey as Regular; a 1200 dpi laser does
not. §0 rule 1 in spirit: judge a face on the device it ships to.

WHAT IS ON THE SHEET

Four blocks — Book and Regular, at 10 pt and 11 pt — each the same three
paragraphs of real ICHITA copy in Thai, mixed and English. Same measure, same
leading, so the only variable is the weight. The Latin-only paragraph is there
because a mixed document still contains English sentences and they are set in
the same face.

USAGE
    python3 scripts/build_book_body_proof.py
    # PRINT it. Do not accept or reject the weight on a screen.
    # Print to PDF, never Save as PDF (§0) — then print that PDF.
"""

import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ab_test_doc import CHROME_FONT, _para  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "test-output" / "th-book-body-proof.docx"

GREY = RGBColor(0x6B, 0x72, 0x80)
BLUE = RGBColor(0x29, 0x78, 0xFF)

# Real ICHITA subject matter, not lorem. A separation-technology paragraph
# carries the numerals, units and technical nouns that actually appear in our
# body copy, and those are where a light weight fails first.
THAI = (
    "ระบบบำบัดน้ำเสียแบบเมมเบรนของ ICHITA ออกแบบมาเพื่อรองรับอัตราการไหล 120 "
    "ลูกบาศก์เมตรต่อชั่วโมง โดยมีประสิทธิภาพการกรองที่ 98.5 เปอร์เซ็นต์ "
    "ระบบนี้ผ่านการทดสอบภาคสนามที่โรงงานผลิตอาหารในจังหวัดสมุทรปราการ "
    "ตลอดระยะเวลาสิบแปดเดือน และไม่พบการอุดตันของเยื่อกรองที่ต้องหยุดเดินระบบ"
)
MIXED = (
    "หน่วย Reverse Osmosis ขนาด 50 m³/h ติดตั้งพร้อมระบบ Clean-in-Place "
    "อัตโนมัติ ค่า SDI ที่วัดได้หลังผ่าน pre-treatment อยู่ที่ 2.8 "
    "ซึ่งต่ำกว่าเกณฑ์ที่ผู้ผลิตเมมเบรนกำหนดไว้ที่ 5.0 "
    "ทำให้อายุการใช้งานของเมมเบรนยืดออกไปเป็น 36 เดือน"
)
LATIN = (
    "The membrane skid is delivered pre-piped and pre-wired on a single "
    "galvanised frame, commissioned against a 72-hour performance test before "
    "handover. Permeate conductivity held below 15 uS/cm throughout, against a "
    "specification of 25, and the differential pressure across the first stage "
    "rose 0.14 bar over the run."
)

# (label, docx font family, the weight it selects, measured Latin/Thai stem)
BLOCKS = [
    ("Book 350", "TH Aeonik Book", 74.2, 66.4),
    ("Regular 400", "TH Aeonik", 85.9, 76.2),
]
SIZES = [10.0, 11.0]


def _body(doc, text, family, pt):
    p = _para(doc, text, family, pt=pt, space_after=5)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    # 1.45 leading at both sizes so the two blocks differ ONLY in weight. Left
    # to Word's single spacing they would not: TH Aeonik's line box is 1537 and
    # the two sizes would land on different multiples.
    pf.line_spacing = Pt(pt * 1.45)
    return p


def main():
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Pt(72)
        section.top_margin = section.bottom_margin = Pt(54)

    _para(doc, "TH Aeonik — Book 350 or Regular 400 for body copy?",
          CHROME_FONT, pt=16, bold=True, space_after=2)
    _para(doc, "PRINT THIS. At 10 pt the difference between the two weights is "
               "0.031 mm of stem; a screen rounds it away and paper does not. "
               "Print to PDF — never Save as PDF, which drops the CFF and "
               "substitutes Calibri — then print that.",
          CHROME_FONT, pt=9, space_after=2, colour=BLUE)
    _para(doc, "The question is only whether Book holds up as running text. "
               "Book's Thai is Bai Jamjuree Regular undistorted, the best-drawn "
               "Thai in the family; its Latin is synthesised and 14% lighter "
               "than Regular's. Read a full paragraph of each at arm's length, "
               "not a specimen line.",
          CHROME_FONT, pt=9, space_after=14, colour=GREY)

    for size in SIZES:
        for label, family, lat, thai in BLOCKS:
            _para(doc, f"{label} at {size:.0f} pt      "
                       f"Latin stem {lat}   Thai stem {thai}",
                  CHROME_FONT, pt=9, bold=True, space_after=4, colour=GREY)
            _body(doc, THAI, family, size)
            _body(doc, MIXED, family, size)
            _body(doc, LATIN, family, size)
            _para(doc, "", CHROME_FONT, pt=6, space_after=10)
        doc.add_page_break()

    _para(doc, "How to judge it", CHROME_FONT, pt=11, bold=True, space_after=4)
    for n, line in enumerate([
        "Hold the sheet at normal reading distance and read a whole paragraph "
        "of each. A weight that is too light announces itself as effort, not as "
        "greyness.",
        "Look at the Thai tone marks and the loops of ธ ฮ ฃ. Book's are Bai's "
        "own drawing; Regular's have been thinned 11.2 units. If Book's marks "
        "read more cleanly, that is the whole argument for it.",
        "Look at the numerals and units — 120, 98.5, 50 m³/h, 15 uS/cm. "
        "Technical copy lives on these and a light face loses them first.",
        "Then the English paragraph on its own. This is where Book is weakest: "
        "its Latin is the synthesised one.",
    ], 1):
        _para(doc, f"{n}. {line}", CHROME_FONT, pt=9, space_after=3,
              colour=GREY)
    _para(doc, "If Book wins, ichita-defaults.md changes and the DOCX and HTML "
               "templates follow. If Regular wins, nothing changes and Book "
               "stays in the font as a weight you can reach for. Either way the "
               "twenty faces ship — only the brand rule waits on this sheet.",
          CHROME_FONT, pt=9, space_after=3, colour=BLUE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  {len(SIZES)} sizes x {len(BLOCKS)} weights x 3 paragraphs")
    print("\n  PRINT it. Print to PDF, never Save as PDF.")


if __name__ == "__main__":
    main()
