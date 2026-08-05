#!/usr/bin/env python3
"""Rebuild the desktop Aeonik cut with the Greek/math coverage it is missing.

WHY THIS EXISTS. Siwatch's 2026-08-05 decision makes the font a function of the
document's language: English-only documents use Aeonik, mixed Thai/English use
TH Aeonik. That turns Aeonik itself into a shipping ICHITA face rather than only
a build input — and it makes a coverage difference between the two fonts into a
defect. If TH-Aeonik carries `μ` and Aeonik does not, then `µS/cm` falls back to a
system font in exactly the documents that were supposed to be the clean case.
Siwatch asked for the parity directly, mid-session:

    "fix the Aeonik .otf to have the same as .woff2 that we rebuild with TH-Aeonik"

So both families get their Greek from the same resolver, scripts/th_greek.py, and
cannot drift apart.

WHAT IS AND IS NOT CHANGED
--------------------------

Changed:  the five missing codepoints — Δ μ Ω harvested from the web cut, Σ and ⌀
          aliased. In the harvested faces `∆` and `µ` are repointed at the newly
          harvested outline so the Greek letter and its maths twin cannot render
          9 units apart in the same word. That is a visible change to two glyphs
          that already existed; it is on the specimen for review.
          OS/2 ulUnicodeRange1 bit 7 (Greek), so Windows' fallback machinery knows
          the font covers the block.
          nameID5, to "Version 1.001; ICHITA Greek/math coverage" — an installed
          font has to be identifiable, and this is the only honest place to say so.

NOT changed, deliberately, and each one would be a defect:

  * EVERY VERTICAL METRIC. The box stays Aeonik's own 1200 (hhea 1000/-200/0,
    usWin 1000/200). The web cut's box is 1140, and adopting it would reflow every
    English document ICHITA has ever produced. `assert_untouched()` fails the
    build if any of them moves.
  * THE LATIN OUTLINES AND SPACING. The web cut also redraws S, 1, 3, 4, 5, 8, @
    and € and respaces them, and it only exists for 6 of the 14 faces. Importing
    that would make the family internally inconsistent — six faces on v2 spacing
    and eight on v1 — which is worse than either cut alone. Open question for
    Siwatch on the specimen; not done here.
  * THE FAMILY NAME. It is still `Aeonik`, because documents and the generator's
    font selection refer to it by that name. Only nameID5 distinguishes the build.

The Latin charstrings come through th_cff.convert_to_cff, which takes the source's
own `CFF ` table wholesale and redraws only the names it is told to. So every
Latin glyph this build does not touch ships as Aeonik's own bytes, with its
BlueValues and hint operators intact — the same guarantee the TH builders rely on.

    python3 scripts/build_aeonik.py                 # all 14 faces
    python3 scripts/build_aeonik.py --faces Regular,Bold
    python3 scripts/build_aeonik.py --check         # report, write nothing
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

from fontTools.ttLib import TTFont

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import th_greek                                              # noqa: E402
from build_th_aeonik import convert_to_glyf, find_aeonik      # noqa: E402
from th_cff import assert_advance_single_source, convert_to_cff  # noqa: E402

warnings.filterwarnings("ignore")

ROOT = SCRIPTS.parent
OUTPUT_DIR = ROOT / "assets" / "fonts" / "aeonik-fixed"

FACES = [
    "Air", "Thin", "Light", "Regular", "Medium", "Bold", "Black",
    "AirItalic", "ThinItalic", "LightItalic", "RegularItalic",
    "MediumItalic", "BoldItalic", "BlackItalic",
]

# Greek and Coptic, U+0370-U+03FF. Set when any codepoint in the block is added.
# The OS/2 spec is explicit that the bit means "any character in the range", not
# "the whole range", so three letters justify it — and without it Windows will not
# consider the font for Greek fallback even though it now has the glyph.
GREEK_RANGE_BIT = 7

# nameID5. The family name stays `Aeonik`; this is the only field that says the
# file is not CoType's original, and an installed font that cannot be identified
# is how a stale build survives for two days.
VERSION_STRING = "Version 1.001; ICHITA Greek/math coverage"

# Every vertical metric, asserted unchanged. Named individually rather than
# compared as a blob so a failure says which field moved.
_VMETRICS = (
    ("hhea", "ascent"), ("hhea", "descent"), ("hhea", "lineGap"),
    ("OS/2", "sTypoAscender"), ("OS/2", "sTypoDescender"),
    ("OS/2", "sTypoLineGap"),
    ("OS/2", "usWinAscent"), ("OS/2", "usWinDescent"),
    ("head", "unitsPerEm"),
)


def _vmetrics(font):
    return {f"{tag}.{attr}": getattr(font[tag], attr) for tag, attr in _VMETRICS}


def assert_untouched(before, after, face):
    """No vertical metric may move. See the docstring on why this is a hard fail.

    The web cut's box is 1140 against the desktop's 1200. Nothing in this build
    should go near a vertical metric, so this is a tripwire rather than a check of
    anything the code deliberately does — which is exactly the kind of assertion
    this repo has learned to want. A silent 5% leading change across every English
    document would be found by a reader, not by a test.
    """
    moved = [f"{k}: {before[k]} -> {after[k]}"
             for k in before if before[k] != after[k]]
    if moved:
        raise SystemExit(
            f"     !! {face}: this build moved a vertical metric, which it must "
            f"never do — {'; '.join(moved)}. The box is Aeonik's own 1200 and "
            f"every English document leads off it.")


def build_face(face, out_dir, check_only=False):
    src_path = find_aeonik(f"Aeonik-{face}.otf")
    if src_path is None:
        print(f"\n  === {face} ===\n     !! source not found: Aeonik-{face}.otf")
        return False

    print(f"\n  === {face} ===")
    print(f"     Source: {src_path}")

    font = TTFont(str(src_path))
    if "CFF " not in font:
        print(f"     !! {face} is not CFF — this build assumes the desktop cut")
        return False

    before = _vmetrics(font)

    if check_only:
        _, report = th_greek.resolve(face, src_path)
        for line in report or ["nothing missing"]:
            print(f"     {line}")
        font.close()
        return True

    # A pristine copy of the source's CFF, read from the file a second time so no
    # mutation below can reach it. Same discipline as the TH builders.
    latin_cff = TTFont(str(src_path))["CFF "]

    convert_to_glyf(font)
    written = th_greek.close_gaps(font, face, src_path, label="1")

    if written:
        font["OS/2"].ulUnicodeRange1 |= (1 << GREEK_RANGE_BIT)

    name_table = font["name"]
    for rec in name_table.names:
        if rec.nameID == 5:
            rec.string = VERSION_STRING

    # `glyf` renderers place an outline at (lsb - xMin) and the CFF pen draws
    # THROUGH that offset, so a stale lsb shifts the charstring. Harvested glyphs
    # arrive with an lsb of 0 from TTGlyphPen; without this they would be drawn
    # displaced by their own xMin. Deleting this step from the TH builder once
    # collapsed a counter from 55.2 to 3.9 — see build_th_aeonik step 6b.
    glyf_table, hmtx = font["glyf"], font["hmtx"]
    shifted = 0
    for gname in font.getGlyphOrder():
        glyph = glyf_table[gname]
        glyph.recalcBounds(glyf_table)
        advance, lsb = hmtx.metrics[gname]
        x_min = getattr(glyph, "xMin", 0)
        if lsb != x_min:
            hmtx.metrics[gname] = (advance, x_min)
            shifted += 1
    if shifted:
        print(f"     [2] lsb re-synced to xMin on {shifted} glyph(s)")

    convert_to_cff(font, latin_cff, written, label="3", kind="Greek")
    assert_advance_single_source(font, label="3b")

    after = _vmetrics(font)
    assert_untouched(before, after, face)
    print(f"     [4] vertical metrics unchanged: box "
          f"{after['hhea.ascent']}/{after['hhea.descent']}/"
          f"{after['hhea.lineGap']} = "
          f"{after['hhea.ascent'] - after['hhea.descent'] + after['hhea.lineGap']}"
          f", usWin {after['OS/2.usWinAscent']}/{after['OS/2.usWinDescent']}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"Aeonik-{face}.otf"
    font.save(str(out_path))
    font.close()

    verify(out_path, face)
    print(f"     Saved: {out_path.name} "
          f"({out_path.stat().st_size / 1024:.0f} KB)")
    return True


def verify(path, face):
    """Assert the five codepoints resolve, and that they resolve to real ink."""
    from fontTools.pens.boundsPen import BoundsPen

    font = TTFont(str(path), lazy=True)
    try:
        cmap = font.getBestCmap()
        gs = font.getGlyphSet()
        missing, blank = [], []
        for cp in list(th_greek.HARVEST) + list(th_greek.ALIAS_ONLY):
            gname = cmap.get(cp)
            if gname is None:
                missing.append(f"U+{cp:04X}")
                continue
            pen = BoundsPen(gs)
            gs[gname].draw(pen)
            if not pen.bounds:
                blank.append(f"U+{cp:04X} -> {gname}")
        # Twin consistency, asserted rather than assumed: the two codepoints must
        # name ONE glyph, or they render at two different widths in one word.
        split = []
        for cp in th_greek.TWIN_SHARES_OUTLINE:
            twin = th_greek.HARVEST[cp][1]
            if cmap.get(cp) != cmap.get(twin):
                split.append(f"U+{cp:04X}={cmap.get(cp)} vs "
                             f"U+{twin:04X}={cmap.get(twin)}")
        greek_bit = bool(font["OS/2"].ulUnicodeRange1 & (1 << GREEK_RANGE_BIT))
        problems = []
        if missing:
            problems.append(f"absent from cmap: {', '.join(missing)}")
        if blank:
            problems.append(f"maps to a blank glyph: {', '.join(blank)}")
        if split:
            problems.append(f"twin split: {'; '.join(split)}")
        if not greek_bit:
            problems.append("OS/2 Greek range bit not set")
        if problems:
            raise SystemExit(f"     !! {face} verify FAILED — "
                             + "; ".join(problems))
        print(f"     [5] Verify: 5/5 codepoints present with ink | twins share "
              f"one glyph | Greek range bit set")
    finally:
        font.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--faces", default=None,
                    help="comma-separated face names (default: all 14)")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--check", action="store_true",
                    help="report what each face would get and write nothing")
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else OUTPUT_DIR
    faces = ([f.strip() for f in args.faces.split(",")] if args.faces
             else FACES)

    print("\n" + "=" * 70)
    print("  AEONIK REBUILD — Greek/math coverage, metrics untouched")
    print("  Parity with TH Aeonik, per Siwatch 2026-08-05")
    print("=" * 70)

    ok = sum(bool(build_face(f, out_dir, args.check)) for f in faces)
    print(f"\n{'=' * 70}")
    print(f"  {'PASS' if ok == len(faces) else 'FAIL'}: {ok}/{len(faces)} faces")
    if not args.check:
        print(f"  Output: {out_dir}")
        print(f"  Install these OVER the current Aeonik — same family name, "
              f"nameID5 '{VERSION_STRING}'")
    print("=" * 70 + "\n")
    return 0 if ok == len(faces) else 1


if __name__ == "__main__":
    sys.exit(main())
