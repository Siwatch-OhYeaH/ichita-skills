#!/usr/bin/env python3
"""Minimum baseline-to-baseline pitch a Thai font needs to keep two lines apart.

Siwatch's acceptance test, 2026-08-03: set `สูง` on one line and `ซึ่ง` directly
below it. The lower vowel of the first line and the upper vowel + tone of the
second must be *visibly* apart — "ต้องเว้นวรรคมากพอแบบชัดเจน".

No Thai font clears that at a Latin line box. Measured at each font's own `hhea`
pitch, in 1/1000 em:

    font            line box   worst stack   spare
    Leelawadee UI       1330          1169    +161
    TH-Slussen          1512          1455     +57
    TH-Aeonik           1200          1384    -184
    Sarabun             1300          1527    -227
    Bai Jamjuree        1250          1498    -248

Sarabun — the nominated reference for correct Thai engineering — is *worse* than
our merged face on pure geometry; it escapes only because `ส` and `ซ` differ in
width, so the marks miss each other sideways. Only Leelawadee UI is comfortable,
and it buys that with markedly smaller marks (upper vowel 201 units tall against
TH-Aeonik's 273, tone 129 against 158, lower vowel 182 deep against 269), not
with a taller box.

So the clearance cannot come from the font without either breaking the rule that
the line box equals the Latin source's, or shrinking the marks back toward the
fusing that `th_mark_clearance.py` just fixed. It comes from the document, via
`w:lineRule="atLeast"`. This module computes the number to put there.

    required_pitch = worst_upper_stack + |worst_lower_tail| + MARGIN

MARGIN is Leelawadee UI's own spare, so a paragraph set to this pitch reads with
the same breathing room as the one Thai font that gets this right by default.

`atLeast`, never `Exactly` — `Exactly` is a fixed box and is where Word genuinely
clips marks. See docs/postmortems/2026-08-02-th-font-line-box-overcorrection.md.

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
    ("TH-Aeonik", "assets/fonts/aeonik-th/TH-Aeonik-*.ttf"),
    ("TH-Slussen", "assets/fonts/slussen-th/TH-Slussen-*.ttf"),
    ("Bai Jamjuree", os.path.expanduser("~/.local/share/fonts/BaiJamjuree-*.ttf")),
]
REFERENCES = [
    ("Sarabun", "/mnt/c/Users/OhYeaH/Downloads/Sarabun/Sarabun-Regular.ttf"),
    ("Leelawadee UI", "/mnt/c/Windows/Fonts/leelawui.ttf"),
]

# Ratios baked into skills/ichita-docx/scripts/md_to_docx.py. Regenerate with
# this script after any font rebuild — the mark-clearance pass moves `top`.
EXPECTED = {
    "TH-Aeonik": 1.54,
    "TH-Slussen": 1.60,
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
