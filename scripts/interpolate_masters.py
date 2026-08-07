#!/usr/bin/env python3
"""
Lossless outline compatibilizer + master interpolator.

Aeonik and Bai Jamjuree ship as static instances, not as an interpolatable
master set. Their weights are topologically identical (contour counts match
across the whole family) but the per-weight curve optimisation applied at
export dropped different redundant points from each instance, so raw
point-wise interpolation is impossible: 'Regular' and 'Medium' disagree on
the point count of most glyphs.

This module reconciles that. For every pair of corresponding contours it
computes a common node set and splits each master's segments at the missing
positions using de Casteljau subdivision. Subdividing a Bezier at parameter
t yields two segments whose union is the *same curve* -- the outline is
mathematically unchanged, only its point count rises. Once both masters
carry nodes at the same normalised positions they are structurally
compatible and can be interpolated point-wise.

    interpolate(A, B, t)  ->  A + t * (B - A)

t in [0, 1] interpolates; t outside that range extrapolates, which is how
weights beyond a family's shipped range are generated.

Invariant (checked by --self-test): compatibilisation is lossless, so
t=0 must reproduce master A's outline exactly and t=1 master B's.

Usage:
  python3 interpolate_masters.py --self-test
"""

import warnings
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

warnings.filterwarnings("ignore")

# Cost of leaving a node unmatched during alignment, in units of normalised
# glyph size. Two nodes are paired when they sit closer together than twice
# this, so at 0.05 anything within 10% of the glyph's size pairs up rather
# than each side splitting separately.
SKIP_COST = 0.05

# A rotated start point is only accepted when it beats the font's own start
# point by this margin, so rotationally symmetric shapes (o, O, degree) keep
# their natural correspondence instead of being twisted by a marginal win.
ROTATION_MARGIN = 0.90

# How far the midpoint's enclosed area may drift from what a faithful blend
# would enclose before the correspondence is judged wrong. Measured over
# Aeonik's Light-to-Regular pairs the error runs smoothly -- 80% of contours
# land under 2% and the failures trail off to 24% -- so there is no natural
# cliff to sit on. 12% clears the visible defects (the percent sign's counter
# filling in solid at 20%) while sparing the mildly imperfect accents that
# make up most of the tail.
AREA_TOLERANCE = 0.12

# Samples per segment used to build the arc-length table.
ARC_SAMPLES = 16


# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------

def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def cubic_at(seg, t):
    """Evaluate a cubic segment (p0, c1, c2, p3) at parameter t."""
    p0, c1, c2, p3 = seg
    mt = 1.0 - t
    a = mt * mt * mt
    b = 3.0 * mt * mt * t
    c = 3.0 * mt * t * t
    d = t * t * t
    return (a * p0[0] + b * c1[0] + c * c2[0] + d * p3[0],
            a * p0[1] + b * c1[1] + c * c2[1] + d * p3[1])


def split_cubic(seg, t):
    """de Casteljau subdivision. The two halves trace the original curve."""
    p0, c1, c2, p3 = seg
    a = lerp(p0, c1, t)
    b = lerp(c1, c2, t)
    c = lerp(c2, p3, t)
    d = lerp(a, b, t)
    e = lerp(b, c, t)
    f = lerp(d, e, t)
    return (p0, a, d, f), (f, e, c, p3)


def line_to_cubic(p0, p1):
    """Represent a straight segment as a cubic so every segment is uniform."""
    return (p0, lerp(p0, p1, 1.0 / 3.0), lerp(p0, p1, 2.0 / 3.0), p1)


def quad_to_cubic(p0, q, p1):
    """Exact degree elevation of a quadratic to a cubic."""
    return (p0,
            (p0[0] + 2.0 / 3.0 * (q[0] - p0[0]), p0[1] + 2.0 / 3.0 * (q[1] - p0[1])),
            (p1[0] + 2.0 / 3.0 * (q[0] - p1[0]), p1[1] + 2.0 / 3.0 * (q[1] - p1[1])),
            p1)


def seg_length(seg):
    """Polyline approximation of a cubic's arc length."""
    total = 0.0
    prev = seg[0]
    for i in range(1, ARC_SAMPLES + 1):
        cur = cubic_at(seg, i / ARC_SAMPLES)
        total += ((cur[0] - prev[0]) ** 2 + (cur[1] - prev[1]) ** 2) ** 0.5
        prev = cur
    return total


def seg_t_at_fraction(seg, frac):
    """Map a fraction of a segment's arc length to its Bezier parameter.

    Arc length is not linear in t, so splitting at the geometrically right
    place needs this lookup. Shape is preserved for any t, but correspondence
    quality between masters is not, which is what this protects.
    """
    if frac <= 0.0:
        return 0.0
    if frac >= 1.0:
        return 1.0
    lengths = [0.0]
    prev = seg[0]
    for i in range(1, ARC_SAMPLES + 1):
        cur = cubic_at(seg, i / ARC_SAMPLES)
        lengths.append(lengths[-1] + ((cur[0] - prev[0]) ** 2 + (cur[1] - prev[1]) ** 2) ** 0.5)
        prev = cur
    target = frac * lengths[-1]
    for i in range(1, len(lengths)):
        if lengths[i] >= target:
            span = lengths[i] - lengths[i - 1]
            local = (target - lengths[i - 1]) / span if span else 0.0
            return (i - 1 + local) / ARC_SAMPLES
    return 1.0


# ---------------------------------------------------------------------------
# Glyph -> contours of cubic segments
# ---------------------------------------------------------------------------

def glyph_to_contours(glyph_set, name):
    """Decompose a glyph into closed contours of cubic segments.

    Handles both CFF (already cubic) and TrueType outlines, expanding the
    implied on-curve points that TrueType leaves between consecutive
    off-curve points.

    Uses a *decomposing* pen deliberately. A plain RecordingPen records
    composite glyphs as addComponent references rather than outlines, which
    this function would then read as having no contours at all -- silently
    emptying every accented Latin glyph and every precomposed Thai mark
    cluster, such as the nikhahit-plus-tone ligature in "น้ำ".
    """
    if name not in glyph_set:
        return None
    pen = DecomposingRecordingPen(glyph_set)
    try:
        glyph_set[name].draw(pen)
    except Exception:
        return None

    contours = []
    segments = []
    start = None
    current = None

    def flush():
        nonlocal segments, start, current
        if segments or start is not None:
            # Close the contour if the outline does not already return home.
            if current is not None and start is not None and _dist(current, start) > 1e-9:
                segments.append(line_to_cubic(current, start))
            if segments:
                contours.append(segments)
        segments = []
        start = None
        current = None

    for op, args in pen.value:
        if op == "moveTo":
            flush()
            start = current = tuple(args[0])
        elif op == "lineTo":
            end = tuple(args[0])
            segments.append(line_to_cubic(current, end))
            current = end
        elif op == "curveTo":
            # May carry several chained cubics.
            pts = [tuple(p) for p in args]
            for i in range(0, len(pts) - 2, 3):
                seg = (current, pts[i], pts[i + 1], pts[i + 2])
                segments.append(seg)
                current = pts[i + 2]
        elif op == "qCurveTo":
            pts = [tuple(p) if p is not None else None for p in args]
            if pts[-1] is None:
                # All-off-curve contour: synthesise the implied start point.
                implied = lerp(pts[-2], pts[0], 0.5)
                pts = pts[:-1] + [implied]
                if current is None:
                    start = current = implied
            offs, on = pts[:-1], pts[-1]
            for i, off in enumerate(offs):
                end = on if i == len(offs) - 1 else lerp(off, offs[i + 1], 0.5)
                segments.append(quad_to_cubic(current, off, end))
                current = end
        elif op in ("closePath", "endPath"):
            flush()

    flush()
    return contours


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


# ---------------------------------------------------------------------------
# Compatibilisation
# ---------------------------------------------------------------------------

def contour_params(contour):
    """Normalised arc-length position of each node, plus segment lengths."""
    lengths = [seg_length(s) for s in contour]
    total = sum(lengths)
    if total <= 0:
        n = len(contour)
        return [i / n for i in range(n)], lengths, total
    params = []
    acc = 0.0
    for L in lengths:
        params.append(acc / total)
        acc += L
    return params, lengths, total


def contour_at(contour, params, u):
    """Evaluate a contour at normalised arc-length position u."""
    n = len(contour)
    u = u % 1.0
    idx = n - 1
    for i in range(n):
        hi = params[i + 1] if i + 1 < n else 1.0
        if params[i] <= u < hi:
            idx = i
            break
    lo = params[idx]
    hi = params[idx + 1] if idx + 1 < n else 1.0
    span = hi - lo
    frac = (u - lo) / span if span > 0 else 0.0
    return cubic_at(contour[idx], seg_t_at_fraction(contour[idx], frac))


def rotate_contour(contour, r):
    return contour[r:] + contour[:r]


def _bbox_scale(contour):
    xs, ys = [], []
    for seg in contour:
        for p in seg:
            xs.append(p[0])
            ys.append(p[1])
    scale = max(max(xs) - min(xs), max(ys) - min(ys))
    return scale if scale > 1e-6 else 1.0


def best_rotation(ca, cb):
    """Choose which node of B corresponds to node 0 of A.

    Font tools normally preserve start points, so rotation 0 is the default
    and is only displaced when another alignment is clearly better.
    """
    pa, _, _ = contour_params(ca)
    scale = _bbox_scale(cb)
    nodes_a = [seg[0] for seg in ca]

    def cost(r):
        rb = rotate_contour(cb, r)
        pb, _, _ = contour_params(rb)
        total = 0.0
        for i, u in enumerate(pa):
            q = contour_at(rb, pb, u)
            total += _dist(nodes_a[i], q) / scale
        return total / len(pa)

    base = cost(0)
    best_r, best_c = 0, base
    for r in range(1, len(cb)):
        c = cost(r)
        if c < best_c:
            best_r, best_c = r, c
    if best_r != 0 and best_c >= base * ROTATION_MARGIN:
        return 0
    return best_r


def dp_align(ca, cb):
    """Align two contours' nodes by geometry, preserving order.

    Matching purely by arc-length position is not good enough: a heavier
    master distributes its length differently, so nodes drift and pair up
    with the wrong partners. Interpolation hides that -- the result still
    passes through both masters at t=0 and t=1 -- but extrapolation doubles
    every mis-pairing, which is what buckled the heavy Thai weights.

    So nodes are matched on where they actually sit, using a Needleman-Wunsch
    style pass that keeps the traversal monotonic. A node with no counterpart
    is skipped, meaning the opposite contour gets split at the corresponding
    place instead.

    Returns a list of ("match", i, j) / ("skipA", i, None) / ("skipB", None, j).
    """
    n, m = len(ca), len(cb)
    scale = max(_bbox_scale(ca), _bbox_scale(cb))
    nodes_a = [seg[0] for seg in ca]
    nodes_b = [seg[0] for seg in cb]

    INF = float("inf")
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0

    for i in range(n + 1):
        for j in range(m + 1):
            c = cost[i][j]
            if c == INF:
                continue
            if i < n and j < m:
                d = c + _dist(nodes_a[i], nodes_b[j]) / scale
                if d < cost[i + 1][j + 1]:
                    cost[i + 1][j + 1] = d
                    back[i + 1][j + 1] = ("match", i, j)
            if i < n and c + SKIP_COST < cost[i + 1][j]:
                cost[i + 1][j] = c + SKIP_COST
                back[i + 1][j] = ("skipA", i, None)
            if j < m and c + SKIP_COST < cost[i][j + 1]:
                cost[i][j + 1] = c + SKIP_COST
                back[i][j + 1] = ("skipB", None, j)

    events = []
    i, j = n, m
    while (i, j) != (0, 0):
        ev = back[i][j]
        if ev is None:
            return None
        events.append(ev)
        if ev[0] == "match":
            i, j = i - 1, j - 1
        elif ev[0] == "skipA":
            i -= 1
        else:
            j -= 1
    events.reverse()
    return events


def _fill_gaps(vals):
    """Fill None entries by spacing them evenly between known neighbours.

    A skipped node has no parameter of its own on the opposite contour, so
    it borrows one interpolated between the matched anchors that surround it.
    The list is cyclic, so the last gap wraps to the first known value.
    """
    k = len(vals)
    known = [idx for idx, v in enumerate(vals) if v is not None]
    if not known:
        return None
    out = list(vals)
    for pos in range(len(known)):
        i1 = known[pos]
        i2 = known[(pos + 1) % len(known)]
        gap = []
        idx = (i1 + 1) % k
        while idx != i2:
            gap.append(idx)
            idx = (idx + 1) % k
        if not gap:
            continue
        v1, v2 = out[i1], out[i2]
        if v2 <= v1:
            v2 += 1.0
        step = (v2 - v1) / (len(gap) + 1)
        for g, idx in enumerate(gap):
            out[idx] = (v1 + step * (g + 1)) % 1.0
    return out


def merge_params(ca, cb, pa, pb):
    """Shared node parameters for both contours, from a geometric alignment."""
    events = dp_align(ca, cb)
    if events is None:
        return None, None
    out_a, out_b = [], []
    for kind, i, j in events:
        out_a.append(pa[i] if kind in ("match", "skipA") else None)
        out_b.append(pb[j] if kind in ("match", "skipB") else None)
    return _fill_gaps(out_a), _fill_gaps(out_b)


def resample_contour(contour, targets):
    """Split a contour so its nodes sit at every parameter in `targets`.

    Purely additive: existing nodes survive and new ones are introduced by
    de Casteljau subdivision, so the traced outline is bit-for-bit the same
    curve.
    """
    params, _, _ = contour_params(contour)
    n = len(contour)

    # Group the requested splits by the segment they land in.
    per_seg = {i: [] for i in range(n)}
    for u in targets:
        idx = n - 1
        for i in range(n):
            hi = params[i + 1] if i + 1 < n else 1.0
            if params[i] <= u < hi:
                idx = i
                break
        lo = params[idx]
        hi = params[idx + 1] if idx + 1 < n else 1.0
        span = hi - lo
        if span <= 0:
            continue
        frac = (u - lo) / span
        if frac > 1e-6:  # frac ~0 means the node already exists here
            per_seg[idx].append(frac)

    out = []
    for i, seg in enumerate(contour):
        fracs = sorted(per_seg[i])
        if not fracs:
            out.append(seg)
            continue
        remaining = seg
        consumed = 0.0
        for frac in fracs:
            # Re-map the split point onto the shrinking tail of the segment.
            local = (frac - consumed) / (1.0 - consumed)
            t = seg_t_at_fraction(remaining, local)
            if t <= 1e-6 or t >= 1.0 - 1e-6:
                continue
            head, remaining = split_cubic(remaining, t)
            out.append(head)
            consumed = frac
        out.append(remaining)
    return out


def _contour_signature(contour, n=48):
    """Centroid and enclosed area, used to identify a contour across masters."""
    pts = _sample_contour(contour, n)
    area = 0.0
    cx = cy = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area /= 2.0
    if abs(area) < 1e-9:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (sum(xs) / len(xs), sum(ys) / len(ys)), 0.0
    return (cx / (6 * area), cy / (6 * area)), area


def match_contours(contours_a, contours_b):
    """Pair contours across masters by geometry rather than by index.

    Masters do not always store a glyph's contours in the same order -- in
    Aeonik's 'oe' the two counters are swapped between Light and Regular.
    Pairing by position would then interpolate the 'o' counter into the 'e'
    counter, so contours are matched on where they sit and how much they
    enclose instead.

    Returns contours_b reordered to correspond to contours_a, or None.
    """
    n = len(contours_a)
    if n != len(contours_b):
        return None
    if n <= 1:
        return contours_b

    sig_a = [_contour_signature(c) for c in contours_a]
    sig_b = [_contour_signature(c) for c in contours_b]
    scale = max(_bbox_scale(contours_a[0]), _bbox_scale(contours_b[0]), 1.0)
    max_area = max([abs(s[1]) for s in sig_a] + [abs(s[1]) for s in sig_b]) or 1.0

    def cost(i, j):
        (ax, ay), aa = sig_a[i]
        (bx, by), ba = sig_b[j]
        centroid = _dist((ax, ay), (bx, by)) / scale
        size = abs(abs(aa) - abs(ba)) / max_area
        winding = 0.0 if (aa > 0) == (ba > 0) else 1.0
        return centroid + size + winding

    order = None
    if n <= 7:
        # Small glyphs: search every pairing for the true optimum.
        from itertools import permutations
        best = float("inf")
        for perm in permutations(range(n)):
            total = sum(cost(i, perm[i]) for i in range(n))
            if total < best:
                best, order = total, perm
    else:
        # Many contours: greedy nearest match, which is ample at this size.
        remaining = set(range(n))
        order = []
        for i in range(n):
            j = min(remaining, key=lambda j: cost(i, j))
            remaining.discard(j)
            order.append(j)

    return [contours_b[j] for j in order]


def _enclosed_area(contour, n=64):
    pts = _sample_contour(contour, n)
    total = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def _resample_pair(ca, cb, rotation):
    rb = rotate_contour(cb, rotation)
    pa, _, _ = contour_params(ca)
    pb, _, _ = contour_params(rb)
    ta, tb = merge_params(ca, rb, pa, pb)
    if ta is None or tb is None:
        return None
    ra, rbb = resample_contour(ca, ta), resample_contour(rb, tb)
    if len(ra) != len(rbb):
        return None
    return ra, rbb


def align_pair(ca, cb):
    """Compatibilise one contour pair, verifying the result actually blends.

    Structural compatibility is not the same as *correct* correspondence.
    Pair a round counter with a rotated copy of itself and every node still
    lines up, but the midpoint interpolates to a visibly smaller shape --
    which is how the counters in Aeonik's percent sign were filling in solid.

    The midpoint area is therefore checked against the average of the two
    masters, which a good correspondence preserves and a bad one shrinks.
    A poor result triggers a search over every start point, and if nothing
    holds up the pairing is rejected so the caller can keep a master's glyph
    instead of emitting a broken one.
    """
    # Area is quadratic in the coordinates, so a correct blend does NOT land
    # on the average of the two areas: blending circles of radius 1 and 2
    # gives radius 1.5, enclosing 2.25pi rather than the mean 2.5pi. The
    # midpoint of the square roots is the right expectation, and it predicts
    # a well-corresponded contour to within a fraction of a percent.
    area_a, area_b = _enclosed_area(ca), _enclosed_area(cb)
    sign = -1.0 if (area_a + area_b) < 0 else 1.0
    target = sign * ((abs(area_a) ** 0.5 + abs(area_b) ** 0.5) / 2.0) ** 2
    scale = max(abs(area_a), abs(area_b), 1.0)

    def error(pair):
        blended = interpolate_contours([pair[0]], [pair[1]], 0.5)[0]
        return abs(_enclosed_area(blended) - target) / scale

    first = best_rotation(ca, cb)
    best = None
    pair = _resample_pair(ca, cb, first)
    if pair is not None:
        err = error(pair)
        if err <= AREA_TOLERANCE:
            return pair
        best = (err, pair)

    for r in range(len(cb)):
        if r == first:
            continue
        pair = _resample_pair(ca, cb, r)
        if pair is None:
            continue
        err = error(pair)
        if err <= AREA_TOLERANCE:
            return pair
        if best is None or err < best[0]:
            best = (err, pair)

    return None


def compatibilize(contours_a, contours_b):
    """Make two glyphs structurally identical, or return None if impossible."""
    if contours_a is None or contours_b is None:
        return None
    if len(contours_a) != len(contours_b):
        return None

    contours_b = match_contours(contours_a, contours_b)
    if contours_b is None:
        return None

    out_a, out_b = [], []
    for ca, cb in zip(contours_a, contours_b):
        if not ca or not cb:
            return None
        pair = align_pair(ca, cb)
        if pair is None:
            return None
        out_a.append(pair[0])
        out_b.append(pair[1])
    return out_a, out_b


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------

def interpolate_contours(ca, cb, t):
    out = []
    for sa, sb in zip(ca, cb):
        segs = []
        for pa, pb in zip(sa, sb):
            segs.append(tuple(lerp(a, b, t) for a, b in zip(pa, pb)))
        out.append(segs)
    return out


def draw_contours(contours, pen):
    for contour in contours:
        pen.moveTo(contour[0][0])
        for seg in contour:
            pen.curveTo(seg[1], seg[2], seg[3])
        pen.closePath()


def interpolate_glyph(glyphset_a, glyphset_b, name_a, name_b, t):
    """Interpolate one glyph. Returns contours, or None when incompatible."""
    ca = glyph_to_contours(glyphset_a, name_a)
    cb = glyph_to_contours(glyphset_b, name_b)
    if ca is None or cb is None:
        return None
    if not ca and not cb:
        return []          # both blank (space etc.)
    pair = compatibilize(ca, cb)
    if pair is None:
        return None
    return interpolate_contours(pair[0], pair[1], t)


# ---------------------------------------------------------------------------
# Self-test: compatibilisation must be lossless
# ---------------------------------------------------------------------------

def _sample_contour(contour, n):
    params, _, _ = contour_params(contour)
    return [contour_at(contour, params, i / n) for i in range(n)]


def _point_segment_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    if L2 <= 1e-12:
        return _dist(p, a)
    t = ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return _dist(p, (a[0] + t * vx, a[1] + t * vy))


def max_deviation(got, ref, n_got=60, n_ref=240):
    """Directed Hausdorff distance from `got` to `ref`, per contour.

    Start points may be rotated during compatibilisation, so comparing node
    by node would measure the rotation rather than the geometry. Measuring
    each sampled point against the reference *polyline* -- not merely against
    its sample points -- keeps this invariant to start point and free of the
    discretisation floor that nearest-sample matching would impose.
    """
    if len(got) != len(ref):
        return float("inf")
    # Compatibilisation may reorder contours and rotate start points, so each
    # generated contour is scored against its best match rather than against
    # whatever sits at the same index.
    return max((min(_contour_deviation(cg, cr, n_got, n_ref) for cr in ref)
                for cg in got), default=0.0)


def _contour_deviation(cg, cr, n_got=60, n_ref=240):
    """Largest distance from any point of contour `cg` to the curve `cr`."""
    worst = 0.0
    gp = _sample_contour(cg, n_got)
    rp = _sample_contour(cr, n_ref)
    rparams, _, _ = contour_params(cr)
    for g in gp:
        # Coarse pass: locate the nearest chord of the reference polyline.
        best_i, best_d = 0, float("inf")
        for i in range(len(rp)):
            d = _point_segment_dist(g, rp[i], rp[(i + 1) % len(rp)])
            if d < best_d:
                best_i, best_d = i, d
        # Refine pass: a coarse polyline cuts corners, so re-evaluate the
        # curve itself around the winning chord. Without this the metric
        # reports its own chord error instead of the outline's deviation.
        lo = (best_i - 1) / n_ref
        hi = (best_i + 2) / n_ref
        fine = [contour_at(cr, rparams, lo + (hi - lo) * k / 64)
                for k in range(65)]
        for i in range(len(fine) - 1):
            best_d = min(best_d, _point_segment_dist(g, fine[i], fine[i + 1]))
        worst = max(worst, best_d)
    return worst


def self_test():
    assets = Path(__file__).parent.parent / "assets" / "fonts"
    checks = [
        ("Aeonik CFF ", assets / "aeonik/Aeonik-Light.otf",
         assets / "aeonik/Aeonik-Regular.otf", 0x20, 0x17F),
        ("Bai TTF    ", assets / "bai-jamjuree/BaiJamjuree-Light.ttf",
         assets / "bai-jamjuree/BaiJamjuree-Regular.ttf", 0x0E01, 0x0E5B),
    ]

    overall_ok = True
    for label, pa, pb, lo, hi in checks:
        fa, fb = TTFont(str(pa)), TTFont(str(pb))
        gsa, gsb = fa.getGlyphSet(), fb.getGlyphSet()
        cma, cmb = fa.getBestCmap(), fb.getBestCmap()
        cps = [c for c in sorted(cma) if c in cmb and lo <= c <= hi]

        compat = incompat = 0
        worst0 = worst1 = 0.0
        for cp in cps:
            ca = glyph_to_contours(gsa, cma[cp])
            cb = glyph_to_contours(gsb, cmb[cp])
            pair = compatibilize(ca, cb)
            if pair is None:
                incompat += 1
                continue
            compat += 1
            # t=0 must reproduce A, t=1 must reproduce B.
            worst0 = max(worst0, max_deviation(
                interpolate_contours(pair[0], pair[1], 0.0), ca))
            worst1 = max(worst1, max_deviation(
                interpolate_contours(pair[0], pair[1], 1.0), cb))

        total = compat + incompat
        pct = 100 * compat / total if total else 0
        ok = worst0 < 0.5 and worst1 < 0.5
        overall_ok &= ok
        print(f"  {label} compatible {compat}/{total} ({pct:.0f}%)  "
              f"max deviation t=0: {worst0:.4f}u  t=1: {worst1:.4f}u  "
              f"[{'LOSSLESS' if ok else 'LOSSY -- INVESTIGATE'}]")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Outline compatibilizer / interpolator")
    ap.add_argument("--self-test", action="store_true",
                    help="verify compatibilisation is lossless")
    args = ap.parse_args()

    if args.self_test:
        print("\nCompatibilisation self-test (t=0 must reproduce master A, t=1 master B)")
        sys.exit(self_test())
    ap.print_help()
