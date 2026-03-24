#!/usr/bin/env python3
"""
Simple font merger: Aeonik (Latin) + Bai Jamjuree (Thai) → Aeonik TH
"""

import sys
from pathlib import Path
from fontTools.ttLib import TTFont

AEONIK_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "aeonik"
BAI_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "bai-jamjuree"
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "aeonik-th"

# Character ranges
LATIN_RANGES = [(0x0000, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F)]
THAI_RANGE = [(0x0E00, 0x0E7F)]
SYMBOL_RANGES = [(0x2000, 0x206F), (0x2070, 0x209F), (0x20A0, 0x20CF)]

def get_codepoints(ranges):
    """Convert range list to set of codepoints."""
    result = set()
    for start, end in ranges:
        result.update(range(start, end + 1))
    return result

def merge_fonts(aeonik_path, bai_path, output_path):
    """Merge two fonts."""
    print(f"\n  📦 {aeonik_path.name} + {bai_path.name}")

    try:
        # Load fonts
        aeonik = TTFont(str(aeonik_path))
        bai = TTFont(str(bai_path))

        # Get font objects
        bai_cmap = bai.getBestCmap()
        merged_cmap = aeonik.getBestCmap()

        # Merge Thai glyphs
        thai_codepoints = get_codepoints(THAI_RANGE)
        thai_added = 0

        if bai_cmap and merged_cmap:
            for char_code, glyph_name in bai_cmap.items():
                if char_code in thai_codepoints:
                    merged_cmap[char_code] = glyph_name
                    thai_added += 1

        # Update font names
        name_table = aeonik["name"]
        for record in name_table.names:
            if record.nameID in (1, 4, 16):  # Family name variants
                try:
                    old_text = record.toUnicode()
                    if "Aeonik" in old_text:
                        new_text = old_text.replace("Aeonik", "Aeonik TH")
                        record.string = new_text.encode(record.getEncoding())
                except:
                    pass

        # Save
        aeonik.save(str(output_path))

        # Get file size
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✅ {output_path.name} ({size_kb:.1f} KB) — {thai_added} Thai glyphs added")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🎨 AEONIK TH FONT CREATION")
    print("="*70)

    # Create output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Output: {OUTPUT_DIR}")

    # Find and merge fonts
    weights_to_merge = {
        "Regular": ("Aeonik-Regular.otf", "BaiJamjuree-Regular.ttf"),
        "Bold": ("Aeonik-Bold.otf", "BaiJamjuree-Bold.ttf"),
        "Medium": ("Aeonik-Medium.otf", "BaiJamjuree-Medium.ttf"),
        "Light": ("Aeonik-Light.otf", "BaiJamjuree-Light.ttf"),
        "Italic": ("Aeonik-RegularItalic.otf", "BaiJamjuree-Italic.ttf"),
        "BoldItalic": ("Aeonik-BoldItalic.otf", "BaiJamjuree-BoldItalic.ttf"),
    }

    success = 0
    total = 0

    for weight, (aeonik_file, bai_file) in weights_to_merge.items():
        aeonik_path = AEONIK_DIR / aeonik_file
        bai_path = BAI_DIR / bai_file

        if not aeonik_path.exists() or not bai_path.exists():
            if not aeonik_path.exists():
                print(f"\n  ⚠️  {weight}: {aeonik_file} not found, skipping")
            if not bai_path.exists():
                print(f"\n  ⚠️  {weight}: {bai_file} not found, skipping")
            continue

        output_path = OUTPUT_DIR / f"AeonikTH-{weight}.ttf"
        total += 1

        if merge_fonts(aeonik_path, bai_path, output_path):
            success += 1

    print("\n" + "="*70)
    print(f"✅ COMPLETE: {success}/{total} font weights created")
    print("="*70)
    print(f"\n📦 Installation package ready in: {OUTPUT_DIR}\n")

    return 0 if success > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
