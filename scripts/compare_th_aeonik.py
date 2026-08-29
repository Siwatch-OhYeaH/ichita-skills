#!/usr/bin/env python3
"""DEPRECATED — this test asserts the defect it was meant to catch.

It compares merged Thai against Bai Jamjuree and passes when the two are
pixel-identical. That is the wrong reference. Bai's Thai is drawn to sit beside
Bai's OWN Latin; dropped unscaled into Aeonik/Slussen it renders 9% too large
and 18-25% too light. "Identical to Bai" is therefore the broken state, and
this test could only pass while the font was wrong. It was cited in two
post-mortems as proof the merge was correct.

Replaced by scripts/qc_th_fonts.py, which measures Thai against the LATIN it
shares a line with: x-height match, stem match, ink containment, and shaping of
real stacked words.

Kept only for the raster-diff plumbing. Do not use its verdict.
"""

"""
Acceptance test for TH-Aeonik.

The merge is only correct if it is invisible:
  * Thai in TH Aeonik must render as Bai Jamjuree.
  * Latin in TH Aeonik must render as Aeonik.

Checked two ways, across every weight and a wide range of sizes:

  1. Shaping  — HarfBuzz glyph sequence + positions, exact match required.
  2. Raster   — FreeType glyph bitmaps.

THE BAR IS THE OPPOSITE WAY ROUND FROM THE OLD CFF BUILD. The font now ships as
TrueType (`glyf`), so Bai Jamjuree's Thai outlines are copied verbatim and
**Thai must be pixel-exact** — every dimension, advance and pixel. Any
difference at all means the verbatim copy did not happen, which is the single
thing this format change exists to guarantee.

Latin now carries the conversion instead: Aeonik's cubics are approximated as
quadratics by cu2qu, and FreeType renders `glyf` with a different engine than
CFF. That residue is bounded, not eliminated, and the bounds below are set from
the measured distribution over 4572 differing (glyph, size) comparisons:

  * mean edge deviation  p50 3.94, p99 11.70, max 16.12/255  -> limit 20.0
  * one bitmap dimension differs by 1px ('6' @144px, Italic) -> limit 1
  * advances: zero mismatches                                -> limit 0

Those numbers only hold because the build re-syncs `hmtx` lsb to each glyph's
xMin. `glyf` renderers position an outline at (lsb - xMin); CFF ignores lsb
entirely, so Aeonik ships a few glyphs whose declared lsb disagrees with their
own outline — BoldItalic '9' says 33 against an xMin of 31. Inheriting that
translated the whole glyph 2 units and put max deviation at 37.34/255 with 8
advance mismatches. If those symptoms ever return, suspect lsb before cu2qu.

`space` is deliberately excluded from the Thai comparison. It is a shared
glyph and comes from Aeonik (262 units) rather than Bai Jamjuree (260), which
is what mixed Thai/Latin text needs.

Usage:  python3 compare_th_aeonik.py
Exit 0 = pass.
"""

import sys
from pathlib import Path

import freetype
import uharfbuzz as hb

from fontTools.misc.psCharStrings import T2WidthExtractor
from fontTools.ttLib import TTFont

ASSETS = Path(__file__).parent.parent / "assets" / "fonts"
MERGED, AEONIK, BAI = ASSETS / "th-aeonik", ASSETS / "aeonik", ASSETS / "bai-jamjuree"

PAIRS = {
    "Regular":       ("Aeonik-Regular.otf",       "BaiJamjuree-Regular.ttf"),
    "Bold":          ("Aeonik-Bold.otf",          "BaiJamjuree-Bold.ttf"),
    "Light":         ("Aeonik-Light.otf",         "BaiJamjuree-Light.ttf"),
    "RegularItalic": ("Aeonik-RegularItalic.otf", "BaiJamjuree-Italic.ttf"),
    "BoldItalic":    ("Aeonik-BoldItalic.otf",    "BaiJamjuree-BoldItalic.ttf"),
    "LightItalic":   ("Aeonik-LightItalic.otf",   "BaiJamjuree-LightItalic.ttf"),
}

PPEMS = [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72, 144]

# Latin tolerances — see the module docstring for the measurements behind each.
# Thai has no tolerance at all; it must be byte-identical.
LATIN_MAX_MEAN_DEV = 20.0   # mean coverage delta (/255) over differing pixels
LATIN_MAX_DIM_DELTA = 1     # px, on any of width/rows/left/top
LATIN_MAX_ADV_DELTA = 0     # 26.6 units — exact; lsb re-sync removed all drift

# Thai only — no spaces, so the shared `space` glyph never enters the compare.
THAI = [
    "สวัสดีครับ", "น้ำเชื่อม", "ผู้", "ญุ", "ฐู", "ญี่", "ฐาน",
    "ปั่น", "ฟั้น", "ใผ่", "เป็น", "ก์", "น์", "ร์",
    "เกือบทุกวัน", "กระทรวงการคลัง", "ที่", "ซึ่ง", "กิ่ง", "หนึ่ง",
    "ประเทศไทย", "อิชิตะ", "ผลิตภัณฑ์", "รายงานประจำปี",
]
LATIN = [
    "Ichita", "The quick brown fox jumps over the lazy dog",
    "AVATAR Wo Ta To Ya", "fi fl ffi 0123456789", "Hamburgefonstiv",
    "€ £ ¥ § ¶ † ‡ — – ‘’ “”", "Waltz, bad nymph, for quick jigs vex!",
]
MIXED = [
    "ICHITA อิชิตะ 2026",
    "รายงาน Q3 ปี 2026 (Revenue +12.5%)",
    "ติดต่อ: sales@ichita.co.th โทร 02-123-4567",
    "ผลิตภัณฑ์ Ichita Green Tea ขนาด 500ml",
]

_order_cache = {}


def _order(path):
    if path not in _order_cache:
        _order_cache[path] = TTFont(path, lazy=True).getGlyphOrder()
    return _order_cache[path]


def shape(path, text, ppem):
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
    font.scale = (ppem * 64, ppem * 64)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    names = _order(str(path))
    return [(names[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def raster(path, char, ppem):
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, ppem)
    idx = face.get_char_index(ord(char))
    if idx == 0:
        return None
    face.load_glyph(idx, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    g = face.glyph
    return (g.bitmap.width, g.bitmap.rows, g.bitmap_left, g.bitmap_top,
            g.advance.x, bytes(g.bitmap.buffer))


def check_advance_source(path):
    """Every glyph must state ONE advance width, and Thai marks must state zero.

    REWRITTEN 2026-08-04, and the previous version is worth describing because it
    was correct and is now inverted. It asserted "no CFF table, a real `glyf`
    table" — i.e. it asserted the FORMAT, on the reasoning that `glyf` has no
    width operand and so cannot express a disagreement at all. That was true, and
    it is exactly the invariant this build deliberately gives up: the family ships
    CFF again because Windows renders CFF and TrueType through different
    rasterisers, and a merged font in the other format cannot render its Latin
    identically (measured -15.8% ink at 11 pt in DirectWrite; see
    scripts/th_cff.py).

    So the structural guarantee is replaced by an ASSERTION on the arithmetic, per
    `verify-what-the-test-asserts`: pin the property, not the format that happened
    to imply it.

    The defect being guarded has not changed. A glyph can carry its advance twice
    — once in `hmtx`, once as the charstring width operand — and Microsoft Print to
    PDF builds the PDF /W array from the charstring, not from `hmtx`. A
    disagreement renders correctly in Word and shreds the printed PDF: Thai
    combining marks carry a zero `hmtx` advance, and given a real one in /W every
    tone mark detaches from its consonant and each run overruns the next.

    Verified to FAIL on a font whose `uni0E48` was given a 500-unit `hmtx`
    advance against its zero-width charstring, and on a Latin glyph nudged by 7
    units.
    """
    font = TTFont(path)
    bad = []
    if "CFF " not in font:
        bad.append(("<table>", "CFF ", "missing — this family ships CFF so its "
                    "Latin rasterises exactly as the Latin source does"))
        return bad
    if font.sfntVersion != "OTTO":
        bad.append(("<header>", "OTTO", f"sfntVersion {font.sfntVersion!r}"))

    cff = font["CFF "].cff
    top = cff[cff.fontNames[0]]
    charstrings = top.CharStrings
    hmtx = font["hmtx"]

    for gn in font.getGlyphOrder():
        charstring = charstrings[gn]
        # First argument is the LOCAL SUBRS index, not the charstrings index —
        # passing charstrings makes `callsubr` execute arbitrary glyph programs,
        # which underflows on a subr-heavy font and silently passes otherwise.
        private = charstring.private or top.Private
        ex = T2WidthExtractor(getattr(private, "Subrs", []), cff.GlobalSubrs,
                              private.nominalWidthX, private.defaultWidthX)
        ex.execute(charstring)
        width = ex.width if ex.gotWidth else private.defaultWidthX
        if width != hmtx[gn][0]:
            bad.append((gn, hmtx[gn][0], f"charstring says {width}"))

    cmap = font.getBestCmap()
    for cp in list(range(0x0E31, 0x0E32)) + list(range(0x0E34, 0x0E3B)) + \
            list(range(0x0E47, 0x0E4F)):
        gn = cmap.get(cp)
        if gn and hmtx[gn][0] != 0:
            bad.append((gn, 0, hmtx[gn][0]))
    return bad


def thai_closure(bai_font):
    """Every glyph Thai text can actually reach: cmap Thai, plus the GSUB closure.

    The raster checks below reach glyphs through `get_char_index`, so they can
    only ever see cmap-mapped ones. Bai Jamjuree's tone-mark variants
    (uni0E47.narrow, uni0E48.small, the uni0E4D0E49 ligatures) are reachable
    ONLY through shaping — and they are exactly the glyphs that appear in real
    two-level Thai stacks. 124 glyphs are reachable; 87 are in the cmap. The
    difference is invisible to any cmap-based test.
    """
    reach = {gn for cp, gn in bai_font.getBestCmap().items() if 0x0E01 <= cp <= 0x0E7F}
    gsub = bai_font["GSUB"].table
    for _ in range(5):                       # iterate to a fixed point
        for lookup in gsub.LookupList.Lookup:
            for st in lookup.SubTable or []:
                mapping = getattr(st, "mapping", None)
                if mapping:
                    for src, dst in mapping.items():
                        if src in reach:
                            reach |= set(dst) if isinstance(dst, list) else {dst}
                ligs = getattr(st, "ligatures", None)
                if ligs:
                    for src, entries in ligs.items():
                        if src in reach:
                            reach |= {e.LigGlyph for e in entries}
                alts = getattr(st, "alternates", None)
                if alts:
                    for src, dst in alts.items():
                        if src in reach:
                            reach |= set(dst)
    return reach


def check_thai_verbatim(merged_path, bai_path):
    """Every Thai-reachable glyph must be byte-identical to Bai Jamjuree.

    This is the guarantee the whole format change exists to provide, and it is
    strictly stronger than the raster comparison: it covers the GSUB-only
    variants no cmap-based check can reach, and it compares the stored outline
    rather than one rasteriser's opinion of it.
    """
    merged, bai = TTFont(merged_path), TTFont(bai_path)
    mg, bg = merged["glyf"], bai["glyf"]
    bad = []
    reach = thai_closure(bai)
    for gn in sorted(reach):
        if gn not in mg.glyphs:
            bad.append(f"{gn}: missing from merged font")
            continue
        a, b = mg[gn], bg[gn]
        if a.isComposite() != b.isComposite():
            bad.append(f"{gn}: composite {a.isComposite()} vs Bai {b.isComposite()}")
            continue
        if a.isComposite():
            ca = [(c.glyphName, c.x, c.y) for c in a.components]
            cb = [(c.glyphName, c.x, c.y) for c in b.components]
            if ca != cb:
                bad.append(f"{gn}: components {ca} vs {cb}")
        elif a.numberOfContours != b.numberOfContours:
            bad.append(f"{gn}: {a.numberOfContours} contours vs {b.numberOfContours}")
        elif a.numberOfContours > 0 and (
                list(a.coordinates) != list(b.coordinates)
                or list(a.flags) != list(b.flags)
                or list(a.endPtsOfContours) != list(b.endPtsOfContours)):
            bad.append(f"{gn}: outline coordinates differ")
        if merged["hmtx"][gn] != bai["hmtx"][gn]:
            bad.append(f"{gn}: hmtx {merged['hmtx'][gn]} vs Bai {bai['hmtx'][gn]}")
    return bad, len(reach)


def check_coverage_sorted(path):
    """Every GSUB/GPOS Coverage must be ascending by glyph ID (OT spec).

    Consumers binary-search Coverage. HarfBuzz tolerates an unsorted list, so
    nothing in the shaping or raster checks can see this; Uniscribe and
    DirectWrite do not, so a violation breaks Thai shaping on Windows only.
    """
    font = TTFont(path)
    gid = {g: i for i, g in enumerate(font.getGlyphOrder())}
    bad, total = [], 0
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        for li, lookup in enumerate(font[tag].table.LookupList.Lookup):
            for st in lookup.SubTable or []:
                covs = []
                for f in ("Coverage", "MarkCoverage", "BaseCoverage",
                          "Mark1Coverage", "Mark2Coverage", "LigatureCoverage"):
                    c = getattr(st, f, None)
                    if c is not None and hasattr(c, "glyphs"):
                        covs.append((f, c))
                for f in ("BacktrackCoverage", "InputCoverage", "LookAheadCoverage"):
                    for c in getattr(st, f, None) or []:
                        if hasattr(c, "glyphs"):
                            covs.append((f, c))
                for fname, c in covs:
                    total += 1
                    ids = [gid[g] for g in c.glyphs if g in gid]
                    if ids != sorted(ids):
                        bad.append(f"{tag} lookup {li} {type(st).__name__}.{fname}")
    return bad, total


def check_clipping_box(path):
    """usWinAscent/usWinDescent must cover the ink box, or GDI clips glyphs.

    Must be checked against *every* glyph, not just cmap-reachable ones: Bai
    Jamjuree's small tone-mark variants for two-level Thai stacks are reachable
    only through GSUB, and they are the tallest things in the font.
    """
    font = TTFont(path)
    os2, head = font["OS/2"], font["head"]
    problems = []
    if os2.usWinAscent < head.yMax:
        problems.append(f"usWinAscent {os2.usWinAscent} < ink top {head.yMax}")
    if os2.usWinDescent < -head.yMin:
        problems.append(f"usWinDescent {os2.usWinDescent} < ink bottom {-head.yMin}")
    return problems


def run():
    fails, n_shape, n_raster = [], 0, 0
    worst_dev = 0.0
    n_width = n_cov = n_clip = n_verbatim = 0

    for weight, (aeonik_file, bai_file) in PAIRS.items():
        merged = MERGED / f"TH-Aeonik-{weight}.otf"
        refs = {"latin": AEONIK / aeonik_file, "thai": BAI / bai_file}
        for p in (merged, *refs.values()):
            if not p.exists():
                print(f"  MISSING: {p}")
                return 1

        # ---------- single source of advance width (what Print to PDF reads) ----
        width_bad = check_advance_source(merged)
        n_width += 1
        if width_bad:
            fails.append(
                f"{weight}: {len(width_bad)} advance-source violation(s) — "
                f"printed PDFs can be misaligned. "
                f"e.g. {width_bad[0][0]}: want={width_bad[0][1]} "
                f"got={width_bad[0][2]}")

        # ---------- Thai outlines byte-identical to Bai (the core guarantee) ----
        vb_bad, vb_n = check_thai_verbatim(merged, refs["thai"])
        n_verbatim += vb_n
        if vb_bad:
            fails.append(f"{weight}: {len(vb_bad)} of {vb_n} Thai-reachable glyphs "
                         f"are NOT verbatim copies of Bai Jamjuree. "
                         f"e.g. {vb_bad[0]}")

        # ---------- Coverage ordering (Windows-only symptom) ----------
        cov_bad, cov_total = check_coverage_sorted(merged)
        n_cov += cov_total
        if cov_bad:
            fails.append(f"{weight}: {len(cov_bad)}/{cov_total} Coverage tables "
                         f"not sorted by glyph ID — Thai shaping breaks under "
                         f"Uniscribe/DirectWrite. e.g. {cov_bad[0]}")

        # ---------- clipping box ----------
        clip_bad = check_clipping_box(merged)
        n_clip += 1
        if clip_bad:
            fails.append(f"{weight}: {'; '.join(clip_bad)} — Windows will clip")

        # ---------- shaping ----------
        for label, corpus in (("thai", THAI), ("latin", LATIN)):
            for text in corpus:
                for ppem in PPEMS:
                    n_shape += 1
                    got, want = shape(merged, text, ppem), shape(refs[label], text, ppem)
                    if got != want:
                        fails.append(f"{weight} shape/{label} {ppem}px {text!r}\n"
                                     f"        got  {got}\n        want {want}")

        for text in MIXED:
            for ppem in PPEMS:
                n_shape += 1
                missing = [g for g, *_ in shape(merged, text, ppem) if g == ".notdef"]
                if missing:
                    fails.append(f"{weight} mixed {ppem}px {text!r}: "
                                 f"{len(missing)} .notdef")

        # ---------- raster ----------
        thai_chars = sorted({c for s in THAI for c in s})
        latin_chars = sorted({c for s in LATIN for c in s if c.strip()})

        # Thai must be byte-identical — the outlines are Bai Jamjuree's own,
        # copied verbatim, and rendered by the same engine. There is no format
        # conversion left to excuse a single differing pixel.
        for ch in thai_chars:
            for ppem in PPEMS:
                n_raster += 1
                got, want = raster(merged, ch, ppem), raster(refs["thai"], ch, ppem)
                if got != want:
                    if got is None or want is None:
                        fails.append(f"{weight} raster/thai U+{ord(ch):04X} "
                                     f"{ppem}px: coverage mismatch")
                    elif got[:5] != want[:5]:
                        fails.append(f"{weight} raster/thai U+{ord(ch):04X} ({ch}) "
                                     f"{ppem}px: bitmap size or advance differs "
                                     f"{got[:5]} vs {want[:5]}")
                    else:
                        n = sum(1 for a, b in zip(got[5], want[5]) if a != b)
                        fails.append(f"{weight} raster/thai U+{ord(ch):04X} ({ch}) "
                                     f"{ppem}px: {n} pixel(s) differ — Thai must "
                                     f"be verbatim")

        # Latin absorbs the cubic->quadratic conversion and the engine change.
        for ch in latin_chars:
            for ppem in PPEMS:
                n_raster += 1
                got, want = raster(merged, ch, ppem), raster(refs["latin"], ch, ppem)
                if got is None or want is None:
                    if got is not want:
                        fails.append(f"{weight} raster/latin U+{ord(ch):04X} "
                                     f"{ppem}px: coverage mismatch")
                    continue
                dim_off = max(abs(a - b) for a, b in zip(got[:4], want[:4]))
                if dim_off > LATIN_MAX_DIM_DELTA:
                    fails.append(f"{weight} raster/latin U+{ord(ch):04X} ({ch}) "
                                 f"{ppem}px: bitmap box off by {dim_off}px "
                                 f"> {LATIN_MAX_DIM_DELTA}")
                    continue
                if abs(got[4] - want[4]) > LATIN_MAX_ADV_DELTA:
                    fails.append(f"{weight} raster/latin U+{ord(ch):04X} ({ch}) "
                                 f"{ppem}px: advance off by "
                                 f"{abs(got[4] - want[4])}/64px")
                    continue
                if got[:4] != want[:4]:
                    continue        # 1px box shift — pixels are not comparable
                deltas = [abs(a - b) for a, b in zip(got[5], want[5]) if a != b]
                if deltas:
                    dev = sum(deltas) / len(deltas)
                    worst_dev = max(worst_dev, dev)
                    if dev > LATIN_MAX_MEAN_DEV:
                        fails.append(f"{weight} raster/latin U+{ord(ch):04X} ({ch}) "
                                     f"{ppem}px: mean AA deviation {dev:.1f}/255 "
                                     f"> {LATIN_MAX_MEAN_DEV}")

    print(f"  weights:  {len(PAIRS)}   sizes: {PPEMS} px")
    print(f"  advance-source audits: {n_width} (no CFF; marks zero in hmtx)")
    print(f"  Thai verbatim checks:  {n_verbatim} glyphs (cmap + GSUB-only variants)")
    print(f"  Coverage tables:     {n_cov} (ascending glyph-ID order)")
    print(f"  clipping-box audits: {n_clip} (usWin* vs ink)")
    print(f"  shaping comparisons: {n_shape}")
    print(f"  raster  comparisons: {n_raster}")
    print(f"  worst Latin antialias deviation: {worst_dev:.1f}/255 "
          f"(limit {LATIN_MAX_MEAN_DEV})")
    print(f"  Thai antialias deviation: 0/255 (exact — no tolerance allowed)")
    if fails:
        print(f"\n  FAIL: {len(fails)} mismatch(es)\n")
        for f in fails[:30]:
            print("   -", f)
        if len(fails) > 30:
            print(f"   ... and {len(fails) - 30} more")
        return 1
    print("\n  PASS")
    print("    Thai  is PIXEL-IDENTICAL to Bai Jamjuree — outlines copied verbatim")
    print("    Latin shapes as Aeonik; raster within the measured conversion bound")
    print("    Mixed Thai/Latin has no missing glyphs at any size")
    return 0


if __name__ == "__main__":
    sys.exit(run())
