#!/usr/bin/env python3
"""th_mark_clearance.py — give Thai upper marks enough air to survive Word.

WHY THIS EXISTS

Bai Jamjuree sets its upper vowels and tone marks very close to the consonant.
Measured as the minimum vertical clearance between base ink and mark ink, in
1/1000 em, against Sarabun (which Siwatch nominated as correctly engineered):

    group          Sarabun p10   Bai p10   TH-Aeonik p10
    upper vowel        62.5        40.0        31.2
    tone only          92.9        50.0        40.0
    vowel + tone       62.5        37.5        25.0
    lower vowel        56.2        62.8        56.2

At 11 pt on a 96 dpi screen one em is 14.7 px, so 40/1000 em is 0.59 px. It
rounds away and the mark fuses into the consonant: `กลิ่น`, `เพื่อ` and `สิทธิ์`
render as blobs in Word while Sarabun stays legible at the same size. The PDF
looks better than the screen only because it rasterises at a higher resolution,
which is why this reads as a Word bug and is really a font-metrics one.

TH-Aeonik is worse than Bai because the Thai is scaled to the Latin x-height
(~0.87) and then emboldened to match the Latin stem — the first shrinks the gap
proportionally and the second eats into what is left from both sides.

Lower vowels need no correction; all three fonts agree there.

WHAT IT DOES

For every Thai base glyph, measures the true vertical clearance to each upper
mark that can attach to it, and raises that base's top mark-to-base anchor by
the shortfall. Raising the base anchor lifts the whole stack, so mark-to-mark
spacing inside the stack is preserved — only the gap to the consonant grows.

Clearance is measured from flattened outlines rather than a raster, so it is
exact at any size and needs no temp files during the build.

USAGE
    python3 scripts/th_mark_clearance.py            # report, touches nothing
    python3 scripts/th_mark_clearance.py --compare  # add Sarabun as reference
"""

import sys
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent

# Target clearance in 1/1000 em, measured against the consonant body. Sarabun,
# the reference, runs worst 56 / p10 73 / median 86; Bai Jamjuree 57 / 66 / 80.
# 72 sits at Sarabun's 10th percentile and just above one pixel at 11 pt on a
# 96 dpi screen (1 em = 14.7 px, so 68/1000 em = 1 px). Aiming at Sarabun's
# median instead would float the marks and change Bai's texture more than the
# defect warrants — the goal is to clear the pixel grid, not to redraw the
# script's proportions.
TARGET = 72.0

# Never move a mark by more than this. The heavy weights need most of it:
# TH-Aeonik-Black starts at a median of 0.6 because emboldening grows the
# consonant and the mark toward each other. A base short by more than the cap
# has a shape problem the anchor cannot fix, and shoving the mark further would
# look worse than the crowding.
MAX_RAISE = 130.0

# Upper marks, by Unicode. Split because they attach at different heights and a
# base's binding constraint is usually one specific mark.
UPPER_VOWELS = [0x0E31, 0x0E34, 0x0E35, 0x0E36, 0x0E37, 0x0E47, 0x0E4D]
TONES = [0x0E48, 0x0E49, 0x0E4A, 0x0E4B, 0x0E4C]
UPPER_MARKS = UPPER_VOWELS + TONES

# Thai consonants plus the independent vowels that take upper marks.
THAI_BASES = list(range(0x0E01, 0x0E2F)) + [0x0E2F, 0x0E30, 0x0E32, 0x0E40,
                                            0x0E41, 0x0E44]

CURVE_STEPS = 12       # samples per curve segment
BUCKET = 8             # x-resolution of the profile, in font units


# ---------------------------------------------------------------------------
# Outline profiles
# ---------------------------------------------------------------------------

def _flatten(glyph_set, name):
    """Glyph outline as a list of (x, y) points, curves sampled to polylines."""
    rp = DecomposingRecordingPen(glyph_set)
    try:
        glyph_set[name].draw(rp)
    except Exception:
        return []
    pts, cur = [], None
    for op, args in rp.value:
        if op == "moveTo":
            cur = args[0]
            pts.append(cur)
        elif op == "lineTo":
            pts.extend(_seg(cur, args[0]))
            cur = args[0]
        elif op == "qCurveTo":
            on = args[-1]
            if on is None:                      # all-off-curve TrueType contour
                continue
            prev = cur
            for ctrl in args[:-1]:
                pts.extend(_quad(prev, ctrl, on))
                prev = on
            cur = on
        elif op == "curveTo":
            pts.extend(_cubic(cur, *args))
            cur = args[-1]
    return pts


def _seg(a, b, n=6):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            for i in range(n + 1)]


def _quad(a, c, b, n=CURVE_STEPS):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
                    u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]))
    return out


def _cubic(a, c1, c2, b, n=CURVE_STEPS):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * b[0],
                    u**3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * b[1]))
    return out


def grid(points, cell):
    """Bucket points into a uniform grid for nearest-neighbour queries."""
    g = {}
    for x, y in points:
        g.setdefault((int(x // cell), int(y // cell)), []).append((x, y))
    return g


def min_distance(base_pts_grid, mark_pts, dx, dy, cell, limit):
    """Smallest distance from any positioned mark point to any base point.

    A column-wise vertical measure was tried first and is wrong for the tall
    consonants: it reads `ป` + `ํ` as a deep collision because the mark shares
    columns with the ascender, when the mark actually sits in the open space
    beside it. Sarabun scores the same false negative, which is the tell. True
    2-D distance matches what the eye and the rasteriser both see.

    Only the 3x3 cell neighbourhood is searched, so anything further away than
    `limit` is reported as `limit` — this measure exists to find marks that are
    too close, and the exact value of a comfortable gap does not matter.
    """
    best = limit
    for mx, my in mark_pts:
        px, py = mx + dx, my + dy
        cx, cy = int(px // cell), int(py // cell)
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for bx, by in base_pts_grid.get((i, j), ()):
                    d = ((px - bx) ** 2 + (py - by) ** 2) ** 0.5
                    if d < best:
                        best = d
    return best


# ---------------------------------------------------------------------------
# GPOS anchors
# ---------------------------------------------------------------------------

def _subtables(font, kind):
    if "GPOS" not in font:
        return
    for lk in font["GPOS"].table.LookupList.Lookup:
        subs = lk.SubTable
        if lk.LookupType == 9:
            subs = [s.ExtSubTable for s in subs if s.ExtSubTable is not None]
        for st in subs:
            if st.__class__.__name__ == kind:
                yield st


def attachments(font, base_names, mark_names):
    """Every (base, mark) pair that can actually attach, with both anchors.

    Mark classes matter and an earlier version of this ignored them: it paired
    every mark with every anchor on the base, including the below-vowel anchor,
    and reported collisions for combinations the shaper never produces. A mark
    attaches only to the BaseAnchor whose index equals its own MarkRecord.Class.

    Yields (base_glyph, base_anchor, mark_glyph, mark_anchor).
    """
    bset, mset = set(base_names), set(mark_names)
    for st in _subtables(font, "MarkBasePos"):
        mcov = st.MarkCoverage.glyphs
        bcov = st.BaseCoverage.glyphs
        marks = []
        for mi, mn in enumerate(mcov):
            if mn not in mset:
                continue
            mr = st.MarkArray.MarkRecord[mi]
            if mr.MarkAnchor is not None:
                marks.append((mn, mr.Class, mr.MarkAnchor))
        if not marks:
            continue
        for bi, bn in enumerate(bcov):
            if bn not in bset:
                continue
            rec = st.BaseArray.BaseRecord[bi]
            for mn, cls, ma in marks:
                if cls < len(rec.BaseAnchor):
                    ba = rec.BaseAnchor[cls]
                    if ba is not None:
                        yield bn, ba, mn, ma


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def mark_attachments(font, vowel_names, tone_names):
    """Mark-to-mark pairs: a tone sitting on an upper vowel.

    This is the second level of the stack — `ครั้ง`, `สิทธิ์`, `เพื่อ` — and it
    needs its own correction. Raising the base anchor lifts the whole stack
    together and does nothing for the gap *inside* it.

    Yields (vowel_glyph, vowel_anchor, tone_glyph, tone_anchor).
    """
    vset, tset = set(vowel_names), set(tone_names)
    for st in _subtables(font, "MarkMarkPos"):
        m1cov = st.Mark1Coverage.glyphs        # the mark being attached
        m2cov = st.Mark2Coverage.glyphs        # the mark attached to
        m1 = []
        for i, gn in enumerate(m1cov):
            if gn not in tset:
                continue
            rec = st.Mark1Array.MarkRecord[i]
            if rec.MarkAnchor is not None:
                m1.append((gn, rec.Class, rec.MarkAnchor))
        if not m1:
            continue
        for j, gn in enumerate(m2cov):
            if gn not in vset:
                continue
            rec2 = st.Mark2Array.Mark2Record[j]
            for tn, cls, ta in m1:
                if cls < len(rec2.Mark2Anchor):
                    va = rec2.Mark2Anchor[cls]
                    if va is not None:
                        yield gn, va, tn, ta


def clearances(font, level="base"):
    """Worst clearance per anchor, in 1/1000 em.

    `level="base"`  consonant -> first mark   (MarkBasePos)
    `level="mark"`  upper vowel -> tone       (MarkMarkPos)

    Keyed by the anchor object so the fix raises exactly the anchor that is
    short, rather than every anchor on the glyph.
    """
    upem = font["head"].unitsPerEm
    k = 1000.0 / upem
    cell = upem * 0.16                 # ~160/1000 em search radius
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    names = lambda cps: [cmap[cp] for cp in cps if cp in cmap]

    if level == "base":
        pairs = attachments(font, names(THAI_BASES), names(UPPER_MARKS))
    else:
        pairs = mark_attachments(font, names(UPPER_VOWELS), names(TONES))

    # Ink above the body height belongs to an ascender (ป ฝ ฟ ฬ), and a mark
    # tucked into the space beside one is close to it horizontally by design —
    # Sarabun scores 7/1000 em on ป+ํ for exactly that reason. Counting it would
    # drive the correction to float the mark above the stem, which is wrong.
    # Clearance is therefore measured against the consonant body only, which is
    # also the only distance that raising the anchor actually changes.
    body_top = None
    if level == "base" and 0x0E01 in cmap:
        pts = _flatten(gs, cmap[0x0E01])
        if pts:
            body_top = max(y for _, y in pts) + upem * 0.02

    lower_grid, upper_pts = {}, {}
    out = {}
    for bn, ba, mn, ma in pairs:
        if bn not in lower_grid:
            pts = _flatten(gs, bn)
            if body_top is not None:
                pts = [(x, y) for x, y in pts if y <= body_top]
            lower_grid[bn] = grid(pts, cell)
        if mn not in upper_pts:
            upper_pts[mn] = _flatten(gs, mn)
        if not lower_grid[bn] or not upper_pts[mn]:
            continue
        d = min_distance(lower_grid[bn], upper_pts[mn],
                         ba.XCoordinate - ma.XCoordinate,
                         ba.YCoordinate - ma.YCoordinate, cell, cell)
        key = id(ba)
        cur = out.get(key)
        if cur is None or d * k < cur[0]:
            out[key] = (d * k, bn, mn, ba)
    return out


MAX_PASSES = 8


def _raise_level(font, level, target, max_raise):
    """Iterate to the target, because clearance does not grow 1:1 with lift.

    The nearest point between a mark and a consonant is often diagonal, so
    lifting the anchor by d increases the distance by less than d. A single
    pass computed from the shortfall therefore undershoots, and it undershoots
    worst exactly where the deficit is largest — TH-Slussen-Bold stalled at 60
    against a target of 72 and raising the per-anchor cap did not move it,
    which is the tell that the cap was never the binding constraint.

    `max_raise` is a budget on the total lift per anchor across all passes, not
    per pass.
    """
    upem = font["head"].unitsPerEm
    k = 1000.0 / upem
    budget = max_raise / k                     # font units
    before = clearances(font, level)
    spent = {}
    for _ in range(MAX_PASSES):
        cur = clearances(font, level)
        progressed = False
        for key, (gap, bn, mn, anchor) in cur.items():
            if gap >= target:
                continue
            used = spent.get(key, 0.0)
            step = min((target - gap) / k, budget - used)
            if step < 1:
                continue
            anchor.YCoordinate = int(round(anchor.YCoordinate + step))
            spent[key] = used + step
            progressed = True
        if not progressed:
            break
    after = clearances(font, level)
    capped = sum(1 for key, (gap, *_) in after.items()
                 if gap < target and spent.get(key, 0.0) >= budget - 1)
    return before, len(spent), capped


def raise_upper_marks(font, target=TARGET, max_raise=MAX_RAISE, verbose=True):
    """Open up both levels of the Thai stack until each clears `target`.

    Base level first, then mark level. Order matters only for reporting — the
    two sets of anchors are disjoint, so neither correction disturbs the other's
    measurement.
    """
    stats = {}
    for level in ("base", "mark"):
        before, moved, capped = _raise_level(font, level, target, max_raise)
        after = clearances(font, level)
        stats[level] = (before, after, moved, capped)

    if verbose:
        bits = []
        for level in ("base", "mark"):
            before, after, moved, capped = stats[level]
            if not before:
                continue
            b = sorted(v[0] for v in before.values())
            a = sorted(v[0] for v in after.values())
            bits.append(f"{level} {moved}/{len(before)}"
                        f"{f'({capped} capped)' if capped else ''} "
                        f"p10 {b[len(b)//10]:.0f}->{a[len(a)//10]:.0f}")
        print(f"     [3c] Mark clearance (target {target:.0f}): " + " | ".join(bits))
    return sum(s[2] for s in stats.values())


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _report(paths):
    import statistics as st
    for label, p in paths:
        p = Path(p)
        if not p.exists():
            print(f"{label:<22} (missing: {p})")
            continue
        f = TTFont(p, fontNumber=0)
        print(f"{label}")
        for level, what in (("base", "consonant -> mark"), ("mark", "vowel -> tone")):
            c = clearances(f, level)
            if not c:
                print(f"    {what:<22} (no anchors)")
                continue
            v = sorted(x[0] for x in c.values())
            tight = sorted((g, bn, mn) for g, bn, mn, _ in c.values())[:5]
            print(f"    {what:<22} worst {v[0]:6.1f}  p10 {v[len(v)//10]:6.1f}  "
                  f"median {st.median(v):6.1f}  ({len(v)} anchors)   "
                  + " ".join(f"{n}+{m}={g:.0f}" for g, n, m in tight))


def main():
    paths = [
        ("TH-Aeonik Regular", ROOT / "assets/fonts/th-aeonik/TH-Aeonik-Regular.otf"),
        ("TH-Aeonik Bold", ROOT / "assets/fonts/th-aeonik/TH-Aeonik-Bold.otf"),
        ("TH-Slussen Regular", ROOT / "assets/fonts/th-slussen/TH-Slussen-Regular.otf"),
        ("BaiJamjuree Regular", ROOT / "assets/fonts/bai-jamjuree/BaiJamjuree-Regular.ttf"),
    ]
    if "--compare" in sys.argv:
        paths.append(("Sarabun Regular (ref)",
                      "/mnt/c/Users/OhYeaH/Downloads/Sarabun/Sarabun-Regular.ttf"))
    print("\nminimum vertical clearance, base ink -> upper-mark ink, in 1/1000 em\n")
    _report(paths)
    print(f"\ntarget {TARGET:.0f}  (Sarabun's 10th percentile)\n")


if __name__ == "__main__":
    main()
