"""
restyle_pptx.py — Apply ICHITA fonts and colors to an existing PPTX.

Preserves all shapes, positions, and layout. Only changes:
  - Font names → Aeonik (Latin) / TH Sarabun New (Thai)
  - Explicit hex color values → ICHITA color palette

Usage:
    python restyle_pptx.py INPUT.pptx OUTPUT.pptx

No external dependencies — Python stdlib only.
"""
import zipfile
import re
import sys
import os


# ── Font mapping ──────────────────────────────────────────────────────────────
# Maps source font names → ICHITA brand fonts.
# Add entries here when new source fonts are encountered.

FONT_MAP = {
    # Common office fonts → Aeonik
    "Calibri Light":   "Aeonik",
    "Calibri":         "Aeonik",
    "Arial Black":     "Aeonik",
    "Arial":           "Aeonik",
    "Tahoma":          "Aeonik",
    "Trebuchet MS":    "Aeonik",
    "Times New Roman": "Aeonik",
    # Theme font placeholders
    "+mj-lt":          "Aeonik",
    "+mn-lt":          "Aeonik",
    # Thai fonts → TH Sarabun New
    "Angsana New":     "TH Sarabun New",
    "Cordia New":      "TH Sarabun New",
    "TH SarabunPSK":   "TH Sarabun New",
    "DilleniaUPC":     "TH Sarabun New",
    "Browallia New":   "TH Sarabun New",
    "LighthaUPC":      "TH Sarabun New",
}

# ── Color mapping (source hex → ICHITA hex, 6-char uppercase) ─────────────────
# ICHITA palette reference:
#   2978FF  Ichita Blue (primary accent)
#   82B0FF  Blue Light (secondary accent)
#   CFD9DB  Blue Grey 01 (main backdrop / light bg)
#   788F9C  Blue Grey 02 (muted text, borders, KPI bg)
#   263338  Blue Grey 03 (primary text, dark bg, logo default)
#   171C21  Blue Black (darkest anchor)
#   FFFFFF  White
#   34A853  Success Green
#   E83E3E  Warning Red
#
# Add source colors below as you encounter them in source files.

COLOR_MAP = {
    # Common dark navy blues → Blue Grey 03 (ICHITA dark anchor)
    "1A2B5E": "263338",
    "0D2040": "263338",
    "002060": "263338",
    "1F3864": "263338",
    "17375E": "263338",
    # Medium navy / corporate blues → Ichita Blue
    "253880": "2978FF",
    "4472C4": "2978FF",
    "2E75B6": "2978FF",
    "0070C0": "2978FF",
    "1565C0": "2978FF",
    "1B4F8A": "2978FF",
    # Teal / cyan → Ichita Blue
    "0F7D8C": "2978FF",
    "00838F": "2978FF",
    # Gold / amber → Blue Grey 02 (muted utility)
    "D4A017": "788F9C",
    "F0C040": "CFD9DB",
    "FFC000": "788F9C",
    "ED7D31": "788F9C",
    # Dark grays / slate → Blue Grey 03
    "334155": "263338",
    "3D3D3D": "263338",
    "404040": "263338",
    "595959": "263338",
    "44546A": "263338",
    # Light grays → Blue Grey 01
    "94A3B8": "CFD9DB",
    "D9D9D9": "CFD9DB",
    "E7E6E6": "CFD9DB",
    "BFBFBF": "CFD9DB",
    # Standard accent colors kept as ICHITA functional colors
    "70AD47": "34A853",   # green → ICHITA success green
    "FF0000": "E83E3E",   # red   → ICHITA warning red
    "C00000": "E83E3E",
}

# Files inside the ZIP to restyle
RESTYLE_PATTERNS = [
    r"ppt/slides/slide\d+\.xml$",
    r"ppt/slideLayouts/slideLayout\d+\.xml$",
    r"ppt/slideMasters/slideMaster\d+\.xml$",
    r"ppt/theme/theme\d+\.xml$",
]


def should_restyle(name: str) -> bool:
    return any(re.search(p, name) for p in RESTYLE_PATTERNS)


def apply_fonts(xml: str) -> str:
    for old, new in FONT_MAP.items():
        xml = xml.replace(f'typeface="{old}"', f'typeface="{new}"')
    return xml


def apply_colors(xml: str) -> str:
    for old, new in COLOR_MAP.items():
        xml = re.sub(
            rf'(?i)\bval="{re.escape(old)}"',
            f'val="{new}"',
            xml,
        )
    return xml


def restyle(xml: str) -> str:
    xml = apply_fonts(xml)
    xml = apply_colors(xml)
    return xml


def main(input_path: str, output_path: str) -> None:
    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    with zipfile.ZipFile(input_path, "r") as zin:
        files = {name: zin.read(name) for name in zin.namelist()}

    changed = []
    for name in list(files):
        if should_restyle(name):
            original = files[name].decode("utf-8", errors="replace")
            restyled = restyle(original)
            if restyled != original:
                changed.append(name)
            files[name] = restyled.encode("utf-8")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)

    print(f"Restyled {len(changed)} file(s) → {output_path}")
    for f in sorted(changed):
        print(f"  {f}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python restyle_pptx.py INPUT.pptx OUTPUT.pptx")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
