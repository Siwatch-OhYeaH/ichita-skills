#!/usr/bin/env python3
"""check_ab_test_pdf.py — verify a Word-exported A/B sheet measured what it claimed.

Companion to build_ab_test_doc.py. Reads a PDF exported from Word and answers
two questions the screen cannot:

  1. Did every requested family actually get used, or did Word substitute?
     The 2026-08-02 manual QC compared TH-Aeonik against a control block that
     had silently become Calibri. Nothing was visibly wrong; the substitution
     showed up only in the embedded font list.

  2. Does each merged face lead exactly like its source? Measured from baseline
     pitch in the PDF, not from the font's declared metrics — the point is to
     catch a disagreement between what the font says and what Word does.

USAGE
    python3 scripts/check_ab_test_pdf.py <exported.pdf>
"""

import html
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Merged face -> (source it is compared against, expected ratio of its pitch to
# the source's). Names are as they appear embedded — Word writes the PostScript
# name, so spaces are stripped.
#
# This asserted an exact match until 2026-08-03. It no longer can: the merged
# line box is deliberately larger, because at Word's Single spacing the line box
# is the only room two consecutive Thai lines have and the Latin box is 334 units
# short. The ratio is asserted instead of the difference, so the deviation is
# still pinned to one number and cannot drift.
EXPECTED_RATIO = {
    "TH-Aeonik": ("Aeonik", 1540 / 1200),
    "TH-Slussen": ("Slussen", 1600 / 1512),
}
REQUIRED = ["Aeonik", "Slussen", "BaiJamjuree", "TH-Aeonik", "TH-Slussen"]
# Chrome font from build_ab_test_doc.py — present by design, not under test.
CHROME = {"Arial", "ArialMT", "Arial-BoldMT", "Liberation", "LiberationSans"}

# Word rounds line pitch to the nearest 0.05 pt or so; anything under this is
# not a real difference. A genuine metric mismatch shows up as whole points.
PITCH_TOL = 0.30

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    for line in (detail or "").splitlines():
        if line.strip():
            print(f"         {line}")


def base_family(embedded_name):
    """'BCDEEE+TH-Aeonik-BoldItalic' -> 'TH-Aeonik'."""
    n = re.sub(r"^[A-Z]{6}\+", "", embedded_name)
    n = re.sub(r"(MT|PS(MT)?)$", "", n)
    # Strip a trailing style, but keep the TH- prefix that distinguishes the
    # merged families from their sources.
    for sep in ("-", ","):
        if sep in n[3:]:
            head, _, tail = n[3:].partition(sep)
            if tail:
                return n[:3] + head
    return n


def check_no_substitution(pdf):
    out = subprocess.run(["pdffonts", str(pdf)], capture_output=True,
                         text=True).stdout
    names = [ln.split()[0] for ln in out.splitlines()[2:] if ln.strip()]
    fams = defaultdict(list)
    for n in names:
        fams[base_family(n)].append(n)

    rows = [f"{f:<16} {len(v)} face(s)" for f, v in sorted(fams.items())]
    missing = [r for r in REQUIRED if r not in fams]
    unexpected = [f for f in fams if f not in REQUIRED and f not in CHROME]
    if unexpected:
        rows.append(f"substituted or extra: {', '.join(sorted(unexpected))}")
    if missing:
        rows.append(f"NOT USED — Word substituted these: {', '.join(missing)}")
    record("A. every requested family is embedded (no silent substitution)",
           not missing, "\n".join(rows))
    return not missing


# Chrome lines emitted by build_ab_test_doc.py. Each one ends the specimen
# above it, so a heading or a wrapped instruction paragraph can never be
# averaged into a specimen's pitch. The '^ <family>' form also names the font
# that produced the block it closes.
LABEL_RE = re.compile(r"^\^\s*(.+?)\s*$")
# pdftotext writes the arrow XML-escaped as '-&gt;'. Matching the literal '->'
# silently failed and let the intro paragraph merge into the first specimen,
# which reported Arial's 10.35 pt as Aeonik's pitch. Line text is unescaped
# before matching, so both forms work.
HEADER_RE = re.compile(r"-\s*>")


def _steady_pitch(tops, tol=0.12):
    """The pitch a block actually held, ignoring the jump into it.

    A block arrives as [pair-header, line1, line2, line3], so its first gap is
    the step down from the header and the rest are the real leading. Take the
    longest run of gaps that agree, and require at least two of them — that
    rejects two-line fragments where no pitch is established.
    """
    gaps = [b - a for a, b in zip(tops, tops[1:]) if b - a > 1]
    best_val, best_len = None, 0
    i = 0
    while i < len(gaps):
        j = i
        while j + 1 < len(gaps) and abs(gaps[j + 1] - gaps[i]) <= tol:
            j += 1
        if (j - i + 1) > best_len:
            best_val, best_len = sum(gaps[i:j + 1]) / (j - i + 1), j - i + 1
        i = j + 1
    return (best_val, best_len) if best_len >= 2 else (None, best_len)


def measured_pitch(pdf):
    """Baseline pitch per family, from the rendered page.

    Uses pdftotext -bbox-layout for the y coordinates. pdftohtml -xml was tried
    first because it tags each run with its font, but it reports `top` as an
    integer in its own scaled units — about 0.67 pt per step on Letter — which
    quantised a 13.20 pt pitch into 12.70 and 13.30 and produced a false
    mismatch. bbox-layout reports floats.

    Attribution comes from the sentinel lines instead of from the font tag.
    """
    xml = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"],
                         capture_output=True, text=True).stdout
    # Groups are 1-based on a Match: 1=xMin 2=yMin 3=xMax 4=yMax 5=body.
    lines = [(float(m[2]),
               html.unescape(" ".join(re.findall(r">([^<]+)</word>", m[5]))))
             for m in re.finditer(
                 r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                 r'yMax="([\d.]+)">(.*?)</line>', xml, re.S)]

    seen = defaultdict(list)
    current = []
    for top, text in lines:
        label = LABEL_RE.match(text)
        if label:
            val, _ = _steady_pitch(current)
            if val is not None:
                fam = label.group(1).replace(" ", "-").replace("Bai-J", "BaiJ")
                seen[fam].append(val)
            current = []
        elif HEADER_RE.search(text):
            current = []
        else:
            current.append(top)

    # A family appears in more than one pair; the agreed value is the pitch.
    pitch = {}
    for fam, vals in seen.items():
        vals.sort()
        pitch[fam] = (vals[len(vals) // 2], len(vals))
    return pitch


def check_pitch_matches_source(pdf):
    """Each merged face must lead by its documented ratio to the source's."""
    pitch = measured_pitch(pdf)
    rows, fails = [], []
    for fam, (p, n) in sorted(pitch.items()):
        rows.append(f"{fam:<14} {p:6.2f} pt  ({n} specimen block(s))")
    rows.append("")
    for merged, (src, ratio) in EXPECTED_RATIO.items():
        pm, ps = pitch.get(merged), pitch.get(src)
        if not pm or not ps:
            rows.append(f"{merged:<14} vs {src:<14} SKIP (font not measurable)")
            continue
        want = ps[0] * ratio
        delta = pm[0] - want
        ok = abs(delta) <= PITCH_TOL
        rows.append(f"{merged:<14} {pm[0]:6.2f} pt  vs {src:<12} {ps[0]:6.2f} pt"
                    f" x {ratio:.3f} = {want:6.2f} pt   {delta:+.2f} pt  "
                    f"{'ok' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(f"{merged} leads {pm[0]:.2f} pt where {ratio:.3f} x "
                         f"{src}'s {ps[0]:.2f} pt predicts {want:.2f} pt — the "
                         f"line box is not the documented one")
    record("B. merged face leads by its documented ratio to the source", not fails,
           "\n".join(rows + fails))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    pdf = Path(sys.argv[1])
    if not pdf.exists():
        print(f"not found: {pdf}")
        sys.exit(2)

    print(f"\n  {pdf}\n")
    if check_no_substitution(pdf):
        check_pitch_matches_source(pdf)
    else:
        print("\n  Pitch not measured — a substituted control cannot be "
              "compared against.")

    n_ok = sum(1 for _, ok, _ in results if ok)
    print(f"\n{n_ok}/{len(results)} checks pass")
    sys.exit(0 if n_ok == len(results) else 1)


if __name__ == "__main__":
    main()
