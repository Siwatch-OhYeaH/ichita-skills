#!/usr/bin/env python3
"""
Render TH Aeonik specimen sheets.

Writes self-contained HTML to docs/specimens/ and, when a Chromium binary is
available, a PNG beside each one. The sheets are built from the font files
themselves -- family names, style slots and weight classes are read out of the
`name` and `OS/2` tables rather than hardcoded -- so a sheet always describes
the fonts as they actually are.

  weight-scale       the ten weights, Latin and Thai, upright and italic
  all-styles         all 20 faces with the family/style each registers under
  word-bold-italic   what Ctrl+B and Ctrl+I do per family in Word/PowerPoint
  bold-all-families  Bold across every font family in assets/fonts

Usage:
  python3 make_specimens.py                  # all sheets
  python3 make_specimens.py --only word-bold-italic
  CHROME=/path/to/chrome python3 make_specimens.py
"""

import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from fontTools.ttLib import TTFont

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent
ASSETS = SCRIPT_DIR.parent / "assets" / "fonts"
TH = ASSETS / "aeonik-th"
OUT = SCRIPT_DIR.parent / "docs" / "specimens"

SCALE = [("Air", 100), ("Thin", 200), ("Light", 300), ("Book", 350),
         ("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700),
         ("ExtraBold", 800), ("Black", 900)]

LATIN_SAMPLE = "Hamburgefonstiv 123"
THAI_SAMPLE = "สวัสดีครับ ภาษาไทย น้ำ ปั๊ม"

CSS_BASE = """
body{background:#fff;color:#111;font-family:system-ui,sans-serif;margin:0;padding:24px 30px}
h1{font:600 16px system-ui;margin:0 0 3px}
.sub{font:12px system-ui;color:#666;margin-bottom:15px;max-width:1050px;line-height:1.5}
.row{display:flex;gap:20px;align-items:center;border-top:1px solid #eee;padding:9px 0}
.meta{flex:none;font:10.5px system-ui;color:#999;display:flex;flex-direction:column}
.meta b{font-size:12.5px;color:#111}
.nm{color:#bbb;font-size:10px}
.ok{color:#178a3a;font-weight:600}
.bad{color:#c62222;font-weight:700}
.none{font:italic 13px system-ui;color:#bbb}
"""


def name_of(font, nid):
    rec = font["name"].getName(nid, 3, 1, 0x409)
    return rec.toUnicode() if rec else "—"


def face_path(style, italic):
    return TH / f"TH-Aeonik-{style}{'Italic' if italic else ''}.otf"


def font_face(family, path, weight=400, style="normal"):
    fmt = "opentype" if path.suffix == ".otf" else "truetype"
    return (f"@font-face{{font-family:'{family}';src:url('file://{path.resolve()}') "
            f"format('{fmt}');font-weight:{weight};font-style:{style};}}")


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------

def sheet_weight_scale():
    css, rows = [], []
    for style, wght in SCALE:
        for italic in (False, True):
            css.append(font_face("THA", face_path(style, italic), wght,
                                 "italic" if italic else "normal"))
    for style, wght in SCALE:
        rows.append(f"""<div class=row>
  <div class=meta style="width:100px"><b>{style}</b><span>{wght}</span></div>
  <div style="font-family:'THA';font-weight:{wght};display:flex;gap:26px;align-items:baseline">
    <div style="font-size:27px">{LATIN_SAMPLE}</div>
    <div style="font-size:27px">{THAI_SAMPLE}</div>
    <div style="font-size:23px;font-style:italic;color:#555">Italic ตัวเอียง</div>
  </div></div>""")
    return ("TH Aeonik — ten-step weight scale",
            "Aeonik (Latin) + Bai Jamjuree (Thai). The Thai flattens at both ends of "
            "the scale: Bai Jamjuree ships 200–700 and cannot be pushed past it.",
            "".join(css), "".join(rows))


def sheet_all_styles():
    css, rows, i = [], [], 0
    for style, wght in SCALE:
        for italic in (False, True):
            p = face_path(style, italic)
            f = TTFont(str(p))
            css.append(font_face(f"S{i}", p))
            rows.append(f"""<div class=row>
  <div class=meta style="width:250px"><b>{style}{' Italic' if italic else ''}</b>
    <span>{wght}{' · italic' if italic else ''}</span>
    <span class=nm>ID1 “{name_of(f, 1)}” · ID2 “{name_of(f, 2)}”</span></div>
  <div style="display:flex;gap:34px;align-items:baseline;white-space:nowrap">
    <div style="font-family:'S{i}';font-size:27px">Hamburgefonstiv</div>
    <div style="font-family:'S{i}';font-size:27px">สวัสดีครับ ภาษาไทย น้ำ</div>
  </div></div>""")
            i += 1
    return ("TH Aeonik — all 20 styles",
            "Ten weights, upright and italic. ID1/ID2 are the family and style slot "
            "each face registers under in Windows.",
            "".join(css), "".join(rows))


def sheet_word_bold_italic():
    # Group faces the way Word sees them: by nameID1, into RIBBI slots.
    families = {}
    for style, _ in SCALE:
        for italic in (False, True):
            p = face_path(style, italic)
            f = TTFont(str(p))
            families.setdefault(name_of(f, 1), {})[name_of(f, 2)] = p

    order = ["TH Aeonik"] + [f"TH Aeonik {s}" for s, _ in SCALE
                             if f"TH Aeonik {s}" in families]
    css, rows = [], []
    for family in order:
        slots = families[family]
        safe = family.replace(" ", "_")
        for slot, path in slots.items():
            css.append(font_face(safe, path,
                                 700 if "Bold" in slot else 400,
                                 "italic" if "Italic" in slot else "normal"))
        has_bold = "Bold" in slots
        cells = []
        for label, wght, st in [("plain", 400, "normal"), ("Ctrl+B", 700, "normal"),
                                ("Ctrl+I", 400, "italic"), ("Ctrl+B+I", 700, "italic")]:
            faux = wght == 700 and not has_bold
            tag = (f"<span class='{'bad' if faux else 'ok'}'>"
                   f"{'FAUX' if faux else 'real'}</span>")
            cells.append(
                f"<div style='width:210px'><div style='font:9.5px system-ui;color:#aaa'>"
                f"{label} {tag}</div>"
                f"<div style=\"font-family:'{safe}';font-weight:{wght};font-style:{st};"
                f"font-size:25px;white-space:nowrap\">Hamburg ไทย</div></div>")
        rows.append(
            f"<div class=row><div class=meta style='width:200px'><b>{family}</b>"
            f"<span>styles in family: {', '.join(sorted(slots))}</span></div>"
            f"<div style='display:flex;gap:16px'>{''.join(cells)}</div></div>")
    return ("What Bold / Italic actually do in Word &amp; PowerPoint",
            "Each family is registered with exactly the styles it exposes to Word, so "
            "these Ctrl+B and Ctrl+I results are produced the same way Word produces "
            "them: with no real Bold in the family, the app smears the outline to fake "
            "one (FAUX).",
            "".join(css), "".join(rows))


def sheet_bold_all_families():
    candidates = [
        ("TH Aeonik Bold", "aeonik-th/TH-Aeonik-Bold.otf", "merged: Aeonik + Bai Jamjuree"),
        ("TH Aeonik Bold Italic", "aeonik-th/TH-Aeonik-BoldItalic.otf", "merged: Aeonik + Bai Jamjuree"),
        ("Aeonik Bold", "aeonik/Aeonik-Bold.otf", "Latin source"),
        ("Aeonik Bold Italic", "aeonik/Aeonik-BoldItalic.otf", "Latin source"),
        ("Bai Jamjuree Bold", "bai-jamjuree/BaiJamjuree-Bold.ttf", "Thai source"),
        ("Bai Jamjuree Bold Italic", "bai-jamjuree/BaiJamjuree-BoldItalic.ttf", "Thai source"),
        ("TH Slussen Bold", "slussen-th/TH-Slussen-Bold.otf", "merged: Slussen + Bai Jamjuree"),
        ("Slussen Bold", "slussen/Slussen-Bold.otf", "Latin source"),
    ]
    css, rows = [], []
    for i, (label, rel, note) in enumerate(candidates):
        p = ASSETS / rel
        if not p.exists():
            continue
        f = TTFont(str(p))
        thai = sum(1 for c in f.getBestCmap() if 0x0E01 <= c <= 0x0E5B)
        css.append(font_face(f"B{i}", p))
        thai_cell = (f"<div style=\"font-family:'B{i}';font-size:30px\">{THAI_SAMPLE}</div>"
                     if thai >= 80 else "<div class=none>no Thai coverage</div>")
        rows.append(f"""<div class=row>
  <div class=meta style="width:210px"><b>{label}</b><span>{note}</span>
    <span>wght {f['OS/2'].usWeightClass} · {thai} Thai glyphs</span></div>
  <div style="display:flex;gap:30px;align-items:baseline;flex-wrap:wrap">
    <div style="font-family:'B{i}';font-size:30px">{LATIN_SAMPLE}</div>
    {thai_cell}
  </div></div>""")
    return ("Bold — every font family in assets/fonts",
            "Betatron is omitted: it ships Regular only. TH Slussen has no italics.",
            "".join(css), "".join(rows))


SHEETS = {
    "weight-scale": (sheet_weight_scale, (1180, 620)),
    "all-styles": (sheet_all_styles, (1240, 1760)),
    "word-bold-italic": (sheet_word_bold_italic, (1180, 790)),
    "bold-all-families": (sheet_bold_all_families, (1250, 760)),
}


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for pattern in ["/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                    "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"]:
        hits = sorted(Path("/").glob(pattern.lstrip("/")))
        if hits:
            return str(hits[-1])
    for name in ["chromium", "chromium-browser", "google-chrome", "chrome"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def render(html_path, png_path, size, chrome):
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--allow-file-access-from-files", "--force-device-scale-factor=2",
         f"--window-size={size[0]},{size[1]}",
         f"--screenshot={png_path}", str(html_path)],
        capture_output=True, timeout=180,
    )
    return png_path.exists()


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Render TH Aeonik specimen sheets")
    ap.add_argument("--only", default=None, help=f"one of: {', '.join(SHEETS)}")
    ap.add_argument("--no-png", action="store_true", help="write HTML only")
    args = ap.parse_args()

    names = [args.only] if args.only else list(SHEETS)
    unknown = [n for n in names if n not in SHEETS]
    if unknown:
        print(f"unknown sheet(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    chrome = None if args.no_png else find_chrome()
    if not args.no_png and not chrome:
        print("  note: no Chromium found; writing HTML only (set CHROME=... for PNGs)")

    for name in names:
        builder, size = SHEETS[name]
        title, subtitle, css, rows = builder()
        html = (f"<meta charset=utf-8><title>{title}</title>"
                f"<style>{css}{CSS_BASE}</style>"
                f"<h1>{title}</h1><div class=sub>{subtitle}</div>{rows}")
        html_path = OUT / f"{name}.html"
        html_path.write_text(html, encoding="utf-8")
        line = f"  {name}: {html_path.relative_to(SCRIPT_DIR.parent)}"
        if chrome:
            png_path = OUT / f"{name}.png"
            if render(html_path, png_path, size, chrome):
                line += f" + {png_path.name} ({png_path.stat().st_size // 1024} KB)"
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
