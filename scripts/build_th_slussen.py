#!/usr/bin/env python3
"""
Build TH-Slussen font family — unified pipeline.

Merges Slussen (Latin) + Bai Jamjuree (Thai) into TH-Slussen with complete
OpenType support for Thai text shaping on Windows.

OUTPUT IS CFF (`.otf`), NOT TrueType, reversing the 2026-08-02 format decision.
The full reasoning and the DirectWrite measurements are in scripts/th_cff.py,
which both builders share. Slussen-specific point: Slussen carries **2712 hint
operators across 1068 glyphs**, all of which the `glyf` flip discarded and which
taking its CFF table wholesale restores. Aeonik has zero, so it lost nothing
there — this family is the one that actually paid for the flip, exactly as the
2026-08-01 post-mortem predicted it would be "the single most likely place this
change is noticed".

Pipeline steps:
  0. Convert the Latin base from CFF to `glyf` — the intermediate working format
     for the merge only; step 7 puts the CFF back
  1. Copy Thai glyphs + variants from Bai Jamjuree (glyf outlines, verbatim)
  2. Union GPOS/GDEF/GSUB from Bai Jamjuree onto Slussen's own (mark positioning)
  3. Apply metadata — RIBBI naming, OS/2
  4. Set OS/2 ulUnicodeRange/ulCodePageRange Thai bits (Windows shaping)
  4b. Greek/math coverage via scripts/th_greek.py — for Slussen this is only the
     Σ and ⌀ aliases; Slussen v1 already ships Δ, μ and Ω
  5. Vertical metrics — ONE box carried by hhea, sTypo AND usWin
  6. Sort GSUB/GPOS Coverage tables + clean Mac cmap (Uniscribe compliance)
  7. Swap `glyf` back to CFF — Slussen's charstrings verbatim, Thai appended
  8. Verify — Thai cmap, Latin match, GPOS, OS/2 bits, metrics

Sources:
  Latin: Slussen OTF (OneDrive path preferred, fallback assets/fonts/slussen/)
  Thai:  Bai Jamjuree (local assets preferred, fallback system fonts)

Line box: hhea = sTypo = usWin = 1233/-369/0 = 1602, from 2026-08-05. ONE box in
  all three metric sets, sized to what the Thai measured out at (need 1527 +
  margin 75) rather than to Slussen's own. Unifying the three is the whole
  cross-platform strategy: which field a renderer consults is not fixed — Word
  takes CFF pitch from usWin — so the font yields 1602 whichever one is read.
  usWin is NOT an ink-containing clip box any more; the ink is allowed outside,
  exactly as Tahoma's and Segoe UI's are. See the long note above ASCENT.

Acceptance test: scripts/compare_th_slussen.py — checks Thai against the LATIN
it shares a line with (x-height, stem weight, ink containment). The previous
test asserted Thai was pixel-identical to Bai Jamjuree, which is the unscaled,
weight-mismatched state this pipeline exists to correct.

Usage:
  python3 build_th_slussen.py                    # Build all 4 weights
  python3 build_th_slussen.py --weights Bold,Regular  # Build specific weights

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

# Source directories
SLUSSEN_ONEDRIVE = Path("/mnt/c/Users/OhYeaH/OneDrive/Documents/Slussen/Slussen")
SLUSSEN_LOCAL = ASSETS / "fonts" / "slussen"
BAI_LOCAL = ASSETS / "fonts" / "bai-jamjuree"
BAI_SYSTEM = Path.home() / ".local" / "share" / "fonts"
OUTPUT_DIR = ASSETS / "fonts" / "th-slussen"

# fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1

# Two boxes, two purposes — see the long note in build_th_aeonik.py for the
# measurements. Short version: the LINE box (hhea/sTypo) sets baseline pitch and
# is NOT required to contain the ink; the CLIP box (usWin) bounds what GDI will
# draw and must contain all of it. Thai marks overflow the line box in every
# Thai font shipped (Bai Jamjuree 1250 vs 1552 of ink, Leelawadee UI 1330,
# Tahoma 1207) and Word renders them intact.
#
# Slussen's own 1074/-272/166 was restored here. Raising it to 1280/-590 to
# "contain the ink" bought nothing and cost 24% of extra leading.
#
# Every weight shares these, otherwise bolding a word changes the line height.
#
# ---------------------------------------------------------------------------
# 2026-08-05: THE FULL PARITY TREATMENT. Box 1625 -> 1602, and usWin unified.
# ---------------------------------------------------------------------------
#
# Siwatch chose the consistent rule over the cheap fix. TH-Slussen now gets the
# same RULE as TH-Aeonik — box = the Thai's measured need + margin, with hhea,
# sTypo and usWin all carrying it — which is NOT the same NUMBER. Slussen's Thai
# is taller, so 1602 where Aeonik lands at 1537. "Follows the Aeonik decision"
# has been misread as "takes Aeonik's box" before; it means the rule.
#
# The usWin half is the important half, and it was a live latent defect rather
# than a tidiness issue. Until now the built .otf carried usWin 1390/590 = 1980
# against a 1625 line box, from the era when usWin was an ink-containing clip box.
# Word leads CFF faces off usWin, and this family ships CFF since 2026-08-04 — so
# installing it would have had Word lead TH Slussen at 1980, a silent +21.7% that
# has nothing to do with the outlines and nothing to do with any decision anyone
# took. The old .ttf hid it: the glyf branch ignores usWin entirely, which is why
# the installed font measured 1627 and looked fine. A FORMAT FLIP RELOCATES THE
# SPACING CONTROL — see win_latin_parity.word_line_box for the branch table.
#
# ---------------------------------------------------------------------------
# THE SPLIT, measured across all four faces (scripts/thai_line_pitch.py):
# ---------------------------------------------------------------------------
#
#   worst UPPER stack  1185  on TH-Slussen-Bold
#   worst LOWER tail    354  on TH-Slussen-Regular
#   envelope           1539  ->  1602 leaves 63 units of slack
#
# The two constraints land on DIFFERENT FACES and all four share one box, so the
# split is sized to the family envelope, not to a face.
#
# How the slack is spent differs from TH-Aeonik's, and the reason is worth stating
# because the rule is the same and only the binding constraint changed. Aeonik's
# frame (1000/-200) could be grown symmetrically to 1537 and still clear the Thai
# on both sides, so it was — the Latin stays optically centred. Slussen's frame is
# usWin 1262/-334 = 1596 (usWin, because that is what Word leads a CFF face off,
# not its hhea 1512 with a 166 gap). Growing THAT symmetrically to 1602 gives
# 1265/-337, and 337 is below the Thai's 354 — the Thai binds on the bottom, so
# the Latin cannot stay centred.
#
# Where the Latin-symmetric split is blocked, the slack goes over the Thai
# envelope in proportion to each side's demand: 1185/1539 and 354/1539 of 63.
#
#   ascent  1185 + 48 = 1233   (48 spare above the worst stack)
#   descent  354 + 15 =  369   (15 spare below the worst tail)
#
# Cost to the Latin: its baseline sits 29 units — 0.43 px at 11 pt — higher in the
# line than in Slussen itself, with 35 units more below. Negligible, and it is the
# direction that gives the Thai room rather than taking it.
#
# CONFIRM IN WORD after install: if the Latin reads high, these 63 units can be
# redistributed without touching the box. The box is the decision; the split is a
# measurement and is re-derivable.
ASCENT, DESCENT, LINEGAP = 1233, -369, 0        # 1602; Slussen's own usWin is 1596

# LINEGAP stays 0 and must: usWin has no lineGap field, so hhea == sTypo == usWin
# is only expressible with the gap folded into the ascent and descent. This is why
# Slussen's own 166-unit gap does not survive into the merged face.

# Minimum the Thai needs, from scripts/thai_line_pitch.py: worst face (SemiBold)
# 1527 of shaped ink extent plus the 75-unit margin.
#
# 1603 -> 1625 on 2026-08-03 (evening), and NOT because anything got heavier —
# the taper thinned SemiBold by 20 units. A thinner consonant is a smaller
# obstacle, so th_mark_clearance's iterative lift settles the mark HIGHER before
# it clears the 72 target, and the shaped stack grows 22 units taller. The line
# box follows the ink, not the weight. 1625 -> 1602 on 2026-08-05 is the same
# effect in reverse plus the removal of the leftover headroom: the box is now
# exactly need + margin. Re-run thai_line_pitch.py --check after any rebuild; this
# number moves whenever the clearance pass does.
REQUIRED_PITCH = 1602

# The margin folded into REQUIRED_PITCH — thai_line_pitch.MARGIN, Leelawadee UI's
# own spare, about one pixel at 11 pt / 96 dpi.
MARGIN_UNITS = 75

# usWin is the THIRD COPY OF THE LINE BOX, not a clip box sized to the ink.
#
# Was 1390/590 = 1980, sized to contain the measured static ink (-535..+1255,
# deepest TH-Slussen-SemiBold:uni0E38.small, highest TH-Slussen-Bold:Aringacute).
# That premise is retired for the same reason it was retired on TH-Aeonik: usWin
# is not a clip bound in DirectWrite-era Word — Tahoma and Segoe UI both draw well
# outside their own and neither clips — and it IS the spacing control for a CFF
# face. A usWin wider than the line box is not headroom, it is extra leading.
WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT


def assert_line_box(latin_src):
    """Assert the line box: THE NUMBER, and its RELATIONSHIP to Slussen's.

    Twin of build_th_aeonik.assert_line_box(), and the same both-halves discipline
    — a number is reviewable on sight, a relationship catches a source change.
    The Thai relationship half is assert_thai_clears(), per face, post-build.
    """
    pitch = ASCENT - DESCENT + LINEGAP
    if pitch != REQUIRED_PITCH:
        raise SystemExit(
            f"     !! line box {pitch} is not the documented {REQUIRED_PITCH} — "
            f"that is the box the Thai measured out at (thai_line_pitch.py). Fix "
            f"ASCENT/DESCENT/LINEGAP, and if the Thai really needs a different box "
            f"now, change REQUIRED_PITCH with it and say why.")
    if (WIN_ASCENT, -WIN_DESCENT) != (ASCENT, DESCENT):
        raise SystemExit(
            f"     !! usWin {-WIN_DESCENT}..{WIN_ASCENT} is not the line box "
            f"{DESCENT}..{ASCENT} — this family ships CFF and Word leads a CFF "
            f"face off usWin, so a wider usWin IS extra leading")
    h = latin_src["hhea"]
    o = latin_src["OS/2"]
    upem = latin_src["head"].unitsPerEm
    latin_hhea = round((h.ascender - h.descender + h.lineGap) * 1000 / upem)
    latin_win = round((o.usWinAscent + o.usWinDescent) * 1000 / upem)
    print(f"     [5] line box {pitch} (Thai needs {REQUIRED_PITCH} = ink "
          f"{REQUIRED_PITCH - MARGIN_UNITS} + margin {MARGIN_UNITS}) vs Slussen's "
          f"usWin {latin_win} — {pitch / latin_win - 1:+.1%}. Same RULE as "
          f"TH-Aeonik, not the same number (Siwatch 2026-08-05). Slussen's hhea is "
          f"{latin_hhea}, which is NOT what Word leads a CFF face off.")


def assert_thai_clears(output_path):
    """box >= this face's own measured Thai requirement. The relationship half.

    Twin of build_th_aeonik.assert_thai_clears(); see it for why this is measured
    on the saved file, per face, rather than predicted from a metric field.
    """
    try:
        from thai_line_pitch import required_pitch
    except ImportError as exc:                       # pragma: no cover
        raise SystemExit(
            f"     !! cannot import thai_line_pitch ({exc}) — the Thai clearance "
            f"half of the line-box assertion cannot run, and this build must not "
            f"report a pass without it. Use the system python3.")

    r = required_pitch(str(output_path))
    pitch = ASCENT - DESCENT + LINEGAP
    spare = pitch - r["required"]
    if spare < 0:
        raise SystemExit(
            f"     !! line box {pitch} is {-spare:.0f} units BELOW what this face "
            f"needs ({r['required']:.0f} = shaped ink {r['need']:.0f} + margin "
            f"{MARGIN_UNITS}). Two consecutive Thai lines will overlap by "
            f"{-spare - MARGIN_UNITS:.0f} units at Single spacing. Re-derive with "
            f"scripts/thai_line_pitch.py; do NOT lower the margin.")
    if ASCENT < r["top"]:
        raise SystemExit(
            f"     !! ascent {ASCENT} is below this face's worst upper stack "
            f"{r['top']:.0f} — re-split ASCENT/DESCENT.")
    if -DESCENT < -r["bottom"]:
        raise SystemExit(
            f"     !! descent {-DESCENT} is below this face's worst lower tail "
            f"{-r['bottom']:.0f} — re-split ASCENT/DESCENT.")
    print(f"     [8] Thai clearance: box {pitch} >= needs {r['required']:.0f} "
          f"(ink {r['need']:.0f} + margin {MARGIN_UNITS}), spare {spare:+.0f}; "
          f"ascent {ASCENT} >= worst stack {r['top']:.0f}, descent {-DESCENT} >= "
          f"worst tail {-r['bottom']:.0f}")

# Weight mapping: output_name -> slussen_file
# Latin source only. Thai pairing lives in th_thai_prep.BUILD_TABLE: matching
# by weight name put Bai Regular next to Slussen Regular and left Thai 25%
# lighter than the Latin beside it.
WEIGHTS = {
    "Regular":  "Slussen-Regular.otf",
    "Medium":   "Slussen-Medium.otf",
    "SemiBold": "Slussen-Semibold.otf",
    "Bold":     "Slussen-Bold.otf",
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

# Cubic -> quadratic error bound, in font units. Deliberately NOT a tuning knob:
# 1.0, 0.5, 0.1 and 0.001 were all measured to produce byte-identical rasters.
# The residual Latin difference is FreeType's CFF engine versus its TrueType
# engine, not curve approximation.
CU2QU_MAX_ERR = 0.5

SKIP_GLYPHS = {".notdef", ".null", "NULL", "nonmarkingreturn", "CR"}


def convert_to_glyf(font):
    """Re-express Slussen's CFF outlines as `glyf`, in place.

    Must run BEFORE any Thai is added, so Slussen keeps its own glyph IDs and
    _union_ot() stays valid verbatim.

    Unlike Aeonik, Slussen IS hinted — 2-6 stem hints per Latin glyph. Those are
    CFF-only and are discarded here; no TrueType instructions replace them. That
    is the accepted cost of making Thai bit-identical to Bai Jamjuree, and it is
    the one thing about this family that needs looking at on Windows at small
    sizes, where grid-fitting matters.
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

    # Without this the file keeps the 'OTTO' tag and consumers reject it —
    # FreeType reports "SFNT font table missing", naming the symptom not the cause.
    font.sfntVersion = "\000\001\000\000"

    del font["CFF "]
    for tag in ("FFTM", "VORG"):
        if tag in font:
            del font[tag]

    print(f"     [0] CFF -> glyf: {len(glyf.glyphOrder)} Latin glyphs "
          f"(cu2qu max_err={CU2QU_MAX_ERR}; Slussen's CFF stem hints dropped)")


def _copy_glyph(target_font, bai_font, bai_glyph_name, target_name, verbatim_ok):
    """Append one Bai Jamjuree glyph, verbatim where possible.

    Verbatim copying is where pixel-identical Thai comes from. A composite may
    only be copied verbatim if every component it names is also coming from Bai;
    otherwise the name resolves against the *Latin* font and the glyph is
    silently rebuilt out of the wrong parts. Measured on Slussen: 291 glyphs
    copied, 135 composite, 180 component references colliding (uni1EAE -> A,
    uni1EB6 -> dotbelowcomb, ...). All 8 Thai composites are translate-only and
    reference only Bai glyphs, so Thai stays verbatim.
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


def copy_thai_glyphs(slussen_font, bai_font):
    """Copy Thai glyphs from BaiJamjuree into the (now glyf-based) Slussen.

    Returns the set of names written, which step 7 needs to decide which glyphs
    must NOT keep Slussen's own charstring — see th_cff.convert_to_cff().
    """
    bai_cmap = bai_font.getBestCmap()
    if not bai_cmap:
        print("     !! No cmap in Bai Jamjuree")
        return set()

    have = set(slussen_font.getGlyphOrder())

    # Cmap-mapped Thai codepoints (U+0E01-0E7F)
    thai_mappings = {
        cp: gn for cp, gn in bai_cmap.items() if 0x0E01 <= cp <= 0x0E7F
    }
    renamed = {gn: f"uni{cp:04X}" for cp, gn in thai_mappings.items()}
    verbatim_ok = {
        gn for gn in bai_font.getGlyphOrder()
        if gn not in SKIP_GLYPHS and (gn in renamed or gn not in have)
    }

    written = set()
    added = 0
    for cp, bai_gn in sorted(thai_mappings.items()):
        if _copy_glyph(slussen_font, bai_font, bai_gn, f"uni{cp:04X}", verbatim_ok):
            added += 1
            written.add(f"uni{cp:04X}")

    glyphs = slussen_font["glyf"].glyphs
    for table in slussen_font["cmap"].tables:
        if hasattr(table, "cmap") and table.cmap is not None:
            for cp in thai_mappings:
                tn = f"uni{cp:04X}"
                if tn in glyphs:
                    table.cmap[cp] = tn

    # Add ALL remaining Bai glyphs (variants + non-Thai needed for GPOS/GSUB integrity)
    extra = 0
    for gn in bai_font.getGlyphOrder():
        if gn in glyphs or gn in SKIP_GLYPHS:
            continue
        if _copy_glyph(slussen_font, bai_font, gn, gn, verbatim_ok):
            extra += 1
            written.add(gn)

    slussen_font["maxp"].numGlyphs = len(slussen_font.getGlyphOrder())

    # Glyph names during the `glyf` stage: post 3.0 stores none and `glyf` has no
    # charset to fall back on, so every name would read glyph00001 for the rest of
    # the pipeline. Step 7 restores 3.0 once the CFF charset can supply them.
    slussen_font["post"].formatType = 2.0
    slussen_font["post"].extraNames = []
    slussen_font["post"].mapping = {}
    slussen_font["post"].glyphOrder = slussen_font.getGlyphOrder()

    print(f"     [1] Glyphs: {added} Thai cmap + {extra} extra (GPOS/GSUB)")
    return written


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
    """One box, carried by all three metric sets. See assert_line_box().

    Until 2026-08-05 this raised if the ink escaped usWin, on the premise that
    usWin is a clip box that must contain every outline. That premise is retired:
    usWin is the third copy of the LINE box, the ink is allowed outside it, and
    Thai marks are drawn outside it on purpose — Tahoma overflows its own by 246
    and Segoe UI by 379, and neither clips in Word. The assertion that replaces it
    is usWin == the line box, in assert_line_box(), because for a CFF face a usWin
    wider than the line box is not headroom, it is silent extra leading.
    """
    os2 = font["OS/2"]
    hhea = font["hhea"]

    lo, hi = _ink_bounds(font)

    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASCENT, DESCENT, LINEGAP
    hhea.ascent, hhea.descent, hhea.lineGap = ASCENT, DESCENT, LINEGAP
    os2.usWinAscent = WIN_ASCENT
    os2.usWinDescent = WIN_DESCENT
    os2.fsSelection |= USE_TYPO          # bit 7 — prefer the sTypo set

    over_up, over_dn = max(0, hi - ASCENT), max(0, -lo + DESCENT)
    print(f"     [5] Metrics: line(hhea=sTypo=usWin)={ASCENT}/{DESCENT}/{LINEGAP} "
          f"({ASCENT - DESCENT + LINEGAP}) "
          f"ink {lo:.0f}..{hi:.0f} (draws outside the box by "
          f"{over_up:.0f}/{over_dn:.0f}, expected — Segoe UI overflows by 379)")


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

    # 1. Latin geometry preserved (H, a, o).
    #
    # Segment-by-segment comparison is meaningless now that the merged font is
    # quadratic and Slussen is cubic — it reports CHANGED on a perfect build.
    # Compare what must survive the conversion instead: advance width and
    # control box. Visual fidelity is compare_th_slussen.py's job, not this
    # smoke check.
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
                pm, ps = ControlBoundsPen(gs_m), ControlBoundsPen(gs_s)
                gs_m[mg].draw(pm)
                gs_s[ag].draw(ps)
                box_ok = (pm.bounds is None) == (ps.bounds is None) and (
                    pm.bounds is None
                    or all(abs(x - y) <= 1 for x, y in zip(pm.bounds, ps.bounds)))
                if not (box_ok and gs_m[mg].width == gs_s[ag].width):
                    latin_ok = False
                    failures.append(
                        f"Latin '{name}' CHANGED (box {pm.bounds} vs {ps.bounds}, "
                        f"width {gs_m[mg].width} vs {gs_s[ag].width})")
        checks.append(f"Latin={'OK' if latin_ok else 'FAIL'}")
    else:
        checks.append("Latin=SKIP(src not found)")

    # 2. usWin must EQUAL the line box, not cover the ink.
    #
    # This check used to assert usWin >= the ink, from the era when usWin was read
    # as a clipping box. Inverted 2026-08-05: this family ships CFF, Word leads a
    # CFF face off usWin, so any usWin wider than the line box is silent extra
    # leading — 1980 against a 1625 box would have led TH Slussen +21.7% loose.
    # The ink is allowed outside; it is reported here, not asserted.
    head = font["head"]
    win_ok = (os2.usWinAscent == ASCENT and os2.usWinDescent == -DESCENT)
    checks.append(f"winAsc={os2.usWinAscent}(ink {head.yMax:+})")
    checks.append(f"winDes={os2.usWinDescent}(ink {head.yMin:+})")
    if not win_ok:
        failures.append(f"usWin {os2.usWinAscent}/{os2.usWinDescent} != the line "
                        f"box {ASCENT}/{-DESCENT} — Word leads a CFF face off "
                        f"usWin, so this is extra leading, not headroom")

    # 3. hhea is the box every weight must share, and it must equal sTypo AND
    # usWin. It is NOT required to contain the ink — Thai marks are drawn outside
    # it on purpose. Conflating box with ink is what inflated this family to
    # 1280/-590 and added 24% of leading to every Slussen document.
    hhea_ok = (hhea.ascent == ASCENT and hhea.descent == DESCENT
               and hhea.lineGap == LINEGAP)
    checks.append(f"hhea={hhea.ascent}/{hhea.descent}({'OK' if hhea_ok else 'FAIL'})")
    if not hhea_ok:
        failures.append(f"hhea mismatch: {hhea.ascent}/{hhea.descent}/{hhea.lineGap}"
                        f" != {ASCENT}/{DESCENT}/{LINEGAP}")

    # 4. sTypo must agree with hhea, so the pitch does not depend on renderer.
    typo_ok = (os2.sTypoAscender == ASCENT and
               os2.sTypoDescender == DESCENT and
               os2.sTypoLineGap == LINEGAP)
    checks.append(f"sTypo={os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap}"
                  f"({'OK' if typo_ok else 'FAIL'})")
    if not typo_ok:
        failures.append("sTypo mismatch: must equal hhea")

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

def build_font(weight_name, slussen_file, bai_file=None):
    """Build a single TH-Slussen weight."""
    print(f"\n  === {weight_name} ===")

    slussen_path = find_slussen(slussen_file)
    if not slussen_path:
        print(f"     !! Slussen not found: {slussen_file}")
        return False

    bai_src, embolden = BUILD_TABLE["TH-Slussen"][weight_name]
    print(f"     Latin: {slussen_path}")
    print(f"     Thai:  {bai_src}  (scale {THAI_SCALE['TH-Slussen']}, "
          f"embolden +{embolden:.1f}u)")

    slussen = TTFont(str(slussen_path))
    # Read the line box off the Latin before anything is merged into it.
    assert_line_box(slussen)
    # Scaled to the Latin x-height and weight-matched before any glyph is
    # copied, so GPOS anchors and the ink assertion all see final-size Thai.
    bai = prepare_bai("TH-Slussen", weight_name, latin_font=slussen)

    if "CFF " not in slussen:
        print(f"     !! Slussen is not CFF format — cannot merge CFF glyphs")
        return False

    # A pristine, untouched copy of Slussen's CFF table — read from the file a
    # second time so no mutation below can reach it. Step 7 puts this back, which
    # is what carries Slussen's 2712 hint operators through to the shipped font.
    latin_cff = TTFont(str(slussen_path))["CFF "]

    output_path = OUTPUT_DIR / f"TH-Slussen-{weight_name}.otf"

    # Step 0: CFF -> glyf, while the glyph set is still purely Latin. Intermediate
    # working format for the merge only; step 7 swaps the CFF back in.
    convert_to_glyf(slussen)

    # Step 1: Copy Thai glyphs (glyph by glyph)
    thai_names = copy_thai_glyphs(slussen, bai)

    # Step 2: Merge GPOS/GDEF/GSUB (Thai mark positioning)
    merge_ot_tables(slussen, bai)

    # Step 3: Metadata (naming, fsSelection, CFF fontName)
    apply_metadata(slussen, weight_name)

    # Step 3b: Uniscribe needs an explicit GDEF class on every Thai glyph,
    # and a dotted circle to hang orphaned marks on. Bai supplies neither,
    # which is why an isolated or repeated 'า' would not type.
    n_base, n_mark = fix_thai_gdef(slussen)
    from fontTools.pens.boundsPen import BoundsPen as _BP
    _gs = slussen.getGlyphSet(); _bp = _BP(_gs)
    _gs[slussen.getBestCmap()[ord('x')]].draw(_bp)
    _xh = _bp.bounds[3] - _bp.bounds[1]
    added = add_dotted_circle(slussen, _xh)
    print(f"     [3b] GDEF: {n_base} Thai -> BASE, {n_mark} -> MARK | "
          f"U+25CC dotted circle: {'synthesised' if added else 'already present'}")

    # Step 3c: put the Thai back on the Latin baseline. The stem match
    # uses FontForge changeWeight, which grows the outline downward as
    # well as sideways, so a flat-bottomed consonant that Bai drew at
    # y=0 ends up below the Latin, worse the bolder the weight. Rigid
    # translation of the bases and their anchors; the marks follow.
    seat_thai_on_baseline(slussen)

    # Step 3d: see build_th_aeonik.py. TH-Slussen-Bold measured a median
    # clearance of 12/1000 em before this ran.
    raise_upper_marks(slussen)

    # Step 4: Thai OS/2 bits
    set_thai_bits(slussen)

    # Greek/math coverage. Slussen v1 already ships Δ, μ and Ω, so in practice this
    # only aliases Σ -> ∑ and ⌀ -> Ø. `harvest_family` is passed so the resolver
    # cannot graft an AEONIK outline into Slussen if a future Slussen source ever
    # drops one of the three — every outline-level check would stay green if it did.
    greek_names = th_greek.close_gaps(slussen, weight_name, slussen_path,
                                      label="4b", harvest_family="Slussen")
    if greek_names:
        slussen["OS/2"].ulUnicodeRange1 |= (1 << 7)      # Greek and Coptic

    # Step 5: Vertical metrics (Slussen line box, Thai-safe clipping box)
    set_vertical_metrics(slussen)

    # Step 6: Spec compliance — Coverage ordering + single-byte Mac cmap
    n_cov = sort_coverage(slussen)
    n_mac = fix_mac_cmap(slussen)
    print(f"     [6] Coverage tables re-sorted: {n_cov} | "
          f"Mac cmap codes >255 dropped: {n_mac}")

    # See the twin in build_th_aeonik.py for why this must stay. Short version:
    # fontTools' glyf glyph set applies the (lsb - xMin) offset while DRAWING, and
    # convert_to_cff() draws through that glyph set, so a stale lsb feeds a shifted
    # outline into the charstring. Deleting this collapsed TH-Aeonik-BoldItalic's
    # `ษ` counter from 55.2 to 3.9. Slussen needs it more, not less: it carries
    # 42-49 disagreeing glyphs per weight against Aeonik's 0-2.
    glyf_table = slussen["glyf"]
    hmtx = slussen["hmtx"]
    shifted = 0
    for gn in slussen.getGlyphOrder():
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

    # Step 7: put the CFF back — Slussen's charstrings verbatim, Thai appended.
    convert_to_cff(slussen, latin_cff, thai_names | greek_names)
    assert_advance_single_source(slussen)

    slussen.save(str(output_path))

    size_kb = output_path.stat().st_size / 1024
    print(f"     Saved: {output_path.name} ({size_kb:.0f} KB)")

    # The relationship half of the line-box assertion, on the face that was
    # actually written — the clearance pass and the baseline seat both move the
    # shaped extents, so the finished file is the only honest place to measure.
    assert_thai_clears(output_path)

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
    for wn, sf in weights.items():
        ok = build_font(wn, sf)
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
