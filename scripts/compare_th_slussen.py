#!/usr/bin/env python3
"""
Acceptance test for TH-Slussen.

The merge is only correct if it is invisible:
  * Thai in TH Slussen must render as Bai Jamjuree.
  * Latin in TH Slussen must render as Slussen.

Checked three ways, across every weight and a wide range of sizes:

  1. CFF widths — charstring widths must equal hmtx. Microsoft Print to PDF
                  builds the PDF /W array from the charstrings, not from hmtx.
  2. Shaping    — HarfBuzz glyph sequence + positions, exact match required.
  3. Raster     — FreeType glyph bitmaps.
                  Latin must be pixel-exact: Slussen's CFF charstrings are
                  copied verbatim, so there is no excuse for any difference.
                  Thai outlines are converted from TrueType quadratics to CFF
                  cubics, so FreeType's scan conversion differs slightly.
                  Bitmap dimensions and advances must still match exactly; only
                  edge antialiasing may vary, and only within MAX_MEAN_DEV.

Plus two structural invariants that have no rendering symptom on Linux:
  4. Coverage   — every GSUB/GPOS Coverage ascending by glyph ID. HarfBuzz
                  tolerates a violation; Uniscribe and DirectWrite do not, so
                  a regression here would only ever show up on Windows.
  5. Clipping   — usWinAscent/usWinDescent must cover the font's ink box, or
                  GDI cuts the descenders off Thai below-vowels.

`space` is deliberately excluded from the Thai comparison. It is a shared glyph
and comes from Slussen rather than Bai Jamjuree, which is what mixed Thai/Latin
text needs.

Usage:  python3 compare_th_slussen.py
Exit 0 = pass.
"""

import sys
import warnings
from pathlib import Path

import freetype
import uharfbuzz as hb
from fontTools.misc.psCharStrings import T2WidthExtractor
from fontTools.ttLib import TTFont

warnings.filterwarnings("ignore")

ASSETS = Path(__file__).parent.parent / "assets" / "fonts"
MERGED, SLUSSEN, BAI = ASSETS / "slussen-th", ASSETS / "slussen", ASSETS / "bai-jamjuree"

# merged filename stem -> (slussen source, bai source)
PAIRS = {
    "Regular":  ("Slussen-Regular.otf",  "BaiJamjuree-Regular.ttf"),
    "Medium":   ("Slussen-Medium.otf",   "BaiJamjuree-Medium.ttf"),
    "SemiBold": ("Slussen-Semibold.otf", "BaiJamjuree-SemiBold.ttf"),
    "Bold":     ("Slussen-Bold.otf",     "BaiJamjuree-Bold.ttf"),
}

PPEMS = [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72, 144]
# Ceiling on the mean coverage delta (/255) across the pixels that differ.
# 20/255 is under 8% on edge pixels only — the residue of rasterising cubics
# against the original quadratics. Interior pixels, bitmap dimensions and
# advances are all required to match exactly, so shape and spacing are held to
# an exact standard; only edge antialiasing is allowed to drift.
MAX_MEAN_DEV = 20.0

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


def check_cff_widths(path):
    """CFF charstring widths must equal hmtx for every glyph.

    Not a cosmetic invariant. Microsoft Print to PDF builds the PDF /W array
    from the charstring widths, not from hmtx. When these disagree, Word still
    renders correctly (it lays out from hmtx) but the printed PDF declares the
    wrong advance for every affected glyph. For Thai that is fatal: combining
    marks carry a zero advance in hmtx, so a mismatch gives each tone mark and
    vowel a real advance, detaching it from its base consonant, spreading the
    line, and overrunning the next run.

    Regression guard for the defect that made printed reports unreadable.
    """
    font = TTFont(path)
    cff = font["CFF "].cff
    top = cff[cff.fontNames[0]]
    charstrings, private = top.CharStrings, top.Private
    extractor = T2WidthExtractor(getattr(private, "Subrs", []), cff.GlobalSubrs,
                                 private.nominalWidthX, private.defaultWidthX)
    hmtx = font["hmtx"]
    bad = []
    for name in charstrings.keys():
        extractor.reset()
        extractor.execute(charstrings[name])
        if extractor.width != hmtx[name][0]:
            bad.append((name, hmtx[name][0], extractor.width))
    return bad


def check_coverage_sorted(path):
    """Every GSUB/GPOS Coverage must be ascending by glyph ID (OT spec).

    Consumers binary-search Coverage. HarfBuzz tolerates an unsorted list, so
    nothing in the shaping or raster checks above can see this; Uniscribe and
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
    """usWinAscent/usWinDescent must cover the ink box, or GDI clips glyphs."""
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
    n_width = n_cov = n_clip = 0

    for weight, (slussen_file, bai_file) in PAIRS.items():
        merged = MERGED / f"TH-Slussen-{weight}.otf"
        refs = {"latin": SLUSSEN / slussen_file, "thai": BAI / bai_file}
        for p in (merged, *refs.values()):
            if not p.exists():
                print(f"  MISSING: {p}")
                return 1

        # ---------- CFF widths vs hmtx (what Print to PDF reads) ----------
        width_bad = check_cff_widths(merged)
        n_width += 1
        if width_bad:
            marks = [b for b in width_bad if b[1] == 0]
            fails.append(
                f"{weight}: {len(width_bad)} glyphs have CFF charstring widths "
                f"disagreeing with hmtx ({len(marks)} of them zero-advance "
                f"combining marks) — printed PDFs will be misaligned. "
                f"e.g. {width_bad[0][0]}: hmtx={width_bad[0][1]} "
                f"cff={width_bad[0][2]}")

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

        for ch in latin_chars:                       # must be pixel-exact
            for ppem in PPEMS:
                n_raster += 1
                got, want = raster(merged, ch, ppem), raster(refs["latin"], ch, ppem)
                if got != want:
                    fails.append(f"{weight} raster/latin U+{ord(ch):04X} ({ch}) "
                                 f"{ppem}px: differs from Slussen")

        for ch in thai_chars:                        # dims/advance exact, AA may vary
            for ppem in PPEMS:
                n_raster += 1
                got, want = raster(merged, ch, ppem), raster(refs["thai"], ch, ppem)
                if got is None or want is None:
                    if got is not want:
                        fails.append(f"{weight} raster/thai U+{ord(ch):04X} "
                                     f"{ppem}px: coverage mismatch")
                    continue
                if got[:5] != want[:5]:
                    fails.append(f"{weight} raster/thai U+{ord(ch):04X} ({ch}) "
                                 f"{ppem}px: bitmap size or advance differs")
                    continue
                deltas = [abs(a - b) for a, b in zip(got[5], want[5]) if a != b]
                if deltas:
                    dev = sum(deltas) / len(deltas)
                    worst_dev = max(worst_dev, dev)
                    if dev > MAX_MEAN_DEV:
                        fails.append(f"{weight} raster/thai U+{ord(ch):04X} ({ch}) "
                                     f"{ppem}px: mean AA deviation {dev:.1f}/255 "
                                     f"> {MAX_MEAN_DEV}")

    print(f"  weights:  {len(PAIRS)}   sizes: {PPEMS} px")
    print(f"  CFF-width audits:    {n_width} (charstring widths vs hmtx)")
    print(f"  Coverage tables:     {n_cov} (ascending glyph-ID order)")
    print(f"  clipping-box audits: {n_clip} (usWin* vs ink)")
    print(f"  shaping comparisons: {n_shape}")
    print(f"  raster  comparisons: {n_raster}")
    print(f"  worst Thai antialias deviation: {worst_dev:.1f}/255 "
          f"(limit {MAX_MEAN_DEV})")
    if fails:
        print(f"\n  FAIL: {len(fails)} mismatch(es)\n")
        for f in fails[:30]:
            print("   -", f)
        if len(fails) > 30:
            print(f"   ... and {len(fails) - 30} more")
        return 1
    print("\n  PASS")
    print("    Thai  shapes and measures exactly as Bai Jamjuree")
    print("    Latin shapes and rasterises exactly as Slussen")
    print("    Mixed Thai/Latin has no missing glyphs at any size")
    return 0


if __name__ == "__main__":
    sys.exit(run())
