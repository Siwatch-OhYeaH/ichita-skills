#!/usr/bin/env python3
"""
Generate the master weights Aeonik and Bai Jamjuree do not ship.

TH Aeonik targets a ten-step scale:

    Air 100  Thin 200  Light 300  Book 350  Regular 400
    Medium 500  SemiBold 600  Bold 700  ExtraBold 800  Black 900

Neither source family covers it:

    Aeonik (Latin)      100 200 300 ___ 400 500 ___ 700 ___ 900
    Bai Jamjuree (Thai) ___ 200 300 ___ 400 500 600 700 ___ ___

The gaps are filled by interpolating between real masters, using the lossless
compatibiliser in interpolate_masters.py. Targets inside the shipped range are
interpolations and are reliable. Targets outside it -- Thai Air 100, ExtraBold
800 and Black 900 -- are extrapolations, and extrapolating a Thai face is the
risky part of this build: Thai counters are small loops that fill in first as
weight rises, and no linear model knows to keep them open. Every generated
weight is therefore checked for counter collapse (see check_counters) rather
than trusted.

Outputs:
  assets/fonts/aeonik-ext/        generated Latin masters (OTF/CFF)
  assets/fonts/bai-jamjuree-ext/  generated Thai masters (TTF)

Usage:
  python3 generate_masters.py                 # all generated masters
  python3 generate_masters.py --upright-only
  python3 generate_masters.py --only Latin:Book
"""

import multiprocessing as mp
import sys
import warnings
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).parent))
from interpolate_masters import (  # noqa: E402
    compatibilize,
    contour_params,
    contour_at,
    draw_contours,
    glyph_to_contours,
    interpolate_contours,
)

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent
ASSETS = SCRIPT_DIR.parent / "assets"
AEONIK = ASSETS / "fonts" / "aeonik"
BAI = ASSETS / "fonts" / "bai-jamjuree"
AEONIK_EXT = ASSETS / "fonts" / "aeonik-ext"
BAI_EXT = ASSETS / "fonts" / "bai-jamjuree-ext"

# Curve error budget when converting the generated cubic outlines back to the
# quadratic form TrueType needs. Half a unit on a 1000 upm em is well below
# rasterisation resolution at any practical size.
CU2QU_ERROR = 0.5

# A generated counter smaller than this fraction of the nearest real master's
# counter is treated as collapsing.
COUNTER_MIN_RATIO = 0.15


def plan_t(w_target, w_a, w_b):
    """Interpolation factor placing w_target on the line through w_a, w_b."""
    return (w_target - w_a) / (w_b - w_a)


# Generated masters, as style -> (master A, master B, weight to generate,
# weight the face is nominally sold as). The two weights differ only where a
# source family cannot reach the nominal target; see THAI_PLAN.
#
# All three Latin targets sit inside Aeonik's shipped range, so these are
# plain interpolations between the two nearest masters.
LATIN_PLAN = {
    "Book":      ("Light",  "Regular", 350, 350),
    "SemiBold":  ("Medium", "Bold",    600, 600),
    "ExtraBold": ("Bold",   "Black",   800, 800),
}
LATIN_WEIGHTS = {"Light": 300, "Regular": 400, "Medium": 500, "Bold": 700, "Black": 900}

# Thai is the constrained script. Bai Jamjuree ships 200-700, and measuring
# where its outlines start to self-intersect shows the design does not
# survive being pushed outside that range:
#
#     900 (t=+2.00): 40 of 86 glyphs self-intersect
#     800 (t=+1.50):  8 of 86
#     730 (t=+1.15):  0            <- last clean step above Bold
#     100 (t=-0.50): 33 of 87 glyphs self-intersect
#     150 (t=-0.25): 11 of 87
#     200          :  0            <- ExtraLight, the lightest clean weight
#
# So Book 350 interpolates normally, the heavy end is damped to a verified
# clean 710/720 rather than a broken 800/900, and Air 100 is not generated at
# all -- it uses real ExtraLight outlines. The Thai therefore stops getting
# lighter below 200 and heavier above ~720 while the Latin runs the full
# 100-900. That is a limit of the source family, not of the pipeline.
THAI_PLAN = {
    "Book":      ("Light",  "Regular", 350, 350),
    "ExtraBold": ("Medium", "Bold",    710, 800),
    "Black":     ("Medium", "Bold",    720, 900),
}
THAI_WEIGHTS = {"ExtraLight": 200, "Light": 300, "Regular": 400,
                "Medium": 500, "SemiBold": 600, "Bold": 700}

# Source filename patterns. Bai Jamjuree calls its upright regular "Regular"
# but its italic simply "Italic", so the roman name is special-cased.
LATIN_FILE = {False: "Aeonik-{}.otf", True: "Aeonik-{}Italic.otf"}


def bai_file(style, italic):
    if not italic:
        return f"BaiJamjuree-{style}.ttf"
    return "BaiJamjuree-Italic.ttf" if style == "Regular" else f"BaiJamjuree-{style}Italic.ttf"


# ---------------------------------------------------------------------------
# Per-glyph work (runs in worker processes)
# ---------------------------------------------------------------------------

_W = {}


def _init_worker(path_a, path_b):
    fa, fb = TTFont(path_a), TTFont(path_b)
    _W["fa"], _W["fb"] = fa, fb
    _W["gsa"], _W["gsb"] = fa.getGlyphSet(), fb.getGlyphSet()
    _W["hmtx_a"], _W["hmtx_b"] = fa["hmtx"].metrics, fb["hmtx"].metrics


def _master_intersects(glyph_set, name):
    contours = glyph_to_contours(glyph_set, name)
    return bool(contours) and self_intersects(contours)


def _has_ink(glyph_set, name):
    """Whether a glyph draws anything, measured without outline extraction."""
    if name not in glyph_set:
        return False
    pen = BoundsPen(glyph_set)
    try:
        glyph_set[name].draw(pen)
    except Exception:
        return False
    return pen.bounds is not None


def _interp_one(job):
    """Interpolate a single glyph. Returns (name, contours|None, width)."""
    name, t = job
    gsa, gsb = _W["gsa"], _W["gsb"]

    wa = _W["hmtx_a"].get(name, (0, 0))[0]
    wb = _W["hmtx_b"].get(name, (wa, 0))[0]
    width = int(round(wa + t * (wb - wa)))

    ca = glyph_to_contours(gsa, name)
    cb = glyph_to_contours(gsb, name)
    if ca is None:
        return name, None, width
    if not ca:
        # Empty contours should mean a genuinely blank glyph such as space.
        # Bounds are measured independently of outline extraction, so if they
        # show ink then extraction failed and writing this out would silently
        # blank a real glyph -- keep the master's instead.
        if _has_ink(gsa, name) or (cb and _has_ink(gsb, name)):
            return name, None, width
        return name, [], width
    pair = compatibilize(ca, cb)
    if pair is None:
        return name, None, width        # incompatible: keep the base master's
    return name, interpolate_contours(pair[0], pair[1], t), width


# ---------------------------------------------------------------------------
# Counter-collapse QA
# ---------------------------------------------------------------------------

def signed_area(contour, n=120):
    pts = _sample(contour, n)
    total = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def _sample(contour, n):
    params, _, _ = contour_params(contour)
    return [contour_at(contour, params, i / n) for i in range(n)]


def _polyline(contours, n=48):
    out = []
    for c in contours:
        params, _, _ = contour_params(c)
        pts = [contour_at(c, params, i / n) for i in range(n)]
        for i in range(n):
            out.append((pts[i], pts[(i + 1) % n], id(c), i, n))
    return out


def _crosses(a1, a2, b1, b2):
    if (max(a1[0], a2[0]) < min(b1[0], b2[0]) or max(b1[0], b2[0]) < min(a1[0], a2[0])
            or max(a1[1], a2[1]) < min(b1[1], b2[1]) or max(b1[1], b2[1]) < min(a1[1], a2[1])):
        return False

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)

    return (orient(a1, a2, b1) != orient(a1, a2, b2)
            and orient(b1, b2, a1) != orient(b1, b2, a2))


def self_intersects(contours):
    """Whether an outline crosses itself.

    This is the failure mode that actually limits extrapolation. Pushing a
    weight past its masters thickens strokes until the two sides of a stroke
    pass through each other -- Thai is especially prone to it because its
    letters are built from small loops that close up first. The glyph keeps
    plausible contour areas throughout, so a counter check never notices;
    only an intersection test does.
    """
    segments = _polyline(contours)
    for i in range(len(segments)):
        a1, a2, ca, ia, na = segments[i]
        for j in range(i + 1, len(segments)):
            b1, b2, cb, ib, _ = segments[j]
            if ca == cb:
                d = abs(ia - ib)
                if d <= 1 or d >= na - 1:
                    continue        # neighbours along a contour always touch
            if _crosses(a1, a2, b1, b2):
                return True
    return False


def check_counters(generated, base_contours):
    """Flag counters that collapsed or inverted relative to the base master.

    A counter that shrinks toward zero or flips winding means the outline has
    started to self-overlap -- the classic failure of pushing a weight past
    the range its masters describe.
    """
    if not generated or not base_contours or len(generated) != len(base_contours):
        return 0
    bad = 0
    for cg, cb in zip(generated, base_contours):
        ag, ab = signed_area(cg), signed_area(cb)
        if abs(ab) < 1e-6:
            continue
        if (ag > 0) != (ab > 0):
            bad += 1                                  # winding inverted
        elif abs(ag) < COUNTER_MIN_RATIO * abs(ab):
            bad += 1                                  # counter closing up
    return bad


# ---------------------------------------------------------------------------
# Writing generated outlines back into a font
# ---------------------------------------------------------------------------

def write_cff(font, results):
    cff = font["CFF "].cff
    top = cff.topDictIndex[0]
    charstrings = top.CharStrings
    hmtx = font["hmtx"]
    kept = 0
    for name, contours, width in results:
        if contours is None:
            kept += 1
            continue
        pen = T2CharStringPen(width, None)
        draw_contours(contours, pen)
        cs = pen.getCharString()
        cs.private = top.Private
        cs.globalSubrs = getattr(cff, "GlobalSubrs", [])
        charstrings[name] = cs
        lsb = hmtx.metrics.get(name, (width, 0))[1]
        hmtx.metrics[name] = (width, lsb)
    return kept


def write_glyf(font, results):
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    kept = 0
    for name, contours, width in results:
        if contours is None:
            kept += 1
            continue
        tt_pen = TTGlyphPen(None)
        # Source and target are both TrueType, so contour direction already
        # matches and must not be reversed.
        draw_contours(contours, Cu2QuPen(tt_pen, CU2QU_ERROR, reverse_direction=False))
        glyph = tt_pen.glyph()
        glyf[name] = glyph
        glyph.recalcBounds(glyf)
        lsb = glyph.xMin if hasattr(glyph, "xMin") else hmtx.metrics.get(name, (width, 0))[1]
        hmtx.metrics[name] = (width, lsb)
    return kept


def set_master_metadata(font, family, style, weight_class, italic):
    nt = font["name"]
    full = f"{family} {style}" + (" Italic" if italic else "")
    ps = f"{family.replace(' ', '')}-{style}" + ("Italic" if italic else "")
    for pid, peid, lid in ((3, 1, 0x0409), (1, 0, 0)):
        nt.setName(f"{family} {style}", 1, pid, peid, lid)
        nt.setName("Italic" if italic else "Regular", 2, pid, peid, lid)
        nt.setName(full, 4, pid, peid, lid)
        nt.setName(ps, 6, pid, peid, lid)
    font["OS/2"].usWeightClass = weight_class


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def generate(script, style, master_a, master_b, target_weight, nominal_weight, italic, jobs):
    if script == "Latin":
        src_dir, ext_dir = AEONIK, AEONIK_EXT
        pa = src_dir / LATIN_FILE[italic].format(master_a)
        pb = src_dir / LATIN_FILE[italic].format(master_b)
        out = ext_dir / LATIN_FILE[italic].format(style)
        wa, wb = LATIN_WEIGHTS[master_a], LATIN_WEIGHTS[master_b]
        family = "Aeonik"
    else:
        src_dir, ext_dir = BAI, BAI_EXT
        pa = src_dir / bai_file(master_a, italic)
        pb = src_dir / bai_file(master_b, italic)
        out = ext_dir / bai_file(style, italic)
        wa, wb = THAI_WEIGHTS[master_a], THAI_WEIGHTS[master_b]
        family = "Bai Jamjuree"

    if not pa.exists() or not pb.exists():
        print(f"     !! missing source: {pa.name} / {pb.name}")
        return False

    t = plan_t(target_weight, wa, wb)
    mode = "interpolate" if 0.0 <= t <= 1.0 else "EXTRAPOLATE"
    label = f"{script} {style}{'  Italic' if italic else ''}"
    damped = "" if target_weight == nominal_weight else \
        f"  [damped: sold as {nominal_weight}, drawn at {target_weight} to stay clean]"
    print(f"\n  === {label} ({nominal_weight}) ===")
    print(f"     {mode}: {pa.name} [{wa}] -> {pb.name} [{wb}]  t={t:+.3f}{damped}")

    fa, fb = TTFont(str(pa)), TTFont(str(pb))
    names_b = set(fb.getGlyphOrder())
    jobs_list = [(g, t) for g in fa.getGlyphOrder() if g in names_b]

    with mp.Pool(jobs, initializer=_init_worker, initargs=(str(pa), str(pb))) as pool:
        results = pool.map(_interp_one, jobs_list, chunksize=16)

    # QA before writing: compare against the nearer real master. Report the
    # in-script glyphs separately -- a Thai master also carries Latin and
    # symbol glyphs, but the merge takes those from Aeonik and drops these,
    # so a collapse there never reaches the shipped font.
    # Glyphs whose correspondence cannot be trusted keep a master's outline
    # rather than a distorted blend, so the master we clone is the one
    # *nearest in weight* to the target -- not simply master A. It matters
    # most for the damped heavy Thai, where the target sits just past Bold:
    # cloning Bold makes a fallback glyph invisible, while cloning Medium
    # would drop common letters 200 weight units below the rest of the face.
    base_path = pa if abs(t) <= abs(1 - t) else pb
    base_font = TTFont(str(base_path))
    base_gs = base_font.getGlyphSet()
    gsa_qa, gsb_qa = TTFont(str(pa)).getGlyphSet(), TTFont(str(pb)).getGlyphSet()
    in_script = (lambda cp: 0x0E01 <= cp <= 0x0E5B) if script == "Thai" else (lambda cp: True)
    reverse_cmap = {g: cp for cp, g in fa.getBestCmap().items()}
    collapsed = collapsed_glyphs = inert = 0
    crossed = []
    for name, contours, _ in results:
        if not contours:
            continue
        cp = reverse_cmap.get(name)
        relevant = cp is not None and in_script(cp)
        bad = check_counters(contours, glyph_to_contours(base_gs, name))
        if bad:
            if relevant:
                collapsed += bad
                collapsed_glyphs += 1
            else:
                inert += 1
        # Only a *new* intersection means something. Type designers routinely
        # leave contours overlapping -- a stem crossing into a bowl fills
        # identically under the non-zero winding rule -- so the masters
        # themselves intersect all over. What matters is an outline that
        # crosses itself when neither master did.
        if relevant and self_intersects(contours):
            if not (_master_intersects(gsa_qa, name) or _master_intersects(gsb_qa, name)):
                crossed.append(chr(cp))

    font = TTFont(str(base_path))
    kept = write_cff(font, results) if script == "Latin" else write_glyf(font, results)
    set_master_metadata(font, family, style, nominal_weight, italic)

    ext_dir.mkdir(parents=True, exist_ok=True)
    font.save(str(out))

    total = len(results)
    in_script_kept = sum(
        1 for name, contours, _ in results
        if contours is None
        and (cp := reverse_cmap.get(name)) is not None and in_script(cp)
    )
    in_script_total = sum(1 for cp in fa.getBestCmap() if in_script(cp))
    print(f"     glyphs: {total - kept} generated, {kept} kept from "
          f"{base_path.stem} (correspondence not trustworthy); of the glyphs "
          f"this face ships, {in_script_kept}/{in_script_total} fell back")
    status = "clean" if collapsed_glyphs == 0 else f"{collapsed_glyphs} glyphs / {collapsed} contours"
    note = f"  ({inert} collapsed in glyphs the merge discards)" if inert else ""
    print(f"     counter check: {status}{note}")
    if crossed:
        print(f"     !! self-intersecting: {len(crossed)} glyphs -- {' '.join(crossed[:20])}")
    else:
        print(f"     intersection check: clean")
    print(f"     saved: {out.relative_to(ASSETS.parent)} "
          f"({out.stat().st_size / 1024:.0f} KB)")
    return True


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate missing TH-Aeonik masters")
    ap.add_argument("--jobs", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--upright-only", action="store_true")
    ap.add_argument("--only", default=None,
                    help="restrict to one target, e.g. Latin:Book or Thai:Black")
    args = ap.parse_args()

    targets = []
    for style, (ma, mb, w, nominal) in LATIN_PLAN.items():
        targets.append(("Latin", style, ma, mb, w, nominal))
    for style, (ma, mb, w, nominal) in THAI_PLAN.items():
        targets.append(("Thai", style, ma, mb, w, nominal))

    if args.only:
        script, style = args.only.split(":")
        targets = [t for t in targets if t[0] == script and t[1] == style]

    italics = [False] if args.upright_only else [False, True]

    print("\n" + "=" * 70)
    print("  GENERATE MISSING MASTERS")
    print("  filling the gaps Aeonik and Bai Jamjuree do not ship")
    print("=" * 70)

    ok = total = 0
    for script, style, ma, mb, w, nominal in targets:
        for italic in italics:
            total += 1
            if generate(script, style, ma, mb, w, nominal, italic, args.jobs):
                ok += 1

    print(f"\n{'=' * 70}")
    print(f"  {'PASS' if ok == total else 'PARTIAL'}: {ok}/{total} masters generated")
    print(f"{'=' * 70}\n")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
