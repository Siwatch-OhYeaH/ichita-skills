#!/usr/bin/env python3
"""Specimen sheet for the Greek/math coverage added on 2026-08-05.

This is the acceptance artifact for Phase 3 of
docs/plans/2026-08-05-th-aeonik-line-box-reversal-and-cross-platform.md, and it
exists because two of the five codepoints CHANGE A GLYPH THAT ALREADY SHIPPED.
Harvesting Greek Δ and μ from the web cut means `∆` U+2206 and `µ` U+00B5 now
carry the v2 drawing, since a Greek letter and its maths twin cannot render at two
different widths in the same word. That is a visible change to Aeonik and it is
Siwatch's call, so it gets looked at rather than asserted.

Three sheets:

  1  the five codepoints beside their twins, all 14 weights — the twin columns are
     where the appearance change shows
  2  running text at reading size: Δp, µS/cm, m³/h, H₂O, ±, ≤, Ω
  3  before/after, v1 source against this build, for the two changed glyphs only

CAVEAT WORTH STATING BECAUSE THIS REPO HAS BEEN BURNED BY IT. This renders through
FreeType, which is NOT the acceptance renderer — Windows rasterises CFF through its
own engine and lands 16-20% apart on ink. That does not matter here: this sheet is
for judging SHAPE, and a shape is a shape in any rasteriser. Anything about weight,
stem pixels or leading has to be measured with scripts/win_latin_parity.py instead.

    python3 scripts/build_greek_specimen.py
    python3 scripts/build_greek_specimen.py --dir assets/fonts/th-aeonik \
        --prefix TH-Aeonik
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import freetype
import numpy as np
from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
ROOT = SCRIPTS.parent

import th_greek                                          # noqa: E402

# (codepoint, twin codepoint, label). Order follows th_greek's own tables.
PAIRS = [
    (0x0394, 0x2206, "Delta"),
    (0x03BC, 0x00B5, "mu"),
    (0x03A9, 0x2126, "Omega"),
    (0x03A3, 0x2211, "Sigma"),
    (0x2300, 0x00D8, "diameter"),
]

FACES = [
    "Air", "Thin", "Light", "Regular", "Medium", "Bold", "Black",
    "AirItalic", "ThinItalic", "LightItalic", "RegularItalic",
    "MediumItalic", "BoldItalic", "BlackItalic",
]

# Real strings from real ICHITA documents. `µS/cm` is the one that matters most —
# conductivity is on every water analysis, and Excel pastes it with U+00B5 about
# as often as Word's equation editor emits U+03BC.
RUNNING = [
    "Δp = 0.42 bar across the membrane stack",
    "Conductivity 148 µS/cm  /  148 μS/cm",
    "Design flow 250 m³/h at 25 °C",
    "H₂O hardness ≤ 120 mg/L as CaCO₃",
    "Ω = 4.7 kΩ  ±2%  ⌀ 150 mm  Σ = 1 240 m³",
]

GREY = 128
BLACK = 0


def _render(path, cp, px):
    """(bitmap, bitmap_top, advance_px) for one codepoint, or None."""
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, px)
    try:
        face.load_char(cp, freetype.FT_LOAD_RENDER)
    except Exception:
        return None
    bm = face.glyph.bitmap
    adv = face.glyph.advance.x / 64.0
    if not bm.width or not bm.rows:
        return None, 0, adv
    a = np.array(bm.buffer, dtype=np.uint8).reshape(
        bm.rows, bm.pitch)[:, :bm.width]
    return a, face.glyph.bitmap_top, adv


def _paste(sheet, path, cp, px, x, y_baseline):
    r = _render(path, cp, px)
    if r is None:
        return 0
    a, top, adv = r
    if a is not None:
        sheet.paste(Image.fromarray(255 - a), (int(x), int(y_baseline - top)))
    return adv


def sheet_grid(src_dir, prefix, out_path, px=54):
    """Sheet 1 — the five codepoints beside their twins, every weight."""
    col_w, row_h = 150, 92
    left = 150
    width = left + col_w * len(PAIRS) + 30
    height = 96 + row_h * len(FACES)
    sheet = Image.new("L", (width, height), 255)
    d = ImageDraw.Draw(sheet)

    d.text((16, 20), "GREEK / MATH COVERAGE — added 2026-08-05", fill=BLACK)
    d.text((16, 38), f"{prefix}  —  each cell: Greek codepoint, then its twin. "
                     f"The TWIN column is where the appearance change shows.",
           fill=GREY)
    for i, (cp, twin, label) in enumerate(PAIRS):
        x = left + i * col_w
        d.text((x, 66), f"U+{cp:04X} {chr(cp)} | U+{twin:04X}", fill=BLACK)
        d.text((x, 78), label, fill=GREY)

    for j, face in enumerate(FACES):
        path = src_dir / f"{prefix}-{face}.otf"
        y = 96 + j * row_h
        d.text((16, y + 30), face, fill=BLACK if path.exists() else GREY)
        if not path.exists():
            d.text((left, y + 30), "not built", fill=GREY)
            continue
        baseline = y + row_h - 26
        for i, (cp, twin, _) in enumerate(PAIRS):
            x = left + i * col_w
            adv = _paste(sheet, path, cp, px, x, baseline)
            _paste(sheet, path, twin, px, x + adv + 14, baseline)
    sheet.save(out_path)
    return out_path


def sheet_running(src_dir, prefix, out_path, px=26):
    """Sheet 2 — reading size, real strings, three weights."""
    faces = ["Light", "Regular", "Bold"]
    line_h = 46
    height = 90 + len(faces) * (line_h * len(RUNNING) + 40)
    sheet = Image.new("L", (1180, height), 255)
    d = ImageDraw.Draw(sheet)
    d.text((16, 20), "RUNNING TEXT — the characters as they actually appear",
           fill=BLACK)
    d.text((16, 38), f"{prefix} at {px} px/em. Line 2 sets U+00B5 and U+03BC side "
                     f"by side: they MUST be indistinguishable.", fill=GREY)

    y = 74
    for face in faces:
        path = src_dir / f"{prefix}-{face}.otf"
        d.text((16, y), face, fill=BLACK)
        y += 24
        if not path.exists():
            d.text((40, y), "not built", fill=GREY)
            y += line_h
            continue
        for text in RUNNING:
            x = 40
            for ch in text:
                x += _paste(sheet, path, ord(ch), px, x, y + px)
            y += line_h
        y += 16
    sheet.save(out_path)
    return out_path


def sheet_before_after(src_dir, prefix, out_path, px=110):
    """Sheet 3 — the two glyphs this build CHANGED, v1 against v2.

    Only meaningful for the Aeonik families, whose twins were redrawn. The old
    outline is read from the pristine source rather than remembered.
    """
    from build_th_aeonik import find_aeonik

    changed = sorted(th_greek.TWIN_SHARES_OUTLINE)
    faces = ["Light", "Regular", "Bold", "LightItalic", "RegularItalic",
             "BoldItalic"]
    col_w, row_h = 330, 150
    sheet = Image.new("L", (60 + col_w * len(changed), 110 + row_h * len(faces)),
                      255)
    d = ImageDraw.Draw(sheet)
    d.text((16, 20), "BEFORE / AFTER — the two glyphs this build changes",
           fill=BLACK)
    d.text((16, 38), "left: Aeonik v1.000 as shipped.  right: this build, the web "
                     "cut's drawing.  Only the harvested faces differ.", fill=GREY)
    for i, cp in enumerate(changed):
        twin = th_greek.HARVEST[cp][1]
        d.text((60 + i * col_w, 66),
               f"U+{twin:04X} {chr(twin)}   v1  ->  v2", fill=BLACK)

    for j, face in enumerate(faces):
        y = 110 + j * row_h
        baseline = y + row_h - 34
        d.text((16, y + 40), face, fill=BLACK)
        new_path = src_dir / f"{prefix}-{face}.otf"
        old_path = find_aeonik(f"Aeonik-{face}.otf")
        for i, cp in enumerate(changed):
            twin = th_greek.HARVEST[cp][1]
            x = 60 + i * col_w
            if old_path:
                adv = _paste(sheet, old_path, twin, px, x, baseline)
            else:
                adv = px
            if new_path.exists():
                _paste(sheet, new_path, twin, px, x + adv + 40, baseline)
    sheet.save(out_path)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default="assets/fonts/aeonik")
    ap.add_argument("--prefix", default="Aeonik")
    ap.add_argument("--out-dir", default="test-output")
    args = ap.parse_args()

    src = ROOT / args.dir if not Path(args.dir).is_absolute() else Path(args.dir)
    out = ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    tag = args.prefix.lower()

    made = [
        sheet_grid(src, args.prefix, out / f"greek-{tag}-1-grid.png"),
        sheet_running(src, args.prefix, out / f"greek-{tag}-2-running.png"),
    ]
    if args.prefix in ("Aeonik", "TH-Aeonik"):
        made.append(sheet_before_after(
            src, args.prefix, out / f"greek-{tag}-3-before-after.png"))

    for p in made:
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size / 1024:.0f} KB)")
    print("\nFreeType render — judge SHAPE here, never weight or leading. "
          "For those use scripts/win_latin_parity.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
