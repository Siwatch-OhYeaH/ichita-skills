#!/usr/bin/env python3
"""
Measure the PDF delivery engines against one fixture.

The question this answers is narrow and it matters: which engine actually gets
ICHITA's CFF fonts into a delivered PDF. Word's Save-as-PDF does not — Office
refuses to embed OpenType-CFF, so our .otf faces become Calibri while the file
still lists them as embedded. Nothing about the file looks wrong.

Checks, per engine:
  1. no non-brand font embedded            (the Calibri substitution)
  2. the Thai text survives, NFC-identical  (the U+0E49 -> U+02D7 class)
  3. measured line pitch                    (the 1537 box, read from the PDF)
  4. page count against the reference
  5. a PNG to look at                       (nothing here replaces that)

Usage:
    python pdf_bakeoff.py FIXTURE.docx OUTDIR [--source FIXTURE.md]
"""

import argparse
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))

BRAND_FAMILIES = ("Aeonik", "TH-Aeonik", "TH Aeonik", "TH-Slussen", "Betatron")


def thai_only(s):
    s = unicodedata.normalize("NFC", s)
    return "".join(c for c in s if "฀" <= c <= "๿")


def base_family(embedded):
    """Strip the 6-letter subset tag PDF producers prepend, e.g. `BAAAAA+`."""
    return embedded.split("+", 1)[-1] if "+" in embedded else embedded


# ── Engines ──────────────────────────────────────────────────────────────────

def engine_libreoffice(docx, outdir):
    """soffice --headless. Re-lays out the document, but embeds CFF as Type1C."""
    if not shutil.which("soffice"):
        return None, "soffice not installed"
    out = outdir / "libreoffice.pdf"
    proc = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir",
         str(outdir), str(docx)],
        capture_output=True, text=True, timeout=300)
    produced = outdir / (docx.stem + ".pdf")
    if not produced.exists():
        return None, f"no output ({proc.stderr.strip()[:100]})"
    produced.replace(out)
    return out, None


def engine_weasyprint(md_src, outdir):
    """md -> branded html -> weasyprint. Discards Word layout entirely."""
    if md_src is None:
        return None, "no markdown source given"
    from emit_html import md_to_html
    html = outdir / "weasyprint.html"
    out = outdir / "weasyprint.pdf"
    md_to_html(md_src, html, quiet=True)
    proc = subprocess.run(
        [sys.executable,
         str(REPO / "skills" / "ichita-exe-brief" / "scripts" / "html2pdf.py"),
         str(html), str(out)],
        capture_output=True, text=True, timeout=300)
    if not out.exists():
        return None, f"weasyprint failed ({proc.stderr.strip()[:100]})"
    return out, None


def engine_word(docx, outdir):
    """Word COM from WSL.

    NOT run by default, and the reason is measured rather than cautious: on
    2026-08-06 two attempts from WSL both hung on a modal dialog that is
    invisible because the automation sets Visible=false, and both orphaned a
    windowless WINWORD.EXE holding font files open. That is the §9 failure —
    an orphan blocks a font install while the applications look closed.

    Run it attended, with Word visible, and check for orphans afterwards.
    """
    return None, ("skipped — Word COM hangs unattended and orphans "
                  "WINWORD.EXE; see reference/pdf-delivery.md")


# ── Checks ───────────────────────────────────────────────────────────────────

def audit(pdf, source_text, ref_pages=None):
    import fitz
    doc = fitz.open(pdf)
    res = {}

    embedded = sorted({base_family(f[3])
                       for p in doc for f in p.get_fonts(full=True)})
    non_brand = [f for f in embedded
                 if not any(b in f for b in BRAND_FAMILIES)]
    res["fonts"] = embedded
    res["no_substitution"] = (not non_brand, non_brand)

    text = "\n".join(p.get_text() for p in doc)
    want, got = thai_only(source_text), thai_only(text)
    res["thai"] = (want == got, f"{len(got)}/{len(want)} Thai chars")

    res["pages"] = (len(doc) == ref_pages if ref_pages else None, len(doc))
    res["pitch"] = _pitch(doc)
    res["size_kb"] = round(pdf.stat().st_size / 1024)
    return res


def _pitch(doc):
    """Median baseline-to-baseline distance of consecutive body lines.

    Read from the PDF rather than from any metric field, because which field
    a renderer uses depends on the outline format — see §2 of the font doc.
    """
    import statistics
    gaps = []
    for page in doc:
        tops = []
        for b in page.get_text("dict")["blocks"]:
            if b.get("type"):
                continue
            for l in b["lines"]:
                if any(s["text"].strip() for s in l["spans"]):
                    tops.append((round(l["bbox"][1], 2),
                                 max(s["size"] for s in l["spans"])))
        tops.sort()
        for (y0, s0), (y1, s1) in zip(tops, tops[1:]):
            d = y1 - y0
            if 0.5 < d < 40 and abs(s0 - s1) < 0.05:
                gaps.append((d, s0))
    if not gaps:
        return None
    body = statistics.mode([round(s, 1) for _, s in gaps])
    same = [d for d, s in gaps if round(s, 1) == body]
    return (round(statistics.median(same), 2), body,
            round(statistics.median(same) / body, 3))


def main():
    ap = argparse.ArgumentParser(description="PDF delivery bake-off.")
    ap.add_argument("fixture", type=Path, help="the reference DOCX")
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--source", type=Path, default=None,
                    help="the Markdown the DOCX was made from (weasyprint leg)")
    ap.add_argument("--png", action="store_true",
                    help="also render page 1 of each engine's PDF")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    source_text = (args.source.read_text(encoding="utf-8")
                   if args.source else "")

    engines = [
        ("LibreOffice headless", lambda: engine_libreoffice(args.fixture, args.outdir)),
        ("md->html->weasyprint", lambda: engine_weasyprint(args.source, args.outdir)),
        ("Word COM Print-to-PDF", lambda: engine_word(args.fixture, args.outdir)),
    ]

    ref_pages = None
    rows = []
    for name, run in engines:
        pdf, err = run()
        if pdf is None:
            rows.append((name, None, err))
            print(f"\n### {name}\n  SKIPPED — {err}")
            continue
        res = audit(pdf, source_text, ref_pages)
        if ref_pages is None:
            ref_pages = res["pages"][1]
        rows.append((name, res, None))

        ok, bad = res["no_substitution"]
        print(f"\n### {name}  ({pdf.name}, {res['size_kb']} KB)")
        print(f"  fonts embedded    {', '.join(res['fonts'])}")
        print(f"  no substitution   {'PASS' if ok else 'FAIL — ' + ', '.join(bad)}")
        tok, tdetail = res["thai"]
        print(f"  thai NFC-identical {'PASS' if tok else 'FAIL'}  ({tdetail})")
        if res["pitch"]:
            pitch, body, ratio = res["pitch"]
            print(f"  measured pitch    {pitch} pt at {body} pt body "
                  f"= {ratio} em")
        print(f"  pages             {res['pages'][1]}")

        if args.png:
            subprocess.run(["pdftoppm", "-png", "-r", "90", "-f", "1", "-l", "1",
                            str(pdf), str(args.outdir / pdf.stem)], check=False)
            print(f"  png               {pdf.stem}-1.png  — look at it")

    print("\nWord's Save-as-PDF is deliberately not an engine here. "
          "It cannot embed CFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
