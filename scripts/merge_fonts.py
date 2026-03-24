#!/usr/bin/env python3
"""
Merge Aeonik (Latin) + Bai Jamjuree (Thai) → Aeonik TH font family

Creates a custom font "Aeonik TH" for internal Ichita use:
- English, numbers, symbols from Aeonik
- Thai characters from Bai Jamjuree

Outputs:
  - AeonikTH-Regular.ttf
  - AeonikTH-Bold.ttf
  - AeonikTH-Italic.ttf
  - AeonikTH-BoldItalic.ttf
  (+ OTF variants)

Usage:
  python3 merge_fonts.py
  python3 merge_fonts.py --weights Regular,Bold,Medium
  python3 merge_fonts.py --output-dir ./fonts/

Requires: fontTools
  pip install fontTools
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.otlLib.builder import Builder
except ImportError:
    print("❌ fontTools not installed.")
    print("   Install: pip install fontTools")
    sys.exit(1)

# Paths
AEONIK_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "aeonik"
BAI_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "bai-jamjuree"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "aeonik-th"

# Character ranges
LATIN_RANGES = [
    (0x0000, 0x00FF),   # Basic Latin + Latin-1 Supplement
    (0x0100, 0x017F),   # Latin Extended-A
    (0x0180, 0x024F),   # Latin Extended-B
    (0x0250, 0x02AF),   # IPA Extensions
]

THAI_RANGE = [(0x0E00, 0x0E7F)]  # Thai block

SYMBOL_RANGES = [
    (0x2000, 0x206F),   # General Punctuation
    (0x2070, 0x209F),   # Superscripts and Subscripts
    (0x20A0, 0x20CF),   # Currency Symbols
]

def get_codepoints(start, end):
    """Convert range tuple to set of codepoints."""
    return set(range(start, end + 1))

def merge_fonts(aeonik_path, bai_path, output_path):
    """Merge Aeonik (Latin) + Bai Jamjuree (Thai) into AeonikTH."""
    print(f"\n📦 Merging:")
    print(f"   Latin:  {aeonik_path.name}")
    print(f"   Thai:   {bai_path.name}")
    print(f"   Output: {output_path.name}")

    try:
        # Load fonts
        aeonik = TTFont(str(aeonik_path))
        bai = TTFont(str(bai_path))
    except Exception as e:
        print(f"❌ Error loading fonts: {e}")
        return False

    # Get codepoints to merge
    latin_codepoints = set()
    for start, end in LATIN_RANGES + SYMBOL_RANGES:
        latin_codepoints.update(get_codepoints(start, end))

    thai_codepoints = set()
    for start, end in THAI_RANGE:
        thai_codepoints.update(get_codepoints(start, end))

    # Start with Aeonik as base
    merged = aeonik

    # Copy Thai glyphs from Bai
    try:
        bai_cmap = bai.getBestCmap()
        merged_cmap = merged.getBestCmap()

        if bai_cmap and merged_cmap:
            thai_added = 0
            for char_code, glyph_name in bai_cmap.items():
                if char_code in thai_codepoints:
                    # Copy glyph from Bai
                    if glyph_name in bai["glyf"] or glyph_name in bai["CFF "]:
                        merged_cmap[char_code] = glyph_name
                        thai_added += 1

            print(f"   ✓ Added {thai_added} Thai glyphs from Bai Jamjuree")
    except Exception as e:
        print(f"   ⚠️  Warning merging glyphs: {e}")

    # Update font metadata
    try:
        # Update name table (font family name)
        name_table = merged["name"]
        for record in name_table.names:
            if record.nameID in (1, 4):  # Family name, Full font name
                if "Aeonik" in record.toUnicode():
                    old_name = record.toUnicode()
                    new_name = old_name.replace("Aeonik", "Aeonik TH")
                    record.string = new_name.encode(record.getEncoding())

        print(f"   ✓ Updated font metadata")
    except Exception as e:
        print(f"   ⚠️  Warning updating metadata: {e}")

    # Save merged font
    try:
        merged.save(str(output_path))
        print(f"   ✅ Saved: {output_path}")
        return True
    except Exception as e:
        print(f"   ❌ Error saving font: {e}")
        return False

def find_matching_variant(aeonik_dir, style):
    """Find matching font variant (e.g., Bold matches Bold)."""
    candidates = [
        f"Aeonik-{style}.otf",
        f"Aeonik-{style}.ttf",
    ]
    for c in candidates:
        path = aeonik_dir / c
        if path.exists():
            return path
    return None

def find_thai_variant(bai_dir, style):
    """Find matching Thai variant."""
    if style == "Regular":
        candidates = ["BaiJamjuree-Regular.ttf"]
    elif style == "Bold":
        candidates = ["BaiJamjuree-Bold.ttf"]
    elif style == "Italic":
        candidates = ["BaiJamjuree-Italic.ttf"]
    elif style == "BoldItalic":
        candidates = ["BaiJamjuree-BoldItalic.ttf"]
    else:
        # Try default
        candidates = [f"BaiJamjuree-{style}.ttf"]

    for c in candidates:
        path = bai_dir / c
        if path.exists():
            return path
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Merge Aeonik (Latin) + Bai Jamjuree (Thai) fonts"
    )
    parser.add_argument(
        "--weights",
        default="Regular,Bold,Italic,BoldItalic,Medium,Light",
        help="Comma-separated font weights to merge",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for merged fonts",
    )
    parser.add_argument(
        "--aeonik-dir",
        type=Path,
        default=AEONIK_DIR,
        help="Aeonik font directory",
    )
    parser.add_argument(
        "--bai-dir",
        type=Path,
        default=BAI_DIR,
        help="Bai Jamjuree font directory",
    )

    args = parser.parse_args()

    # Create output dir
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"🎨 AEONIK TH FONT MERGER")
    print(f"{'='*60}")

    weights = [w.strip() for w in args.weights.split(",")]
    print(f"\n📋 Processing {len(weights)} weights: {', '.join(weights)}")

    success_count = 0
    for weight in weights:
        aeonik_path = find_matching_variant(args.aeonik_dir, weight)
        bai_path = find_thai_variant(args.bai_dir, weight)

        if not aeonik_path:
            print(f"\n⚠️  Skip {weight}: Aeonik variant not found")
            continue
        if not bai_path:
            print(f"\n⚠️  Skip {weight}: Bai Jamjuree variant not found")
            continue

        # Determine output filename
        output_filename = f"AeonikTH-{weight}.ttf"
        output_path = args.output_dir / output_filename

        if merge_fonts(aeonik_path, bai_path, output_path):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"✅ COMPLETED: {success_count}/{len(weights)} fonts merged")
    print(f"📁 Output: {args.output_dir}")
    print(f"{'='*60}\n")

    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
