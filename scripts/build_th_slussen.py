#!/usr/bin/env python3
"""
Build TH-Slussen font family — unified pipeline.

Merges Slussen (Latin) + Bai Jamjuree (Thai) into TH-Slussen with complete
OpenType support for Thai text shaping on Windows.

Pipeline steps:
  1. Copy Thai glyphs + variants from Bai Jamjuree (CFF charstrings via T2CharStringPen)
  2. Merge GPOS/GDEF/GSUB tables from Bai Jamjuree (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2, CFF fontName
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Keep vertical metrics IDENTICAL to original Slussen (no adjustments)
  6. TTX roundtrip — sort coverage tables (Uniscribe compliance)
  7. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Sources:
  Latin: Slussen OTF (OneDrive path preferred, fallback assets/fonts/slussen/)
  Thai:  Bai Jamjuree (local assets preferred, fallback system fonts)

Original Slussen metrics (preserved exactly):
  usWinAscent=1262  usWinDescent=334
  sTypoAscender=1074  sTypoDescender=-272  sTypoLineGap=166
  hhea ascent=1074  hhea descent=-272  hhea lineGap=166
  fsSelection: Regular/Medium/Semibold=0x00C0, Bold=0x00A0

Usage:
  python3 build_th_slussen.py                    # Build all 4 weights
  python3 build_th_slussen.py --weights Bold,Regular  # Build specific weights

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
SLUSSEN_ONEDRIVE = Path("/mnt/c/Users/OhYeaH/OneDrive/Documents/Slussen/Slussen")
SLUSSEN_LOCAL = ASSETS / "fonts" / "slussen"
BAI_LOCAL = ASSETS / "fonts" / "bai-jamjuree"
BAI_SYSTEM = Path.home() / ".local" / "share" / "fonts"
OUTPUT_DIR = ASSETS / "fonts" / "slussen-th"

# fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1

# Original Slussen vertical metrics (preserved exactly, never modified)
ORIG_WIN_ASCENT = 1262
ORIG_WIN_DESCENT = 334
ORIG_TYPO_ASC = 1074
ORIG_TYPO_DES = -272
ORIG_TYPO_GAP = 166
ORIG_HHEA_ASC = 1074
ORIG_HHEA_DES = -272
ORIG_HHEA_GAP = 166

# Weight mapping: output_name -> (slussen_file, bai_file)
WEIGHTS = {
    "Regular":  ("Slussen-Regular.otf",  "BaiJamjuree-Regular.ttf"),
    "Medium":   ("Slussen-Medium.otf",   "BaiJamjuree-Medium.ttf"),
    "Semibold": ("Slussen-Semibold.otf", "BaiJamjuree-SemiBold.ttf"),
    "Bold":     ("Slussen-Bold.otf",     "BaiJamjuree-Bold.ttf"),
}

# Per-weight metadata config (Windows RIBBI model)
# nameID1 = 'TH Slussen' for ALL weights (family name, never append weight)
# nameID16 = 'TH Slussen' (preferred family)
# nameID17 = weight name (preferred subfamily)
# nameID2 follows RIBBI: Regular/Bold/Italic/Bold Italic only
WEIGHT_CONFIG = {
    "Regular": {
        "nameID1": "TH Slussen",   "nameID2": "Regular",
        "nameID4": "TH Slussen",   "nameID6": "TH-Slussen-Regular",
        "nameID16": "TH Slussen",  "nameID17": "Regular",
        "fsSelection": REGULAR | USE_TYPO,  "macStyle": 0,
        "weightClass": 400, "panose_bWeight": 5,
    },
    "Medium": {
        # Non-RIBBI weight: nameID1 must be unique for Windows font picker
        "nameID1": "TH Slussen",   "nameID2": "Regular",
        "nameID4": "TH Slussen Medium", "nameID6": "TH-Slussen-Medium",
        "nameID16": "TH Slussen",  "nameID17": "Medium",
        "fsSelection": REGULAR | USE_TYPO,  "macStyle": 0,
        "weightClass": 500, "panose_bWeight": 6,
    },
    "Semibold": {
        "nameID1": "TH Slussen",   "nameID2": "Regular",
        "nameID4": "TH Slussen Semibold", "nameID6": "TH-Slussen-Semibold",
        "nameID16": "TH Slussen",  "nameID17": "Semibold",
        "fsSelection": REGULAR | USE_TYPO,  "macStyle": 0,
        "weightClass": 600, "panose_bWeight": 7,
    },
    "Bold": {
        "nameID1": "TH Slussen",   "nameID2": "Bold",
        "nameID4": "TH Slussen Bold", "nameID6": "TH-Slussen-Bold",
        "nameID16": "TH Slussen",  "nameID17": "Bold",
        "fsSelection": BOLD | USE_TYPO,    "macStyle": MAC_BOLD,
        "weightClass": 700, "panose_bWeight": 8,
    },
}


# ---------------------------------------------------------------------------
# Source finding
# ---------------------------------------------------------------------------

def find_slussen(filename):
    for d in [SLUSSEN_ONEDRIVE, SLUSSEN_LOCAL]:
        p = d / filename
        if p.exists():
            return p
    return None


def find_bai(filename):
    for d in [BAI_LOCAL, BAI_SYSTEM]:
        p = d / filename
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Step 1: Copy Thai glyphs (glyph by glyph, NOT bulk)
# ---------------------------------------------------------------------------

def _add_glyph_to_cff(slussen_font, bai_font, bai_glyph_name, target_name):
    """Add a single glyph from bai_font into slussen_font's CFF table."""
    cff = slussen_font["CFF "]
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

    glyph_order = slussen_font.getGlyphOrder()
    if target_name not in glyph_order:
        glyph_order.append(target_name)
        slussen_font.setGlyphOrder(glyph_order)

    hmtx = slussen_font["hmtx"]
    if bai_glyph_name in bai_font["hmtx"].metrics:
        hmtx.metrics[target_name] = bai_font["hmtx"].metrics[bai_glyph_name]

    return True


def copy_thai_glyphs(slussen_font, bai_font):
    """Copy Thai glyphs from BaiJamjuree into Slussen CFF font."""
    bai_cmap = bai_font.getBestCmap()
    if not bai_cmap:
        print("     !! No cmap in Bai Jamjuree")
        return 0

    # Cmap-mapped Thai codepoints (U+0E01-0E7F)
    thai_mappings = {
        cp: gn for cp, gn in bai_cmap.items() if 0x0E01 <= cp <= 0x0E7F
    }

    added = 0
    for cp, bai_gn in sorted(thai_mappings.items()):
        if _add_glyph_to_cff(slussen_font, bai_font, bai_gn, f"uni{cp:04X}"):
            added += 1

    # Update cmap for Thai range
    charstrings = slussen_font["CFF "].cff.topDictIndex[0].CharStrings
    for table in slussen_font["cmap"].tables:
        if hasattr(table, "cmap") and table.cmap is not None:
            for cp in thai_mappings:
                tn = f"uni{cp:04X}"
                if tn in charstrings.charStrings:
                    table.cmap[cp] = tn

    # Add ALL remaining Bai glyphs (variants + non-Thai needed for GPOS/GSUB integrity)
    extra = 0
    skip = {".notdef", ".null", "NULL", "nonmarkingreturn", "CR"}
    for gn in bai_font.getGlyphOrder():
        if gn in charstrings.charStrings or gn in skip:
            continue
        if _add_glyph_to_cff(slussen_font, bai_font, gn, gn):
            extra += 1

    print(f"     [1] Glyphs: {added} Thai cmap + {extra} extra (GPOS/GSUB)")
    return added + extra


# ---------------------------------------------------------------------------
# Step 2: Merge GPOS/GDEF/GSUB from BaiJamjuree (Thai mark lookups)
# ---------------------------------------------------------------------------

def merge_ot_tables(slussen_font, bai_font):
    """Replace GPOS/GDEF/GSUB with BaiJamjuree's tables (Thai shaping)."""
    if "GPOS" not in bai_font:
        print("     !! No GPOS in Bai Jamjuree — Thai marks will NOT work")
        return

    slussen_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
    gpos_n = len(bai_font["GPOS"].table.LookupList.Lookup)
    scripts = [sr.ScriptTag for sr in slussen_font["GPOS"].table.ScriptList.ScriptRecord]

    marks = 0
    if "GDEF" in bai_font:
        merged_gdef = copy_mod.deepcopy(bai_font["GDEF"])
        if "GDEF" in slussen_font and slussen_font["GDEF"].table.GlyphClassDef:
            for g, c in slussen_font["GDEF"].table.GlyphClassDef.classDefs.items():
                if g not in merged_gdef.table.GlyphClassDef.classDefs:
                    merged_gdef.table.GlyphClassDef.classDefs[g] = c
        merged_glyphs = set(slussen_font.getGlyphOrder())
        merged_gdef.table.GlyphClassDef.classDefs = {
            g: c for g, c in merged_gdef.table.GlyphClassDef.classDefs.items()
            if g in merged_glyphs
        }
        slussen_font["GDEF"] = merged_gdef
        marks = len([g for g, c in merged_gdef.table.GlyphClassDef.classDefs.items() if c == 3])

    gsub_n = 0
    if "GSUB" in bai_font:
        slussen_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
        gsub_n = len(bai_font["GSUB"].table.LookupList.Lookup)

    print(f"     [2] OT tables: GPOS={gpos_n} lookups, GDEF={marks} marks, "
          f"GSUB={gsub_n} lookups, scripts={','.join(scripts)}")


# ---------------------------------------------------------------------------
# Step 3: Metadata (RIBBI naming + OS/2 + CFF fontName)
# ---------------------------------------------------------------------------

def _set_name(nt, nid, val, pid=3, peid=1, lid=0x0409):
    if val is None:
        nt.removeNames(nameID=nid, platformID=pid, platEncID=peid, langID=lid)
        return
    nt.setName(val, nid, pid, peid, lid)


def apply_metadata(font, weight_name):
    """Apply TH Slussen naming, OS/2 version/fsSelection, CFF fontName."""
    cfg = WEIGHT_CONFIG[weight_name]
    nt = font["name"]

    # Name table — Windows (pid=3) and Mac (pid=1)
    for nid in [1, 2, 4, 6, 16, 17]:
        key = f"nameID{nid}"
        _set_name(nt, nid, cfg[key])
        _set_name(nt, nid, cfg[key], pid=1, peid=0, lid=0)

    uid = f"THSlussen-{weight_name}"
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
    if hasattr(os2, "panose") and os2.panose:
        os2.panose.bWeight = cfg["panose_bWeight"]

    # head.macStyle
    font["head"].macStyle = cfg["macStyle"]

    # CFF fontName
    if "CFF " in font:
        font["CFF "].cff.fontNames[0] = cfg["nameID6"]

    print(f"     [3] Metadata: ID1='{cfg['nameID1']}' ID2='{cfg['nameID2']}' "
          f"fsSel=0x{cfg['fsSelection']:04X} wt={cfg['weightClass']}")


# ---------------------------------------------------------------------------
# Step 4: OS/2 Thai Unicode Range + CodePage bits
# ---------------------------------------------------------------------------

def set_thai_bits(font):
    """Set OS/2 bit 24 (Thai Unicode Range) and bit 16 (CP874 Thai CodePage)."""
    os2 = font["OS/2"]
    os2.ulUnicodeRange1 |= (1 << 24)   # bit 24 = Thai
    os2.ulCodePageRange1 |= (1 << 16)  # bit 16 = CP874 (Thai)
    print(f"     [4] Thai bits: ulUR1 bit24=True, ulCPR1 bit16=True")


# ---------------------------------------------------------------------------
# Step 5: Preserve vertical metrics — keep IDENTICAL to original Slussen
# ---------------------------------------------------------------------------

def preserve_vertical_metrics(font):
    """Restore vertical metrics to original Slussen values (Thai clipping is acceptable)."""
    os2 = font["OS/2"]
    hhea = font["hhea"]

    # Restore exactly — never adjust for Thai
    os2.usWinAscent = ORIG_WIN_ASCENT
    os2.usWinDescent = ORIG_WIN_DESCENT
    os2.sTypoAscender = ORIG_TYPO_ASC
    os2.sTypoDescender = ORIG_TYPO_DES
    os2.sTypoLineGap = ORIG_TYPO_GAP
    hhea.ascent = ORIG_HHEA_ASC
    hhea.descent = ORIG_HHEA_DES
    hhea.lineGap = ORIG_HHEA_GAP

    print(f"     [5] Metrics: winAsc={ORIG_WIN_ASCENT} winDes={ORIG_WIN_DESCENT} "
          f"sTypo={ORIG_TYPO_ASC}/{ORIG_TYPO_DES}/{ORIG_TYPO_GAP} "
          f"hhea={ORIG_HHEA_ASC}/{ORIG_HHEA_DES}/{ORIG_HHEA_GAP} (original Slussen, preserved)")


# ---------------------------------------------------------------------------
# Step 6: TTX roundtrip (sort coverage tables for Uniscribe)
# ---------------------------------------------------------------------------

def ttx_roundtrip(font_path):
    """Save/reload via TTX to sort coverage table glyph lists (Uniscribe requirement)."""
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
# Step 7: Validate — full verification report
# ---------------------------------------------------------------------------

def verify_font(weight_name, slussen_file):
    """Run full validation and print report. Returns True if all checks pass."""
    cfg = WEIGHT_CONFIG[weight_name]
    path = OUTPUT_DIR / f"TH-Slussen-{weight_name}.otf"
    if not path.exists():
        print(f"     [7] FAIL: Output file not found: {path}")
        return False

    font = TTFont(str(path))
    cmap = font.getBestCmap()
    os2 = font["OS/2"]
    hhea = font["hhea"]
    nt = font["name"]
    failures = []
    checks = []

    # 1. Latin outlines identical (RecordingPen compare: H, a, o)
    slussen_path = find_slussen(slussen_file)
    if slussen_path:
        slussen_src = TTFont(str(slussen_path))
        gs_m = font.getGlyphSet()
        gs_s = slussen_src.getGlyphSet()
        sc = slussen_src.getBestCmap()
        latin_ok = True
        for cp, name in [(0x48, "H"), (0x61, "a"), (0x6F, "o")]:
            mg = cmap.get(cp)
            ag = sc.get(cp) if sc else None
            if mg and ag and mg in gs_m and ag in gs_s:
                pm, ps = RecordingPen(), RecordingPen()
                gs_m[mg].draw(pm)
                gs_s[ag].draw(ps)
                ok = pm.value == ps.value
                if not ok:
                    latin_ok = False
                    failures.append(f"Latin '{name}' CHANGED")
        checks.append(f"Latin={'OK' if latin_ok else 'FAIL'}")
    else:
        checks.append("Latin=SKIP(src not found)")

    # 2. usWinAscent/Descent exact
    win_ok = (os2.usWinAscent == ORIG_WIN_ASCENT and os2.usWinDescent == ORIG_WIN_DESCENT)
    checks.append(f"winAsc={os2.usWinAscent}({'OK' if os2.usWinAscent == ORIG_WIN_ASCENT else 'FAIL'})")
    checks.append(f"winDes={os2.usWinDescent}({'OK' if os2.usWinDescent == ORIG_WIN_DESCENT else 'FAIL'})")
    if not win_ok:
        failures.append(f"usWinAscent/Descent mismatch: {os2.usWinAscent}/{os2.usWinDescent}")

    # 3. hhea ascent/descent exact
    hhea_ok = (hhea.ascent == ORIG_HHEA_ASC and hhea.descent == ORIG_HHEA_DES)
    checks.append(f"hhea={hhea.ascent}/{hhea.descent}({'OK' if hhea_ok else 'FAIL'})")
    if not hhea_ok:
        failures.append(f"hhea mismatch: {hhea.ascent}/{hhea.descent}")

    # 4. sTypo exact
    typo_ok = (os2.sTypoAscender == ORIG_TYPO_ASC and
               os2.sTypoDescender == ORIG_TYPO_DES and
               os2.sTypoLineGap == ORIG_TYPO_GAP)
    checks.append(f"sTypo={os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap}"
                  f"({'OK' if typo_ok else 'FAIL'})")
    if not typo_ok:
        failures.append(f"sTypo mismatch")

    # 5. nameID 1 = 'TH Slussen' (no weight appended)
    n1 = nt.getName(1, 3, 1, 0x0409)
    n1t = n1.toUnicode() if n1 else "?"
    name_ok = n1t == "TH Slussen"
    checks.append(f"nameID1='{n1t}'({'OK' if name_ok else 'FAIL'})")
    if not name_ok:
        failures.append(f"nameID1 wrong: '{n1t}'")

    # 6. Thai glyphs present (U+0E01 กอไก่)
    thai_count = sum(1 for cp in cmap if 0x0E01 <= cp <= 0x0E7F)
    ko_kai = 0x0E01 in cmap
    checks.append(f"Thai={thai_count}({'OK' if ko_kai else 'FAIL:no-U+0E01'})")
    if not ko_kai:
        failures.append("U+0E01 (กอไก่) missing from cmap")

    # 7. GPOS has Thai mark lookups
    gpos_n = len(font["GPOS"].table.LookupList.Lookup) if "GPOS" in font else 0
    marks = 0
    if "GDEF" in font and font["GDEF"].table.GlyphClassDef:
        marks = len([g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3])
    gpos_ok = gpos_n > 0
    checks.append(f"GPOS={gpos_n}({'OK' if gpos_ok else 'FAIL'})")
    checks.append(f"marks={marks}")
    if not gpos_ok:
        failures.append("GPOS missing Thai mark lookups")

    # OS/2 Thai bits
    thai_ur = bool(os2.ulUnicodeRange1 & (1 << 24))
    thai_cp = bool(os2.ulCodePageRange1 & (1 << 16))
    bits_ok = thai_ur and thai_cp
    checks.append(f"ThaiBits={'OK' if bits_ok else 'FAIL'}")
    if not bits_ok:
        failures.append(f"Thai OS/2 bits missing: UR={thai_ur} CP={thai_cp}")

    status = "PASS" if not failures else "FAIL"
    print(f"     [7] {status}: {' | '.join(checks)}")
    if failures:
        for f in failures:
            print(f"         !! {f}")

    return not failures


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build_font(weight_name, slussen_file, bai_file):
    """Build a single TH-Slussen weight."""
    print(f"\n  === {weight_name} ===")

    slussen_path = find_slussen(slussen_file)
    bai_path = find_bai(bai_file)

    if not slussen_path:
        print(f"     !! Slussen not found: {slussen_file}")
        return False
    if not bai_path:
        print(f"     !! Bai Jamjuree not found: {bai_file}")
        return False

    print(f"     Latin: {slussen_path}")
    print(f"     Thai:  {bai_path}")

    slussen = TTFont(str(slussen_path))
    bai = TTFont(str(bai_path))

    if "CFF " not in slussen:
        print(f"     !! Slussen is not CFF format — cannot merge CFF glyphs")
        return False

    output_path = OUTPUT_DIR / f"TH-Slussen-{weight_name}.otf"

    # Step 1: Copy Thai glyphs (glyph by glyph)
    copy_thai_glyphs(slussen, bai)

    # Step 2: Merge GPOS/GDEF/GSUB (Thai mark positioning)
    merge_ot_tables(slussen, bai)

    # Step 3: Metadata (naming, fsSelection, CFF fontName)
    apply_metadata(slussen, weight_name)

    # Step 4: Thai OS/2 bits
    set_thai_bits(slussen)

    # Step 5: Preserve vertical metrics (keep original Slussen exact)
    preserve_vertical_metrics(slussen)

    # Save before TTX roundtrip
    slussen.save(str(output_path))

    # Step 6: TTX roundtrip (sort coverage tables)
    ttx_roundtrip(output_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"     Saved: {output_path.name} ({size_kb:.0f} KB)")

    # Step 7: Verify
    passed = verify_font(weight_name, slussen_file)

    return passed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build TH-Slussen font family")
    parser.add_argument("--weights", default=None,
                        help="Comma-separated weights: Regular,Medium,Semibold,Bold (default: all)")
    args = parser.parse_args()

    weights = WEIGHTS
    if args.weights:
        selected = [w.strip() for w in args.weights.split(",")]
        weights = {k: v for k, v in WEIGHTS.items() if k in selected}

    print("\n" + "=" * 70)
    print("  TH-SLUSSEN BUILD PIPELINE")
    print("  Slussen (Latin) + Bai Jamjuree (Thai) = TH Slussen")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    results = {}
    for wn, (sf, bf) in weights.items():
        ok = build_font(wn, sf, bf)
        results[wn] = ok
        if ok:
            success += 1

    total = len(weights)
    print(f"\n{'=' * 70}")
    status = "PASS" if success == total else "PARTIAL" if success > 0 else "FAIL"
    print(f"  {status}: {success}/{total} fonts built")
    print(f"  Output: {OUTPUT_DIR}")
    for wn, ok in results.items():
        print(f"    {'OK' if ok else 'FAIL'}: TH-Slussen-{wn}.otf")
    print(f"{'=' * 70}\n")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
