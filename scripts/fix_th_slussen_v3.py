#!/usr/bin/env python3
"""
fix_th_slussen_v3.py
Fix TH-Slussen fonts:
  Issue 1: Re-merge Thai glyphs for 4 fonts (Medium, MediumItalic, Semibold, SemiboldItalic)
  Issue 2: Fix nameID16/17 for all 10 fonts
"""

import os
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen

TH_DIR = Path("/mnt/c/Users/OhYeaH/OneDrive/Documents/fonts/fonts")
BAI_DIR = Path.home() / ".local/share/fonts"

NAME_CONFIG = {
    "Regular":        {"nameID16": "TH Slussen", "nameID17": "Regular"},
    "Bold":           {"nameID16": "TH Slussen", "nameID17": "Bold"},
    "Light":          {"nameID16": "TH Slussen", "nameID17": "Light"},
    "Medium":         {"nameID16": "TH Slussen", "nameID17": "Medium"},
    "Semibold":       {"nameID16": "TH Slussen", "nameID17": "SemiBold"},
    "RegularItalic":  {"nameID16": "TH Slussen", "nameID17": "Regular Italic"},
    "BoldItalic":     {"nameID16": "TH Slussen", "nameID17": "Bold Italic"},
    "LightItalic":    {"nameID16": "TH Slussen", "nameID17": "Light Italic"},
    "MediumItalic":   {"nameID16": "TH Slussen", "nameID17": "Medium Italic"},
    "SemiboldItalic": {"nameID16": "TH Slussen", "nameID17": "SemiBold Italic"},
}

REMERGE = {
    "Medium":         "BaiJamjuree-Medium.ttf",
    "MediumItalic":   "BaiJamjuree-MediumItalic.ttf",
    "Semibold":       "BaiJamjuree-SemiBold.ttf",
    "SemiboldItalic": "BaiJamjuree-SemiBoldItalic.ttf",
}

ALL_WEIGHTS = [
    "Regular",
    "Bold",
    "Light",
    "Medium",
    "Semibold",
    "RegularItalic",
    "BoldItalic",
    "LightItalic",
    "MediumItalic",
    "SemiboldItalic",
]


def remerge_thai(font_path: Path, bai_path: Path, weight_name: str) -> None:
    print(f"\n[remerge] {font_path.name} ← {bai_path.name}")

    th_font = TTFont(font_path)
    bai_font = TTFont(bai_path)

    bai_gs = bai_font.getGlyphSet()
    cff = th_font["CFF "]
    top_dict = cff.cff.topDictIndex[0]
    charstrings = top_dict.CharStrings

    replaced = 0
    skipped_no_bai = 0

    for glyph_name in th_font.getGlyphOrder():
        if "uni0E" not in glyph_name:
            continue
        if glyph_name not in bai_gs:
            skipped_no_bai += 1
            continue

        bai_glyph = bai_gs[glyph_name]
        pen = T2CharStringPen(bai_glyph.width, bai_gs)
        bai_glyph.draw(pen)
        new_cs = pen.getCharString()
        new_cs.private = top_dict.Private
        new_cs.globalSubrs = getattr(cff.cff, "GlobalSubrs", [])

        old_index = charstrings.charStrings[glyph_name]
        charstrings.charStringsIndex[old_index] = new_cs

        th_font["hmtx"].metrics[glyph_name] = bai_font["hmtx"].metrics[glyph_name]
        replaced += 1

    print(f"  Replaced: {replaced} glyphs | Skipped (not in BaiJamjuree): {skipped_no_bai}")
    th_font.save(font_path)
    print(f"  Saved: {font_path}")


def fix_name_ids(font_path: Path, weight_name: str) -> None:
    print(f"\n[names] {font_path.name}")
    cfg = NAME_CONFIG[weight_name]
    font = TTFont(font_path)
    name_table = font["name"]

    for nameID, value in [(16, cfg["nameID16"]), (17, cfg["nameID17"])]:
        # Windows
        name_table.setName(value, nameID, platformID=3, platEncID=1, langID=0x0409)
        # Mac
        name_table.setName(value, nameID, platformID=1, platEncID=0, langID=0)
        print(f"  nameID{nameID} = '{value}'")

    font.save(font_path)
    print(f"  Saved: {font_path}")


def verify(font_path: Path, bai_path: Path | None, weight_name: str) -> None:
    print(f"\n[verify] {font_path.name}")
    font = TTFont(font_path)

    # Check nameID16/17
    name_table = font["name"]
    cfg = NAME_CONFIG[weight_name]
    for nameID, expected in [(16, cfg["nameID16"]), (17, cfg["nameID17"])]:
        record = name_table.getName(nameID, 3, 1, 0x0409)
        actual = record.toUnicode() if record else None
        status = "OK" if actual == expected else f"MISMATCH (got '{actual}')"
        print(f"  nameID{nameID}: expected='{expected}' → {status}")

    # Check Thai glyph widths against BaiJamjuree
    if bai_path is not None:
        bai_font = TTFont(bai_path)
        th_hmtx = font["hmtx"].metrics
        bai_hmtx = bai_font["hmtx"].metrics

        thai_glyphs = [g for g in font.getGlyphOrder() if "uni0E" in g]
        match = 0
        total = 0
        for g in thai_glyphs:
            if g not in bai_hmtx:
                continue
            total += 1
            if th_hmtx.get(g, (None,))[0] == bai_hmtx[g][0]:
                match += 1
        print(f"  Thai width match: {match}/{total}")


def main():
    print("=" * 60)
    print("TH-Slussen Font Fixer v3")
    print("=" * 60)

    # Issue 1: Re-merge Thai glyphs for 4 fonts
    print("\n--- Issue 1: Re-merge Thai glyphs ---")
    for weight, bai_file in REMERGE.items():
        font_path = TH_DIR / f"TH-Slussen-{weight}.otf"
        bai_path = BAI_DIR / bai_file
        if not font_path.exists():
            print(f"  SKIP (not found): {font_path}")
            continue
        if not bai_path.exists():
            print(f"  SKIP (BaiJamjuree not found): {bai_path}")
            continue
        remerge_thai(font_path, bai_path, weight)

    # Issue 2: Fix nameID16/17 for all 10 fonts
    print("\n--- Issue 2: Fix nameID16/17 ---")
    for weight in ALL_WEIGHTS:
        font_path = TH_DIR / f"TH-Slussen-{weight}.otf"
        if not font_path.exists():
            print(f"  SKIP (not found): {font_path}")
            continue
        fix_name_ids(font_path, weight)

    # Verification
    print("\n--- Verification ---")
    for weight in ALL_WEIGHTS:
        font_path = TH_DIR / f"TH-Slussen-{weight}.otf"
        if not font_path.exists():
            print(f"  SKIP (not found): {font_path}")
            continue
        bai_file = REMERGE.get(weight)
        bai_path = (BAI_DIR / bai_file) if bai_file else None
        verify(font_path, bai_path, weight)

    print("\n Done.")


if __name__ == "__main__":
    main()
