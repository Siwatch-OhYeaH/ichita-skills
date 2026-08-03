#!/usr/bin/env python3
"""Mechanical QC for test-output/th-font-qc.{docx,pdf}.

Four checks, none of which require looking at the document:

  A  every paragraph and run in the DOCX resolves to an intended font
  B  the PDF embeds only intended fonts (catches silent fallback)
  C  every character in the inventory survived into the PDF text layer
  D  line pitch per block, measured from glyph positions

Check D is measured from a LibreOffice render, which honours
OS/2.fsSelection USE_TYPO_METRICS and therefore leads off the typo metrics.
Word on Windows has historically led off usWinAscent/usWinDescent instead. So
D answers "what do typo-metric renderers do"; the DOCX opened in Word answers
the other half. Both are needed.

Run: python3 scripts/qc_check_th_font_doc.py
Exit 0 = all checks pass.
"""

import re
import statistics
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCX = ROOT / "test-output" / "th-font-qc.docx"
PDF = ROOT / "test-output" / "th-font-qc.pdf"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

EXPECTED_FONTS = {
    "TH Aeonik", "TH Aeonik Light", "TH Slussen", "TH Slussen Medium",
    "TH Slussen SemiBold", "Bai Jamjuree", "Aeonik",
}
# Aeonik-Regular is the deliberate Latin baseline; Bai is the Thai reference.
EXPECTED_PDF = {
    "TH-Aeonik-Regular", "TH-Aeonik-Bold", "TH-Aeonik-RegularItalic",
    "TH-Aeonik-BoldItalic", "TH-Aeonik-Light", "TH-Aeonik-LightItalic",
    "TH-Slussen-Regular", "TH-Slussen-Medium", "TH-Slussen-SemiBold",
    "TH-Slussen-Bold", "BaiJamjuree-Regular", "Aeonik-Regular",
}

PITCH_BLOCKS = [
    ("TH Aeonik",    "Single"), ("TH Slussen",   "Single"),
    ("Bai Jamjuree", "Single"), ("Aeonik (base)", "Single"),
    ("TH Aeonik",    "Exact"),  ("TH Slussen",   "Exact"),
    ("Bai Jamjuree", "Exact"),  ("Aeonik (base)", "Exact"),
]

FONT_FILES = {
    "TH Aeonik":     "assets/fonts/aeonik-th/TH-Aeonik-Regular.ttf",
    "TH Slussen":    "assets/fonts/slussen-th/TH-Slussen-Regular.ttf",
    "Bai Jamjuree":  "assets/fonts/bai-jamjuree/BaiJamjuree-Regular.ttf",
    "Aeonik (base)": "assets/fonts/aeonik/Aeonik-Regular.otf",
}

# Each merged family and the Latin source whose leading it must reproduce.
SOURCE_OF = {
    "TH Aeonik":  "assets/fonts/aeonik/Aeonik-Regular.otf",
    "TH Slussen": "assets/fonts/slussen/Slussen-Regular.otf",
}

# The deliberate line box, per Siwatch 2026-08-03. Larger than the Latin
# source's, because at Word's Single spacing the line box is the only room two
# consecutive Thai lines have and the Latin box is 334 units short — three
# Shift+Enter lines of Thai fused into one band. Asserted as an exact value, not
# as ">= the Latin", so the deviation cannot grow quietly the way the 1.71 em
# build's did. Sized by scripts/thai_line_pitch.py.
EXPECTED_LINE_EM = {
    "TH Aeonik":  1.5400,      # Aeonik 1.2000, +28.3%
    "TH Slussen": 1.6000,      # Slussen 1.5120, +5.8%
}


def effective_line_em(path):
    """Line height in em, and which metric set drives it.

    fsSelection bit 7 (USE_TYPO_METRICS) tells the renderer to lead off
    sTypoAscender/Descender/LineGap. Without it the classic behaviour is to
    use usWinAscent+usWinDescent, which for a Thai-merged font is inflated by
    the tone marks and below-vowels and has nothing to do with the intended
    leading.
    """
    from fontTools.ttLib import TTFont
    f = TTFont(path, lazy=True)
    os2, upm = f["OS/2"], f["head"].unitsPerEm
    if os2.fsSelection & (1 << 7):
        total = os2.sTypoAscender - os2.sTypoDescender + os2.sTypoLineGap
        mode = "typo"
    else:
        total = os2.usWinAscent + os2.usWinDescent
        mode = "win"
    f.close()
    return total / upm, mode

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if detail:
        for line in detail.rstrip().splitlines():
            print(f"         {line}")


# ------------------------------------------------------------------ check A
def resolve_styles(zf):
    """styleId -> effective ascii/cs font, following basedOn chains."""
    root = ET.fromstring(zf.read("word/styles.xml"))
    raw, based = {}, {}
    for st in root.findall(f"{W}style"):
        sid = st.get(f"{W}styleId")
        bo = st.find(f"{W}basedOn")
        if bo is not None:
            based[sid] = bo.get(f"{W}val")
        rf = st.find(f"{W}rPr/{W}rFonts")
        if rf is not None:
            # A theme attribute overrides the explicit font beside it, so a
            # style can name a TH font and still render in the theme's
            # Calibri. Surface it as its own failure rather than reading
            # w:ascii and declaring victory.
            a = ("THEME:" + rf.get(f"{W}asciiTheme")
                 if rf.get(f"{W}asciiTheme") else rf.get(f"{W}ascii"))
            c = ("THEME:" + rf.get(f"{W}cstheme")
                 if rf.get(f"{W}cstheme") else rf.get(f"{W}cs"))
            raw[sid] = (a, c)

    def eff(sid, seen=()):
        if sid in seen:
            return (None, None)
        a, c = raw.get(sid, (None, None))
        if a and c:
            return (a, c)
        parent = based.get(sid)
        if parent:
            pa, pc = eff(parent, seen + (sid,))
            return (a or pa, c or pc)
        return (a, c)

    return {sid: eff(sid) for sid in set(list(raw) + list(based))}


def check_docx_fonts():
    with zipfile.ZipFile(DOCX) as zf:
        styles = resolve_styles(zf)
        doc = ET.fromstring(zf.read("word/document.xml"))

    bad = Counter()
    total = 0
    for p in doc.iter(f"{W}p"):
        text = "".join(t.text or "" for t in p.iter(f"{W}t"))
        if not text.strip():
            continue
        total += 1
        ps = p.find(f"{W}pPr/{W}pStyle")
        pid = ps.get(f"{W}val") if ps is not None else "Normal"
        for r in p.iter(f"{W}r"):
            rt = "".join(t.text or "" for t in r.iter(f"{W}t"))
            if not rt.strip():
                continue
            rs = r.find(f"{W}rPr/{W}rStyle")
            sid = rs.get(f"{W}val") if rs is not None else pid
            ascii_f, cs_f = styles.get(sid, (None, None))
            has_thai = any("฀" <= ch <= "๿" for ch in rt)
            for slot, fnt in (("ascii", ascii_f),
                              ("cs", cs_f) if has_thai else ("ascii", ascii_f)):
                if fnt is None:
                    bad[f"{sid} ({slot}: unset)"] += 1
                elif fnt not in EXPECTED_FONTS:
                    bad[f"{sid} ({slot}: {fnt})"] += 1

    detail = "\n".join(f"{n:>4}x  {k}" for k, n in bad.most_common())
    record(f"A. DOCX styles resolve to intended fonts ({total} paragraphs)",
           not bad, detail or "every run resolves to a TH/baseline font")
    return bad


# ------------------------------------------------------------------ check B
def check_pdf_fonts():
    out = subprocess.run(["pdffonts", str(PDF)], capture_output=True,
                         text=True).stdout
    names, unembedded = set(), []
    for line in out.splitlines()[2:]:
        if not line.strip():
            continue
        raw = line.split()[0]
        nm = raw.split("+", 1)[1] if "+" in raw else raw
        names.add(nm)
        if " no " in f" {line.split()[-4]} ":
            unembedded.append(nm)

    unexpected = sorted(names - EXPECTED_PDF)
    missing = sorted(EXPECTED_PDF - names)
    d = []
    if unexpected:
        d.append("UNEXPECTED (fallback happened): " + ", ".join(unexpected))
    if missing:
        d.append("expected but absent: " + ", ".join(missing))
    if unembedded:
        d.append("NOT EMBEDDED: " + ", ".join(unembedded))
    record("B. PDF embeds only intended fonts",
           not unexpected and not unembedded,
           "\n".join(d) or f"{len(names)} fonts, all intended, all embedded")
    return unexpected


# ------------------------------------------------------------------ check C
def check_coverage():
    txt = subprocess.run(["pdftotext", "-enc", "UTF-8", str(PDF), "-"],
                         capture_output=True, text=True).stdout
    present = set(txt)

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_th_font_qc import (CONSONANTS, VOWELS, THAI_DIGITS, UPPER,
                                  LOWER, DIGITS, PUNCT)

    groups = {
        "Thai consonants": CONSONANTS, "Thai vowels": VOWELS,
        "Thai digits": THAI_DIGITS, "Latin upper": UPPER,
        "Latin lower": LOWER, "digits": DIGITS, "punctuation": PUNCT,
    }
    miss = {}
    for label, chars in groups.items():
        gone = [c for c in chars if c not in present]
        if gone:
            miss[label] = gone

    # A .notdef reaching the text layer usually surfaces as U+FFFD or NUL.
    tofu = [c for c in present if c in "�\x00"]

    d = []
    for label, gone in miss.items():
        d.append(f"{label}: missing {' '.join(gone)}")
    if tofu:
        d.append(f"replacement/notdef characters present: {len(tofu)}")
    total = sum(len(v) for v in groups.values())
    record(f"C. all {total} inventory characters survive into the PDF",
           not miss and not tofu,
           "\n".join(d) or "every character in the inventory is present")
    return miss


# ------------------------------------------------------------------ check D
def pdf_lines():
    """(page, yMin, text) for every line, in document order."""
    # -bbox-layout, not -bbox: the plain form emits bare <word> elements with
    # no <line> grouping, so there is nothing to measure a pitch between.
    xml = subprocess.run(["pdftotext", "-bbox-layout", str(PDF), "-"],
                         capture_output=True, text=True).stdout
    xml = re.sub(r'\sxmlns="[^"]+"', "", xml, count=1)
    root = ET.fromstring(xml)
    out = []
    for pno, page in enumerate(root.iter("page")):
        for ln in page.iter("line"):
            words = [w.text or "" for w in ln.iter("word")]
            if not words:
                continue
            out.append((pno, float(ln.get("yMin")), " ".join(words)))
    return out


def check_pitch():
    lines = pdf_lines()
    marker = "Latin only line one"
    blocks, i = [], 0
    while i < len(lines):
        if lines[i][2].startswith(marker):
            blk = lines[i:i + 6]
            if len(blk) == 6 and len({b[0] for b in blk}) == 1:
                blocks.append(blk)
                i += 6
                continue
        i += 1

    if len(blocks) != len(PITCH_BLOCKS):
        record("D. line pitch measurable", False,
               f"found {len(blocks)} pitch blocks, expected "
               f"{len(PITCH_BLOCKS)} (a block split across a page break is "
               f"skipped; re-run after adjusting page flow)")
        return None

    pitches = {}
    rows = ["block                    pitch(pt)  per-gap deltas"]
    for (label, mode), blk in zip(PITCH_BLOCKS, blocks):
        ys = [b[1] for b in blk]
        gaps = [round(b - a, 2) for a, b in zip(ys, ys[1:])]
        med = statistics.median(gaps)
        pitches[(label, mode)] = med
        rows.append(f"{label + ' ' + mode:<24} {med:>7.2f}   "
                    f"{' '.join(f'{g:.1f}' for g in gaps)}")

    fails = []

    # Predicted pitch from each font's own declared metrics. A renderer that
    # honours USE_TYPO_METRICS leads off sTypo*; otherwise off usWin*. If
    # measurement matches prediction, the renderer's rule is confirmed and the
    # remaining question is purely which numbers the font declares.
    rows.append("")
    rows.append("measured vs predicted from the font's own metrics (11 pt):")
    for label, rel in FONT_FILES.items():
        if (label, "Single") not in pitches:
            continue
        em, mode_used = effective_line_em(ROOT / rel)
        pred = em * 11
        got = pitches[(label, "Single")]
        ok = abs(got - pred) < 0.15
        rows.append(f"  {label:<16} predicted {pred:>6.2f} ({mode_used}) "
                    f"measured {got:>6.2f}  {'ok' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(f"{label}: renderer does not follow the declared "
                         f"metrics (predicted {pred:.2f}, got {got:.2f})")

    # The merged line box must EQUAL the Latin source's, so a paragraph does not
    # reflow when it is switched between Aeonik and TH-Aeonik.
    #
    # This was informational, on the reasoning that the box had to grow to
    # contain Thai ink. It does not: the line box sets baseline pitch, the clip
    # box (usWin) bounds what gets drawn, and Thai marks are meant to overflow
    # the former into the leading above. Treating them as one box put TH-Aeonik
    # at 1.71 em against Aeonik's 1.20 em, and the 2026-08-02 QC caught it as
    # 42% of extra leading on the same paragraph.
    rows.append("")
    rows.append("line box vs the Latin source (deliberately larger since "
                "2026-08-03 — the Latin box cannot hold two Thai lines apart "
                "at Word's Single spacing):")
    for label, src_rel in SOURCE_OF.items():
        em_m, _ = effective_line_em(ROOT / FONT_FILES[label])
        em_s, _ = effective_line_em(ROOT / src_rel)
        delta = (em_m - em_s) / em_s * 100
        want = EXPECTED_LINE_EM[label]
        ok = abs(em_m - want) < 1e-3
        rows.append(f"  {label:<16} {em_m:.4f} em vs source {em_s:.4f} em   "
                    f"{delta:+6.1f}%  (expected {want:.4f}) "
                    f"{'ok' if ok else 'UNEXPECTED'}")
        if not ok:
            fails.append(f"{label}: line box {em_m:.4f} em is not the "
                         f"documented {want:.4f} em — the deviation from the "
                         f"Latin must be the deliberate one, not drift")

    # Within a block, Thai lines must not push apart relative to Latin lines.
    rows.append("")
    for (label, mode), blk in zip(PITCH_BLOCKS, blocks):
        ys = [b[1] for b in blk]
        gaps = [b - a for a, b in zip(ys, ys[1:])]
        spread = max(gaps) - min(gaps)
        if spread > 0.75:
            fails.append(f"{label} {mode}: pitch varies {spread:.2f} pt "
                         f"within the block (content is driving leading)")
            rows.append(f"  uneven: {label} {mode} spread {spread:.2f} pt")

    record("D. line pitch is metric-driven and uniform", not fails,
           "\n".join(rows))
    return pitches


def main():
    # Optional PDF override. The default PDF is a LibreOffice render, which
    # honours USE_TYPO_METRICS. Point this at a PDF produced by Word to
    # measure what Word's layout engine actually does — the two disagree, and
    # which one is right for a given renderer is exactly the open question.
    global PDF
    if len(sys.argv) > 1:
        PDF = Path(sys.argv[1]).expanduser().resolve()
        if not PDF.exists():
            sys.exit(f"{PDF} not found")

    if not DOCX.exists():
        sys.exit(f"{DOCX} missing — run scripts/build_th_font_qc.py first")
    if not PDF.exists():
        sys.exit(f"{PDF} missing — run scripts/build_th_font_qc.py first")

    print(f"QC  {DOCX.relative_to(ROOT)}")
    try:
        print(f"    {PDF.relative_to(ROOT)}\n")
    except ValueError:
        print(f"    {PDF}   (external render)\n")
    check_docx_fonts()
    check_pdf_fonts()
    check_coverage()
    check_pitch()

    npass = sum(1 for _, ok, _ in results if ok)
    print(f"\n{npass}/{len(results)} checks pass")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
