#!/usr/bin/env python3
"""
Figure extraction from a born-digital PDF.

The part with no prior art in this repo, and the part where the obvious
approach fails completely. Measured on ICHITA's own briefs, 2026-08-06:

    every page carries exactly 1 raster image — the logo, the same xref
    repeated — and 26 to 77 vector paths.

So every chart, KPI card, process arrow and rule in an ICHITA PDF is vector.
`get_images()` recovers the logo and not a single chart. The figures have to be
found in `get_drawings()` and rendered back out as pixels.

Usage:
    python pdf_figures.py IN.pdf MEDIA_DIR [--dpi 200]
    from pdf_figures import extract_figures
"""

import argparse
from collections import defaultdict
from pathlib import Path

# A drawing has to be at least this big, in points, to be a figure rather than
# a rule, a border or a bullet. 24pt x 24pt is about 8mm square at print size.
MIN_W, MIN_H = 24.0, 24.0
MIN_AREA = 2400.0          # ~55pt x 44pt — smaller than any real chart

# A full-width band under 6pt tall is an accent rule or a table border, never a
# figure. Measured against the brand's 2pt .accent-line and 0.5px table rules.
RULE_MAX_H = 6.0
RULE_MIN_WIDTH_FRAC = 0.55

# Two drawings closer than this belong to the same figure. A chart's axis, bars
# and gridlines arrive as dozens of separate path objects.
CLUSTER_GAP = 9.0

# An xref on this share of pages is brand furniture, not content.
FURNITURE_PAGE_FRAC = 0.8


def _rects_touch(a, b, gap):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0]
                or a[3] + gap < b[1] or b[3] + gap < a[1])


def _union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _cluster(rects, gap=CLUSTER_GAP):
    """Merge overlapping/nearby rectangles until nothing more merges.

    Quadratic in the number of drawings, which is fine — the measured worst
    page has 77.
    """
    boxes = list(rects)
    changed = True
    while changed:
        changed = False
        out = []
        for box in boxes:
            for i, existing in enumerate(out):
                if _rects_touch(existing, box, gap):
                    out[i] = _union(existing, box)
                    changed = True
                    break
            else:
                out.append(box)
        boxes = out
    return boxes


def _furniture_xrefs(doc):
    """xrefs that appear on ≥80% of pages — the logo, the letterhead mark."""
    seen = defaultdict(int)
    for page in doc:
        for xref in {img[0] for img in page.get_images(full=True)}:
            seen[xref] += 1
    threshold = max(2, int(len(doc) * FURNITURE_PAGE_FRAC))
    return {x for x, n in seen.items() if n >= threshold}


def _drawing_boxes(page):
    """Candidate figure rectangles from the page's vector content."""
    page_w = page.rect.width
    rects = []
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None or r.is_empty or r.is_infinite:
            continue
        w, h = r.width, r.height
        # Accent rules and table borders: wide and flat.
        if h <= RULE_MAX_H and w >= page_w * RULE_MIN_WIDTH_FRAC:
            continue
        # Hairlines in either direction.
        if w < 2.0 or h < 2.0:
            continue
        rects.append((r.x0, r.y0, r.x1, r.y1))
    return rects


def extract_figures(doc, media_dir, dpi=200, quiet=False):
    """Find and render the figures in `doc`.

    Returns {page_index: [(bbox, relative_png_path), ...]} in top-to-bottom
    order, so the caller can interleave the images with the text.
    """
    import fitz

    media_dir = Path(media_dir)
    furniture = _furniture_xrefs(doc)
    found = {}
    n_written = 0
    n_furniture = 0

    for pno, page in enumerate(doc):
        boxes = []

        # 1. Raster images that are not brand furniture.
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in furniture:
                n_furniture += 1
                continue
            for r in page.get_image_rects(xref):
                boxes.append((r.x0, r.y0, r.x1, r.y1))

        # 2. Vector clusters — where the charts actually are.
        boxes.extend(_drawing_boxes(page))
        if not boxes:
            continue

        clusters = _cluster(boxes)
        keep = [
            b for b in clusters
            if (b[2] - b[0]) >= MIN_W
            and (b[3] - b[1]) >= MIN_H
            and (b[2] - b[0]) * (b[3] - b[1]) >= MIN_AREA
        ]
        if not keep:
            continue

        keep.sort(key=lambda b: (round(b[1], 1), b[0]))   # reading order
        media_dir.mkdir(parents=True, exist_ok=True)

        page_figs = []
        for idx, b in enumerate(keep, 1):
            clip = fitz.Rect(*b) & page.rect
            if clip.is_empty:
                continue
            name = f"p{pno + 1}-fig{idx}.png"
            pix = page.get_pixmap(clip=clip, dpi=dpi)
            pix.save(media_dir / name)
            page_figs.append(((clip.x0, clip.y0, clip.x1, clip.y1), name))
            n_written += 1
        if page_figs:
            found[pno] = page_figs

    if not quiet:
        print(f"  figures: {n_written} rendered at {dpi} dpi -> {media_dir}")
        if n_furniture:
            print(f"  skipped {n_furniture} brand-furniture image placement(s) "
                  f"({len(furniture)} xref(s) on >={int(FURNITURE_PAGE_FRAC * 100)}% "
                  f"of pages)")
    return found


def main():
    import fitz
    ap = argparse.ArgumentParser(description="Extract figures from a PDF.")
    ap.add_argument("input", type=Path)
    ap.add_argument("media_dir", type=Path)
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    doc = fitz.open(args.input)
    figs = extract_figures(doc, args.media_dir, args.dpi)
    for pno in sorted(figs):
        for bbox, name in figs[pno]:
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            print(f"  page {pno + 1}: {name}  {w:.0f}x{h:.0f} pt")


if __name__ == "__main__":
    main()
