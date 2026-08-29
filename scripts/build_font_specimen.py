#!/usr/bin/env python3
"""
Generate a self-contained visual test page for the merged Thai/Latin families.

Renders TH-Aeonik and TH-Slussen beside the two fonts each was merged from, so
the central claim can be checked by eye: *the merge should be invisible*. Latin
must look like Aeonik/Slussen, Thai must look like Bai Jamjuree.

Fonts are embedded as base64 data URIs. That is deliberate — browsers refuse
@font-face loads from file:// URLs (opaque origin), so a page using relative
paths would silently fall back to a system font and every comparison on it
would be a lie. One self-contained file also survives being copied out of WSL
to Windows, which is where the fonts actually have to work.

Output:  test-output/th-font-specimen.html   (~5 MB, regenerate after any rebuild)
Usage:   python3 build_font_specimen.py
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
A = ROOT / "assets" / "fonts"
OUT = ROOT / "test-output" / "th-font-specimen.html"

# (css family, weight, style, path)
FACES = [
    ("THAeonik", 300, "normal", A / "th-aeonik/TH-Aeonik-Light.otf"),
    ("THAeonik", 300, "italic", A / "th-aeonik/TH-Aeonik-LightItalic.otf"),
    ("THAeonik", 400, "normal", A / "th-aeonik/TH-Aeonik-Regular.otf"),
    ("THAeonik", 400, "italic", A / "th-aeonik/TH-Aeonik-RegularItalic.otf"),
    ("THAeonik", 700, "normal", A / "th-aeonik/TH-Aeonik-Bold.otf"),
    ("THAeonik", 700, "italic", A / "th-aeonik/TH-Aeonik-BoldItalic.otf"),

    ("Aeonik", 300, "normal", A / "aeonik/Aeonik-Light.otf"),
    ("Aeonik", 300, "italic", A / "aeonik/Aeonik-LightItalic.otf"),
    ("Aeonik", 400, "normal", A / "aeonik/Aeonik-Regular.otf"),
    ("Aeonik", 400, "italic", A / "aeonik/Aeonik-RegularItalic.otf"),
    ("Aeonik", 700, "normal", A / "aeonik/Aeonik-Bold.otf"),
    ("Aeonik", 700, "italic", A / "aeonik/Aeonik-BoldItalic.otf"),

    ("THSlussen", 400, "normal", A / "th-slussen/TH-Slussen-Regular.otf"),
    ("THSlussen", 500, "normal", A / "th-slussen/TH-Slussen-Medium.otf"),
    ("THSlussen", 600, "normal", A / "th-slussen/TH-Slussen-SemiBold.otf"),
    ("THSlussen", 700, "normal", A / "th-slussen/TH-Slussen-Bold.otf"),

    ("Slussen", 400, "normal", A / "slussen/Slussen-Regular.otf"),
    ("Slussen", 500, "normal", A / "slussen/Slussen-Medium.otf"),
    ("Slussen", 600, "normal", A / "slussen/Slussen-Semibold.otf"),
    ("Slussen", 700, "normal", A / "slussen/Slussen-Bold.otf"),

    ("Bai", 300, "normal", A / "bai-jamjuree/BaiJamjuree-Light.ttf"),
    ("Bai", 300, "italic", A / "bai-jamjuree/BaiJamjuree-LightItalic.ttf"),
    ("Bai", 400, "normal", A / "bai-jamjuree/BaiJamjuree-Regular.ttf"),
    ("Bai", 400, "italic", A / "bai-jamjuree/BaiJamjuree-Italic.ttf"),
    ("Bai", 500, "normal", A / "bai-jamjuree/BaiJamjuree-Medium.ttf"),
    ("Bai", 600, "normal", A / "bai-jamjuree/BaiJamjuree-SemiBold.ttf"),
    ("Bai", 700, "normal", A / "bai-jamjuree/BaiJamjuree-Bold.ttf"),
    ("Bai", 700, "italic", A / "bai-jamjuree/BaiJamjuree-BoldItalic.ttf"),
]

CONSONANTS = "ก ข ฃ ค ฅ ฆ ง จ ฉ ช ซ ฌ ญ ฎ ฏ ฐ ฑ ฒ ณ ด ต ถ ท ธ น บ ป ผ ฝ พ ฟ ภ ม ย ร ล ว ศ ษ ส ห ฬ อ ฮ".split()
VOWELS = "ะ า ำ เ แ โ ใ ไ ๅ ๆ ฯ".split()
# combining marks shown on a base consonant — alone they have nothing to sit on
MARKS = ["ก" + m for m in "ั ิ ี ึ ื ุ ู ็ ่ ้ ๊ ๋ ์ ํ".split()]
THAI_DIGITS = list("๐๑๒๓๔๕๖๗๘๙")
UPPER = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWER = list("abcdefghijklmnopqrstuvwxyz")
DIGITS = list("0123456789")
PUNCT = list(". , : ; ! ? ' \" ( ) [ ] { } / \\ - – — _ @ # $ % & * + = < > ~ ^ | ° € £ ¥ § ¶ † ‡".split())

SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48, 72]

PANGRAM_LATIN = "The quick brown fox jumps over the lazy dog"
PANGRAM_THAI = "เป็นมนุษย์สุดประเสริฐเลิศคุณค่า กว่าบรรดาฝูงสัตว์เดรัจฉาน"

# Space-free Thai, for the graded pixel-diff panels only.
#
# `space` is a SHARED glyph and deliberately comes from the Latin source, not
# from Bai Jamjuree — mixed Thai/Latin text needs the Latin one. The advances
# genuinely differ (Bai Regular 260 vs Aeonik 262 vs Slussen 276; Bai Bold 288
# vs TH-Aeonik Bold 248), and browsers round each advance to a whole pixel, so
# one space can shift the rest of the string by a full pixel and light up every
# edge after it. That is not a merge defect and it must not be graded as one:
# a TH-Slussen panel with 11 spaces read 11px wider than Bai purely from this.
# compare_th_*.py excludes `space` from the Thai comparison for the same reason.
PANGRAM_THAI_NOSPACE = "เป็นมนุษย์สุดประเสริฐเลิศคุณค่ากว่าบรรดาฝูงสัตว์เดรัจฉาน"
STACKS_NOSPACE = "น้ำเชื่อมผู้ที่ซึ่งหนึ่ง"
TONE_RAMP_NOSPACE = "ก่ก้ก๊ก๋ก์กักิกีกึกืกุกู"
MIXED = "ICHITA อิชิตะ — รายงาน Q3 ปี 2026 (Revenue +12.5%)"

# Words that force two-level Thai stacks: consonant + upper vowel + tone mark.
# These are the glyphs (uni0E48.small et al) that overflowed the clipping box.
STACKS = ["น้ำเชื่อม", "ฟั้น", "ญี่", "ผู้", "ซึ่ง", "หนึ่ง", "ปั่น", "เกี๊ยว"]
# Pairs whose spacing comes from the Latin source's GPOS kerning.
KERN_PAIRS = ["Ta", "To", "Ya", "Wo", "AV", "LT", "P.", "r,", "fi", "fl", "ffi"]


def baseline_fraction(path):
    """Where the first baseline sits below the top of a line-height:1 line box.

    CSS puts the baseline at half-leading + ascent. With line-height:1 that is
    (1 - a - d)/2 + a in em, where a/d come from hhea. Two fonts with different
    vertical metrics therefore render the same string on *different* baselines
    inside identically-sized boxes — TH Aeonik descends to -300 where Aeonik
    descends to -200, a 0.05em (1.3px at 26px) offset.

    The difference overlays have to correct for this. Without it, two fonts with
    byte-identical outlines produce white ghosting, and the overlay reports a
    defect where there is only a line-box difference.
    """
    from fontTools.ttLib import TTFont
    f = TTFont(str(path), lazy=True)
    upm = f["head"].unitsPerEm
    a, d = f["hhea"].ascent / upm, -f["hhea"].descent / upm
    return (1 - a - d) / 2 + a


# one representative face per CSS family — metrics are uniform within each
BASELINE = {}


def data_uri(path):
    mime = "font/otf" if path.suffix.lower() == ".otf" else "font/ttf"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def font_faces():
    out = []
    missing = []
    for fam, wt, style, path in FACES:
        if not path.exists():
            missing.append(str(path))
            continue
        out.append(
            "@font-face{font-family:'%s';font-weight:%d;font-style:%s;"
            "font-display:block;src:url(%s);}" % (fam, wt, style, data_uri(path)))
    if missing:
        print("  !! missing font files:", *missing, sep="\n     ")
        sys.exit(1)
    return "\n".join(out)


def grid(chars, fam, size=28, cls="grid"):
    cells = "".join(f'<span lang="th">{c}</span>' for c in chars)
    return (f'<div class="{cls}" style="font-family:\'{fam}\';font-size:{size}px">'
            f'{cells}</div>')


def triptych(label, text, merged, latin_ref, thai_ref, size, weight=400,
             style="normal", note=""):
    """Merged font beside both sources, same string, same size."""
    st = (f"font-size:{size}px;font-weight:{weight};font-style:{style}")
    return f"""
<div class="tri">
  <div class="tri-label">{label}{f'<em>{note}</em>' if note else ''}</div>
  <div class="tri-row">
    <div class="tri-cell merged"><b>{merged}</b><p lang="th" style="font-family:'{merged}';{st}">{text}</p></div>
    <div class="tri-cell"><b>{latin_ref} <i>(Latin source)</i></b><p lang="th" style="font-family:'{latin_ref}';{st}">{text}</p></div>
    <div class="tri-cell"><b>{thai_ref} <i>(Thai source)</i></b><p lang="th" style="font-family:'{thai_ref}';{st}">{text}</p></div>
  </div>
</div>"""


def overlay(text, top, bottom, size, weight=400, lang="en"):
    """Real pixel diff of two fonts, drawn on canvas and measured.

    Not a CSS blend. Stacking two spans compares line boxes as well as glyphs:
    TH Aeonik's hhea descent is -300 against Aeonik's -200, so identical
    outlines land 0.05em apart and the blend shows ghosting where there is no
    defect. Canvas lets both strings be drawn on the *same* explicit baseline,
    so the only thing being compared is glyph shape and advance — and the
    difference can be counted rather than eyeballed.
    """
    import html as _h
    # THIS IS THE OPPOSITE WAY ROUND FROM THE OLD CFF BUILD. The merged families
    # now ship as TrueType, so Bai Jamjuree's Thai outlines are copied verbatim:
    # THAI is graded pass/fail and must be pixel-identical. Latin is what now
    # carries the cubic->quadratic conversion and the engine change, so browsers
    # rasterise it slightly differently — reported, not graded. compare_th_*.py
    # is the authority on the bound (measured max 16.1/255).
    exact = "1" if bottom == "Bai" else "0"
    return (f'<div class="diff" data-exact="{exact}" '
            f'data-text="{_h.escape(text, quote=True)}" '
            f'data-a="{top}" data-b="{bottom}" data-size="{size}" '
            f'data-weight="{weight}" lang="{lang}">'
            f'<canvas></canvas><div class="dcap">…</div></div>')


def size_ramp(fam, text, lang="en"):
    rows = "".join(
        f'<tr><td class="sz">{s}px</td>'
        f'<td lang="{lang}" style="font-family:\'{fam}\';font-size:{s}px">{text}</td></tr>'
        for s in SIZES)
    return f'<table class="ramp">{rows}</table>'


DIFF_SCRIPT = r"""<script>
// Pixel diff of two fonts drawn on an identical baseline.
// Black = identical. Red = difference, amplified 6x so faint antialiasing shows.
(async () => {
  await document.fonts.ready;
  const nodes = [...document.querySelectorAll('.diff')];
  // make sure every face we are about to draw is actually loaded
  await Promise.all(nodes.flatMap(n => [n.dataset.a, n.dataset.b].map(f =>
    document.fonts.load(`${n.dataset.weight} ${n.dataset.size}px "${f}"`, n.dataset.text)
      .catch(() => {}))));

  for (const n of nodes) {
    const {text, a, b, size, weight} = n.dataset;
    const s = +size, dpr = 2;
    const cv = n.querySelector('canvas');
    const W = Math.max(320, n.clientWidth), H = Math.ceil(s * 1.9);
    cv.width = W * dpr; cv.height = H * dpr;
    cv.style.height = H + 'px';

    const draw = (fam) => {
      const c = document.createElement('canvas');
      c.width = W * dpr; c.height = H * dpr;
      const x = c.getContext('2d', {willReadFrequently: true});
      x.scale(dpr, dpr);
      x.fillStyle = '#000'; x.fillRect(0, 0, W, H);
      x.fillStyle = '#fff';
      x.font = `${weight} ${s}px "${fam}"`;
      x.textBaseline = 'alphabetic';          // same explicit baseline for both
      x.fillText(text, 4, s * 1.32);
      return x.getImageData(0, 0, c.width, c.height);
    };

    let A, B;
    try { A = draw(a); B = draw(b); } catch (e) { n.querySelector('.dcap').textContent = 'diff failed: ' + e; continue; }

    const ctx = cv.getContext('2d');
    const out = ctx.createImageData(A.width, A.height);
    let ndiff = 0, sum = 0, max = 0, ink = 0;
    for (let i = 0; i < A.data.length; i += 4) {
      const va = A.data[i], vb = B.data[i];
      if (va > 8 || vb > 8) ink++;
      const d = Math.abs(va - vb);
      if (d > 0) { ndiff++; sum += d; if (d > max) max = d; }
      const amp = Math.min(255, d * 6);
      out.data[i] = amp;                          // red channel carries the delta
      out.data[i + 1] = d > 6 ? 0 : amp;
      out.data[i + 2] = d > 6 ? 0 : amp;
      out.data[i + 3] = 255;
    }
    ctx.putImageData(out, 0, 0);

    const mean = ndiff ? (sum / ndiff) : 0;
    const pct = ink ? (100 * ndiff / ink) : 0;
    const cap = n.querySelector('.dcap');

    // measured advance of the whole string in each font
    const mc = document.createElement('canvas').getContext('2d');
    const wof = (f) => { mc.font = `${weight} ${s}px "${f}"`; return mc.measureText(text).width; };
    const wa = wof(a), wb = wof(b);

    if (n.dataset.exact === '1') {
      // Thai: Bai Jamjuree's glyf outlines are copied byte-for-byte, so the
      // stored shapes are identical and compare_th_*.py proves it directly.
      //
      // A browser can still differ by a hair, and it is worth knowing why before
      // reading red here as a defect. Browsers grid-fit (hint); FreeType's
      // autohinter derives its zones from the whole font, and a MERGED font's
      // glyph set can never equal either source's. One glyph lands on a rounding
      // boundary because of it: uni0E47.narrow (the tone mark after ป) is 10 rows
      // tall in both merged families and 9 in Bai at 26px. Unhinted, all three
      // agree exactly. The old CFF build had the identical 1px offset, so this is
      // inherent to merging, not to the format.
      const verdict = ndiff === 0
        ? '<b class="good">PIXEL-IDENTICAL</b>'
        : (pct < 2.0
           ? '<b>grid-fit residue</b> — browser hinting, not a merge defect'
           : '<b class="bad">DIFFERS</b> — too large for grid-fitting; investigate');
      cap.innerHTML = `${a} vs ${b} @${s}px — ${verdict} · ` +
        `${ndiff.toLocaleString()} differing subpixels (${pct.toFixed(1)}% of inked), ` +
        `max Δ ${max}/255 · advance ${wa.toFixed(1)}px vs ${wb.toFixed(1)}px · ` +
        `outline equality is proven byte-for-byte over all 124 Thai-reachable ` +
        `glyphs by <code>compare_th_*.py</code>`;
    } else {
      // Latin: Aeonik/Slussen cubics approximated as quadratics, then rendered by
      // the TrueType engine instead of the CFF one. Edges drift; advances do not.
      // Report it, do not grade it.
      cap.innerHTML = `${a} vs ${b} @${s}px — <b>rasterisation comparison</b> ` +
        `(informational): ${ndiff.toLocaleString()} differing subpixels ` +
        `(${pct.toFixed(1)}% of inked), max Δ ${max}/255 · ` +
        `advance ${wa.toFixed(1)}px vs ${wb.toFixed(1)}px ` +
        `(Δ ${(wa - wb).toFixed(1)}px). Latin cubics were converted to quadratics ` +
        `and now render through the TrueType engine, so faint red here is expected. ` +
        `The bound (mean ≤20/255, advances exact) is asserted by ` +
        `<code>compare_th_*.py</code>, not by this panel.`;
    }
  }
})();
</script>"""


def build():
    css = """
:root{--blue:#2978FF;--blue-light:#82B0FF;--grey1:#CFD9DB;--grey2:#788F9C;
--grey3:#263338;--blue-black:#171C21;--green:#34A853;--red:#E83E3E;
--orange:#FFA000;--white:#FFFFFF;--alt-row:#F0F4F5;}
*{box-sizing:border-box}
body{margin:0;background:var(--alt-row);color:var(--grey3);
font-family:'THAeonik',system-ui,sans-serif;font-size:15px;line-height:1.5;}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 80px}
header{background:var(--blue-black);color:#fff;padding:34px 0 28px;margin-bottom:28px}
header .wrap{padding-bottom:0}
h1{font-size:30px;font-weight:700;margin:0 0 6px}
header p{color:var(--grey1);margin:0;max-width:76ch}
nav{position:sticky;top:0;z-index:20;background:rgba(23,28,33,.97);
backdrop-filter:blur(6px);padding:9px 0;margin-bottom:26px}
nav .wrap{display:flex;gap:6px;flex-wrap:wrap;padding-bottom:0}
nav a{color:var(--grey1);text-decoration:none;font-size:13px;padding:5px 11px;
border-radius:99px}
nav a:hover{background:rgba(255,255,255,.12);color:#fff}
section{background:#fff;border:1px solid var(--grey1);border-radius:10px;
padding:22px 24px;margin-bottom:20px}
h2{font-size:20px;font-weight:700;margin:0 0 4px;scroll-margin-top:60px}
h2 .tag{font-size:11px;font-weight:500;color:#fff;background:var(--blue);
padding:2px 8px;border-radius:99px;vertical-align:3px;margin-left:8px}
h3{font-size:14px;font-weight:600;margin:22px 0 8px;color:var(--grey2);
text-transform:uppercase;letter-spacing:.06em}
.lede{color:var(--grey2);margin:0 0 4px;max-width:80ch}
.grid{display:flex;flex-wrap:wrap;gap:5px}
.grid span{min-width:1.7em;padding:7px 5px;text-align:center;
background:var(--alt-row);border-radius:5px;line-height:1.35}
.tri{margin:14px 0 22px}
.tri-label{font-size:12px;font-weight:600;color:var(--grey2);margin-bottom:6px;
text-transform:uppercase;letter-spacing:.05em}
.tri-label em{font-weight:400;text-transform:none;letter-spacing:0;
color:var(--grey2);margin-left:8px;font-style:italic}
.tri-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.tri-cell{border:1px solid var(--grey1);border-radius:8px;padding:10px 12px;
overflow:hidden}
.tri-cell.merged{border-color:var(--blue);background:#F5F9FF}
.tri-cell b{display:block;font-size:10px;font-weight:600;color:var(--grey2);
letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px}
.tri-cell b i{font-weight:400;text-transform:none;letter-spacing:0}
.tri-cell p{margin:0;line-height:1.45}
.diff{margin:10px 0 14px}
.diff canvas{display:block;width:100%;background:#000;border-radius:8px}
.dcap{font-size:11px;color:var(--grey2);margin:5px 0 0 2px;
font-variant-numeric:tabular-nums}
.dcap b{font-weight:600}
.dcap .good{color:var(--green)}
.dcap .warn{color:var(--orange)}
.dcap .bad{color:var(--red)}
.ramp{border-collapse:collapse;width:100%}
.ramp td{border-bottom:1px solid var(--alt-row);padding:5px 8px;
vertical-align:baseline}
.ramp .sz{width:52px;color:var(--grey2);font-size:11px;text-align:right;
font-variant-numeric:tabular-nums}
.mx{display:grid;grid-template-columns:110px 1fr 1fr;gap:8px;align-items:baseline}
.mx .k{font-size:11px;color:var(--grey2);text-transform:uppercase;
letter-spacing:.05em}
.mx>div{padding:5px 0;border-bottom:1px solid var(--alt-row)}
.note{background:#FFF8E8;border-left:3px solid var(--orange);padding:11px 14px;
border-radius:0 7px 7px 0;margin:14px 0;font-size:13.5px}
.note b{color:#8a5a00}
.ok{background:#F0F9F2;border-left-color:var(--green)}
.ok b{color:#1c6b33}
.ruler{border-top:2px dashed var(--red);margin-top:0;padding-top:0}
.stack-row{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start}
.stack-row div{text-align:center}
.stack-row .cap{font-size:10px;color:var(--grey2);margin-top:2px}
.kern{display:flex;gap:10px;flex-wrap:wrap}
.kern div{border:1px solid var(--grey1);border-radius:7px;padding:8px 12px;
text-align:center}
.kern .cap{font-size:10px;color:var(--grey2);margin-top:4px}
footer{color:var(--grey2);font-size:12.5px;text-align:center;padding:26px 0 0}
code{background:var(--alt-row);padding:1px 5px;border-radius:4px;font-size:.9em;
font-family:ui-monospace,Menlo,Consolas,monospace}

/* ---------- ICHITA report specimen: A4 ---------- */
.page{width:210mm;min-height:297mm;background:#fff;margin:0 auto;
padding:18mm 17mm;box-shadow:0 2px 18px rgba(0,0,0,.14);
font-family:'THAeonik',sans-serif;color:var(--grey3);position:relative}
.stamp{position:absolute;top:12mm;right:17mm;font-size:9px;letter-spacing:.16em;
color:var(--red);border:1px solid var(--red);padding:3px 9px;border-radius:3px;
font-weight:600}
.rpt-head{border-bottom:2px solid var(--blue-black);padding-bottom:9px;
margin-bottom:16px;display:flex;justify-content:space-between;align-items:flex-end}
.rpt-brand{font-size:21px;font-weight:700;letter-spacing:-.01em}
.rpt-brand span{color:var(--blue)}
.rpt-meta{text-align:right;font-size:10.5px;color:var(--grey2);line-height:1.45}
.rpt-title{font-size:25px;font-weight:700;line-height:1.22;margin:0 0 4px}
.rpt-sub{font-size:13px;color:var(--grey2);margin:0 0 16px;font-weight:300}
.rpt h3{font-size:11px;margin:18px 0 6px}
.rpt p{margin:0 0 9px;font-size:11.5px;line-height:1.62}
.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:14px 0 18px}
.kpi div{background:var(--alt-row);border-radius:7px;padding:10px 11px}
.kpi .n{font-size:19px;font-weight:700;line-height:1.15;
font-variant-numeric:tabular-nums}
.kpi .l{font-size:9.5px;color:var(--grey2);margin-top:2px;line-height:1.35}
.kpi .up{color:var(--green)}.kpi .dn{color:var(--red)}
table.rpt-t{width:100%;border-collapse:collapse;font-size:10.5px;margin:6px 0 14px}
table.rpt-t th{background:var(--blue-black);color:#fff;text-align:left;
padding:6px 8px;font-weight:600;font-size:9.5px;letter-spacing:.04em;
text-transform:uppercase}
table.rpt-t td{padding:5px 8px;border-bottom:1px solid var(--grey1)}
table.rpt-t tr:nth-child(even) td{background:var(--alt-row)}
table.rpt-t .num{text-align:right;font-variant-numeric:tabular-nums}
.callout{background:#F5F9FF;border-left:3px solid var(--blue);padding:10px 13px;
border-radius:0 7px 7px 0;margin:12px 0;font-size:11px;line-height:1.6}
.rpt ul{margin:0 0 10px;padding-left:17px;font-size:11.5px;line-height:1.62}
.rpt li{margin-bottom:3px}
.rpt-foot{border-top:1px solid var(--grey1);margin-top:20px;padding-top:8px;
display:flex;justify-content:space-between;font-size:9px;color:var(--grey2)}
.switcher{display:flex;gap:8px;align-items:center;margin:0 0 14px;font-size:13px}
.switcher button{font-family:inherit;font-size:12.5px;border:1px solid var(--grey1);
background:#fff;padding:6px 14px;border-radius:99px;cursor:pointer;color:var(--grey3)}
.switcher button.on{background:var(--blue-black);color:#fff;border-color:var(--blue-black)}

@media print{
  body{background:#fff}
  header,nav,footer,section,.switcher{display:none!important}
  .page{box-shadow:none;margin:0;width:auto;min-height:0;padding:0}
  #report{display:block!important}
}
"""

    def sec(id_, title, tag, lede, body):
        t = f'<span class="tag">{tag}</span>' if tag else ""
        return (f'<section id="{id_}"><h2>{title}{t}</h2>'
                f'<p class="lede">{lede}</p>{body}</section>')

    # ---- character inventories -------------------------------------------
    def inventory(merged, latin_ref, thai_ref):
        return f"""
<h3>Latin uppercase — {merged} vs {latin_ref}</h3>
{grid(UPPER, merged)}{grid(UPPER, latin_ref)}
<h3>Latin lowercase</h3>
{grid(LOWER, merged)}{grid(LOWER, latin_ref)}
<h3>Figures &amp; punctuation</h3>
{grid(DIGITS + PUNCT, merged)}{grid(DIGITS + PUNCT, latin_ref)}
<h3>Thai consonants (44) — {merged} vs {thai_ref}</h3>
{grid(CONSONANTS, merged)}{grid(CONSONANTS, thai_ref)}
<h3>Thai vowels &amp; signs</h3>
{grid(VOWELS, merged)}{grid(VOWELS, thai_ref)}
<h3>Combining marks on base ก — the glyphs that must carry zero advance</h3>
{grid(MARKS, merged, 30)}{grid(MARKS, thai_ref, 30)}
<h3>Thai digits</h3>
{grid(THAI_DIGITS, merged)}{grid(THAI_DIGITS, thai_ref)}"""

    aeonik_matrix = "".join(
        f'<div class="k">{n}</div>'
        f'<div style="font-family:\'THAeonik\';font-weight:{w};font-style:{s};font-size:21px">{PANGRAM_LATIN[:30]}</div>'
        f'<div lang="th" style="font-family:\'THAeonik\';font-weight:{w};font-style:{s};font-size:21px">สวัสดีครับ ประเทศไทย</div>'
        for n, w, s in [("Light 300", 300, "normal"), ("Light Italic", 300, "italic"),
                        ("Regular 400", 400, "normal"), ("Regular Italic", 400, "italic"),
                        ("Bold 700", 700, "normal"), ("Bold Italic", 700, "italic")])

    slussen_matrix = "".join(
        f'<div class="k">{n}</div>'
        f'<div style="font-family:\'THSlussen\';font-weight:{w};font-size:21px">{PANGRAM_LATIN[:30]}</div>'
        f'<div lang="th" style="font-family:\'THSlussen\';font-weight:{w};font-size:21px">สวัสดีครับ ประเทศไทย</div>'
        for n, w in [("Regular 400", 400), ("Medium 500", 500),
                     ("SemiBold 600", 600), ("Bold 700", 700)])

    stacks_big = "".join(
        f'<div><span lang="th" style="font-family:\'THAeonik\';font-size:64px;'
        f'font-weight:700">{w}</span><div class="cap">{w}</div></div>'
        for w in STACKS)
    stacks_slu = "".join(
        f'<div><span lang="th" style="font-family:\'THSlussen\';font-size:64px;'
        f'font-weight:700">{w}</span><div class="cap">{w}</div></div>'
        for w in STACKS)

    kern_cells = "".join(
        f'<div><div style="font-family:\'THAeonik\';font-size:34px">{p}</div>'
        f'<div style="font-family:\'Aeonik\';font-size:34px">{p}</div>'
        f'<div class="cap">{p}</div></div>' for p in KERN_PAIRS)

    body = f"""
{sec("read", "How to read this page", "",
  "Every comparison puts the merged font next to the two fonts it was built from. "
  "The merge is correct only if it is invisible: Latin should be indistinguishable "
  "from Aeonik/Slussen, Thai indistinguishable from Bai Jamjuree.",
  """<div class="note ok"><b>Difference overlays.</b> The black panels stack the merged
  font directly on top of its source using <code>mix-blend-mode:difference</code>.
  <b>Pure black means pixel-identical.</b> Any white ghosting is a mismatch.
  <b>Thai must be pure black</b> — the merged families ship as TrueType and carry
  Bai Jamjuree's outlines verbatim. Faint grey edges are now expected on
  <b>Latin</b> instead: Aeonik/Slussen cubics are approximated as quadratics and
  rendered by a different engine, which moves antialiasing by up to 16/255
  without moving a single advance or position. Thai panels may show a trace of
  red from browser <i>grid-fitting</i>: the autohinter's zones are derived from
  the whole font, and a merged font's glyph set cannot equal either source's.
  That is a rasteriser artefact — the stored Thai outlines are verified
  byte-for-byte against Bai Jamjuree across all 124 reachable glyphs, including
  the GSUB-only tone-mark variants no cmap-based test can reach.</div>
  <div class="note"><b>Two defects cannot be seen here.</b> Coverage-table ordering
  only affects Uniscribe/DirectWrite on Windows, and the family-naming fix only
  shows up in a font picker. Browsers use HarfBuzz and their own font matching, so
  both look fine here regardless. Those need Word on Windows.</div>""")}

{sec("aeonik", "TH Aeonik", "Aeonik + Bai Jamjuree",
  "Six weights: Light, Regular and Bold, each upright and italic.",
  triptych("Latin — must match Aeonik within the conversion bound", PANGRAM_LATIN, "THAeonik", "Aeonik", "Bai", 19)
  + triptych("Thai — must be PIXEL-IDENTICAL to Bai Jamjuree", PANGRAM_THAI, "THAeonik", "Aeonik", "Bai", 19,
             note="the Aeonik cell has no Thai — that is the point of the merge")
  + triptych("Mixed", MIXED, "THAeonik", "Aeonik", "Bai", 19)
  + '<h3>Difference overlay — Latin, TH Aeonik over Aeonik</h3>'
  + overlay(PANGRAM_LATIN, "THAeonik", "Aeonik", 26)
  + overlay("Hamburgefonstiv AVATAR 0123456789", "THAeonik", "Aeonik", 26, 700)
  + '<h3>Difference overlay — Thai, TH Aeonik over Bai Jamjuree</h3>'
  + overlay(PANGRAM_THAI_NOSPACE, "THAeonik", "Bai", 26, 400, "th")
  + overlay(STACKS_NOSPACE, "THAeonik", "Bai", 26, 700, "th"))}

{sec("aeonik-chars", "TH Aeonik — every character", "inventory",
  "Merged font on the first row of each pair, source font on the second. "
  "Scan for shape changes, missing glyphs and spacing drift.",
  inventory("THAeonik", "Aeonik", "Bai"))}

{sec("aeonik-sizes", "TH Aeonik — size ramp", "8–72px",
  "The sizes the acceptance test rasterises at. Small sizes are where hinting and "
  "rounding differences would surface first.",
  '<h3>Latin</h3>' + size_ramp("THAeonik", PANGRAM_LATIN)
  + '<h3>Thai</h3>' + size_ramp("THAeonik", PANGRAM_THAI, "th")
  + '<h3>Mixed</h3>' + size_ramp("THAeonik", MIXED, "th"))}

{sec("aeonik-weights", "TH Aeonik — weights and italics", "6 faces",
  "Italic weights were the ones that broke two earlier fix attempts, because "
  "Aeonik's italics ship a stub Thai script record the uprights do not have. "
  "Thai must render in all six.",
  f'<div class="mx">{aeonik_matrix}</div>')}

{sec("slussen", "TH Slussen", "Slussen + Bai Jamjuree",
  "Four weights: Regular, Medium, SemiBold, Bold. No italics.",
  triptych("Latin — must match Slussen within the conversion bound", PANGRAM_LATIN, "THSlussen", "Slussen", "Bai", 19)
  + triptych("Thai — must be PIXEL-IDENTICAL to Bai Jamjuree", PANGRAM_THAI, "THSlussen", "Slussen", "Bai", 19)
  + triptych("Mixed", MIXED, "THSlussen", "Slussen", "Bai", 19)
  + '<h3>Difference overlay — Latin, TH Slussen over Slussen</h3>'
  + overlay(PANGRAM_LATIN, "THSlussen", "Slussen", 26)
  + overlay("Hamburgefonstiv AVATAR 0123456789", "THSlussen", "Slussen", 26, 700)
  + '<h3>Difference overlay — Thai, TH Slussen over Bai Jamjuree</h3>'
  + overlay(PANGRAM_THAI_NOSPACE, "THSlussen", "Bai", 26, 400, "th"))}

{sec("slussen-chars", "TH Slussen — every character", "inventory",
  "Same layout: merged font first, source second.",
  inventory("THSlussen", "Slussen", "Bai"))}

{sec("slussen-sizes", "TH Slussen — size ramp", "8–72px", "",
  '<h3>Latin</h3>' + size_ramp("THSlussen", PANGRAM_LATIN)
  + '<h3>Thai</h3>' + size_ramp("THSlussen", PANGRAM_THAI, "th")
  + '<h3>Mixed</h3>' + size_ramp("THSlussen", MIXED, "th"))}

{sec("slussen-weights", "TH Slussen — weights", "4 faces",
  "Regular, Medium and SemiBold previously shared one family+subfamily name and "
  "were indistinguishable to Windows. That is a font-picker symptom, not a "
  "rendering one — check it in Word, not here.",
  f'<div class="mx">{slussen_matrix}</div>')}

{sec("defects", "Targeted checks for the defects that were fixed", "regression",
  "Each block below is the visual counterpart of one thing the acceptance tests "
  "assert numerically.",
  f"""
<h3>Tone-mark clipping — <code>usWinAscent</code> too small</h3>
<p class="lede">Two-level stacks (consonant + upper vowel + tone mark) reach highest.
The red dashed line is the old TH-Aeonik ceiling relative to these glyphs; nothing
should be cut off at the top now.</p>
<div class="ruler"></div>
<div class="stack-row">{stacks_big}</div>
<div class="stack-row" style="margin-top:14px">{stacks_slu}</div>

<h3>Latin kerning — Aeonik's GPOS must survive the merge</h3>
<p class="lede">Each cell shows TH Aeonik above, Aeonik below. The two lines must sit
identically; when Bai Jamjuree's kerning replaced Aeonik's, these pairs drifted apart
by 20–50 units.</p>
<div class="kern">{kern_cells}</div>

<h3>Mark advances — combining marks must consume no width</h3>
<p class="lede">If the CFF charstring widths disagree with <code>hmtx</code>, marks
gain a real advance and detach from their consonant. This is the defect that made
printed PDFs unreadable.</p>
{overlay(TONE_RAMP_NOSPACE, "THAeonik", "Bai", 40, 400, "th")}
{overlay(TONE_RAMP_NOSPACE, "THSlussen", "Bai", 40, 400, "th")}""")}
"""

    report = f"""
<div class="switcher">
  <button class="on" onclick="document.getElementById('rpt').style.fontFamily=&quot;'THAeonik',sans-serif&quot;;
    this.parentNode.querySelectorAll('button').forEach(b=>b.classList.remove('on'));this.classList.add('on')">TH Aeonik</button>
  <button onclick="document.getElementById('rpt').style.fontFamily=&quot;'THSlussen',sans-serif&quot;;
    this.parentNode.querySelectorAll('button').forEach(b=>b.classList.remove('on'));this.classList.add('on')">TH Slussen</button>
  <span style="color:var(--grey2);font-size:12px">— switch the whole report between families</span>
</div>
<div class="page rpt" id="rpt">
  <div class="stamp">SPECIMEN</div>
  <div class="rpt-head">
    <div class="rpt-brand">ICHITA<span>.</span></div>
    <div class="rpt-meta">รายงานผลการดำเนินงานรายไตรมาส<br>
      Quarterly Performance Report · Q3 FY2026<br>
      ออกเมื่อ 1 สิงหาคม 2569 · Ref. ICH-Q3-2026-014</div>
  </div>

  <h1 class="rpt-title">ผลประกอบการไตรมาสที่ 3<br>Q3 Performance &amp; Product Outlook</h1>
  <p class="rpt-sub">ฝ่ายวางแผนกลยุทธ์ · Strategic Planning Division · จัดทำโดย ทีมวิเคราะห์ข้อมูล</p>

  <div class="kpi">
    <div><div class="n">฿248.6M</div><div class="l">รายได้รวม<br>Total revenue</div></div>
    <div><div class="n up">+12.5%</div><div class="l">เติบโตเทียบปีก่อน<br>YoY growth</div></div>
    <div><div class="n">฿61.2M</div><div class="l">กำไรขั้นต้น<br>Gross profit</div></div>
    <div><div class="n dn">−3.1%</div><div class="l">ต้นทุนวัตถุดิบ<br>Material cost</div></div>
  </div>

  <h3>บทสรุปผู้บริหาร · Executive Summary</h3>
  <p>ไตรมาสที่ 3 ปีงบประมาณ 2569 บริษัท อิชิตะ จำกัด (มหาชน) มีรายได้รวม 248.6 ล้านบาท
  เพิ่มขึ้นร้อยละ 12.5 เมื่อเทียบกับช่วงเดียวกันของปีก่อน โดยได้รับแรงหนุนหลักจากกลุ่มผลิตภัณฑ์
  <b>Ichita Green Tea</b> ซึ่งเติบโตอย่างต่อเนื่องเป็นไตรมาสที่สี่ติดต่อกัน ขณะที่ต้นทุนวัตถุดิบ
  ปรับตัวลดลงร้อยละ 3.1 จากการเจรจาสัญญาระยะยาวกับผู้จัดจำหน่ายรายใหญ่</p>

  <div class="callout">
    <b>ข้อสังเกตสำคัญ · Key observation</b><br>
    ช่องทางจำหน่ายออนไลน์ (e-commerce) มีสัดส่วนเพิ่มขึ้นจากร้อยละ 18 เป็นร้อยละ 27 ของยอดขายรวม
    ภายในสี่ไตรมาส ซึ่งเร็วกว่าที่ประมาณการไว้ในแผนกลยุทธ์ฉบับเดือนมกราคม
  </div>

  <h3>ผลการดำเนินงานรายผลิตภัณฑ์ · Performance by Product Line</h3>
  <table class="rpt-t">
    <tr><th>ผลิตภัณฑ์ / Product</th><th>ขนาด</th>
        <th class="num">Q2 (฿M)</th><th class="num">Q3 (฿M)</th>
        <th class="num">Δ %</th><th>สถานะ</th></tr>
    <tr><td>Ichita Green Tea — ชาเขียวต้นตำรับ</td><td>500 ml</td>
        <td class="num">72.4</td><td class="num">86.1</td>
        <td class="num">+18.9</td><td>เติบโตสูง</td></tr>
    <tr><td>Ichita Honey Lemon — น้ำผึ้งมะนาว</td><td>350 ml</td>
        <td class="num">41.8</td><td class="num">45.3</td>
        <td class="num">+8.4</td><td>เติบโต</td></tr>
    <tr><td>Ichita Barley — ชาข้าวบาร์เลย์</td><td>500 ml</td>
        <td class="num">33.9</td><td class="num">34.2</td>
        <td class="num">+0.9</td><td>คงที่</td></tr>
    <tr><td>Ichita Sparkling Yuzu — ยูซุอัดลม</td><td>325 ml</td>
        <td class="num">28.6</td><td class="num">24.7</td>
        <td class="num">−13.6</td><td>ทบทวน</td></tr>
    <tr><td>Ichita Original — สูตรดั้งเดิม</td><td>1,000 ml</td>
        <td class="num">44.2</td><td class="num">48.9</td>
        <td class="num">+10.6</td><td>เติบโต</td></tr>
  </table>

  <h3>ประเด็นที่ต้องติดตาม · Items Requiring Attention</h3>
  <ul>
    <li>ผลิตภัณฑ์ <b>Sparkling Yuzu</b> ยอดขายลดลงร้อยละ 13.6 ควรทบทวนกลยุทธ์ราคาและช่องทางจัดจำหน่าย
        ภายในสิ้นเดือนกันยายน</li>
    <li>กำลังการผลิตของโรงงานที่ 2 (จังหวัดชลบุรี) อยู่ที่ร้อยละ 91 ซึ่งใกล้เต็มกำลัง
        — เสนอให้พิจารณาแผนขยายกำลังการผลิตในไตรมาสถัดไป</li>
    <li>ต้นทุนบรรจุภัณฑ์ PET คาดว่าจะปรับขึ้นร้อยละ 4–6 ใน Q4 ตามราคาน้ำมันดิบ</li>
    <li>เตรียมทดสอบตลาดผลิตภัณฑ์ใหม่ <i>Ichita Matcha Latte</i> ในเขตกรุงเทพฯ และปริมณฑล เดือนตุลาคม</li>
  </ul>

  <h3>แผนดำเนินการไตรมาสถัดไป · Next Quarter Plan</h3>
  <p>ฝ่ายกลยุทธ์เสนอให้จัดสรรงบประมาณการตลาดเพิ่มเติมจำนวน 12.5 ล้านบาท ไปยังช่องทางออนไลน์
  โดยเน้นกลุ่มผู้บริโภคอายุ 25–34 ปี ซึ่งมีอัตราการซื้อซ้ำสูงที่สุดที่ร้อยละ 63.8 ทั้งนี้
  คณะกรรมการบริหารจะพิจารณาอนุมัติในการประชุมวันที่ 15 สิงหาคม 2569</p>

  <div class="rpt-foot">
    <span>ICHITA Public Company Limited · เอกสารตัวอย่างสำหรับทดสอบการแสดงผลฟอนต์เท่านั้น</span>
    <span>หน้า 1 / 1</span>
  </div>
</div>"""

    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TH Aeonik &amp; TH Slussen — visual test</title>
<style>{font_faces()}
{css}</style>
<header><div class="wrap">
  <h1>TH Aeonik &amp; TH Slussen — visual test</h1>
  <p>Merged Thai/Latin families rendered beside the fonts they were built from,
  plus a formatted mixed-language report specimen. Fonts are embedded in this
  file, so what you see does not depend on what is installed.</p>
</div></header>
<nav><div class="wrap">
  <a href="#read">How to read</a>
  <a href="#aeonik">TH Aeonik</a>
  <a href="#aeonik-chars">· characters</a>
  <a href="#aeonik-sizes">· sizes</a>
  <a href="#aeonik-weights">· weights</a>
  <a href="#slussen">TH Slussen</a>
  <a href="#slussen-chars">· characters</a>
  <a href="#slussen-sizes">· sizes</a>
  <a href="#slussen-weights">· weights</a>
  <a href="#defects">Regression checks</a>
  <a href="#report">ICHITA report</a>
</div></nav>
<div class="wrap">
{body}
<section id="report"><h2>ICHITA report specimen<span class="tag">A4 · mixed Thai/Latin</span></h2>
<p class="lede">A single formatted page exercising headings, tabular figures, a data
table, bullets and a callout in mixed Thai and English — the shapes real documents
actually take. Use your browser's Print to PDF on this page: it prints the report
alone, and the resulting PDF is a useful check of the text layer.</p>
{report}
</section>
<footer>Generated by <code>scripts/build_font_specimen.py</code> ·
regenerate after any font rebuild · report content is fictional test data</footer>
</div>
{DIFF_SCRIPT}
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for fam, _, _, path in FACES:
        if fam not in BASELINE and path.exists():
            BASELINE[fam] = baseline_fraction(path)
    print("  baselines (em below line-box top, line-height:1):")
    for fam, v in sorted(BASELINE.items()):
        print(f"     {fam:11} {v:.4f}")
    html = build()
    OUT.write_text(html, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(ROOT)}  ({len(html.encode())/1024/1024:.1f} MB, "
          f"{len(FACES)} font faces embedded)")
