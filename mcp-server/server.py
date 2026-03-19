#!/usr/bin/env python3
"""
Ichita MCP Server — branded document generation tools.

Tools:
  - generate_brief: HTML → PDF executive brief
  - generate_docx: Markdown → branded DOCX
  - list_templates: show available templates/assets

Usage (stdio, for Claude Code):
  python server.py

Usage (HTTP, for claude.ai co-work):
  python server.py --http --port 8100
"""

import sys
import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Paths
SKILLS_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = SKILLS_ROOT / "assets" / "fonts"
LOGOS_DIR = SKILLS_ROOT / "assets" / "logos"
BRAND_DIR = SKILLS_ROOT / "assets" / "brand"
TEMPLATES_DIR = SKILLS_ROOT / "assets" / "templates"

mcp = FastMCP(
    "ichita",
    instructions="ICHITA branded document tools — executive briefs, DOCX, presentations.",
)


@mcp.tool()
def generate_brief(
    html_content: str,
    output_filename: str = "executive_brief.pdf",
    inject_fonts: bool = True,
) -> str:
    """Generate a print-ready PDF from an HTML executive brief template.

    Write the full HTML (with CSS) as html_content. The server renders it
    to a branded A4 PDF at 300 DPI using weasyprint.

    Args:
        html_content: Complete HTML string with embedded CSS for the brief.
        output_filename: Output PDF filename (saved to /tmp/).
        inject_fonts: Whether to inject Ichita brand fonts (AeonikTH etc).

    Returns:
        Path to generated PDF file and its size.
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        return "ERROR: weasyprint not installed. Run: pip install weasyprint"

    output_path = Path("/tmp") / output_filename

    # Build font CSS
    font_css = ""
    if inject_fonts and FONTS_DIR.exists():
        font_css = _build_font_css(FONTS_DIR)

    stylesheets = []
    if font_css:
        stylesheets.append(CSS(string=font_css))

    html = HTML(string=html_content, base_url=str(SKILLS_ROOT))
    html.write_pdf(str(output_path), stylesheets=stylesheets or None, presentational_hints=True)

    size_kb = output_path.stat().st_size / 1024
    return f"✓ Generated {output_path} ({size_kb:.0f} KB)"


@mcp.tool()
def generate_docx(
    markdown_content: str,
    output_filename: str = "document.docx",
) -> str:
    """Generate a branded ICHITA DOCX from Markdown content.

    Args:
        markdown_content: Markdown text to convert.
        output_filename: Output filename (saved to /tmp/).

    Returns:
        Path to generated DOCX file and its size.
    """
    import subprocess

    script = SKILLS_ROOT / "skills" / "ichita-docx" / "scripts" / "md_to_docx.py"
    if not script.exists():
        return f"ERROR: md_to_docx.py not found at {script}"

    md_path = Path("/tmp") / "input.md"
    output_path = Path("/tmp") / output_filename

    md_path.write_text(markdown_content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(script), str(md_path), str(output_path)],
        capture_output=True, text=True, timeout=30,
    )

    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip()}"

    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        return f"✓ Generated {output_path} ({size_kb:.0f} KB)"
    return f"ERROR: Output not created. stdout: {result.stdout.strip()}"


@mcp.tool()
def list_templates() -> str:
    """List available ICHITA brand assets, fonts, logos, and templates.

    Returns:
        Formatted list of available assets.
    """
    lines = ["# ICHITA Brand Assets\n"]

    # Logos
    if LOGOS_DIR.exists():
        logos = sorted(LOGOS_DIR.glob("*.png")) + sorted(LOGOS_DIR.glob("*.jpg")) + sorted(LOGOS_DIR.glob("*.jpeg"))
        lines.append(f"## Logos ({len(logos)})")
        for f in logos:
            size_kb = f.stat().st_size / 1024
            lines.append(f"  - {f.name} ({size_kb:.0f} KB)")

    # Fonts
    if FONTS_DIR.exists():
        font_dirs = sorted([d for d in FONTS_DIR.iterdir() if d.is_dir()])
        lines.append(f"\n## Font Families ({len(font_dirs)})")
        for d in font_dirs:
            fonts = list(d.glob("*.ttf")) + list(d.glob("*.otf"))
            lines.append(f"  - {d.name}/ ({len(fonts)} weights)")

    # Templates
    if TEMPLATES_DIR.exists():
        templates = sorted(TEMPLATES_DIR.glob("*"))
        lines.append(f"\n## Templates ({len(templates)})")
        for f in templates:
            lines.append(f"  - {f.name}")

    # Brand docs
    if BRAND_DIR.exists():
        docs = sorted(BRAND_DIR.glob("*.md"))
        lines.append(f"\n## Brand Documentation ({len(docs)})")
        for f in docs:
            lines.append(f"  - {f.name}")

    return "\n".join(lines)


@mcp.tool()
def get_brand_colors() -> str:
    """Get ICHITA brand color palette as CSS variables.

    Returns:
        CSS :root block with all brand colors.
    """
    return """:root {
  --blue: #2978FF;        /* Primary accent */
  --blue-light: #82B0FF;  /* Secondary accent */
  --grey1: #CFD9DB;        /* Borders, dividers */
  --grey2: #788F9C;        /* Muted text */
  --grey3: #263338;        /* Primary text */
  --blue-black: #171C21;  /* Dark backgrounds */
  --green: #34A853;        /* Positive */
  --red: #E83E3E;          /* Negative */
  --orange: #FFA000;       /* Warning */
  --white: #FFFFFF;
  --alt-row: #F0F4F5;     /* Table alternating rows */
}"""


def _build_font_css(font_dir: Path) -> str:
    """Generate @font-face CSS for fonts in directory."""
    WEIGHT_MAP = {
        "thin": 100, "light": 300, "regular": 400, "medium": 500,
        "semibold": 600, "bold": 700, "extrabold": 800, "black": 900,
    }
    faces = []
    for ext in ("*.ttf", "*.otf"):
        for f in font_dir.rglob(ext):
            name = f.stem.lower()
            weight = 400
            for key, val in WEIGHT_MAP.items():
                if key in name:
                    weight = val
                    break
            family = f.stem.split("-")[0] if "-" in f.stem else f.stem
            fmt = "truetype"
            faces.append(
                f"@font-face {{\n"
                f"  font-family: '{family}';\n"
                f"  src: url('{f.resolve()}') format('{fmt}');\n"
                f"  font-weight: {weight};\n"
                f"  font-style: normal;\n"
                f"}}"
            )
    return "\n".join(faces)


if __name__ == "__main__":
    if "--http" in sys.argv:
        port = 8100
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
