#!/usr/bin/env python3
"""
Build TH-Aeonik font family — unified pipeline.

Merges Aeonik (Latin) + Bai Jamjuree (Thai) into TH-Aeonik with complete
OpenType support for Thai text shaping on Windows.

OUTPUT IS CFF (`.otf`), NOT TrueType. This reverses the 2026-08-02 decision to
ship `glyf`, and the reason is that Windows renders the two formats through
different rasterisers — so a merged font in a different format from its Latin
source cannot render that Latin identically, no matter how exact the outlines.

Measured 2026-08-04 in DirectWrite, the renderer Word 2016+ and PowerPoint
actually use, at 11 pt with byte-identical outlines and identical advances:

    Aeonik      .otf/CFF    stems 2,1 px   ink 11,056
    TH Aeonik   .ttf/glyf   stems 1,1 px   ink  9,310   -15.8%
    Slussen     .otf/CFF    stems 2,2 px   ink 12,485
    TH Slussen  .ttf/glyf   stems 2,2 px   ink  9,940   -20.4%

Siwatch reported it as "TH Aeonik is slightly thinner than Aeonik, especially
Regular". It is worst at text sizes, which is why Regular shows it most. The
CFF rasteriser also consults the Private dict's BlueValues for alignment, and
those zones are part of what the format flip discarded.

Nothing on Linux can see this — FreeType does not reproduce Windows'
per-format behaviour. `scripts/win_latin_parity.py` measures it on the real
renderer and is the acceptance test for this decision.

How the Latin stays exactly Aeonik: the merge still runs in `glyf`, because
every downstream step (mark clearance, baseline seating, GPOS anchor work) is
written against it. The final step swaps the outlines back to CFF by taking
**Aeonik's own `CFF ` table wholesale** — its charstrings, Private dict,
BlueValues and local Subrs — and appending only the Thai as new charstrings.
Latin charstrings are never redrawn, so the cu2qu approximation the old build
baked into them is gone too: measured 0 of 656 Latin outlines differing.

Thai is converted quadratic -> cubic, which is EXACT (a quadratic Bézier has an
exact cubic form). This is the favourable direction; the old build's cubic ->
quadratic was the approximate one. Thai is deliberately NOT identical to Bai
anyway — Bai's Thai is drawn for Bai's own Latin, see scripts/th_thai_prep.py.

The one real cost, stated plainly: CFF can express an advance width TWICE —
in `hmtx` and as the charstring width operand — and a disagreement is what made
every printed PDF unreadable in 2026-08-01 (Microsoft Print to PDF builds the
PDF /W array from the charstring, not from `hmtx`, so Thai marks given a real
advance detached from their consonants). `glyf` made that unrepresentable. Going
back to CFF makes it representable again, so it is now asserted instead:
every appended charstring takes its width from `hmtx`, and
assert_advance_single_source() fails the build if any glyph disagrees. That
guard was verified to fail on a deliberately corrupted width.

Also note Print to PDF will now declare /CIDFontType0 + /FontFile3 rather than
CIDFontType2/FontFile2; scripts/check_print_pdf.py expects the CFF forms.

Pipeline steps:
  0. Convert the Latin base from CFF to `glyf` — the intermediate working
     format for the merge only; step 8 puts the CFF back
  0b. Scale + weight-match Bai to this Latin weight (scripts/th_thai_prep.py)
  1. Copy Thai glyphs + variants from Bai Jamjuree (glyf outlines)
  2. Merge GPOS/GDEF/GSUB tables from Bai Jamjuree (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2 v4, fsType, panose
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  5. Set vertical metrics — hhea/sTypo/usWin agree, Thai-safe descent
  6. Sort GSUB/GPOS Coverage tables + clean Mac cmap (Uniscribe compliance)
  7. Swap `glyf` back to CFF — Aeonik's charstrings verbatim, Thai appended
  8. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

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
from th_mark_clearance import raise_upper_marks
from th_baseline import seat_thai_on_baseline
from th_cff import assert_advance_single_source, convert_to_cff
import th_greek

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent
ASSETS = SCRIPT_DIR.parent / "assets"

# Source directories.
#
# The Latin base must be CoType's pristine v1.000 and is NOT in the repo —
# Siwatch keeps it locally and archives the old cuts himself, deliberately, so
# that nobody browsing assets/fonts/ has to work out which of two identically
# named Aeoniks to install.
#
# It must never be `fonts/aeonik/`. That directory holds our v1.001 Greek/math
# build, and feeding a build's own output back in as its source applies the
# version string twice and stops the build being reproducible. find_aeonik()
# fails loudly rather than falling back to it.
AEONIK_D_DRIVE = Path("/mnt/d/Doccument/New Identity/Aeonik-font-download/Aeonik-font-download")
AEONIK_LOCAL = ASSETS / "fonts" / "aeonik-v1000"   # git-ignored local drop point
BAI_SYSTEM = Path.home() / ".local" / "share" / "fonts"
BAI_LOCAL = ASSETS / "fonts" / "bai-jamjuree"
OUTPUT_DIR = ASSETS / "fonts" / "th-aeonik"

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
    """Locate one pristine Aeonik v1.000 face.

    Returns None when it is not there, and the caller must treat that as fatal.
    Do NOT add `fonts/aeonik/` as a fallback: that is our v1.001 build, and a
    silent fallback to it would rebuild the merged fonts from output that has
    already been through this pipeline once. The failure has to be visible —
    an unavailable source is recoverable, a quietly wrong one is not.
    """
    for d in [AEONIK_D_DRIVE, AEONIK_LOCAL]:
        p = d / filename
        if p.exists():
            return p
    return None


def require_aeonik_source():
    """Fail before doing any work if the pristine Latin source is missing."""
    if find_aeonik("Aeonik-Regular.otf") is None:
        sys.exit(
            "ERROR: pristine Aeonik v1.000 not found. Looked in:\n"
            f"  {AEONIK_D_DRIVE}\n"
            f"  {AEONIK_LOCAL}\n"
            "\n"
            "It is not kept in the repo — see assets/fonts/README.md. Drop the\n"
            "14 original CoType faces into the second path (git-ignored) or\n"
            "mount the D: drive, then re-run.\n"
            "\n"
            "assets/fonts/aeonik/ is NOT a substitute: it holds our v1.001\n"
            "Greek/math build, and building from it would apply this pipeline\n"
            "to its own output."
        )


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
    """Copy Bai's Thai into the merged font. Returns the set of names written.

    The returned set is what step 7 needs to decide which glyphs must NOT keep
    Aeonik's own charstring — see convert_to_cff() on `uni0E3F`.
    """
    bai_cmap = bai_font.getBestCmap()
    if not bai_cmap:
        print("     !! No cmap in Bai Jamjuree")
        return set()

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

    written = set()
    added = 0
    for cp, bai_gn in sorted(thai_mappings.items()):
        if _copy_glyph(aeonik_font, bai_font, bai_gn, f"uni{cp:04X}", verbatim_ok):
            added += 1
            written.add(f"uni{cp:04X}")

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
            written.add(gn)

    aeonik_font["maxp"].numGlyphs = len(aeonik_font.getGlyphOrder())

    # Glyph names during the `glyf` stage: post 3.0 stores none, and `glyf` has no
    # charset to fall back on, so every name would read glyph00001 for the rest of
    # the pipeline. Step 7 sets it back to 3.0 once the CFF charset can supply
    # them, which is what Aeonik itself ships.
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
    return written


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

# There are two boxes here and they answer different questions. Conflating them
# is what produced the 2026-08-02 defects at both extremes.
#
#   LINE BOX  (hhea, sTypo)  — how far apart consecutive baselines sit.
#   CLIP BOX  (usWin)        — how much ink GDI is willing to draw.
#
# The line box is NOT required to contain the ink. No Thai font sizes it that
# way. Measured, on this machine:
#
#     Bai Jamjuree   line 1250   worst shaped stack needs 1552   overflows 302
#     Leelawadee UI  line 1330
#     Tahoma         line 1207
#     Leelawadee     line 1196
#
# Thai marks are meant to overflow into the leading of the line above, where the
# Latin ascenders leave the space empty. Proof this is safe in the target
# renderer: printpdf4.pdf (Word 2024 -> PDF, TH-Aeonik at line 1300, shaped ink
# needing 1552) renders every stack in น้ำเชื่อม / ทั้งนี้ / ซึ่ง / ประสิทธิภาพ
# complete, with no clipping and no collision with the line above.
#
# So the earlier reasoning here — "usWin already contained the ink yet marks
# still clipped, therefore Word clips at hhea" — was wrong. Word does not clip
# at hhea in body text. Sizing the line box to contain the mark stack cost 42%
# of extra leading and is the reason TH-Aeonik set 1.71 em against Aeonik's
# 1.20 em on the same paragraph.
#
# That much still stands: Word does not clip at hhea, and 1.71 em was an
# over-correction.
#
# ---------------------------------------------------------------------------
# 2026-08-05: the box is 1537 — what the Thai needs — and TH Aeonik is no longer
# a drop-in Aeonik replacement. THE FONT CHOICE IS THE DOCUMENT'S LANGUAGE.
# ---------------------------------------------------------------------------
#
# This reverses 2026-08-04, and it is not a regression of it. It dissolves the
# conflict that produced that day's accepted defect.
#
# The history in one line each:
#
#     2026-08-03  box 1540, sized to the Thai. Latin-only lines led 28% loose.
#     2026-08-04  box 1200, Aeonik's exactly. Thai-over-Thai overlapped 262u.
#     2026-08-05  box 1537, sized to the Thai. English-only documents use
#                 ACTUAL AEONIK, so nothing has to lead like Aeonik any more.
#
# The 08-04 requirement was "a Latin-only paragraph in a TH-Aeonik document must
# lead exactly as Aeonik does". One font has one `hhea`, so that requirement and
# "room for two Thai lines" were not jointly satisfiable, and the Thai lost.
# Siwatch's 08-05 decision removes the requirement instead of the room:
#
#     English-only document  ->  Aeonik      box 1200, native leading
#     Thai + English mixed   ->  TH Aeonik   box 1537
#
# CONFIRMED CONSEQUENCE, ACCEPTED EXPLICITLY: in a mixed document, English-only
# paragraphs also lead +28% wider than the same text set in an Aeonik document.
# That is the price of one `hhea`, and it is now paid only by documents that
# contain Thai. Do not "fix" it — fixing it is what produced the 08-04 defect.
#
# What this retires: the 262-unit worst-case Thai-over-Thai overlap logged on
# 08-04 as a permanent accepted cost. At 1537 clearance is satisfied with the
# full 75-unit margin, so the overlap is gone rather than tolerated.
#
# Marks stay at 1.000 (th_thai_prep.MARK_SCALE) and that is still not re-openable.
# scripts/solve_mark_scale.py swept the real builder on 08-04:
#
#     mark scale   top   bottom   need   required(+75)
#        1.00     1139    -323    1462       1537
#        0.80     1096    -258    1354       1429
#        0.70     1078    -258    1336       1411
#        0.60     1061    -258    1319       1394
#
# A 25% mark reduction buys 35 units, because raise_upper_marks() re-lifts a
# smaller mark to hold its one-pixel target, and `bottom` floors on `ฐ`'s
# CONSONANT TAIL, which no mark scale can move. Shrinking marks would cost
# tone-mark legibility (่ ้ ๊ ๋ differ by small strokes) and buy nothing. The
# point is moot at 1537 anyway — the box now fits the marks at full size.
#
# ---------------------------------------------------------------------------
# THE SPLIT IS A MEASUREMENT, NOT A PREFERENCE.
# ---------------------------------------------------------------------------
#
# 1537 is the family's need. How it divides into ascent and descent is set by
# three constraints, all measured (scripts/thai_line_pitch.py, all 14 faces):
#
#   1. ascent >= the worst UPPER stack, 1139 on TH-Aeonik-Black.
#   2. descent >= the worst LOWER tail, 341 on TH-Aeonik-AirItalic.
#   3. all 14 faces share ONE box (qc_th_fonts check 4), otherwise bolding a
#      word changes the line height.
#
# Constraints 1 and 2 land on DIFFERENT FACES, so the split is sized to the
# family's envelope (1139 + 341 = 1480), not to any one face. That leaves 57
# units of slack inside the 1537.
#
# The slack is spent on keeping the LATIN optically where it was. Aeonik's own
# frame is 1000/-200; growing it to 1169/-368 adds 169 above and 168 below, so a
# Latin-only paragraph in a mixed document gains equal air on both sides and the
# Latin stays centred in the taller line rather than sitting low in it. The
# alternative candidate 1177/-360 clears the Thai equally well but pushes the
# Latin 9 units off centre for no measured gain.
#
# Both Thai constraints keep spare room at this split: 30 units above the worst
# stack, 27 below the worst tail.
#
# CONFIRM IN WORD after install (Phase 5): first-baseline position in an empty
# document, and a Latin-only paragraph inspected for sitting low. Until that is
# measured, the centring argument above is a construction argument.
ASCENT, DESCENT, LINEGAP = 1169, -368, 0        # 1537 — what the Thai needs

# LINEGAP stays 0 and must. `usWin` has no lineGap field, so hhea == sTypo ==
# usWin — the whole cross-platform strategy below — is only expressible with the
# gap folded into the ascent and descent.

# What the Thai needs for two consecutive lines to clear, from
# scripts/thai_line_pitch.py: worst face 1462 of shaped ink extent plus the
# 75-unit margin. The box above now MEETS this, and assert_line_box() enforces it
# per face against the built font. Re-derive after any rebuild that moves the
# marks: `python3 scripts/thai_line_pitch.py`.
THAI_NEEDS_PITCH = 1537

# The margin folded into THAI_NEEDS_PITCH — thai_line_pitch.MARGIN. It is
# Leelawadee UI's own spare and about one pixel at 11 pt / 96 dpi.
MARGIN_UNITS = 75

# usWin is the THIRD copy of THE LINE BOX, not a clip box sized to the ink.
#
# 2026-08-05: the box it copies is now 1537 rather than Aeonik's 1200, but the
# reason all three sets carry the same number is unchanged and is the entire
# cross-platform strategy. Which vertical field a renderer consults is not fixed
# (see the branch table in win_latin_parity.word_line_box), so rather than trying
# to learn every renderer's rule, the font yields the same box whichever field is
# read. That is what makes Word, PowerPoint, Excel, CoreText and browsers agree.
#
# It was 1240/560 until 2026-08-04, on the reasoning recorded in the line above it
# at the time: "widening this does not touch line spacing — Word leads off hhea
# and LibreOffice off sTypo, neither of which is usWin." That is false, and it was
# false in the shipping renderer while every Linux and outline-level check stayed
# green. Measured in Word via COM, same paragraph, same 11 pt, 5 lines each:
#
#     Aeonik      75.80 pt / 5 = 15.16 pt per line
#     TH Aeonik  114.00 pt / 5 = 22.80 pt per line   ratio 1.504
#
# 1.504 is usWin 1800/1200, not hhea 1200/1200 = 1.000. Siwatch reported it as the
# Latin line spacing still being wrong after the hhea fix, and he was right: hhea
# and sTypo were both already Aeonik's exactly, and the leading was still 50% over.
#
# 2026-08-05, IMPORTANT BOUND ON THAT CONCLUSION. It was written here as "Word
# leads off usWinAscent+usWinDescent", full stop. That is over-general. Word's
# pitch was then measured for 15 installed families and usWin is only the source
# for CFF faces; a glyf face with USE_TYPO_METRICS set ignores usWin entirely
# (Bai Jamjuree carries usWin 1786 and Word leads it at 1250; Sarabun 1853 and
# leads at 1300). See scripts/win_latin_parity.word_line_box for the three
# branches and the full evidence table.
#
# This does not weaken the fix below — TH Aeonik ships CFF, so usWin really is its
# spacing control, and the fix is robust by design rather than by luck because it
# sets hhea, sTypo and usWin all to the same number and therefore lands on that
# number whichever branch applies.
# What it does mean: THE FORMAT IS PART OF THE VERTICAL METRICS. Flipping this
# family back to glyf would silently move the spacing control off usWin, and the
# 2026-08-04 CFF flip is what put it on usWin in the first place.
#
# So all three metric sets carry 1537, and the ink is allowed out of the box.
# That is what the fonts Windows itself ships do — measured on this machine, ink
# extent against usWin:
#
#     Aeonik         usWin 1200   ink 1104   -96
#     Bai Jamjuree   usWin 1786   ink 1694   -92
#     Leelawadee UI  usWin 1330   ink 1287   -43
#     Tahoma         usWin 1207   ink 1453   +246
#     Segoe UI       usWin 1330   ink 1709   +379
#
# Read that table for CLIPPING only, not for spacing. All four Windows fonts in it
# are glyf, so none of them is led off usWin at all — Bai Jamjuree's 1786 is not
# its line box, it is only the bound its ink is measured against.
#
# Tahoma and Segoe UI both draw well outside usWin and neither clips in Word, so
# usWin is not a clip bound in DirectWrite-era Word. TH Aeonik lands at +391 here,
# which is Segoe UI's overflow. If Thai marks are ever reported clipped, this is
# the first constant to suspect — but re-measure before moving it, because the
# 2026-08-02 build raised it on a clipping premise that was never verified against
# the artifact (docs/THAI-LATIN-FONT-ENGINEERING.md (§3); the original is docs/archive/2026-08-02-th-font-line-box-overcorrection.md).
WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT


LINE_BOX = 1537             # what the Thai needs; pinned as a number
LATIN_PITCH = 1200          # Aeonik-Regular.otf hhea, for the ratio, not a target


def assert_line_box(latin_src):
    """Assert the line box: THE NUMBER, and its RELATIONSHIP to Aeonik's.

    Third flip of this assertion — 1610 -> 1200 -> 1537 — and it is designed so
    the next one fails loudly instead of quietly. The lesson this repo keeps
    re-learning cuts both ways:

      * Pinning ONLY the number let a defect read as a principle for two days
        while four separate checks asserted it. "The line box equals the Latin
        source's" was never a principle; it was one day's trade.
      * Pinning ONLY the relationship is unreviewable. A relationship cannot be
        checked on sight; a number can.

    So both halves are asserted, here and in assert_thai_clears() below:

      * THE NUMBER 1537, so the value is reviewable on sight.
      * THE RATIO to Aeonik, so an Aeonik update cannot silently redefine what
        "+28% wider than Aeonik" means. Aeonik's own box is still read from the
        source at build time and asserted.
      * THE THAI RELATIONSHIP — box >= this face's own measured requirement — in
        assert_thai_clears(), against the BUILT font, per face. That is the half
        that was missing on 08-04: the box was 337 units short of the Thai and no
        assertion said so, because the only bar was a number.
    """
    pitch = ASCENT - DESCENT + LINEGAP
    h = latin_src["hhea"]
    upem = latin_src["head"].unitsPerEm
    latin = round((h.ascender - h.descender + h.lineGap) * 1000 / upem)

    if pitch != LINE_BOX:
        raise SystemExit(
            f"     !! line box {pitch} is not the documented {LINE_BOX} — that is "
            f"the box the Thai measured out at (thai_line_pitch.py). Fix "
            f"ASCENT/DESCENT/LINEGAP, and if the Thai really needs a different "
            f"box now, change LINE_BOX with it and say why.")
    if latin != LATIN_PITCH:
        raise SystemExit(
            f"     !! Aeonik's own line box is {latin}, not the {LATIN_PITCH} the "
            f"documented +{LINE_BOX / LATIN_PITCH - 1:.1%} deviation is measured "
            f"against. The Latin source changed; re-derive rather than letting the "
            f"ratio quietly mean something new.")

    print(f"     [5] line box {pitch} (Thai needs {THAI_NEEDS_PITCH} = ink "
          f"{THAI_NEEDS_PITCH - MARGIN_UNITS} + margin {MARGIN_UNITS}) vs Aeonik's "
          f"{latin} — deliberately {pitch / latin - 1:+.1%}. TH Aeonik is the "
          f"MIXED-LANGUAGE face by decision (Siwatch 2026-08-05); English-only "
          f"documents use Aeonik itself, so nothing here has to lead like Aeonik.")


def assert_thai_clears(output_path):
    """box >= this face's own measured Thai requirement. The relationship half.

    Measured on the SAVED font, by shaping the worst stacks — not predicted from a
    metric field and not inherited from the family's worst face. Two reasons it
    has to be per face and post-build:

      * `top` moves whenever th_mark_clearance settles the marks differently, and
        the clearance pass is weight-dependent. A box derived from last week's
        worst face is not evidence about this face.
      * The worst upper stack and the worst lower tail live on DIFFERENT faces
        (Black and AirItalic), so only a per-face check can tell which constraint
        a given face is actually near.

    A future Thai change that needs more room fails HERE, at build time, instead
    of silently overlapping in Word and waiting for a defect report.
    """
    try:
        from thai_line_pitch import required_pitch
    except ImportError as exc:                       # pragma: no cover
        raise SystemExit(
            f"     !! cannot import thai_line_pitch ({exc}) — the Thai clearance "
            f"half of the line-box assertion cannot run, and this build must not "
            f"report a pass without it. Use the system python3, which has "
            f"uharfbuzz; venv_fonts/bin/python cannot run this build at all.")

    r = required_pitch(str(output_path))
    pitch = ASCENT - DESCENT + LINEGAP
    spare = pitch - r["required"]
    # Ascent and descent are checked separately from the total. A box big enough
    # overall can still clip a mark at the top of the frame or a tail at the
    # bottom if the split is wrong, and the total alone would not show it.
    if spare < 0:
        raise SystemExit(
            f"     !! line box {pitch} is {-spare:.0f} units BELOW what this face "
            f"needs ({r['required']:.0f} = shaped ink {r['need']:.0f} + margin "
            f"{MARGIN_UNITS}). Two consecutive Thai lines will overlap by "
            f"{-spare - MARGIN_UNITS:.0f} units at Single spacing. Re-derive the "
            f"box with scripts/thai_line_pitch.py; do NOT lower the margin.")
    if ASCENT < r["top"]:
        raise SystemExit(
            f"     !! ascent {ASCENT} is below this face's worst upper stack "
            f"{r['top']:.0f} — the top of the stack sits above the line box, so "
            f"the first line of a frame can clip. Re-split ASCENT/DESCENT.")
    if -DESCENT < -r["bottom"]:
        raise SystemExit(
            f"     !! descent {-DESCENT} is below this face's worst lower tail "
            f"{-r['bottom']:.0f} — re-split ASCENT/DESCENT.")
    print(f"     [8] Thai clearance: box {pitch} >= needs {r['required']:.0f} "
          f"(ink {r['need']:.0f} + margin {MARGIN_UNITS}), spare {spare:+.0f}; "
          f"ascent {ASCENT} >= worst stack {r['top']:.0f}, descent {-DESCENT} >= "
          f"worst tail {-r['bottom']:.0f}")


def set_vertical_metrics(font):
    """Line box from the Latin source; clip box from the measured ink.

    All three metric sets carry the same numbers, because all three are read as
    line spacing by something that matters: Word leads off usWin, LibreOffice and
    browsers off sTypo when USE_TYPO_METRICS is on, and hhea is the fallback. A
    single box is the only way the pitch stops depending on the renderer.
    """
    os2 = font["OS/2"]
    hhea = font["hhea"]

    # Fail the build if any box drifts off the Latin's. The ink is NOT asserted to
    # fit — Thai marks are drawn outside the box on purpose, exactly as Tahoma and
    # Segoe UI do. See the note on WIN_ASCENT for the measurements.
    lo, hi = _ink_bounds(font)
    if (WIN_ASCENT, -WIN_DESCENT) != (ASCENT, DESCENT):
        raise SystemExit(
            f"     !! clip box {-WIN_DESCENT}..{WIN_ASCENT} is not the line box "
            f"{DESCENT}..{ASCENT} — Word leads off usWin, so they must match")

    os2.usWinAscent = WIN_ASCENT
    os2.usWinDescent = WIN_DESCENT
    hhea.ascent, hhea.descent, hhea.lineGap = ASCENT, DESCENT, LINEGAP
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASCENT, DESCENT, LINEGAP
    os2.fsSelection |= USE_TYPO          # bit 7 — prefer the sTypo set
    over_up, over_dn = max(0, hi - ASCENT), max(0, -lo + DESCENT)
    print(f"     [5] Metrics: line(hhea=sTypo=usWin)={ASCENT}/{DESCENT}/{LINEGAP} "
          f"({ASCENT - DESCENT + LINEGAP}) "
          f"ink {lo:.0f}..{hi:.0f} (draws outside the box by {over_up:.0f}/{over_dn:.0f}, "
          f"expected — Segoe UI overflows by 379)")


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

def build_font(weight_name, aeonik_file, bai_file=None, mark_scale=None,
               out_dir=None):
    print(f"\n  === {weight_name} ===")
    out_dir = out_dir or OUTPUT_DIR

    aeonik_path = find_aeonik(aeonik_file)
    if not aeonik_path:
        print(f"     !! Aeonik not found: {aeonik_file}")
        return False

    bai_src, embolden = BUILD_TABLE["TH-Aeonik"][weight_name]
    print(f"     Latin: {aeonik_path}")
    print(f"     Thai:  {bai_src}  (scale {THAI_SCALE['TH-Aeonik']}, "
          f"embolden +{embolden:.1f}u)")

    aeonik = TTFont(str(aeonik_path))
    # Read the line box off the Latin before anything is merged into it. The
    # merged face no longer has to lead as Aeonik does — English-only documents
    # use Aeonik itself — but Aeonik's own box is still what the documented +28%
    # is measured against, so it is asserted rather than assumed.
    assert_line_box(aeonik)
    # Scaled to the Latin x-height and weight-matched before a single glyph is
    # copied, so everything downstream — GPOS anchors, ink bounds, the metrics
    # assertion — sees the Thai at its final size.
    bai = prepare_bai("TH-Aeonik", weight_name, latin_font=aeonik,
                      mark_scale=mark_scale)

    if "CFF " not in aeonik:
        print(f"     !! Aeonik is not CFF format")
        return False

    # A pristine, untouched copy of Aeonik's CFF table. Step 7 puts this back, so
    # the shipped Latin charstrings are Aeonik's own bytes rather than anything
    # this pipeline redrew. Read from the file a second time rather than
    # deepcopied, so no mutation below can possibly reach it.
    latin_cff = TTFont(str(aeonik_path))["CFF "]

    output_path = out_dir / f"TH-Aeonik-{weight_name}.otf"

    # Step 0: CFF -> glyf, while the glyph set is still purely Latin. This is the
    # intermediate working format for the merge only — every step below is written
    # against `glyf`, and step 7 swaps the CFF back in.
    convert_to_glyf(aeonik)

    # Step 1: Copy Thai glyphs
    thai_names = copy_thai_glyphs(aeonik, bai)

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

    # Step 3c: put the Thai back on the Latin baseline. The stem match
    # uses FontForge changeWeight, which grows the outline downward as
    # well as sideways, so a flat-bottomed consonant that Bai drew at
    # y=0 ends up below the Latin, worse the bolder the weight. Rigid
    # translation of the bases and their anchors; the marks follow.
    seat_thai_on_baseline(aeonik)

    # Step 3d: open up the Thai stack. Bai sets its upper marks close to the
    # consonant and the scale-plus-embolden this pipeline applies closes the
    # gap further, worst in the heavy weights — TH-Aeonik-Black measured a
    # median clearance of 0.6/1000 em, i.e. touching. Below about 65/1000 em
    # the gap is under one pixel at 11 pt on a 96 dpi screen and Word renders
    # the mark fused into the consonant.
    raise_upper_marks(aeonik)

    # Step 4: Thai range bits
    set_thai_bits(aeonik)

    # Step 4b: the Greek/math codepoints Aeonik v1 is missing. Same resolver as
    # scripts/build_aeonik.py, so the two families cannot drift apart in coverage
    # — which matters now that the font is chosen by the document's language: a
    # character present in one and absent in the other falls back to a system font
    # depending on whether the document happens to contain Thai.
    greek_names = th_greek.close_gaps(aeonik, weight_name, aeonik_path,
                                      label="4b")
    if greek_names:
        aeonik["OS/2"].ulUnicodeRange1 |= (1 << 7)      # Greek and Coptic

    # Step 5: Vertical metrics
    set_vertical_metrics(aeonik)

    # Step 6: Spec compliance — Coverage ordering + single-byte Mac cmap
    n_cov = sort_coverage(aeonik)
    n_mac = fix_mac_cmap(aeonik)
    print(f"     [6] Coverage tables re-sorted: {n_cov} | "
          f"Mac cmap codes >255 dropped: {n_mac}")

    # `glyf` renderers place an outline at (lsb - xMin), so a stale lsb silently
    # translates the whole glyph — Aeonik's BoldItalic '9' declares lsb 33 against
    # an xMin of 31.
    #
    # This step was briefly deleted on 2026-08-04 on the reasoning that CFF ignores
    # `hmtx` lsb, so a CFF output could not care. The reasoning was sound and the
    # premise was not checked: fontTools' glyf glyph set applies that same
    # (lsb - xMin) offset WHILE DRAWING, and convert_to_cff() draws every Thai glyph
    # through exactly that glyph set. Deleting the sync therefore fed a shifted
    # outline into the charstring — TH-Aeonik-BoldItalic's `ษ` counter collapsed
    # from 55.2 to 3.9, i.e. the loop filled in solid, and qc_th_fonts check 10
    # caught it. Keep the sync: it must run BEFORE the conversion, not because CFF
    # reads lsb but because the pen does.
    #
    # recalcBounds is also required here — glyphs built by TTGlyphPen carry no
    # bounds until asked, and both the sync and the conversion read xMin.
    glyf_table = aeonik["glyf"]
    hmtx = aeonik["hmtx"]
    shifted = 0
    for gn in aeonik.getGlyphOrder():
        glyph = glyf_table[gn]
        glyph.recalcBounds(glyf_table)
        advance, lsb = hmtx.metrics[gn]
        x_min = getattr(glyph, "xMin", 0)
        if lsb != x_min:
            hmtx.metrics[gn] = (advance, x_min)
            shifted += 1
    if shifted:
        print(f"     [6b] lsb re-synced to xMin on {shifted} glyph(s) — the CFF "
              f"pen draws through the (lsb - xMin) offset")

    # Step 7: put the CFF back — Aeonik's charstrings verbatim, Thai appended.
    # The harvested Greek names MUST be in this set. Anything absent from it is
    # taken from the pristine Latin CFF verbatim, so an outline written over an
    # existing name (uni2206, uni00B5) would be silently discarded and the v1 twin
    # would ship — the same trap uni0E3F fell into. See convert_to_cff's docstring.
    convert_to_cff(aeonik, latin_cff, thai_names | greek_names)
    assert_advance_single_source(aeonik)

    aeonik.save(str(output_path))

    size_kb = output_path.stat().st_size / 1024
    print(f"     Saved: {output_path.name} ({size_kb:.0f} KB)")

    # Step 8: the relationship half of the line-box assertion, measured on the
    # face that was actually written. Post-save on purpose — the mark clearance
    # pass and the baseline seat both move the shaped extents, so the only honest
    # place to measure them is the finished file.
    assert_thai_clears(output_path)

    # Step 9: Verify
    if out_dir == OUTPUT_DIR:
        verify_font(weight_name)

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build TH-Aeonik font family")
    parser.add_argument("--weights", default=None,
                        help="Comma-separated weights (default: all)")
    parser.add_argument("--mark-scale", type=float, default=None,
                        help="override th_thai_prep.MARK_SCALE (sweep knob for "
                             "scripts/solve_mark_scale.py)")
    parser.add_argument("--out-dir", default=None,
                        help="write elsewhere than assets/fonts/th-aeonik, so a "
                             "sweep does not overwrite the shipped faces")
    args = parser.parse_args()
    require_aeonik_source()
    out_dir = Path(args.out_dir) if args.out_dir else OUTPUT_DIR

    weights = WEIGHTS
    if args.weights:
        selected = [w.strip() for w in args.weights.split(",")]
        weights = {k: v for k, v in WEIGHTS.items() if k in selected}

    print("\n" + "=" * 70)
    print("  TH-AEONIK BUILD PIPELINE")
    print("  Aeonik (Latin) + Bai Jamjuree (Thai) = TH Aeonik")
    print("=" * 70)

    out_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for wn, af in weights.items():
        if build_font(wn, af, mark_scale=args.mark_scale, out_dir=out_dir):
            success += 1

    total = len(weights)
    print(f"\n{'=' * 70}")
    status = "PASS" if success == total else "FAIL"
    print(f"  {status}: {success}/{total} fonts built")
    print(f"  Output: {out_dir}")
    print(f"{'=' * 70}\n")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
