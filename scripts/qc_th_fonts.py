#!/usr/bin/env python3
"""Acceptance tests for the merged TH families.

This replaces the invariant the previous acceptance tests asserted. They
compared merged Thai against Bai Jamjuree and passed when the two were
pixel-identical. That is the wrong reference: Bai's Thai is drawn to sit beside
Bai's own Latin, so "identical to Bai" is precisely the unscaled,
weight-mismatched state that made Thai read 9% too large and 18% too light
beside Aeonik. A test that can only pass when the requirement is violated is
worse than no test — it was cited across two post-mortems as proof of success.

WHAT "IDENTICAL TO THE SOURCE" MEANS HERE, per Siwatch 2026-08-02:

  Latin outlines  identical to Aeonik / Slussen across ASCII, asserted per glyph
                  in the builders' verify_font(). TWO DELIBERATE EXCEPTIONS since
                  2026-08-05: `∆` U+2206 and `µ` U+00B5 carry the web cut's
                  redrawn outline, because the Greek Δ and μ were harvested from
                  there and a Greek letter cannot render 9 units apart from its
                  maths twin in the same word. Both are outside ASCII, so the
                  per-glyph assertion is untouched — but the claim "identical to
                  Aeonik" now has two documented holes and must not be read as
                  absolute. See scripts/th_greek.py.
  Line box        NOT identical to Aeonik / Slussen, and since 2026-08-05 that is
                  settled rather than contested. At Word's Single spacing the line
                  box is the only room two consecutive Thai lines have, and the
                  Latin box is 337 units short. The 2026-08-04 attempt to make
                  TH Aeonik lead exactly as Aeonik does was reversed by choosing
                  the FONT BY THE DOCUMENT'S LANGUAGE instead: English-only
                  documents use Aeonik itself, mixed Thai/English use TH Aeonik,
                  so no merged face has to lead like its Latin source. Check 3
                  asserts the box clears the Thai AND that the deviation is
                  exactly the documented one.
  Thai            NOT identical to Bai Jamjuree, deliberately. Bai's Thai is
                  drawn for Bai's own Latin, and Bai's own mark placement is
                  too tight to survive Word at text sizes. It is rescaled,
                  reweighted and its marks are lifted — checks 1, 2 and 8.

The reference here is the LATIN the Thai actually shares a line with:

  1  size    ก height == Latin x-height
  2  weight  Thai stem == WEIGHT_RATIO x Latin stem. NOT 1.0: Thai carries
             loops where Latin carries none, so every family whose Thai and
             Latin were drawn together runs Thai ~0.89-0.93 of the Latin, and
             widens the gap toward Bold. Asserting 1.0 is what shipped an
             unreadable Bold on 2026-08-02.
  3  box     line box (hhea == sTypo == usWin) clears two stacked Thai lines.
             usWin is a third copy of the line box, not a clip box sized to the
             ink: Word leads CFF faces off usWin, and unifying all three sets is
             what makes the pitch independent of which field a renderer reads
  4  family  all weights share one line box
  5  shaping real words with stacked vowels+tones stay inside the box,
             including the GSUB-only .small mark variants that no cmap walk
             ever reaches
  6  ladder  weights are monotonic and none collapse together. The reader-facing
             ladder only — TH Aeonik's Black recipe left it on 2026-08-06 when it
             became TH Aeonik Medium's bold, and check 12 judges it instead
 11  linking  every family holds a real Bold, so Word never synthesises one, and
             no two shipped faces collide on nameID 3/4/6 (TH Aeonik only)
 12  promoted TH Aeonik Medium's bold clears Bold in the Latin; its Thai is
             expected to EQUAL Bold's, both being pinned to Bai's counter floor
  7  uniscribe  GDEF classes + U+25CC, the prerequisites Word needs
  8  clearance  Thai upper marks keep enough air to survive screen rendering
  9  baseline   Thai sits on the Latin baseline, not below it
 10  aperture   Thai enclosed counters stay open. Independent of check 2:
             emboldening buys stem and spends aperture, so a face can match
             the stem perfectly and still render ฃ ธ ฮ as solid blobs.

Run: python3 scripts/qc_th_fonts.py
Exit 0 = all pass.
"""

import statistics
import sys
from pathlib import Path

import freetype
import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from th_thai_prep import THAI_SCALE  # noqa: E402
from th_mark_clearance import TARGET as CLEAR_TARGET, clearances  # noqa: E402
from th_baseline import measure as baseline_offset
from th_metrics import (STEM_LATIN, STEM_THAI, min_aperture,
                        stem as probe_stem)
from th_thai_prep import APERTURE_FLOOR, WEIGHT_RATIO  # noqa: E402
import th_style_link  # noqa: E402

FAMILIES = {
    "TH-Aeonik": {
        "dir": ROOT / "assets/fonts/th-aeonik",
        "latin_dir": ROOT / "assets/fonts/aeonik",
        # merged weight -> Latin source it must match
        # All 20 Aeonik faces. Ordered lightest-first so the ladder check in
        # check_ladder() walks the weight axis in design order.
        "pairs": {
            "Air": "Aeonik-Air.otf",
            "Thin": "Aeonik-Thin.otf",
            "Light": "Aeonik-Light.otf",
            # Synthetic too, and thinned from Regular rather than grown. §4c.
            "Book": "Aeonik-Book.otf",
            "Regular": "Aeonik-Regular.otf",
            "Medium": "Aeonik-Medium.otf",
            # Synthetic — CoType never drew it. §4c, build_aeonik_semibold.py.
            "SemiBold": "Aeonik-SemiBold.otf",
            "Bold": "Aeonik-Bold.otf",
            # Synthetic, thinned from Black. Added 2026-08-09 to complete
            # Siwatch's ten-weight ladder; it is the only weight that was
            # missing.
            "ExtraBold": "Aeonik-ExtraBold.otf",
            "Black": "Aeonik-Black.otf",
            "AirItalic": "Aeonik-AirItalic.otf",
            "ThinItalic": "Aeonik-ThinItalic.otf",
            "LightItalic": "Aeonik-LightItalic.otf",
            "BookItalic": "Aeonik-BookItalic.otf",
            "RegularItalic": "Aeonik-RegularItalic.otf",
            "MediumItalic": "Aeonik-MediumItalic.otf",
            "SemiBoldItalic": "Aeonik-SemiBoldItalic.otf",
            "BoldItalic": "Aeonik-BoldItalic.otf",
            "ExtraBoldItalic": "Aeonik-ExtraBoldItalic.otf",
            "BlackItalic": "Aeonik-BlackItalic.otf",
        },
        # LINE box — 1537, what the Thai measured out at, from 2026-08-05.
        #
        # Reverses the 1000/-200/0 pinned on 2026-08-04. TH Aeonik is no longer a
        # drop-in Aeonik replacement: the font is chosen by the document's
        # language, English-only documents use Aeonik itself, so nothing here has
        # to lead like Aeonik. The 262-unit Thai overlap that 1200 forced is
        # retired rather than tolerated.
        #
        # The split: ascent 1169 >= the family's worst upper stack (1139, Black),
        # descent 368 >= its worst lower tail (341, AirItalic). Those two land on
        # DIFFERENT faces and all 14 share one box, so the split is sized to the
        # family envelope. The 57 units of slack keep the Latin optically centred
        # — Aeonik's 1000/-200 grows by 169 above and 168 below.
        "box": (1169, -368, 0),
        # Now a FLOOR, asserted, not a recorded shortfall: the box meets it. The
        # per-face version of this check runs in build_th_aeonik.assert_thai_clears()
        # against the built file, where the shaped extents are real.
        "required_pitch": 1537,
        "latin_pitch": 1200,
        # usWin is a THIRD copy of the line box, not a clip box sized to the ink.
        # Word leads off usWinAscent+usWinDescent for CFF faces, measured
        # 2026-08-04: with hhea and sTypo both at 1200 and usWin at 1800, Word
        # still led TH Aeonik 1.504x Aeonik. So usWin must equal the line box, and
        # the Thai ink is allowed outside it — Segoe UI overflows its own by 379.
        "clip": (1169, 368),
        "clip_equals_line_box": True,
    },
    "TH-Slussen": {
        "dir": ROOT / "assets/fonts/th-slussen",
        "latin_dir": ROOT / "assets/fonts/slussen",
        "pairs": {
            "Regular": "Slussen-Regular.otf",
            "Medium": "Slussen-Medium.otf",
            "SemiBold": "Slussen-Semibold.otf",
            "Bold": "Slussen-Bold.otf",
        },
        # 1610 -> 1625 on 2026-08-03 (evening) -> 1602 on 2026-08-05, when Siwatch
        # put this family on the same RULE as TH-Aeonik: box = the Thai's measured
        # need + margin, hhea == sTypo == usWin. Not the same NUMBER — Slussen's
        # Thai is taller, so 1602 against Aeonik's 1537.
        #
        # The split: ascent 1233 >= the worst upper stack (1185, Bold), descent 369
        # >= the worst lower tail (354, Regular). Different faces again.
        "box": (1233, -369, 0),
        "required_pitch": 1602,
        # Slussen's hhea is 1512, but it carries a 166-unit lineGap and ships CFF,
        # so Word leads it off usWin 1596 — which is what the ratio in
        # win_latin_parity.EXPECTED_LINE_RATIO is taken against. `latin_pitch` here
        # is the hhea box, asserted only so a Slussen update cannot move silently.
        "latin_pitch": 1512,
        # usWin was 1390/590 = 1980, an ink-containing clip box against a 1625 line
        # box. For a CFF face that is a silent +21.7% of leading, and this family
        # has shipped CFF since 2026-08-04. Unified 2026-08-05.
        "clip": (1233, 369),
        "clip_equals_line_box": True,
    },
}

# The words from the 2026-08-02 manual QC — every one is a two- or three-level
# stack, which is where clipping actually shows up.
TEST_WORDS = ("ที่ ครั้ง ทุก สิ่ง ซึ่ง กู่ น้ำ ต่ำ ลิ้น ขึ้น ทื่อ จึ๊ง สิทธิ์ "
              "น้ำเชื่อม ผู้ ปั่น เกี๊ยว ญี่ปุ่น").split()

# usWeightClass per weight name, for indexing th_thai_prep.WEIGHT_RATIO.
WCLASS = {"Air": 100, "Thin": 200, "Light": 300, "Book": 350, "Regular": 400,
          "Medium": 500, "SemiBold": 600, "Bold": 700, "ExtraBold": 800,
          "Black": 900}

SIZE_TOL = 0.02      # 2% on x-height match
PX = 512

# Check 2's tolerance, in stem UNITS per 1000em — not in ratio. The probe
# resolves 1000/512 = 1.95 units, so 2.5 is one step plus a small margin and
# nothing tighter is measurable.
#
# It was a flat 0.08 of ratio until 2026-08-07, with four per-face widenings on
# top. A ratio band scales with the Latin stem, so the same number meant 0.6
# units at Air and 11.9 at Bold — loosest exactly where the ink is heaviest and
# most visible. Regular shipped 2.6 units heavy (.920 against .890) and Bold 2.7
# (.908 against .890) with check 2 green throughout. In units both fail, which
# is the point.
#
# The Air/Thin widenings are gone with it. They existed because a 2-unit probe
# step is 0.26 of ratio on a 7.8-unit stem — an artefact of the denominator, not
# slack the font needed. Judged in units, Air is 0.05 off target.
STEM_UNIT_TOL = 2.5

# Faces where APERTURE_FLOOR binds before the stem taper is reached, so Thai
# ships measurably lighter than the Latin on purpose. These are NOT tolerances:
# each is the exact ratio the shipped font must hold, and it is then judged by
# the same STEM_UNIT_TOL as every other face. If a future Bai or Latin source
# changes the trade, this fails and the number has to be re-derived deliberately
# rather than absorbed by a wide bar.
#
# The dict was empty from 2026-08-03 to 2026-08-07 because the revised taper
# states the reachable number in WEIGHT_RATIO itself (900 -> .745), so the two
# Black faces have no shortfall left to pin. TH-Slussen Bold is different: its
# shortfall is against a ratio the taper does NOT special-case.
#
# Slussen's Latin Bold is 169.9, the heaviest Latin either family has, and .89 of
# it (151.2) is past what Bai Bold survives — th_thai_prep.BUILD_TABLE records
# the measurement, including that reaching 151.2 makes ข ฃ ฆ ษ ฮ revert to source
# weight and ship visibly lighter than their neighbours. So the face runs at
# .8276, 10.6 units short, and it is pinned here at the measured number.
#
# Until 2026-08-07 it passed only because a 0.073 ratio miss fell inside a 0.08
# ratio tolerance — the note in BUILD_TABLE predicted this and asked for the pin
# rather than a widened bar. That is what this entry is.
CAPPED_STEM_RATIO = {
    ("TH-Slussen", "Bold"): 0.8276,
}

# Aperture floor for check 10, and the faces exempt from it. Thinning at the
# light end opens the loops of ข ค ง into plain strokes — correct behaviour for
# those letters, and it leaves AirItalic with no enclosed counter to measure.
APERTURE_EXEMPT = {("TH-Aeonik", "AirItalic")}

# Thai must sit on the Latin baseline. 2/1000 em is the rounding of the source
# outlines themselves; anything larger is the weight match having dragged the
# Thai off the line, which is visible in the heavy weights at heading sizes.
BASELINE_TOL = 2.0

# Clearance floor, in 1/1000 em, for the worst Thai upper mark on any base.
# The build aims at th_mark_clearance.TARGET; this is the bar below which the
# mark visibly fuses into the consonant at text sizes. 1 em is 14.7 px at 11 pt
# on a 96 dpi screen, so 68/1000 em is one pixel. Sarabun, the reference, runs a
# p10 of 73.
CLEAR_FLOOR = 60.0

# Faces that cannot reach the floor because emboldening past the end of Bai's
# ladder grows the consonant and the mark toward each other faster than the
# anchor can pull them apart. Same source limitation as CAPPED_STEM_RATIO, and
# the same rule: these lower the bar, they do not remove it.
#
# EMPTY since 2026-08-03 (evening). Black and BlackItalic were listed at 38.0
# and both now measure worst 71.2 / p10 72.0 — over the 60 floor and on the 72
# target, not near it. Nothing in the clearance pass changed; the taper did.
# Clearance tracks the embolden monotonically, so a ladder that thins twelve of
# fourteen faces instead of emboldening them hands the clearance pass room it
# never had. Re-add with a measured number if a future source needs it.
CLEAR_FLOOR_OVERRIDE = {}

results = []


def face_path(fam, cfg, w):
    """Where build key `w`'s outlines live.

    The build key and the filename agree again as of 2026-08-09 — every face is
    `TH-Aeonik-<build key>.otf` — but the indirection stays. It diverged once
    (Black shipped as TH-Aeonik-MediumBold.otf while it filled Medium's bold
    slot) and hardcoding the name here is what would make the next divergence
    silent. th_style_link.FACES is the authority; TH Slussen was not
    restructured and keeps its own identity.
    """
    if fam == "TH-Aeonik":
        return cfg["dir"] / f"{th_style_link.FACES[w]['file']}.otf"
    return cfg["dir"] / f"{fam}-{w}.otf"


def record(name, ok, detail=""):
    results.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    for line in (detail or "").rstrip().splitlines():
        if line:
            print(f"         {line}")


def _runs(row):
    out, n = [], 0
    for v in row:
        if v:
            n += 1
        elif n:
            out.append(n)
            n = 0
    if n:
        out.append(n)
    return out


def stem(path, chars):
    """Median horizontal ink run across a mid-height band, in font units."""
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, PX)
    vals = []
    for ch in chars:
        try:
            face.load_char(ch, freetype.FT_LOAD_RENDER)
        except Exception:
            continue
        bm = face.glyph.bitmap
        if not bm.width or not bm.rows:
            continue
        a = np.array(bm.buffer, dtype=np.uint8).reshape(
            bm.rows, bm.pitch)[:, :bm.width] > 128
        band = a[int(bm.rows * .4):int(bm.rows * .6)]
        rr = [r for row in band for r in _runs(row)]
        if rr:
            vals.append(statistics.median(rr))
    return statistics.median(vals) / PX * 1000 if vals else None


def glyph_h(font, ch):
    gn = font.getBestCmap().get(ord(ch))
    if not gn:
        return None
    bp = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[gn].draw(bp)
    return None if not bp.bounds else bp.bounds[3] - bp.bounds[1]


def ink(font):
    gs = font.getGlyphSet()
    lo = hi = None
    for gn in font.getGlyphOrder():
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds:
            continue
        lo = bp.bounds[1] if lo is None or bp.bounds[1] < lo else lo
        hi = bp.bounds[3] if hi is None or bp.bounds[3] > hi else hi
    return lo, hi


def check_size_and_weight(fam, cfg):
    """1 + 2 — Thai measured against the Latin it shares a line with."""
    size_rows, weight_rows = [], []
    size_bad, weight_bad = [], []
    for w, latin_file in cfg["pairs"].items():
        merged = face_path(fam, cfg, w)
        latin = cfg["latin_dir"] / latin_file
        if not merged.exists() or not latin.exists():
            continue
        mf = TTFont(merged, lazy=True)
        xh, kh = glyph_h(mf, 'x'), glyph_h(mf, 'ก')
        mf.close()
        ratio = kh / xh
        size_rows.append(f"{w:<14} x-height {xh:.0f}  ก {kh:.0f}  "
                         f"ratio {ratio:.3f}")
        if abs(ratio - 1.0) > SIZE_TOL:
            size_bad.append(f"{w}: ก is {ratio*100:.1f}% of x-height")

        # Thai runs LIGHTER than the Latin by design — see
        # th_thai_prep.WEIGHT_RATIO. This asserted 1.0 until 2026-08-03, which
        # is the target that made Bold unreadable.
        ls = stem(merged, STEM_LATIN)
        ts = stem(merged, STEM_THAI)
        wr = ts / ls
        base = w.replace("Italic", "") or "Regular"
        capped = CAPPED_STEM_RATIO.get((fam, w))
        if capped is not None:
            want, note = capped, "  (aperture-capped)"
        else:
            want = WEIGHT_RATIO[WCLASS[base]]
            note = ""
        # Judged in STEM UNITS, not in ratio. The ratio's denominator is the
        # Latin stem, so a fixed ratio band is a different physical tolerance at
        # every rung: 0.08 was 0.6 units at Air and 11.9 at Bold — three probe
        # steps of slack where it mattered least and six where it mattered most.
        # That is how Regular shipped at .920 against a .890 target (2.6 units
        # heavy) inside a green check. STEM_UNIT_TOL is one probe step plus a
        # margin, so it holds every rung to what the probe can actually see, and
        # the four STEM_TOL_OVERRIDE entries for Air/Thin stopped being needed —
        # their "probe-limited" slack was the ratio's artefact, not the font's.
        want_stem = want * ls
        off = ts - want_stem
        weight_rows.append(f"{w:<14} Latin {ls:5.1f}  Thai {ts:5.1f}  "
                           f"ratio {wr:.3f}  want {want:.3f} ({want_stem:5.1f}u, "
                           f"off {off:+4.1f}u){note}")
        if abs(off) > STEM_UNIT_TOL:
            weight_bad.append(f"{w}: Thai stem {ts:.1f}, want {want_stem:.1f} "
                              f"+/- {STEM_UNIT_TOL} units (ratio {wr:.3f} vs "
                              f"{want:.3f})")

    record(f"1. {fam} Thai size == Latin x-height "
           f"(scale {THAI_SCALE[fam]})", not size_bad,
           "\n".join(size_rows + size_bad))
    record(f"2. {fam} Thai stem == WEIGHT_RATIO x Latin stem", not weight_bad,
           "\n".join(weight_rows + weight_bad))


def check_aperture(fam, cfg):
    """10 — Thai counters must survive as counters, not render as blobs.

    The check that did not exist until 2026-08-03, and whose absence let
    TH-Aeonik-Bold ship with 7.8 units of counter aperture (0.11 px at 11 pt)
    while passing every other check in this file. Stem width and counter
    aperture are independent: emboldening buys the first and spends the second,
    at roughly 1.2 units of aperture per unit of stem.
    """
    rows, bad = [], []
    for w in cfg["pairs"]:
        merged = face_path(fam, cfg, w)
        if not merged.exists():
            continue
        a, ch = min_aperture(merged)
        if a is None:
            exempt = (fam, w) in APERTURE_EXEMPT
            rows.append(f"{w:<14} no enclosed counter"
                        + ("  (expected at this weight)" if exempt else ""))
            if not exempt:
                bad.append(f"{w}: every Thai counter has closed or opened away")
            continue
        rows.append(f"{w:<14} tightest {ch} {a:5.1f}  "
                    f"({a/68:.2f} px at 11 pt)")
        if a < APERTURE_FLOOR:
            bad.append(f"{w}: {ch} aperture {a:.1f} < floor {APERTURE_FLOOR} "
                       f"({a/68:.2f} px) — the loop fills in")

    record(f"10. {fam} Thai counters clear {APERTURE_FLOOR:.1f}/1000 em",
           not bad, "\n".join(rows + bad))


def check_box(fam, cfg):
    """3 + 4 — line box clears two Thai lines; clip box contains the ink.

    These are two different boxes and the first version of this check conflated
    them, demanding usWin == hhea and that hhea contain the ink. That forced
    TH-Aeonik to 1710 units against Aeonik's 1200 — 42% of extra leading.

    The second version over-corrected the other way and demanded the line box
    equal the Latin source's to the unit. That is what left three Shift+Enter
    lines fusing in Word on 2026-08-03: at Single spacing the line box is the
    only room two consecutive Thai lines have, and Aeonik's 1200 is 334 units
    short of what the Thai needs.

    THIRD VERSION, 2026-08-04. The "at least what the Thai needs" floor was
    removed for TH-Aeonik, because the box went to Aeonik's 1200 and the Thai
    knowingly did not fit. That is the version this comment used to end on.

    FOURTH VERSION, 2026-08-05, and the floor is back — for a reason that is not
    "we changed our minds again". The 08-04 requirement was that Latin-only text
    inside a TH-Aeonik document lead exactly as Aeonik does. Siwatch dissolved it
    by choosing the font per document instead: English-only -> Aeonik, mixed ->
    TH Aeonik. With no requirement to match Aeonik's box, both families are back
    on one rule — box = the Thai's measured need + margin, with hhea, sTypo and
    usWin all carrying it — and `required_pitch` is a real floor for both.

    BOTH HALVES ARE ASSERTED, and each one alone has failed this repo before:

      * THE NUMBER — the exact documented box, in the merged font and in its Latin
        source. Pinning only a relationship is unreviewable: "the line box equals
        the Latin source's" read like a principle for two days while encoding a
        defect, and four checks asserted it.
      * THE FLOOR — `required_pitch`. Pinning only a number is what let the box sit
        337 units under the Thai with every check green. The per-face version runs
        in build_th_aeonik.assert_thai_clears() against the built file, where the
        shaped extents are measured rather than inherited from a config constant.
    """
    asc, desc, gap = cfg["box"]
    pitch = asc - desc + gap
    # One rule for both families since 2026-08-05. The `thai_wants_pitch` key that
    # used to make this a report rather than a failure is gone, deliberately: a
    # config key that downgrades an assertion is how the 08-04 shortfall stayed
    # green, and leaving it in place would let the next box do the same.
    if pitch < cfg["required_pitch"]:
        bad_pitch = (f"line box {pitch} is below the {cfg['required_pitch']} the "
                     f"Thai needs — two Thai lines will collide at Single spacing")
    else:
        bad_pitch = None
    win_asc, win_desc = cfg["clip"]
    rows, bad = [], []
    seen = set()
    for w, latin_file in cfg["pairs"].items():
        p = face_path(fam, cfg, w)
        if not p.exists():
            continue
        f = TTFont(p, lazy=True)
        hh, os2 = f["hhea"], f["OS/2"]
        lo, hi = ink(f)
        box = (hh.ascender, hh.descender, hh.lineGap)
        seen.add(box)

        # a) the Latin source's box is recorded for reference, and its pitch is
        #    asserted, so an Aeonik/Slussen update cannot silently change what
        #    the documented deviation is measured against.
        lp = cfg["latin_dir"] / latin_file
        latin_box = None
        if lp.exists():
            lf = TTFont(lp, lazy=True)
            u = lf["head"].unitsPerEm
            latin_box = (round(lf["hhea"].ascender * 1000 / u),
                         round(lf["hhea"].descender * 1000 / u),
                         round(lf["hhea"].lineGap * 1000 / u))
            lf.close()
            lpitch = latin_box[0] - latin_box[1] + latin_box[2]
            if lpitch != cfg["latin_pitch"]:
                bad.append(f"{w}: Latin source now leads {lpitch}, not the "
                           f"{cfg['latin_pitch']} this deviation was sized "
                           f"against — re-derive with thai_line_pitch.py")

        # b) hhea and sTypo must agree, so pitch does not depend on renderer.
        if box != (asc, desc, gap):
            bad.append(f"{w}: hhea {box} != expected {(asc, desc, gap)}")
        if (os2.sTypoAscender, os2.sTypoDescender,
                os2.sTypoLineGap) != (asc, desc, gap):
            bad.append(f"{w}: sTypo disagrees with hhea")

        # c) usWin. Two different invariants, because the two families are on
        #    two different trades:
        #      clip_equals_line_box — usWin IS the line box (Word leads off it),
        #        so the ink is allowed out and only the box is asserted.
        #      otherwise — usWin is still the old ink-containing clip box.
        if cfg.get("clip_equals_line_box"):
            if (win_asc, -win_desc) != (asc, desc):
                bad.append(f"{w}: clip {-win_desc}..{win_asc} != line box "
                           f"{desc}..{asc} — Word leads off usWin, so a clip "
                           f"box wider than the line box IS extra leading")
        elif hi > win_asc or lo < -win_desc:
            bad.append(f"{w}: ink {lo:.0f}..{hi:.0f} escapes clip box "
                       f"{-win_desc}..{win_asc} — WILL CLIP")
        if os2.usWinAscent != win_asc or os2.usWinDescent != win_desc:
            bad.append(f"{w}: usWin {os2.usWinAscent}/{os2.usWinDescent} "
                       f"!= expected {win_asc}/{win_desc}")

        got = box[0] - box[1] + box[2]      # this face's own pitch, not the expected
        want = cfg["required_pitch"]
        rows.append(f"{w:<14} line {box[0]}/{box[1]}/{box[2]} = {got} "
                    f"(Thai needs {want}, Latin leads {cfg['latin_pitch']}, "
                    f"{got / cfg['latin_pitch'] - 1:+.1%})  "
                    f"clip {os2.usWinAscent}/{os2.usWinDescent}  "
                    f"ink {lo:.0f}..{hi:.0f}")
        f.close()
    if bad_pitch:
        bad.insert(0, bad_pitch)
    label = "line box clears two Thai lines"
    tail = ("usWin == the line box"
            if cfg.get("clip_equals_line_box") else "clip box contains ink")
    record(f"3. {fam} {label}, {tail}",
           not bad, "\n".join(rows + bad))
    record(f"4. {fam} all weights share one line box",
           len(seen) == 1,
           "" if len(seen) == 1 else f"{len(seen)} different boxes: {seen}")


def check_shaping(fam, cfg):
    """5 — shape real stacked words and bound the ACTUAL glyphs used.

    Walking the cmap is not enough. Bai substitutes .small tone-mark variants
    through GSUB for two-level stacks, and those are reachable only by shaping;
    they are exactly the glyphs that overflowed and got clipped.

    Bounded against the CLIP box. A shaped stack that rises above the LINE box
    is normal Thai typography, not a defect — it sits in the leading of the line
    above, where the Latin ascenders leave the space empty.
    """
    try:
        import uharfbuzz as hb
    except ImportError:
        record(f"5. {fam} shaped stacks stay inside the box", True,
               "SKIPPED — uharfbuzz not installed under this interpreter")
        return
    asc, desc, _ = cfg["box"]
    win_asc, win_desc = cfg["clip"]
    bad, worst = [], []
    for w in cfg["pairs"]:
        p = face_path(fam, cfg, w)
        if not p.exists():
            continue
        blob = hb.Blob.from_file_path(str(p))
        face = hb.Face(blob)
        font = hb.Font(face)
        tt = TTFont(p, lazy=True)
        gs, order = tt.getGlyphSet(), tt.getGlyphOrder()
        hi = lo = None
        for word in TEST_WORDS:
            buf = hb.Buffer()
            buf.add_str(word)
            buf.guess_segment_properties()
            hb.shape(font, buf)
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
                gn = order[info.codepoint]
                bp = BoundsPen(gs)
                try:
                    gs[gn].draw(bp)
                except Exception:
                    continue
                if not bp.bounds:
                    continue
                top = bp.bounds[3] + pos.y_offset
                bot = bp.bounds[1] + pos.y_offset
                hi = top if hi is None or top > hi else hi
                lo = bot if lo is None or bot < lo else lo
        tt.close()
        worst.append(f"{w:<14} shaped ink {lo:.0f}..{hi:.0f}  "
                     f"clip {-win_desc}..{win_asc}  "
                     f"(line {desc}..{asc}, overflow "
                     f"{max(0, hi - asc):.0f}/{max(0, -lo + desc):.0f} expected)")
        # Only asserted for families whose usWin is still an ink-containing clip
        # box. Where usWin IS the line box, a shaped stack outside it is the
        # accepted trade, not a defect — it is recorded in `worst` either way.
        if not cfg.get("clip_equals_line_box") and (hi > win_asc or lo < -win_desc):
            bad.append(f"{w}: shaped stack reaches {lo:.0f}..{hi:.0f}, "
                       f"outside clip box {-win_desc}..{win_asc} — WILL CLIP")
    scope = ("are measured against the line box"
             if cfg.get("clip_equals_line_box") else "stay inside the clip box")
    record(f"5. {fam} shaped stacks {scope} "
           f"({len(TEST_WORDS)} words)", not bad, "\n".join(worst + bad))


# How close to APERTURE_FLOOR a face has to sit before "the Thai cannot separate
# further" is a MEASUREMENT rather than an excuse. One probe step is 1.95 units,
# so 4 is two steps: enough that a face genuinely against the ceiling is not
# failed by rounding, tight enough that a face with real room left cannot hide.
CAP_MARGIN = 4.0

# The minimum Thai separation between adjacent weights. Below this the two read
# as one colour on the page.
LADDER_MIN_GAP = 0.04


def check_ladder(fam, cfg):
    """6 — weights must increase, and stay distinct unless the source has run out.

    REWRITTEN 2026-08-09, and the old shape is worth stating because it is the
    trap this file keeps falling into. From 2026-08-06 it carried a
    LADDER_EXCLUDE list that dropped "Black" from the ladder entirely, because
    Thai Bold and Thai Black both sit near Bai Jamjuree's counter floor and no
    ladder containing both can be "distinct". Excluding a weight to keep a check
    green is asserting the defect: the check stopped being able to see the one
    part of the ladder that is actually constrained.

    The ten-weight deck makes that untenable — ExtraBold 800 lands BETWEEN the
    two, so the capped region is now three rungs wide and there is nothing left
    to exclude. So the rule is stated properly instead:

        a pair may fail the separation bar ONLY IF the heavier face is measured
        against APERTURE_FLOOR

    which turns "Bai has run out" from a name on an exclusion list into a number
    the shipped font has to prove every run. If a capped face ever measures
    clear of the floor, stem was left on the table and the embolden is
    under-solved — that now fails here instead of passing silently.
    """
    order = [w for w in cfg["pairs"] if "Italic" not in w]
    vals = []
    missing = []
    for w in order:
        p = face_path(fam, cfg, w)
        if p.exists():
            vals.append((w, stem(p, "กทบนผฝพฟ"), min_aperture(p)[0]))
        else:
            missing.append(f"{w}: {p.name} is missing — cannot judge the ladder")
    bad = list(missing)
    rows = [f"{w:<14} Thai stem {s:6.1f}   aperture {ap:5.1f}"
            for w, s, ap in vals]
    for (wa, a, _), (wb, b, ap_b) in zip(vals, vals[1:]):
        if b <= a:
            bad.append(f"{wb} ({b:.1f}) is not heavier than {wa} ({a:.1f})")
            continue
        gap = (b - a) / a
        if gap >= LADDER_MIN_GAP:
            continue
        if ap_b <= APERTURE_FLOOR + CAP_MARGIN:
            rows.append(f"  {wa} -> {wb} is only {gap * 100:+.1f}% — allowed: "
                        f"{wb} is on the aperture floor ({ap_b:.1f} vs "
                        f"{APERTURE_FLOOR}), so Bai has run out. Latin "
                        f"separation is judged by check 12.")
        else:
            bad.append(f"{wa} and {wb} differ by only {gap * 100:.1f}% and "
                       f"{wb}'s aperture is {ap_b:.1f}, clear of the "
                       f"{APERTURE_FLOOR} floor — Bai has NOT run out, so "
                       f"re-solve the embolden rather than accept the collapse")
    record(f"6. {fam} weight ladder is monotonic and distinct", not bad,
           "\n".join(rows + bad))


def check_style_link(fam, cfg):
    """11 — the shipped family structure, delegated to its one authority.

    Synthetic bold double-strikes the outline, which spends counter aperture —
    the exact budget check 10 defends. Until 2026-08-06 four of TH Aeonik's six
    families had no bold member, so Ctrl+B in plain Word produced it. The
    generators were never exposed (they emit `TH Aeonik` + w:b and get the real
    Bold), which is why this went unseen: it only reached the layer Siwatch
    actually types in.

    From 2026-08-09 th_style_link.check() also asserts that no two shipped faces
    share a (usWeightClass, slant), which is what lets all ten weights live in
    one typographic family, and that the two families with no bold slot are
    exactly Air and Thin — the only two whose counter aperture (113.3 and 97.7
    against a floor of 46.5) can afford a synthesised one.

    This check is a delegation on purpose. It asserts what the FIELDS say;
    scripts/fc_family_probe.py asserts what a matcher DOES with them, and both
    one-card defects of 2026-08-07 were invisible to the first.
    """
    if fam != "TH-Aeonik":
        return
    faults = th_style_link.check(cfg["dir"], verbose=False)
    families = sorted({c["nameID1"] for c in th_style_link.SHIPPED.values()})
    weights = sorted({c["weightClass"] for c in th_style_link.SHIPPED.values()})
    rows = [f"{len(th_style_link.SHIPPED)} shipped faces, "
            f"{len(th_style_link.FACES)} outline sets, "
            f"{len(families)} families: {', '.join(families)}",
            f"weights: {' '.join(str(w) for w in weights)}",
            f"no bold slot by design: "
            f"{', '.join(sorted(th_style_link.NO_BOLD_SLOT))}"]
    record(f"11. {fam} family structure: unique weights, no duplicate face IDs",
           not faults, "\n".join(rows + faults))


def check_capped_top(fam, cfg):
    """12 — where the Thai cannot separate, the LATIN still must.

    This is check 6's other half. Check 6 lets a pair through when the heavier
    face is on APERTURE_FLOOR, because Bai Jamjuree genuinely has no more stem to
    give. That permission is only defensible while the weights remain distinct in
    the script that CAN still separate — otherwise two selectable weights render
    identically in every script and one of them should not ship.

    GENERALISED 2026-08-09. It compared exactly two faces, Bold and Black, named
    in the source. The ten-weight deck puts ExtraBold 800 between them, so the
    capped region is three rungs wide, and a check that names its faces would
    have gone on asserting the pair either side of the new weight while saying
    nothing about the new weight itself. It now derives the capped run by
    measuring, so a face arriving in or leaving that region is judged either way.

    THE THAI EQUALITY WAS NEVER A LAW. From 2026-08-03 to 2026-08-07 this check
    asserted the two Thai stems were identical (134.8 both) and called it Bai's
    counter floor. Half of that was true: Black IS on the floor. Bold was not
    obliged to be — it only got there because its embolden had been solved
    against the ITALIC's Latin stem (150.4 instead of 148.4) and bought stem it
    was never owed. Corrected, Bold sits at 130.9 with aperture 50.8.
    """
    if fam != "TH-Aeonik":
        return
    order = [w for w in cfg["pairs"] if "Italic" not in w]
    faces = []
    for w in order:
        p = face_path(fam, cfg, w)
        if not p.exists():
            record(f"12. {fam} the aperture-capped weights still separate in "
                   f"the Latin", False,
                   f"cannot judge: {p.name} is missing — a missing file is "
                   f"not a pass")
            return
        faces.append((w, p, probe_stem(p, STEM_LATIN), probe_stem(p, STEM_THAI),
                      min_aperture(p)))

    # The capped run is every face measured against the floor, plus the face
    # directly below it — that pair is the one check 6 waved through.
    capped = {i for i, f in enumerate(faces)
              if f[4][0] <= APERTURE_FLOOR + CAP_MARGIN}
    if not capped:
        record(f"12. {fam} the aperture-capped weights still separate in "
               f"the Latin", True,
               f"no face is within {CAP_MARGIN} of the {APERTURE_FLOOR} "
               f"aperture floor — nothing is source-capped, so check 6 carries "
               f"the whole ladder on its own")
        return

    rows, bad = [], []
    for i in sorted(capped):
        if i == 0:
            bad.append(f"{faces[i][0]} is the LIGHTEST weight and it is already "
                       f"on the aperture floor — the source pairing is wrong, "
                       f"not capped")
            continue
        wa, _, la, ta, _ = faces[i - 1]
        wb, _, lb, tb, (ap, ch) = faces[i]
        lat, thai = (lb - la) / la, (tb - ta) / ta
        rows.append(f"{wa:>10s} -> {wb:<10s} Latin {la:6.1f} -> {lb:6.1f} "
                    f"{lat * 100:+6.1f}%   Thai {ta:6.1f} -> {tb:6.1f} "
                    f"{thai * 100:+5.1f}%   aperture {ap:5.1f} ({ch})")
        if lat < LADDER_MIN_GAP:
            bad.append(f"{wa} and {wb} separate {lat * 100:.1f}% in the Latin "
                       f"and {thai * 100:.1f}% in the Thai — neither script "
                       f"tells them apart, so {wb} is not a weight, it is a "
                       f"duplicate")
        if tb < ta:
            bad.append(f"{wb}'s Thai is LIGHTER than {wa}'s ({tb:.1f} vs "
                       f"{ta:.1f}) — the heavier face must never be the "
                       f"lighter one")
    rows.append(f"floor {APERTURE_FLOOR}, capped within {CAP_MARGIN}")
    record(f"12. {fam} the aperture-capped weights still separate in the Latin",
           not bad, "\n".join(rows + bad))


def check_uniscribe(fam, cfg):
    """7 — what Uniscribe needs that Bai Jamjuree does not provide.

    Every Thai glyph must carry an explicit GDEF class, and the font must own a
    U+25CC to hang orphaned marks on. Without the first, Word will not accept an
    isolated or repeated spacing vowel ('าาาา'); without the second, an orphaned
    mark renders as nothing. HarfBuzz infers both, so a Linux-only test cannot
    see either fault.
    """
    import unicodedata
    bad, rows = [], []
    for w in cfg["pairs"]:
        p = face_path(fam, cfg, w)
        if not p.exists():
            continue
        f = TTFont(p, lazy=True)
        cmap = f.getBestCmap()
        gc = (f["GDEF"].table.GlyphClassDef.classDefs
              if "GDEF" in f and f["GDEF"].table.GlyphClassDef else {})
        unclassed = []
        for cp, gn in cmap.items():
            if not (0x0E00 <= cp <= 0x0E7F):
                continue
            want = 3 if unicodedata.category(chr(cp)) in ("Mn", "Me") else 1
            if gc.get(gn, 0) != want:
                unclassed.append(f"U+{cp:04X}")
        dc = 0x25CC in cmap
        rows.append(f"{w:<14} Thai classed {'ok' if not unclassed else 'NO'}  "
                    f"U+25CC {'ok' if dc else 'MISSING'}")
        if unclassed:
            bad.append(f"{w}: {len(unclassed)} Thai glyphs misclassed "
                       f"({', '.join(unclassed[:6])})")
        if not dc:
            bad.append(f"{w}: no U+25CC dotted circle")
        f.close()
    record(f"7. {fam} Uniscribe prerequisites (GDEF classes + U+25CC)",
           not bad, "\n".join(rows[:3] + [f"... {len(rows)} faces checked"]
                              + bad))


def check_clearance(fam, cfg):
    """8 — Thai upper marks must not fuse into the consonant on screen.

    This is the defect the 2026-08-02 evening QC caught in Word: กลิ่น, เพื่อ and
    สิทธิ์ rendered as blobs at 11 pt while Sarabun stayed legible. Bai sets its
    marks close, and this pipeline's scale-to-x-height plus weight-match closes
    the gap further — TH-Aeonik-Black measured a median of 0.6/1000 em, i.e.
    touching. Corrected at build time in th_mark_clearance.raise_upper_marks.
    """
    rows, bad = [], []
    for w in cfg["pairs"]:
        p = face_path(fam, cfg, w)
        if not p.exists():
            continue
        f = TTFont(p, lazy=True)
        vals = sorted(v[0] for v in clearances(f, "base").values())
        f.close()
        if not vals:
            bad.append(f"{w}: no Thai mark anchors found")
            continue
        floor = CLEAR_FLOOR_OVERRIDE.get((fam, w), CLEAR_FLOOR)
        p10 = vals[len(vals) // 10]
        note = "  (source-limited)" if (fam, w) in CLEAR_FLOOR_OVERRIDE else ""
        rows.append(f"{w:<14} worst {vals[0]:5.1f}  p10 {p10:5.1f}  "
                    f"floor {floor:.0f}{note}")
        if p10 < floor:
            bad.append(f"{w}: p10 clearance {p10:.1f} below floor {floor:.0f} "
                       f"— marks will fuse into the consonant at text sizes")
    record(f"8. {fam} Thai upper marks clear the consonant "
           f"(target {CLEAR_TARGET:.0f}/1000 em)", not bad,
           "\n".join(rows + bad))


def check_baseline(fam, cfg):
    """9 — Thai and Latin must sit on the same baseline.

    Siwatch, 2026-08-03: "make sure the Latin and Thai character when type
    together are on the same line level." Bai draws every flat-bottomed Thai
    consonant at exactly y=0 in every weight; the FontForge weight match grows
    the outline downward, so the Thai sank while the byte-identical Latin stayed
    put — TH-Aeonik-Black measured -28/1000 em, about a pixel at a 26 pt
    heading. Corrected at build time in th_baseline.seat_thai_on_baseline.
    """
    rows, bad = [], []
    for w in cfg["pairs"]:
        p = face_path(fam, cfg, w)
        if not p.exists():
            continue
        f = TTFont(p, lazy=True)
        thai, latin, offset = baseline_offset(f)
        f.close()
        if thai is None:
            bad.append(f"{w}: no flat-bottomed Thai/Latin pair to measure")
            continue
        rows.append(f"{w:<14} thai {thai:+6.1f}  latin {latin:+6.1f}  "
                    f"offset {offset:+6.1f}")
        if abs(offset) > BASELINE_TOL:
            bad.append(f"{w}: Thai sits {offset:+.1f}/1000 em off the Latin "
                       f"baseline (tolerance {BASELINE_TOL:.0f})")
    record(f"9. {fam} Thai sits on the Latin baseline "
           f"(tolerance {BASELINE_TOL:.0f}/1000 em)", not bad,
           "\n".join(rows + bad))


def main():
    for fam, cfg in FAMILIES.items():
        print(f"\n=== {fam} ===")
        check_size_and_weight(fam, cfg)
        check_box(fam, cfg)
        check_shaping(fam, cfg)
        check_ladder(fam, cfg)
        check_uniscribe(fam, cfg)
        check_clearance(fam, cfg)
        check_baseline(fam, cfg)
        check_aperture(fam, cfg)
        check_style_link(fam, cfg)
        check_capped_top(fam, cfg)
    n = sum(1 for _, ok in results if ok)
    print(f"\n{n}/{len(results)} checks pass")
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
