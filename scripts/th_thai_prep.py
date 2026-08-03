#!/usr/bin/env python3
"""Prepare Bai Jamjuree for merging into a Latin family.

Two corrections are applied here that the earlier builds did not make, and
between them they are the root cause of every defect found in the 2026-08-02
manual QC:

1. SCALE. Bai's Thai is drawn to sit beside Bai's own Latin. Dropped unscaled
   into Aeonik or Slussen it is too big: ก is 558 units against an Aeonik
   x-height of 510, so Thai reads 9% larger than the Latin it shares a line
   with. Each family therefore gets its own factor, chosen so ก matches the
   Latin x-height exactly.

2. WEIGHT. Stem width is a property of the *source* weight, and Bai's weight
   ladder does not line up with Aeonik's or Slussen's. Bai Regular next to
   Aeonik Regular leaves Thai 18% too light. The right source for Aeonik
   Regular is Bai *Medium*; the correct pairing per weight is in BUILD_TABLE
   below, with any residual closed by synthetic emboldening.

   Corrected 2026-08-03: matching the Latin stem 1:1 is the WRONG target and
   it is what made Bold unreadable. See WEIGHT_RATIO and APERTURE_FLOOR.

The old build asserted the opposite of (1) — that merged Thai should be
pixel-identical to Bai — and passed. That test enforced the defect. See
compare_th_aeonik.py for what replaced it.

All stem figures are median horizontal run length across a mid-height band,
measured at 512 px/em; see scripts/measure_stems.py.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem

ROOT = Path(__file__).parent.parent
BAI = ROOT / "assets" / "fonts" / "bai-jamjuree"

# ก height / Latin x-height. Aeonik x-height 510, Slussen 540, Bai ก 558.
THAI_SCALE = {
    "TH-Aeonik": 0.914,
    "TH-Slussen": 0.968,
}

# Thai stem as a fraction of the Latin stem it sits beside, by usWeightClass.
#
# The 2026-08-02 build targeted 1.0 — Thai stem == Latin stem. That is wrong,
# and it is the whole reason Bold shipped unreadable. Thai carries enclosed
# loops (ก ถ ภ ศ ฃ ธ ฮ) where Latin carries none, so matching stems makes Thai
# read heavier than the Latin AND spends the counter budget on stem width.
#
# These figures are not invented. They are measured from families whose Thai
# and Latin were drawn together by one designer, at 512 px/em on 2026-08-03:
#
#   Sarabun        ExtraLight .931  Regular .915  Medium .911  Bold .897
#                  SemiBold   .885  ExtraBold .890
#   Leelawadee     Regular    .921  Bold    .887
#   Leelawadee UI  Regular    .921  Semilight .909
#   Tahoma         Regular    .959  Bold    .774
#
# Every one runs Thai lighter than its Latin, and every one widens the gap as
# the weight increases. Sarabun is Siwatch's nominated reference for correct
# Thai engineering, so the ladder below tracks Sarabun's.
WEIGHT_RATIO = {100: 0.93, 200: 0.93, 300: 0.92, 400: 0.915,
                500: 0.91, 600: 0.90, 700: 0.895, 900: 0.89}

# Minimum counter aperture, units/1000em: the widest circle that fits inside
# the tightest enclosed counter of the Thai consonants. This is the number that
# decides whether a loop survives as a loop or renders as a blob, and NOTHING
# measured it before 2026-08-03 — which is why a Bold with 7.8 units of
# aperture (0.11 px at 11 pt) passed the whole suite on its stem match alone.
#
# changeWeight grows outlines in every direction, so a counter bounded by two
# strokes loses ~1.2x the stem gain, then falls off a cliff as a tighter glyph
# crosses below the previous minimum. Measured on BaiJamjuree-Bold:
#
#   embolden    +0     +10     +20    +31.7
#   aperture  66.4    54.7    46.9     11.0   <- ฃ closes; ฮ was binding before
#
# The floor is what shipping Thai families refuse to go below at their heaviest:
# Sarabun ExtraBold 46.9, Leelawadee Bold 46.9. (Tahoma Bold reaches 39.1 and
# is famously heavy in Thai — not a model to follow.)
#
# 46.5, not a round 47.0, and the 0.5 matters. The probe resolves in steps of
# 1000/512 = 1.95 units, so the reference value 46.9 and the next step up 48.8
# are adjacent readings. A floor of 47.0 would fail a face measuring exactly
# what Sarabun ExtraBold measures, which is a mis-set constant rather than a
# font defect — TH-Aeonik-BlackItalic hit precisely that. 46.5 admits
# reference-level and still fails the next step down (44.9).
APERTURE_FLOOR = 46.5

# weight -> (Bai source file, embolden in unscaled Bai units)
#
# The embolden figure is the LESSER of what the two constraints allow:
#   1. WEIGHT_RATIO[weight] * latin_stem / scale - bai_stem
#   2. the largest value keeping the scaled aperture >= APERTURE_FLOOR
# Solved per face by measurement, not prediction; scripts/qc_th_fonts.py
# check 10 re-measures both on the shipped fonts.
#
# Aeonik ships 7 weights x roman/italic = 14 faces; Bai ships 6 x 2 = 12, and
# its ladder is narrower at BOTH ends. Bai's lightest (ExtraLight, stem 35.2)
# is far heavier than Aeonik Air (7.8) and Thin (23.4), and its heaviest (Bold,
# 134.8) is far lighter than Aeonik Black (183.6). Those four faces are
# therefore reached by thinning or emboldening past the source ladder, with the
# quality cost measured per weight — see EXTREME_WEIGHTS below.
#
# Values below |EMBOLDEN_FLOOR| are skipped, so those faces ship pristine Bai
# outlines — the best outcome available, since every FontForge round trip risks
# deforming a mark.
#
# The three aperture-capped faces carry ~3.5u less embolden than the constraint
# solve alone gives. The merge costs a further ~4 units of aperture that the
# solve cannot see, because the build re-solves the scale from ink per weight
# (Black lands on 0.9085, not the nominal 0.914) and then rounds coordinates to
# integers. Measured prepared -> shipped on 2026-08-03: Black 50.8 -> 46.9,
# Slussen Bold 46.9 -> 43.0. So the figures below are set from the SHIPPED
# aperture, which is the only one that matters.
BUILD_TABLE = {
    "TH-Aeonik": {
        "Air":           ("BaiJamjuree-ExtraLight.ttf",      -27.2),
        "Thin":          ("BaiJamjuree-ExtraLight.ttf",      -11.3),
        "Light":         ("BaiJamjuree-Light.ttf",             0.3),
        "Regular":       ("BaiJamjuree-Medium.ttf",           -5.8),
        "Medium":        ("BaiJamjuree-SemiBold.ttf",          1.4),
        "Bold":          ("BaiJamjuree-Bold.ttf",              8.6),
        "Black":         ("BaiJamjuree-Bold.ttf",             13.0),
        "AirItalic":     ("BaiJamjuree-ExtraLightItalic.ttf",-29.2),
        "ThinItalic":    ("BaiJamjuree-ExtraLightItalic.ttf",-13.3),
        "LightItalic":   ("BaiJamjuree-LightItalic.ttf",      -1.6),
        "RegularItalic": ("BaiJamjuree-MediumItalic.ttf",     -7.7),
        "MediumItalic":  ("BaiJamjuree-SemiBoldItalic.ttf",   -0.5),
        "BoldItalic":    ("BaiJamjuree-BoldItalic.ttf",        8.6),
        "BlackItalic":   ("BaiJamjuree-BoldItalic.ttf",       13.0),
    },
    "TH-Slussen": {
        "Regular":  ("BaiJamjuree-Medium.ttf",   -3.2),
        "Medium":   ("BaiJamjuree-SemiBold.ttf", -1.3),
        "SemiBold": ("BaiJamjuree-Bold.ttf",     -0.4),
        "Bold":     ("BaiJamjuree-Bold.ttf",     13.0),
    },
}

# Weight changes below this many units are not worth a FontForge round trip:
# inside the stem probe's noise, and perturbing outlines for no visible gain.
EMBOLDEN_FLOOR = 2.0

# Faces reached by pushing past the end of Bai's ladder, and what it costs.
# Rewritten 2026-08-03 when APERTURE_FLOOR replaced the 1:1 stem target.
#
#   Thin  -11.3  clean; stem within ~1% of target.
#   Air   -27.2  structurally intact but hairline, and thinning opens the loops
#                of ข ค ง right out of existence (two contours -> one). That is
#                what those letters do as they get lighter, so it is correct,
#                but AirItalic ends with no enclosed counter at all.
#   Black +13.0  APERTURE-CAPPED. Aeonik Black's stem is 183.6 and the taper
#                asks for 163.4, but Bai Bold cannot be emboldened past +13.0
#                without driving the counters under the floor. Thai therefore
#                ships at ratio 0.729 — visibly lighter than the Latin.
#                The alternative was the old +68.1, which produced 3.9 units of
#                aperture: solid blobs. Light Thai is the better trade, and it
#                is the same trade Tahoma makes at Bold (0.774).
#   Slussen
#   Bold  +13.0  APERTURE-CAPPED for the same reason; ratio 0.839.
#
# Bold vs Black is the tightest call in the table. Both draw on Bai Bold — Bai
# has nothing heavier — and both are aperture-capped, so there are only ~4 units
# of stem between them: Bold +8.6 (stem 130.9) and Black +13.0 (136.7). That is
# barely above the probe's 1.95-unit resolution, and it is the whole reason Bold
# is set to 8.6 rather than the 10.6 the solve returned. The old build gave Black
# +68.1 to separate them properly and produced 3.9 units of aperture: Word
# rendered ฃ ธ ฮ as solid ink. Check 6 asserts the pair stays distinct.
#
# These are real quality losses against an unreachable target, not regressions,
# and they are not silently accepted — qc_th_fonts check 10 pins each one.
EXTREME_WEIGHTS = {
    ("TH-Aeonik", "Air"): "hairline; Thai very faint at text sizes",
    ("TH-Aeonik", "AirItalic"): "hairline; loops open out entirely",
    ("TH-Aeonik", "Black"): "aperture-capped; Thai ~27% lighter than the Latin",
    ("TH-Aeonik", "BlackItalic"): "aperture-capped; Thai ~27% lighter",
    ("TH-Slussen", "Bold"): "aperture-capped; Thai ~14% lighter than the Latin",
}

_FF_SCRIPT = """
import fontforge, sys
f = fontforge.open(sys.argv[1])
f.selection.all()
f.changeWeight(float(sys.argv[3]))
f.generate(sys.argv[2])
"""


def _embolden(src, amount, workdir):
    """Thicken every stem by `amount` em units using FontForge.

    Returns the path to the emboldened file. FontForge rewrites the OpenType
    layout tables on generate, so the caller must take GPOS/GSUB from the
    pristine source and only the outlines from here.
    """
    out = workdir / (src.stem + f"-bold{amount:.0f}.ttf")
    script = workdir / "embolden.py"
    script.write_text(_FF_SCRIPT)
    r = subprocess.run(
        ["fontforge", "-lang=py", "-script", str(script),
         str(src), str(out), str(amount)],
        capture_output=True, text=True)
    if not out.exists():
        raise RuntimeError(f"FontForge embolden failed for {src.name}:\n"
                           f"{r.stdout}\n{r.stderr}")
    return out


def _bounds(font, gn):
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    if gn not in gs:
        return None
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        return None
    return bp.bounds


def _graft_outlines(base, bolder, delta=0.0):
    """Copy emboldened outlines into `base`, keeping base's layout tables.

    FontForge's generate() reflows GPOS/GSUB/GDEF, and Thai depends heavily on
    mark-attachment anchors that must stay exactly as Bai authored them. So the
    emboldened font is used purely as a source of `glyf` outlines and advances;
    every other table stays as the original shipped it.

    Thai glyphs whose bounding box moved much further than the weight change
    could account for are rejected and keep their original outline.
    `BaiJamjuree-ExtraLightItalic` thinned by 9.5 units came back with `๊`
    stretched from y659 down to y418 — 241 units — which dragged the mark below
    its own anchor, far enough that no amount of clearance correction could lift
    it off the consonant. That is why TH-Aeonik-ThinItalic shipped with a broken
    tone mark. A rejected glyph is slightly off-weight, which is invisible next
    to a mark that is visibly broken.

    Contour count was tried as a second signal and had to be dropped: it fires
    on normal weight change. Thinning closes the loop of `ข` `ค` `ง` and dozens
    of other consonants from two contours to one, which is what those letters
    are supposed to do as they get lighter. Screening on it rejected ~100 Thai
    glyphs per weight and left the consonants at the source weight, undoing the
    stem match this pipeline exists to make.
    """
    bg, bb = base["glyf"], bolder["glyf"]
    # changeWeight moves each edge by about `delta`; allow generous slack for
    # curve reconstruction before calling it a deformation.
    slack = abs(delta) * 2 + 20
    grafted, rejected = 0, []
    for gn in base.getGlyphOrder():
        if gn not in bb.glyphs:
            continue
        # Only Thai is checked. Bai's Latin is never copied into the merged
        # font — the Latin there comes from Aeonik or Slussen — so rejecting a
        # deformed `Aring` would cost a FontForge round trip to protect a glyph
        # that gets discarded. Screening everything also produced hundreds of
        # false rejections on accented composites, whose diagonals legitimately
        # grow more than `slack` under a heavy weight change.
        why = None
        if gn.startswith("uni0E"):
            b0, b1 = _bounds(base, gn), _bounds(bolder, gn)
            if b0 and b1:
                drift = max(abs(x - y) for x, y in zip(b0, b1))
                if drift > slack:
                    why = f"bbox moved {drift:.0f}u"
        if why:
            rejected.append(f"{gn}({why})")
            continue
        bg.glyphs[gn] = bb[gn]
        if gn in bolder["hmtx"].metrics:
            base["hmtx"].metrics[gn] = bolder["hmtx"].metrics[gn]
        grafted += 1
    return grafted, rejected


def _repair_collapsed_counters(font, src, target, workdir, verbose=True):
    """Revert Thai glyphs whose counter did not survive embolden + rounding.

    `_graft_outlines` screens on bounding-box drift, which cannot see this: a
    counter closes without the bbox moving at all. Measured on
    BaiJamjuree-BoldItalic +10.5 (2026-08-03), aperture in units/1000em:

        ษ   source 70.4   emboldened 61.0   emboldened+scaled  3.9   <-- gone
        ฮ   source 66.4   emboldened 54.7   emboldened+scaled 50.8
        ฆ   source 66.5   emboldened 56.9   emboldened+scaled 51.4

    The emboldened outline is not deformed — ษ keeps its 3 contours and grows
    9.7% in area, indistinguishable from its neighbours. It is fragile to
    *rounding*: two edges land within a unit of each other once coordinates are
    scaled by 0.914 and snapped to integers, and the loop fills. That is why
    this screen has to render and measure rather than inspect the outline, and
    why it has to run after scale_upem rather than before.

    A reverted glyph carries the source weight, so it is slightly light against
    its neighbours. That is invisible next to a consonant rendering as a blob —
    the same trade `_graft_outlines` already makes.

    LIMITATION, measured on BlackItalic ฮ: for a composite glyph this reverts
    the composite record only, and its components stay emboldened, so the
    recovery is partial (ฮ 47.0 -> 50.8 rather than to the source's 59.6). It is
    enough to clear the floor and it is honest about what it did — the printed
    figure is the pre-merge measurement, and the merge costs a further ~4 units
    to rounding. Decomposing the composite first would recover the rest, at the
    cost of losing the component structure the mark anchors depend on.
    """
    from th_metrics import LOOP_THAI, apertures

    prepared = workdir / "prepared-probe.ttf"
    font.save(str(prepared))
    got = apertures(prepared, LOOP_THAI)

    ref = TTFont(str(src))
    scale_upem(ref, target)
    ref["head"].unitsPerEm = 1000
    ref_path = workdir / "unweighted-probe.ttf"
    ref.save(str(ref_path))
    ref_ap = apertures(ref_path, LOOP_THAI)

    cmap = font.getBestCmap()
    glyf, ref_glyf = font["glyf"], ref["glyf"]
    repaired = []
    for ch in LOOP_THAI:
        a, r = got.get(ch), ref_ap.get(ch)
        if a is None or r is None or a >= APERTURE_FLOOR or r <= a:
            continue
        gn = cmap.get(ord(ch))
        if gn is None or gn not in ref_glyf.glyphs:
            continue
        glyf.glyphs[gn] = ref_glyf[gn]
        if gn in ref["hmtx"].metrics:
            font["hmtx"].metrics[gn] = ref["hmtx"].metrics[gn]
        repaired.append(f"{ch}({a:.0f}->{r:.0f})")
    ref.close()
    if verbose and repaired:
        print(f"     [0d] Counter collapse repaired on {len(repaired)} glyph(s), "
              f"reverted to source weight: {' '.join(repaired)}")
    return repaired


def _glyph_height(font, ch):
    from fontTools.pens.boundsPen import BoundsPen
    gn = font.getBestCmap().get(ord(ch))
    if not gn:
        return None
    bp = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[gn].draw(bp)
    return None if not bp.bounds else bp.bounds[3] - bp.bounds[1]


def prepare_bai(family, weight, latin_font=None, verbose=True):
    """Return a Bai TTFont scaled (and emboldened) ready to merge into `family`.

    The scale is applied with scaleUpem so that GPOS anchors, mark attachment
    points and advances all move with the outlines. Scaling glyphs alone would
    leave every tone mark anchored at its original height — the marks would
    detach from the consonants they sit on.
    """
    scale = THAI_SCALE[family]
    bai_file, embolden = BUILD_TABLE[family][weight]
    src = BAI / bai_file
    if not src.exists():
        raise FileNotFoundError(src)

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        font = TTFont(str(src))
        if abs(embolden) >= EMBOLDEN_FLOOR:
            # Negative thins. Aeonik Air and Thin sit below Bai's lightest
            # weight, so there is no source to copy — the stems have to come
            # down.
            bolder = TTFont(str(_embolden(src, embolden, workdir)))
            n, rejected = _graft_outlines(font, bolder, embolden)
            bolder.close()
            if verbose:
                verb = "Embolden" if embolden > 0 else "Thin"
                warn = EXTREME_WEIGHTS.get((family, weight))
                print(f"     [0a] {verb} {embolden:+.1f}u on {n} outlines "
                      f"({bai_file})"
                      + (f"  ** {warn}" if warn else ""))
                if rejected:
                    print(f"          {len(rejected)} glyph(s) kept unweighted, "
                          f"deformed by changeWeight: {' '.join(rejected[:8])}"
                          + (" ..." if len(rejected) > 8 else ""))
        elif verbose:
            print(f"     [0a] Weight delta {embolden:+.1f}u skipped, below "
                  f"floor ({bai_file})")

        # Solve the scale against the emboldened outline rather than trusting
        # the table constant. Emboldening grows the glyph box — it pushes the
        # outline outward on every side — so a fixed factor overshoots exactly
        # where the embolden is largest. Measured on the first build: Bold came
        # out at ก = 105% of x-height, Slussen Bold 108%, while the lighter
        # weights landed on target. Measuring here makes the scale exact for
        # every weight and leaves THAI_SCALE as documentation of the nominal.
        if latin_font is not None:
            xh = _glyph_height(latin_font, 'x')
            kh = _glyph_height(font, 'ก')
            if xh and kh:
                scale = xh / kh
                if verbose:
                    print(f"     [0b] Scale solved from ink: x-height {xh:.0f}"
                          f" / ก {kh:.0f} = {scale:.4f} "
                          f"(nominal {THAI_SCALE[family]})")

        # scaleUpem to `scale * 1000` then declare the em back at 1000: the
        # coordinates shrink by `scale` while the em stays the size the Latin
        # font expects.
        target = round(1000 * scale)
        scale_upem(font, target)
        font["head"].unitsPerEm = 1000
        if verbose:
            print(f"     [0c] Thai scaled x{target/1000:.3f} "
                  f"(upem {target} -> declared 1000)")

        # Must run here: the collapse is caused by rounding at this scale, so it
        # is not visible before scale_upem.
        if abs(embolden) >= EMBOLDEN_FLOOR:
            _repair_collapsed_counters(font, src, target, workdir, verbose)
        return font


def fix_thai_gdef(font):
    """Give every Thai glyph an explicit GDEF class.

    Bai Jamjuree leaves its spacing vowels — า ะ ำ เ แ โ ใ ไ ๆ — at GDEF class 0
    (unassigned) and only classifies the combining marks. Every shipping Thai
    font checked (Leelawadee, Leelawadee UI, Tahoma, Noto Looped Thai) declares
    them BASE.

    It matters because Uniscribe's Thai engine reads GDEF to decide what may act
    as a base when it validates a syllable. A spacing vowel with no class is not
    a base as far as that validation is concerned, so an isolated or repeated
    'าาาา' is rejected and will not type. HarfBuzz infers the class from Unicode
    and hides the problem, which is why this survived every Linux-side test.

    Class is taken from the Unicode general category, not a hand-written list:
    Mn/Me -> MARK, everything else in the Thai block -> BASE.
    """
    import unicodedata
    from fontTools.ttLib.tables import otTables

    if "GDEF" not in font:
        return 0, 0
    gdef = font["GDEF"].table
    if gdef.GlyphClassDef is None:
        gdef.GlyphClassDef = otTables.GlyphClassDef()
        gdef.GlyphClassDef.classDefs = {}
    cd = gdef.GlyphClassDef.classDefs

    cmap = font.getBestCmap()
    n_base = n_mark = 0
    for cp, gn in cmap.items():
        if not (0x0E00 <= cp <= 0x0E7F):
            continue
        want = 3 if unicodedata.category(chr(cp)) in ("Mn", "Me") else 1
        if cd.get(gn) != want:
            cd[gn] = want
            if want == 1:
                n_base += 1
            else:
                n_mark += 1
    return n_base, n_mark


def _circle(pen, cx, cy, r):
    """Approximate a circle with four quadratic segments."""
    k = r * 1.0
    pen.moveTo((cx + r, cy))
    pen.qCurveTo((cx + k, cy + k), (cx, cy + r))
    pen.qCurveTo((cx - k, cy + k), (cx - r, cy))
    pen.qCurveTo((cx - k, cy - k), (cx, cy - r))
    pen.qCurveTo((cx + k, cy - k), (cx + r, cy))
    pen.closePath()


def add_dotted_circle(font, x_height):
    """Synthesise U+25CC if the font lacks it.

    The shaper substitutes a dotted circle as a placeholder when a mark appears
    with no base to attach to. Bai ships none, so an orphaned vowel or tone mark
    has nothing to render against and simply vanishes. Leelawadee, Tahoma and
    Noto Looped Thai all carry one.

    Drawn here rather than copied: the only U+25CC available locally are in
    licensed Windows system fonts, and lifting an outline out of those into a
    redistributed binary is not ours to do.
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    cmap = font.getBestCmap()
    if 0x25CC in cmap:
        return False

    # Proportions matched against Leelawadee rendered at 90 px: a larger ring
    # also drags any attached mark upward, because the mark anchors off the
    # base's height, so an oversized placeholder misrepresents where the real
    # mark will sit.
    name = "uni25CC"
    r_ring = x_height * 0.48
    r_dot = x_height * 0.058
    cy = x_height * 0.50
    advance = int(r_ring * 2 + r_dot * 4)
    cx = advance / 2

    import math
    N_DOTS = 14
    pen = TTGlyphPen(None)
    for i in range(N_DOTS):
        a = math.pi * 2 * i / N_DOTS
        _circle(pen, cx + r_ring * math.cos(a), cy + r_ring * math.sin(a),
                r_dot)
    glyph = pen.glyph()

    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
        font.setGlyphOrder(order)
        font["glyf"].glyphOrder = order
    font["glyf"].glyphs[name] = glyph
    font["hmtx"].metrics[name] = (advance, 0)

    for table in font["cmap"].tables:
        # Unicode subtables only; the Mac format-6 table is deliberately
        # restricted to codes <= 255 for Uniscribe compliance.
        if table.platformID == 3 or (table.platformID == 0
                                     and table.format in (4, 12)):
            if table.cmap is not None:
                table.cmap[0x25CC] = name

    if "GDEF" in font and font["GDEF"].table.GlyphClassDef is not None:
        font["GDEF"].table.GlyphClassDef.classDefs[name] = 1  # BASE
    return True


def ink_bounds(font, glyphs=None):
    """(ymin, ymax) over every glyph's ink, including shaping-only variants."""
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    lo = hi = None
    for gn in (glyphs or font.getGlyphOrder()):
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds:
            continue
        if lo is None or bp.bounds[1] < lo:
            lo = bp.bounds[1]
        if hi is None or bp.bounds[3] > hi:
            hi = bp.bounds[3]
    return lo, hi


if __name__ == "__main__":
    fam = sys.argv[1] if len(sys.argv) > 1 else "TH-Aeonik"
    print(f"{fam}  scale {THAI_SCALE[fam]}")
    for w in BUILD_TABLE[fam]:
        f = prepare_bai(fam, w)
        lo, hi = ink_bounds(f)
        print(f"  {w:<15} ink {lo:>7.0f} .. {hi:>7.0f}")
        f.close()
