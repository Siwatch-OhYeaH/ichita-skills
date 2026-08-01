#!/usr/bin/env python3
"""
Audit a Windows "Print to PDF" output for TH-Aeonik / TH-Slussen problems.

Answers the two questions a visual inspection cannot:

  1. WHICH BUILD did Word actually embed? Windows does not overwrite a
     registered font file, so a rebuilt font can be installed and still not be
     the one that gets used. This hashes each embedded font program against
     every build in assets/fonts/ and against git HEAD, and says so plainly.

  2. ARE THE ADVANCE WIDTHS RIGHT? Print to PDF builds the PDF /W array from
     the CFF charstring widths rather than from hmtx. When those disagree, Thai
     combining marks are declared with a real advance instead of zero, which
     detaches every tone mark from its consonant and shreds copy-paste.

Usage:  python3 check_print_pdf.py <file.pdf>
Exit 0 = the embedded fonts are a current build and their /W arrays are sane.
"""

import hashlib
import io
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import pikepdf
from fontTools.ttLib import TTFont
from fontTools.misc.psCharStrings import T2WidthExtractor

ROOT = Path(__file__).parent.parent
FONT_DIRS = [ROOT / "assets/fonts/aeonik-th", ROOT / "assets/fonts/slussen-th"]

# Thai combining marks: zero advance in hmtx, must be zero in /W too
MARKS = set(range(0x0E31, 0x0E32)) | set(range(0x0E34, 0x0E3B)) | set(range(0x0E47, 0x0E4F))


def known_builds():
    """sha256 -> label, for every current build and its git HEAD ancestor."""
    out = {}
    for d in FONT_DIRS:
        for p in sorted(d.glob("*.otf")):
            out[hashlib.sha256(p.read_bytes()).hexdigest()] = f"CURRENT  {p.name}"
            rel = p.relative_to(ROOT)
            try:
                blob = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
                                      capture_output=True, check=True).stdout
                out.setdefault(hashlib.sha256(blob).hexdigest(),
                               f"git HEAD (older build)  {p.name}")
            except subprocess.CalledProcessError:
                pass
    return out


def widths_from_W(df):
    W = {}
    if "/W" not in df:
        return W
    arr = list(df["/W"])
    i = 0
    while i < len(arr):
        first = int(arr[i])
        if i + 1 < len(arr) and isinstance(arr[i + 1], pikepdf.Array):
            for j, w in enumerate(arr[i + 1]):
                W[first + j] = float(w)
            i += 2
        elif i + 2 < len(arr):
            for c in range(first, int(arr[i + 1]) + 1):
                W[c] = float(arr[i + 2])
            i += 3
        else:
            break
    return W


def cid_to_unicode(font):
    """Map CID -> unicode via the embedded font's cmap (CIDs are GIDs here)."""
    order = font.getGlyphOrder()
    gid = {g: i for i, g in enumerate(order)}
    return {gid[g]: cp for cp, g in font.getBestCmap().items() if g in gid}


def audit(pdf_path):
    builds = known_builds()
    pdf = pikepdf.open(pdf_path)
    seen, problems, checked = {}, [], 0

    for page in pdf.pages:
        for _, f in page.get("/Resources", {}).get("/Font", {}).items():
            if "/DescendantFonts" not in f:
                continue
            base = str(f.get("/BaseFont", ""))
            df = f["/DescendantFonts"][0]
            desc = df.get("/FontDescriptor")
            if not desc:
                continue
            key = next((k for k in ("/FontFile3", "/FontFile2", "/FontFile")
                        if k in desc), None)
            if not key:
                continue
            data = bytes(desc[key].read_bytes())
            h = hashlib.sha256(data).hexdigest()
            if h in seen:
                continue
            seen[h] = True

            try:
                font = TTFont(io.BytesIO(data))
            except Exception as e:
                print(f"  {base}: could not parse embedded program ({e})")
                continue
            name = font["name"].getName(4, 3, 1, 0x409)
            name = name.toUnicode() if name else base
            if not (name.startswith("TH Aeonik") or name.startswith("TH Slussen")):
                continue
            checked += 1

            label = builds.get(h)
            print(f"\n  {base}  ->  {name}")
            print(f"    embedded program: {len(data):,} bytes  sha256 {h[:16]}")
            if label and label.startswith("CURRENT"):
                print(f"    build: {label}  [OK]")
            elif label:
                print(f"    build: {label}  [STALE]")
                problems.append(f"{name}: Word embedded an older build "
                                f"({label.split()[-1]}), not the current one")
            else:
                print(f"    build: UNRECOGNISED — matches no build in assets/fonts/ "
                      f"nor git HEAD  [STALE?]")
                problems.append(f"{name}: embedded font matches no known build")

            # ---- CFF charstring widths vs hmtx (inside the embedded program)
            if "CFF " in font:
                cff = font["CFF "].cff
                top = cff[cff.fontNames[0]]
                ex = T2WidthExtractor(getattr(top.Private, "Subrs", []), cff.GlobalSubrs,
                                      top.Private.nominalWidthX, top.Private.defaultWidthX)
                hmtx = font["hmtx"]
                bad = badmark = 0
                for gn in top.CharStrings.keys():
                    ex.reset(); ex.execute(top.CharStrings[gn])
                    if ex.width != hmtx[gn][0]:
                        bad += 1
                        if hmtx[gn][0] == 0:
                            badmark += 1
                tag = "OK" if not bad else "BROKEN"
                print(f"    CFF widths vs hmtx: {bad} disagree "
                      f"({badmark} zero-advance marks)  [{tag}]")
                if bad:
                    problems.append(f"{name}: {bad} CFF widths disagree with hmtx "
                                    f"({badmark} combining marks) — printed text will spread")

            # ---- the PDF /W array itself, which is what a reader trusts
            W = widths_from_W(df)
            if W:
                c2u = cid_to_unicode(font)
                wrong = [(cid, w, c2u[cid]) for cid, w in W.items()
                         if cid in c2u and c2u[cid] in MARKS and w != 0]
                tag = "OK" if not wrong else "BROKEN"
                print(f"    /W entries: {len(W)}; Thai marks with non-zero advance: "
                      f"{len(wrong)}  [{tag}]")
                for cid, w, cp in wrong[:4]:
                    print(f"      U+{cp:04X} declared /W {w:g}, must be 0")
                if wrong:
                    problems.append(f"{name}: {len(wrong)} Thai combining marks carry a "
                                    f"non-zero advance in the PDF /W array")

    if not checked:
        print("\n  No TH-Aeonik / TH-Slussen fonts embedded in this PDF.")
        return 1

    print(f"\n{'-'*68}")
    if problems:
        print(f"  FAIL — {len(problems)} problem(s):\n")
        for p in problems:
            print(f"   - {p}")
        return 1
    print("  PASS — embedded fonts are a current build and all Thai combining "
          "marks\n         carry a zero advance in the PDF.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    print(f"\n=== {sys.argv[1]} ===")
    sys.exit(audit(sys.argv[1]))
