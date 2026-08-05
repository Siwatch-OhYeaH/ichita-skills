#!/usr/bin/env python3
"""
markdown -> branded HTML.

Also the route to md->PDF: this emits the HTML, html2pdf.py renders it. Keeping
them separate means the intermediate is inspectable — when a PDF comes out
wrong you open the HTML in a browser and see whether the problem is the content
or the renderer, instead of guessing at weasyprint.

Everything visual comes from assets/brand/ichita.css. There is deliberately no
styling in this file: the two hand-built briefs each carried their own copy of
the brand, both got the font family name wrong, and both rendered off-brand for
months because nobody had a single place to look.

Usage:
    python emit_html.py IN.md OUT.html [--title "..."] [--link-css]
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BRAND_CSS = REPO / "assets" / "brand" / "ichita.css"

# A flowing document needs page margins; the fixed-layout briefs set margin 0
# and position everything inside a .page div. @page cannot be scoped by class,
# so the flowing variant is injected here rather than living in ichita.css.
#
# The margin box carries its own font-family. It does NOT inherit from body,
# and without it weasyprint set the page number in FreeSerif and embedded a
# whole extra font into the PDF for one digit.
FLOW_PAGE_CSS = """
@page {{
  size: A4;
  margin: 18mm 16mm 16mm;
  @bottom-right {{
    content: counter(page);
    font-family: '{family}';
    font-size: 8px;
    color: #788F9C;
  }}
}}
body {{ background: #FFFFFF; }}
.prose {{ max-width: 178mm; margin: 0 auto; }}
"""


def has_thai(text):
    return any('฀' <= c <= '๿' for c in text)


def _inline_css(css_path):
    """Read ichita.css and make its url() references absolute.

    The stylesheet resolves font paths against its own location. Once inlined
    into an HTML file somewhere else, those relative paths point at nothing —
    and a missing @font-face does not raise, it silently falls back. Rewriting
    to absolute file paths is what keeps the output on-brand.
    """
    css = css_path.read_text(encoding="utf-8")
    base = css_path.parent

    def fix(m):
        url = m.group(1).strip("'\"")
        if url.startswith(("http:", "https:", "data:", "/")):
            return m.group(0)
        return f"url('{(base / url).resolve()}')"

    return re.sub(r"url\(([^)]+)\)", fix, css)


def md_to_html(src, dst, title=None, link_css=False, quiet=False):
    try:
        import markdown
    except ImportError:
        print("ERROR: needs the markdown package. See requirements.txt.",
              file=sys.stderr)
        sys.exit(1)

    src, dst = Path(src), Path(dst)
    text = unicodedata.normalize("NFC", src.read_text(encoding="utf-8"))

    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "attr_list", "sane_lists", "toc"],
        output_format="html5",
    )

    # The document's language picks the face — English-only Aeonik (line box
    # 1200), Thai or mixed TH Aeonik (1537). Same rule as md_to_docx; the two
    # must agree or the DOCX and the PDF of one source lay out differently.
    thai = has_thai(text)
    doc_class = "doc-th" if thai else ""
    lang = "th" if thai else "en"

    if title is None:
        m = re.search(r'^#\s+(.+)$', text, flags=re.MULTILINE)
        title = m.group(1).strip() if m else src.stem

    if link_css:
        try:
            href = BRAND_CSS.resolve().relative_to(dst.resolve().parent)
        except ValueError:
            href = BRAND_CSS.resolve()
        style = f'<link rel="stylesheet" href="{href}">'
    else:
        page_css = FLOW_PAGE_CSS.format(
            family="TH Aeonik" if thai else "Aeonik")
        style = f"<style>\n{_inline_css(BRAND_CSS)}\n{page_css}</style>"

    html = f"""<!DOCTYPE html>
<html lang="{lang}" class="{doc_class}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{style}
</head>
<body>
<article class="prose">
{body}
</article>
</body>
</html>
"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(html, encoding="utf-8")

    if not quiet:
        face = "TH Aeonik (1537)" if thai else "Aeonik (1200)"
        print(f"  {src.name} -> {dst.name}  ({dst.stat().st_size:,} B)")
        print(f"  font: {face}  [source {'contains' if thai else 'has no'} Thai]")
    return html


def main():
    ap = argparse.ArgumentParser(description="Markdown -> branded HTML.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--title", default=None)
    ap.add_argument("--link-css", action="store_true",
                    help="link ichita.css instead of inlining it "
                         "(smaller file, only works in place)")
    args = ap.parse_args()
    md_to_html(args.input, args.output, args.title, args.link_css)


if __name__ == "__main__":
    main()
