#!/usr/bin/env python3
"""Re-seat Thai on the Latin baseline after the weight match has moved it.

Siwatch, 2026-08-03: *"make sure the Latin and Thai character when type together
are on the same line level."*

Bai Jamjuree draws every flat-bottomed Thai consonant with its bottom edge at
exactly y=0, in every weight — `ก` `ง` `บ` `ม` `ว` `ส` all sit on the baseline
like `H` and `n` do. This pipeline breaks that. `th_thai_prep` weight-matches the
Thai to the Latin stem with FontForge `changeWeight`, which grows the outline in
*every* direction, so a consonant that sat at 0 ends up below it. The Latin is
byte-identical to the source and does not move, so the two scripts drift apart.

Measured, flat-bottomed Thai consonant bottoms in 1/1000 em, against Latin at 0:

    TH-Aeonik   Air +8   Thin 0   Regular -1   Medium -6   Bold -14   Black -28
    TH-Slussen                    Regular -4   Medium -6   SemiBold -8   Bold -20

Monotonic in the weight change, and it flips sign for the thinned weights — the
signature of `changeWeight`, not of anything else in the pipeline. Invisible in
Regular; about a pixel at a 26 pt Black heading, which is where it shows.

The correction is a rigid translation of the Thai bases by the measured offset.
Marks are deliberately *not* translated: a mark is positioned at
`base_origin + base_anchor - mark_anchor`, so moving the base anchor carries the
whole stack with it. Translating the marks as well would move them twice.

Run before `th_mark_clearance.raise_upper_marks` so clearance is measured on the
seated geometry. The translation is rigid, so it does not change clearance —
this is ordering for clarity, not for correctness.
"""
from __future__ import annotations

import statistics

from fontTools.pens.boundsPen import BoundsPen

# Flat-bottomed Thai consonants: no curve overshoot, so their bottom edge *is*
# the baseline. Round-bottomed ones (`ค` `ต` `อ`) overshoot by ~10 units in the
# source and would bias the measurement.
FLAT_THAI = "กงบปฝฟมยรลวสหฬ"

# Flat-bottomed Latin, for the reference. All sit at exactly 0 in Aeonik and
# Slussen, and stay there because the Latin outlines are never touched.
FLAT_LATIN = "HInxlLETFm"

# Below this the correction is not worth the churn — it is inside the rounding
# of the source outlines themselves.
DEADBAND = 2.0


def _flat_bottoms(font, chars):
    """Bottom edge of each flat-bottomed glyph in `chars`, in 1/1000 em."""
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    scale = 1000.0 / font["head"].unitsPerEm
    out = []
    for ch in chars:
        name = cmap.get(ord(ch))
        if not name:
            continue
        pen = BoundsPen(glyphs)
        try:
            glyphs[name].draw(pen)
        except Exception:
            continue
        if pen.bounds:
            out.append(pen.bounds[1] * scale)
    return out


def measure(font):
    """(thai_seat, latin_seat, offset) in 1/1000 em. Offset < 0 means Thai sank."""
    thai = _flat_bottoms(font, FLAT_THAI)
    latin = _flat_bottoms(font, FLAT_LATIN)
    if not thai or not latin:
        return None, None, 0.0
    t, l = statistics.median(thai), statistics.median(latin)
    return t, l, t - l


def _thai_glyphs(font):
    """Thai glyph names split into (bases, marks) by their GDEF class.

    Marks are excluded from the translation on purpose — see the module
    docstring. `fix_thai_gdef` must have run first, or every Thai glyph looks
    like a base and the marks get moved twice.
    """
    classes = {}
    if "GDEF" in font and font["GDEF"].table.GlyphClassDef is not None:
        classes = font["GDEF"].table.GlyphClassDef.classDefs
    bases, marks = [], []
    for name in font.getGlyphOrder():
        if not name.startswith("uni0E"):
            continue
        (marks if classes.get(name) == 3 else bases).append(name)
    return bases, marks


def _translate_glyphs(font, names, dy):
    """Shift `names` up by `dy` font units, in place, in the glyf table."""
    glyf = font["glyf"]
    shifted = set(names)
    n = 0
    for name in names:
        g = glyf[name]
        if g.numberOfContours == 0:
            continue
        if g.isComposite():
            # A composite whose components are all being shifted inherits the
            # move; shifting its offsets too would double it.
            for comp in g.components:
                if comp.glyphName not in shifted:
                    comp.y += dy
            n += 1
            continue
        coords = g.coordinates
        for i in range(len(coords)):
            x, y = coords[i]
            coords[i] = (x, y + dy)
        g.recalcBounds(glyf)
        n += 1
    return n


def _translate_base_anchors(font, base_names, dy):
    """Shift every mark-attachment anchor that lives on a translated base."""
    if "GPOS" not in font:
        return 0
    bset = set(base_names)
    n = 0
    for lookup in font["GPOS"].table.LookupList.Lookup:
        subs = lookup.SubTable
        if lookup.LookupType == 9:
            subs = [s.ExtSubTable for s in subs if s.ExtSubTable is not None]
        for st in subs:
            kind = st.__class__.__name__
            if kind == "MarkBasePos":
                for gi, gname in enumerate(st.BaseCoverage.glyphs):
                    if gname not in bset:
                        continue
                    for anchor in st.BaseArray.BaseRecord[gi].BaseAnchor:
                        if anchor is not None:
                            anchor.YCoordinate += dy
                            n += 1
            elif kind == "MarkLigPos":
                for gi, gname in enumerate(st.LigatureCoverage.glyphs):
                    if gname not in bset:
                        continue
                    for comp in st.LigatureArray.LigatureAttach[gi].ComponentRecord:
                        for anchor in comp.LigatureAnchor:
                            if anchor is not None:
                                anchor.YCoordinate += dy
                                n += 1
    return n


def seat_thai_on_baseline(font, verbose=True):
    """Translate Thai bases so their flat bottoms return to the Latin baseline."""
    thai, latin, offset = measure(font)
    if thai is None:
        if verbose:
            print("     [3c] baseline: no Thai or no Latin to measure")
        return 0.0
    if abs(offset) < DEADBAND:
        if verbose:
            print(f"     [3c] baseline: Thai {thai:+.0f} vs Latin {latin:+.0f}, "
                  f"offset {offset:+.1f} — within deadband, left alone")
        return 0.0

    upem = font["head"].unitsPerEm
    dy = -round(offset * upem / 1000.0)          # font units, up is positive
    bases, marks = _thai_glyphs(font)
    n_glyphs = _translate_glyphs(font, bases, dy)
    n_anchors = _translate_base_anchors(font, bases, dy)

    _, _, after = measure(font)
    if verbose:
        print(f"     [3c] baseline: Thai sat {offset:+.1f} from the Latin baseline "
              f"-> moved {dy:+d}u across {n_glyphs} bases / {n_anchors} anchors "
              f"({len(marks)} marks follow their anchors) -> {after:+.1f}")
    return offset


def _report(paths):
    from fontTools.ttLib import TTFont
    print(f"{'face':32s} {'thai':>7s} {'latin':>7s} {'offset':>8s}")
    for p in paths:
        f = TTFont(p, fontNumber=0)
        t, l, o = measure(f)
        if t is None:
            print(f"{p.split('/')[-1]:32s}   (no Thai/Latin pair)")
            continue
        flag = "" if abs(o) < 3 else "   <-- off baseline"
        print(f"{p.split('/')[-1]:32s} {t:7.1f} {l:7.1f} {o:+8.1f}{flag}")


def main():
    import argparse
    import glob
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("fonts", nargs="*", help="font files (default: the built TH families)")
    args = ap.parse_args()
    paths = args.fonts or sorted(glob.glob("assets/fonts/*-th/TH-*.ttf"))
    _report(paths)


if __name__ == "__main__":
    main()
