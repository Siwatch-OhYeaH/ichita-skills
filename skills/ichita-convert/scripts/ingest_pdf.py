#!/usr/bin/env python3
"""
pdf -> markdown, via pymupdf.

Born-digital only. A scanned page has no character stream to read and this
extractor returns nothing useful for it — that is the honest failure, and it is
better than an OCR guess presented as the document.

Do NOT replace this with "ask a model to read the PDF". pymupdf returns the
exact codepoints the producer wrote. A model paraphrases, drops table cells and
re-types numbers, and every one of those is invisible in the output.

There are no headings, paragraphs or lists in a PDF — only glyphs at
coordinates. Everything below is inference, and each rule says what it keys on
so that when it is wrong you can see why rather than tune it blind.

Usage:
    python ingest_pdf.py IN.pdf OUT.md [--no-figures] [--dpi 200]
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_clean import clean  # noqa: E402
from pdf_figures import extract_figures  # noqa: E402

# A line this much larger than body text is a heading. Three thresholds give
# h1/h2/h3; bold-and-slightly-larger is a run-in h4.
HEADING_RATIOS = [(1.55, 1), (1.28, 2), (1.12, 3)]

# Running header/footer detection: near an edge AND repeated across pages.
EDGE_FRAC = 0.09
REPEAT_PAGE_FRAC = 0.6

# Paragraph assembly. A line whose right edge falls short of the column's is
# the last line of its paragraph — the standard cue, and the only one that
# works without knowing the text's language.
SHORT_LINE_FRAC = 0.92
LINE_GAP_FACTOR = 1.75      # x line height; more than this is a new block
INDENT_TOL = 6.0            # pt; a bigger x0 shift starts a new paragraph

# Written as escapes on purpose. U+F0B7 is the Private Use Area bullet Word
# emits for a Symbol-font list marker; as a literal it reads as a stray box in
# an editor and gets "tidied" away by the next person to touch this file.
BULLET_CHARS = (
    "\u2022"    # bullet
    "\u25cf"    # black circle
    "\u25aa"    # black small square
    "\u25e6"    # white bullet
    "\u2023"    # triangular bullet
    "\u2043"    # hyphen bullet
    "\u00b7"    # middle dot
    "\u2219"    # bullet operator
    "\uf0b7"    # PUA - Word's Symbol-font bullet
)


# Fragments on one baseline separated by more than this many multiples of the
# font size are different columns, not one line. Keeps a bullet glyph with its
# text without welding the two halves of a two-column layout together.
SAME_LINE_GAP = 3.0


def _is_thai(ch):
    return '฀' <= ch <= '๿'


def _join(a, b):
    """Join two text fragments.

    Thai does not space its words, so a wrapped Thai line joined with a space
    puts one in the middle of a word — `ใช้ พลังงาน` for `ใช้พลังงาน`. Where
    Thai breaks a line is the renderer's business, not the text's.
    """
    if not a:
        return b
    if not b:
        return a
    if _is_thai(a[-1]) and _is_thai(b[0]):
        return a + b
    return a + " " + b


def _lines(page):
    """Flatten a page to (bbox, text, size, bold) tuples in reading order."""
    raw = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            size = max(round(s["size"], 1) for s in spans)
            bold = any("bold" in s["font"].lower() or s["flags"] & 2 ** 4
                       for s in spans)
            raw.append((tuple(line["bbox"]), text, size, bold))
    raw.sort(key=lambda t: (t[0][1], t[0][0]))

    # pymupdf reports a list bullet and its text as two separate lines — they
    # are separate objects in the content stream, and the bullet's box often
    # starts a couple of points LOWER than the text's, so sorting by y alone
    # puts the marker after the words it belongs to.
    #
    # Group into visual rows by vertical overlap first, order each row by x,
    # and only then join. Getting this wrong is what turned every bullet into
    # an empty list item with the text orphaned above it.
    rows = []
    for item in raw:
        bbox = item[0]
        if rows:
            rb = rows[-1][0]
            overlap = min(rb[3], bbox[3]) - max(rb[1], bbox[1])
            height = min(rb[3] - rb[1], bbox[3] - bbox[1])
            if height > 0 and overlap > height * 0.6:
                rows[-1][1].append(item)
                rows[-1][0] = (min(rb[0], bbox[0]), min(rb[1], bbox[1]),
                               max(rb[2], bbox[2]), max(rb[3], bbox[3]))
                continue
        rows.append([bbox, [item]])

    out = []
    for _, items in rows:
        items.sort(key=lambda t: t[0][0])
        merged = []
        for bbox, text, size, bold in items:
            if merged:
                pb, pt, ps, pbold = merged[-1]
                gap = bbox[0] - pb[2]
                if -1.0 <= gap <= size * SAME_LINE_GAP:
                    merged[-1] = (
                        (min(pb[0], bbox[0]), min(pb[1], bbox[1]),
                         max(pb[2], bbox[2]), max(pb[3], bbox[3])),
                        _join(pt, text), max(ps, size), pbold or bold,
                    )
                    continue
            merged.append((bbox, text, size, bold))
        out.extend(merged)
    return out


def _body_size(doc):
    """Modal line size weighted by character count — the body text size."""
    sizes = Counter()
    for page in doc:
        for _, text, size, _ in _lines(page):
            sizes[size] += len(text)
    return sizes.most_common(1)[0][0] if sizes else 10.0


def _running_text(doc):
    counts = Counter()
    for page in doc:
        h = page.rect.height
        for bbox, text, _, _ in _lines(page):
            if bbox[1] < h * EDGE_FRAC or bbox[3] > h * (1 - EDGE_FRAC):
                counts[text] += 1
    threshold = max(2, int(len(doc) * REPEAT_PAGE_FRAC))
    return {t for t, c in counts.items() if c >= threshold and len(t) < 120}


def _heading_level(size, body, bold):
    ratio = size / body if body else 1.0
    for cut, level in HEADING_RATIOS:
        if ratio >= cut:
            return level
    if bold and ratio >= 1.04:
        return 4
    return None


def _inside(bbox, boxes):
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    return any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boxes)


def _table_md(rows):
    """Render an extracted table as a pipe table, or None if it is not one.

    A single-column 'table' is pymupdf finding a bordered callout, and it reads
    far better as a paragraph than as a one-cell table.
    """
    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows]
    rows = [r for r in rows if any(r)]
    if len(rows) < 2 or len(rows[0]) < 2:
        return None
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head, body = rows[0], rows[1:]
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join(["---"] * width) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def _emit_paragraphs(lines, body_size, out):
    """Group consecutive lines into paragraphs, headings and list items."""
    para = []
    prev = None            # (bbox, size)
    col_right = max((l[0][2] for l in lines), default=0.0)

    def flush():
        if para:
            joined = para[0]
            for frag in para[1:]:
                joined = _join(joined, frag)
            out.append(joined.strip())
            out.append("")
            para.clear()

    for bbox, text, size, bold in lines:
        level = _heading_level(size, body_size, bold)

        bullet = text[:1] in BULLET_CHARS
        if bullet:
            text = text[1:].strip()

        if level is not None:
            # Consecutive heading lines of the same size are one wrapped
            # heading, not two headings.
            if (out and prev and prev[1] == size
                    and out[-1] == "" and len(out) >= 2
                    and out[-2].startswith("#" * level + " ")
                    and bbox[1] - prev[0][3] < size * 0.9):
                out[-2] = _join(out[-2], text)
            else:
                flush()
                out.append(f"{'#' * level} {text}")
                out.append("")
            prev = (bbox, size)
            continue

        if bullet:
            flush()
            out.append(f"- {text}")
            prev = (bbox, size)
            continue

        if prev is not None and para:
            gap = bbox[1] - prev[0][3]
            new_para = (
                gap > size * LINE_GAP_FACTOR                 # vertical break
                or abs(bbox[0] - prev[0][0]) > INDENT_TOL    # re-indent
                or prev[0][2] < col_right * SHORT_LINE_FRAC  # prev line ended short
            )
            if new_para:
                flush()

        para.append(text)
        prev = (bbox, size)

    flush()


def pdf_to_md(src, dst, figures=True, dpi=200, quiet=False):
    try:
        import fitz
    except ImportError:
        print("ERROR: needs pymupdf. See requirements.txt.", file=sys.stderr)
        sys.exit(1)

    src, dst = Path(src), Path(dst)
    doc = fitz.open(src)

    if doc.is_encrypted and not doc.authenticate(""):
        print("ERROR: PDF is encrypted.", file=sys.stderr)
        sys.exit(1)

    chars = sum(len(p.get_text()) for p in doc)
    if chars < 40 * len(doc):
        print(f"WARNING: {chars} characters over {len(doc)} page(s). This looks "
              f"like a scanned PDF; OCR is out of scope and nothing useful will "
              f"be extracted.", file=sys.stderr)

    body = _body_size(doc)
    running = _running_text(doc)

    media_dir = dst.parent / f"{dst.stem}-media"
    figs = extract_figures(doc, media_dir, dpi, quiet) if figures else {}

    out = []
    n_tables = 0
    for pno, page in enumerate(doc):
        # Tables first: their region is removed from the text flow, otherwise
        # every cell reappears as a stray paragraph under the table.
        table_items = []
        table_boxes = []
        try:
            for tbl in page.find_tables().tables:
                md = _table_md(tbl.extract())
                if md:
                    table_items.append((tbl.bbox[1], md))
                    table_boxes.append(tbl.bbox)
                    n_tables += 1
        except Exception:
            pass    # find_tables is best-effort; a failure must not lose the text

        lines = [l for l in _lines(page)
                 if l[1] not in running and not _inside(l[0], table_boxes)]

        # Interleave tables and figures with the text by vertical position.
        anchored = table_items + [(b[1], f"![]({media_dir.name}/{n})")
                                  for b, n in figs.get(pno, [])]
        anchored.sort(key=lambda t: t[0])

        cursor = 0
        for y, chunk in anchored:
            before = [l for l in lines[cursor:] if l[0][1] < y]
            if before:
                _emit_paragraphs(before, body, out)
                cursor += len(before)
            out.append(chunk)
            out.append("")
        if cursor < len(lines):
            _emit_paragraphs(lines[cursor:], body, out)

    text = clean("\n".join(out), source="pdf")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

    if not quiet:
        before, after = src.stat().st_size, dst.stat().st_size
        print(f"  {src.name} -> {dst.name}  "
              f"{before:,} B -> {after:,} B  ({before / max(after, 1):.0f}x smaller)")
        print(f"  {len(doc)} page(s), body text {body} pt, {n_tables} table(s)")
    return text


def main():
    ap = argparse.ArgumentParser(description="PDF -> Markdown (born-digital only).")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()
    pdf_to_md(args.input, args.output, not args.no_figures, args.dpi)


if __name__ == "__main__":
    main()
