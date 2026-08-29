#!/usr/bin/env python3
"""Minimum baseline-to-baseline pitch a Thai font needs to keep two lines apart.

Siwatch's acceptance test, 2026-08-03: set `สูง` on one line and `ซึ่ง` directly
below it. The lower vowel of the first line and the upper vowel + tone of the
second must be *visibly* apart — "ต้องเว้นวรรคมากพอแบบชัดเจน".

No Thai font clears that at a Latin line box. Measured at each font's own `hhea`
pitch, in 1/1000 em, as of the 2026-08-05 build:

    font            line box   worst stack   spare
    TH-Slussen          1602          1527     +75
    TH-Aeonik           1537          1462     +75
    Leelawadee UI       1330          1255     +75
    Sarabun             1300          1582    -282
    Bai Jamjuree        1250          1564    -314

The two merged families now sit exactly where Leelawadee UI sits, and that is not
a coincidence — MARGIN is Leelawadee's own spare, so matching it is the design
target, reached by sizing the box to the measured stack rather than by shrinking
marks.

Sarabun — the nominated reference for correct Thai engineering — is *worse* than
our merged faces on pure geometry; it escapes only because `ส` and `ซ` differ in
width, so the marks miss each other sideways. Leelawadee UI buys its comfort with
markedly smaller marks (upper vowel 201 units tall against TH-Aeonik's 273, tone
129 against 158, lower vowel 182 deep against 269) rather than with a taller box;
this project took the other route, because tone marks that differ by small
strokes (่ ้ ๊ ๋) cannot afford to shrink.

    required_pitch = worst_upper_stack + |worst_lower_tail| + MARGIN

MARGIN is Leelawadee UI's own spare, so a paragraph set to this pitch reads with
the same breathing room as the one Thai font that gets this right by default.

WHERE THE CLEARANCE COMES FROM — read this before trusting the table above.

Until 2026-08-05 this docstring said the clearance "cannot come from the font
without breaking the rule that the line box equals the Latin source's", and
therefore had to come from the document via `w:lineRule="atLeast"`. THE RULE IT
APPEALED TO NO LONGER EXISTS. It was never a principle — it was one day's trade,
and it is the exact kind of stale premise this repo has been burned by twice.

Siwatch's 2026-08-05 decision removes it: the font is chosen by the document's
language, so English-only documents get Aeonik and only mixed Thai/English
documents get TH Aeonik. Nothing has to lead like Aeonik, so THE FONT CARRIES ITS
OWN CLEARANCE — TH-Aeonik's box is 1537 and TH-Slussen's 1602, each `required`
below. That matters because the acceptance test is someone typing in plain Word,
where no generator is around to set a paragraph property.

The document-layer ratios in EXPECTED below are now belt and braces rather than
the only thing holding two Thai lines apart. They still earn their place: they
protect a document whose font is missing and got substituted, and Bai Jamjuree
(box 1250 against a 1639 need) has no font-side fix at all.

`atLeast`, never `Exactly` — `Exactly` is a fixed box and is where Word genuinely
clips marks. See docs/THAI-LATIN-FONT-ENGINEERING.md (§3); the original is docs/archive/2026-08-02-th-font-line-box-overcorrection.md.

Usage:
    python3 scripts/thai_line_pitch.py                 # report every known font
    python3 scripts/thai_line_pitch.py --check         # assert the md_to_docx constants
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

# Leelawadee UI's own spare against this corpus: 1330 - 1255. Two derivations
# land on the same number, which is why it is trustworthy:
#   - it is what the one Thai font that gets this right actually delivers;
#   - 68/1000 em is one pixel at 11 pt / 96 dpi, so 75 is the smallest gap that
#     survives the pixel grid instead of merely existing in the outline.
# On Siwatch's own `สูง` / `ซึ่ง` pair the realised gap is about twice this,
# since that pair is not the worst the script can produce.
MARGIN = 75.0

# Tallest stacks the shaper can produce: a high-ascender consonant carrying an
# upper vowel and a tone. `ปั๊` and `ฟื้` beat `ซึ่` because the ascender pushes
# the whole stack up.
UPPER_WORST = ["ปื้", "ฟื๊", "ฝั้", "ฬึ๋", "ขึ้", "ที่", "ซึ่ง", "ครั้", "จึ๊", "ณิ์"]

# Deepest ink below the baseline: the two tailed consonants, the below-vowels,
# and the vocalic letters.
LOWER_WORST = ["ญ", "ฐ", "สูง", "ภู", "ปุ", "ฎ", "ฏ", "ฤ", "ฦ", "กฺ"]


def _extremes(path: str, corpus: list[str]) -> tuple[float, float]:
    """(lowest, highest) shaped ink across `corpus`, in 1/1000 em."""
    with open(path, "rb") as fh:
        data = fh.read()
    face = hb.Face(data)
    hbfont = hb.Font(face)
    tt = TTFont(path, fontNumber=0)
    scale = 1000.0 / tt["head"].unitsPerEm
    glyphs = tt.getGlyphSet()
    order = tt.getGlyphOrder()

    lo, hi = 0.0, 0.0
    for text in corpus:
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hbfont, buf)
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            pen = BoundsPen(glyphs)
            try:
                glyphs[order[info.codepoint]].draw(pen)
            except Exception:
                continue
            if not pen.bounds:
                continue
            off = pos.y_offset * scale
            lo = min(lo, pen.bounds[1] * scale + off)
            hi = max(hi, pen.bounds[3] * scale + off)
    return lo, hi


def required_pitch(path: str) -> dict:
    """Minimum baseline-to-baseline pitch, in 1/1000 em, plus the workings."""
    _, top = _extremes(path, UPPER_WORST)
    bottom, _ = _extremes(path, LOWER_WORST)
    tt = TTFont(path, fontNumber=0)
    hhea = tt["hhea"]
    scale = 1000.0 / tt["head"].unitsPerEm
    box = (hhea.ascender - hhea.descender + hhea.lineGap) * scale
    need = top - bottom
    return {
        "top": top,
        "bottom": bottom,
        "need": need,
        "box": box,
        "spare": box - need,
        "required": need + MARGIN,
        "ratio": (need + MARGIN) / 1000.0,
    }


# The families this repo ships or sets text in. Each entry is (label, glob).
FAMILIES = [
    ("TH-Aeonik", "assets/fonts/th-aeonik/TH-Aeonik-*.otf"),
    ("TH-Slussen", "assets/fonts/th-slussen/TH-Slussen-*.otf"),
    ("Bai Jamjuree", os.path.expanduser("~/.local/share/fonts/BaiJamjuree-*.ttf")),
]
REFERENCES = [
    ("Sarabun", "/mnt/c/Users/OhYeaH/Downloads/Sarabun/Sarabun-Regular.ttf"),
    ("Leelawadee UI", "/mnt/c/Windows/Fonts/leelawui.ttf"),
]

# Ratios baked into skills/ichita-docx/scripts/md_to_docx.py. Regenerate with
# this script after any font rebuild — the mark-clearance pass moves `top`.
#
# DOCUMENT-layer ratios. From 2026-08-05 they CONVERGE with the font's own line
# box for the two merged families rather than diverging from it — TH-Aeonik's box
# is 1537 against the 1.537 below, TH-Slussen's is 1602 against 1.602 — because
# the font now carries its own clearance (see the docstring). `atLeast` takes the
# larger of the two, so for those families this is a no-op that costs nothing and
# fails safe if the font is missing and Word substitutes.
#
# Bai Jamjuree is the case that still needs the document layer: its box is 1250
# against a 1639 need and this repo does not build it, so nothing but the
# paragraph property can hold its lines apart.
#
# Regenerate after any rebuild — the mark-clearance pass moves `top`, and these
# must stay at or above the `required` column this script prints.
EXPECTED = {
    "TH-Aeonik": 1.54,
    "TH-Slussen": 1.63,
    "Bai Jamjuree": 1.64,
}


def family_worst(pattern: str) -> tuple[dict | None, str]:
    worst, worst_path = None, ""
    for path in sorted(glob.glob(pattern)):
        try:
            r = required_pitch(path)
        except Exception:
            continue
        if worst is None or r["required"] > worst["required"]:
            worst, worst_path = r, path
    return worst, worst_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if a family needs more than the ratio in md_to_docx.py")
    args = ap.parse_args()

    print(f"{'family':16s} {'worst face':26s} {'top':>7s} {'bottom':>7s} "
          f"{'need':>7s} {'box':>6s} {'spare':>7s} {'atLeast x pt':>13s}")
    fails = []
    for label, pattern in FAMILIES:
        r, path = family_worst(pattern)
        if r is None:
            print(f"{label:16s} (not found: {pattern})")
            continue
        face = os.path.basename(path)
        print(f"{label:16s} {face:26s} {r['top']:7.0f} {r['bottom']:7.0f} "
              f"{r['need']:7.0f} {r['box']:6.0f} {r['spare']:+7.0f} {r['ratio']:13.3f}")
        want = EXPECTED.get(label)
        if want is not None and r["ratio"] > want + 1e-9:
            fails.append(f"{label}: needs {r['ratio']:.3f} x pt, "
                         f"md_to_docx.py carries {want:.2f}")

    print()
    for label, path in REFERENCES:
        if not os.path.exists(path):
            continue
        r = required_pitch(path)
        print(f"{label:16s} {'(reference)':26s} {r['top']:7.0f} {r['bottom']:7.0f} "
              f"{r['need']:7.0f} {r['box']:6.0f} {r['spare']:+7.0f} {r['ratio']:13.3f}")

    if args.check:
        print()
        if fails:
            for f in fails:
                print(f"FAIL  {f}")
            return 1
        print(f"OK  all families fit the ratios in md_to_docx.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
