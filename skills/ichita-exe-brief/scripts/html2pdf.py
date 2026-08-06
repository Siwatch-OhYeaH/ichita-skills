#!/usr/bin/env python3
"""
Ichita HTML→PDF Generator

Two engines, chosen from the document rather than hard-wired:

    the HTML builds its DOM with script  ->  chromium    (weasyprint renders nothing)
    the document contains Thai           ->  chromium    (weasyprint corrupts the text layer)
    otherwise: static, English-only      ->  weasyprint  (CID-CFF font program, smaller file)

Both branches were measured, not assumed — reference/pdf-delivery.md in
skills/ichita-convert has the numbers. The short version:

  * weasyprint does not execute JavaScript. Handed a Claude-designed standalone
    HTML, whose static markup is a loading placeholder, it renders the
    placeholder, **exits 0**, and produces a well-formed A4 PDF containing none
    of the document.
  * weasyprint's Thai text layer is wrong even when the glyphs are right: every
    า (U+0E32) extracts as ำ (U+0E33), the U+0E49 tone mark is dropped, and
    U+02D7 appears in its place. Search, copy-paste and re-ingestion all return
    corrupted Thai from a page that looks perfect.

Usage:
    python html2pdf.py INPUT.html OUTPUT.pdf
    python html2pdf.py INPUT.html OUTPUT.pdf --engine chromium
    python html2pdf.py INPUT.html OUTPUT.pdf --fonts ../../assets/fonts --dpi 150
"""

import argparse
import re
import sys
from pathlib import Path

# Markers that mean the document cannot be rendered without executing script.
# Err toward chromium: the cost of a wrong guess is asymmetric — chromium
# renders static HTML correctly, weasyprint renders scripted HTML as a blank.
JS_MARKERS = ("__bundler", "DOMContentLoaded", "ReactDOM", "React.createElement",
              "document.createElement", "<script")

# A rendered page with less text than this is almost certainly a shell.
MIN_PLAUSIBLE_CHARS = 200
NOSCRIPT_HINTS = ("requires JavaScript", "enable JavaScript", "JavaScript to display")


def has_thai(text):
    return any("฀" <= c <= "๿" for c in text)


def needs_js(html_text):
    """True if the document builds itself with script."""
    return any(m in html_text for m in JS_MARKERS)


def choose_engine(html_text):
    if needs_js(html_text):
        return "chromium", "document builds its DOM with script"
    if has_thai(html_text):
        return "chromium", "document contains Thai; weasyprint corrupts the text layer"
    return "weasyprint", "static and English-only"


def find_font_faces(font_dir: Path) -> str:
    """Generate @font-face CSS for all fonts in directory tree."""
    if not font_dir or not font_dir.exists():
        return ""

    WEIGHT_MAP = {
        "thin": 100, "light": 300, "regular": 400, "medium": 500,
        "semibold": 600, "bold": 700, "extrabold": 800, "black": 900,
    }

    faces = []
    for ext in ("*.ttf", "*.otf", "*.woff", "*.woff2"):
        for f in font_dir.rglob(ext):
            name = f.stem.lower()
            weight = 400
            for key, val in WEIGHT_MAP.items():
                if key in name:
                    weight = val
                    break
            family_base = f.stem.split("-")[0] if "-" in f.stem else f.stem
            family = family_base
            fmt = "truetype" if f.suffix in (".ttf", ".otf") else f.suffix.lstrip(".")
            faces.append(
                f"@font-face {{\n"
                f"  font-family: '{family}';\n"
                f"  src: url('{f.resolve()}') format('{fmt}');\n"
                f"  font-weight: {weight};\n"
                f"  font-style: normal;\n"
                f"}}"
            )
    return "\n".join(faces)


# ── weasyprint ───────────────────────────────────────────────────────────────

def render_weasyprint(input_html: Path, output_pdf: Path, font_dir=None, dpi=300):
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        print("ERROR: weasyprint not installed. Run: pip install weasyprint",
              file=sys.stderr)
        sys.exit(1)

    html_content = input_html.read_text(encoding="utf-8")

    stylesheets = []
    if font_dir:
        font_css = find_font_faces(font_dir)
        if font_css:
            print(f"  Injecting {font_css.count('@font-face')} font faces from {font_dir}")
            stylesheets.append(CSS(string=font_css))

    html = HTML(string=html_content, base_url=str(input_html.parent))
    html.write_pdf(str(output_pdf), stylesheets=stylesheets or None,
                   presentational_hints=True)


# ── chromium ─────────────────────────────────────────────────────────────────

BRAND_FAMILIES = ("Aeonik", "TH Aeonik", "TH Slussen", "Slussen", "Betatron",
                  "Bai Jamjuree")


def _platform_fonts(page, limit=200):
    """Ask Chromium which fonts it actually used to lay the page out.

    Chromium's Skia PDF backend emits Type 3 fonts, which carry no name — a
    PDF-side "is this a brand font" check is therefore impossible on chromium
    output. Asking the renderer is better anyway: it reports the font that was
    used, not the font that was requested, so a silent fallback shows up.
    """
    try:
        cdp = page.context.new_cdp_session(page)
        cdp.send("DOM.enable")
        cdp.send("CSS.enable")
        root = cdp.send("DOM.getDocument")["root"]["nodeId"]
        nodes = cdp.send("DOM.querySelectorAll", {
            "nodeId": root,
            "selector": "p, h1, h2, h3, h4, h5, h6, li, td, th, span, div",
        })["nodeIds"][:limit]
        seen = {}
        for nid in nodes:
            try:
                for f in cdp.send("CSS.getPlatformFontsForNode",
                                  {"nodeId": nid})["fonts"]:
                    key = f.get("familyName", "?")
                    seen[key] = seen.get(key, 0) + f.get("glyphCount", 0)
            except Exception:
                continue
        return seen
    except Exception:
        return {}


def _page_width_px(output_pdf: Path):
    """Width of the page that was actually produced, in CSS px at 96 dpi.

    Read from the artifact, not predicted from the options. `@page size`,
    `prefer_css_page_size`, `--width` and `--landscape` all move it, and an
    earlier version of this check inferred the page size instead of measuring
    it — which is how it came to disagree with the file it was checking.
    """
    try:
        import fitz
    except ImportError:
        return None
    doc = fitz.open(output_pdf)
    try:
        return doc[0].rect.width * 96 / 72
    finally:
        doc.close()


_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "px": 25.4 / 96, "": 1.0}


def _horizontal_margin_mm(shorthand):
    """Left + right of a CSS `margin` shorthand, in mm. None if unparseable."""
    parts = re.findall(r"(-?[\d.]+)(mm|cm|in|pt|px|)", shorthand)
    if not parts:
        return None
    vals = [float(n) * _MM[u] for n, u in parts]
    if len(vals) == 1:
        return vals[0] * 2
    if len(vals) in (2, 3):
        return vals[1] * 2
    return vals[1] + vals[3]


def _declared_margin_mm(page):
    """The `@page` horizontal margin, in mm.

    Returns three states, and the distinction is the whole point:

      float   the document declares one and we read it        — use it
      "none"  stylesheets read fine, no @page margin declared — our margin applies
      None    a stylesheet refused to open its rules          — unknown

    A `<link>`ed `file://` stylesheet throws SecurityError on `cssRules`, so
    "unknown" is the normal state for a hand-authored brief that links
    `ichita.css` rather than inlining it. Guessing our own margin there
    reported `designed.html` as clipping 46 px that it does not clip; the
    caller treats unknown as a zero margin instead, which can only
    under-report, never invent.
    """
    try:
        res = page.evaluate("""() => {
          let blocked = false;
          for (const s of document.styleSheets) {
            let rules;
            try { rules = s.cssRules; } catch (e) { blocked = true; continue; }
            for (const r of rules) {
              if (r.constructor.name === 'CSSPageRule' && r.style.margin)
                return r.style.margin;
            }
          }
          return blocked ? null : "none";
        }""")
    except Exception:
        return None
    if res in (None, "none"):
        return res
    return _horizontal_margin_mm(res)


def measure_clipping(page, output_pdf: Path, margin_mm, scale):
    """Report content that the produced page cuts off the right edge.

    Laid out at the *page* width rather than the design viewport. That
    distinction is the whole measurement: `scrollWidth` in a 1700 px viewport
    is 1700 px for every document, so comparing it against a page width
    reports every document as overflowing. Re-laying out at the printable
    width lets a responsive document reflow and prove it fits, and leaves a
    fixed 1700 px diagram sticking out where it can be seen.

    Reports rather than raises: some documents overflow a few px and reflow
    fine. A 1700 px mass balance on A4 does not.
    """
    page_px = _page_width_px(output_pdf)
    if page_px is None:
        return None
    try:
        m = _declared_margin_mm(page)
        # declared -> that; none declared -> ours applies; unknown -> assume
        # the whole page prints, so an unreadable stylesheet cannot invent a
        # clipping report.
        gutter_mm = margin_mm * 2 if m == "none" else (0.0 if m is None else m)
        printable = round(page_px - gutter_mm * 96 / 25.4)
        page.emulate_media(media="print")
        page.set_viewport_size({"width": max(120, printable), "height": 1030})
        content = round(page.evaluate(
            "Math.max(document.documentElement.scrollWidth,"
            " document.body.scrollWidth)") * scale)
        if content > printable + 4:
            return {"content_px": content, "printable_px": printable,
                    "page_px": round(page_px)}
    except Exception:
        return None
    return None


def render_chromium(input_html: Path, output_pdf: Path, page_format="A4",
                    landscape=False, scale=1.0, margin_mm=6,
                    width=None, height=None, timeout_ms=120_000):
    """Render through headless Chromium.

    The waits are not defensive padding. Each one corresponds to a way the
    print fired too early on a real deliverable, and the last content wait in
    particular is a measured race: on `RO Recycle Mass Balance.html` the
    `.sc-placeholder` logo slot is still unresolved when
    `document.fonts.status === 'loaded'` first becomes true, and clears about
    150 ms later. Printing at that moment ships a PDF with the ICHITA logo as
    an empty grey box — reproducible, and invisible unless you look.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed.\n"
              "  pip install playwright && python3 -m playwright install chromium\n"
              "  (the browser is a separate ~150 MB download; pip alone is not enough)",
              file=sys.stderr)
        sys.exit(1)

    url = input_html.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1700, "height": 1030})
            page.goto(url, wait_until="load", timeout=timeout_ms)

            def settle(js, why, ms, fatal):
                """Wait for a readiness condition.

                Only the shell check is fatal. The rest are conditions that a
                perfectly good document may simply never satisfy — a page with
                no images, or one whose whole content is a two-word heading —
                and a hard wait on those turns a legal document into a
                two-minute hang followed by a crash.
                """
                try:
                    page.wait_for_function(js, timeout=ms)
                except Exception:
                    if fatal:
                        raise
                    print(f"  note: proceeding without {why}", file=sys.stderr)

            # The one that matters: the loading shell must be gone, or we print
            # the placeholder — the whole defect this engine exists to fix.
            settle("!document.getElementById('__bundler_thumbnail') "
                   "&& !document.getElementById('__bundler_loading')",
                   "the bundler shell clearing", timeout_ms, fatal=True)

            # Content appeared. Short and optional: a legitimately brief page
            # never crosses the threshold and that is not an error.
            settle("document.body.innerText.trim().length > 20",
                   "a body-text check", 10_000, fatal=False)
            # Webfonts resolved — otherwise the page lays out in a fallback face.
            settle("document.fonts.status === 'loaded'",
                   "webfonts settling", 30_000, fatal=False)
            # Images decoded.
            settle("Array.from(document.images)"
                   ".every(i => i.complete && i.naturalWidth > 0)",
                   "images decoding", 30_000, fatal=False)
            # Design-system slots filled — the measured .sc-placeholder race.
            settle("document.querySelectorAll('.sc-placeholder').length === 0",
                   "component slots filling", 30_000, fatal=False)
            # Two frames of paint settle.
            settle("new Promise(r => requestAnimationFrame("
                   "() => requestAnimationFrame(() => r(true))))",
                   "a paint settle", 30_000, fatal=False)

            fonts = _platform_fonts(page)

            page.emulate_media(media="print")
            opts = dict(
                print_background=True,
                prefer_css_page_size=True,
                margin={k: f"{margin_mm}mm"
                        for k in ("top", "bottom", "left", "right")},
            )
            if width and height:
                opts.update(width=width, height=height, prefer_css_page_size=False)
            else:
                opts.update(format=page_format, landscape=landscape, scale=scale)
            page.pdf(path=str(output_pdf), **opts)

            # After the print, not before: the check needs the page that was
            # actually produced, and it re-lays the document out at that width.
            overflow = measure_clipping(page, output_pdf, margin_mm, scale)
            return fonts, overflow
        finally:
            browser.close()


# ── acceptance ───────────────────────────────────────────────────────────────

def pdf_text(pdf: Path):
    try:
        import fitz
    except ImportError:
        return None
    return "".join(p.get_text() for p in fitz.open(pdf))


def looks_like_a_shell(text):
    if text is None:
        return False
    if any(h in text for h in NOSCRIPT_HINTS):
        return True
    return len(text.strip()) < MIN_PLAUSIBLE_CHARS


def report_overflow(overflow):
    """Print the clipping warning, with the numbers and the two ways out."""
    if not overflow:
        return
    c, p = overflow["content_px"], overflow["printable_px"]
    print(f"  WARNING: content lays out {c} px wide but only {p} px is "
          f"printable on the {overflow['page_px']} px page that was produced.\n"
          f"           {c - p} px is cut off the right edge. Either:\n"
          f"             --landscape --scale {min(1.0, p / c):.2f}\n"
          f"             --width {c}px --height <measured height>px",
          file=sys.stderr)


def build_pdf(input_html: Path, output_pdf: Path, font_dir=None, dpi=300,
              engine="auto", page_format="A4", landscape=False, scale=1.0,
              margin_mm=6, width=None, height=None):
    html_content = input_html.read_text(encoding="utf-8")

    if engine == "auto":
        engine, why = choose_engine(html_content)
        print(f"  Engine: {engine} — {why}")
    else:
        print(f"  Engine: {engine} (forced)")

    print(f"  Rendering {input_html.name} → {output_pdf.name}")
    used_fonts = overflow = None
    if engine == "chromium":
        used_fonts, overflow = render_chromium(
            input_html, output_pdf, page_format, landscape, scale,
            margin_mm, width, height)
    else:
        render_weasyprint(input_html, output_pdf, font_dir, dpi)

        # Behavioural backstop, not a marker list: if what came out has no
        # plausible amount of text, the source was a shell this detector had
        # not seen. Re-render rather than shipping a valid empty PDF.
        text = pdf_text(output_pdf)
        if text is None:
            print("ERROR: pymupdf is not installed, so the weasyprint output "
                  "cannot be read back.\n"
                  "       That check is the only thing between a scripted "
                  "document and a\n"
                  "       valid, empty PDF at exit 0, so this is fatal rather "
                  "than a warning.\n"
                  "         pip install pymupdf      — restore the check\n"
                  "         --engine chromium        — skip the engine that "
                  "needs it",
                  file=sys.stderr)
            sys.exit(1)
        if looks_like_a_shell(text):
            print(f"  WARNING: weasyprint produced {len((text or '').strip())} "
                  f"characters of text — this looks like an unrendered shell.\n"
                  f"           Re-rendering with chromium.", file=sys.stderr)
            used_fonts, overflow = render_chromium(
                input_html, output_pdf, page_format, landscape, scale,
                margin_mm, width, height)
            engine = "chromium"

    if used_fonts:
        off_brand = [f for f in used_fonts
                     if not any(b in f for b in BRAND_FAMILIES)]
        print(f"  Fonts used: {', '.join(sorted(used_fonts))}")
        if off_brand:
            print(f"  WARNING: non-brand font(s) used: {', '.join(off_brand)}.\n"
                  f"           A @font-face that fails to load falls back "
                  f"silently — check the paths.", file=sys.stderr)

    report_overflow(overflow)
    size_kb = output_pdf.stat().st_size / 1024
    print(f"  ✓ {output_pdf.name} ({size_kb:.0f} KB, {engine})")
    return engine, used_fonts


def main():
    parser = argparse.ArgumentParser(
        description="Ichita HTML→PDF Generator — branded print-quality PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="Input HTML file")
    parser.add_argument("output", type=Path, help="Output PDF file")
    parser.add_argument("--engine", default="auto",
                        choices=["auto", "weasyprint", "chromium"],
                        help="default auto: chromium for scripted or Thai "
                             "documents, weasyprint otherwise")
    parser.add_argument("--fonts", type=Path, default=None,
                        help="Font directory to inject (weasyprint only)")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--format", dest="page_format", default="A4")
    parser.add_argument("--landscape", action="store_true")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--margin-mm", type=float, default=6)
    parser.add_argument("--width", default=None,
                        help='explicit page width, e.g. "1700px"')
    parser.add_argument("--height", default=None)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(args.input, args.output, args.fonts, args.dpi, args.engine,
              args.page_format, args.landscape, args.scale, args.margin_mm,
              args.width, args.height)


if __name__ == "__main__":
    main()
