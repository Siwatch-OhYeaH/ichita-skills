#!/usr/bin/env python3
"""build_style_link_doc.py — the Word acceptance sheet for TH Aeonik's ten weights.

WHY THIS EXISTS

Word on Windows is the acceptance renderer and Linux cannot stand in for it
(§0 rule 1). Everything this build claims about style linking is a Uniscribe/GDI
font-mapper question, and `fc_family_probe.py` — which returns zero faults —
only speaks for fontconfig.

WHAT CHANGED ON 2026-08-09, AND WHY THE SHEET HAD TO BE REWRITTEN

The old sheet's method was to set a bolded line and, directly beneath it, THE
SAME OUTLINES SELECTED BY ANOTHER FAMILY NAME. If the link worked the two lines
were indistinguishable; if Word synthesised, the first was a fuzzy double-strike.
It worked because bold slots were duplicates — `TH Aeonik Light + Ctrl+B` and
`TH Aeonik Medium` were literally the same file.

There are no duplicates left. Each of the ten weights is drawn once, and four of
them — SemiBold, Bold, ExtraBold, Black — are reachable ONLY by pressing Ctrl+B
on their family. There is no second name to compare against, so that test cannot
be built any more.

WHAT REPLACES IT

Page 1 is the ladder: all ten weights in ink order, each labelled with how a
Word user reaches it. Every line must be visibly heavier than the one above.
That is a stronger test than the old one for what Siwatch actually asked for —
ten weights that read as ten weights — and it is still read by eye at 100% with
no instrument.

Pages 2 onward are one family each: Regular, Ctrl+B, Ctrl+I, Ctrl+B+Ctrl+I, with
the measured stem printed beside each. A synthesised bold lands near the plain
stem plus one pixel and looks blurred rather than drawn.

THE TWO FAMILIES THAT SYNTHESISE ON PURPOSE

`TH Aeonik Air` and `TH Aeonik Thin` hold no bold slot, so Word WILL synthesise
their bold. That is the decision, not a defect, and the sheet says so on those
pages — otherwise it reads as exactly the failure the rest of the sheet hunts
for. The reason it is safe only there: synthetic bold spends counter aperture,
and these two measure 113.3 and 97.7 against a floor of 46.5.

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
BLUE = RGBColor(0x29, 0x78, 0xFF)

# Mixed Thai + Latin, because the two scripts fail differently. A synthesised
# bold is obvious in the Thai (the counters of ธ and ฮ fill) and subtle in the
# Latin, so a Latin-only specimen would hide the thing most worth catching.
SPEC = "ประสิทธิภาพการกรอง 98.5% — Handgloves 0123 ธ ฮ ฃ น้ำเชื่อม"

# Measured on the shipped faces 2026-08-09, th_metrics at 512 px/em:
# (Latin stem, Thai stem).
STEMS = {
    "Air": (7.8, 7.3),
    "Thin": (23.4, 20.5),
    "Light": (52.7, 48.8),
    "Book": (74.2, 66.4),
    "Regular": (85.9, 76.2),
    "Medium": (115.2, 102.5),
    "SemiBold": (130.9, 118.2),
    "Bold": (148.4, 130.9),
    "ExtraBold": (166.0, 134.8),
    "Black": (183.6, 136.7),
}

# The ladder, lightest first: (weight name, usWeightClass, family to select in
# Word, whether Ctrl+B is needed to reach it).
LADDER = [
    ("Air", 100, "TH Aeonik Air", False),
    ("Thin", 200, "TH Aeonik Thin", False),
    ("Light", 300, "TH Aeonik Light", False),
    ("Book", 350, "TH Aeonik Book", False),
    ("Regular", 400, "TH Aeonik", False),
    ("Medium", 500, "TH Aeonik Medium", False),
    ("SemiBold", 600, "TH Aeonik Book", True),
    ("Bold", 700, "TH Aeonik", True),
    ("ExtraBold", 800, "TH Aeonik Light", True),
    ("Black", 900, "TH Aeonik Medium", True),
]

# (family, its Regular weight, its Bold weight or None, note)
FAMILIES = [
    ("TH Aeonik Air", "Air", None,
     "NO BOLD SLOT — Word synthesises, and that is the decision"),
    ("TH Aeonik Thin", "Thin", None,
     "NO BOLD SLOT — Word synthesises, and that is the decision"),
    ("TH Aeonik Light", "Light", "ExtraBold",
     "bolds to ExtraBold 800 — a display pair, deliberately the widest jump"),
    ("TH Aeonik Book", "Book", "SemiBold",
     "the BODY weight for Thai and mixed text; bolds to SemiBold 600"),
    ("TH Aeonik", "Regular", "Bold",
     "the classic pair, unchanged"),
    ("TH Aeonik Medium", "Medium", "Black",
     "bolds to Black 900"),
]


def main():
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Pt(54)
        section.top_margin = section.bottom_margin = Pt(54)

    # ---- page 1: the ladder ------------------------------------------------
    _para(doc, "TH Aeonik — ten weights, one card", CHROME_FONT,
          pt=16, bold=True, space_after=2)
    _para(doc, "Read this page first. Every line must be visibly heavier than "
               "the one above it. Ten lines, ten weights.", CHROME_FONT, pt=9,
          space_after=2, colour=GREY)
    _para(doc, "Before you start: Windows Settings > Fonts should show ONE card "
               "called TH Aeonik listing all ten styles. If you see extra cards, "
               "or a style called Air Bold, Light Bold, Book Bold, Medium Bold "
               "or SemiBold Bold, the old faces were not removed before these "
               "went in — close Word, PowerPoint and Excel, delete every "
               "TH-Aeonik file, and install the twenty again.",
          CHROME_FONT, pt=9, space_after=2, colour=RED)
    _para(doc, "EXPECTED, NOT A DEFECT: the top three weights barely separate in "
               "the Thai. Bold, ExtraBold and Black are 2.3% apart in Thai and "
               "11% apart in the Latin, because Bai Jamjuree has no heavier "
               "source and emboldening past it fills the counters of ธ ฮ ฃ. On "
               "a Thai-dominant line those three will look like one weight. On "
               "a Latin-dominant line they will not.",
          CHROME_FONT, pt=9, space_after=12, colour=BLUE)

    for name, wclass, family, needs_bold in LADDER:
        lat, thai = STEMS[name]
        _para(doc, SPEC, family, pt=BODY_PT, bold=needs_bold, space_after=1)
        how = f"{family} + Ctrl+B" if needs_bold else family
        _para(doc, f"^ {name} {wclass}   —   select \"{how}\"   —   "
                   f"Latin stem {lat}, Thai stem {thai}",
              CHROME_FONT, pt=8, space_after=7, colour=GREY)

    # ---- one page per family -----------------------------------------------
    for family, plain_w, bold_w, note in FAMILIES:
        doc.add_page_break()
        _para(doc, f"{family}    ({note})", CHROME_FONT, pt=11, bold=True,
              space_after=1)

        p_lat, p_thai = STEMS[plain_w]
        if bold_w:
            b_lat, b_thai = STEMS[bold_w]
            _para(doc, f"Ctrl+B must reach {bold_w} — Latin stem {p_lat} -> "
                       f"{b_lat}, a real drawn face. A synthesised bold lands "
                       f"near {p_lat} + 1 px instead, and looks blurred rather "
                       f"than drawn.",
                  CHROME_FONT, pt=8, space_after=6, colour=GREY)
        else:
            _para(doc, f"THIS FAMILY HAS NO BOLD. Word will synthesise one and "
                       f"it is meant to — {plain_w} is a hairline whose counters "
                       f"({'113.3' if plain_w == 'Air' else '97.7'}/1000 em) can "
                       f"afford the double-strike, and giving it a real bold is "
                       f"what broke the one-card structure on 2026-08-07. The "
                       f"bold rows below should look thickened. Report them only "
                       f"if the counters of ธ ฮ ฃ have FILLED IN.",
                  CHROME_FONT, pt=8, space_after=6, colour=BLUE)

        _para(doc, SPEC, family, pt=BODY_PT, space_after=1)
        _para(doc, f"^ {family}, Regular — {plain_w} {p_lat}/{p_thai}",
              CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, bold=True, space_after=1)
        _para(doc, f"^ {family} + Ctrl+B — must be "
                   f"{bold_w + ' ' + str(STEMS[bold_w][0]) if bold_w else 'SYNTHETIC, expected'}",
              CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, italic=True, space_after=1)
        _para(doc, f"^ {family} + Ctrl+I", CHROME_FONT, pt=8, space_after=6,
              colour=GREY)

        # The italic slots are where a half-linked family shows up — Word takes
        # the real bold for upright text and synthesises the italic — so the
        # bold italic gets its own row rather than a cross-reference.
        _para(doc, SPEC, family, pt=BODY_PT, bold=True, italic=True,
              space_after=1)
        _para(doc, f"^ {family} + Ctrl+B + Ctrl+I — must match the Ctrl+B row's "
                   f"weight, sloped",
              CHROME_FONT, pt=8, space_after=12, colour=GREY)

    # ---- what the sheet cannot tell you ------------------------------------
    doc.add_page_break()
    _para(doc, "Three things this sheet cannot tell you", CHROME_FONT, pt=11,
          bold=True, space_after=4)
    _para(doc, "1. SemiBold, Bold, ExtraBold and Black are NOT in the font "
               "dropdown. They are reachable only by pressing Ctrl+B on Book, "
               "TH Aeonik, Light and Medium. That is the cost of ten weights in "
               "one card: Word lists nameID1 families, and a family holds four "
               "slots.", CHROME_FONT, pt=9, space_after=3, colour=GREY)
    _para(doc, "2. Aeonik (Latin, for English-only documents) was deliberately "
               "NOT restructured, so bolding Aeonik Light there still "
               "synthesises. Siwatch's call, 2026-08-06 and again 2026-08-09.",
          CHROME_FONT, pt=9, space_after=3, colour=GREY)
    _para(doc, "3. Whether Book 350 is the right body weight. That is a paper "
               "judgement and it has its own proof — th-book-body-proof.docx.",
          CHROME_FONT, pt=9, space_after=3, colour=GREY)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(f"  {OUT.relative_to(ROOT)}")
    print(f"  {len(LADDER)} weights on page 1, {len(FAMILIES)} families after it")
    print(f"  {sum(1 for _, _, b, _ in FAMILIES if b)} real bold slots, "
          f"{sum(1 for _, _, b, _ in FAMILIES if not b)} that synthesise by design")
    print("\n  Close Word/PowerPoint/Excel, delete every TH-Aeonik file from the "
          "font folder,\n  install the 20 from assets/fonts/th-aeonik, then open "
          "this in Word.")


if __name__ == "__main__":
    main()
