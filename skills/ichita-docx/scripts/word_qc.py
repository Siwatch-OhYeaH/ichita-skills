#!/usr/bin/env python3
"""
word_qc.py — check a .docx the way the reader will see it, before anyone says "done".

    python3 word_qc.py FILE.docx                      # Word check + line check
    python3 word_qc.py FILE.docx --pdf FILE.pdf       # ... and write the delivery PDF
    python3 word_qc.py FILE.docx --pdf FILE.pdf --png DIR

What it does, and what each step is for:

  1. Word (Windows, from WSL through powershell.exe + COM) — the acceptance renderer.
     Page count, and every spelling flag split into Thai and Latin. A Thai flag on a
     fixed file is a real word Word does not know (or a misspelling), never a tagging
     fault — so each one is listed for a person to decide.
     Word also prints the file through "Microsoft Print to PDF" into DIR, for the page
     images only: that PDF's Thai text layer drops tone marks (measured 2026-09-24,
     ้ 76 -> 47), so it is never delivered.
  2. The delivery PDF — LibreOffice headless (ichita-convert reference/pdf-delivery.md:
     brand fonts embedded, Thai text layer intact). Checked: every embedded font is a
     brand face, and every Thai character of the source is in the text layer.
     LibreOffice lays Thai lines out with its own dictionary, not Word's, so its page
     count and line breaks can differ from the .docx — both are reported.
  3. Line check, on both layouts — lines that start with a closing bracket, "/", a dash
     or a Thai following vowel or tone mark; lines that end on a Thai leading vowel, an
     opening bracket, a hyphen, a number or a title (Mr, Dr, นาย, คุณ ...); a single word
     left on the last line of a block. Thai split in the middle of a word is NOT detected — read
     the page images.
  Also: tables wider than the text block (WARN), and --pages N (FAIL on any other count).
  4. Page images of both layouts into DIR, to be read, every page, every line.

Exit status 1 when a check FAILs (non-brand font, Thai text lost, Word unreachable with
--require-word). Thai spelling flags and line flags are WARN: a person decides.
Word runs hidden with alerts off; a Word it started is killed if it overruns --timeout.
"""
import argparse, collections, json, os, re, shutil, subprocess, sys, tempfile, unicodedata, zipfile
from pathlib import Path

BRAND = re.compile(r"^(?:[A-Z]{6}\+)?(TH-?Aeonik|Aeonik|Betatron|BaiJamjuree|Bai-Jamjuree)", re.I)
THAI = re.compile("[฀-๿]")
FOLLOW = "ะัาำิีึืฺุูๅๆ็่้๊๋์ํ๎"
LEAD = "เแโใไ"
TITLES = {"Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Dr", "Dr.", "Prof", "Prof.", "นาย", "นาง", "นางสาว", "ดร.", "คุณ"}

PS = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$src = $args[0]; $pdf = $args[1]
$before = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object Id)
$w = New-Object -ComObject Word.Application
$w.Visible = $false; $w.DisplayAlerts = 0
$mine = @(Get-Process WINWORD | Where-Object { $before -notcontains $_.Id } | ForEach-Object Id)
[Console]::Out.WriteLine("PID " + ($mine -join ','))
$res = @{ thai = @(); latin = @() }
$prev = $w.ActivePrinter
try {
  $d = $w.Documents.Open($src, $false, $true, $false)
  $d.SpellingChecked = $false
  foreach ($r in $d.Range().SpellingErrors) {
    if ($r.Text -match '[฀-๿]') { $res.thai += $r.Text } else { $res.latin += $r.Text } }
  $res.pages = $d.ComputeStatistics(2)
  if ($pdf) {
    $w.ActivePrinter = 'Microsoft Print to PDF'
    $d.PrintOut($false, $false, 0, $pdf, '', '', 0, 1, '', 0, $true)
  }
  $d.Close($false)
} finally {
  if ($pdf) { $w.ActivePrinter = $prev }
  $w.Quit()
}
[Console]::Out.WriteLine("JSON " + ($res | ConvertTo-Json -Compress))
"""


def win_temp():
    out = subprocess.run(["cmd.exe", "/c", "echo %TEMP%"], capture_output=True, text=True,
                         cwd="/mnt/c").stdout.strip()
    return out, subprocess.run(["wslpath", "-u", out], capture_output=True, text=True).stdout.strip()


def word_check(docx, want_pdf, timeout):
    """-> (result dict or None, reason, print-pdf path or None)"""
    if not shutil.which("powershell.exe"):
        return None, "powershell.exe not reachable — not WSL on a Windows machine", None
    wtmp, ltmp = win_temp()
    work = Path(tempfile.mkdtemp(prefix="ichita-word-qc-", dir=ltmp))
    wwork = wtmp + "\\" + work.name
    shutil.copy(docx, work / "in.docx")                     # ASCII name: no path encoding issues
    (work / "qc.ps1").write_bytes(b"\xef\xbb\xbf" + PS.encode("utf-8"))   # BOM: PowerShell 5 reads UTF-8
    args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", wwork + "\\qc.ps1",
            wwork + "\\in.docx", (wwork + "\\word-print.pdf") if want_pdf else ""]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                         cwd="/mnt/c")
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        pid = re.search(r"PID ([\d,]+)", out or "")
        if pid:
            for x in pid.group(1).split(","):
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {x} -Force"],
                               capture_output=True)
        return None, f"Word did not finish in {timeout}s (a hidden dialog?) — killed the Word it started", None
    m = re.search(r"^JSON (.*)$", out or "", re.M)
    if not m:
        return None, "Word failed: " + (err or out).strip()[-400:], None
    res = json.loads(m.group(1))
    for k in ("thai", "latin"):                             # ConvertTo-Json: one item -> a string
        v = res.get(k) or []
        res[k] = [v] if isinstance(v, str) else v
    pdf = work / "word-print.pdf"
    return res, "", (pdf if pdf.exists() else None)


def source_thai(docx):
    """Thai characters the reader should find on the pages: body once, headers/footers per page."""
    z = zipfile.ZipFile(docx)
    text = lambda n: "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", z.read(n).decode("utf-8")))
    body = text("word/document.xml")
    hf = [text(n) for n in z.namelist() if re.match(r"word/(header|footer)\d+\.xml$", n)]
    return body, hf


def thai_count(s):
    return collections.Counter(c for c in unicodedata.normalize("NFC", s) if THAI.match(c))


def libreoffice_pdf(docx, out_pdf):
    tmp = Path(tempfile.mkdtemp(prefix="ichita-lo-"))
    r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(docx)],
                       capture_output=True, text=True, timeout=300)
    made = tmp / (Path(docx).stem + ".pdf")
    if not made.exists():
        return "LibreOffice produced nothing: " + (r.stderr or r.stdout)[-300:]
    shutil.move(str(made), out_pdf)
    return ""


def wide_tables(docx):
    """Tables wider than the text block (grid + indent vs page width - margins), in twips.
    A too-wide table is why a layout "looks off" (seminar invitation, 2026-09-25: 9778 on 9638)."""
    x = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    pg, mar = re.search(r'<w:pgSz\b[^>]*w:w="(\d+)"', x), re.search(r"<w:pgMar\b[^>]*>", x)
    if not (pg and mar):
        return []
    lr = [re.search(r'w:%s="(-?\d+)"' % k, mar.group(0)) for k in ("left", "right")]
    text_w = int(pg.group(1)) - sum(int(m.group(1)) for m in lr if m)
    out = []
    for i, t in enumerate(re.findall(r"<w:tbl>.*?</w:tblGrid>", x, re.S), 1):
        grid = sum(int(w) for w in re.findall(r'<w:gridCol w:w="(\d+)"', t))
        ind = re.search(r'<w:tblInd w:w="(-?\d+)"', t)
        total = grid + (int(ind.group(1)) if ind else 0)
        if total > text_w + 15:
            out.append(f"table {i}: {total} twips (grid {grid}, indent {ind.group(1) if ind else 0}) on a {text_w} text width")
    return out


def pdf_fonts(pdf):
    out = subprocess.run(["pdffonts", str(pdf)], stdout=subprocess.PIPE, text=True,
                         stderr=subprocess.DEVNULL).stdout.splitlines()[2:]
    return [l.split()[0] for l in out if l.strip()]


def pdf_pages(pdf):
    m = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout)
    return int(m.group(1)) if m else None


def page_lines(page):
    """[(x0, y0, x1, y1, words)] for every text line on a pdftotext -bbox-layout page."""
    out = []
    for l in re.findall(r"<line\b.*?</line>", page, re.S):
        m = re.match(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', l)
        words = [unescape(w) for w in re.findall(r"<word[^>]*>(.*?)</word>", l, re.S)]
        if m and words:
            out.append((*map(float, m.groups()), words))
    return out


def next_lines(lines):
    """Line i -> the line that continues it: directly below (gap under 0.8 x its height) and
    overlapping it horizontally. pdftotext's own blocks cannot be used: each centred table
    line comes out as a block of its own."""
    nxt = {}
    for i, (x0, y0, x1, y1, _) in enumerate(lines):
        h, best = y1 - y0, None
        for j, (a0, b0, a1, b1, _) in enumerate(lines):
            gap, overlap = b0 - y1, min(x1, a1) - max(x0, a0)
            if j != i and -0.2 * h <= gap <= 0.8 * h and overlap > 0 and (best is None or gap < best[0]):
                best = (gap, j)
        if best:
            nxt[i] = best[1]
    return nxt


def source_paragraphs(docx):
    """Every paragraph of the .docx (body, headers, footers) as plain text."""
    z = zipfile.ZipFile(docx)
    out = []
    for n in z.namelist():
        if re.match(r"word/(document|header\d+|footer\d+)\.xml$", n):
            for p in re.findall(r"<w:p[ >].*?</w:p>", z.read(n).decode("utf-8"), re.S):
                p = p.replace("<w:noBreakHyphen/>", "<w:t>-</w:t>")
                out.append(unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p))))
    return out


def squash(s, thai):
    s = re.sub(r"\s+", "", unicodedata.normalize("NFC", s))
    return s if thai else THAI.sub("", s)


def line_flags(pdf, paragraphs, thai=True):
    """Suspicious line starts/ends and one-word last lines. Two lines are one paragraph only
    when their joined text is inside one source paragraph — geometry alone cannot tell a
    cell's second line from the next table row. thai=False for Word's printed PDF, whose
    Thai text layer is broken: Thai is ignored in the match and in the checks."""
    paras = [squash(p, thai) for p in paragraphs]
    x = subprocess.run(["pdftotext", "-bbox-layout", str(pdf), "-"], stdout=subprocess.PIPE, text=True,
                       stderr=subprocess.DEVNULL).stdout
    flags = []
    for pno, page in enumerate(re.findall(r"<page\b.*?</page>", x, re.S), 1):
        lines = page_lines(page)
        nxt = {i: j for i, j in next_lines(lines).items()
               if squash(" ".join(lines[i][4]), thai) and squash(" ".join(lines[j][4]), thai)
               and len(k := squash(" ".join(lines[i][4] + lines[j][4]), thai)) >= 5   # "1"+"1" is in "11"
               and any(k in p for p in paras)}
        prev = {j: i for i, j in nxt.items()}
        for i, (*_, words) in enumerate(lines):
            first, last, line = words[0], words[-1], " ".join(words)
            cont, has_next = i in prev, i in nxt
            if not thai and not squash(line, thai):
                continue                          # all-Thai line on Word's broken text layer
            why = []
            if cont and (first[0] in ")]}/—–-,.;:!?%" or (thai and first[0] in FOLLOW)):
                why.append(f"starts with {first[0]!r}")
            if has_next and ((thai and last[-1] in LEAD) or last[-1] in "([{/"):
                why.append(f"ends with {last[-1]!r}")
            if has_next and last.endswith("-") and not re.search(r"\d-$", last):
                why.append("hyphen break")
            if has_next and re.fullmatch(r"[<>≤≥≈~±]?[\d.,]+(?:[–-][\d.,]+)?[–-]?", last):
                why.append(f"number {last!r} at line end — split from its unit or range?")
            if has_next and line.count("(") > line.count(")") and len(lines[nxt[i]][4]) <= 2 \
                    and ")" in " ".join(lines[nxt[i]][4]):
                why.append("bracket split — its last words sit alone on the next line")
            if has_next and last in TITLES:
                why.append(f"title {last!r} split from its name")
            if cont and not has_next and len(words) == 1 and len(first) <= 12 and (thai or not THAI.search(line)) \
                    and not re.fullmatch(r"[\d.,/–-]+", first):
                why.append("one word alone on the last line")
            if why:
                flags.append((pno, line[:70], "; ".join(why)))
    return flags


def unescape(s):
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")


def pngs(pdf, outdir, prefix):
    """-> (image paths, error text or "")"""
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob(prefix + "-*.png"):
        old.unlink()
    r = subprocess.run(["pdftoppm", "-r", "110", "-png", str(pdf), str(outdir / prefix)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err = "" if r.returncode == 0 else f"pdftoppm exit {r.returncode}: " + \
        " ".join(l for l in r.stderr.splitlines() if "Syntax Warning" not in l)[-300:]
    return sorted(outdir.glob(prefix + "-*.png")), err


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--pdf", help="write the delivery PDF here (LibreOffice headless)")
    ap.add_argument("--png", help="page images of both layouts go here (default: a temp dir)")
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--require-word", action="store_true", help="FAIL if Word cannot be reached")
    ap.add_argument("--pages", type=int, help="FAIL unless Word lays the document out on exactly this many pages")
    a = ap.parse_args()
    docx = Path(a.docx).resolve()
    if a.pdf:
        a.pdf = str(Path(a.pdf).resolve())
    imgdir = Path(a.png).resolve() if a.png else Path(tempfile.mkdtemp(prefix="ichita-qc-png-"))
    fails, warns = [], []

    print(f"== {docx.name}")
    settings = zipfile.ZipFile(docx).read("word/settings.xml").decode("utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fix_thai_docx import compat_mode
    mode = compat_mode(settings)
    if mode is None or mode < 14:
        (fails if mode is None else warns).append(
            f"compatibilityMode {mode if mode is not None else 'missing'} — Word will not break Thai lines "
            "between words (missing: measured 2026-09-25). Run fix_thai_docx.py")
    for w in wide_tables(docx):
        warns.append("wider than the text block — " + w)
    res, why, word_pdf = word_check(docx, True, a.timeout)
    if res is None:
        (fails if a.require_word else warns).append("Word not checked: " + why +
                                                     ". LibreOffice is only a proxy for Word — say so.")
    else:
        print(f"Word: {res['pages']} pages · Thai spelling flags {len(res['thai'])} · Latin {len(res['latin'])}")
        if a.pages and res["pages"] != a.pages:
            fails.append(f"Word lays it out on {res['pages']} pages, not {a.pages}")
        for k in ("thai", "latin"):
            if res[k]:
                c = collections.Counter(res[k])
                warns.append(f"Word flags ({k}): " + ", ".join(f"{w} ×{n}" for w, n in c.most_common()))

    if a.pdf:
        err = libreoffice_pdf(docx, a.pdf)
        if err:
            fails.append(err)
        else:
            bad = [f for f in pdf_fonts(a.pdf) if not BRAND.match(f)]
            if bad:
                fails.append("non-brand font in the PDF: " + ", ".join(sorted(set(bad))))
            body, hf = source_thai(docx)
            n = pdf_pages(a.pdf)
            want = thai_count(body)      # body only: which header prints on which page varies (titlePg)
            got = thai_count(subprocess.run(["pdftotext", a.pdf, "-"], stdout=subprocess.PIPE, text=True,
                                            stderr=subprocess.DEVNULL).stdout)
            lost = {c: want[c] - got[c] for c in want if got[c] < want[c]}
            if lost:
                fails.append("Thai missing from the PDF text layer: " +
                             ", ".join(f"U+{ord(c):04X} {c} −{k}" for c, k in lost.items()))
            print(f"PDF: {a.pdf} · {n} pages · fonts {', '.join(sorted(set(pdf_fonts(a.pdf))))}")
            if res and n != res["pages"]:
                warns.append(f"page count differs: Word {res['pages']}, PDF {n} — LibreOffice re-lays out")

    for name, pdf in (("Word", word_pdf), ("PDF", a.pdf)):
        if not pdf:
            continue
        for pno, line, why in line_flags(pdf, source_paragraphs(docx), thai=(name == "PDF")):
            warns.append(f"line ({name} p{pno}): {why}: {line}")
        imgs, err = pngs(Path(pdf), imgdir, name.lower())
        if err:
            fails.append(f"{name} page images not made — {err}")
        print(f"{name} page images: " + " ".join(str(p) for p in imgs))

    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print("Thai split mid-word is not detected here. Read every page image, every line, before saying done.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
