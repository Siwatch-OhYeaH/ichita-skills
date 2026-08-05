#!/usr/bin/env python3
"""Close the Greek/math coverage gaps in Aeonik's desktop cut.

Five codepoints are missing from Aeonik v1.000, the desktop cut this repo builds
against and the one Word actually uses:

    Δ  U+0394  GREEK CAPITAL LETTER DELTA
    μ  U+03BC  GREEK SMALL LETTER MU
    Ω  U+03A9  GREEK CAPITAL LETTER OMEGA
    Σ  U+03A3  GREEK CAPITAL LETTER SIGMA
    ⌀  U+2300  DIAMETER SIGN

WHY IT MATTERS IN A WATER-TREATMENT PROPOSAL, which is the whole reason this is
worth any code at all. Word's Symbol dialog and Insert->Equation both emit the
GREEK codepoints, not the maths ones, and lab data pasted from Excel carries
`µS/cm` with U+03BC about as often as with U+00B5. So today those characters fall
back to a system font in the middle of a line — a different typeface, a different
weight, mid-sentence, in a document that is meant to demonstrate precision.

Slussen v1 already ships Δ, μ and Ω, and needs only the two aliases. That is why
nothing here is hardcoded per family: this module reads the font's cmap and closes
whatever is actually missing. A future CoType desktop release that ships Greek
makes it quietly do nothing.

---------------------------------------------------------------------------
HOW EACH GAP IS CLOSED, and the measurement behind the choice
---------------------------------------------------------------------------

Siwatch's decision, 2026-08-05: HARVEST the web cut's outlines rather than alias
existing glyphs. The alternative was measured and put to him — in the web cut,
`uni0394` is POINT-IDENTICAL to `uni2206` and `uni03BC` to `uni00B5`, so CoType
draws one glyph for each of those pairs and a cmap alias inside the desktop cut
would have been faithful to Aeonik's own design at zero cost. He chose the
harvest anyway. Recorded because the reasoning is not obvious from the code:

    codepoint   web cut ships          v1 twin            harvest source
    Δ U+0394    uni0394                ∆ U+2206 w670      web, 6 faces
    μ U+03BC    uni03BC                µ U+00B5 w564      web, 6 faces
    Ω U+03A9    uni03A9 (19 segs)      Ω U+2126 (32)      web, 6 faces
    Σ U+03A3    absent everywhere      ∑ U+2211           ALIAS ONLY
    ⌀ U+2300    absent everywhere      Ø U+00D8           ALIAS ONLY

Σ and ⌀ are genuine shape compromises, not equivalents: `∑` is drawn for maths
and sits larger and wider than a Greek sigma, and `Ø` is a letter where `⌀` is a
symbol. Flagged on every build. Revisit only if a real document reads wrong.

TWIN CONSISTENCY. Where the web cut draws Greek and maths as ONE outline, this
module points both codepoints at one glyph, so `Δ` and `∆` cannot render 9 units
apart in the same word. That means `∆` and `µ` CHANGE APPEARANCE in the harvested
faces — the v2 drawing replaces the v1 one. It is a visible change to an existing
glyph and it is on the specimen for review. `Ω` is the exception: the web cut
itself draws U+03A9 and U+2126 differently (19 segments against 32), so the two
stay distinct and the v1 ohm sign is left alone.

---------------------------------------------------------------------------
THE EIGHT FACES THE WEB CUT DOES NOT SHIP
---------------------------------------------------------------------------

The web cut is Light, Regular, Bold and their italics. The desktop cut is those
six plus Air, Thin, Medium, Black and their italics. Decision 4: interpolate
Medium, extrapolate the rest, and VERIFY EACH RESULT AGAINST THAT FACE'S OWN
MEASURED STEM rather than trusting the arithmetic. A face whose derived glyph
misses tolerance falls back to the alias FOR THAT FACE ONLY, and the number that
made it fail is recorded rather than swallowed.

That verification is not ceremony. Extrapolating a two-master design past its
masters is exactly where stems inverse and joins break, and `μ` cannot be
interpolated across the full range at all: measured point counts are

    uni0394   Light 9    Regular 9    Bold 9     compatible
    uni03A9   Light 34   Regular 34   Bold 34    compatible
    uni03BC   Light 30   Regular 29   Bold 29    LIGHT IS NOT COMPATIBLE

so `μ` has a two-master basis (Regular, Bold) where the others have three, and
Air/Thin must reach it by extrapolating backwards past Regular. If that lands
outside tolerance the alias is the right answer, which is the point of having one.

The tolerance is `solve_weight_table.TOL`, 2.0 units/1000 em — one step of the
512 px probe, so anything tighter is noise rather than accuracy.
"""
from __future__ import annotations

import statistics
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

ROOT = SCRIPTS.parent
WEB_DIR = ROOT / "assets" / "fonts" / "aeonik-woff"

# Where the decompressed web cut is cached. freetype cannot read WOFF2, and the
# harvest needs a rasterisable file as well as an outline, so the .woff2 is
# expanded once per process into a temp dir rather than into the repo — nothing
# here is a build artifact worth keeping, and an expanded webfont sitting in
# assets/ is exactly the thing the licence position (see the plan's Risks) says
# should not accumulate.
_web_cache: dict[str, Path] = {}
_tmpdir: tempfile.TemporaryDirectory | None = None

# codepoint -> (glyph name in the web cut, twin codepoint in the desktop cut)
HARVEST = {
    0x0394: ("uni0394", 0x2206),
    0x03BC: ("uni03BC", 0x00B5),
    0x03A9: ("uni03A9", 0x2126),
}

# codepoint -> twin codepoint. No outline exists in any cut, so these are cmap
# aliases and shape compromises. See the module docstring.
ALIAS_ONLY = {
    0x03A3: 0x2211,
    0x2300: 0x00D8,
}

# Pairs the web cut draws as one outline, measured point-exact across Light,
# Regular and Bold. Both codepoints get the harvested glyph, so they cannot
# disagree. U+03A9/U+2126 is deliberately absent: Aeonik draws those two
# differently and collapsing them would be a change nobody asked for.
TWIN_SHARES_OUTLINE = {0x0394, 0x03BC}

# Web faces, by desktop face name. The web cut ships six.
WEB_FACES = {
    "Light": "Aeonik-Light",
    "Regular": "Aeonik-Regular",
    "Bold": "Aeonik-Bold",
    "LightItalic": "Aeonik-LightItalic",
    "RegularItalic": "Aeonik-RegularItalic",
    "BoldItalic": "Aeonik-BoldItalic",
}

# Interpolation basis per slant, lightest first. A derived face's weight is found
# by measuring, not by assuming a position on this list.
BASIS = {
    False: ["Light", "Regular", "Bold"],
    True: ["LightItalic", "RegularItalic", "BoldItalic"],
}

# One step of the 512 px stem probe. Matches solve_weight_table.TOL, and for the
# same reason: 1000/512 = 1.95 units, so a tighter bar measures noise.
STEM_TOL = 2.0
PX = 512
MAX_ITER = 6

# How much more within-glyph weight variation a derived glyph may have than the
# twin it is measured against. See _stroke_spread() for the measurements: good
# faces land at 0.93-1.22, collapsed ones at 3.67-12.67, so 1.5 sits in a 3x gap
# and is not a delicately-placed number.
SPREAD_EXCESS_MAX = 1.5

# Extrapolation is bounded. Past this the outline stops being Aeonik and starts
# being an artifact of the arithmetic — stems invert, joins cross. A face that
# needs more than this falls back to the alias by construction rather than by
# failing the stem check with a broken glyph that happens to measure right.
T_LIMIT = 2.5


def _cleanup_registered():
    global _tmpdir
    if _tmpdir is None:
        _tmpdir = tempfile.TemporaryDirectory(prefix="th-greek-")
    return Path(_tmpdir.name)


def _web_path(face: str) -> Path | None:
    """Expand the web cut for `face` to a plain .otf, cached per process."""
    if face in _web_cache:
        return _web_cache[face]
    stem_name = WEB_FACES.get(face)
    if stem_name is None:
        return None
    src = WEB_DIR / f"{stem_name}.woff2"
    if not src.exists():
        src = WEB_DIR / f"{stem_name}.woff"
    if not src.exists():
        return None
    from fontTools.ttLib import TTFont
    out = _cleanup_registered() / f"{stem_name}.otf"
    font = TTFont(str(src))
    font.flavor = None
    font.save(str(out))
    font.close()
    _web_cache[face] = out
    return out


# ---------------------------------------------------------------------------
# Outline arithmetic
# ---------------------------------------------------------------------------

def _record(path: Path, gname: str):
    """(pen recording, advance width) for `gname` in `path`, or None."""
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont
    font = TTFont(str(path), lazy=True)
    try:
        gs = font.getGlyphSet()
        if gname not in gs:
            return None
        pen = RecordingPen()
        gs[gname].draw(pen)
        return pen.value, gs[gname].width
    finally:
        font.close()


def _signature(value):
    """Structural fingerprint: the op sequence and the point count of each op.

    Two outlines can only be interpolated if this matches. Comparing coordinate
    counts rather than coordinates is the whole check — a curve split, a doubled
    on-curve point or a contour drawn in the other direction all show up here,
    and all three produce garbage if interpolated anyway.
    """
    return tuple((op, tuple(len(p) if isinstance(p, tuple) else 0 for p in pts))
                 for op, pts in value)


def _lerp(v0, v1, t):
    """Linear blend of two structurally identical pen recordings."""
    out = []
    for (op0, pts0), (op1, pts1) in zip(v0, v1):
        pts = []
        for p0, p1 in zip(pts0, pts1):
            if p0 is None or p1 is None:
                pts.append(p0)
                continue
            pts.append(tuple(a + (b - a) * t for a, b in zip(p0, p1)))
        out.append((op0, tuple(pts)))
    return out


def _replay(value, pen):
    for op, pts in value:
        getattr(pen, op)(*pts)


# ---------------------------------------------------------------------------
# Stem measurement
# ---------------------------------------------------------------------------

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


def _bitmap(path, cp, px=PX):
    import freetype
    import numpy as np
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, px)
    try:
        face.load_char(cp, freetype.FT_LOAD_RENDER)
    except Exception:
        return None
    bm = face.glyph.bitmap
    if not bm.width or not bm.rows:
        return None
    return np.array(bm.buffer, dtype=np.uint8).reshape(
        bm.rows, bm.pitch)[:, :bm.width] > 128


def _stem_of_char(path, cp, px=PX):
    """Median horizontal ink run across the mid-height band, units/1000 em.

    The same probe as th_metrics.stem, on one codepoint instead of a corpus. For
    Δ the band crosses the two diagonals, for μ the two verticals, for Ω the two
    sides — in every case the runs ARE the stem, which is why these three are
    measurable this way and a loop-heavy glyph would not be.
    """
    a = _bitmap(path, cp, px)
    if a is None:
        return None
    band = a[int(a.shape[0] * .4):int(a.shape[0] * .6)]
    rr = [r for row in band for r in _runs(row)]
    if not rr:
        return None
    return statistics.median(rr) / px * 1000


def _stroke_spread(path, cp, px=PX):
    """(p10, p50, p90, p90/p10) of every ink run in the WHOLE glyph.

    THIS IS THE CHECK THAT CATCHES A COLLAPSED EXTRAPOLATION, and it exists
    because the two obvious checks do not.

    Measured 2026-08-05 on the first build of this module: extrapolating `μ`
    backwards from the Regular/Bold basis to Air (t = -1.55) produced a glyph with
    HAIRLINE STEMS AND A HEAVY BOWL — stems 1 px against a bowl of 16 px at 512
    px/em — plus a truncated right stem. It was visibly broken on the specimen and
    BOTH of the checks already in place passed it:

      * the median stem, because the 0.4-0.6 band crosses the bowl, so the median
        landed on the target;
      * total ink, because a bowl that is too heavy and stems that are too light
        cancel out — Air measured 1.041 of the twin's ink.

    What is wrong with the glyph is not its average weight, it is that the weight
    is not CONSISTENT WITHIN the glyph. p90/p10 measures exactly that, and against
    the twin's own p90/p10 it separates cleanly:

        glyph  face          derived    v1 twin    excess
        μ      Air             16.00       1.50     10.67   REJECTED
        μ      AirItalic       19.00       1.50     12.67   REJECTED
        μ      ThinItalic       6.00       1.50      4.00   REJECTED
        μ      Thin             5.00       1.36      3.67   REJECTED
        Ω      AirItalic        5.33       2.00      2.67   REJECTED
        Ω      Air              4.25       2.00      2.12   REJECTED
        Ω      Thin             2.42       1.75      1.38   kept
        μ      Medium           1.47       1.49      0.99   kept
        Δ      every face                        0.93-1.20  kept
        everything else kept                     0.93-1.38

    Worst kept 1.38, best rejected 2.12 — a comfortable gap, so 1.5 is not a
    delicately-placed number.

    Ω AT AIR AND AIRITALIC IS WORTH SINGLING OUT: it was found BY this check, not
    before it. The first pass of this module shipped those two faces and the eye
    that reviewed the specimen went to the four broken μ and missed them. A check
    that only confirms what someone already spotted is not doing any work.

    Δ survives at every weight because it has a three-master basis and no bowl —
    nine points, all corners. μ has only a two-master basis (Light is not
    point-compatible), so Air and Thin must reach it by extrapolating backwards
    past Regular, and that is where the bowl and the stems part company.
    """
    a = _bitmap(path, cp, px)
    if a is None:
        return None
    rr = sorted(r for row in a for r in _runs(row))
    if len(rr) < 8:
        return None
    n = len(rr)
    p10, p50, p90 = rr[int(n * .10)], rr[int(n * .50)], rr[int(n * .90)]
    return p10, p50, p90, p90 / max(p10, 1)


def _probe_font(desktop_path, cp, gname, value, width):
    """Write a candidate outline into a copy of the real face and return its path.

    Predicting the stem from the interpolation factor would measure the
    arithmetic; rasterising the glyph in the face it will ship in measures the
    glyph, which is the point of decision 4.
    """
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.ttLib import TTFont

    font = TTFont(str(desktop_path))
    try:
        cff = font["CFF "].cff
        top = cff[cff.fontNames[0]]
        charstrings = top.CharStrings
        private = top.Private

        pen = T2CharStringPen(width - private.nominalWidthX, None,
                              roundTolerance=0.5)
        _replay(value, pen)
        cs = pen.getCharString(private=private, globalSubrs=cff.GlobalSubrs)

        if gname in charstrings:
            charstrings[gname] = cs
        else:
            charstrings.charStringsIndex.append(cs)
            charstrings.charStrings[gname] = len(charstrings.charStringsIndex) - 1
            order = font.getGlyphOrder() + [gname]
            font.setGlyphOrder(order)
            top.charset = list(order)
            font["hmtx"].metrics[gname] = (width, 0)
        for table in font["cmap"].tables:
            if table.platformID == 3 and table.platEncID in (1, 10):
                table.cmap[cp] = gname
        out = _cleanup_registered() / f"probe-{gname}-{cp:04X}.otf"
        font.save(str(out))
    finally:
        font.close()
    return out


def _probe_candidate(desktop_path, cp, gname, value, width):
    """Mid-band median stem of a candidate outline, units/1000 em."""
    return _stem_of_char(
        _probe_font(desktop_path, cp, gname, value, width), cp)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

class Resolved:
    """One codepoint's answer for one face, with the evidence behind it."""

    __slots__ = ("cp", "kind", "gname", "value", "width", "twin_cp", "note")

    def __init__(self, cp, kind, gname=None, value=None, width=None,
                 twin_cp=None, note=""):
        self.cp = cp
        self.kind = kind          # harvested | interpolated | extrapolated | alias
        self.gname = gname
        self.value = value
        self.width = width
        self.twin_cp = twin_cp
        self.note = note


def _derive(face, cp, gname, desktop_path, target_stem, italic):
    """Interpolate or extrapolate `gname` for a face the web cut does not ship.

    Returns (Resolved, report line). Falls back to the alias for this face alone
    when the derived glyph cannot be brought within STEM_TOL of `target_stem`.
    """
    basis = BASIS[italic]
    masters = []
    for name in basis:
        path = _web_path(name)
        if path is None:
            continue
        rec = _record(path, gname)
        if rec is not None:
            masters.append((name, rec[0], rec[1]))

    # Keep only the largest structurally-compatible group, and require the
    # middle master to be in it — an interpolation basis that excludes Regular
    # is extrapolating across the whole range and is not worth having.
    groups: dict = {}
    for name, value, width in masters:
        groups.setdefault(_signature(value), []).append((name, value, width))
    usable = max(groups.values(), key=len) if groups else []
    if len(usable) < 2:
        return None, (f"{chr(cp)} U+{cp:04X}  no compatible master pair "
                      f"({len(masters)} master(s), "
                      f"{len(groups)} incompatible group(s)) -> ALIAS")

    # Two anchors: the lightest and heaviest compatible masters. t=0 is the
    # lightest, t=1 the heaviest, and a derived face lands wherever its own
    # measured stem puts it — outside [0,1] for Air, Thin and Black.
    usable.sort(key=lambda m: basis.index(m[0]))
    (n0, v0, w0), (n1, v1, w1) = usable[0], usable[-1]

    # Secant iteration on t against the MEASURED stem. Same method and the same
    # reason as solve_weight_table: the relationship between t and the rendered
    # stem is not linear once the rasteriser and its hinting are involved, so it
    # is measured instead of modelled.
    hist = []
    t = 0.5
    best = None
    for _ in range(MAX_ITER):
        value = _lerp(v0, v1, t)
        width = w0 + (w1 - w0) * t
        got = _probe_candidate(desktop_path, cp, gname, value, round(width))
        if got is None:
            return None, (f"{chr(cp)} U+{cp:04X}  candidate did not rasterise "
                          f"at t={t:+.3f} -> ALIAS")
        err = got - target_stem
        if best is None or abs(err) < best[0]:
            best = (abs(err), t, got, value, round(width))
        if abs(err) <= STEM_TOL:
            break
        hist.append((t, got))
        if len(hist) >= 2 and hist[-1][1] != hist[-2][1]:
            (t0, s0), (t1, s1) = hist[-2], hist[-1]
            slope = (s1 - s0) / (t1 - t0)
        else:
            slope = (_probe_or_zero(desktop_path, cp, gname, v0, v1, w0, w1)
                     or 1.0)
        if abs(slope) < 1e-6:
            break
        t = t - err / slope
        if not -T_LIMIT <= t <= T_LIMIT:
            return None, (f"{chr(cp)} U+{cp:04X}  needs t={t:+.2f}, beyond the "
                          f"+/-{T_LIMIT} extrapolation limit -> ALIAS")

    err, t, got, value, width = best
    kind = "interpolated" if 0.0 <= t <= 1.0 else "extrapolated"
    line = (f"{chr(cp)} U+{cp:04X}  {kind:12s} t={t:+.3f} from {n0}/{n1}  "
            f"stem {got:5.1f} vs this face's own {target_stem:5.1f} "
            f"(err {err:+.1f}, tol {STEM_TOL})")
    if err > STEM_TOL:
        return None, line + "  -> MISSED TOLERANCE, ALIAS"

    # SHAPE INTEGRITY, and it is a separate question from weight. A glyph can hit
    # the target stem exactly and still be broken — see _stroke_spread's docstring
    # for the four faces that did. Checked after the stem converges, because a
    # candidate that is still mid-iteration is expected to be the wrong weight.
    twin_cp = HARVEST[cp][1]
    cand = _stroke_spread(_probe_font(desktop_path, cp, gname, value, width), cp)
    ref = _stroke_spread(desktop_path, twin_cp)
    if cand and ref and ref[3] > 0:
        excess = cand[3] / ref[3]
        line += (f"; spread p90/p10 {cand[3]:.2f} vs twin {ref[3]:.2f} "
                 f"= {excess:.2f}x")
        if excess > SPREAD_EXCESS_MAX:
            return None, line + (f"  -> WEIGHT NOT CONSISTENT WITHIN THE GLYPH "
                                 f"(limit {SPREAD_EXCESS_MAX}x), ALIAS")
    return Resolved(cp, kind, gname, value, width,
                    note=f"t={t:+.3f} stem {got:.1f} vs {target_stem:.1f}"), line


def _probe_or_zero(desktop_path, cp, gname, v0, v1, w0, w1):
    """Slope of stem against t, from the two anchors. First-step estimate only."""
    s0 = _probe_candidate(desktop_path, cp, gname, v0, round(w0))
    s1 = _probe_candidate(desktop_path, cp, gname, v1, round(w1))
    if s0 is None or s1 is None:
        return None
    return s1 - s0


def resolve(face: str, desktop_path, harvest_family="Aeonik"):
    """Decide how to close every gap in `face`. Returns (resolutions, report).

    `desktop_path` is the pristine Latin source for this face — read for the twin
    outlines, for the stem the derived glyphs are measured against, and as the
    rasterisation host for candidates. Never written.

    `harvest_family` gates the web-cut harvest, and the gate is load-bearing rather
    than defensive. The web cut here is AEONIK's. Slussen v1 already ships Δ, μ and
    Ω so it never reaches the harvest branch today — but if a future Slussen source
    dropped one, an ungated resolver would quietly graft an Aeonik outline into
    Slussen and every outline-level check would stay green. Pass the family and the
    harvest only fires for the family the masters belong to.
    """
    from fontTools.ttLib import TTFont

    italic = face.endswith("Italic")
    font = TTFont(str(desktop_path), lazy=True)
    try:
        cmap = font.getBestCmap()
    finally:
        font.close()

    out, report = [], []

    for cp, twin_cp in ALIAS_ONLY.items():
        if cp in cmap:
            continue
        if cmap.get(twin_cp) is None:
            report.append(f"{chr(cp)} U+{cp:04X}  twin U+{twin_cp:04X} absent "
                          f"too — CANNOT CLOSE")
            continue
        out.append(Resolved(cp, "alias", twin_cp=twin_cp))
        report.append(f"{chr(cp)} U+{cp:04X}  alias -> U+{twin_cp:04X} "
                      f"{cmap[twin_cp]}  SHAPE COMPROMISE, not an equivalent")

    for cp, (gname, twin_cp) in HARVEST.items():
        if cp in cmap:
            continue
        if harvest_family != "Aeonik":
            twin_name = cmap.get(twin_cp)
            if twin_name is None:
                report.append(f"{chr(cp)} U+{cp:04X}  missing, and no Aeonik "
                              f"harvest is permitted for {harvest_family} — "
                              f"CANNOT CLOSE")
                continue
            out.append(Resolved(cp, "alias", twin_cp=twin_cp))
            report.append(f"{chr(cp)} U+{cp:04X}  alias -> U+{twin_cp:04X} "
                          f"{twin_name}  (no {harvest_family} web cut to harvest)")
            continue
        web = _web_path(face)
        if web is not None:
            rec = _record(web, gname)
            if rec is not None:
                value, width = rec
                shares = cp in TWIN_SHARES_OUTLINE
                note = ""
                if shares and twin_cp in cmap:
                    twin_stem = _stem_of_char(desktop_path, twin_cp)
                    new_stem = _probe_candidate(desktop_path, cp, gname,
                                                value, width)
                    if twin_stem and new_stem:
                        note = (f"twin U+{twin_cp:04X} REDRAWN: stem "
                                f"{twin_stem:.1f} -> {new_stem:.1f}")
                out.append(Resolved(cp, "harvested", gname, value, width,
                                    twin_cp=twin_cp if shares else None,
                                    note=note))
                report.append(
                    f"{chr(cp)} U+{cp:04X}  harvested   from the web cut, "
                    f"w={width}"
                    + (f"; also replaces U+{twin_cp:04X} (twin consistency)"
                       if shares else "")
                    + (f"; {note}" if note else ""))
                continue

        # Not a web face: derive it, and verify against this face's own weight.
        target_stem = (_stem_of_char(desktop_path, twin_cp)
                       if twin_cp in cmap else None)
        if target_stem is None:
            out.append(Resolved(cp, "alias", twin_cp=twin_cp))
            report.append(f"{chr(cp)} U+{cp:04X}  no twin to measure against "
                          f"-> ALIAS -> U+{twin_cp:04X}")
            continue
        res, line = _derive(face, cp, gname, desktop_path, target_stem, italic)
        report.append(line)
        if res is None:
            out.append(Resolved(cp, "alias", twin_cp=twin_cp))
        else:
            if cp in TWIN_SHARES_OUTLINE:
                res.twin_cp = twin_cp
            out.append(res)

    return out, report


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def close_gaps(font, face: str, desktop_path, label="3e",
               harvest_family="Aeonik") -> set[str]:
    """Add the missing Greek/math coverage to `font`, in `glyf` format.

    Called from the builders while the font is in the `glyf` intermediate stage,
    which is where every other outline step in this pipeline runs.

    RETURNS THE SET OF GLYPH NAMES IT WROTE, and the caller MUST pass them to
    th_cff.convert_to_cff() alongside the Thai names. Anything not in that set is
    taken from the pristine Latin CFF verbatim — so a harvested outline written
    over an existing name (`uni2206`, `uni00B5`) would be silently discarded and
    the v1 twin would ship. That is the same trap `uni0E3F` fell into; see the
    convert_to_cff docstring.
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    resolutions, report = resolve(face, desktop_path, harvest_family)
    if not resolutions:
        print(f"     [{label}] Greek/math: nothing missing")
        return set()

    glyf = font["glyf"]
    hmtx = font["hmtx"]
    cmap_tables = [t for t in font["cmap"].tables
                   if t.platformID == 3 and t.platEncID in (1, 10)]
    written: set[str] = set()

    for res in resolutions:
        if res.kind == "alias":
            twin_name = font.getBestCmap().get(res.twin_cp)
            if twin_name is None:
                continue
            for table in cmap_tables:
                table.cmap[res.cp] = twin_name
            continue

        # TWIN CONSISTENCY, and which glyph NAME carries the outline matters.
        #
        # Where the Greek codepoint and its maths twin share one drawing, the
        # harvested outline is written into THE TWIN'S EXISTING GLYPH NAME
        # (`uni2206`, `uni00B5`) and both codepoints are pointed at it — rather
        # than adding a new `uni0394` and repointing `∆` away from its old glyph.
        # The difference is not cosmetic: the old name is referenced by the
        # source's own GPOS kern pairs and GSUB lookups, and orphaning it would
        # silently drop `∆`'s and `µ`'s kerning. Reusing the name keeps every
        # existing reference pointing at the glyph the reader now sees.
        target = res.gname
        if res.twin_cp is not None:
            twin_name = font.getBestCmap().get(res.twin_cp)
            if twin_name is not None:
                target = twin_name

        pen = TTGlyphPen(font.getGlyphSet())
        _replay(res.value, pen)
        glyph = pen.glyph()
        if target not in font.getGlyphOrder():
            font.setGlyphOrder(font.getGlyphOrder() + [target])
        glyf[target] = glyph
        glyph.recalcBounds(glyf)
        hmtx.metrics[target] = (res.width, getattr(glyph, "xMin", 0))
        written.add(target)
        for table in cmap_tables:
            table.cmap[res.cp] = target
            if res.twin_cp is not None:
                table.cmap[res.twin_cp] = target

    kinds: dict[str, int] = {}
    for res in resolutions:
        kinds[res.kind] = kinds.get(res.kind, 0) + 1
    summary = ", ".join(f"{n} {k}" for k, n in sorted(kinds.items()))
    print(f"     [{label}] Greek/math: {summary}")
    for line in report:
        print(f"          {line}")
    return written


def main() -> int:
    """Report what every desktop Aeonik face would get. Changes nothing."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--faces", default=None,
                    help="comma-separated face names (default: all 14)")
    ap.add_argument("--dir", default=str(ROOT / "assets" / "fonts" / "aeonik"),
                    help="directory of the desktop cut")
    args = ap.parse_args()

    src = Path(args.dir)
    faces = ([f.strip() for f in args.faces.split(",")] if args.faces else
             [p.stem.replace("Aeonik-", "") for p in sorted(src.glob("Aeonik-*.otf"))])

    worst = 0
    for face in faces:
        path = src / f"Aeonik-{face}.otf"
        if not path.exists():
            print(f"\n=== {face} — NOT FOUND: {path}")
            worst = 1
            continue
        print(f"\n=== {face} ===")
        _, report = resolve(face, path)
        if not report:
            print("     nothing missing")
        for line in report:
            print(f"     {line}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
