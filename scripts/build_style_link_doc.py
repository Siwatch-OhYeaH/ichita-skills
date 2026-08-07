#!/usr/bin/env python3
"""build_style_link_doc.py — the Word acceptance sheet for TH Aeonik's bold slots.

WHY THIS EXISTS

On 2026-08-06 every TH Aeonik family got a real bold member so Word would stop
synthesising one (§4b). Four of the six families had none, and Ctrl+B in plain
Word double-struck the outline — which spends exactly the counter aperture that
keeps ฃ ธ ฮ open at text sizes. Extended 2026-08-07: a SemiBold was added and
the Thin family retired, leaving five families and 20 shipped faces.

Eight of those 20 fill a bold slot, and every one declares `usWeightClass` 700
over outlines that are really 200, 500 or 900. Word links on nameID1 + nameID2 +
the macStyle bold bit, not on usWeightClass, so that should be fine — but §0
rule 1 says Linux cannot validate Word, and this is precisely a Uniscribe/GDI
font-mapper question. So it gets measured on the real renderer.

WHAT IT TESTS, AND WHY IT NEEDS NO INSTRUMENT

Each family gets four rows: Regular, Bold, Italic, Bold Italic — the bold rows
carrying `w:b`/`w:bCs`, which is what Ctrl+B produces. Directly beneath each
bold row, the SAME TEXT is set in the face that bold is supposed to resolve to,
selected by its own family name.

    TH Aeonik Light + Ctrl+B      <- the style link
    TH Aeonik Medium              <- what it must equal

If the link works, the two lines are indistinguishable — same stroke weight,
same line breaks, same width. If Word synthesised instead, the first line is a
visibly blurred double-strike of Light and breaks differently. **That is the
whole test, and it is read by eye at 100%.** No stem probe required, which
matters because the failure mode is one anybody can see and nobody can argue
with.

If a pair does NOT match, the fix is to give each bold-slot face its own true
weight instead of 700 — see §4b.

BEFORE RUNNING IT IN WORD

Install all 20 faces from assets/fonts/th-aeonik, and UNINSTALL `TH Aeonik
Black` AND `TH Aeonik Thin` first — both are retired and nothing overwrites
them, so they would otherwise sit in the dropdown beside their replacements.
Close Word, PowerPoint AND Excel before either step; a locked file leaves a
stale registration under the family name. §9 for the rest of the traps.

USAGE
    python3 scripts/build_style_link_doc.py
    # open test-output/th-style-link-acceptance.docx in Word and read it
"""

import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ab_test_doc import CHROME_FONT, _para  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "test-output" / "th-style-link-acceptance.docx"

BODY_PT = 12.0
GREY = RGBColor(0x6B, 0x72, 0x80)
RED = RGBColor(0xB4, 0x23, 0x1A)

# Mixed Thai + Latin, because the two scripts fail differently. A synthesised
# bold is obvious in the Thai (the counters of ธ and ฮ fill) and subtle in the
# Latin, so a Latin-only specimen would hide the thing most worth catching.
SPEC = "ประสิทธิภาพการกรอง 98.5% — Handgloves 0123 ธ ฮ ฃ น้ำเชื่อม"

# (family, what its Bold slot must resolve to). Straight out of
# th_style_link: the Bold member of each nameID1 family, named by the family
# that owns those same outlines as its Regular.
FAMILIES = [
    ("TH Aeonik Air", None, "promoted — the retired Thin outlines"),
    ("TH Aeonik Light", "TH Aeonik Medium", "alias — Medium outlines"),
    ("TH Aeonik", None, "real Bold, unchanged since before 2026-08-06"),
    ("TH Aeonik Medium", None, "promoted — the retired Black outlines"),
    ("TH Aeonik SemiBold", "TH Aeonik Medium", "SYNTHETIC Latin; bolds to Black"),
]

# (plain Latin stem, bolded Latin stem) at 512 px/em over th_metrics.STEM_LATIN,
# so the numbers printed in the sheet are the ones §4b's acceptance table quotes.
STEMS = {
    "TH Aeonik Air": (7.8, 23.4),
    "TH Aeonik Light": (52.7, 115.2),
    "TH Aeonik": (85.9, 148.4),
    "TH Aeonik Medium": (115.2, 183.6),
    "TH Aeonik SemiBold": (130.9, 183.6),
}


def main():
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Pt(54)
        section.top_margin = section.bottom_margin = Pt(54)

    _para(doc, "TH Aeonik — bold style-link acceptance", CHROME_FONT,
          pt=16, bold=True, space_after=2)
    _para(doc, "Every family must bold to a REAL face. Read each pair: the "
               "bolded line and the line under it are the same outlines, so "
               "they must look identical.", CHROME_FONT, pt=9, space_after=2,
          colour=GREY)
    _para(doc, "A fuzzy, thickened, differently-breaking bold line means Word "
               "synthesised it and the style link FAILED. Report it — the fix "
               "is to set each bold-slot face to its own true weight instead "
               "of 700.", CHROME_FONT, pt=9, space_after=4, colour=RED)
    _para(doc, "Check first: 'TH Aeonik Black' and 'TH Aeonik Thin' must NOT "
               "be in the font dropdown. Both are retired — their outlines now "
               "ship as Medium's and Air's bold. If either is listed, it was "
               "not uninstalled before the new faces went in.", CHROME_FONT,
          pt=9, space_after=4, colour=RED)
    _para(doc, "SEMIBOLD NEEDS ITS OWN LOOK. LibreOffice re-reads the word "
               "\"SemiBold\" in the family name as a weight request and serves "
               "the family's BOLD for plain text — measured here, so on page 5 "
               "the Regular row and the Ctrl+B row came out identical. Word may "
               "or may not do the same; nothing on Linux can answer that. On "
               "page 5, the Regular row MUST be lighter than the Ctrl+B row. "
               "If they match, say so — the fix is a family name without a "
               "weight word in it.", CHROME_FONT, pt=9, space_after=16,
          colour=RED)

    for n, (family, equals, note) in enumerate(FAMILIES):
        plain, bold = STEMS[family]
        # One family per page. A pair split across a page break cannot be
        # compared, and comparison is the entire point of the sheet — the first
        # render put TH Aeonik Light's bold on page 1 and its match on page 2.
        if n:
            doc.add_page_break()
        _para(doc, f"{family}    ({note})", CHROME_FONT, pt=11, bold=True,
              space_after=1)
        _para(doc, f"Latin stem {plain} plain, {bold} bolded — a synthesised "
                   f"bold lands near {plain} + 1 px instead.",
              CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, space_after=1)
        _para(doc, f"^ {family}, Regular", CHROME_FONT, pt=8, space_after=6,
              colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, bold=True, space_after=1)
        _para(doc, f"^ {family} + Ctrl+B", CHROME_FONT, pt=8, space_after=6,
              colour=GREY)

        if equals:
            eq_bold = family == "TH Aeonik SemiBold"
            _para(doc, SPEC, equals, pt=BODY_PT, bold=eq_bold, space_after=1)
            _para(doc, f"^ {equals}{' + Ctrl+B' if eq_bold else ', Regular'} — "
                       f"the line above must match THIS exactly",
                  CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, italic=True, space_after=1)
        _para(doc, f"^ {family} + Ctrl+I", CHROME_FONT, pt=8, space_after=6,
              colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, bold=True, italic=True,
              space_after=1)
        _para(doc, f"^ {family} + Ctrl+B + Ctrl+I", CHROME_FONT, pt=8,
              space_after=6, colour=GREY)

        # The bold-italic slot gets its own comparison line rather than a
        # cross-reference. Naming the face it must match is not the same test:
        # the eye can only judge "identical" against something adjacent, and
        # the italic slots are where a half-linked family would show up — Word
        # takes the real bold for upright text and synthesises the italic.
        if equals:
            eq_bold = family == "TH Aeonik SemiBold"
            _para(doc, SPEC, equals, pt=BODY_PT, bold=eq_bold, italic=True,
                  space_after=1)
            _para(doc, f"^ {equals}{' + Ctrl+B' if eq_bold else ''} Italic — "
                       f"the line above must match THIS exactly",
                  CHROME_FONT, pt=8, space_after=18, colour=GREY)
        else:
            _para(doc, "", CHROME_FONT, pt=4, space_after=12)

    _para(doc, "Two things this sheet cannot tell you", CHROME_FONT, pt=11,
          bold=True, space_after=4)
    _para(doc, "1. TH Aeonik Bold and TH Aeonik Medium Bold carry IDENTICAL "
               "Thai (stem 134.8 both) — Bai Jamjuree has nothing heavier and "
               "emboldening past it fills the counters. They differ by +23.7% "
               "in the Latin only. That is the documented cap, not a defect.",
          CHROME_FONT, pt=9, space_after=3, colour=GREY)
    _para(doc, "2. Aeonik (Latin, for English-only documents) was deliberately "
               "NOT restructured, so bolding Aeonik Light there still "
               "synthesises. Siwatch's call, 2026-08-06.",
          CHROME_FONT, pt=9, space_after=3, colour=GREY)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  {len(FAMILIES)} families, "
          f"{sum(1 for _, e, _ in FAMILIES if e)} style-link pairs to compare")
    print("\n  Uninstall TH Aeonik Black AND TH Aeonik Thin, install the 20 "
          "faces, then open this in Word.")


if __name__ == "__main__":
    main()
