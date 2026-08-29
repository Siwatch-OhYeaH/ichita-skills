#!/usr/bin/env python3
"""Solve th_thai_prep.BUILD_TABLE embolden values from the SHIPPED measurement.

Until 2026-08-04 these values were hand-set: change WEIGHT_RATIO, build, read
the stem, nudge the number, rebuild, repeat — per face, fourteen faces. That is
why the table carried stale entries that still passed (see the note on
CAPPED_STEM_RATIO in th_thai_prep).

It cannot be solved arithmetically, for three reasons the build itself
documents:

  * changeWeight UNDER-DELIVERS ON NEGATIVE AMOUNTS, roughly half the requested
    thinning reaching the outline, so the embolden->stem slope differs by sign.
  * the build RE-SOLVES THE SCALE FROM INK per weight, so nominal 0.914 lands
    anywhere in 0.905..0.941 and moves the result again.
  * _repair_collapsed_counters REVERTS glyphs that collapsed, and reverted
    glyphs drag the stem median DOWN — so past a point more embolden buys less
    weight AND worse counters.

So this measures the shipped font and iterates a secant step, which handles all
three without modelling any of them.

  python3 scripts/solve_weight_table.py --weights Bold,Regular
  python3 scripts/solve_weight_table.py --all
  python3 scripts/solve_weight_table.py --family TH-Slussen --all

It REPORTS a table and never edits th_thai_prep: the entries are pasted in by
hand so the documented trailing comment on each line stays under human control.
It does leave the built fonts in assets/fonts/ at the last iteration's values,
so rebuild the whole family from the committed table afterwards.

WEIGHT_RATIO is shared by both families, so changing it invalidates BOTH tables
— re-solve TH-Slussen too or its qc_th_fonts check 2 fails.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import th_thai_prep  # noqa: E402
from th_metrics import STEM_LATIN, STEM_THAI, min_aperture, stem  # noqa: E402
from th_thai_prep import APERTURE_FLOOR, WEIGHT_RATIO  # noqa: E402

# Probe resolution is 1000/512 = 1.95 units, so anything tighter than one step
# is noise, not accuracy. 2.0 is one step.
TOL = 2.0
MAX_ITER = 7

FAMILIES = {
    "TH-Aeonik": ("build_th_aeonik", "th-aeonik"),
    "TH-Slussen": ("build_th_slussen", "th-slussen"),
}


def measure(family, out_dir, weight):
    """(latin_stem, thai_stem, aperture, binding_glyph) of the TRIAL face.

    `out_dir` is a scratch directory, never `assets/fonts/`. This function used
    to read the shipped face because `solve()` used to build into the shipped
    directory — so a `--all` run replaced all 16 shipped outline faces with
    non-converged trials and left the last iteration on disk. Found 2026-08-07,
    after a solve made every font in `assets/fonts/th-aeonik/` show as modified
    in `git status` before a real build had been run.

    Two things were stale here and both made the solver unable to run at all:

      * `.ttf`. The merged families have shipped `.otf`/CFF since 2026-08-04
        (§6 — a merged font must carry its Latin source's outline format or
        Windows renders the Latin 16-20% lighter). The extension was never
        updated, so every call raised `cannot open resource`.
      * `{family}-{weight}`. The build key stopped being the filename on
        2026-08-06; th_style_link.FACES is the authority.

    A solver that cannot measure cannot solve, and this one is cited in
    th_thai_prep.BUILD_TABLE as the authority for every value in it.
    """
    import th_style_link
    stem_name = (th_style_link.FACES[weight]["file"] if family == "TH-Aeonik"
                 else f"{family}-{weight}")
    p = out_dir / f"{stem_name}.otf"
    if not p.exists():
        raise SystemExit(f"ERROR: {p} was not written — cannot measure, and a "
                         f"missing file must not read as a converged solve")
    ap, ch = min_aperture(p)
    return stem(p, STEM_LATIN), stem(p, STEM_THAI), ap, ch


def solve(family, out_dir, weight, wclass, build_font, weights_map,
          verbose=True):
    src, e = th_thai_prep.BUILD_TABLE[family][weight]
    ratio = WEIGHT_RATIO[wclass]
    hist = []          # (embolden, thai_stem)
    best = None        # (abs_err, embolden, stem, aperture, glyph)

    for it in range(MAX_ITER):
        th_thai_prep.BUILD_TABLE[family][weight] = (src, e)
        if not build_font(weight, weights_map[weight], out_dir=out_dir):
            print(f"  {weight}: BUILD FAILED at embolden {e:+.1f}")
            return None
        latin, thai, ap, ch = measure(family, out_dir, weight)
        target = ratio * latin
        err = thai - target
        # ap is None when NO glyph still has an enclosed counter — the light end,
        # where thinning legitimately opens the loops of ข ค ง. There is then
        # nothing for the floor to bind on, so it is satisfied, not violated.
        ok_ap = True if ap is None else ap >= APERTURE_FLOOR
        if verbose:
            aps = "  n/a" if ap is None else f"{ap:5.1f}"
            flag = "" if ok_ap else f"  APERTURE {ap:.1f} < {APERTURE_FLOOR}"
            print(f"  {weight:14s} it{it} e={e:+7.2f} thai={thai:6.1f} "
                  f"target={target:6.1f} err={err:+6.1f} aper={aps} "
                  f"{ch or '-'}{flag}")

        if ok_ap and (best is None or abs(err) < best[0]):
            best = (abs(err), e, thai, ap, ch, latin, target)

        if abs(err) <= TOL and ok_ap:
            break

        hist.append((e, thai))
        if not ok_ap:
            # Overshot the counter floor: retreat toward the last aperture-safe
            # point rather than continuing to chase the stem.
            e = e - max(2.0, abs(err) * 0.6)
            continue

        if len(hist) >= 2 and hist[-1][1] != hist[-2][1]:
            (e0, s0), (e1, s1) = hist[-2], hist[-1]
            slope = (s1 - s0) / (e1 - e0)
            if abs(slope) < 0.05:
                slope = 0.9 if err < 0 else 0.5
            step = -err / slope
        else:
            # First step: changeWeight delivers ~0.9 of a unit going up and
            # ~0.5 going down, in scaled stem units.
            step = -err / (0.9 if err < 0 else 0.5)
        step = max(-25.0, min(25.0, step))
        e = e + step

    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--family", default="TH-Aeonik", choices=list(FAMILIES))
    args = ap.parse_args()

    import importlib
    from qc_th_fonts import WCLASS

    family = args.family
    modname, subdir = FAMILIES[family]
    builder = importlib.import_module(modname)

    names = list(builder.WEIGHTS)
    if args.weights:
        names = [w.strip() for w in args.weights.split(",")]
    elif not args.all:
        ap.error("pass --weights or --all")

    print(f"family={family}  APERTURE_FLOOR={APERTURE_FLOOR}  TOL={TOL}")
    print(f"WEIGHT_RATIO={WEIGHT_RATIO}\n")

    # Trials go to scratch. `subdir` is now only used to name it, so a solve can
    # never touch assets/fonts/ — see measure().
    out_dir = Path(tempfile.mkdtemp(prefix=f"solve-{subdir}-"))
    print(f"trials -> {out_dir}\n")

    results = {}
    try:
        for w in names:
            # WCLASS is keyed on the roman name; an italic shares its class.
            base = w[:-6] if w.endswith("Italic") else w
            r = solve(family, out_dir, w, WCLASS[base], builder.build_font,
                      builder.WEIGHTS)
            if r:
                results[w] = r
            print()
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    print("=" * 72)
    print("SOLVED BUILD_TABLE entries (paste into th_thai_prep.BUILD_TABLE):\n")
    for w, (err, e, thai, aper, ch, latin, target) in results.items():
        src = th_thai_prep.BUILD_TABLE[family][w][0]
        cap = " CAP" if aper is not None and aper < APERTURE_FLOOR + 4 else ""
        aps = "n/a" if aper is None else f"{aper:.1f}"
        print(f'        "{w}":{" " * max(0, 14 - len(w))}("{src}",'
              f'{e:9.1f}),  # {latin:.1f} -> {thai:.1f}'
              f' (want {target:.1f}, aper {aps} {ch or "-"}){cap}')
    print()
    bad = [w for w, r in results.items() if r[0] > TOL]
    if bad:
        print(f"NOT CONVERGED within {TOL}: {', '.join(bad)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
