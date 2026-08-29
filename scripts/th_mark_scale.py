#!/usr/bin/env python3
"""Shrink Thai marks so a Thai stack fits inside the Latin's line box.

WHY THIS EXISTS. TH-Aeonik led 28.3% looser than Aeonik because one font has one
`hhea`, so the box that has to hold a three-level Thai stack also sets the pitch
of a Latin-only line. Siwatch ruled out the two-font (Latin/Complex-Script) split
— *"solve it with the font engineering, not by set up two separate fonts"* — so
the box has to come down to Aeonik's 1200 and the Thai has to fit inside it.

WHERE THE ROOM IS. Decomposing the worst shaped stack `ปื้` on TH-Aeonik-Black
(1/1000 em) showed the inter-level gaps are already at or under one pixel:

    base ป          1..701
    upper vowel ื  590..867     gap to base  +65   (1 px is 68)
    tone ้.small   905..1139    gap to vowel +38   (under 1 px)
    worst lower ุ     -323

So nothing can be reclaimed by moving marks — `th_mark_clearance.py` already has
them as close as the pixel grid allows. The height is in the marks THEMSELVES.
Against Leelawadee UI at the same consonant height (ข top 510 in both):

              ื     ึ     ิ     ้     ุ/ู
    ours    248   267   212   226   266/264
    Leelawadee 197   201   167   201   182      <- ours are +26% to +45%
    Sarabun    290   285   234   268   270/272  <- bigger than ours

Bai simply draws large marks, and this pipeline inherited them unquestioned while
scaling and emboldening everything else. Leelawadee UI fits the same consonant
size into 1255; Bai needs 1564.

HOW THE TRANSFORM WORKS, and why it is anchor-relative. A mark renders at
`base_origin + base_anchor - mark_anchor`. Scaling a mark's outline about its
own origin therefore MOVES it, because the anchor no longer sits where the ink
does. Scaling about an arbitrary point and then fixing it up by editing anchors
is the same mistake in two steps.

Instead every mark is scaled about its OWN GPOS anchor:

    p' = A + s * (p - A)      where A is the mark's anchor

The anchor is a fixed point of that map, so it needs no adjustment at all and the
mark does not move by a single unit. The ink shrinks toward the attachment point,
which means the top of an upper mark comes DOWN while the gap to the consonant
below is held or slightly opened — so this composes with the clearance floor in
`th_mark_clearance.py` rather than fighting it. Same for a below-vowel: its
deepest ink rises toward the baseline.

It must run BEFORE th_mark_clearance.raise_upper_marks(): a smaller mark is a
smaller obstacle, so the clearance pass re-settles the lift, and running it first
would leave that work stale (the same second-order effect recorded in
`taper-a-ladder-to-its-hard-cap`).

THE COST, which is a brand decision and not a measurement. The four tone marks
่ ้ ๊ ๋ differ only by small strokes. Shrunk far enough they stop being
distinguishable at 11 pt, and no amount of measuring settles where that line is —
`scripts/build_th_mark_specimen.py` renders them for that judgment.
"""
from __future__ import annotations

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.misc.transform import Transform


def _mark_anchors(font):
    """{glyph name: (x, y)} for every mark GPOS attaches by an anchor.

    Read from the GPOS MarkArray rather than from a hand-written codepoint list,
    so the GSUB-only variants (`uni0E48.small`, `uni0E47.narrow`, the
    `uni0E4D0E49` ligatures) are covered too. Those are exactly the glyphs that
    appear in real two-level stacks and exactly the ones a cmap-based list
    misses — the same blind spot that hid a defect from every raster test in
    the 2026-08-01 post-mortem.
    """
    if "GPOS" not in font:
        return {}

    anchors: dict[str, tuple[float, float]] = {}

    def _record(coverage, mark_array):
        if coverage is None or mark_array is None:
            return
        for name, rec in zip(coverage.glyphs, mark_array.MarkRecord):
            anchor = rec.MarkAnchor
            if anchor is None or name in anchors:
                continue
            anchors[name] = (anchor.XCoordinate, anchor.YCoordinate)

    for lookup in font["GPOS"].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            sub = getattr(sub, "ExtSubTable", sub)
            # 4 = MarkBasePos, 5 = MarkLigPos, 6 = MarkMarkPos. MarkBasePos is
            # visited first because it is the attachment that decides where a
            # mark sits on a consonant; a mark reached only through MarkMarkPos
            # still gets its Mark1 anchor.
            if getattr(sub, "LookupType", lookup.LookupType) == 4:
                _record(sub.MarkCoverage, sub.MarkArray)
            elif getattr(sub, "LookupType", lookup.LookupType) == 6:
                _record(sub.Mark1Coverage, sub.Mark1Array)
            elif getattr(sub, "LookupType", lookup.LookupType) == 5:
                _record(sub.MarkCoverage, sub.MarkArray)
    return anchors


def scale_thai_marks(font, scale, verbose=True):
    """Scale every anchored mark about its own anchor. Returns (n, report).

    `report` maps glyph name -> (height before, height after) for the marks that
    matter to the line box, so the caller can print measured sizes rather than
    the nominal factor.
    """
    if scale >= 1.0:
        if verbose:
            print(f"     [0d] Mark scale {scale:.3f} — no change")
        return 0, {}

    anchors = _mark_anchors(font)
    if not anchors:
        if verbose:
            print("     [0d] !! no GPOS mark anchors found — marks NOT scaled")
        return 0, {}

    glyf = font["glyf"]
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]
    report = {}
    done = 0

    for name, (ax, ay) in sorted(anchors.items()):
        if name not in glyf.glyphs:
            continue

        before = _ink_height(glyph_set, name)

        # Decompose first. A composite mark (Bai's uni0E4D0E48 family) references
        # component marks that are themselves being scaled here, so leaving it
        # composite would apply the scale to the components AND keep the original
        # component offsets — the parts would shrink but stay spread apart.
        rec = DecomposingRecordingPen(glyph_set)
        try:
            glyph_set[name].draw(rec)
        except Exception:
            continue

        pen = TTGlyphPen(None)
        # p' = A + s*(p - A), i.e. translate the anchor to the origin, scale,
        # translate back. The anchor is a fixed point, so GPOS needs no edit.
        transform = (Transform()
                     .translate(ax, ay)
                     .scale(scale)
                     .translate(-ax, -ay))
        rec.replay(TransformPen(pen, transform))
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)
        glyf.glyphs[name] = glyph

        # A combining mark carries a zero advance and must keep it — a real
        # advance in the PDF /W array is what detaches every tone mark from its
        # consonant. Scaling never introduces one, but spacing marks that DO
        # carry an advance need it scaled with the ink.
        advance, lsb = hmtx.metrics[name]
        if advance:
            hmtx.metrics[name] = (round(advance * scale), lsb)

        after = _ink_height(glyph_set, name)
        if before and after:
            report[name] = (before, after)
        done += 1

    if verbose:
        print(f"     [0d] Marks scaled x{scale:.3f} about their own anchors: "
              f"{done} glyphs (GPOS anchors unchanged — the anchor is the "
              f"fixed point)")
    return done, report


def _ink_height(glyph_set, name):
    from fontTools.pens.boundsPen import BoundsPen
    pen = BoundsPen(glyph_set)
    try:
        glyph_set[name].draw(pen)
    except Exception:
        return None
    if not pen.bounds:
        return None
    return pen.bounds[3] - pen.bounds[1]
