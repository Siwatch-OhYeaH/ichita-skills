#!/usr/bin/env python3
"""Does a shipped font directory actually RESOLVE? — fontconfig acceptance probe.

WHY THIS FILE EXISTS
--------------------
`th_style_link.py --check` verifies that every face carries the name and weight
fields it is supposed to carry. That is necessary and it is not sufficient: it
says nothing about which file an application gets back when it asks for one.
Twice now the fields were exactly right and the answer was wrong.

  * 2026-08-07, weight 700 on every bold slot: `fc-match "TH Aeonik:bold"`
    returned AirBold, so a bold line rendered LIGHTER than body text.
  * 2026-08-07, true weights on every bold slot: `fc-match "TH Aeonik Light"`
    returned LightBold, +92.5% ink, heavier than the Medium beneath it.

Both are matcher behaviour, not metadata. Only a matcher finds them.

WHAT IT ASKS
------------
Three queries, and the expected answer for each is derived FROM THE FONTS, not
hardcoded — so this works against any structure, including one it has never
seen. That matters: a probe with a baked-in answer table only ever confirms the
structure it was written for.

  A. bare `nameID1`            -> that family's non-bold, non-italic face
  B. `nameID1` + `:bold`       -> that family's bold face
  C. `nameID16` + `:weight=N`  -> the face declaring N, for every N present

Query A is the one that constrains the design, and it is worth understanding
before reading a failure. An unqualified pattern defaults to fc weight 80
(regular), and within one family the NEAREST member wins. So a family's plain
face resolves only while it sits closer to fc 80 than its own bold slot does —
which a light family cannot do once its bold declares a true, heavy weight.
See docs/THAI-LATIN-FONT-ENGINEERING.md §1b.

FONTCONFIG IS NOT WINDOWS. This probe covers Pango, WeasyPrint and LibreOffice
— which includes `soffice`, the DOCX->PDF delivery engine. GDI and DirectWrite
match on nameID1 + the macStyle bold bit and ignore all of this, so a green run
here is not evidence about Word. §7 has the table; Word is measured in Word.

USAGE
-----
    python3 fc_family_probe.py                     # the shipped th-aeonik dir
    python3 fc_family_probe.py --dir <d>           # any directory of faces
    python3 fc_family_probe.py --render out.png    # also draw what resolves
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "assets" / "fonts" / "th-aeonik"

# A Thai clause and a Latin clause on one line — a weight defect shows in both
# scripts at once, and Thai is where a wrong face is easiest to miss.
SPECIMEN = "ระบบบำบัดน้ำ Filtration 98.5%"


# ---------------------------------------------------------------------------
# An isolated fontconfig tree, so the system's installed copy cannot answer
# ---------------------------------------------------------------------------

def isolate(fonts_dir, tmp):
    """FONTCONFIG_FILE env pointing at `fonts_dir` alone, with its own cache.

    The <dir> path MUST be absolute. A relative one resolves against the
    caller's cwd, and fontconfig then mis-scores queries while `fc-scan` still
    reports every file correctly — which reads as a font defect and is not one.
    It cost an hour on 2026-08-07.
    """
    fonts_dir = Path(fonts_dir).resolve()
    cache = tmp / "cache"
    cache.mkdir(exist_ok=True)
    conf = tmp / "fonts.conf"
    conf.write_text(
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
        "<fontconfig>\n"
        f"  <dir>{fonts_dir}</dir>\n"
        f"  <cachedir>{cache}</cachedir>\n"
        "</fontconfig>\n")
    env = dict(os.environ, FONTCONFIG_FILE=str(conf))
    out = subprocess.run(["fc-cache", "-f"], env=env,
                         capture_output=True, text=True, check=True)
    if "warning" in (out.stderr or "").lower():
        raise SystemExit(f"ERROR: fontconfig warned building the rig, so "
                         f"nothing it reports can be trusted:\n{out.stderr}")
    return env


def fc_match(env, pattern):
    out = subprocess.run(["fc-match", "-f", "%{file}", pattern],
                         env=env, capture_output=True, text=True)
    return Path(out.stdout.strip()).stem or "<no match>"


# ---------------------------------------------------------------------------
# What the directory claims about itself
# ---------------------------------------------------------------------------

def survey(fonts_dir):
    """Read every face's identity straight off the bytes.

    fontTools rather than fc-scan: fc-scan reports fontconfig's OPINION of the
    weight, and the point of query C is to check that opinion against the file.
    """
    faces = []
    for path in sorted(Path(fonts_dir).glob("*.otf")):
        font = TTFont(str(path))
        nt = font["name"]
        faces.append({
            "stem": path.stem,
            "id1": nt.getDebugName(1),
            "id2": nt.getDebugName(2) or "",
            "id16": nt.getDebugName(16),
            "weight": font["OS/2"].usWeightClass,
            "bold": bool(font["head"].macStyle & 1),
            "italic": bool(font["head"].macStyle & 2),
        })
        font.close()
    if not faces:
        raise SystemExit(f"ERROR: no .otf in {fonts_dir} — an empty directory "
                         f"is not a pass")
    return faces


def _slot(faces, id1, *, bold, italic=False):
    hit = [f for f in faces
           if f["id1"] == id1 and f["bold"] is bold and f["italic"] is italic]
    return hit[0] if len(hit) == 1 else None


# ---------------------------------------------------------------------------
# The three queries
# ---------------------------------------------------------------------------

def probe(faces, env, verbose=True):
    faults = []

    def row(label, got, want):
        ok = got == want
        if not ok:
            faults.append(f"{label} -> {got}, want {want}")
        if verbose:
            print(f"  {label:<34s} -> {got:<30s} "
                  f"{'OK' if ok else 'BROKEN  want ' + want}")

    # --- 0. the invariant every query below depends on ---------------------
    #
    # Scoped to the TYPOGRAPHIC family, because that is the only place it
    # binds. A face with no nameID16 is not in one — today's bold slots all
    # declare 700 and that is deliberate and harmless, since none of them is a
    # candidate for a `TH Aeonik:weight=700` query. It is also exactly why
    # those faces make their own Settings cards. Checking it globally would
    # fail the shipped structure for a collision that cannot be reached.
    if verbose:
        print("0. Within one typographic family, one face per "
              "(declared weight, slant).\n   Nothing else can make a weight "
              "query unambiguous.\n")
    loose = [f for f in faces if not f["id16"]]
    for fam in sorted({f["id16"] for f in faces if f["id16"]}):
        if verbose:
            print(f"  [{fam}]")
        pairs = {}
        for f in sorted((f for f in faces if f["id16"] == fam),
                        key=lambda f: (f["weight"], f["italic"])):
            key = (f["weight"], f["italic"])
            tag = f"{f['weight']:>4d}{'i' if f['italic'] else ' '}"
            if key in pairs:
                faults.append(f"{f['stem']} shares (weight {f['weight']}, "
                              f"{'italic' if f['italic'] else 'roman'}) with "
                              f"{pairs[key]} inside {fam!r} — a weight query "
                              f"cannot choose between them")
                if verbose:
                    print(f"    {tag}  {f['stem']:<32s} COLLIDES with "
                          f"{pairs[key]}")
            else:
                pairs[key] = f["stem"]
                if verbose:
                    print(f"    {tag}  {f['stem']}")
    if verbose and loose:
        print(f"\n  [no nameID16 — each nameID1 below is its own Settings card]")
        for f in sorted(loose, key=lambda f: f["stem"]):
            print(f"    {f['weight']:>4d}{'i' if f['italic'] else ' '}  "
                  f"{f['stem']:<32s} card {f['id1']!r}")

    families = sorted({f["id1"] for f in faces})

    # --- A. bare nameID1 ---------------------------------------------------
    if verbose:
        print(f"\nA. Bare family name — what a Word run carries, and what "
              f"soffice resolves.\n")
    for id1 in families:
        want = _slot(faces, id1, bold=False)
        if want is None:
            continue
        row(repr(id1), fc_match(env, id1), want["stem"])

    # --- B. nameID1 + :bold ------------------------------------------------
    if verbose:
        print(f"\nB. Family + :bold — Ctrl+B's fontconfig equivalent.\n")
    for id1 in families:
        want = _slot(faces, id1, bold=True)
        if want is None:
            continue
        row(f"{id1!r}:bold", fc_match(env, f"{id1}:bold"), want["stem"])

    # --- C. nameID16 + :weight ---------------------------------------------
    typo = sorted({f["id16"] for f in faces if f["id16"]})
    if verbose:
        print(f"\nC. Typographic family + :weight — every declared weight must "
              f"reach its own file.\n")
    # Ask in fontconfig's units, which are not OS/2's, and let fontconfig do
    # the conversion rather than reimplementing its ladder here — it is
    # piecewise (400->80, 500->100, 600->180, 700->200, 900->210) and guessing
    # it wrong is how the first run of this probe produced five false faults.
    weight_of = _fc_weights(env)
    for fam in typo:
        members = sorted((f for f in faces if f["id16"] == fam),
                         key=lambda f: (f["weight"], f["italic"]))
        for f in members:
            fcw = weight_of.get(f["stem"])
            if fcw is None:
                faults.append(f"{f['stem']}: fontconfig did not scan it")
                continue
            pat = f"{fam}:weight={fcw:g}"
            if f["italic"]:
                pat += ":slant=100"
            row(f"{fam} w={f['weight']}{'i' if f['italic'] else ''}",
                fc_match(env, pat), f["stem"])

    return faults


def _fc_weights(env):
    """fontconfig's own weight for each scanned file, keyed by file stem."""
    out = subprocess.run(["fc-list", "-f", "%{file}\t%{weight}\n"],
                         env=env, capture_output=True, text=True).stdout
    return {Path(f).stem: float(w)
            for f, w in (l.split("\t") for l in out.splitlines() if "\t" in l)}


# ---------------------------------------------------------------------------
# Look at it
# ---------------------------------------------------------------------------

def render(faces, env, out_png, tmp):
    """Draw one specimen line per family, named the way a Word run names it.

    No @font-face and no weight — query A, on the page. A green table is not
    evidence of what the page looks like (§0 rule 1).
    """
    families = sorted({f["id1"] for f in faces})
    rows = "\n".join(
        f'<tr><td class="n">{f}</td>'
        f'<td class="s" style="font-family:\'{f}\'">{SPECIMEN}</td></tr>'
        for f in families)
    # f-string throughout, no %-formatting: the specimen carries a literal "%"
    # and %-formatting reads it as a conversion. charset FIRST — WeasyPrint
    # renders Thai as mojibake without it (§0).
    # Deliberately over-tall, then trimmed to the ink. Sizing the page to the
    # content means guessing a Thai row height, and guessing it low pushes
    # families onto page 2 where `pdftoppm -singlefile` drops them — the
    # picture then looks fine and is missing the evidence. 15pt TH Aeonik
    # carries a 1537/1000 line box, so a row is ~12.5mm, but the estimate is
    # not load-bearing here and the page count is asserted anyway.
    tall = 60 + 18 * len(families)
    html = tmp / "probe.html"
    html.write_text(
        '<meta charset="utf-8">\n'
        "<style>"
        f"@page{{size:190mm {tall}mm;margin:9mm 10mm}}"
        "body{font-family:sans-serif;color:#16181c}"
        "h1{font:600 11pt sans-serif;margin:0 0 1mm;letter-spacing:.04em}"
        "p{font:8.5pt sans-serif;color:#6b7280;margin:0 0 4mm}"
        "table{border-collapse:collapse;width:100%}"
        "td{padding:2.1mm 0;border-bottom:.3pt solid #e5e7eb;"
        "vertical-align:baseline}"
        "td.n{font:8pt sans-serif;color:#6b7280;width:42mm;white-space:nowrap}"
        "td.s{font-size:15pt}</style>\n"
        "<h1>Bare family name — what resolves</h1>\n"
        "<p>No weight, no @font-face. Each line asks for the family the way a "
        "Word run does.</p>\n"
        f"<table>\n{rows}\n</table>\n",
        encoding="utf-8")
    pdf = tmp / "probe.pdf"
    subprocess.run(["python3", "-m", "weasyprint", str(html), str(pdf)],
                   env=env, check=True, capture_output=True)
    pages = subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                           text=True).stdout
    n = next((int(l.split(":")[1]) for l in pages.splitlines()
              if l.startswith("Pages:")), 1)
    if n != 1:
        raise SystemExit(f"ERROR: the specimen ran to {n} pages, so the PNG "
                         f"would show only some of the families")
    out_png = Path(out_png)
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile",
                    str(pdf), str(out_png.with_suffix(""))], check=True)

    from PIL import Image, ImageChops
    img = Image.open(out_png).convert("RGB")
    box = ImageChops.difference(
        img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    if box:
        pad = 22
        img.crop((max(box[0] - pad, 0), max(box[1] - pad, 0),
                  min(box[2] + pad, img.width),
                  min(box[3] + pad, img.height))).save(out_png)
    print(f"\nRendered {out_png}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dir", default=str(OUTPUT_DIR),
                    help="directory of built faces to probe")
    ap.add_argument("--render", metavar="PNG",
                    help="also draw what each bare family name resolves to")
    args = ap.parse_args()

    fonts_dir = Path(args.dir)
    if not fonts_dir.is_dir():
        print(f"ERROR: {fonts_dir} is not a directory", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="fc-probe-"))
    try:
        faces = survey(fonts_dir)
        env = isolate(fonts_dir, tmp)
        print(f"{len(faces)} faces in {fonts_dir}\n")
        faults = probe(faces, env)
        if args.render:
            render(faces, env, args.render, tmp)
        print()
        if faults:
            print(f"FAIL — {len(faults)} fault(s)")
            for f in faults:
                print(f"  - {f}")
            return 1
        print(f"OK — every family and every declared weight resolves to its "
              f"own file")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
