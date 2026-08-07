#!/usr/bin/env python3
"""
Build TH-Aeonik font family — unified pipeline.

Merges Aeonik (Latin) + Bai Jamjuree (Thai) into TH-Aeonik with complete
OpenType support for Thai text shaping on Windows.

The family spans a ten-step weight scale:

    Air 100  Thin 200  Light 300  Book 350  Regular 400
    Medium 500  SemiBold 600  Bold 700  ExtraBold 800  Black 900

Neither source family ships all ten, so the missing masters are produced
first by generate_masters.py and picked up here from the *-ext directories.
Run that script before this one.

Pipeline steps:
  1. Copy Thai glyphs + variants from Bai Jamjuree (CFF charstrings)
  2. Merge GPOS/GDEF/GSUB tables from Bai Jamjuree (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2 v4, fsType, panose, CFF fontName
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Set vertical metrics — measured per weight to prevent Thai clipping
  6. TTX roundtrip — sort coverage tables (Uniscribe compliance)
  7. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Usage:
  python3 build_th_aeonik.py                       # all 20 faces
  python3 build_th_aeonik.py --upright-only        # 10 uprights
  python3 build_th_aeonik.py --weights Bold,Light

Requires: fontTools >= 4.0
"""

import copy as copy_mod
import os
import sys
import warnings
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent
ASSETS = SCRIPT_DIR.parent / "assets"

AEONIK = ASSETS / "fonts" / "aeonik"
AEONIK_EXT = ASSETS / "fonts" / "aeonik-ext"
BAI = ASSETS / "fonts" / "bai-jamjuree"
BAI_EXT = ASSETS / "fonts" / "bai-jamjuree-ext"
OUTPUT_DIR = ASSETS / "fonts" / "aeonik-th"

FAMILY = "TH Aeonik"

# fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1

# The ten-step scale. For each step: the weight class, the PANOSE weight
# code, and which master supplies each script. `gen` marks a master that
# generate_masters.py produces rather than one the source family ships.
#
# The Latin runs the full 100-900 on real or interpolated Aeonik masters. The
# Thai cannot: Bai Jamjuree ships 200-700 and self-intersects when pushed
# outside that range, so Air borrows ExtraLight and the two heaviest steps use
# damped masters (drawn ~710/720). The Thai therefore flattens at both ends
# while the Latin keeps going -- a limit of the source family. See THAI_PLAN
# in generate_masters.py for the measurements behind those cutoffs.
#
#   style        wght  panose  latin master     gen    thai master      gen
SCALE = [
    ("Air",       100,  2,     "Air",           False, "ExtraLight",    False),
    ("Thin",      200,  3,     "Thin",          False, "ExtraLight",    False),
    ("Light",     300,  4,     "Light",         False, "Light",         False),
    ("Book",      350,  5,     "Book",          True,  "Book",          True),
    ("Regular",   400,  5,     "Regular",       False, "Regular",       False),
    ("Medium",    500,  6,     "Medium",        False, "Medium",        False),
    ("SemiBold",  600,  7,     "SemiBold",      True,  "SemiBold",      False),
    ("Bold",      700,  8,     "Bold",          False, "Bold",          False),
    ("ExtraBold", 800,  9,     "ExtraBold",     True,  "ExtraBold",     True),
    ("Black",     900,  10,    "Black",         False, "Black",         True),
]

# Only these two styles can occupy a RIBBI slot; every other weight needs its
# own nameID1 so legacy Windows pickers (Word's font menu) can reach it.
RIBBI = {"Regular", "Bold"}

# Minimum Windows clipping box. These are the family's production floors --
# verify-fonts.py enforces the ascent one -- and they exist because a stacked
# Thai cluster rises above the tallest single glyph, so no per-glyph
# measurement can discover the space it needs.
THAI_ASCENT_FLOOR = 1550
THAI_DESCENT_FLOOR = 561


def thai_filename(style, italic):
    """Bai Jamjuree names its upright roman 'Regular' but its italic 'Italic'."""
    if not italic:
        return f"BaiJamjuree-{style}.ttf"
    return "BaiJamjuree-Italic.ttf" if style == "Regular" else f"BaiJamjuree-{style}Italic.ttf"


def build_weight_table(upright_only=False):
    """Expand SCALE into one entry per face, with sources and metadata."""
    table = {}
    for style, wght, panose, latin, latin_gen, thai, thai_gen in SCALE:
        for italic in ([False] if upright_only else [False, True]):
            key = style + ("Italic" if italic else "")
            display = style + (" Italic" if italic else "")

            latin_dir = AEONIK_EXT if latin_gen else AEONIK
            thai_dir = BAI_EXT if thai_gen else BAI
            latin_path = latin_dir / (f"Aeonik-{latin}Italic.otf" if italic
                                      else f"Aeonik-{latin}.otf")
            thai_path = thai_dir / thai_filename(thai, italic)

            # RIBBI grouping: Regular and Bold share the base family name and
            # carry the real subfamily; all other weights become their own
            # family with a Regular/Italic subfamily.
            if style in RIBBI:
                name1 = FAMILY
                if style == "Bold":
                    name2 = "Bold Italic" if italic else "Bold"
                else:
                    name2 = "Italic" if italic else "Regular"
            else:
                name1 = f"{FAMILY} {style}"
                name2 = "Italic" if italic else "Regular"

            if style == "Regular" and not italic:
                name4 = FAMILY
            else:
                name4 = f"{FAMILY} {display}"

            fs = USE_TYPO
            fs |= ITALIC if italic else 0
            if style == "Bold":
                fs |= BOLD
            elif not italic:
                fs |= REGULAR
            mac = (MAC_BOLD if style == "Bold" else 0) | (MAC_ITALIC if italic else 0)

            table[key] = {
                "latin_path": latin_path,
                "thai_path": thai_path,
                "latin_generated": latin_gen,
                "thai_generated": thai_gen,
                "nameID1": name1,
                "nameID2": name2,
                "nameID4": name4,
                "nameID6": f"TH-Aeonik-{key}",
                "nameID16": FAMILY,
                "nameID17": display,
                "fsSelection": fs,
                "macStyle": mac,
                "weightClass": wght,
                "panose_bWeight": panose,
            }
    return table


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


def apply_metadata(font, key, cfg):
    nt = font["name"]

    # Name table (Windows + Mac)
    for nid in [1, 2, 4, 6, 16, 17]:
        value = cfg[f"nameID{nid}"]
        _set_name(nt, nid, value)
        _set_name(nt, nid, value, pid=1, peid=0, lid=0)

    uid = f"THAeonik-{key}"
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
          f"ID17='{cfg['nameID17']}' fsSel=0x{cfg['fsSelection']:04X} "
          f"wt={cfg['weightClass']}")


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

def measure_ink(font):
    """Extreme yMin/yMax across every glyph in the merged font."""
    glyph_set = font.getGlyphSet()
    y_min = y_max = 0
    for name in font.getGlyphOrder():
        if name not in glyph_set:
            continue
        pen = BoundsPen(glyph_set)
        try:
            glyph_set[name].draw(pen)
        except Exception:
            continue
        if pen.bounds is None:
            continue
        y_min = min(y_min, pen.bounds[1])
        y_max = max(y_max, pen.bounds[3])
    return y_min, y_max


def set_vertical_metrics(font):
    """Size the Windows clipping box to hold stacked Thai, per weight.

    Aeonik's own sTypo* and hhea values are left untouched so line spacing
    stays identical to the Latin original (USE_TYPO_METRICS is set, so those
    are what layout actually uses). Only usWinAscent/usWinDescent move, since
    those are what Windows clips against.

    Both a floor and a measurement are needed. Measured ink alone is not
    enough: GPOS stacks a tone mark on top of a vowel, so a cluster reaches
    higher than any single glyph's bbox, and the floors carry the headroom
    for that. The floors alone are not enough either -- the heaviest weights
    push descenders past the historic 561, and Black measures -629 -- so the
    measurement covers what the constants cannot anticipate.
    """
    os2 = font["OS/2"]
    y_min, y_max = measure_ink(font)

    win_asc = max(THAI_ASCENT_FLOOR, int(round(y_max)))
    win_desc = max(THAI_DESCENT_FLOOR, int(round(-y_min)))
    by_ink = win_asc > THAI_ASCENT_FLOOR or win_desc > THAI_DESCENT_FLOOR
    os2.usWinAscent = win_asc
    os2.usWinDescent = win_desc

    print(f"     [5] Metrics: ink y=[{y_min:.0f},{y_max:.0f}] -> "
          f"winAsc={win_asc} winDes={win_desc} "
          f"{'(raised above floor by ink)' if by_ink else '(at floor)'}; "
          f"sTypo={os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap} kept")


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

def verify_font(key, cfg):
    path = OUTPUT_DIR / f"TH-Aeonik-{key}.otf"
    if not path.exists():
        return False

    font = TTFont(str(path))
    cmap = font.getBestCmap()
    os2 = font["OS/2"]
    checks = []
    ok = True

    # Thai cmap
    thai = {cp: g for cp, g in cmap.items() if 0x0E00 <= cp <= 0x0E7F}
    checks.append(f"Thai={len(thai)}")
    if len(thai) < 80:
        ok = False
    if 0x0E00 in thai:
        checks.append("U+0E00=YES!!")
        ok = False
    if any(0x0E5C <= cp <= 0x0E7F for cp in thai):
        checks.append("spurious!!")
        ok = False

    # Latin fidelity against the Latin master this face was built from
    latin_path = cfg["latin_path"]
    if latin_path.exists():
        aeonik_src = TTFont(str(latin_path))
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
        if pct < 99:
            ok = False

    # GPOS/GDEF
    gpos_n = len(font["GPOS"].table.LookupList.Lookup) if "GPOS" in font else 0
    marks = 0
    if "GDEF" in font and font["GDEF"].table.GlyphClassDef:
        marks = len([g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3])
    checks.append(f"GPOS={gpos_n}")
    checks.append(f"marks={marks}")
    if gpos_n == 0 or marks == 0:
        ok = False

    # OS/2 bits
    thai_ur = bool(os2.ulUnicodeRange1 & (1 << 24))
    thai_cp = bool(os2.ulCodePageRange1 & (1 << 16))
    checks.append(f"ThaiBits={'OK' if thai_ur and thai_cp else 'FAIL'}")
    if not (thai_ur and thai_cp):
        ok = False

    # Weight + naming
    checks.append(f"wt={os2.usWeightClass}")
    if os2.usWeightClass != cfg["weightClass"]:
        ok = False
    n1 = font["name"].getName(1, 3, 1, 0x0409)
    n2 = font["name"].getName(2, 3, 1, 0x0409)
    n1t = n1.toUnicode() if n1 else "?"
    n2t = n2.toUnicode() if n2 else "?"
    checks.append(f"'{n1t}/{n2t}'")

    # Clipping box must contain the ink
    y_min, y_max = measure_ink(font)
    if os2.usWinAscent < y_max - 1 or os2.usWinDescent < -y_min - 1:
        checks.append("CLIPS!!")
        ok = False

    print(f"     [7] Verify: {' | '.join(checks)} -> {'PASS' if ok else 'FAIL'}")
    return ok


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------

def build_font(key, cfg):
    print(f"\n  === {key} ({cfg['weightClass']}) ===")

    latin_path, thai_path = cfg["latin_path"], cfg["thai_path"]
    if not latin_path.exists():
        print(f"     !! Latin master not found: {latin_path}")
        return False
    if not thai_path.exists():
        print(f"     !! Thai master not found: {thai_path}")
        return False

    tag_l = " (generated)" if cfg["latin_generated"] else ""
    tag_t = " (generated)" if cfg["thai_generated"] else ""
    print(f"     Latin: {latin_path.name}{tag_l}")
    print(f"     Thai:  {thai_path.name}{tag_t}")

    aeonik = TTFont(str(latin_path))
    bai = TTFont(str(thai_path))

    if "CFF " not in aeonik:
        print(f"     !! Latin master is not CFF format")
        return False

    output_path = OUTPUT_DIR / f"TH-Aeonik-{key}.otf"

    copy_thai_glyphs(aeonik, bai)
    merge_ot_tables(aeonik, bai)
    apply_metadata(aeonik, key, cfg)
    set_thai_bits(aeonik)
    set_vertical_metrics(aeonik)

    aeonik.save(str(output_path))
    ttx_roundtrip(output_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"     Saved: {output_path.name} ({size_kb:.0f} KB)")

    return verify_font(key, cfg)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build TH-Aeonik font family")
    parser.add_argument("--weights", default=None,
                        help="Comma-separated face keys (default: all)")
    parser.add_argument("--upright-only", action="store_true",
                        help="skip italics")
    args = parser.parse_args()

    table = build_weight_table(upright_only=args.upright_only)
    if args.weights:
        selected = [w.strip() for w in args.weights.split(",")]
        table = {k: v for k, v in table.items() if k in selected}

    print("\n" + "=" * 70)
    print("  TH-AEONIK BUILD PIPELINE")
    print("  Aeonik (Latin) + Bai Jamjuree (Thai) = TH Aeonik")
    print(f"  {len(table)} faces across a ten-step weight scale")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = []
    for key, cfg in table.items():
        if build_font(key, cfg):
            success += 1
        else:
            failed.append(key)

    total = len(table)
    print(f"\n{'=' * 70}")
    status = "PASS" if success == total else "FAIL"
    print(f"  {status}: {success}/{total} faces built and verified")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'=' * 70}\n")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
