#!/usr/bin/env python3
"""Build the TH font QC document: markdown -> DOCX -> PDF.

Mirrors the coverage of test-output/th-font-specimen.html, but as a printable
document so the fonts can be checked in Word and in a real PDF rather than in
a browser.

Outputs:
    qc/th-font-qc.md              markdown source of truth
    qc/qc-reference.docx          pandoc reference doc (style definitions)
    test-output/th-font-qc.docx
    test-output/th-font-qc.pdf

Run: python3 scripts/build_th_font_qc.py
Then verify: python3 scripts/qc_check_th_font_doc.py
"""

import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).parent.parent
QC = ROOT / "qc"
OUT = ROOT / "test-output"
MD = QC / "th-font-qc.md"
REF = QC / "qc-reference.docx"
DOCX = OUT / "th-font-qc.docx"
PDF = OUT / "th-font-qc.pdf"

# ---------------------------------------------------------------- inventory
# Kept in sync with scripts/build_font_specimen.py.
CONSONANTS = ("ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ "
              "ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ").split()
VOWELS = "ะ า ำ เ แ โ ใ ไ ๅ ๆ ฯ".split()
MARKS = ["ก" + m for m in "ั ิ ี ึ ื ุ ู ็ ่ ้ ๊ ๋ ์ ํ".split()]
THAI_DIGITS = list("๐๑๒๓๔๕๖๗๘๙")
UPPER = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWER = list("abcdefghijklmnopqrstuvwxyz")
DIGITS = list("0123456789")
PUNCT = ". , : ; ! ? ' \" ( ) [ ] { } / \\ - – — _ @ # $ % & * + = < > ~ ^ | ° € £ ¥ § ¶ † ‡".split()
SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72]

PANGRAM_LATIN = "The quick brown fox jumps over the lazy dog"
PANGRAM_THAI = "เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน"
STACKS = ["น้ำเชื่อม", "ฟั้น", "ญี่", "ผู้", "ซึ่ง", "หนึ่ง", "ปั่น", "เกี๊ยว"]
TONE_RAMP = "ก่ ก้ ก๊ ก๋ ก์ กั กิ กี กึ กื กุ กู"
KERN_PAIRS = ["Ta", "To", "Ya", "Wo", "AV", "LT", "P.", "r,", "fi", "fl", "ffi"]
MIXED = "ICHITA อิชิตะ — รายงาน Q3 ปี 2026 (Revenue +12.5%)"

# Paragraph used for the line-pitch measurement. Deliberately mixes Thai with
# above-marks and below-vowels against plain Latin: if leading is driven by the
# font's declared metrics rather than by the ink on each line, every one of
# these lines gets the same pitch regardless of what is actually on it.
PITCH_LINES = [
    "Latin only line one with no tall or deep marks at all",
    "Latin only line two with no tall or deep marks at all",
    "ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น",
    "ปูผู้ญี่ปุ่นซึ่งหนึ่งน้ำเชื่อมกรุ๊ปเกี๊ยวฟั้นปั่น",
    "Latin only line three with no tall or deep marks at all",
    "Latin only line four with no tall or deep marks at all",
]

# Source Aeonik has no Thai coverage, so Thai lines in that block would fall
# back to a system Thai face and measure that font's leading instead of
# Aeonik's. The baseline block is therefore Latin-only.
PITCH_LINES_LATIN = [
    "Latin only line one with no tall or deep marks at all",
    "Latin only line two with no tall or deep marks at all",
    "Latin only line three with no tall or deep marks at all",
    "Latin only line four with no tall or deep marks at all",
    "Latin only line five with no tall or deep marks at all",
    "Latin only line six with no tall or deep marks at all",
]

# ------------------------------------------------------------------- styles
# (style name, font family, pt, bold, italic)
CHAR_STYLES = [
    ("QCAeonikLight",       "TH Aeonik Light",    11, False, False),
    ("QCAeonikLightItalic", "TH Aeonik Light",    11, False, True),
    ("QCAeonikRegular",     "TH Aeonik",          11, False, False),
    ("QCAeonikItalic",      "TH Aeonik",          11, False, True),
    ("QCAeonikBold",        "TH Aeonik",          11, True,  False),
    ("QCAeonikBoldItalic",  "TH Aeonik",          11, True,  True),
    ("QCSlussenRegular",    "TH Slussen",         11, False, False),
    ("QCSlussenMedium",     "TH Slussen Medium",  11, False, False),
    ("QCSlussenSemiBold",   "TH Slussen SemiBold", 11, False, False),
    ("QCSlussenBold",       "TH Slussen",         11, True,  False),
    ("QCBai",               "Bai Jamjuree",       11, False, False),
    ("QCAeonikLatin",       "Aeonik",             11, False, False),
]

# Fonts whose line pitch we measure, and the Latin source each should match.
PITCH_FONTS = [
    ("QCPitchAeonik",  "TH Aeonik",    "Aeonik"),
    ("QCPitchSlussen", "TH Slussen",   "Slussen"),
    ("QCPitchBai",     "Bai Jamjuree", "(Thai reference)"),
    ("QCPitchLatin",   "Aeonik",       "(Latin baseline)"),
]

GRID_FONTS = [("Aeonik", "QCGridAeonik", "TH Aeonik"),
              ("Slussen", "QCGridSlussen", "TH Slussen")]


def _set_cs(style, font, pt, bold, italic):
    """Apply complex-script twins of the Latin run properties.

    Word routes Thai through the complex-script slot: w:cs / w:szCs / w:bCs /
    w:iCs. Setting only the ascii/hAnsi side leaves Thai on whatever the
    theme's cs font is, which silently defeats the whole test.
    """
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    # The built-in heading styles carry w:asciiTheme="majorHAnsi" and friends.
    # A theme attribute takes precedence over the explicit w:ascii sitting
    # next to it, so setting the font alone leaves headings on the theme's
    # Calibri. They have to be removed, not merely overridden.
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme",
                 "w:cstheme"):
        if rFonts.get(qn(attr)) is not None:
            del rFonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), font)
    for tag, val in (("w:szCs", str(int(pt * 2))),
                     ("w:bCs", "1" if bold else "0"),
                     ("w:iCs", "1" if italic else "0")):
        for old in rPr.findall(qn(tag)):
            rPr.remove(old)
        el = OxmlElement(tag)
        el.set(qn("w:val"), val)
        rPr.append(el)
    # Tag the runs as Thai so Word does not reflow them under a Latin locale.
    for old in rPr.findall(qn("w:lang")):
        rPr.remove(old)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:bidi"), "th-TH")
    rPr.append(lang)


def _char_style(doc, name, font, pt, bold=False, italic=False):
    st = doc.styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
    st.font.name = font
    st.font.size = Pt(pt)
    st.font.bold = bold
    st.font.italic = italic
    _set_cs(st, font, pt, bold, italic)
    return st


def _para_style(doc, name, font, pt, bold=False, italic=False,
                exact_pt=None, space_after=2, keep=False):
    st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.font.name = font
    st.font.size = Pt(pt)
    st.font.bold = bold
    st.font.italic = italic
    _set_cs(st, font, pt, bold, italic)
    pf = st.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    if keep:
        # A pitch block split by a page break cannot be measured: the gap
        # across the break is page geometry, not line leading.
        pf.keep_together = True
        pf.keep_with_next = True
    if exact_pt is None:
        # Single: the font's own declared metrics decide the pitch. This is
        # the setting that exposes the bug.
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    else:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(exact_pt)
    return st


def build_reference():
    """Create the pandoc reference doc that defines every QC style."""
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "TH Aeonik"
    normal.font.size = Pt(10.5)
    _set_cs(normal, "TH Aeonik", 10.5, False, False)
    normal.paragraph_format.space_after = Pt(4)

    # Pandoc emits its own styles for prose, and defines them itself when the
    # reference doc does not. Its defaults are Calibri, which means the body
    # text renders in a substitute face and any Thai inside it falls back to a
    # system Thai font — fallback noise in the very document meant to detect
    # fallback. Define them here so everything inherits the TH fonts.
    for sname, pt in [("Body Text", 10.5), ("Compact", 10.5),
                      ("First Paragraph", 10.5)]:
        try:
            st = doc.styles[sname]
        except KeyError:
            st = doc.styles.add_style(sname, WD_STYLE_TYPE.PARAGRAPH)
        st.font.name = "TH Aeonik"
        st.font.size = Pt(pt)
        _set_cs(st, "TH Aeonik", pt, False, False)
        st.paragraph_format.space_after = Pt(4)

    try:
        vc = doc.styles["Verbatim Char"]
    except KeyError:
        vc = doc.styles.add_style("Verbatim Char", WD_STYLE_TYPE.CHARACTER)
    vc.font.name = "TH Aeonik"
    vc.font.size = Pt(9.5)
    _set_cs(vc, "TH Aeonik", 9.5, False, False)

    for lvl, (fnt, pt) in enumerate(
            [("TH Slussen SemiBold", 18), ("TH Slussen SemiBold", 14),
             ("TH Slussen Medium", 11.5)], start=1):
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = fnt
        h.font.size = Pt(pt)
        h.font.bold = False
        _set_cs(h, fnt, pt, False, False)
        h.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
        h.paragraph_format.space_after = Pt(4)

    for args in CHAR_STYLES:
        _char_style(doc, *args)

    # Character-grid paragraphs: generous fixed leading so tall Thai marks are
    # never clipped, keeping this section independent of the spacing question.
    for _, sty, fnt in GRID_FONTS:
        _para_style(doc, sty, fnt, 15, exact_pt=26, space_after=4)

    # Size ramp. Exact leading at 1.35x so a clipped glyph means a real font
    # bug rather than a too-tight paragraph.
    for size in SIZES:
        for tag, fnt in (("Aeonik", "TH Aeonik"), ("Slussen", "TH Slussen")):
            _para_style(doc, f"QCSize{tag}{size}", fnt, size,
                        exact_pt=round(size * 1.35), space_after=1)

    # Weights.
    for name, fnt, bold in [
            ("QCWeightAeonikLight", "TH Aeonik Light", False),
            ("QCWeightAeonikRegular", "TH Aeonik", False),
            ("QCWeightAeonikBold", "TH Aeonik", True),
            ("QCWeightSlussenRegular", "TH Slussen", False),
            ("QCWeightSlussenMedium", "TH Slussen Medium", False),
            ("QCWeightSlussenSemiBold", "TH Slussen SemiBold", False),
            ("QCWeightSlussenBold", "TH Slussen", True)]:
        _para_style(doc, name, fnt, 14, bold=bold, exact_pt=20, space_after=2)

    # Line-pitch probes: Single (diagnostic) and Exactly 14pt (proposed fix).
    for sty, fnt, _ in PITCH_FONTS:
        _para_style(doc, sty + "Single", fnt, 11, space_after=0, keep=True)
        _para_style(doc, sty + "Exact", fnt, 11, exact_pt=14, space_after=0,
                    keep=True)

    # Each pitch block starts a page. keep_with_next alone was not enough —
    # LibreOffice still split a block across a page break, and a gap measured
    # across a page boundary is page geometry, not line leading, so the block
    # becomes unmeasurable and the whole check reports "not measurable".
    lbl = _para_style(doc, "QCPitchLabel", "TH Aeonik", 10.5, bold=True,
                      exact_pt=15, space_after=6)
    lbl.paragraph_format.page_break_before = True
    lbl.paragraph_format.keep_with_next = True

    REF.parent.mkdir(parents=True, exist_ok=True)
    doc.save(REF)
    return REF


# ------------------------------------------------------------------ markdown
_MD_SPECIAL = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def md_escape(s):
    """Backslash-escape ASCII punctuation so pandoc emits it literally.

    The punctuation row is a QC target in its own right, so every glyph has to
    survive the markdown layer verbatim — an unescaped ``*`` or ``_`` turns
    into emphasis and the character silently vanishes from the document.
    """
    return "".join("\\" + c if c in _MD_SPECIAL else c for c in s)


def div(style, text, escape=False):
    body = md_escape(text) if escape else text
    return f'::: {{custom-style="{style}"}}\n{body}\n:::\n'


def grid(style, chars, per_row=None):
    """Emit characters as spaced paragraphs, optionally wrapped into rows."""
    if per_row is None:
        return div(style, "  ".join(chars), escape=True)
    out = []
    for i in range(0, len(chars), per_row):
        out.append(div(style, "  ".join(chars[i:i + per_row]), escape=True))
    return "".join(out)


def build_markdown(metrics):
    d = date.today().isoformat()
    L = []
    add = L.append

    add(f"# TH font QC — {d}\n")
    add("Print-path counterpart to `test-output/th-font-specimen.html`. The "
        "specimen proves the fonts in a browser; this document proves them in "
        "Word and in a printed PDF, which is where the defects have actually "
        "shown up.\n")
    add("Every section states the pass condition. Where a check can be made "
        "mechanically it is, by `scripts/qc_check_th_font_doc.py` — do not "
        "sign these off by eye.\n")

    # -- section 1: the open issue, first because it is the live defect ------
    add("## 1. Line pitch — the open issue\n")
    add("Reported symptom: too much space between lines, top to bottom.\n")
    add("Measured vertical metrics of the shipped fonts against the Latin "
        "source each was built from:\n")
    add(metrics)
    add("\nA font declares its line box three separate ways and different "
        "renderers believe different ones. `usWinAscent`/`usWinDescent` must "
        "stay wide enough to avoid clipping Thai — the tone marks reach "
        "+1206 and the below-vowels −488 — but if the renderer uses that pair "
        "for *leading* as well, every line inherits the Thai extremes even on "
        "a pure-Latin line.\n")
    add("**The discriminator.** TH Slussen's typo and hhea metrics are "
        "identical to source Slussen; only `usWinDescent` changed. So:\n")
    # Deliberately not a markdown list: pandoc's numbering puts the bullet
    # glyph in Symbol, which is absent on Linux and pulls a substitute font
    # into the PDF — fallback noise in a document built to detect fallback.
    add("— loose pitch in **both** families → the renderer is on the win "
        "metrics\n")
    add("— loose pitch in **Aeonik only** → the renderer is on the typo "
        "metrics, and Aeonik's `USE_TYPO_METRICS` flip is the whole cause\n")
    add("\n### 1a. Single line spacing — diagnostic\n")
    add("Six lines per block: Latin, Latin, Thai, Thai, Latin, Latin. "
        "**Pass = all six baselines evenly spaced, and the block heights "
        "match the Latin baseline block.** If the Thai lines push apart, or a "
        "whole block is taller than the Latin one, that block's font is "
        "leading off the wrong metric.\n")
    for sty, fnt, ref in PITCH_FONTS:
        lines = PITCH_LINES_LATIN if sty == "QCPitchLatin" else PITCH_LINES
        add(div("QCPitchLabel", f"{fnt} — Single (source: {ref})"))
        for line in lines:
            add(div(sty + "Single", line))

    add("\n### 1b. Exactly 14 pt — proposed fix\n")
    add("Same text, leading pinned to 14 pt so the font's declared metrics "
        "are bypassed. **Pass = uniform pitch and no clipped Thai marks.** If "
        "this reads correctly while 1a does not, the glyphs are fine and the "
        "defect is purely metadata.\n")
    for sty, fnt, ref in PITCH_FONTS:
        lines = PITCH_LINES_LATIN if sty == "QCPitchLatin" else PITCH_LINES
        add(div("QCPitchLabel", f"{fnt} — Exactly 14 pt"))
        for line in lines:
            add(div(sty + "Exact", line))

    # -- letters -------------------------------------------------------------
    add("\n## 2. Letters\n")
    add("**Pass = every slot filled, no tofu boxes, no fallback glyph in a "
        "visibly different style.**\n")
    for tag, sty, fnt in GRID_FONTS:
        add(f"\n### 2.{'12'[GRID_FONTS.index((tag, sty, fnt))]} {fnt}\n")
        add(f"\nThai consonants — 44\n\n")
        add(grid(sty, CONSONANTS, 15))
        add("\nThai vowels and signs\n\n")
        add(grid(sty, VOWELS))
        add("\nLatin uppercase\n\n")
        add(grid(sty, UPPER, 26))
        add("\nLatin lowercase\n\n")
        add(grid(sty, LOWER, 26))

    # -- symbols -------------------------------------------------------------
    add("\n## 3. Symbols and digits\n")
    add("**Pass = all present; Thai and Latin digits the same height and "
        "weight as the surrounding text.**\n")
    for tag, sty, fnt in GRID_FONTS:
        add(f"\n**{fnt}**\n\n")
        add("Latin digits\n\n")
        add(grid(sty, DIGITS))
        add("Thai digits\n\n")
        add(grid(sty, THAI_DIGITS))
        add("Punctuation and symbols\n\n")
        add(grid(sty, PUNCT, 20))

    # -- syllables -----------------------------------------------------------
    add("\n## 4. Syllables and mark stacking\n")
    add("The hardest part of a merged Thai font. **Pass = tone mark sits "
        "directly above its vowel, not beside or on top of it; below-vowels "
        "clear the baseline; nothing collides with the line above.**\n")
    for tag, sty, fnt in GRID_FONTS:
        add(f"\n**{fnt}**\n\n")
        add("Two- and three-level clusters\n\n")
        add(grid(sty, STACKS))
        add("Tone and vowel ramp on a single base\n\n")
        add(div(sty, TONE_RAMP))
        add("Mark inventory on ก\n\n")
        add(grid(sty, MARKS))

    # -- size ----------------------------------------------------------------
    add("\n## 5. Size ramp\n")
    add("**Pass = legible and correctly proportioned at every size; no "
        "clipping at 8–11 pt, no mark collision at 36–72 pt.** The one thing "
        "the CFF→glyf conversion genuinely risked is Latin at 9–11 pt, where "
        "Slussen's original stem hints were dropped — look hardest there.\n")
    for tag, sty, fnt in GRID_FONTS:
        add(f"\n**{fnt}**\n\n")
        for size in SIZES:
            add(div(f"QCSize{tag}{size}",
                    f"{size} pt — {PANGRAM_LATIN} — {''.join(STACKS[:3])}"))

    # -- style ---------------------------------------------------------------
    add("\n## 6. Style — roman and italic\n")
    add("TH Aeonik ships italics; TH Slussen does not. **Pass = the italic "
        "rows are genuinely slanted drawn forms, and Word is not faking a "
        "slant on the upright.** A synthesised oblique on Thai is a defect.\n")
    for label, sty in [("Light", "QCAeonikLight"),
                       ("Light Italic", "QCAeonikLightItalic"),
                       ("Regular", "QCAeonikRegular"),
                       ("Regular Italic", "QCAeonikItalic"),
                       ("Bold", "QCAeonikBold"),
                       ("Bold Italic", "QCAeonikBoldItalic")]:
        add(f"\n[TH Aeonik {label}]{{custom-style=\"{sty}\"}} — "
            f"[{PANGRAM_LATIN}]{{custom-style=\"{sty}\"}} "
            f"[{PANGRAM_THAI}]{{custom-style=\"{sty}\"}}\n")

    # -- weight --------------------------------------------------------------
    add("\n## 7. Weight\n")
    add("**Pass = each step visibly heavier than the one above, in Thai as "
        "well as Latin, with no two steps identical.** TH Slussen Medium and "
        "SemiBold must be distinct — they register as separate families and "
        "are the pair most likely to collapse.\n")
    for name, label in [
            ("QCWeightAeonikLight", "TH Aeonik Light 300"),
            ("QCWeightAeonikRegular", "TH Aeonik Regular 400"),
            ("QCWeightAeonikBold", "TH Aeonik Bold 700"),
            ("QCWeightSlussenRegular", "TH Slussen Regular 400"),
            ("QCWeightSlussenMedium", "TH Slussen Medium 500"),
            ("QCWeightSlussenSemiBold", "TH Slussen SemiBold 600"),
            ("QCWeightSlussenBold", "TH Slussen Bold 700")]:
        add(div(name, f"{label} — Handgloves 123 — น้ำเชื่อมผู้ที่ซึ่งหนึ่ง"))

    # -- spacing -------------------------------------------------------------
    add("\n## 8. Horizontal spacing\n")
    add("**Pass = the word space is the Latin one (it is taken from the "
        "Latin source deliberately, not from Bai Jamjuree), kern pairs are "
        "not gappy, and mixed Thai/Latin runs sit on a common baseline with "
        "even colour.**\n")
    for tag, sty, fnt in GRID_FONTS:
        add(f"\n**{fnt}**\n\n")
        add("Kern pairs\n\n")
        add(grid(sty, KERN_PAIRS))
        add("Mixed script\n\n")
        add(div(sty, MIXED))
        add("Word-space ruler — the pipes must be evenly spaced\n\n")
        add(div(sty, "| a | b | c | d | e | f | g | h |"))
        add(div(sty, "| ก | ข | ค | ง | จ | ฉ | ช | ซ |"))

    add("\n---\n")
    add(f"Generated by `scripts/build_th_font_qc.py` on {d}. "
        "Verify with `scripts/qc_check_th_font_doc.py`.\n")

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(L), encoding="utf-8")
    return MD


def metrics_table():
    """Render the measured vertical metrics as a markdown table."""
    from fontTools.ttLib import TTFont
    rows = [
        ("TH Aeonik",  "assets/fonts/th-aeonik/TH-Aeonik-Regular.otf"),
        ("  Aeonik (source)", "assets/fonts/aeonik/Aeonik-Regular.otf"),
        ("TH Slussen", "assets/fonts/th-slussen/TH-Slussen-Regular.otf"),
        ("  Slussen (source)", "assets/fonts/slussen/Slussen-Regular.otf"),
        ("  Bai Jamjuree", "assets/fonts/bai-jamjuree/BaiJamjuree-Regular.ttf"),
    ]
    out = ["| font | hhea asc/desc/gap | hhea line | typo asc/desc/gap | "
           "winAsc+winDesc | USE_TYPO |",
           "|---|---|---|---|---|---|"]
    for label, rel in rows:
        f = TTFont(ROOT / rel, lazy=True)
        hh, os2 = f["hhea"], f["OS/2"]
        hline = hh.ascender - hh.descender + hh.lineGap
        win = os2.usWinAscent + os2.usWinDescent
        upm = f["head"].unitsPerEm
        out.append(
            f"| {label.strip()} | {hh.ascender}/{hh.descender}/{hh.lineGap} | "
            f"{hline} ({hline/upm:.3f} em) | "
            f"{os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap} | "
            f"**{win}** ({win/upm:.3f} em) | "
            f"{bool(os2.fsSelection & (1 << 7))} |")
        f.close()
    return "\n".join(out) + "\n"


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def main():
    if not shutil.which("pandoc"):
        sys.exit("pandoc not found")
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("libreoffice not found")

    OUT.mkdir(parents=True, exist_ok=True)

    print("building reference docx ...")
    build_reference()
    print(f"  {REF.relative_to(ROOT)}")

    print("building markdown ...")
    build_markdown(metrics_table())
    print(f"  {MD.relative_to(ROOT)}  ({MD.stat().st_size:,} bytes)")

    print("markdown -> docx ...")
    # -smart: keep straight quotes straight. The apostrophe and double quote
    # are characters under test; curling them means the QC never checks the
    # glyphs the font actually ships.
    run(["pandoc", str(MD), "-o", str(DOCX), f"--reference-doc={REF}",
         "--from", "markdown+fenced_divs+bracketed_spans-smart"])
    print(f"  {DOCX.relative_to(ROOT)}  ({DOCX.stat().st_size:,} bytes)")

    print("docx -> pdf ...")
    run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(OUT),
         str(DOCX)])
    if not PDF.exists():
        sys.exit("PDF was not produced")
    print(f"  {PDF.relative_to(ROOT)}  ({PDF.stat().st_size:,} bytes)")

    print("\ndone. now run: python3 scripts/qc_check_th_font_doc.py")


if __name__ == "__main__":
    main()
