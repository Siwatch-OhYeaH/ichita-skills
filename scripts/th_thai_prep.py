#!/usr/bin/env python3
"""Prepare Bai Jamjuree for merging into a Latin family.

Two corrections are applied here that the earlier builds did not make, and
between them they are the root cause of every defect found in the 2026-08-02
manual QC:

1. SCALE. Bai's Thai is drawn to sit beside Bai's own Latin. Dropped unscaled
   into Aeonik or Slussen it is too big: ก is 558 units against an Aeonik
   x-height of 510, so Thai reads 9% larger than the Latin it shares a line
   with. Each family therefore gets its own factor, chosen so ก matches the
   Latin x-height exactly.

2. WEIGHT. Stem width is a property of the *source* weight, and Bai's weight
   ladder does not line up with Aeonik's or Slussen's. Bai Regular next to
   Aeonik Regular leaves Thai 18% too light. The right source for Aeonik
   Regular is Bai *Medium*; the correct pairing per weight is in BUILD_TABLE
   below, with any residual closed by synthetic emboldening.

   Corrected 2026-08-03: matching the Latin stem 1:1 is the WRONG target and
   it is what made Bold unreadable. See WEIGHT_RATIO and APERTURE_FLOOR.

The old build asserted the opposite of (1) — that merged Thai should be
pixel-identical to Bai — and passed. That test enforced the defect. See
compare_th_aeonik.py for what replaced it.

All stem figures are median horizontal run length across a mid-height band,
measured at 512 px/em; see scripts/measure_stems.py.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem

sys.path.insert(0, str(Path(__file__).parent))
from th_mark_scale import scale_thai_marks  # noqa: E402

ROOT = Path(__file__).parent.parent
BAI = ROOT / "assets" / "fonts" / "bai-jamjuree"

# ก height / Latin x-height. Aeonik x-height 510, Slussen 540, Bai ก 558.
THAI_SCALE = {
    "TH-Aeonik": 0.914,
    "TH-Slussen": 0.968,
}

# Extra scale applied to MARKS ONLY, on top of THAI_SCALE, so a Thai stack fits
# inside the Latin's own line box. Full reasoning and the transform are in
# scripts/th_mark_scale.py; the short version is that TH-Aeonik led 28.3% looser
# than Aeonik, Siwatch ruled out the two-font split, and one font has one `hhea`
# — so the Thai has to fit 1200 and the marks are the only slack left.
#
# SOLVE THIS, DO NOT GUESS IT. `scripts/solve_mark_scale.py` sweeps candidates
# and measures the resulting worst stack with thai_line_pitch, because the number
# cannot be derived: shrinking a mark makes the consonant a smaller obstacle, so
# th_mark_clearance's iterative lift re-settles and the stack height does not
# move linearly with the scale.
#
# 1.000 is the pre-2026-08-04 behaviour and leaves the box at 1540.
MARK_SCALE = {
    "TH-Aeonik": 1.000,
    "TH-Slussen": 1.000,
}

# Thai stem as a fraction of the Latin stem it sits beside, by usWeightClass.
#
# The 2026-08-02 build targeted 1.0 — Thai stem == Latin stem. That is wrong,
# and it is the whole reason Bold shipped unreadable. Thai carries enclosed
# loops (ก ถ ภ ศ ฃ ธ ฮ) where Latin carries none, so matching stems makes Thai
# read heavier than the Latin AND spends the counter budget on stem width.
#
# These figures are not invented. They are measured from families whose Thai
# and Latin were drawn together by one designer, at 512 px/em on 2026-08-03:
#
#   Sarabun        ExtraLight .931  Regular .915  Medium .911  Bold .897
#                  SemiBold   .885  ExtraBold .890
#   Leelawadee     Regular    .921  Bold    .887
#   Leelawadee UI  Regular    .921  Semilight .909
#   Tahoma         Regular    .959  Bold    .774
#
# Every one runs Thai lighter than its Latin, and every one widens the gap as
# the weight increases.
#
# REVISED 2026-08-03 (evening). The ladder used to track Sarabun's ratios
# directly. That was wrong for two reasons, and Siwatch saw both:
#
#  1. A RATIO IS ONLY MEANINGFUL AGAINST THE LATIN IT WAS DRAWN FOR. Sarabun's
#     .915 pairs its Thai with Sarabun's own Latin. Aeonik's Latin is a much
#     heavier Regular than either Sarabun's or Bai's — measured, Aeonik Regular
#     85.9 against Bai Regular 74.2, +15.8%, and Medium +20.4%. Borrowing
#     Sarabun's ratio and applying it to Aeonik's heavier Latin drove our Thai
#     to 80.1 where Bai's own Regular is 70.3: +13.9% bolder than the source.
#     Siwatch, 2026-08-03: "if you look at regular font between TH aeonik and
#     baijamjuree, ours TH aeonik is more bold than original one."
#
#  2. THE OLD LADDER ENDED IN A CLIFF, NOT A TAPER. Black is hard-capped at
#     .745 by APERTURE_FLOOR (see EXTREME_WEIGHTS) and cannot move. A ladder
#     that holds .915 to .895 and then drops to .745 at the top is not a taper.
#     It is why Bold and Black were 5.8 units apart in Thai — 0.09 px at 11 pt,
#     invisible — against 33.2 units in the Latin. Siwatch reported exactly
#     that: Thai Bold and Black look the same, the Latin pair does not.
#
# So the ladder now runs TOWARD the cap the heavy end is stuck at, which is the
# shape Tahoma has for the same reason (.959 Regular -> .774 Bold). Two
# consequences, both wanted:
#
#   * Regular Thai lands 74.3, only +5.7% over Bai's own 70.3 instead of
#     +13.9%. Lighter, deliberately not as light as Bai — Siwatch: "we may not
#     need to make it as light as the original to balance with the latin."
#   * Bold/Black separation goes 5.8 -> 21.7 units, 0.09 -> 0.32 px at 11 pt.
#
# The light end is unchanged: Air is a 7.8-unit hairline already and thinning
# it further would erase it.
#
# Third consequence, not designed for but worth knowing: every face except
# Black, BlackItalic and TH-Slussen-Bold is now reached by THINNING Bai rather
# than emboldening it. Thinning opens counters, so APERTURE_FLOOR stops binding
# almost everywhere, and each skipped FontForge round trip is one less chance to
# deform a mark (see _graft_outlines).
#  3. RE-FLATTENED 2026-08-04. The taper above was solved against the WRONG
#     COMPARISON, and Siwatch's two reports only look contradictory until you
#     name what each one compared:
#
#       2026-08-03 "ours TH aeonik is more bold than original one"
#                  -> merged Thai vs BAI JAMJUREE's Thai.
#       2026-08-04 "bold font of TH Aeonik thai is not balanced with latin
#                  thickness ... when type both thai and english in one line, I
#                  want them to have the same font thickness. It's fair to use
#                  the Aeonik (original) as benchmark."
#                  -> merged Thai vs AEONIK's Latin, on one line.
#
#     The second is the product requirement: the face exists to set Thai beside
#     Aeonik, and a reader sees the two scripts side by side, never our Thai
#     beside Bai's. So the Latin-on-the-same-line comparison governs, and the
#     ratio goes back to what families whose Thai and Latin were drawn together
#     hold for PERCEIVED equal weight — ~.89 (Sarabun Bold .897, Leelawadee
#     Bold .887). The taper had driven Bold to .766, which is the Tahoma
#     extreme, and Tahoma is the one reference this file already refuses to
#     follow.
#
#     Known and accepted consequence: Regular lands ~+11% over Bai's own
#     Regular, which is close to the +13.9% that drew the 2026-08-03 complaint.
#     That is now the INTENDED reading of the rule, not a regression — matching
#     Aeonik's heavier Latin necessarily means out-weighing Bai. If Siwatch
#     judges Regular too bold again, the fix is to re-open which benchmark
#     governs, NOT to taper the top back down and re-break Bold.
#
#     Black stays at .745. It is not a choice: 136.7 is Bai Bold's emboldening
#     ceiling under APERTURE_FLOOR, re-confirmed 2026-08-04 by measuring every
#     heavier Thai on the machine. Sarabun ExtraBold scales to stem 124.1 at
#     aperture 40.8 — ALREADY under the floor — so it buys 0.9 units of stem and
#     spends the whole counter budget. Bai Bold remains the best source. The
#     cost is that Bold (.89 -> ~134) and Black (~137) sit close again; Siwatch
#     accepted that trade and asked for an external heavier Thai for Black
#     (Kanit/Noto Sans Thai, neither present locally) as the separate fix.
#     350 (Book) is the taper's own value between 300 and 400, not a new
#     decision. Book is the one weight defined from the THAI side — its Latin
#     was synthesised to fit Bai Regular undistorted rather than the reverse —
#     so the ratio here is what pinned the Latin at stem 74.0, and changing it
#     would invalidate Aeonik-Book.otf rather than just re-solve a Thai.
#     800 (ExtraBold) is NOT the linear interpolation of 700 and 900, and the
#     difference is the whole point of the entry. Above Bold the Thai has 5.8
#     units of range left — Bold 130.9 to Black 136.7, which is Bai Bold's
#     emboldening ceiling under APERTURE_FLOOR — while the Latin climbs 148.4 to
#     183.6. Interpolating the RATIO (.8175) puts the Thai at 135.7, one unit
#     under Black, which is HALF A PROBE STEP: the two would measure as one
#     weight and could invert on rounding.
#
#     So 800 is set to split the available range evenly instead: .806 x 166.0 =
#     133.8, giving 2.9 units to each of Bold->ExtraBold and ExtraBold->Black.
#     That is the most gradual ladder the source admits, which is what Siwatch
#     asked for on 2026-08-09 — "I know thai font has limitation for heavier
#     size, so just let it gradually and maximum at black." It is still ~1.5
#     probe steps per rung, so the top three weights read as one Thai colour and
#     three Latin colours. Accepted, measured, and not a defect to re-open.
WEIGHT_RATIO = {100: 0.93, 200: 0.92, 300: 0.905, 350: 0.8975, 400: 0.89,
                500: 0.89, 600: 0.89, 700: 0.89, 800: 0.806, 900: 0.745}

# Minimum counter aperture, units/1000em: the widest circle that fits inside
# the tightest enclosed counter of the Thai consonants. This is the number that
# decides whether a loop survives as a loop or renders as a blob, and NOTHING
# measured it before 2026-08-03 — which is why a Bold with 7.8 units of
# aperture (0.11 px at 11 pt) passed the whole suite on its stem match alone.
#
# changeWeight grows outlines in every direction, so a counter bounded by two
# strokes loses ~1.2x the stem gain, then falls off a cliff as a tighter glyph
# crosses below the previous minimum. Measured on BaiJamjuree-Bold:
#
#   embolden    +0     +10     +20    +31.7
#   aperture  66.4    54.7    46.9     11.0   <- ฃ closes; ฮ was binding before
#
# The floor is what shipping Thai families refuse to go below at their heaviest:
# Sarabun ExtraBold 46.9, Leelawadee Bold 46.9. (Tahoma Bold reaches 39.1 and
# is famously heavy in Thai — not a model to follow.)
#
# 46.5, not a round 47.0, and the 0.5 matters. The probe resolves in steps of
# 1000/512 = 1.95 units, so the reference value 46.9 and the next step up 48.8
# are adjacent readings. A floor of 47.0 would fail a face measuring exactly
# what Sarabun ExtraBold measures, which is a mis-set constant rather than a
# font defect — TH-Aeonik-BlackItalic hit precisely that. 46.5 admits
# reference-level and still fails the next step down (44.9).
APERTURE_FLOOR = 46.5

# weight -> (Bai source file, embolden in unscaled Bai units)
#
# The embolden figure is the LESSER of what the two constraints allow:
#   1. WEIGHT_RATIO[weight] * latin_stem / scale - bai_stem
#   2. the largest value keeping the scaled aperture >= APERTURE_FLOOR
# Solved per face by measurement, not prediction; scripts/qc_th_fonts.py
# check 10 re-measures both on the shipped fonts.
#
# Aeonik ships 7 weights x roman/italic = 14 faces; Bai ships 6 x 2 = 12, and
# its ladder is narrower at BOTH ends. Bai's lightest (ExtraLight, stem 35.2)
# is far heavier than Aeonik Air (7.8) and Thin (23.4), and its heaviest (Bold,
# 134.8) is far lighter than Aeonik Black (183.6). Those four faces are
# therefore reached by thinning or emboldening past the source ladder, with the
# quality cost measured per weight — see EXTREME_WEIGHTS below.
#
# Values below |EMBOLDEN_FLOOR| are skipped, so those faces ship pristine Bai
# outlines — the best outcome available, since every FontForge round trip risks
# deforming a mark.
#
# The three aperture-capped faces carry ~3.5u less embolden than the constraint
# solve alone gives. The merge costs a further ~4 units of aperture that the
# solve cannot see, because the build re-solves the scale from ink per weight
# (Black lands on 0.9085, not the nominal 0.914) and then rounds coordinates to
# integers. Measured prepared -> shipped on 2026-08-03: Black 50.8 -> 46.9,
# Slussen Bold 46.9 -> 43.0. So the figures below are set from the SHIPPED
# aperture, which is the only one that matters.
# Re-solved 2026-08-03 (evening) for the revised WEIGHT_RATIO. The trailing
# comment on each line is the SHIPPED Latin stem the face has to match and the
# Thai stem the taper therefore asks for, so a value can be checked without
# re-running the solve. Only the three faces marked CAP embolden; the rest thin.
#
# Two things make these values unpredictable from the arithmetic alone, so they
# are set from the shipped measurement over one iteration:
#
#   * changeWeight UNDER-DELIVERS ON NEGATIVE AMOUNTS — roughly half the
#     requested thinning reaches the outline. TH-Slussen-SemiBold asks -20.7 to
#     move the stem the 8.3 units the taper wants. The outline change is still
#     only ~8 units, so this is compensation for the tool, NOT extra thinning,
#     and it carries none of the loop-opening risk a real -20 would.
#   * the build re-solves the scale from ink per weight, so nominal 0.914 lands
#     anywhere from 0.905 to 0.914 and shifts the result again.
#
# Black is +13.0, not the +14.9 the taper asks for, and this is measured rather
# than cautious: at +14.9 the shipped aperture is 43.0 — under the floor — and
# the stem comes out LOWER (134.8 vs 136.7), because _repair_collapsed_counters
# reverts the glyphs that collapsed and reverted glyphs drag the median down.
# More embolden buys less weight AND worse counters. Do not raise it.
BUILD_TABLE = {
    # Re-solved 2026-08-04 by scripts/solve_weight_table.py, which measures the
    # SHIPPED face and iterates a secant step instead of predicting the
    # embolden. Trailing comment is `shipped Latin stem -> shipped Thai stem
    # (target, counter aperture and the glyph that binds)`.
    #
    # CAP marks a face whose aperture is within 4 units of APERTURE_FLOOR, i.e.
    # one probe step from blobs. Only Black is CAP; it is Bai Bold's emboldening
    # ceiling, and that is the measured reason Thai Bold and Black cannot both be
    # balanced and distinct from this source — see WEIGHT_RATIO note 3.
    #
    # RE-SOLVED 2026-08-07, and the reason is a defect rather than a drift.
    # solve_weight_table.py could not open a single font from 2026-08-04 to
    # 2026-08-07 — it looked for `{family}-{weight}.ttf`, an extension left stale
    # by the CFF flip — so the values below were last set by hand while the
    # script that documents them as measured was raising `cannot open resource`
    # on every call. Three faces were solved against the ITALIC's Latin stem:
    # Light 54.7, Regular 87.9 and Bold 150.4 are Aeonik's italic figures; the
    # romans measure 52.7, 85.9 and 148.4. A target computed from a Latin ~2
    # units too heavy asks the Thai for ~2 units it should not have.
    #
    #   Regular  -8.4 -> -11.2   thai 79.1 -> 76.2   ratio .920 -> .887
    #   Bold     13.4 ->   8.1   thai 134.8 -> 130.9  ratio .908 -> .882
    #   Black    13.0 ->  15.2   thai 136.7 (same, the cap is unmoved)
    #
    # Bold is the one that mattered: at 13.4 it sat on APERTURE_FLOOR (46.9) to
    # buy stem it was never owed. The correct target frees 3.9 units of counter.
    "TH-Aeonik": {
        "Air":           ("BaiJamjuree-ExtraLight.ttf",      -27.2),  # 7.8 -> 7.3 (want 7.3, aper 113.3 ฆ)
        "Thin":          ("BaiJamjuree-ExtraLight.ttf",      -13.5),  # 23.4 -> 20.5 (want 21.6, aper 97.7 ฆ)
        "Light":         ("BaiJamjuree-Light.ttf",            -0.4),  # 52.7 -> 48.8 (want 47.7, aper 74.2 ฆ)
        # Added 2026-08-07. THE ONLY ENTRY THAT MUST STAY AT 0.0. Every other
        # face bends Bai to fit a Latin; Book is the reverse — Siwatch asked for
        # "Regular Bai Jamjuree thickness after normalize", so Bai Regular ships
        # UNDISTORTED and Aeonik-Book.otf was synthesised to stem 74.0 to sit
        # beside it. Emboldening this face would defeat the weight; if its ratio
        # ever misses, move the Latin.
        "Book":          ("BaiJamjuree-Regular.ttf",           0.0),
        "BookItalic":    ("BaiJamjuree-Italic.ttf",            0.0),
        "Regular":       ("BaiJamjuree-Medium.ttf",          -11.2),  # 85.9 -> 76.2 (want 76.5, aper 78.1 ฆ)
        "Medium":        ("BaiJamjuree-SemiBold.ttf",         -4.8),  # 115.2 -> 102.5 (want 102.6, aper 67.4 ฆ)
        # Added 2026-08-07. Bai BOLD thinned, not Bai SemiBold emboldened, and
        # that choice is measured rather than conventional. Both routes hit the
        # .89 target; they differ entirely in counter:
        #
        #   Bai SemiBold +15.2  -> thai 117.2  aperture 48.3  CAP
        #   Bai Bold     -10.0  -> thai 118.2  aperture 70.3
        #
        # 48.3 is 1.8 units off APERTURE_FLOOR on a weight LIGHTER than Bold,
        # which is absurd on its face — and the italic came out at 47.0, one
        # probe step from failing. Thinning opens counters, emboldening spends
        # them, so pairing one Bai step heavier and thinning is what the rest of
        # this table already does (Regular<-Medium, Medium<-SemiBold).
        "SemiBold":      ("BaiJamjuree-Bold.ttf",            -10.0),  # 130.9 -> 118.2 (want 116.5, aper 70.3 ฮ)
        "Bold":          ("BaiJamjuree-Bold.ttf",              8.1),  # 148.4 -> 130.9 (want 132.1, aper 50.8 ฮ)
        # Added 2026-08-09. Same source as Bold and Black — Bai Bold is the
        # heaviest Thai this family has, and 2026-08-04 measured every heavier
        # Thai on the machine to confirm none of them buys stem without going
        # under APERTURE_FLOOR. So all three of the top weights are one Bai face
        # at three embolden amounts, and the whole ladder above 700 lives in the
        # 7.1 units between Bold's +8.1 and Black's +15.2. SEED VALUE, replaced
        # by the solver below.
        "ExtraBold":     ("BaiJamjuree-Bold.ttf",             11.5),  # SEED
        "Black":         ("BaiJamjuree-Bold.ttf",             15.2),  # 183.6 -> 136.7 (want 136.8, aper 46.9 ฆ) CAP
        "AirItalic":     ("BaiJamjuree-ExtraLightItalic.ttf",-29.2),  # 7.8 -> 5.9 (want 7.3, no enclosed counter)
        "ThinItalic":    ("BaiJamjuree-ExtraLightItalic.ttf",-13.4),  # 23.4 -> 21.5 (want 21.6, aper 93.2 ฬ)
        "LightItalic":   ("BaiJamjuree-LightItalic.ttf",      -0.4),  # 54.7 -> 48.8 (want 49.5, aper 73.0 ฆ)
        "RegularItalic": ("BaiJamjuree-MediumItalic.ttf",     -9.5),  # 87.9 -> 77.1 (want 78.2, aper 74.6 ฆ)
        "MediumItalic":  ("BaiJamjuree-SemiBoldItalic.ttf",   -4.8),  # 115.2 -> 101.6 (want 102.6, aper 66.9 ฆ)
        "SemiBoldItalic": ("BaiJamjuree-BoldItalic.ttf",   -10.0),  # 132.8 -> 117.2 (want 118.2, aper 70.3 ฮ)
        "BoldItalic":    ("BaiJamjuree-BoldItalic.ttf",       10.6),  # 150.4 -> 132.8 (want 133.8, aper 50.8 ฮ)
        "ExtraBoldItalic": ("BaiJamjuree-BoldItalic.ttf",     13.5),  # SEED
        "BlackItalic":   ("BaiJamjuree-BoldItalic.ttf",       16.4),  # 183.6 -> 138.7 (want 136.8, aper 49.7 ษ) CAP
    },
    # Re-solved 2026-08-04 for the same WEIGHT_RATIO change; WEIGHT_RATIO is
    # shared, so leaving these at the taper's values would have failed check 2
    # on all four Slussen faces.
    "TH-Slussen": {
        "Regular":  ("BaiJamjuree-Medium.ttf",    -6.6),  # 95.7 -> 84.0 (want 85.2, aper 74.2 ฆ)
        "Medium":   ("BaiJamjuree-SemiBold.ttf",  -8.4),  # 117.2 -> 103.5 (want 104.3, aper 78.1 ฆ)
        "SemiBold": ("BaiJamjuree-Bold.ttf",      -5.8),  # 144.5 -> 127.0 (want 128.6, aper 70.3 ฮ)
        # NOT the solver's 29.7. Slussen's Latin Bold is 169.9, the heaviest
        # Latin either family has, and .89 of it (151.2) is past what Bai Bold
        # survives. Measured 2026-08-04, embolden -> (thai stem, aperture,
        # glyphs reverted to source weight by _repair_collapsed_counters):
        #
        #   +4.0  134.8  58.6  0      +18.0  144.5  46.9  1
        #   +12.0 138.7  50.8  0      +22.3  146.5  46.9  2
        #                             +29.7  152.3  49.4  5   <- hits the target
        #
        # A reverted glyph ships at Bai Bold's weight while its neighbours are
        # emboldened, so 29.7 buys the stem target by making ข ฃ ฆ ษ ฮ visibly
        # lighter than the rest of the alphabet — a defect the eye catches long
        # before a stem ratio does. 12.0 is the heaviest value that reverts
        # NOTHING and keeps aperture clear of the floor, so this face runs
        # measurably short of its .89 target.
        #
        # DONE 2026-08-07: check 2 moved from a 0.08 ratio band to 2.5 stem
        # units, and this face was the one the old band was hiding — a 0.073
        # ratio miss inside a 0.08 tolerance is a pass by luck, not by design.
        # It is now pinned in qc_th_fonts.CAPPED_STEM_RATIO at the measured
        # .8276 (140.6 units against a 151.2 target), so the shortfall is stated
        # as a number instead of absorbed by a wide bar.
        "Bold":     ("BaiJamjuree-Bold.ttf",      12.0),  # 169.9 -> 138.7 (want 151.2, aper 50.8 ฮ) SHORT
    },
}

# Weight changes below this many units are not worth a FontForge round trip:
# inside the stem probe's noise, and perturbing outlines for no visible gain.
EMBOLDEN_FLOOR = 2.0

# Faces reached by pushing past the end of Bai's ladder, and what it costs.
# Rewritten 2026-08-03 when APERTURE_FLOOR replaced the 1:1 stem target.
#
#   Thin  -11.3  clean; stem within ~1% of target.
#   Air   -27.2  structurally intact but hairline, and thinning opens the loops
#                of ข ค ง right out of existence (two contours -> one). That is
#                what those letters do as they get lighter, so it is correct,
#                but AirItalic ends with no enclosed counter at all.
#   Black +14.9  APERTURE-CAPPED. Aeonik Black's stem is 183.6 and a .89 taper
#                would ask for 163.4, but Bai Bold cannot be emboldened that far
#                without driving the counters under the floor. Black is the one
#                weight whose ratio is set BY the cap rather than by the taper:
#                0.745. Since 2026-08-03 evening WEIGHT_RATIO[900] states that
#                number outright instead of asking for .89 and recording the
#                shortfall elsewhere, so the ladder ends where it can actually
#                land. The alternative was the old +68.1, which produced 3.9
#                units of aperture: solid blobs. It is the same trade Tahoma
#                makes at Bold (0.774).
#   Slussen
#   Bold   +9.3  APERTURE-CAPPED for the same reason; ratio 0.775.
#
# Bold vs Black used to be the tightest call in the table, and it was too tight:
# both draw on Bai Bold, Bai has nothing heavier, and with the old near-flat
# ladder there were 5.8 units of stem between them — 0.09 px at 11 pt, which
# Siwatch correctly reported as no difference at all. It is not fixable from the
# Black end; Bai's ceiling and the aperture floor are both hard. It is fixable
# from the Bold end, which is what the revised taper does: Bold thins to 115.0
# and the pair opens to 21.7 units, 0.32 px. Check 6 asserts they stay distinct.
#
# So do not "restore" Bold toward the Latin to close the ratio gap. The gap is
# the mechanism that makes Black visible.
#
# These are real quality losses against an unreachable target, not regressions,
# and they are not silently accepted — qc_th_fonts check 10 pins each one.
EXTREME_WEIGHTS = {
    ("TH-Aeonik", "Air"): "hairline; Thai very faint at text sizes",
    ("TH-Aeonik", "AirItalic"): "hairline; loops open out entirely",
    ("TH-Aeonik", "ExtraBold"): "aperture-capped; Thai ~19% lighter, and within "
                                "1.5 probe steps of Bold and Black either side",
    ("TH-Aeonik", "ExtraBoldItalic"): "aperture-capped; Thai ~19% lighter",
    ("TH-Aeonik", "Black"): "aperture-capped; Thai ~26% lighter than the Latin",
    ("TH-Aeonik", "BlackItalic"): "aperture-capped; Thai ~26% lighter",
    ("TH-Slussen", "Bold"): "aperture-capped; Thai ~23% lighter than the Latin",
}

_FF_SCRIPT = """
import fontforge, sys
f = fontforge.open(sys.argv[1])
f.selection.all()
f.changeWeight(float(sys.argv[3]), "auto", 0, 0, sys.argv[4])
f.generate(sys.argv[2])
"""


def _embolden(src, amount, workdir, counter_type="auto"):
    """Thicken every stem by `amount` em units using FontForge.

    Returns the path to the emboldened file. FontForge rewrites the OpenType
    layout tables on generate, so the caller must take GPOS/GSUB from the
    pristine source and only the outlines from here.

    `counter_type` is FontForge's counter/sidebearing policy and "auto" is its
    own default, so the Thai builds behave exactly as before. It is exposed for
    build_aeonik_semibold.py, which needs "squish" — measured 2026-08-07 on
    Aeonik Medium +14, the two modes give the SAME stem (128.9) and the SAME
    tightest counter (97.7) and differ only in advance: auto 11930, squish
    11398. So the choice here is purely about letterfit, and squish is the one
    that leaves the advance somewhere a correction can start from.
    """
    out = workdir / (src.stem + f"-bold{amount:.0f}.ttf")
    script = workdir / "embolden.py"
    script.write_text(_FF_SCRIPT)
    r = subprocess.run(
        ["fontforge", "-lang=py", "-script", str(script),
         str(src), str(out), str(amount), counter_type],
        capture_output=True, text=True)
    if not out.exists():
        raise RuntimeError(f"FontForge embolden failed for {src.name}:\n"
                           f"{r.stdout}\n{r.stderr}")
    return out


def _bounds(font, gn):
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    if gn not in gs:
        return None
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        return None
    return bp.bounds


def _graft_outlines(base, bolder, delta=0.0):
    """Copy emboldened outlines into `base`, keeping base's layout tables.

    FontForge's generate() reflows GPOS/GSUB/GDEF, and Thai depends heavily on
    mark-attachment anchors that must stay exactly as Bai authored them. So the
    emboldened font is used purely as a source of `glyf` outlines and advances;
    every other table stays as the original shipped it.

    Thai glyphs whose bounding box moved much further than the weight change
    could account for are rejected and keep their original outline.
    `BaiJamjuree-ExtraLightItalic` thinned by 9.5 units came back with `๊`
    stretched from y659 down to y418 — 241 units — which dragged the mark below
    its own anchor, far enough that no amount of clearance correction could lift
    it off the consonant. That is why TH-Aeonik-ThinItalic shipped with a broken
    tone mark. A rejected glyph is slightly off-weight, which is invisible next
    to a mark that is visibly broken.

    Contour count was tried as a second signal and had to be dropped: it fires
    on normal weight change. Thinning closes the loop of `ข` `ค` `ง` and dozens
    of other consonants from two contours to one, which is what those letters
    are supposed to do as they get lighter. Screening on it rejected ~100 Thai
    glyphs per weight and left the consonants at the source weight, undoing the
    stem match this pipeline exists to make.
    """
    bg, bb = base["glyf"], bolder["glyf"]
    # changeWeight moves each edge by about `delta`; allow generous slack for
    # curve reconstruction before calling it a deformation.
    slack = abs(delta) * 2 + 20
    grafted, rejected = 0, []
    for gn in base.getGlyphOrder():
        if gn not in bb.glyphs:
            continue
        # Only Thai is checked. Bai's Latin is never copied into the merged
        # font — the Latin there comes from Aeonik or Slussen — so rejecting a
        # deformed `Aring` would cost a FontForge round trip to protect a glyph
        # that gets discarded. Screening everything also produced hundreds of
        # false rejections on accented composites, whose diagonals legitimately
        # grow more than `slack` under a heavy weight change.
        why = None
        if gn.startswith("uni0E"):
            b0, b1 = _bounds(base, gn), _bounds(bolder, gn)
            if b0 and b1:
                drift = max(abs(x - y) for x, y in zip(b0, b1))
                if drift > slack:
                    why = f"bbox moved {drift:.0f}u"
        if why:
            rejected.append(f"{gn}({why})")
            continue
        bg.glyphs[gn] = bb[gn]
        if gn in bolder["hmtx"].metrics:
            base["hmtx"].metrics[gn] = bolder["hmtx"].metrics[gn]
        grafted += 1
    return grafted, rejected


def _repair_collapsed_counters(font, src, target, workdir, verbose=True):
    """Revert Thai glyphs whose counter did not survive embolden + rounding.

    `_graft_outlines` screens on bounding-box drift, which cannot see this: a
    counter closes without the bbox moving at all. Measured on
    BaiJamjuree-BoldItalic +10.5 (2026-08-03), aperture in units/1000em:

        ษ   source 70.4   emboldened 61.0   emboldened+scaled  3.9   <-- gone
        ฮ   source 66.4   emboldened 54.7   emboldened+scaled 50.8
        ฆ   source 66.5   emboldened 56.9   emboldened+scaled 51.4

    The emboldened outline is not deformed — ษ keeps its 3 contours and grows
    9.7% in area, indistinguishable from its neighbours. It is fragile to
    *rounding*: two edges land within a unit of each other once coordinates are
    scaled by 0.914 and snapped to integers, and the loop fills. That is why
    this screen has to render and measure rather than inspect the outline, and
    why it has to run after scale_upem rather than before.

    A reverted glyph carries the source weight, so it is slightly light against
    its neighbours. That is invisible next to a consonant rendering as a blob —
    the same trade `_graft_outlines` already makes.

    LIMITATION, measured on BlackItalic ฮ: for a composite glyph this reverts
    the composite record only, and its components stay emboldened, so the
    recovery is partial (ฮ 47.0 -> 50.8 rather than to the source's 59.6). It is
    enough to clear the floor and it is honest about what it did — the printed
    figure is the pre-merge measurement, and the merge costs a further ~4 units
    to rounding. Decomposing the composite first would recover the rest, at the
    cost of losing the component structure the mark anchors depend on.
    """
    from th_metrics import LOOP_THAI, apertures

    prepared = workdir / "prepared-probe.ttf"
    font.save(str(prepared))
    got = apertures(prepared, LOOP_THAI)

    ref = TTFont(str(src))
    scale_upem(ref, target)
    ref["head"].unitsPerEm = 1000
    ref_path = workdir / "unweighted-probe.ttf"
    ref.save(str(ref_path))
    ref_ap = apertures(ref_path, LOOP_THAI)

    cmap = font.getBestCmap()
    glyf, ref_glyf = font["glyf"], ref["glyf"]
    repaired = []
    for ch in LOOP_THAI:
        a, r = got.get(ch), ref_ap.get(ch)
        if a is None or r is None or a >= APERTURE_FLOOR or r <= a:
            continue
        gn = cmap.get(ord(ch))
        if gn is None or gn not in ref_glyf.glyphs:
            continue
        glyf.glyphs[gn] = ref_glyf[gn]
        if gn in ref["hmtx"].metrics:
            font["hmtx"].metrics[gn] = ref["hmtx"].metrics[gn]
        repaired.append(f"{ch}({a:.0f}->{r:.0f})")
    ref.close()
    if verbose and repaired:
        print(f"     [0d] Counter collapse repaired on {len(repaired)} glyph(s), "
              f"reverted to source weight: {' '.join(repaired)}")
    return repaired


def _glyph_height(font, ch):
    from fontTools.pens.boundsPen import BoundsPen
    gn = font.getBestCmap().get(ord(ch))
    if not gn:
        return None
    bp = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[gn].draw(bp)
    return None if not bp.bounds else bp.bounds[3] - bp.bounds[1]


def prepare_bai(family, weight, latin_font=None, verbose=True, mark_scale=None):
    """Return a Bai TTFont scaled (and emboldened) ready to merge into `family`.

    The scale is applied with scaleUpem so that GPOS anchors, mark attachment
    points and advances all move with the outlines. Scaling glyphs alone would
    leave every tone mark anchored at its original height — the marks would
    detach from the consonants they sit on.

    `mark_scale` overrides MARK_SCALE[family] and exists so
    scripts/solve_mark_scale.py can sweep candidates without editing the constant.
    """
    scale = THAI_SCALE[family]
    if mark_scale is None:
        mark_scale = MARK_SCALE[family]
    bai_file, embolden = BUILD_TABLE[family][weight]
    src = BAI / bai_file
    if not src.exists():
        raise FileNotFoundError(src)

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        font = TTFont(str(src))
        if abs(embolden) >= EMBOLDEN_FLOOR:
            # Negative thins. Aeonik Air and Thin sit below Bai's lightest
            # weight, so there is no source to copy — the stems have to come
            # down.
            bolder = TTFont(str(_embolden(src, embolden, workdir)))
            n, rejected = _graft_outlines(font, bolder, embolden)
            bolder.close()
            if verbose:
                verb = "Embolden" if embolden > 0 else "Thin"
                warn = EXTREME_WEIGHTS.get((family, weight))
                print(f"     [0a] {verb} {embolden:+.1f}u on {n} outlines "
                      f"({bai_file})"
                      + (f"  ** {warn}" if warn else ""))
                if rejected:
                    print(f"          {len(rejected)} glyph(s) kept unweighted, "
                          f"deformed by changeWeight: {' '.join(rejected[:8])}"
                          + (" ..." if len(rejected) > 8 else ""))
        elif verbose:
            print(f"     [0a] Weight delta {embolden:+.1f}u skipped, below "
                  f"floor ({bai_file})")

        # Solve the scale against the emboldened outline rather than trusting
        # the table constant. Emboldening grows the glyph box — it pushes the
        # outline outward on every side — so a fixed factor overshoots exactly
        # where the embolden is largest. Measured on the first build: Bold came
        # out at ก = 105% of x-height, Slussen Bold 108%, while the lighter
        # weights landed on target. Measuring here makes the scale exact for
        # every weight and leaves THAI_SCALE as documentation of the nominal.
        if latin_font is not None:
            xh = _glyph_height(latin_font, 'x')
            kh = _glyph_height(font, 'ก')
            if xh and kh:
                scale = xh / kh
                if verbose:
                    print(f"     [0b] Scale solved from ink: x-height {xh:.0f}"
                          f" / ก {kh:.0f} = {scale:.4f} "
                          f"(nominal {THAI_SCALE[family]})")

        # scaleUpem to `scale * 1000` then declare the em back at 1000: the
        # coordinates shrink by `scale` while the em stays the size the Latin
        # font expects.
        target = round(1000 * scale)
        scale_upem(font, target)
        font["head"].unitsPerEm = 1000
        if verbose:
            print(f"     [0c] Thai scaled x{target/1000:.3f} "
                  f"(upem {target} -> declared 1000)")

        # Must run here: the collapse is caused by rounding at this scale, so it
        # is not visible before scale_upem.
        if abs(embolden) >= EMBOLDEN_FLOOR:
            _repair_collapsed_counters(font, src, target, workdir, verbose)

        # Last, so it sees final-size marks — and before the merge, which puts it
        # ahead of th_mark_clearance.raise_upper_marks() as that pass requires.
        scale_thai_marks(font, mark_scale, verbose)
        normalise_thai_tracking(font, latin_font, verbose)
        return font


# Thai and Latin probes for the tracking pass. Spacing glyphs only — the Thai
# set is deliberately the bases and spacing vowels, because marks carry no
# advance and would only dilute the sum.
THAI_ADV_PROBE = "กขคงจดตนบปผพภมยรลวสหอาเแโใไะำ"
LATIN_ADV_PROBE = "Handgloves 0123456789"

# Thai advance sum / Latin advance sum, measured on TH-Aeonik Regular 2026-08-07.
# Siwatch framed the rule: "if we take Regular as standard, the lighter font face
# like Book, light, air, should have total width of sentence in order."
THAI_ADV_RATIO = 1.3857
TRACKING_MAX = 0.08     # a correction past this is a defect upstream, not tracking


def normalise_thai_tracking(font, latin_font, verbose=True):
    """Put the Thai advance ladder in weight order, by tracking alone.

    WHY THIS EXISTS. The scale above is solved so ก's HEIGHT matches the Latin
    x-height, and nothing controls the WIDTH — it just inherits that factor. Each
    face pairs with a different Bai weight, emboldened or thinned by a different
    amount, so each needs a different compensating scale (Air .9509, Light .9086,
    Book .8889, Regular .9341) and the Thai widths come out in whatever order
    those accidents produce. Measured 2026-08-07 on one mixed line: Air's Thai ran
    WIDER than Light's and Book's, and SemiBold's wider than Bold's, while the
    Latin column was perfectly monotonic. Siwatch saw it on the page first.

    WHY ADVANCE AND NOT OUTLINE. Scaling the Thai horizontally would fix the
    widths and thicken every vertical stem by the same percentage — Book's Thai
    would go 64.0 to 67.8 and fail check 2. Weight is the constraint that costs
    the most to get right here, so the width correction must not touch it. That
    leaves tracking: the ink is untouched and only the advances move.

    Marks are skipped because they are zero-advance; scaling zero is a no-op, but
    saying so is cheaper than wondering. Outlines are NOT shifted, so glyph-space
    GPOS anchors stay valid and the whole correction reads as even tracking.
    """
    if latin_font is None:
        return
    hm, cmap = font["hmtx"], font.getBestCmap()
    lat_hm, lat_cmap = latin_font["hmtx"], latin_font.getBestCmap()
    lat_upem = latin_font["head"].unitsPerEm

    thai = sum(hm[cmap[ord(c)]][0] for c in THAI_ADV_PROBE if ord(c) in cmap)
    lat = sum(lat_hm[lat_cmap[ord(c)]][0] for c in LATIN_ADV_PROBE
              if ord(c) in lat_cmap) * 1000 / lat_upem
    if not thai or not lat:
        return
    k = (THAI_ADV_RATIO * lat) / thai
    if abs(k - 1.0) > TRACKING_MAX:
        raise SystemExit(
            f"ERROR: Thai tracking correction is {k:.4f}, past the "
            f"{TRACKING_MAX:.0%} bound. That is not a spacing problem — the "
            f"scale or the Bai pairing is wrong upstream. Do not widen this.")

    moved = 0
    for gn in font.getGlyphOrder():
        adv, lsb = hm[gn]
        if adv <= 0:                       # marks, and .notdef-likes
            continue
        hm[gn] = (round(adv * k), lsb)
        moved += 1
    if verbose:
        after = sum(hm[cmap[ord(c)]][0] for c in THAI_ADV_PROBE if ord(c) in cmap)
        print(f"     [0e] Thai tracking x{k:.4f} on {moved} advances "
              f"(Thai/Latin {thai / lat:.4f} -> {after / lat:.4f}, "
              f"want {THAI_ADV_RATIO})")


def fix_thai_gdef(font):
    """Give every Thai glyph an explicit GDEF class.

    Bai Jamjuree leaves its spacing vowels — า ะ ำ เ แ โ ใ ไ ๆ — at GDEF class 0
    (unassigned) and only classifies the combining marks. Every shipping Thai
    font checked (Leelawadee, Leelawadee UI, Tahoma, Noto Looped Thai) declares
    them BASE.

    It matters because Uniscribe's Thai engine reads GDEF to decide what may act
    as a base when it validates a syllable. A spacing vowel with no class is not
    a base as far as that validation is concerned, so an isolated or repeated
    'าาาา' is rejected and will not type. HarfBuzz infers the class from Unicode
    and hides the problem, which is why this survived every Linux-side test.

    Class is taken from the Unicode general category, not a hand-written list:
    Mn/Me -> MARK, everything else in the Thai block -> BASE.
    """
    import unicodedata
    from fontTools.ttLib.tables import otTables

    if "GDEF" not in font:
        return 0, 0
    gdef = font["GDEF"].table
    if gdef.GlyphClassDef is None:
        gdef.GlyphClassDef = otTables.GlyphClassDef()
        gdef.GlyphClassDef.classDefs = {}
    cd = gdef.GlyphClassDef.classDefs

    cmap = font.getBestCmap()
    n_base = n_mark = 0
    for cp, gn in cmap.items():
        if not (0x0E00 <= cp <= 0x0E7F):
            continue
        want = 3 if unicodedata.category(chr(cp)) in ("Mn", "Me") else 1
        if cd.get(gn) != want:
            cd[gn] = want
            if want == 1:
                n_base += 1
            else:
                n_mark += 1
    return n_base, n_mark


def _circle(pen, cx, cy, r):
    """Approximate a circle with four quadratic segments."""
    k = r * 1.0
    pen.moveTo((cx + r, cy))
    pen.qCurveTo((cx + k, cy + k), (cx, cy + r))
    pen.qCurveTo((cx - k, cy + k), (cx - r, cy))
    pen.qCurveTo((cx - k, cy - k), (cx, cy - r))
    pen.qCurveTo((cx + k, cy - k), (cx + r, cy))
    pen.closePath()


def add_dotted_circle(font, x_height):
    """Synthesise U+25CC if the font lacks it.

    The shaper substitutes a dotted circle as a placeholder when a mark appears
    with no base to attach to. Bai ships none, so an orphaned vowel or tone mark
    has nothing to render against and simply vanishes. Leelawadee, Tahoma and
    Noto Looped Thai all carry one.

    Drawn here rather than copied: the only U+25CC available locally are in
    licensed Windows system fonts, and lifting an outline out of those into a
    redistributed binary is not ours to do.
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    cmap = font.getBestCmap()
    if 0x25CC in cmap:
        return False

    # Proportions matched against Leelawadee rendered at 90 px: a larger ring
    # also drags any attached mark upward, because the mark anchors off the
    # base's height, so an oversized placeholder misrepresents where the real
    # mark will sit.
    name = "uni25CC"
    r_ring = x_height * 0.48
    r_dot = x_height * 0.058
    cy = x_height * 0.50
    advance = int(r_ring * 2 + r_dot * 4)
    cx = advance / 2

    import math
    N_DOTS = 14
    pen = TTGlyphPen(None)
    for i in range(N_DOTS):
        a = math.pi * 2 * i / N_DOTS
        _circle(pen, cx + r_ring * math.cos(a), cy + r_ring * math.sin(a),
                r_dot)
    glyph = pen.glyph()

    order = font.getGlyphOrder()
    if name not in order:
        order.append(name)
        font.setGlyphOrder(order)
        font["glyf"].glyphOrder = order
    font["glyf"].glyphs[name] = glyph
    font["hmtx"].metrics[name] = (advance, 0)

    for table in font["cmap"].tables:
        # Unicode subtables only; the Mac format-6 table is deliberately
        # restricted to codes <= 255 for Uniscribe compliance.
        if table.platformID == 3 or (table.platformID == 0
                                     and table.format in (4, 12)):
            if table.cmap is not None:
                table.cmap[0x25CC] = name

    if "GDEF" in font and font["GDEF"].table.GlyphClassDef is not None:
        font["GDEF"].table.GlyphClassDef.classDefs[name] = 1  # BASE
    return True


def ink_bounds(font, glyphs=None):
    """(ymin, ymax) over every glyph's ink, including shaping-only variants."""
    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    lo = hi = None
    for gn in (glyphs or font.getGlyphOrder()):
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds:
            continue
        if lo is None or bp.bounds[1] < lo:
            lo = bp.bounds[1]
        if hi is None or bp.bounds[3] > hi:
            hi = bp.bounds[3]
    return lo, hi


if __name__ == "__main__":
    fam = sys.argv[1] if len(sys.argv) > 1 else "TH-Aeonik"
    print(f"{fam}  scale {THAI_SCALE[fam]}")
    for w in BUILD_TABLE[fam]:
        f = prepare_bai(fam, w)
        lo, hi = ink_bounds(f)
        print(f"  {w:<15} ink {lo:>7.0f} .. {hi:>7.0f}")
        f.close()
