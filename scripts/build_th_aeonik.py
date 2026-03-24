#!/usr/bin/env python3
"""
Build TH-Aeonik font family — unified pipeline.

Merges Aeonik (Latin) + Bai Jamjuree (Thai) into TH-Aeonik with complete
OpenType support for Thai text shaping on Windows.

Pipeline steps:
  1. Copy Thai glyphs + variants from Bai Jamjuree (CFF charstrings)
  2. Merge GPOS/GDEF/GSUB tables from Bai Jamjuree (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2 v4, fsType, panose, CFF fontName
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Set vertical metrics — usWinAscent/Descent for Thai clipping prevention
  6. TTX roundtrip — sort coverage tables (Uniscribe compliance)
  7. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Sources:
  Latin: Aeonik OTF (D:\\ drive preferred, fallback assets/fonts/aeonik/)
  Thai:  Bai Jamjuree (system fonts preferred, fallback assets/fonts/bai-jamjuree/)

Usage:
  python3 build_th_aeonik.py                    # Build all 6 weights
  python3 build_th_aeonik.py --weights Bold,Light  # Build specific weights

Requires: fontTools >= 4.0
"""

import copy as copy_mod
import os
import sys
import warnings
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent
ASSETS = SCRIPT_DIR.parent / "assets"

# Source directories
AEONIK_D_DRIVE = Path("/mnt/d/Doccument/New Identity/Aeonik-font-download/Aeonik-font-download")
AEONIK_LOCAL = ASSETS / "fonts" / "aeonik"
BAI_SYSTEM = Path.home() / ".local" / "share" / "fonts"
BAI_LOCAL = ASSETS / "fonts" / "bai-jamjuree"
OUTPUT_DIR = ASSETS / "fonts" / "aeonik-th"

# fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1

# Weight mapping: output_name -> (aeonik_file, bai_file)
WEIGHTS = {
    "Regular":       ("Aeonik-Regular.otf",        "BaiJamjuree-Regular.ttf"),
    "Bold":          ("Aeonik-Bold.otf",            "BaiJamjuree-Bold.ttf"),
    "Light":         ("Aeonik-Light.otf",           "BaiJamjuree-Light.ttf"),
    "RegularItalic": ("Aeonik-RegularItalic.otf",   "BaiJamjuree-Italic.ttf"),
    "BoldItalic":    ("Aeonik-BoldItalic.otf",      "BaiJamjuree-BoldItalic.ttf"),
    "LightItalic":   ("Aeonik-LightItalic.otf",     "BaiJamjuree-LightItalic.ttf"),
}

# Per-weight metadata config (Windows RIBBI model)
WEIGHT_CONFIG = {
    "Regular": {
        "nameID1": "TH Aeonik", "nameID2": "Regular",
        "nameID4": "TH Aeonik", "nameID6": "TH-Aeonik-Regular",
        "nameID16": "TH Aeonik", "nameID17": "Regular",
        "fsSelection": REGULAR | USE_TYPO, "macStyle": 0,
        "weightClass": 400, "panose_bWeight": 5,
    },
    "Bold": {
        "nameID1": "TH Aeonik", "nameID2": "Bold",
        "nameID4": "TH Aeonik Bold", "nameID6": "TH-Aeonik-Bold",
        "nameID16": "TH Aeonik", "nameID17": "Bold",
        "fsSelection": BOLD | USE_TYPO, "macStyle": MAC_BOLD,
        "weightClass": 700, "panose_bWeight": 8,
    },
    "Light": {
        "nameID1": "TH Aeonik Light", "nameID2": "Regular",
        "nameID4": "TH Aeonik Light", "nameID6": "TH-Aeonik-Light",
        "nameID16": "TH Aeonik", "nameID17": "Light",
        "fsSelection": REGULAR | USE_TYPO, "macStyle": 0,
        "weightClass": 300, "panose_bWeight": 4,
    },
    "RegularItalic": {
        "nameID1": "TH Aeonik", "nameID2": "Italic",
        "nameID4": "TH Aeonik Italic", "nameID6": "TH-Aeonik-RegularItalic",
        "nameID16": "TH Aeonik", "nameID17": "Regular Italic",
        "fsSelection": ITALIC | USE_TYPO, "macStyle": MAC_ITALIC,
        "weightClass": 400, "panose_bWeight": 5,
    },
    "BoldItalic": {
        "nameID1": "TH Aeonik", "nameID2": "Bold Italic",
        "nameID4": "TH Aeonik Bold Italic", "nameID6": "TH-Aeonik-BoldItalic",
        "nameID16": "TH Aeonik", "nameID17": "Bold Italic",
        "fsSelection": BOLD | ITALIC | USE_TYPO, "macStyle": MAC_BOLD | MAC_ITALIC,
        "weightClass": 700, "panose_bWeight": 8,
    },
    "LightItalic": {
        "nameID1": "TH Aeonik Light", "nameID2": "Italic",
        "nameID4": "TH Aeonik Light Italic", "nameID6": "TH-Aeonik-LightItalic",
        "nameID16": "TH Aeonik", "nameID17": "Light Italic",
        "fsSelection": ITALIC | USE_TYPO, "macStyle": MAC_ITALIC,
        "weightClass": 300, "panose_bWeight": 4,
    },
}


# ---------------------------------------------------------------------------
# Source finding
# ---------------------------------------------------------------------------

def find_aeonik(filename):
    for d in [AEONIK_D_DRIVE, AEONIK_LOCAL]:
        p = d / filename
        if p.exists():
            return p
    return None


def find_bai(filename):
    for d in [BAI_SYSTEM, BAI_LOCAL]:
        p = d / filename
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Step 1: Copy Thai glyphs
# ---------------------------------------------------------------------------

def _add_glyph_to_cff(aeonik_font, bai_font, bai_glyph_name, target_name):
    cff = aeonik_font["CFF "]
    top_dict = cff.cff.topDictIndex[0]
    charstrings = top_dict.CharStrings

    bai_glyph_set = bai_font.getGlyphSet()
    if bai_glyph_name not in bai_glyph_set:
        return False

    bai_glyph = bai_glyph_set[bai_glyph_name]
    pen = T2CharStringPen(bai_glyph.width, bai_glyph_set)
    bai_glyph.draw(pen)
    charstring = pen.getCharString()

    charstring.private = top_dict.Private
    charstring.globalSubrs = getattr(cff.cff, "GlobalSubrs", [])

    new_index = len(charstrings.charStringsIndex)
    charstrings.charStringsIndex.append(charstring)
    charstrings.charStrings[target_name] = new_index

    glyph_order = aeonik_font.getGlyphOrder()
    if target_name not in glyph_order:
        glyph_order.append(target_name)
        aeonik_font.setGlyphOrder(glyph_order)

    hmtx = aeonik_font["hmtx"]
    if bai_glyph_name in bai_font["hmtx"].metrics:
        hmtx.metrics[target_name] = bai_font["hmtx"].metrics[bai_glyph_name]

    return True


def copy_thai_glyphs(aeonik_font, bai_font):
    bai_cmap = bai_font.getBestCmap()
    if not bai_cmap:
        print("     !! No cmap in Bai Jamjuree")
        return 0

    # Cmap-mapped Thai codepoints (U+0E01-0E5B)
    thai_mappings = {
        cp: gn for cp, gn in bai_cmap.items() if 0x0E01 <= cp <= 0x0E5B
    }

    added = 0
    for cp, bai_gn in sorted(thai_mappings.items()):
        if _add_glyph_to_cff(aeonik_font, bai_font, bai_gn, f"uni{cp:04X}"):
            added += 1

    # Update cmap
    charstrings = aeonik_font["CFF "].cff.topDictIndex[0].CharStrings
    for table in aeonik_font["cmap"].tables:
        if hasattr(table, "cmap") and table.cmap is not None:
            for cp in thai_mappings:
                tn = f"uni{cp:04X}"
                if tn in charstrings.charStrings:
                    table.cmap[cp] = tn

    # Add ALL remaining Bai glyphs (variants + non-Thai for GPOS/GSUB integrity)
    extra = 0
    skip = {".notdef", ".null", "NULL", "nonmarkingreturn", "CR"}
    for gn in bai_font.getGlyphOrder():
        if gn in charstrings.charStrings or gn in skip:
            continue
        if _add_glyph_to_cff(aeonik_font, bai_font, gn, gn):
            extra += 1

    print(f"     [1] Glyphs: {added} Thai cmap + {extra} extra (GPOS/GSUB)")
    return added + extra


# ---------------------------------------------------------------------------
# Step 2: Merge GPOS/GDEF/GSUB
# ---------------------------------------------------------------------------

def merge_ot_tables(aeonik_font, bai_font):
    if "GPOS" not in bai_font:
        return

    aeonik_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
    gpos_n = len(bai_font["GPOS"].table.LookupList.Lookup)
    scripts = [sr.ScriptTag for sr in aeonik_font["GPOS"].table.ScriptList.ScriptRecord]

    if "GDEF" in bai_font:
        merged_gdef = copy_mod.deepcopy(bai_font["GDEF"])
        if "GDEF" in aeonik_font and aeonik_font["GDEF"].table.GlyphClassDef:
            for g, c in aeonik_font["GDEF"].table.GlyphClassDef.classDefs.items():
                if g not in merged_gdef.table.GlyphClassDef.classDefs:
                    merged_gdef.table.GlyphClassDef.classDefs[g] = c
        merged_glyphs = set(aeonik_font.getGlyphOrder())
        merged_gdef.table.GlyphClassDef.classDefs = {
            g: c for g, c in merged_gdef.table.GlyphClassDef.classDefs.items()
            if g in merged_glyphs
        }
        aeonik_font["GDEF"] = merged_gdef
        marks = len([g for g, c in merged_gdef.table.GlyphClassDef.classDefs.items() if c == 3])
    else:
        marks = 0

    gsub_n = 0
    if "GSUB" in bai_font:
        aeonik_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
        gsub_n = len(bai_font["GSUB"].table.LookupList.Lookup)

    print(f"     [2] OT tables: GPOS={gpos_n} lookups, GDEF={marks} marks, "
          f"GSUB={gsub_n} lookups, scripts={','.join(scripts)}")


# ---------------------------------------------------------------------------
# Step 3: Metadata (RIBBI naming + OS/2 + CFF)
# ---------------------------------------------------------------------------

def _set_name(nt, nid, val, pid=3, peid=1, lid=0x0409):
    if val is None:
        nt.removeNames(nameID=nid, platformID=pid, platEncID=peid, langID=lid)
        return
    nt.setName(val, nid, pid, peid, lid)


def apply_metadata(font, weight_name):
    cfg = WEIGHT_CONFIG[weight_name]
    nt = font["name"]

    # Name table (Windows + Mac)
    for nid in [1, 2, 4, 6, 16, 17]:
        key = f"nameID{nid}"
        _set_name(nt, nid, cfg[key])
        mac_val = cfg[key]
        _set_name(nt, nid, mac_val, pid=1, peid=0, lid=0)

    uid = f"THAeonik-{weight_name}"
    _set_name(nt, 3, uid)
    _set_name(nt, 3, uid, pid=1, peid=0, lid=0)

    # OS/2
    os2 = font["OS/2"]
    os2.fsType = 0
    if os2.version < 4:
        os2.version = 4
        for attr, default in [("sxHeight", 0), ("sCapHeight", 0),
                              ("usDefaultChar", 0), ("usBreakChar", 32),
                              ("usMaxContext", 0)]:
            if not hasattr(os2, attr):
                setattr(os2, attr, default)
    os2.fsSelection = cfg["fsSelection"]
    os2.usWeightClass = cfg["weightClass"]
    os2.panose.bWeight = cfg["panose_bWeight"]

    # head.macStyle
    font["head"].macStyle = cfg["macStyle"]

    # CFF fontName
    if "CFF " in font:
        font["CFF "].cff.fontNames[0] = cfg["nameID6"]

    print(f"     [3] Metadata: ID1='{cfg['nameID1']}' ID2='{cfg['nameID2']}' "
          f"fsSel=0x{cfg['fsSelection']:04X} wt={cfg['weightClass']}")


# ---------------------------------------------------------------------------
# Step 4: OS/2 Thai range bits
# ---------------------------------------------------------------------------

def set_thai_bits(font):
    os2 = font["OS/2"]
    os2.ulUnicodeRange1 |= (1 << 24)   # bit 24 = Thai
    os2.ulCodePageRange1 |= (1 << 16)  # bit 16 = CP874 (Thai)
    print(f"     [4] Thai bits: ulUR1 bit24=True, ulCPR1 bit16=True")


# ---------------------------------------------------------------------------
# Step 5: Vertical metrics
# ---------------------------------------------------------------------------

def set_vertical_metrics(font):
    os2 = font["OS/2"]
    hhea = font["hhea"]
    os2.usWinAscent = 1550
    os2.usWinDescent = 561
    hhea.ascent = 1550
    hhea.descent = -561
    # sTypoAscender/sTypoDescender/sTypoLineGap untouched
    print(f"     [5] Metrics: winAsc=1550 winDes=561 hhea=1550/-561 "
          f"(sTypo={os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap} kept)")


# ---------------------------------------------------------------------------
# Step 6: TTX roundtrip (sort coverage tables)
# ---------------------------------------------------------------------------

def ttx_roundtrip(font_path):
    import tempfile
    ttx_path = tempfile.mktemp(suffix=".ttx")
    f = TTFont(str(font_path))
    f.saveXML(ttx_path)
    f2 = TTFont()
    f2.importXML(ttx_path)
    f2.save(str(font_path))
    os.unlink(ttx_path)
    print(f"     [6] TTX roundtrip: coverage tables sorted")


# ---------------------------------------------------------------------------
# Step 7: Verify
# ---------------------------------------------------------------------------

def verify_font(weight_name):
    cfg = WEIGHT_CONFIG[weight_name]
    path = OUTPUT_DIR / f"TH-Aeonik-{weight_name}.otf"
    if not path.exists():
        return

    font = TTFont(str(path))
    cmap = font.getBestCmap()
    os2 = font["OS/2"]
    checks = []

    # Thai cmap
    thai = {cp: g for cp, g in cmap.items() if 0x0E00 <= cp <= 0x0E7F}
    checks.append(f"Thai={len(thai)}")
    if 0x0E00 in thai:
        checks.append("U+0E00=YES!!")
    if any(0x0E5C <= cp <= 0x0E7F for cp in thai):
        checks.append("spurious!!")

    # Latin match
    aeonik_path = find_aeonik(WEIGHTS[weight_name][0])
    if aeonik_path:
        aeonik_src = TTFont(str(aeonik_path))
        gs_m, gs_a = font.getGlyphSet(), aeonik_src.getGlyphSet()
        ac = aeonik_src.getBestCmap()
        match = total = 0
        for cp in range(0x20, 0x7F):
            mg, ag = cmap.get(cp), ac.get(cp)
            if mg and ag and mg in gs_m and ag in gs_a:
                total += 1
                pm, pa = RecordingPen(), RecordingPen()
                gs_m[mg].draw(pm)
                gs_a[ag].draw(pa)
                if pm.value == pa.value:
                    match += 1
        pct = 100 * match / total if total else 0
        checks.append(f"Latin={pct:.0f}%")

    # GPOS/GDEF
    gpos_n = len(font["GPOS"].table.LookupList.Lookup) if "GPOS" in font else 0
    marks = 0
    if "GDEF" in font and font["GDEF"].table.GlyphClassDef:
        marks = len([g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3])
    checks.append(f"GPOS={gpos_n}")
    checks.append(f"marks={marks}")

    # OS/2 bits
    thai_ur = bool(os2.ulUnicodeRange1 & (1 << 24))
    thai_cp = bool(os2.ulCodePageRange1 & (1 << 16))
    checks.append(f"ThaiBits={'OK' if thai_ur and thai_cp else 'FAIL'}")

    # Vertical metrics
    checks.append(f"winAsc={os2.usWinAscent}")
    checks.append(f"winDes={os2.usWinDescent}")

    # RIBBI
    n1 = font["name"].getName(1, 3, 1, 0x0409)
    n2 = font["name"].getName(2, 3, 1, 0x0409)
    n1t = n1.toUnicode() if n1 else "?"
    n2t = n2.toUnicode() if n2 else "?"
    checks.append(f"'{n1t}/{n2t}'")

    print(f"     [7] Verify: {' | '.join(checks)}")


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build_font(weight_name, aeonik_file, bai_file):
    print(f"\n  === {weight_name} ===")

    aeonik_path = find_aeonik(aeonik_file)
    bai_path = find_bai(bai_file)

    if not aeonik_path:
        print(f"     !! Aeonik not found: {aeonik_file}")
        return False
    if not bai_path:
        print(f"     !! Bai Jamjuree not found: {bai_file}")
        return False

    print(f"     Latin: {aeonik_path}")
    print(f"     Thai:  {bai_path}")

    aeonik = TTFont(str(aeonik_path))
    bai = TTFont(str(bai_path))

    if "CFF " not in aeonik:
        print(f"     !! Aeonik is not CFF format")
        return False

    output_path = OUTPUT_DIR / f"TH-Aeonik-{weight_name}.otf"

    # Step 1: Copy Thai glyphs
    copy_thai_glyphs(aeonik, bai)

    # Step 2: Merge GPOS/GDEF/GSUB
    merge_ot_tables(aeonik, bai)

    # Step 3: Metadata
    apply_metadata(aeonik, weight_name)

    # Step 4: Thai range bits
    set_thai_bits(aeonik)

    # Step 5: Vertical metrics
    set_vertical_metrics(aeonik)

    # Save (before TTX roundtrip)
    aeonik.save(str(output_path))

    # Step 6: TTX roundtrip
    ttx_roundtrip(output_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"     Saved: {output_path.name} ({size_kb:.0f} KB)")

    # Step 7: Verify
    verify_font(weight_name)

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build TH-Aeonik font family")
    parser.add_argument("--weights", default=None,
                        help="Comma-separated weights (default: all)")
    args = parser.parse_args()

    weights = WEIGHTS
    if args.weights:
        selected = [w.strip() for w in args.weights.split(",")]
        weights = {k: v for k, v in WEIGHTS.items() if k in selected}

    print("\n" + "=" * 70)
    print("  TH-AEONIK BUILD PIPELINE")
    print("  Aeonik (Latin) + Bai Jamjuree (Thai) = TH Aeonik")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    for wn, (af, bf) in weights.items():
        if build_font(wn, af, bf):
            success += 1

    total = len(weights)
    print(f"\n{'=' * 70}")
    status = "PASS" if success == total else "FAIL"
    print(f"  {status}: {success}/{total} fonts built")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'=' * 70}\n")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
