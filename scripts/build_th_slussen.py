#!/usr/bin/env python3
"""
Build TH-Slussen font family — unified pipeline.

Merges Slussen (Latin) + Bai Jamjuree (Thai) into TH-Slussen with complete
OpenType support for Thai text shaping on Windows.

Pipeline steps:
  1. Copy Thai glyphs + variants from Bai Jamjuree (CFF charstrings via T2CharStringPen)
  2. Union GPOS/GDEF/GSUB from Bai Jamjuree onto Slussen's own (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2, CFF fontName
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Vertical metrics — Slussen's line box preserved, clipping box widened for Thai
  6. Sort GSUB/GPOS Coverage tables + clean Mac cmap (Uniscribe compliance)
  7. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Sources:
  Latin: Slussen OTF (OneDrive path preferred, fallback assets/fonts/slussen/)
  Thai:  Bai Jamjuree (local assets preferred, fallback system fonts)

Slussen line box (preserved exactly — do not retune, it sets document line spacing):
  sTypoAscender=1074  sTypoDescender=-272  sTypoLineGap=166
  hhea ascent=1074  hhea descent=-272  hhea lineGap=166
  fsSelection: Regular/Medium/Semibold=0x00C0, Bold=0x00A0 (USE_TYPO_METRICS on)

Acceptance test: scripts/compare_th_slussen.py — the merge is only correct if it
is invisible (Thai renders as Bai Jamjuree, Latin renders as Slussen).

Usage:
  python3 build_th_slussen.py                    # Build all 4 weights
  python3 build_th_slussen.py --weights Bold,Regular  # Build specific weights

Requires: fontTools >= 4.0
"""

import copy as copy_mod
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

# Vertical metrics.
#
# The line box stays exactly as Slussen shipped it: hhea and sTypo already agree
# with each other, USE_TYPO_METRICS is set on every weight, and these numbers
# decide line spacing in every existing document. They are not retuned.
#
# usWinAscent/usWinDescent are a different thing — the GDI *clipping* box, not
# the line box. Merged ink reaches +1255/-561 (Slussen tops out at +1255, Bai
# Jamjuree bottoms out at -561), so the shipped usWinDescent of 334 cut the
# descenders off Thai below-vowels on Windows. Widened to clear the ink; because
# USE_TYPO_METRICS is on, consumers still take spacing from sTypo, so this
# changes what is visible without changing how far apart the lines sit.
ORIG_TYPO_ASC = 1074
ORIG_TYPO_DES = -272
ORIG_TYPO_GAP = 166
ORIG_HHEA_ASC = 1074
ORIG_HHEA_DES = -272
ORIG_HHEA_GAP = 166

WIN_ASCENT = 1262    # clears merged ink top    (+1255)
WIN_DESCENT = 570    # clears merged ink bottom (-561); was 334, which clipped

# Weight mapping: output_name -> (slussen_file, bai_file)
WEIGHTS = {
    "Regular":  ("Slussen-Regular.otf",  "BaiJamjuree-Regular.ttf"),
    "Medium":   ("Slussen-Medium.otf",   "BaiJamjuree-Medium.ttf"),
    "SemiBold": ("Slussen-Semibold.otf", "BaiJamjuree-SemiBold.ttf"),
    "Bold":     ("Slussen-Bold.otf",     "BaiJamjuree-Bold.ttf"),
}

# Per-weight metadata config (Windows RIBBI model).
#
# nameID2 may only be Regular / Bold / Italic / Bold Italic. A family sharing
# one nameID1 therefore holds at most those four faces. Medium and SemiBold do
# not fit, so each takes its own unique nameID1 — otherwise Regular, Medium and
# SemiBold would all announce themselves as 'TH Slussen' + 'Regular' and
# Windows could not tell them apart, leaving only one of the three selectable.
# nameID16/17 (preferred family / preferred subfamily) put all four back
# together as one 'TH Slussen' family in applications that read them.
WEIGHT_CONFIG = {
    "Regular": {
        "nameID1": "TH Slussen",   "nameID2": "Regular",
        "nameID4": "TH Slussen",   "nameID6": "TH-Slussen-Regular",
        "nameID16": "TH Slussen",  "nameID17": "Regular",
        "fsSelection": REGULAR | USE_TYPO,  "macStyle": 0,
        "weightClass": 400, "panose_bWeight": 5,
    },
    "Medium": {
        # Non-RIBBI weight: nameID1 must be unique for the Windows font picker
        "nameID1": "TH Slussen Medium", "nameID2": "Regular",
        "nameID4": "TH Slussen Medium", "nameID6": "TH-Slussen-Medium",
        "nameID16": "TH Slussen",  "nameID17": "Medium",
        "fsSelection": REGULAR | USE_TYPO,  "macStyle": 0,
        "weightClass": 500, "panose_bWeight": 6,
    },
    "SemiBold": {
        # Non-RIBBI weight: nameID1 must be unique for the Windows font picker
        "nameID1": "TH Slussen SemiBold", "nameID2": "Regular",
        "nameID4": "TH Slussen SemiBold", "nameID6": "TH-Slussen-SemiBold",
        "nameID16": "TH Slussen",  "nameID17": "SemiBold",
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
    # T2CharStringPen encodes the width operand assuming nominalWidthX == 0.
    # This charstring adopts Slussen's Private DICT below, so pre-compensate:
    # the operand must be (width - nominalWidthX) for the rasteriser to decode
    # the intended advance. Without this every Thai glyph decodes nominalWidthX
    # units too wide (616 Regular / 632 Bold / ...) in any consumer that trusts
    # charstring widths over hmtx — which Microsoft Print to PDF does. Word
    # looks fine because Word lays out from hmtx; the printed PDF does not.
    priv = top_dict.Private
    pen = T2CharStringPen(bai_glyph.width - priv.nominalWidthX, bai_glyph_set)
    bai_glyph.draw(pen)
    charstring = pen.getCharString()

    charstring.private = priv
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

def _shift_nested_lookups(lookup, offset):
    """Lookups can invoke other lookups by index; those indices move too."""
    for sub in lookup.SubTable or []:
        for field in ("SubstLookupRecord", "PosLookupRecord"):
            for rec in getattr(sub, field, None) or []:
                rec.LookupListIndex += offset
        for rule_set_field in ("ChainSubRuleSet", "SubRuleSet",
                               "ChainPosRuleSet", "PosRuleSet",
                               "ChainSubClassSet", "SubClassSet",
                               "ChainPosClassSet", "PosClassSet"):
            for rule_set in getattr(sub, rule_set_field, None) or []:
                if rule_set is None:
                    continue
                for attr in ("ChainSubRule", "SubRule", "ChainPosRule", "PosRule",
                             "ChainSubClassRule", "SubClassRule",
                             "ChainPosClassRule", "PosClassRule"):
                    for rule in getattr(rule_set, attr, None) or []:
                        for field in ("SubstLookupRecord", "PosLookupRecord"):
                            for rec in getattr(rule, field, None) or []:
                                rec.LookupListIndex += offset


def _union_ot(base_table, add_table, take_scripts):
    """Append add_table's lookups/features, then adopt only `take_scripts`.

    Slussen keeps its own glyph IDs (Thai is appended after them), so its
    GSUB/GPOS stay valid verbatim. Bai Jamjuree's Thai lookups are grafted on
    top, and only the Thai script record is taken — 'latn' and 'DFLT' stay
    Slussen's, so Latin kerning and ligatures survive the merge.

    The previous build assigned Bai's tables over Slussen's, which silently
    discarded 43 GSUB and 7 GPOS lookups: Latin glyphs stayed Slussen's while
    every kerning pair and ligature applied to them became Bai Jamjuree's.
    """
    base, add = base_table.table, add_table.table
    offset = len(base.LookupList.Lookup)

    for lk in add.LookupList.Lookup:
        new = copy_mod.deepcopy(lk)
        _shift_nested_lookups(new, offset)
        base.LookupList.Lookup.append(new)
    base.LookupList.LookupCount = len(base.LookupList.Lookup)

    feature_map = {}
    for i, frec in enumerate(add.FeatureList.FeatureRecord):
        new = copy_mod.deepcopy(frec)
        new.Feature.LookupListIndex = [x + offset
                                       for x in new.Feature.LookupListIndex]
        new.Feature.LookupCount = len(new.Feature.LookupListIndex)
        base.FeatureList.FeatureRecord.append(new)
        feature_map[i] = len(base.FeatureList.FeatureRecord) - 1
    base.FeatureList.FeatureCount = len(base.FeatureList.FeatureRecord)

    def remap(langsys):
        if langsys is None:
            return
        langsys.FeatureIndex = [feature_map[i] for i in langsys.FeatureIndex
                                if i in feature_map]
        langsys.FeatureCount = len(langsys.FeatureIndex)
        if getattr(langsys, "ReqFeatureIndex", 0xFFFF) != 0xFFFF:
            langsys.ReqFeatureIndex = feature_map.get(
                langsys.ReqFeatureIndex, 0xFFFF)

    records = base.FeatureList.FeatureRecord

    def absorb(dst, src):
        """Union src's (already remapped) features into dst, merging by tag.

        A LangSys must not list the same feature tag twice — consumers take the
        first and ignore the rest. Slussen ships no 'thai' script today, so this
        path is unused for it; it is kept because it is the correct behaviour
        and the Aeonik build hit exactly this case on its italic weights.
        """
        if dst is None or src is None:
            return
        by_tag = {records[i].FeatureTag: i for i in reversed(dst.FeatureIndex)}
        for i in src.FeatureIndex:
            tag = records[i].FeatureTag
            if tag not in by_tag:
                dst.FeatureIndex.append(i)
                by_tag[tag] = i
                continue
            # Clone rather than mutate: the existing record is likely shared
            # with the 'latn'/'DFLT' scripts, which must not gain Thai lookups.
            old = records[by_tag[tag]]
            merged = copy_mod.deepcopy(old)
            seen = set(merged.Feature.LookupListIndex)
            merged.Feature.LookupListIndex += [
                x for x in records[i].Feature.LookupListIndex if x not in seen]
            merged.Feature.LookupListIndex.sort()
            merged.Feature.LookupCount = len(merged.Feature.LookupListIndex)
            records.append(merged)
            new_idx = len(records) - 1
            dst.FeatureIndex = [new_idx if x == by_tag[tag] else x
                                for x in dst.FeatureIndex]
            by_tag[tag] = new_idx
        dst.FeatureIndex.sort()
        dst.FeatureCount = len(dst.FeatureIndex)
        base.FeatureList.FeatureCount = len(records)
        if getattr(dst, "ReqFeatureIndex", 0xFFFF) == 0xFFFF:
            dst.ReqFeatureIndex = getattr(src, "ReqFeatureIndex", 0xFFFF)

    existing = {sr.ScriptTag: sr for sr in base.ScriptList.ScriptRecord}
    for srec in add.ScriptList.ScriptRecord:
        if srec.ScriptTag not in take_scripts:
            continue
        new = copy_mod.deepcopy(srec)
        remap(new.Script.DefaultLangSys)
        for lsr in new.Script.LangSysRecord or []:
            remap(lsr.LangSys)

        prior = existing.get(srec.ScriptTag)
        if prior is None:
            base.ScriptList.ScriptRecord.append(new)
            continue
        if prior.Script.DefaultLangSys is None:
            prior.Script.DefaultLangSys = new.Script.DefaultLangSys
        else:
            absorb(prior.Script.DefaultLangSys, new.Script.DefaultLangSys)
        by_tag = {l.LangSysTag: l for l in prior.Script.LangSysRecord or []}
        for lsr in new.Script.LangSysRecord or []:
            if lsr.LangSysTag in by_tag:
                absorb(by_tag[lsr.LangSysTag].LangSys, lsr.LangSys)
            else:
                prior.Script.LangSysRecord = (prior.Script.LangSysRecord or []) + [lsr]
        if prior.Script.LangSysRecord:
            prior.Script.LangSysRecord.sort(key=lambda l: l.LangSysTag)
            prior.Script.LangSysCount = len(prior.Script.LangSysRecord)
    # ScriptRecords must be sorted by tag
    base.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
    base.ScriptList.ScriptCount = len(base.ScriptList.ScriptRecord)


def merge_ot_tables(slussen_font, bai_font):
    """Graft Bai Jamjuree's Thai lookups onto Slussen's own GPOS/GDEF/GSUB."""
    if "GPOS" not in bai_font:
        print("     !! No GPOS in Bai Jamjuree — Thai marks will NOT work")
        return

    if "GPOS" in slussen_font:
        _union_ot(slussen_font["GPOS"], bai_font["GPOS"], {"thai"})
    else:
        slussen_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
    gpos_n = len(slussen_font["GPOS"].table.LookupList.Lookup)
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
        if "GSUB" in slussen_font:
            _union_ot(slussen_font["GSUB"], bai_font["GSUB"], {"thai"})
        else:
            slussen_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
        gsub_n = len(slussen_font["GSUB"].table.LookupList.Lookup)

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

def set_vertical_metrics(font):
    """Keep Slussen's line box; widen the clipping box so Thai is not cut off."""
    os2 = font["OS/2"]
    hhea = font["hhea"]

    # Line box — Slussen's, exactly. Never retune: this is document line spacing.
    os2.sTypoAscender = ORIG_TYPO_ASC
    os2.sTypoDescender = ORIG_TYPO_DES
    os2.sTypoLineGap = ORIG_TYPO_GAP
    hhea.ascent = ORIG_HHEA_ASC
    hhea.descent = ORIG_HHEA_DES
    hhea.lineGap = ORIG_HHEA_GAP

    # Clipping box — must cover merged ink, Latin and Thai alike.
    os2.usWinAscent = WIN_ASCENT
    os2.usWinDescent = WIN_DESCENT
    os2.fsSelection |= USE_TYPO          # bit 7 — spacing comes from sTypo

    print(f"     [5] Metrics: sTypo/hhea={ORIG_TYPO_ASC}/{ORIG_TYPO_DES}/{ORIG_TYPO_GAP} "
          f"(Slussen, preserved) win={WIN_ASCENT}/{WIN_DESCENT} "
          f"(widened for Thai ink) USE_TYPO_METRICS=on")


# ---------------------------------------------------------------------------
# Step 6: Spec compliance — Coverage ordering + single-byte Mac cmap
# ---------------------------------------------------------------------------

# This step used to be a TTX save/reload that printed "coverage tables sorted".
# A TTX roundtrip preserves list order verbatim — measured 29/57 unsorted before
# and 29/57 after on the sibling TH-Aeonik build. It sorted nothing and logged a
# success it never performed. Replaced with a check that actually does the work.


def _cov_perm(cov, gid):
    """Permutation sorting cov.glyphs by GID, or None if already ascending."""
    ids = [gid[g] for g in cov.glyphs]
    if ids == sorted(ids):
        return None
    return sorted(range(len(ids)), key=lambda i: ids[i])


def _cov_apply(cov, perm, *parallel):
    """Reorder cov.glyphs, and every Coverage-index-parallel array identically."""
    cov.glyphs = [cov.glyphs[i] for i in perm]
    for lst in parallel:
        if lst is not None:
            lst[:] = [lst[i] for i in perm]


def sort_coverage(font):
    """Restore ascending glyph-ID order in every GSUB/GPOS Coverage table.

    Bai Jamjuree's Coverage tables are sorted against *Bai's* glyph IDs.
    Re-parented onto Slussen's glyph order they may no longer be ascending,
    which violates the OpenType spec: consumers binary-search Coverage.
    HarfBuzz tolerates a violation, Uniscribe and DirectWrite do not, so Thai
    shaping would break only on Windows.

    Several subtables index a sibling array by Coverage index (MarkArray,
    BaseArray, PairSet, ...). Those must be permuted with the Coverage or the
    sort silently reattaches marks to the wrong anchors.

    Slussen's own glyph IDs do not move (Thai is appended after them), so its
    Coverage tables stay valid. As it happens Bai's survive re-parenting here
    too and this returns 0 — unlike TH-Aeonik, where 29 needed fixing. It runs
    unconditionally because that is a property of the glyph orders involved,
    not something the build should assume.
    """
    gid = {g: i for i, g in enumerate(font.getGlyphOrder())}
    fixed = 0

    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        for lookup in font[tag].table.LookupList.Lookup:
            for st in lookup.SubTable or []:
                kind = type(st).__name__

                # --- Coverage index selects a parallel record: permute both
                if kind == "MarkBasePos":
                    pairs = ((st.MarkCoverage, st.MarkArray.MarkRecord),
                             (st.BaseCoverage, st.BaseArray.BaseRecord))
                elif kind == "MarkMarkPos":
                    pairs = ((st.Mark1Coverage, st.Mark1Array.MarkRecord),
                             (st.Mark2Coverage, st.Mark2Array.Mark2Record))
                elif kind == "MarkLigPos":
                    pairs = ((st.MarkCoverage, st.MarkArray.MarkRecord),
                             (st.LigatureCoverage, st.LigatureArray.LigatureAttach))
                elif kind == "PairPos":
                    # format 2 is class-based and has no PairSet
                    pairs = ((st.Coverage, getattr(st, "PairSet", None)),)
                elif kind == "SinglePos":
                    pairs = ((st.Coverage, getattr(st, "Value", None)),)
                elif kind == "CursivePos":
                    pairs = ((st.Coverage, getattr(st, "EntryExitRecord", None)),)
                else:
                    pairs = None

                if pairs is not None:
                    for cov, arr in pairs:
                        perm = _cov_perm(cov, gid)
                        if perm:
                            _cov_apply(cov, perm, arr)
                            fixed += 1
                    continue

                # --- pure sets: membership only, order carries no meaning
                for field in ("BacktrackCoverage", "InputCoverage",
                              "LookAheadCoverage"):
                    for cov in getattr(st, field, None) or []:
                        perm = _cov_perm(cov, gid)
                        if perm:
                            _cov_apply(cov, perm)
                            fixed += 1
                cov = getattr(st, "Coverage", None)
                if cov is not None and hasattr(cov, "glyphs"):
                    perm = _cov_perm(cov, gid)
                    if perm:
                        _cov_apply(cov, perm)
                        fixed += 1

    return fixed


def fix_mac_cmap(font):
    """Drop codes >255 from the (1,0) subtable — it is a single-byte platform.

    copy_thai_glyphs() writes the Thai codepoints into every cmap subtable it
    finds, including the Macintosh one, where only 0-255 is addressable.
    """
    dropped = 0
    for t in font["cmap"].tables:
        if (t.platformID, t.platEncID) == (1, 0):
            over = [c for c in t.cmap if c > 255]
            for c in over:
                del t.cmap[c]
            dropped += len(over)
    return dropped


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

    # 2. usWinAscent/Descent must cover the merged ink, or Windows clips it
    head = font["head"]
    win_ok = (os2.usWinAscent >= head.yMax and os2.usWinDescent >= -head.yMin)
    checks.append(f"winAsc={os2.usWinAscent}(ink {head.yMax:+})")
    checks.append(f"winDes={os2.usWinDescent}(ink {head.yMin:+})")
    if not win_ok:
        failures.append(f"clipping box does not cover ink: "
                        f"win={os2.usWinAscent}/{os2.usWinDescent} "
                        f"vs ink {head.yMax:+}/{head.yMin:+}")

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

    # 5. Naming: nameID1 per RIBBI config, nameID16 always the shared family
    n1 = nt.getName(1, 3, 1, 0x0409)
    n16 = nt.getName(16, 3, 1, 0x0409)
    n1t = n1.toUnicode() if n1 else "?"
    n16t = n16.toUnicode() if n16 else "?"
    name_ok = (n1t == cfg["nameID1"] and n16t == "TH Slussen")
    checks.append(f"nameID1='{n1t}' nameID16='{n16t}'({'OK' if name_ok else 'FAIL'})")
    if not name_ok:
        failures.append(f"naming wrong: nameID1='{n1t}' (want '{cfg['nameID1']}') "
                        f"nameID16='{n16t}' (want 'TH Slussen')")

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

    # Step 5: Vertical metrics (Slussen line box, Thai-safe clipping box)
    set_vertical_metrics(slussen)

    # Step 6: Spec compliance — Coverage ordering + single-byte Mac cmap
    n_cov = sort_coverage(slussen)
    n_mac = fix_mac_cmap(slussen)
    print(f"     [6] Coverage tables re-sorted: {n_cov} | "
          f"Mac cmap codes >255 dropped: {n_mac}")

    slussen.save(str(output_path))

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
