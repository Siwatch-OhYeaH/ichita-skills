#!/usr/bin/env python3
"""Stem and counter-aperture measurement for the merged TH families.

Both numbers are needed to judge a Thai weight, and until 2026-08-03 only the
first was measured. That is how TH-Aeonik-Bold shipped with 7.8 units of
counter aperture — 0.11 px at 11 pt, i.e. `ฃ` and `ธ` as solid blobs — while
passing the stem check at 0.974 of the Latin.

  stem      median horizontal ink run across a mid-height band, units/1000em.
            Probed on flat-sided glyphs only, so loops and diagonals do not
            contaminate the median.

  aperture  the widest circle that fits inside the TIGHTEST enclosed counter of
            the Thai consonants, units/1000em. Enclosed counters are found by
            labelling the white regions of the rendered glyph and discarding
            the one connected to the exterior. This is the quantity that decides
            whether a loop renders as a loop.

One pixel at 11 pt / 96 dpi is 68 units/1000em, so an aperture below ~47 is
under 0.7 px and starts to fill in under any rasteriser.

The rule these feed is in th_thai_prep.WEIGHT_RATIO / APERTURE_FLOOR; the
assertions are qc_th_fonts.py checks 2 and 10.
"""
import statistics

import freetype
import numpy as np
from scipy import ndimage

PX = 512          # 1 px at this size is ~2 units/1000em, the probe's floor

STEM_LATIN = "HInlmuEFT"
# Flat-stemmed Thai bases: no loop, no diagonal, so the median run IS the stem.
STEM_THAI = "กงบปฝฟมยรลวสหฬ"
# Every one of these carries an enclosed loop, and they are the glyphs that
# fill in first when Thai is over-emboldened. ฃ and ธ are the usual binding
# pair on Aeonik; ฮ binds on Slussen.
LOOP_THAI = "กถภศลฎฏญขฃคฅฆทธนบปษสหฬฮ"

MIN_HOLE_PX = 4   # below this a labelled region is an antialias speck


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


def _bitmap(face, ch):
    try:
        face.load_char(ch, freetype.FT_LOAD_RENDER)
    except Exception:
        return None
    bm = face.glyph.bitmap
    if not bm.width or not bm.rows:
        return None
    return np.array(bm.buffer, dtype=np.uint8).reshape(
        bm.rows, bm.pitch)[:, :bm.width] > 128


def stem(path, chars=STEM_THAI, px=PX):
    """Median stem width of `chars` in `path`, units/1000em, or None."""
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, px)
    vals = []
    for ch in chars:
        a = _bitmap(face, ch)
        if a is None:
            continue
        band = a[int(a.shape[0] * .4):int(a.shape[0] * .6)]
        rr = [r for row in band for r in _runs(row)]
        if rr:
            vals.append(statistics.median(rr))
    return statistics.median(vals) / px * 1000 if vals else None


def apertures(path, chars=LOOP_THAI, px=PX):
    """{char: tightest enclosed-counter aperture in units/1000em}.

    A char is absent when it has no enclosed counter at all — which happens
    legitimately at the light end, where thinning opens the loops of ข ค ง into
    plain strokes.
    """
    face = freetype.Face(str(path))
    face.set_pixel_sizes(0, px)
    out = {}
    for ch in chars:
        a = _bitmap(face, ch)
        if a is None:
            continue
        p = np.pad(a, 1, constant_values=False)
        lbl, n = ndimage.label(~p)
        exterior = lbl[0, 0]
        best = None
        for i in range(1, n + 1):
            if i == exterior:
                continue
            hole = lbl == i
            if hole.sum() < MIN_HOLE_PX:
                continue
            ap = 2.0 * ndimage.distance_transform_edt(hole).max()
            if best is None or ap < best:
                best = ap
        if best is not None:
            out[ch] = best / px * 1000
    return out


def min_aperture(path, chars=LOOP_THAI, px=PX):
    """(tightest aperture, the char that binds) or (None, None)."""
    ap = apertures(path, chars, px)
    if not ap:
        return None, None
    ch = min(ap, key=ap.get)
    return ap[ch], ch
