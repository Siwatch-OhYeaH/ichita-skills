#!/usr/bin/env python3
"""build_aeonik_semibold.py — synthesise the Aeonik SemiBold that CoType never drew.

READ THIS BEFORE USING THE OUTPUT ANYWHERE
------------------------------------------
**This face is NOT Aeonik.** Every other Latin glyph this repo ships is CoType's
own charstrings, byte for byte — `th_cff.convert_to_cff` exists specifically to
put them back untouched after the merge, and `win_latin_parity.py` is the
acceptance test for that invariant. This script breaks it deliberately, once,
because Siwatch asked for a SemiBold on 2026-08-07 and there is no source for
one.

What was ruled out first, measured, not assumed:

  * **No Aeonik SemiBold exists in either cut we hold.** Desktop v1.000 is
    Air/Thin/Light/Regular/Medium/Bold/Black; the v2.000 web cut is only
    Light/Regular/Bold.
  * **Interpolating Medium -> Bold fails.** 197 of 657 glyphs have incompatible
    point structures, `three` `five` `six` `dollar` `ampersand` `question`
    among them. The digits are in the broken set, which for a company whose
    documents are full of flow rates and tolerances is disqualifying on its own.

So the only route left is synthetic emboldening, and its cost is recorded in
§4c of docs/THAI-LATIN-FONT-ENGINEERING.md. The two things it gets wrong:

  1. **Counters overshoot.** The synthetic reaches Bold's tightest counter
     (97.7 at `e`) while carrying only SemiBold's stem. A drawn SemiBold would
     be near 108. It will read very slightly darker and tighter than a real one.
  2. **Fit is approximate.** changeWeight has no opinion about letterfit, so
     the advances are corrected here arithmetically (see WIDTH TARGET) rather
     than drawn. Kerning is inherited from Medium, whose pairs were fitted for
     Medium's sidebearings.

If CoType ever ships an Aeonik SemiBold — or a VARIABLE Aeonik, which would let
us instance a real 600 — replace this and delete the script. That is the fix,
not tuning the numbers here.

THE TARGETS, AND WHERE THEY COME FROM
-------------------------------------
Aeonik's real ladder, measured 2026-08-07 (th_metrics.stem over STEM_LATIN;
advance is the sum over "Handgloves 0123456789" per 1000 em):

    weight   class    stem   advance   counter e
    Medium     500   115.2     11398       118.2
    Bold       700   148.4     11634        97.7
    Black      900   183.6     11867        78.1

Between 500 and 700 that is 16.6 of stem and 118 of advance per 100 weight
units, so weight 600 sits at **stem 131.8, advance 11516**. Both are
interpolated from the faces either side rather than picked, and both are
asserted after the build.

USAGE
    python3 scripts/build_aeonik_semibold.py            # build + verify
    python3 scripts/build_aeonik_semibold.py --check    # verify only
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import th_metrics as tm  # noqa: E402
from th_thai_prep import _embolden  # noqa: E402
from th_cff import convert_to_cff  # noqa: E402
from build_th_aeonik import convert_to_glyf  # noqa: E402
from th_style_link import set_name  # noqa: E402

AEONIK = ROOT / "assets" / "fonts" / "aeonik"

# Sum of advances over this string, per 1000 em. A fixed string rather than a
# per-glyph average so the number is comparable to the ladder table above and
# reproducible by hand.
WIDTH_PROBE = "Handgloves 0123456789"

# Tolerances are what the probe can actually resolve: the stem probe reads in
# ~2 unit steps at 512 px/em, and the advance is a 21-glyph sum so 0.25% is
# under a unit per glyph.
STEM_TOL = 2.0
ADVANCE_TOL = 0.0025

# THE COUNTER IS THE ONE THING SYNTHESIS GETS WRONG AND CANNOT FIX.
#
# A drawn SemiBold would interpolate to ~108 at `e`. changeWeight spends counter
# roughly 1:1 with the stem it adds and has no idea it should be reopening the
# bowl, so the synthetic lands near 94 — TIGHTER than Bold's 97.7, which makes
# the counter ladder non-monotonic across Medium -> SemiBold -> Bold.
#
# Measured 2026-08-07 at the same stem, all three of FontForge's counter modes
# give the IDENTICAL counter (squish/retain/auto all 93.8): counter_type moves
# sidebearings, not counters. So this is not a knob that was left untuned, it
# is the ceiling of the technique.
#
# It is ~4% at ~0.06 px at 11 pt, which is why it ships. It is bounded rather
# than ignored: a change that makes it materially worse must fail the build
# instead of quietly darkening the face. This is NOT a red-on-purpose check —
# the bound is expected to pass, and check 6's three days of expected-red is
# exactly the pattern being avoided.
COUNTER_INVERSION_MAX = 0.10

# The faces to synthesise, what each is derived from, and where it must land.
#
# The filename still says "semibold" because SemiBold was the first and the name
# is referenced from CLAUDE.md, the engineering record, th_style_link,
# build_th_aeonik and the README. Renaming a module that a dozen files key on is
# exactly what broke twelve scripts on 2026-08-06; the docstring carries the
# correction instead.
#
# SemiBold GROWS from Medium; Book THINS from Regular, and the direction is not
# incidental. §4c: changeWeight spends counter roughly 1:1 with the stem it adds
# and never reopens a bowl, which is why the synthetic SemiBold lands tighter
# than Bold and needs COUNTER_INVERSION_MAX. Thinning runs the other way — it
# opens counters — so Book's counter ladder is monotonic by construction and
# needs no bound. Book is the safer synthesis of the two.
#
# Book targets, derived 2026-08-07 rather than chosen:
#   stem     Bai Jamjuree Regular is the whole point of the weight (Siwatch, the
#            2026-08-07 list), and it normalises to Thai stem 66.4. At
#            WEIGHT_RATIO 350 = .8975 that pins the Latin at 66.4/.8975 = 74.0.
#            NOT the arithmetic midpoint of Light and Regular, which is 69.3 —
#            distorting Bai to hit a round number would defeat the weight.
#   advance  74.0 sits 64% of the way from Light to Regular (58% for the
#            italic), so the advance is interpolated at that fraction.
#   wclass   350 is a declared sorting key for CSS and fontconfig, not a
#            measurement; nothing reads it against the stem.
SYNTH = {
    "SemiBold":       dict(base="Medium",        stem=131.8, advance=11516.0,
                           family="Aeonik SemiBold", wclass=600, panose=7),
    "SemiBoldItalic": dict(base="MediumItalic",  stem=131.8, advance=11516.0,
                           family="Aeonik SemiBold", wclass=600, panose=7),
    # Re-targeted from 74.0 after the first build measured out. THINNING SHRINKS
    # THE GLYPH: Aeonik-Book's x ink-top came out 504 against Regular's 510,
    # because changeWeight moves every edge inward, not just the vertical stems.
    # build_th_aeonik then scales the Thai to the LATIN'S X-HEIGHT (QC check 1),
    # so a 6-unit shorter x-height scaled Bai Regular down with it and the merged
    # Thai landed 64.5 instead of the 66.4 the weight is defined by.
    #
    # Book's rule is that the Thai is fixed and the Latin moves (see
    # th_thai_prep.BUILD_TABLE), so the Latin comes down to 64.5/.8975 = 71.9.
    # Advances re-interpolated at the new fraction of Light -> Regular.
    "Book":           dict(base="Regular",       stem=71.9,  advance=11129.0,
                           family="Aeonik Book", wclass=350, panose=4),
    "BookItalic":     dict(base="RegularItalic", stem=71.8,  advance=11079.0,
                           family="Aeonik Book", wclass=350, panose=4),
}
FACES = {k: v["base"] for k, v in SYNTH.items()}

# A glyph whose bounding box moves much further than the weight change can
# account for came back deformed, not emboldened. th_thai_prep._graft_outlines
# screens only Thai because Bai's Latin is discarded by the merge; here EVERY
# glyph is under the knife, so every glyph is screened.
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


def advance_sum(path_or_font):
    font = (TTFont(str(path_or_font)) if not isinstance(path_or_font, TTFont)
            else path_or_font)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] for c in WIDTH_PROBE) * 1000 / upem


PUA_BASE = 0xE000


def tag_unencoded(font):
    """Give every unencoded glyph a temporary Private Use codepoint.

    WHY. FontForge RENAMES glyphs on generate, and it derives the new name from
    the glyph's Unicode value: `uni2126` comes back as `Omega`, `summation` as
    `Sigma`, `a.ss01` as `a.salt`. Grafting by name therefore silently missed
    147 of Aeonik's 657 glyphs on the first build — every `.case` punctuation,
    every oldstyle and tabular figure, the `fi` and `fl` ligatures, and all four
    harvested Greek/math glyphs (µ ∆ Ω ∑). Those would have shipped at MEDIUM
    weight inside a SemiBold face, and `fi`/`fl` fire in ordinary text, so it
    would have been visible in the first paragraph anybody set.

    Two cheaper fixes were tried and measured, both worse:
      * strip the cmap first — FontForge then renames EVERYTHING by index, and
        656 of 657 became unmappable.
      * match by glyph order — FontForge inserts `.null` and
        `nonmarkingreturn`, and the index offset is not constant (measured
        offsets ranged -304..+5 across encoded glyphs).

    Tagging makes the naming a function we control: every glyph is encoded, so
    every glyph maps back by codepoint. Measured 656/656, a clean bijection.
    The tags live only in the throwaway file handed to FontForge.
    """
    cmap = font.getBestCmap()
    encoded = {g: cp for cp, g in cmap.items()}
    unencoded = [g for g in font.getGlyphOrder()
                 if g not in encoded and g != ".notdef"]
    if PUA_BASE + len(unencoded) > 0xF8FF:
        raise SystemExit(f"ERROR: {len(unencoded)} unencoded glyphs will not fit "
                         f"in the BMP Private Use Area")
    pua = {g: PUA_BASE + i for i, g in enumerate(unencoded)}
    for table in font["cmap"].tables:
        if table.isUnicode():
            for g, cp in pua.items():
                table.cmap[cp] = g
    return {**encoded, **pua}, pua


def untag(font, pua):
    for table in font["cmap"].tables:
        if table.isUnicode():
            for cp in pua.values():
                table.cmap.pop(cp, None)


def graft(base, bolder, delta, codepoints):
    """Take outlines and advances from `bolder`, keep every other table.

    `codepoints` is {base glyph name: codepoint} covering EVERY glyph, so the
    match survives FontForge's renaming. A glyph that cannot be resolved is
    counted and returned — never silently skipped, which is how the 147 got
    through the first time.
    """
    bg, bb = base["glyf"], bolder["glyf"]
    bolder_cmap = bolder.getBestCmap()
    slack = abs(delta) * 2 + 20
    grafted, rejected, unresolved = 0, [], []
    for gn in base.getGlyphOrder():
        cp = codepoints.get(gn)
        target = bolder_cmap.get(cp) if cp is not None else None
        if target is None or target not in bb.glyphs:
            if gn != ".notdef":
                unresolved.append(gn)
            continue
        b0 = _bounds(base, gn)
        b1 = _bounds(bolder, target)
        if b0 and b1:
            drift = max(abs(x - y) for x, y in zip(b0, b1))
            if drift > slack:
                rejected.append(gn)
                continue
        bg.glyphs[gn] = bb.glyphs[target]
        base["hmtx"].metrics[gn] = bolder["hmtx"].metrics[target]
        grafted += 1
    return grafted, rejected, unresolved


def scale_advances(font, k):
    """Widen every advance by `k`, splitting the gain across both sidebearings.

    changeWeight has no model of letterfit: "squish" holds the advance at the
    source weight, so the letters get fatter inside spacing drawn for a lighter
    face and the line reads cramped. Growing the advance and re-centring the
    outline is the arithmetic stand-in for what a designer would draw. It is
    approximate by construction — real spacing is per-glyph and contextual —
    which is why it is called out in the header rather than buried here.
    """
    glyf, hmtx = font["glyf"], font["hmtx"]
    moved = 0
    for gn in font.getGlyphOrder():
        adv, lsb = hmtx.metrics[gn]
        if adv <= 0:
            continue
        new_adv = round(adv * k)
        shift = (new_adv - adv) // 2
        if shift:
            g = glyf[gn]
            if g.numberOfContours > 0:
                g.coordinates.translate((shift, 0))
                g.recalcBounds(glyf)
            elif g.numberOfContours < 0:
                for comp in g.components:
                    comp.x += shift
        hmtx.metrics[gn] = (new_adv, lsb + shift)
        moved += 1
    return moved


def build_face(name, base_name=None, verbose=True):
    spec = SYNTH[name]
    base_name = base_name or spec["base"]
    src = AEONIK / f"Aeonik-{base_name}.otf"
    out = AEONIK / f"Aeonik-{name}.otf"
    if not src.exists():
        raise SystemExit(f"ERROR: {src} is missing")

    if verbose:
        print(f"\n  Aeonik-{name}  <- Aeonik-{base_name}")

    # The Greek/math build, NOT the pristine v1.000, and that is on purpose: a
    # synthesised weight must not be the one face in the family missing Δ μ Ω.
    # It is also why this script does not go through build_th_aeonik's
    # require_aeonik_source() — it is not merging, it is deriving a Latin face
    # from a Latin face.
    pristine_cff = TTFont(str(src))["CFF "]

    font = TTFont(str(src))
    convert_to_glyf(font)

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        codepoints, pua = tag_unencoded(font)
        glyf_src = work / f"{base_name}-glyf.ttf"
        font.save(str(glyf_src))
        untag(font, pua)
        if verbose:
            print(f"     tagged {len(pua)} unencoded glyphs into the PUA so "
                  f"FontForge's renaming stays reversible")

        # Solve the embolden rather than table it: the response is not linear
        # and changeWeight under-delivers, so a constant would be a guess.
        amount, got, tried = _solve_embolden(glyf_src, work, verbose, spec)
        if abs(got - spec["stem"]) > STEM_TOL:
            raise SystemExit(
                f"ERROR: {name} stem solve did not converge — best {got:.1f} "
                f"against {spec['stem']} (+/-{STEM_TOL}) after {tried} probes")

        bolder = TTFont(str(_embolden(glyf_src, amount, work,
                                      counter_type="squish")))
        n, rejected, unresolved = graft(font, bolder, amount, codepoints)
        bolder.close()
        if verbose:
            print(f"     grafted {n}/{len(font.getGlyphOrder())} outlines "
                  f"at +{amount:.1f}u")
            if rejected:
                print(f"     {len(rejected)} kept unweighted (deformed): "
                      f"{' '.join(rejected[:8])}")
        if unresolved:
            raise SystemExit(
                f"ERROR: {name} could not resolve {len(unresolved)} glyph(s) "
                f"through FontForge's renaming: {' '.join(unresolved[:12])}\n"
                f"They would ship at {base_name} weight. Fix the mapping "
                f"rather than letting them through.")

        before = advance_sum(font)
        k = spec["advance"] / before
        moved = scale_advances(font, k)
        if verbose:
            print(f"     advances x{k:.5f} on {moved} glyphs "
                  f"({before:.0f} -> {advance_sum(font):.0f}, "
                  f"target {spec['advance']:.0f})")

        convert_to_cff(font, pristine_cff, set(font.getGlyphOrder()),
                       label="cff", kind="all")

    _name_face(font, name)
    font.save(str(out))
    font.close()
    if verbose:
        print(f"     -> {out.name}")
    return out


def _solve_embolden(glyf_src, work, verbose, spec):
    """Secant search on the MEASURED stem, the same shape as solve_weight_table.

    The bracket has to straddle zero now that Book THINS its base. changeWeight
    delivers roughly 0.9 of a unit going up and only ~0.5 going down, so the
    negative side needs about twice the range to cover the same stem distance —
    hence -40..40 rather than the old 1..40.
    """
    target = spec["stem"]
    grow = spec["stem"] > 100          # SemiBold grows, Book thins
    probes = []
    for amount in ((10.0, 24.0) if grow else (-6.0, -20.0)):
        p = _embolden(glyf_src, amount, work, counter_type="squish")
        probes.append((amount, tm.stem(p, chars=tm.STEM_LATIN)))
    for _ in range(6):
        (a0, s0), (a1, s1) = probes[-2], probes[-1]
        best = min(probes, key=lambda t: abs(t[1] - target))
        if abs(best[1] - target) <= STEM_TOL:
            break
        if s1 == s0:
            break
        nxt = a1 + (target - s1) * (a1 - a0) / (s1 - s0)
        nxt = max(-40.0, min(40.0, round(nxt, 1)))
        if any(abs(nxt - a) < 0.05 for a, _ in probes):
            break
        p = _embolden(glyf_src, nxt, work, counter_type="squish")
        probes.append((nxt, tm.stem(p, chars=tm.STEM_LATIN)))
    best = min(probes, key=lambda t: abs(t[1] - target))
    if verbose:
        trail = "  ".join(f"{a:+.1f}->{s:.1f}" for a, s in probes)
        print(f"     stem solve (target {target}): {trail}")
    return best[0], best[1], len(probes)


def _name_face(font, name):
    """Name it, and say in the font itself that it is not CoType's drawing.

    The provenance is not decoration. Two directories of Aeonik with the same
    family name is what nearly went wrong on 2026-08-06, and a synthesised
    weight sitting in a family of authentic ones is the same hazard: anybody
    inspecting this file must be able to tell without asking.
    """
    spec = SYNTH[name]
    italic = name.endswith("Italic")
    style = name[:-6] if italic else name          # "SemiBold" / "Book"
    label = f"{style} Italic" if italic else style
    nt = font["name"]

    fields = {
        1: spec["family"],
        2: "Italic" if italic else "Regular",
        3: f"Aeonik-{name}-ICHITA-synthesised",
        4: f"{spec['family']}{' Italic' if italic else ''}",
        5: "Version 1.001; ICHITA synthesised weight — NOT a CoType drawing",
        6: f"Aeonik-{name}",
        16: "Aeonik",
        17: label,
        # nameID 10 is the description field a font inspector shows first.
        10: (f"Synthesised by ICHITA from Aeonik {spec['base']}: FontForge "
             f"changeWeight to stem {spec['stem']} with counters squished, then "
             f"advances scaled to {spec['advance']:.0f}/1000em. CoType did not "
             f"draw this weight. See scripts/build_aeonik_semibold.py."),
    }
    for nid, val in fields.items():
        set_name(nt, nid, val)
        set_name(nt, nid, val, pid=1, peid=0, lid=0)

    # sxHeight and sCapHeight are INHERITED FROM THE BASE and changeWeight moves
    # the ink they describe, so they must be re-measured or they lie. Measured
    # 2026-08-07: Aeonik-Book shipped sxHeight 510 over ink that tops out at 504.
    # It did not show on SemiBold because emboldening happened to leave Medium's
    # 512 intact, which is exactly the kind of accident that keeps a stale field
    # looking correct.
    os2 = font["OS/2"]
    for field, glyph in (("sxHeight", "x"), ("sCapHeight", "H")):
        b = _bounds(font, glyph)
        if b:
            setattr(os2, field, round(b[3]))
    os2.usWeightClass = spec["wclass"]
    os2.panose.bWeight = spec["panose"]
    os2.fsSelection = (1 << 0 | 1 << 7) if italic else (1 << 6 | 1 << 7)
    font["head"].macStyle = (1 << 1) if italic else 0
    if "CFF " in font:
        font["CFF "].cff.fontNames[0] = f"Aeonik-{name}"


def _check_ladder(ladder, rows, faults):
    """Stem and width must rise, counters must close, along one weight run."""
    prev = None
    for w in ladder:
        p = AEONIK / f"Aeonik-{w}.otf"
        if not p.exists():
            faults.append(f"Aeonik-{w}.otf is missing — cannot judge the "
                          f"ladder, and a missing file is not a pass")
            prev = None
            continue
        stem = tm.stem(p, chars=tm.STEM_LATIN)
        adv = advance_sum(p)
        ap, ch = tm.min_aperture(p, chars="aeog")
        rows.append(f"  {w:14s} stem {stem:6.1f}   advance {adv:7.0f}   "
                    f"counter {ap:5.1f} ({ch})")
        if prev:
            pw, ps, pa, pc = prev
            if stem <= ps:
                faults.append(f"{w} stem {stem:.1f} is not heavier than "
                              f"{pw} {ps:.1f}")
            if adv <= pa:
                faults.append(f"{w} sets NARROWER than {pw} ({adv:.0f} vs "
                              f"{pa:.0f}) — the width ladder is inverted, "
                              f"which is the defect synthesis causes")
            # Counters must CLOSE as the weight rises. The synthetic SemiBold
            # is the one known exception, so that single step is BOUNDED rather
            # than exempted; every other step is a hard fault. Book needs no
            # such bound: it THINS its base, and thinning opens counters.
            if ap > pc:
                inv = (ap - pc) / pc
                if (pw, w) == ("SemiBold", "Bold"):
                    rows.append(
                        f"  {'':14s} ^ counter inverts {inv:+.1%} here — the "
                        f"synthetic SemiBold cannot reopen a bowl. Bounded at "
                        f"{COUNTER_INVERSION_MAX:.0%}, §4c.")
                    if inv > COUNTER_INVERSION_MAX:
                        faults.append(
                            f"SemiBold counter {pc:.1f} is {inv:.1%} tighter "
                            f"than Bold's {ap:.1f}, past the "
                            f"{COUNTER_INVERSION_MAX:.0%} bound — it now reads "
                            f"darker than the weight above it")
                else:
                    faults.append(f"{w} counter {ap:.1f} is MORE open than "
                                  f"{pw}'s {pc:.1f} — counters must close as "
                                  f"the weight rises")
        prev = (w, stem, adv, ap)


def check(verbose=True):
    faults = []
    rows = []
    # Two ladders, one per synthesised weight, each running from the face below
    # it to the face above. Book is checked on Light->Book->Regular->Medium
    # because a fault there is a fault in the THINNING direction and the
    # SemiBold ladder cannot see it.
    ladders = [["Light", "Book", "Regular", "Medium"],
               ["Medium", "SemiBold", "Bold", "Black"]]
    for ladder in ladders:
        rows.append(" -> ".join(ladder))
        _check_ladder(ladder, rows, faults)

    for name, spec in SYNTH.items():
        p = AEONIK / f"Aeonik-{name}.otf"
        if not p.exists():
            faults.append(f"Aeonik-{name}.otf is missing")
            continue
        f = TTFont(str(p))
        stem = tm.stem(p, chars=tm.STEM_LATIN)
        adv = advance_sum(p)
        if abs(stem - spec["stem"]) > STEM_TOL:
            faults.append(f"{name} stem {stem:.1f}, want {spec['stem']} "
                          f"+/-{STEM_TOL}")
        if abs(adv - spec["advance"]) / spec["advance"] > ADVANCE_TOL:
            faults.append(f"{name} advance {adv:.0f}, want "
                          f"{spec['advance']:.0f} +/-{ADVANCE_TOL:.2%}")
        if f["OS/2"].usWeightClass != spec["wclass"]:
            faults.append(f"{name} usWeightClass {f['OS/2'].usWeightClass}, "
                          f"want {spec['wclass']}")
        v = f["name"].getDebugName(5) or ""
        if "synthesised" not in v:
            faults.append(f"{name} nameID5 does not declare its provenance: "
                          f"{v!r}")
        # A synthesised weight must not be the one face missing Greek/math.
        cmap = f.getBestCmap()
        missing = [hex(cp) for cp in (0x0394, 0x03BC, 0x03A9, 0x03A3, 0x2300)
                   if cp not in cmap]
        if missing:
            faults.append(f"{name} is missing Greek/math {missing}")
        f.close()

    if verbose:
        for r in rows:
            print(f"  {r}")
        print()
        if faults:
            print(f"FAIL — {len(faults)} fault(s)")
            for x in faults:
                print(f"  - {x}")
        else:
            print(f"OK — both ladders are monotonic in stem AND width, and all "
                  f"{len(SYNTH)} synthesised faces declare themselves in "
                  f"nameID5")
    return faults


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true", help="verify only")
    ap.add_argument("--weights", default=None,
                    help=f"comma-separated subset of {','.join(SYNTH)}")
    args = ap.parse_args()

    names = list(SYNTH)
    if args.weights:
        names = [w.strip() for w in args.weights.split(",")]
        unknown = [w for w in names if w not in SYNTH]
        if unknown:
            ap.error(f"unknown face(s): {', '.join(unknown)}")

    if not args.check:
        if shutil.which("fontforge") is None:
            print("ERROR: fontforge is not installed — it does the "
                  "emboldening, and there is no fallback.", file=sys.stderr)
            return 2
        print(f"Synthesising {', '.join(names)}. THESE ARE NOT COTYPE "
              f"DRAWINGS —\nsee the module docstring and §4c before shipping "
              f"anything that uses them.")
        for name in names:
            build_face(name)
        print("\nNow verifying what was written:\n")

    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
