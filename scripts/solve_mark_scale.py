#!/usr/bin/env python3
"""Solve th_thai_prep.MARK_SCALE against a target line box, by measurement.

The number cannot be derived in closed form. Shrinking a mark makes the consonant
below it a smaller obstacle, so `th_mark_clearance.raise_upper_marks()` re-settles
its iterative lift and the shaped stack does not shrink linearly with the scale —
the same second-order effect that made the Slussen line box GROW when the weight
taper thinned it (see `taper-a-ladder-to-its-hard-cap`).

So this sweeps candidate scales through the REAL builder into a temp directory and
measures the result with `thai_line_pitch.required_pitch()`. Driving the actual
build rather than reimplementing it is deliberate: this repo has twice scored a
green suite against artifacts its own code could not produce
(`rebuild-before-trusting-qc`).

Reading the output:

    need      worst upper stack + |worst lower tail|, 1/1000 em
    required  need + MARGIN, i.e. what the line box must be. MARGIN is 75 —
              Leelawadee UI's own spare, and about one pixel at 11 pt / 96 dpi.
    verdict   FITS when required <= target.

A scale that only fits with MARGIN removed is reported as TIGHT, not FITS. Zero
margin means two consecutive Thai lines touch exactly, which is a defect at any
rasterisation.

WHAT THIS CANNOT DECIDE. The four tone marks ่ ้ ๊ ๋ differ only by small
strokes, and below some size they stop being distinguishable at 11 pt. That is a
brand-visual judgment for Siwatch, not a measurement — this script reports the
landed mark heights against Leelawadee UI and Sarabun so the trade is visible,
and `build_th_mark_specimen.py` renders it.

Usage:
    python3 scripts/solve_mark_scale.py                      # default sweep
    python3 scripts/solve_mark_scale.py --scales 0.75 0.70
    python3 scripts/solve_mark_scale.py --family TH-Slussen --target 1512
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from thai_line_pitch import MARGIN, required_pitch  # noqa: E402
from th_mark_scale import _ink_height, _mark_anchors  # noqa: E402

from fontTools.ttLib import TTFont  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

BUILDER = {
    "TH-Aeonik": "build_th_aeonik.py",
    "TH-Slussen": "build_th_slussen.py",
}

# The faces that bind. Black/SemiBold carry the tallest stacks because
# emboldening grows the consonant and the mark toward each other, so the
# clearance pass lifts the mark furthest. Regular is measured too because it is
# what body text actually uses and a solve that only satisfies the extreme is not
# obviously safe for it.
BINDING = {
    "TH-Aeonik": ["Black", "Regular"],
    "TH-Slussen": ["SemiBold", "Regular"],
}

# Reference mark heights at the same consonant height, 1/1000 em, measured
# 2026-08-04. Leelawadee UI is the only Thai font that clears its own line box
# comfortably; Sarabun is the reference Siwatch nominated for Thai engineering and
# is LARGER than ours, which is why it needs 1582 and gets -282 of margin.
REFERENCE_MARKS = {
    "leelawadee": {"uni0E37": 197, "uni0E36": 201, "uni0E34": 167,
                   "uni0E49": 201, "uni0E38": 182},
    "sarabun":    {"uni0E37": 290, "uni0E36": 285, "uni0E34": 234,
                   "uni0E49": 268, "uni0E38": 270},
}
MARK_LABEL = {"uni0E37": "ue-vowel", "uni0E36": "uee-vowel",
              "uni0E34": "i-vowel", "uni0E49": "tone-2", "uni0E38": "u-vowel"}


def build_at(family, scale, weights, out_dir, verbose=False):
    """Build `weights` of `family` at `scale` into `out_dir`. Returns built paths."""
    cmd = [sys.executable, str(ROOT / "scripts" / BUILDER[family]),
           "--weights", ",".join(weights),
           "--mark-scale", f"{scale:.4f}",
           "--out-dir", str(out_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout[-3000:] + proc.stderr[-2000:])
        raise SystemExit(f"build failed at mark scale {scale}")
    if verbose:
        print(proc.stdout)
    return sorted(out_dir.glob(f"{family}-*.otf"))


def mark_heights(path):
    """{glyph: ink height} for the reference marks in a built face."""
    font = TTFont(str(path))
    glyph_set = font.getGlyphSet()
    out = {}
    for name in REFERENCE_MARKS["leelawadee"]:
        h = _ink_height(glyph_set, name)
        if h:
            out[name] = h
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="TH-Aeonik", choices=sorted(BUILDER))
    ap.add_argument("--target", type=float, default=1200.0,
                    help="line box the Thai must fit (default 1200, Aeonik's own)")
    ap.add_argument("--scales", nargs="+", type=float,
                    default=[1.00, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60],
                    help="mark scales to sweep")
    ap.add_argument("--weights", nargs="+", default=None,
                    help="faces to measure (default: the binding ones)")
    args = ap.parse_args()

    weights = args.weights or BINDING[args.family]
    print(f"Solving {args.family} MARK_SCALE against a {args.target:.0f} line box")
    print(f"faces: {', '.join(weights)}   margin: {MARGIN:.0f} "
          f"(Leelawadee UI's own spare, ~1 px at 11 pt)\n")

    print(f"{'scale':>6} {'face':10} {'top':>6} {'bottom':>7} {'need':>6} "
          f"{'required':>9} {'vs target':>10}  verdict")
    results = []
    for scale in args.scales:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            paths = build_at(args.family, scale, weights, out_dir)
            worst = None
            for path in paths:
                r = required_pitch(str(path))
                face = path.stem.replace(f"{args.family}-", "")
                slack = args.target - r["required"]
                if slack >= 0:
                    verdict = "FITS"
                elif args.target - r["need"] >= 0:
                    verdict = "TIGHT (no margin)"
                else:
                    verdict = "COLLIDES"
                print(f"{scale:6.2f} {face:10} {r['top']:6.0f} {r['bottom']:7.0f} "
                      f"{r['need']:6.0f} {r['required']:9.0f} {slack:+10.0f}  "
                      f"{verdict}")
                if worst is None or r["required"] > worst[1]["required"]:
                    worst = (path, r)
            if worst is not None:
                heights = mark_heights(worst[0])
                cells = []
                for name, h in sorted(heights.items()):
                    lee = REFERENCE_MARKS["leelawadee"].get(name)
                    delta = f"{h / lee - 1:+.0%}" if lee else "?"
                    cells.append(f"{MARK_LABEL.get(name, name)} {h:.0f}({delta} Lee)")
                print(f"       marks: {'  '.join(cells)}")
                results.append((scale, worst[1]["required"]))
        print()

    fitting = [s for s, req in results if req <= args.target]
    print("-" * 78)
    if fitting:
        print(f"Largest mark scale that FITS {args.target:.0f} with full margin: "
              f"{max(fitting):.2f}")
        print("Set th_thai_prep.MARK_SCALE and re-run "
              "scripts/thai_line_pitch.py --check.")
    else:
        best = min(results, key=lambda r: r[1]) if results else None
        print(f"NOTHING in this sweep fits {args.target:.0f} with the "
              f"{MARGIN:.0f}-unit margin.")
        if best:
            print(f"Closest was scale {best[0]:.2f} needing {best[1]:.0f} — "
                  f"{best[1] - args.target:+.0f} over.")
        print("This is a real result, not a failure to search: it means Aeonik's "
              "box cannot hold a Thai stack at any mark size worth shipping, and "
              "the trade has to go back to Siwatch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
