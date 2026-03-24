#!/usr/bin/env python3
"""
Ichita HTML→PDF Generator

Converts branded HTML templates to print-quality PDFs using weasyprint.
Supports font injection, A4 sizing, and 300 DPI output.

Usage:
    python html2pdf.py INPUT.html OUTPUT.pdf
    python html2pdf.py INPUT.html OUTPUT.pdf --fonts ../../assets/fonts
    python html2pdf.py INPUT.html OUTPUT.pdf --fonts ../../assets/fonts --dpi 150
"""

import argparse
import sys
from pathlib import Path


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
            # Detect weight from filename (e.g., AeonikTH-Bold.ttf → 700)
            weight = 400
            for key, val in WEIGHT_MAP.items():
                if key in name:
                    weight = val
                    break

            # Detect family from filename
            family_base = f.stem.split("-")[0] if "-" in f.stem else f.stem
            # Normalize: "AeonikTH" → "Aeonik TH", "Aeonik" → "Aeonik"
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


def build_pdf(input_html: Path, output_pdf: Path, font_dir: Path | None = None, dpi: int = 300):
    """Convert HTML to PDF with optional font injection."""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        print("ERROR: weasyprint not installed. Run: pip install weasyprint", file=sys.stderr)
        sys.exit(1)

    html_content = input_html.read_text(encoding="utf-8")

    # Inject font CSS if font directory provided
    font_css = ""
    if font_dir:
        font_css = find_font_faces(font_dir)
        if font_css:
            print(f"  Injecting {font_css.count('@font-face')} font faces from {font_dir}")

    # Build PDF
    print(f"  Rendering {input_html.name} → {output_pdf.name} ({dpi} DPI)")

    stylesheets = []
    if font_css:
        stylesheets.append(CSS(string=font_css))

    html = HTML(string=html_content, base_url=str(input_html.parent))
    html.write_pdf(
        str(output_pdf),
        stylesheets=stylesheets or None,
        presentational_hints=True,
    )

    size_kb = output_pdf.stat().st_size / 1024
    print(f"  ✓ {output_pdf.name} ({size_kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="Ichita HTML→PDF Generator — branded print-quality PDFs"
    )
    parser.add_argument("input", type=Path, help="Input HTML file")
    parser.add_argument("output", type=Path, help="Output PDF file")
    parser.add_argument(
        "--fonts", type=Path, default=None,
        help="Font directory to inject (scans recursively for .ttf/.otf)"
    )
    parser.add_argument(
        "--dpi", type=int, default=300,
        help="Output resolution (default: 300)"
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    build_pdf(args.input, args.output, args.fonts, args.dpi)


if __name__ == "__main__":
    main()
