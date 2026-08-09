#!/usr/bin/env python3
"""build_style_link_doc.py — the Word acceptance sheet for TH Aeonik's ten weights.

WHY THIS EXISTS

Word on Windows is the acceptance renderer and Linux cannot stand in for it
(§0 rule 1). Everything this build claims about style linking is a Uniscribe/GDI
font-mapper question, and `fc_family_probe.py` — which returns zero faults —
only speaks for fontconfig.

WHAT THE STRUCTURE IS, AND WHY THE SHEET LOOKS LIKE THIS

Siwatch, 2026-08-09: "my target is one card." Ten weights, twenty files, ONE
Windows Settings card, and only the RIBBI core (`TH Aeonik`) holds a real bold.
That is the Arial and Segoe UI pattern — `Arial Black` is a plain face in its
own dropdown family, not Arial's bold — and it is what Word does naturally.

So there is nothing left to compare against by name, and the old method is gone.
It used to set a bolded line above THE SAME OUTLINES SELECTED BY ANOTHER FAMILY
NAME, which only worked while bold slots were duplicates.

Page 1 is the ladder instead: ten weights in ink order, each with the family
name that reaches it. Every line must be heavier than the one above.

Pages 2 onward are one family each, and each page states WHICH OF THREE THINGS
Ctrl+B should do — measured on Windows GDI+ 2026-08-09, not assumed:

  weight < 600   Word thickens the outline itself, +23/1000 em. Ratio depends
                 entirely on how light the face was: 1.50x at Light, 1.17x at
                 Medium.
  weight >= 600  Word REFUSES and returns the face unchanged. Segoe UI Semibold
                 600 and Arial Black 900 both measure exactly 1.00; Marlett at
                 500 synthesises at 1.24, which fixes the threshold at 600.
  real bold      only `TH Aeonik`, which reaches the drawn Bold 700 at 1.73x.

Saying which is expected is the whole point. Three of these families are
SUPPOSED to do nothing on Ctrl+B, and without the sheet saying so that reads as
the exact defect the rest of it hunts for.

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

# The ladder, lightest first. Every weight is its own dropdown name now, so the
# "how do I reach it" column is just the family — except Bold, which is
# TH Aeonik's bold slot and therefore Ctrl+B only, exactly as `Arial Bold` is.
LADDER = [
    ("Air", 100, "TH Aeonik Air", False),
    ("Thin", 200, "TH Aeonik Thin", False),
    ("Light", 300, "TH Aeonik Light", False),
    ("Book", 350, "TH Aeonik Book", False),
    ("Regular", 400, "TH Aeonik", False),
    ("Medium", 500, "TH Aeonik Medium", False),
    ("SemiBold", 600, "TH Aeonik SemiBold", False),
    ("Bold", 700, "TH Aeonik", True),
    ("ExtraBold", 800, "TH Aeonik ExtraBold", False),
    ("Black", 900, "TH Aeonik Black", False),
]

# What Ctrl+B does in each family, and the stem it should land on.
#
# Measured on Windows GDI+ 2026-08-09: below usWeightClass 600 Word applies a
# +23/1000 em double-strike; at 600 and above it REFUSES and returns the face
# itself (Segoe UI Semibold 600 and Arial Black 900 both measured 1.00, and
# Marlett at 500 synthesises at 1.24, which fixes the threshold at 600).
#
# (family, weight key, kind, expected Latin stem after Ctrl+B, note)
CTRL_B = [
    ("TH Aeonik Air", "Air", "synth", 9.8,
     "hairline — the offset is wider than the stem, so expect a DOUBLE IMAGE "
     "rather than a thicker letter. Report it only if it looks doubled at "
     "11 pt, not at heading sizes."),
    ("TH Aeonik Thin", "Thin", "synth", 46.9, "thickens cleanly"),
    ("TH Aeonik Light", "Light", "synth", 76.2, "thickens cleanly"),
    ("TH Aeonik Book", "Book", "synth", 95.7,
     "THE BODY WEIGHT for Thai and mixed text. 1.29x against a real bold's "
     "1.73x — bolded body copy will read lighter than you are used to. This is "
     "the one place the single-card structure costs something."),
    ("TH Aeonik", "Regular", "real", 148.4,
     "the ONLY real bold in the typeface — a drawn face, 1.73x"),
    ("TH Aeonik Medium", "Medium", "synth", 134.8,
     "1.17x — barely visible, because the synthetic offset is a constant and "
     "Medium is already heavy"),
    ("TH Aeonik SemiBold", "SemiBold", "none", 130.9,
     "NOTHING HAPPENS, and that is correct — Word refuses to simulate a bold "
     "at weight 600 or above"),
    ("TH Aeonik ExtraBold", "ExtraBold", "none", 166.0,
     "NOTHING HAPPENS — same rule. This is what you asked for: Ctrl+B on "
     "ExtraBold gives ExtraBold."),
    ("TH Aeonik Black", "Black", "none", 183.6,
     "NOTHING HAPPENS — same rule, and the same as Arial Black on any Windows "
     "machine."),
]

KIND_LABEL = {
    "real": "REAL drawn Bold 700",
    "synth": "Word synthesises",
    "none": "Word refuses — returns the face itself",
}


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
    for family, key, kind, want, note in CTRL_B:
        doc.add_page_break()
        plain = STEMS[key][0]
        _para(doc, f"{family}    ({KIND_LABEL[kind]})", CHROME_FONT, pt=11,
              bold=True, space_after=1)
        colour = GREY if kind == "real" else BLUE
        if kind == "real":
            detail = (f"Ctrl+B must reach the drawn Bold face — Latin stem "
                      f"{plain} -> {want}, {want/plain:.2f}x. A synthesised "
                      f"bold would land near {plain} + 1 px and look blurred.")
        elif kind == "synth":
            detail = (f"Word has no bold face to reach, so it thickens the "
                      f"outline itself — Latin stem {plain} -> about {want}, "
                      f"{want/plain:.2f}x. {note}")
        else:
            detail = (f"Ctrl+B changes NOTHING here, by Word's own rule. The "
                      f"two rows below must be identical. {note}")
        _para(doc, detail, CHROME_FONT, pt=8, space_after=6, colour=colour)

        _para(doc, SPEC, family, pt=BODY_PT, space_after=1)
        _para(doc, f"^ {family}, plain — {key} {STEMS[key][0]}/{STEMS[key][1]}",
              CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, bold=True, space_after=1)
        tail = {"real": "must be the drawn Bold",
                "synth": f"expect about {want}",
                "none": "must be IDENTICAL to the row above"}[kind]
        _para(doc, f"^ {family} + Ctrl+B — {tail}",
              CHROME_FONT, pt=8, space_after=6, colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, italic=True, space_after=1)
        _para(doc, f"^ {family} + Ctrl+I", CHROME_FONT, pt=8, space_after=6,
              colour=GREY)

        _para(doc, SPEC, family, pt=BODY_PT, bold=True, italic=True,
              space_after=1)
        _para(doc, f"^ {family} + Ctrl+B + Ctrl+I", CHROME_FONT, pt=8,
              space_after=12, colour=GREY)

    # ---- what the sheet cannot tell you ------------------------------------
    doc.add_page_break()
    _para(doc, "Three things this sheet cannot tell you", CHROME_FONT, pt=11,
          bold=True, space_after=4)
    _para(doc, "1. Bold 700 is the only weight NOT in the font dropdown. It is "
               "TH Aeonik's bold slot, reached with Ctrl+B — exactly as "
               "\"Arial Bold\" is not in the dropdown either. Every other "
               "weight has its own name.", CHROME_FONT, pt=9, space_after=3,
          colour=GREY)
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
    print(f"  {len(LADDER)} weights on page 1, {len(CTRL_B)} families after it")
    for k, label in KIND_LABEL.items():
        print(f"  {sum(1 for c in CTRL_B if c[2] == k)} x {label}")
    print("\n  Close Word/PowerPoint/Excel, delete every TH-Aeonik file from the "
          "font folder,\n  install the 20 from assets/fonts/th-aeonik, then open "
          "this in Word.")


if __name__ == "__main__":
    main()
