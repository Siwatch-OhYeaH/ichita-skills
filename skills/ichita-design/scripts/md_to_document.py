#!/usr/bin/env python3
"""Markdown -> an ICHITA A4 document, built to "The document standard".

    python3 md_to_document.py IN.md OUT.html [--eyebrow "…"]
    python3 ../../ichita-exe-brief/scripts/html2pdf.py OUT.html OUT.pdf

This is not a second `ichita-convert`. That skill *renders the record* — one
Markdown source, a DOCX and a PDF that lay out the same, and a reconcile path
back. This designs it: the type ramp, the grounds, the running header and the
table style come from `../README.md`, and the output is a document you would
send outside the building.

Use ichita-convert when the point is the content and the round trip. Use this
when the point is the artefact.

**It depends on `assets/brand/ichita.css`**, which arrives with the
ichita-convert branch (PR #7). Until that merges this script cannot run on
`main` — it does not carry its own @font-face block on purpose. Re-declaring
the brand is how the two hand-built executive briefs both ended up naming a
family (`AeonikTH`) that has never existed and rendering in a fallback for
months. ichita.css is the one place those declarations live; everything below
layers on top of it and never touches `.prose`, so the two do not fight.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BRAND_CSS = REPO / "assets" / "brand" / "ichita.css"
WORDMARK = REPO / "assets" / "logos" / "ichita-wordmark-dark-on-white.png"

# Measured on ichita-wordmark-dark-on-white.png (2251x626). The approved file
# carries its own padding: the mark itself is 0.67 of the file width and its
# baseline sits 0.34 of the file height above the bottom edge. The header wants
# the MARK at 38 mm (README.md, The document standard), so the file is placed
# at 38/0.67 and shifted left by its own left padding. The file is never
# cropped or redrawn — Guidelines 1.2, "always place the supplied file".
WORDMARK_INK_FRACTION = 0.67
WORDMARK_LEFT_PAD_MM = 9.4


def inline_brand_css(css_path: Path) -> str:
    """ichita.css with its relative url() rewritten absolute.

    A relative @font-face src resolves against the STYLESHEET's location, so an
    inlined copy living somewhere else silently points at nothing — and a
    missing @font-face does not raise, it falls back. Same fix emit_html.py
    makes for the same reason.
    """
    css = css_path.read_text(encoding="utf-8")
    base = css_path.parent

    def absolute(m):
        url = m.group(1).strip("'\"")
        if url.startswith(("http", "data:", "/")):
            return m.group(0)
        return f"url('{(base / url).resolve()}')"

    return re.sub(r"url\(([^)]+)\)", absolute, css)


DOC_CSS = """
/* ---------------------------------------------------------------------------
   ICHITA document standard — ../README.md, "The document standard".
   Layered over ichita.css, which supplies @font-face and the colour tokens.
   Nothing here touches .prose.
   --------------------------------------------------------------------------- */
:root {
  --ich-blue:       #2978FF;  /* accent: rules, bars, fills — never body type */
  --ich-blue-text:  #1A56C4;  /* 6.64:1 on white — the accessible text step   */
  --ich-steel:      #788F9C;  /* decorative labels only, at 12px Medium up    */
  --ich-steel-text: #4F6472;  /* 6.18:1 — muted text                          */
  --ich-grey-03:    #263338;  /* 13.02:1 — the only safe body colour          */
  --ich-off-white:  #F8FAFB;
  --ich-alt-row:    #EFF2F3;
  --ich-rule:       #A0B0B8;
}

@page {
  size: A4;
  margin: 25mm;
  @top-center {
    content: "";
    width: 100%;
    height: 25mm;
    background: url('WORDMARK_URL') no-repeat LEFT_SHIFT bottom / MARK_WIDTH auto;
    border-bottom: 0.75pt solid var(--ich-blue);
    margin-bottom: 4mm;
  }
  @bottom-right {
    content: counter(page);
    font-family: 'TH Aeonik';
    font-weight: 500;
    font-size: 8pt;
    color: var(--ich-steel-text);
    margin-top: 4mm;
  }
}

/* TH Aeonik is the only face; the document chooses a WEIGHT, not a face.
   English-only -> Regular 400 body, SemiBold 600 emphasis, Bold 700 headings.
   `font-synthesis: none` so a face that fails to load shows as the wrong
   weight rather than a convincing fake bold. */
body {
  font-family: 'TH Aeonik', 'Aeonik', 'Bai Jamjuree', 'Trebuchet MS', system-ui;
  font-synthesis: none;
  font-weight: 400;
  font-size: 10pt;
  line-height: 1.5;
  color: var(--ich-grey-03);
  background: #FFFFFF;
  margin: 0;
}
/* Thai body runs 1.75 and Thai headings 1.55 — marks collide below 1.35.
   Set by :lang so a bilingual source needs no switch here. */
:lang(th) { line-height: 1.75; }
h1:lang(th), h2:lang(th), h3:lang(th), h4:lang(th) { line-height: 1.55; }
body[data-typeset="mixed"] { font-weight: 350; }   /* Book */
body[data-typeset="mixed"] strong { font-weight: 600; }

strong, b { font-weight: 600; }

/* -- Title: 26 pt Bold, centred, over a 3 pt Ichita Blue rule ------------- */
.doc-title {
  font-size: 26pt;
  font-weight: 700;
  line-height: 1.18;
  letter-spacing: -0.012em;
  text-align: center;
  color: var(--ich-grey-03);
  margin: 0 0 6mm;
  padding-bottom: 5mm;
  border-bottom: 3pt solid var(--ich-blue);
}
.doc-eyebrow {
  font-size: 9pt;
  font-weight: 500;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  text-align: center;
  color: var(--ich-steel);
  margin: 0 0 3mm;
}

/* -- H1: 15 pt Bold, 3 pt blue left bar, 6 pt inset, over a 0.75 pt rule -- */
h2.h1 {
  font-size: 15pt;
  font-weight: 700;
  line-height: 1.25;
  color: var(--ich-grey-03);
  border-top: 0.75pt solid var(--ich-blue);
  border-left: 3pt solid var(--ich-blue);
  padding: 3mm 0 0 6pt;
  margin: 9mm 0 3mm;
}
.doc > h2.h1:first-of-type { margin-top: 6mm; }

/* -- H2: 12 pt Bold, Ichita Blue at its accessible text step -------------- */
h3.h2 {
  font-size: 12pt;
  font-weight: 700;
  line-height: 1.3;
  color: var(--ich-blue-text);
  margin: 6mm 0 1.5mm;
}

/* -- H3: 10.5 pt Bold Italic, Ichita Blue -------------------------------- */
h4 {
  font-size: 10.5pt;
  font-weight: 700;
  font-style: italic;
  color: var(--ich-blue-text);
  margin: 4mm 0 1mm;
}

h2.h1, h3.h2, h4 { break-after: avoid; }

/* -- Body: 2 pt before / 5 pt after -------------------------------------- */
p { margin: 2pt 0 5pt; }
p, li { orphans: 2; widows: 2; }

/* -- Lists: indent 18 pt ------------------------------------------------- */
ul, ol { margin: 2pt 0 5pt; padding-left: 18pt; }
li { margin: 0 0 3pt; }
li::marker { color: var(--ich-steel-text); }
ol > li::marker { font-weight: 600; color: var(--ich-grey-03); }
li > ul, li > ol { margin-top: 3pt; }

/* -- Callout: Off White field, 4 pt Ichita Blue left bar, 10 pt italic ---- */
.callout {
  background: var(--ich-off-white);
  border-left: 4pt solid var(--ich-blue);
  padding: 4mm 5mm;
  margin: 3mm 0 6mm;
  font-style: italic;
}
.callout > :first-child { margin-top: 0; }
.callout > :last-child  { margin-bottom: 0; }
.callout ul { padding-left: 16pt; }

/* -- Table: 9 pt, header row Blue Grey 03, banding, 0.5 pt hairlines ------ */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  line-height: 1.4;
  margin: 3mm 0 5mm;
}
thead { display: table-header-group; }
th {
  background: var(--ich-grey-03);
  color: #FFFFFF;
  font-weight: 700;
  text-align: left;
  padding: 2pt 5.4pt;
  border: 0.5pt solid var(--ich-grey-03);
}
td {
  padding: 2pt 5.4pt;
  border: 0.5pt solid var(--ich-rule);
  vertical-align: top;
  /* A DOI or a part number is one long unbreakable token. Left alone it wins
     the column auto-layout and starves the column the reader actually reads. */
  overflow-wrap: anywhere;
}
/* ...but `anywhere` also lets auto-layout squeeze a column to one character,
   which is how "Subscription" came out as "Subscrip / tion". A floor per
   column stops the squeeze without pinning any column to a fixed width. */
th:not(:first-child), td:not(:first-child) { min-width: 21mm; }
/* A row number is a label, not a column. */
th:first-child, td:first-child { width: 3%; white-space: nowrap; }
tbody tr:nth-child(even) td { background: var(--ich-alt-row); }
/* A table taller than the page breaks BETWEEN rows. `avoid` on the table is
   unsatisfiable, and the engine takes the row apart rather than drop it. */
table { break-inside: auto; }
tr { break-inside: avoid; page-break-inside: avoid; }

/* -- Any figure the reader reads or compares ----------------------------- */
.ich-figure {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.035em;
}

/* -- Caption: 9 pt, under the table -------------------------------------- */
figcaption, .caption {
  font-size: 9pt;
  color: var(--ich-steel-text);
  margin: -3mm 0 5mm;
}

/* Aeonik has no fixed-pitch cut, and misaligned code is worse than off-brand
   code. The one place a non-brand family is allowed. */
code, pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; }
code { background: var(--ich-alt-row); padding: 0 3pt; border-radius: 2px; }
"""


def has_thai(text: str) -> bool:
    return any("฀" <= ch <= "๿" for ch in text)


def build(src: Path, dst: Path, eyebrow: str, title: str | None = None) -> Path:
    try:
        import markdown
    except ImportError:
        print("ERROR: needs the markdown package. "
              "See ../../ichita-convert/requirements.txt.", file=sys.stderr)
        sys.exit(1)

    text = unicodedata.normalize("NFC", src.read_text(encoding="utf-8"))
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "attr_list", "sane_lists"],
        output_format="html5",
    )

    # h1 becomes the title block; h2 takes the H1 spec, h3 the H2 spec. The
    # standard's ramp starts at the document title, so everything shifts one.
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, flags=re.S)
    if title is None:
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else src.stem
    body = re.sub(r"<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r"<h2([^>]*)>", r'<h2 class="h1"\1>', body)
    body = re.sub(r"<h3([^>]*)>", r'<h3 class="h2"\1>', body)

    # TL;DR is what the standard's callout style is for. Match the heading the
    # source actually wrote, and leave everything else alone.
    body = re.sub(
        r'(<h2 class="h1"[^>]*>(?:TL;DR|Summary|Executive Summary)</h2>)\s*'
        r'(<ul>.*?</ul>|<p>.*?</p>)',
        r'\1<div class="callout">\2</div>', body, flags=re.S | re.I)

    thai = has_thai(text)
    mark_w = 38.0 / WORDMARK_INK_FRACTION
    css = inline_brand_css(BRAND_CSS) + (
        DOC_CSS
        .replace("WORDMARK_URL", WORDMARK.resolve().as_uri())
        .replace("MARK_WIDTH", f"{mark_w:.1f}mm")
        .replace("LEFT_SHIFT", f"-{WORDMARK_LEFT_PAD_MM}mm"))

    html = (
        '<!DOCTYPE html>\n'
        f'<html lang="{"th" if thai else "en"}">\n<head>\n'
        '<meta charset="UTF-8">\n'
        f"<title>{title}</title>\n<style>\n{css}</style>\n</head>\n"
        f'<body data-typeset="{"mixed" if thai else "en"}">\n'
        '<article class="doc">\n'
        f'<p class="doc-eyebrow">{eyebrow}</p>\n'
        f'<h1 class="doc-title">{title}</h1>\n{body}\n'
        "</article>\n</body>\n</html>\n")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html, encoding="utf-8")
    weight = "Book 350" if thai else "Regular 400"
    print(f"  {src.name} -> {dst.name}  ({dst.stat().st_size:,} B)")
    print(f"  TH Aeonik {weight}  [source {'contains' if thai else 'has no'} Thai]")
    return dst


def main():
    ap = argparse.ArgumentParser(
        description="Markdown -> an ICHITA A4 document (HTML; render with "
                    "ichita-exe-brief/scripts/html2pdf.py).")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--eyebrow", default="ICHITA Technology",
                    help="the uppercase line above the title")
    ap.add_argument("--title", default=None,
                    help="override the title taken from the first h1")
    a = ap.parse_args()
    if not BRAND_CSS.exists():
        print(f"ERROR: {BRAND_CSS} not found. This script does not carry its "
              "own @font-face block; see the module docstring.", file=sys.stderr)
        sys.exit(1)
    build(Path(a.input), Path(a.output), a.eyebrow, a.title)


if __name__ == "__main__":
    main()
