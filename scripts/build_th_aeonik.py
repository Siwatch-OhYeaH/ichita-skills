#!/usr/bin/env python3
"""
Build TH-Aeonik font family — unified pipeline.

Merges Aeonik (Latin) + Bai Jamjuree (Thai) into TH-Aeonik with complete
OpenType support for Thai text shaping on Windows.

OUTPUT IS TRUETYPE (`glyf`), NOT CFF. This is the load-bearing design choice
and it is not cosmetic:

  * Thai comes from Bai Jamjuree's own `glyf` outlines rather than being
    re-expressed as CFF, so the only transforms applied to them are the
    deliberate ones: the scale to the Latin x-height and the weight match.
    A CFF base added a rasteriser difference on top — 8.36% of pixels, mean
    delta 6.83/255 — that was FreeType's Adobe CFF engine versus its TrueType
    engine, not curve approximation (max_err 1.0 / 0.5 / 0.1 gave byte-
    identical deltas). NOTE: Thai is deliberately NOT identical to Bai any
    more. Bai's Thai is drawn for Bai's own Latin; see scripts/th_thai_prep.py.

  * `glyf` has no width operand, so the defect that made every printed PDF
    unreadable — CFF charstring widths disagreeing with `hmtx`, which Microsoft
    Print to PDF turns into the PDF /W array — becomes impossible to express.

  * Print to PDF already declares /Subtype /CIDFontType2 + /FontFile2 for these
    fonts. Shipping `glyf` makes that declaration truthful and clears poppler's
    "Mismatch between font type and embedded font file" warnings.

The cost, accepted knowingly: Latin is no longer pixel-exact to Aeonik (10.16%
of pixels, mean delta 3.90/255 — lower amplitude than the Thai error it
replaces). Aeonik carries zero hint operators, so nothing is lost structurally.
TH-Slussen is the same pipeline but Slussen *is* hinted; see its build script.

Pipeline steps:
  0. Convert the Latin base from CFF to `glyf` — before any Thai is added
  0b. Scale + weight-match Bai to this Latin weight (scripts/th_thai_prep.py)
  1. Copy Thai glyphs + variants from Bai Jamjuree (glyf outlines)
  2. Merge GPOS/GDEF/GSUB tables from Bai Jamjuree (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2 v4, fsType, panose
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Set vertical metrics — hhea/sTypo/usWin agree, Thai-safe descent
  6. Sort GSUB/GPOS Coverage tables + clean Mac cmap (Uniscribe compliance)
  7. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Sources:
  Latin: Aeonik OTF (D:\\ drive preferred, fallback assets/fonts/aeonik/)
  Thai:  Bai Jamjuree (system fonts preferred, fallback assets/fonts/bai-jamjuree/)

Usage:
  python3 build_th_aeonik.py                    # Build all 14 faces
  python3 build_th_aeonik.py --weights Bold,Light  # Build specific weights

Requires: fontTools >= 4.0
"""

import copy as copy_mod
import sys
import warnings
from pathlib import Path

from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

sys.path.insert(0, str(Path(__file__).parent))
from th_thai_prep import (BUILD_TABLE, THAI_SCALE, add_dotted_circle,  # noqa: E402
                          fix_thai_gdef, prepare_bai)

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
# Latin source per weight. The Thai source is NOT chosen here — Bai's weight
# ladder does not align with Aeonik's, so the pairing (and the emboldening that
# closes the residual) lives in th_thai_prep.BUILD_TABLE. Pairing by matching
# names is what left Thai 18% lighter than the Latin beside it.
WEIGHTS = {
    "Air":           "Aeonik-Air.otf",
    "Thin":          "Aeonik-Thin.otf",
    "Light":         "Aeonik-Light.otf",
    "Regular":       "Aeonik-Regular.otf",
    "Medium":        "Aeonik-Medium.otf",
    "Bold":          "Aeonik-Bold.otf",
    "Black":         "Aeonik-Black.otf",
    "AirItalic":     "Aeonik-AirItalic.otf",
    "ThinItalic":    "Aeonik-ThinItalic.otf",
    "LightItalic":   "Aeonik-LightItalic.otf",
    "RegularItalic": "Aeonik-RegularItalic.otf",
    "MediumItalic":  "Aeonik-MediumItalic.otf",
    "BoldItalic":    "Aeonik-BoldItalic.otf",
    "BlackItalic":   "Aeonik-BlackItalic.otf",
}

# Per-weight metadata config (Windows RIBBI model)
#
# nameID2 may only be Regular / Bold / Italic / Bold Italic, so one nameID1 can
# carry at most those four faces. Aeonik has seven weights, so Air, Thin, Light,
# Medium and Black each take their own nameID1 and pair their italic through
# nameID2='Italic'. nameID16/17 put all fourteen back together as one 'TH
# Aeonik' family wherever they are read. Same scheme as TH Slussen Medium and
# SemiBold, which is what made those two selectable in Word.
def _nonribbi(label, slug, weight_class, panose, italic=False):
    """Config for a weight that has no RIBBI slot of its own."""
    return {
        "nameID1": f"TH Aeonik {label}",
        "nameID2": "Italic" if italic else "Regular",
        "nameID4": f"TH Aeonik {label}" + (" Italic" if italic else ""),
        "nameID6": f"TH-Aeonik-{slug}" + ("Italic" if italic else ""),
        "nameID16": "TH Aeonik",
        "nameID17": f"{label} Italic" if italic else label,
        "fsSelection": (ITALIC if italic else REGULAR) | USE_TYPO,
        "macStyle": MAC_ITALIC if italic else 0,
        "weightClass": weight_class, "panose_bWeight": panose,
    }


WEIGHT_CONFIG = {
    "Air":          _nonribbi("Air", "Air", 100, 2),
    "AirItalic":    _nonribbi("Air", "Air", 100, 2, italic=True),
    "Thin":         _nonribbi("Thin", "Thin", 200, 3),
    "ThinItalic":   _nonribbi("Thin", "Thin", 200, 3, italic=True),
    "Medium":       _nonribbi("Medium", "Medium", 500, 6),
    "MediumItalic": _nonribbi("Medium", "Medium", 500, 6, italic=True),
    "Black":        _nonribbi("Black", "Black", 900, 9),
    "BlackItalic":  _nonribbi("Black", "Black", 900, 9, italic=True),
}

WEIGHT_CONFIG.update({
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
})


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
# Step 0: Convert the Latin base from CFF to glyf
# ---------------------------------------------------------------------------

# Cubic -> quadratic error bound, in font units. Deliberately NOT a tuning knob:
# 1.0, 0.5 and 0.1 were measured to produce byte-identical rasters, because the
# residual Latin difference is FreeType's CFF engine versus its TrueType engine,
# not curve approximation. Anyone tightening this to chase the drift is chasing
# the wrong variable.
CU2QU_MAX_ERR = 0.5

SKIP_GLYPHS = {".notdef", ".null", "NULL", "nonmarkingreturn", "CR"}


def convert_to_glyf(font):
    """Re-express the Latin base's CFF outlines as `glyf`, in place.

    Must run BEFORE any Thai is added. `_union_ot()` is only valid because the
    Latin font keeps its own glyph IDs — Thai is appended after them, so its
    GSUB/GPOS survive the merge verbatim. Converting while the glyph set is
    still purely Latin preserves that invariant exactly.
    """
    glyph_set = font.getGlyphSet()
    glyf = newTable("glyf")
    glyf.glyphOrder = list(font.getGlyphOrder())
    glyf.glyphs = {}
    for gn in glyf.glyphOrder:
        pen = TTGlyphPen(None)
        glyph_set[gn].draw(Cu2QuPen(pen, CU2QU_MAX_ERR, reverse_direction=True))
        glyf[gn] = pen.glyph()

    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    font["maxp"].tableVersion = 0x00010000
    for attr, default in [("maxZones", 1), ("maxTwilightPoints", 0),
                          ("maxStorage", 0), ("maxFunctionDefs", 0),
                          ("maxInstructionDefs", 0), ("maxStackElements", 0),
                          ("maxSizeOfInstructions", 0),
                          ("maxComponentElements", 0), ("maxComponentDepth", 0)]:
        setattr(font["maxp"], attr, default)
    font["head"].indexToLocFormat = 0

    # Without this the file keeps the 'OTTO' tag and every consumer rejects it —
    # FreeType fails with "SFNT font table missing", which names the symptom and
    # not the cause.
    font.sfntVersion = "\000\001\000\000"

    del font["CFF "]
    for tag in ("FFTM", "VORG"):
        if tag in font:
            del font[tag]

    print(f"     [0] CFF -> glyf: {len(glyf.glyphOrder)} Latin glyphs "
          f"(cu2qu max_err={CU2QU_MAX_ERR})")


# ---------------------------------------------------------------------------
# Step 1: Copy Thai glyphs
# ---------------------------------------------------------------------------

def _copy_glyph(target_font, bai_font, bai_glyph_name, target_name, verbatim_ok):
    """Append one Bai Jamjuree glyph to the merged font.

    Copied verbatim when it can be — that is where pixel-identical Thai comes
    from. A composite may only be copied verbatim if every component it names is
    also being copied from Bai; otherwise the component name resolves against
    the *Latin* font and the glyph is silently rebuilt out of the wrong parts.

    Measured on Aeonik: of 362 Bai glyphs copied, 175 are composite and 212
    component references collide with a Latin glyph the base already owns
    (uni1EAE -> A, uni1EB6 -> uni0306, ...). Those are decomposed. All 8 Thai
    composites (uni0E4D0E48..uni0E4D0E4B and their .narrow forms) are
    translate-only and reference only Bai glyphs, so Thai stays verbatim.
    """
    bai_glyf = bai_font["glyf"]
    if bai_glyph_name not in bai_glyf.glyphs:
        return False

    src = bai_glyf[bai_glyph_name]
    if src.isComposite() and not all(
            c.glyphName in verbatim_ok for c in src.components):
        pen = TTGlyphPen(None)
        rec = DecomposingRecordingPen(bai_font.getGlyphSet())
        bai_font.getGlyphSet()[bai_glyph_name].draw(rec)
        rec.replay(pen)
        glyph = pen.glyph()
    else:
        glyph = copy_mod.deepcopy(src)

    target_font["glyf"].glyphs[target_name] = glyph

    glyph_order = target_font.getGlyphOrder()
    if target_name not in glyph_order:
        glyph_order.append(target_name)
        target_font.setGlyphOrder(glyph_order)
        target_font["glyf"].glyphOrder = glyph_order

    if bai_glyph_name in bai_font["hmtx"].metrics:
        target_font["hmtx"].metrics[target_name] = \
            bai_font["hmtx"].metrics[bai_glyph_name]

    return True


def copy_thai_glyphs(aeonik_font, bai_font):
    bai_cmap = bai_font.getBestCmap()
    if not bai_cmap:
        print("     !! No cmap in Bai Jamjuree")
        return 0

    have = set(aeonik_font.getGlyphOrder())

    # Cmap-mapped Thai codepoints (U+0E01-0E5B) land under uniXXXX names; every
    # other Bai glyph keeps its own name. Both sets are known up front so
    # composite components can be resolved before the first glyph is written.
    thai_mappings = {
        cp: gn for cp, gn in bai_cmap.items() if 0x0E01 <= cp <= 0x0E5B
    }
    renamed = {gn: f"uni{cp:04X}" for cp, gn in thai_mappings.items()}
    verbatim_ok = {
        gn for gn in bai_font.getGlyphOrder()
        if gn not in SKIP_GLYPHS and (gn in renamed or gn not in have)
    }

    added = 0
    for cp, bai_gn in sorted(thai_mappings.items()):
        if _copy_glyph(aeonik_font, bai_font, bai_gn, f"uni{cp:04X}", verbatim_ok):
            added += 1

    glyphs = aeonik_font["glyf"].glyphs
    for table in aeonik_font["cmap"].tables:
        if hasattr(table, "cmap") and table.cmap is not None:
            for cp in thai_mappings:
                tn = f"uni{cp:04X}"
                if tn in glyphs:
                    table.cmap[cp] = tn

    # Add ALL remaining Bai glyphs (variants + non-Thai for GPOS/GSUB integrity)
    extra = 0
    for gn in bai_font.getGlyphOrder():
        if gn in glyphs or gn in SKIP_GLYPHS:
            continue
        if _copy_glyph(aeonik_font, bai_font, gn, gn, verbatim_ok):
            extra += 1

    aeonik_font["maxp"].numGlyphs = len(aeonik_font.getGlyphOrder())

    # `gasp` is what tells GDI/DirectWrite to grid-fit and antialias a TrueType
    # face. CFF needs none, so neither Latin source ships one; Bai does.
    if "gasp" in bai_font:
        aeonik_font["gasp"] = copy_mod.deepcopy(bai_font["gasp"])

    # post 3.0 stores no glyph names. The CFF build got them from the charset;
    # `glyf` has no such fallback, so every consumer — and every acceptance
    # test that compares by name — would see glyph00001. Format 2.0 keeps them.
    aeonik_font["post"].formatType = 2.0
    aeonik_font["post"].extraNames = []
    aeonik_font["post"].mapping = {}
    aeonik_font["post"].glyphOrder = aeonik_font.getGlyphOrder()

    verbatim = sum(1 for gn in bai_font.getGlyphOrder()
                   if not bai_font["glyf"][gn].isComposite()
                   or all(c.glyphName in verbatim_ok
                          for c in bai_font["glyf"][gn].components))
    print(f"     [1] Glyphs: {added} Thai cmap + {extra} extra (GPOS/GSUB) | "
          f"{verbatim} copyable verbatim, rest decomposed")
    return added + extra


# ---------------------------------------------------------------------------
# Step 2: Merge GPOS/GDEF/GSUB
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

    Aeonik keeps its own glyph IDs (Thai is appended after them), so its
    GSUB/GPOS stay valid verbatim. Bai Jamjuree's Thai lookups are grafted on
    top, and only the Thai script record is taken — 'latn' and 'DFLT' stay
    Aeonik's, so Latin kerning and ligatures survive the merge.
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

        A LangSys must not list the same feature tag twice — consumers take
        the first and ignore the rest. Aeonik's italics register a stub 'mark'
        feature under 'thai'; appending Bai's real 'mark' beside it would let
        the stub win and silently kill Thai mark positioning. So same-tag
        features are combined into a single fresh FeatureRecord.
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

        # Aeonik's italics ship a stub 'thai' ScriptRecord with no Thai glyphs
        # behind it. Skipping on collision would drop Bai's entire Thai feature
        # set, so union into the existing record instead of ignoring it.
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


def merge_ot_tables(aeonik_font, bai_font):
    if "GPOS" not in bai_font:
        return

    if "GPOS" in aeonik_font:
        _union_ot(aeonik_font["GPOS"], bai_font["GPOS"], {"thai"})
    else:
        aeonik_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
    gpos_n = len(aeonik_font["GPOS"].table.LookupList.Lookup)
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
        if "GSUB" in aeonik_font:
            _union_ot(aeonik_font["GSUB"], bai_font["GSUB"], {"thai"})
        else:
            aeonik_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
        gsub_n = len(aeonik_font["GSUB"].table.LookupList.Lookup)

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

# Line box. Thai ink reaches +987/-364 (Bai) vs Latin +898/-206 (Aeonik), and
# GPOS mark stacking pushes higher still, so the descent is deepened past both
# sources. All three metric sets must agree: browsers honour sTypo, Word and
# most PDF engines honour hhea/usWin. Leaving them to disagree made the same
# file render at 1.20 em in one and 2.11 em in the other.
# Line box. This must CONTAIN the ink, not merely describe an intended leading.
#
# The 2026-08-02 build set these to 1000/-300 on the reasoning — recorded in the
# comment below — that USE_TYPO_METRICS made only the sTypo set matter for
# spacing. It does not. Word leads off hhea, and the evidence is direct: the old
# .otf declared hhea 1550/-561 and printed at 25.30 pt, this build declared
# 1000/-300 and printed the same document at 15.60 pt. 2111/1300 = 1.624;
# 25.30/15.60 = 1.622. A 38% collapse, predicted by the hhea ratio alone.
#
# The same undersized box clipped Thai. usWinAscent/Descent were already 1250/570
# and did contain the ink, yet tone marks were still cut off — so the clip is
# taken against the hhea line box, and raising usWin alone cannot fix it.
#
# Values below clear the measured union of Latin and scaled-Thai ink
# (-527..1134) with headroom. Every weight in the family MUST share them, or
# bolding a word would change the line height.
ASCENT, DESCENT, LINEGAP = 1160, -550, 0

# Clipping box — a different thing from the line box. usWinAscent/usWinDescent
# bound what GDI will draw, so they must contain every glyph's ink, not just the
# ink of the cmap-reachable ones.
#
# These were 1050/400, which did not. The overflow is not theoretical: Bai
# Jamjuree substitutes small tone-mark variants (uni0E48.small and friends) via
# GSUB for two-level stacks, and those are reachable only through shaping, never
# through cmap. Shaping 'น้ำเชื่อม' puts uni0E48.small at +1136 and 'ฟั้น' puts
# uni0E49.small at +1168 in Bold — 86 and 118 units above the old ceiling, so
# the top of the tone mark was cut off. Raw glyph ink runs to +1225/-561 across
# the six weights; the box now clears that with headroom.
#
# Raising these does not change line spacing: USE_TYPO_METRICS is set below, so
# consumers take spacing from the sTypo set above.
WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT


def set_vertical_metrics(font):
    """Set all three metric sets to the same containing box, then prove it.

    hhea, sTypo and usWin are deliberately identical. Renderers disagree about
    which set to read — Word takes hhea, LibreOffice and browsers take sTypo
    when USE_TYPO_METRICS is on, GDI clips against usWin — and the previous
    build shipped three different answers, so the same document reflowed
    differently in each. One box everywhere means the line pitch is a property
    of the font rather than of whoever opens it.
    """
    os2 = font["OS/2"]
    hhea = font["hhea"]

    # Fail the build rather than ship a font that clips. The overflow is never
    # in the cmap-reachable glyphs — it is the shaping-only tone-mark variants
    # (uni0E48.small and friends) that GSUB substitutes into two-level stacks.
    lo, hi = _ink_bounds(font)
    if hi > ASCENT or lo < DESCENT:
        raise SystemExit(
            f"     !! ink {lo:.0f}..{hi:.0f} escapes the line box "
            f"{DESCENT}..{ASCENT} — raise ASCENT/DESCENT, do not ship this")

    os2.usWinAscent = WIN_ASCENT
    os2.usWinDescent = WIN_DESCENT
    hhea.ascent, hhea.descent, hhea.lineGap = ASCENT, DESCENT, LINEGAP
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASCENT, DESCENT, LINEGAP
    os2.fsSelection |= USE_TYPO          # bit 7 — prefer the sTypo set
    print(f"     [5] Metrics: hhea/sTypo/win={ASCENT}/{DESCENT}/{LINEGAP} "
          f"(line {ASCENT - DESCENT + LINEGAP}) ink {lo:.0f}..{hi:.0f} fits")


def _ink_bounds(font):
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    lo = hi = None
    for gn in font.getGlyphOrder():
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds:
            continue
        lo = bp.bounds[1] if lo is None or bp.bounds[1] < lo else lo
        hi = bp.bounds[3] if hi is None or bp.bounds[3] > hi else hi
    return lo, hi


# ---------------------------------------------------------------------------
# Step 6: TTX roundtrip (sort coverage tables)
# ---------------------------------------------------------------------------

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

    GSUB/GPOS are copied wholesale from Bai Jamjuree, where each Coverage was
    sorted against *Bai's* glyph IDs. Re-parented onto Aeonik's glyph order
    those lists are no longer ascending, which violates the OpenType spec:
    consumers binary-search Coverage. HarfBuzz tolerates it, Uniscribe and
    DirectWrite do not, so Thai shaping breaks only on Windows.

    Several subtables index a sibling array by Coverage index (MarkArray,
    BaseArray, PairSet, ...). Those must be permuted with the Coverage or the
    sort silently reattaches marks to the wrong anchors.
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

    The merge wrote raw Thai codepoints (up to U+0E5B) into the Macintosh
    subtable, where only 0-255 is addressable.
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
# Step 7: Verify
# ---------------------------------------------------------------------------

def verify_font(weight_name):
    cfg = WEIGHT_CONFIG[weight_name]
    path = OUTPUT_DIR / f"TH-Aeonik-{weight_name}.ttf"
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

    # Latin match. Segment-by-segment comparison is meaningless now that the
    # merged font is quadratic and Aeonik is cubic — it would report 0% on a
    # perfect build. Compare what survives the conversion instead: advance width
    # and control box, both of which must be exact. Visual fidelity is the
    # acceptance test's job (compare_th_aeonik.py), not this smoke check.
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
                pm, pa = ControlBoundsPen(gs_m), ControlBoundsPen(gs_a)
                gs_m[mg].draw(pm)
                gs_a[ag].draw(pa)
                same_box = (pm.bounds is None) == (pa.bounds is None) and (
                    pm.bounds is None
                    or all(abs(x - y) <= 1 for x, y in zip(pm.bounds, pa.bounds)))
                if same_box and gs_m[mg].width == gs_a[ag].width:
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

def build_font(weight_name, aeonik_file, bai_file=None):
    print(f"\n  === {weight_name} ===")

    aeonik_path = find_aeonik(aeonik_file)
    if not aeonik_path:
        print(f"     !! Aeonik not found: {aeonik_file}")
        return False

    bai_src, embolden = BUILD_TABLE["TH-Aeonik"][weight_name]
    print(f"     Latin: {aeonik_path}")
    print(f"     Thai:  {bai_src}  (scale {THAI_SCALE['TH-Aeonik']}, "
          f"embolden +{embolden:.1f}u)")

    aeonik = TTFont(str(aeonik_path))
    # Scaled to the Latin x-height and weight-matched before a single glyph is
    # copied, so everything downstream — GPOS anchors, ink bounds, the metrics
    # assertion — sees the Thai at its final size.
    bai = prepare_bai("TH-Aeonik", weight_name, latin_font=aeonik)

    if "CFF " not in aeonik:
        print(f"     !! Aeonik is not CFF format")
        return False

    output_path = OUTPUT_DIR / f"TH-Aeonik-{weight_name}.ttf"

    # Step 0: CFF -> glyf, while the glyph set is still purely Latin
    convert_to_glyf(aeonik)

    # Step 1: Copy Thai glyphs
    copy_thai_glyphs(aeonik, bai)

    # Step 2: Merge GPOS/GDEF/GSUB
    merge_ot_tables(aeonik, bai)

    # Step 3: Metadata
    apply_metadata(aeonik, weight_name)

    # Step 3b: Uniscribe needs an explicit GDEF class on every Thai
    # glyph, and a dotted circle to hang orphaned marks on. Bai supplies
    # neither, which is why an isolated or repeated 'า' would not type.
    n_base, n_mark = fix_thai_gdef(aeonik)
    from fontTools.pens.boundsPen import BoundsPen as _BP
    _gs = aeonik.getGlyphSet(); _bp = _BP(_gs)
    _gs[aeonik.getBestCmap()[ord('x')]].draw(_bp)
    _xh = _bp.bounds[3] - _bp.bounds[1]
    added = add_dotted_circle(aeonik, _xh)
    print(f"     [3b] GDEF: {n_base} Thai -> BASE, {n_mark} -> MARK | "
          f"U+25CC dotted circle: {'synthesised' if added else 'already present'}")

    # Step 4: Thai range bits
    set_thai_bits(aeonik)

    # Step 5: Vertical metrics
    set_vertical_metrics(aeonik)

    # Step 6: Spec compliance — Coverage ordering + single-byte Mac cmap
    n_cov = sort_coverage(aeonik)
    n_mac = fix_mac_cmap(aeonik)
    print(f"     [6] Coverage tables re-sorted: {n_cov} | "
          f"Mac cmap codes >255 dropped: {n_mac}")

    # maxPoints / maxContours / maxComponent* are read by Windows to size its
    # rasteriser buffers. They must describe the final glyph set, not the Latin
    # one convert_to_glyf() left behind. Glyphs built by TTGlyphPen carry no
    # bounds until asked, and maxp.recalc reads xMin off every one of them.
    glyf_table = aeonik["glyf"]
    hmtx = aeonik["hmtx"]
    shifted = 0
    for gn in aeonik.getGlyphOrder():
        glyph = glyf_table[gn]
        glyph.recalcBounds(glyf_table)
        # `glyf` renderers place the outline at (lsb - xMin), so a stale lsb
        # silently translates the whole glyph. CFF ignores hmtx lsb entirely,
        # which is why Aeonik ships some that disagree with their own outlines —
        # BoldItalic '9' declares lsb 33 against an xMin of 31, and inheriting
        # that shifted every point of the glyph 2 units right. Harmless in the
        # source, a visible defect the moment the font becomes TrueType.
        advance, lsb = hmtx.metrics[gn]
        x_min = getattr(glyph, "xMin", 0)
        if lsb != x_min:
            hmtx.metrics[gn] = (advance, x_min)
            shifted += 1
    aeonik["maxp"].recalc(aeonik)
    if shifted:
        print(f"     [6b] lsb re-synced to xMin on {shifted} glyph(s)")

    aeonik.save(str(output_path))

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
    for wn, af in weights.items():
        if build_font(wn, af):
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
