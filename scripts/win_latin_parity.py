#!/usr/bin/env python3
"""Assert a merged TH family renders its Latin exactly like the Latin it merged.

This is the test whose absence let a 16% ink deficit ship. Every existing check
in this repo compares OUTLINES, and the outlines were never wrong: TH-Aeonik's
Latin is dimensionally identical to Aeonik's — same bbox, same advance, all
seven weights. What differed was the RASTERISER, because the 2026-08-02 format
flip moved the family from CFF to `glyf` and Windows renders the two through
different engines. Measured 2026-08-04 at 11 pt in DirectWrite:

    Aeonik      .otf/CFF    stems 2,1 px   ink 11,056   advance 9.857
    TH Aeonik   .ttf/glyf   stems 1,1 px   ink  9,310   advance 9.857   -15.8%
    Slussen     .otf/CFF    stems 2,2 px   ink 12,485   advance 11.293
    TH Slussen  .ttf/glyf   stems 2,2 px   ink  9,940   advance 11.293  -20.4%

Siwatch reported it as "TH Aeonik is slightly thinner than Aeonik, especially
Regular", and Regular shows it most because the gap is largest at text sizes.

Nothing on Linux can see this. FreeType's engines do not reproduce Windows'
per-format behaviour, so a green HarfBuzz/FreeType suite says nothing here — the
same structural blindness that cost this project four sessions. `powershell.exe`
is on PATH from WSL, so the shipping renderer is directly measurable, and this
module measures it.

The PowerShell is generated and passed as `-EncodedCommand` (base64 UTF-16LE)
rather than written to a `.ps1`. That is deliberate: PowerShell 5.1 mis-parses a
`.ps1` without a UTF-8 BOM, and an encoded command has no file and therefore no
encoding to get wrong.

WHAT IS ASSERTED, and why each one is separate:

    advance      metric identity. Already true; this keeps it true.
    capH/bboxW   glyph SIZE in pixels. Separates "smaller" from "thinner" —
                 total ink alone conflates them, and the first probe run did.
    stems        stem width in whole pixels. This is what a reader sees as
                 weight; it is the metric that caught the defect.
    ink          total darkness. Catches antialiasing/gamma differences that
                 leave the stem pixel count intact — TH-Slussen matched Slussen
                 on stems and was still 20.4% lighter.
    lineSpacing  what the GRAPHICS API reports as the line box: GDI+ returns
                 hhea ascent+descent+lineGap, WPF returns hhea ascent+descent.
                 NEITHER is what Word leads off, so this column is reference
                 only and nothing is asserted against it. It is printed because
                 a disagreement between it and wordBox is the tell that the
                 font's metric fields do not agree with each other.
    wordBox      the box Word actually leads off, derived from the resolved file
                 by word_line_box() below. THIS is the line-spacing assertion.
                 Measured 2026-08-05 across 15 installed families, and it is not
                 one field: see word_line_box() for the branch and the evidence.

Also reported: the font FILE Windows resolved. The installed fonts are a third
artifact layer and go stale silently — on 2026-08-04 the current
TH-Aeonik-Regular build was sitting in `TH-Aeonik-Regular_0.ttf` because Windows
renamed it on a locked-file collision, leaving a stale file registered under the
family name. A parity result measured against the wrong file is worthless, so
the resolved path is part of the output rather than an afterthought.

Usage:
    python3 scripts/win_latin_parity.py                 # both families
    python3 scripts/win_latin_parity.py --pair Aeonik "TH Aeonik"
    python3 scripts/win_latin_parity.py --sizes 11      # single size
    python3 scripts/win_latin_parity.py --json
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

# Latin only. Thai never appears in this file — the probe compares the LATIN
# half of a merged font against its source, and the Thai half has no counterpart
# to compare against. (Were Thai ever needed here it would have to be built from
# codepoints, never written literally: see the module docstring on encoding.)
INK_TEXT = "Hamburgefonstiv 123"

# 'H' carries two flat vertical stems and a flat cap, so its rendered bbox gives
# cap height and its mid-band gives stem width without curves or diagonals
# contaminating either.
PROBE_GLYPH = "H"

DEFAULT_PAIRS = [("Aeonik", "TH Aeonik"), ("Slussen", "TH Slussen")]
DEFAULT_SIZES = [11, 14, 22]

# Ink is a sum over an antialiased bitmap, so it carries a little renderer noise
# even between two runs of the same font. 3% is well inside the 15.8%-20.4%
# defect this exists to catch, and comfortably outside the noise.
INK_TOL_PCT = 3.0

# The stem row is sampled this far down from the top of the H — clear of the
# crossbar, which would otherwise read as one solid run across the whole glyph.
STEM_ROW_FRAC = 0.20

# Line box as a ratio of the Latin source's, per family, pinned as a NUMBER.
#
# The ratio is taken over word_line_box(), NOT over the lineSpacing the graphics
# APIs report. The previous version of this constant compared WPF's number for
# one family against GDI+'s for the same family across two engine rows, which are
# different quantities (WPF omits hhea lineGap, GDI+ includes it). Slussen has a
# 166-unit lineGap, so the identical font scored 1.207x in dwrite and 1.075x in
# gdi and one of the two was always red for reasons that had nothing to do with
# the font.
#
# These two families deliberately differ, so a single "must equal the Latin"
# assertion would be permanently red for one of them — and a check that is always
# red is a check nobody reads.
#
#   TH Aeonik  1.281 — Siwatch 2026-08-05: TH AEONIK IS NO LONGER A DROP-IN
#              AEONIK REPLACEMENT. The font is chosen by the document's language
#              — English-only documents use Aeonik itself, mixed Thai/English use
#              TH Aeonik — so the box is 1537, sized to what the Thai measured
#              out at, and 1537/1200 = 1.281.
#              This reverses the 1.000 pinned on 2026-08-04, and it is not a
#              regression of it: the 08-04 requirement existed only so Latin-only
#              text inside a TH-Aeonik document would lead like Aeonik. Once
#              English-only documents use actual Aeonik that requirement is gone,
#              and with it the 262-unit Thai overlap it forced.
#              ACCEPTED CONSEQUENCE: English-only paragraphs inside a MIXED
#              document also lead +28% wider. One font has one hhea.
#              MEASURE in Word after install: 1537/em = 16.91 pt at 11 pt Single.
#   TH Slussen 1.004 — 1602 against Slussen's own usWin 1596. Slussen gets the
#              same RULE as Aeonik, not the same number: box = the Thai's
#              measured need + margin, with hhea/sTypo/usWin unified. Slussen's
#              Thai is taller, so 1602 where Aeonik lands at 1537 — and because
#              Slussen's own Latin box is already generous, the same rule leaves
#              it within 0.4% of its source rather than 28% over.
#              Replaces the 1.241 pinned on 2026-08-05, which was a PREDICTION of
#              what the then-built faces would do (usWin 1980 against 1596) and
#              was labelled as such. That usWin/box disagreement is exactly what
#              this phase fixed: 1980 against a 1625 box would have had Word lead
#              TH Slussen at +21.7% for reasons that had nothing to do with the
#              outlines.
#
# Pinning the ratio rather than only the relationship is deliberate: "the line box
# equals the Latin source's" read as a principle in this repo for two days while
# encoding a defect, and four separate checks asserted it. The relationship half
# lives where it can be measured against the Thai — build_th_aeonik.
# assert_thai_clears() and its Slussen twin, per face, on the built file.
EXPECTED_LINE_RATIO = {
    "TH Aeonik": 1.281,
    "TH Slussen": 1.004,
}

# The box is an integer count of font units, so a ratio can only land within
# rounding of the documented value.
LINE_RATIO_TOL = 0.002


def word_line_box(wsl_path):
    """Return the line box Word leads off, in units per 1000 em, or None.

    "Word leads off usWinAscent+usWinDescent" is what this repo believed on
    2026-08-04 and it is not true in general. Word's line pitch was measured on
    2026-08-05 for 15 installed families (six paragraphs at 11 pt, Single, baseline
    travel / 5, via Word COM) and compared against each file's three metric sets.
    Three branches fit all 15; no single field fits any 10 of them:

        format  bit 7   field Word uses          evidence
        CFF     set     usWin                    Slussen 1595 (usWin 1596, hhea 1512)
                                                 TH Aeonik pre-fix 1.504x = 1800/1200
        glyf    set     sTypo (== hhea here)     Bai Jamjuree 1250 (usWin 1786!)
                                                 Sarabun 1300 (usWin 1853), Noto 1364,
                                                 Gabriola 1700, Sitka 1250, Ubuntu 1123,
                                                 TH Slussen 1627
        glyf    clear   max(hhea, usWin)         Arial 1150 (hhea 1150 > usWin 1117),
                                                 Times 1150, Ebrima 1359, Segoe Print
                                                 1764, DilleniaUPC 1305 (hhea only 600!),
                                                 Ink Free 1236 (usWin 1238 > hhea 1200)

    Two consequences worth keeping in mind before editing any vertical metric:

      * The 2026-08-04 TH-Aeonik fix is correct for the format it ships. It ships
        CFF, so usWin genuinely is its spacing control. The fix was also made
        robust by accident rather than by design — it set hhea, sTypo and usWin
        all to 1200, so it lands on 1200 in every branch above.
      * A format flip silently relocates the spacing control. TH Slussen is glyf
        today and Word ignores its usWin 1980; rebuild it as CFF and that 1980
        becomes the line box. Nothing about the outlines changes.

    bit 7 is OS/2.fsSelection USE_TYPO_METRICS. In every glyf font measured here
    sTypo and hhea agreed, so which of the two the set-bit branch reads is NOT
    established — only that usWin is not it. Slussen is the single measured font
    where a CFF face has usWin != hhea, so the CFF branch rests on it plus the
    pre-fix TH-Aeonik observation.
    """
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    try:
        font = TTFont(wsl_path, fontNumber=0, lazy=True)
    except Exception:
        return None
    try:
        os2, hhea, head = font["OS/2"], font["hhea"], font["head"]
        per_em = 1000.0 / head.unitsPerEm
        hhea_box = (hhea.ascent - hhea.descent + hhea.lineGap) * per_em
        typo_box = (os2.sTypoAscender - os2.sTypoDescender
                    + os2.sTypoLineGap) * per_em
        win_box = (os2.usWinAscent + os2.usWinDescent) * per_em
        is_cff = "CFF " in font or "CFF2" in font
        use_typo = bool(os2.fsSelection & (1 << 7))
        if is_cff:
            box, field = win_box, "usWin"
        elif use_typo:
            box, field = typo_box, "sTypo"
        else:
            box, field = max(hhea_box, win_box), (
                "hhea" if hhea_box >= win_box else "usWin")
        return {"box": box, "field": field,
                "format": "CFF" if is_cff else "glyf",
                "useTypo": use_typo, "hhea": hhea_box,
                "sTypo": typo_box, "usWin": win_box}
    except KeyError:
        return None
    finally:
        font.close()


def _wsl_path(win_path):
    """Convert a Windows path as reported by the probe to a WSL path, or None."""
    if not win_path:
        return None
    out = subprocess.run(["wslpath", "-u", win_path],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None

# GDI and DirectWrite are measured in SEPARATE PowerShell processes, and that is
# not tidiness — it is a correctness requirement found the hard way.
#
# Loading WPF (PresentationCore) flips the process to DPI-aware the moment the
# first WPF object is constructed. This machine runs at 150% display scaling, so
# from that point on GDI+ reports DpiX 144 instead of 96 and every Point-sized
# font renders 1.5x larger. In a single-process run the first GDI measurement was
# correct and every subsequent one was inflated by exactly 144/96 — which read as
# "TH Aeonik is 50% bigger than Aeonik", a defect that does not exist.
#
# Belt and braces on top of the isolation: GDI is sized in PIXELS with PageUnit
# set to Pixel, so the conversion never consults the process DPI at all.
_PS = r'''
$ErrorActionPreference = 'Stop'
$engine = __ENGINE__
if ($engine -eq 'gdi') {
  Add-Type -AssemblyName System.Drawing
} else {
  Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase
}

$fonts    = __FONTS__
$dirs     = __DIRS__
$sizes    = __SIZES__
$inkText  = __INKTEXT__
$probe    = __PROBE__
$stemFrac = __STEMFRAC__

# A font may be measured straight off disk instead of from the installed set.
# That matters twice over: a freshly built face can be verified before anyone
# installs it, and it sidesteps the installed-font layer entirely — which has
# gone stale silently more than once (on 2026-08-04 the current
# TH-Aeonik-Regular build was sitting in TH-Aeonik-Regular_0.ttf because Windows
# renamed it on a locked-file collision, leaving a stale file registered).
function Resolve-Typeface($name) {
  if ($dirs.ContainsKey($name)) {
    $ff = New-Object System.Windows.Media.FontFamily(
            (New-Object System.Uri($dirs[$name])), "./#$name")
    return New-Object System.Windows.Media.Typeface(
             $ff, [System.Windows.FontStyles]::Normal,
             [System.Windows.FontWeights]::Normal,
             [System.Windows.FontStretches]::Normal)
  }
  return New-Object System.Windows.Media.Typeface($name)
}

# --- shared bitmap analysis -------------------------------------------------
# Returns capH / bboxW / stem runs for the probe glyph. `lum` is a closure the
# caller supplies so GDI (Bitmap.GetPixel) and WPF (raw Pbgra32 buffer) can share
# one implementation instead of drifting apart.
function Measure-Glyph($w, $h, $lum) {
  $minX = 999999; $maxX = -1; $minY = 999999; $maxY = -1
  for ($y = 0; $y -lt $h; $y++) {
    for ($x = 0; $x -lt $w; $x++) {
      if ((& $lum $x $y) -lt 128) {
        if ($x -lt $minX) { $minX = $x }; if ($x -gt $maxX) { $maxX = $x }
        if ($y -lt $minY) { $minY = $y }; if ($y -gt $maxY) { $maxY = $y }
      }
    }
  }
  if ($maxY -lt 0) { return @{ capH = 0; bboxW = 0; stems = 'none' } }
  $row = [int]($minY + ($maxY - $minY) * $stemFrac)
  $runs = @(); $n = 0
  for ($x = 0; $x -lt $w; $x++) {
    if ((& $lum $x $row) -lt 128) { $n++ }
    elseif ($n -gt 0) { $runs += $n; $n = 0 }
  }
  if ($n -gt 0) { $runs += $n }
  $s = if ($runs.Count -gt 0) { [string]::Join(',', $runs) } else { 'none' }
  return @{ capH = ($maxY - $minY + 1); bboxW = ($maxX - $minX + 1); stems = $s }
}

function Sum-Ink($w, $h, $lum) {
  $ink = 0.0
  for ($y = 0; $y -lt $h; $y++) {
    for ($x = 0; $x -lt $w; $x++) { $ink += (255 - (& $lum $x $y)) }
  }
  return $ink
}

# --- GDI / Uniscribe --------------------------------------------------------
function Probe-Gdi($name, $sizePt) {
  # PrivateFontCollection cannot load CFF/.otf on .NET Framework, so an
  # off-disk measurement is DirectWrite-only. That is not a real gap: DirectWrite
  # is the renderer Word 2016+ and PowerPoint actually use.
  if ($dirs.ContainsKey($name)) { throw "gdi cannot load $name off disk (.otf)" }
  $ff  = New-Object System.Drawing.FontFamily($name)
  $em  = $ff.GetEmHeight([System.Drawing.FontStyle]::Regular)
  $lsp = $ff.GetLineSpacing([System.Drawing.FontStyle]::Regular)
  # Pixel units, not Point: see the note above _PS on DPI awareness.
  $emPx = $sizePt * 96.0 / 72.0
  $f   = New-Object System.Drawing.Font(
           $name, $emPx, [System.Drawing.FontStyle]::Regular,
           [System.Drawing.GraphicsUnit]::Pixel)

  # A silent substitution makes every number below meaningless, so the resolved
  # family is reported and compared rather than assumed.
  $resolved = $f.Name

  $gw = 40 + [int]($sizePt * 4); $gh = 40 + [int]($sizePt * 4)
  $bmp = New-Object System.Drawing.Bitmap $gw, $gh
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.PageUnit = [System.Drawing.GraphicsUnit]::Pixel
  $g.Clear([System.Drawing.Color]::White)
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
  $g.DrawString($probe, $f, [System.Drawing.Brushes]::Black, 6, 6)
  $g.Dispose()
  $lum = { param($x, $y) $c = $bmp.GetPixel($x, $y)
           0.299 * $c.R + 0.587 * $c.G + 0.114 * $c.B }
  $m = Measure-Glyph $gw $gh $lum
  $bmp.Dispose()

  $iw = 60 + [int]($sizePt * 22); $ih = 20 + [int]($sizePt * 3)
  $bmp2 = New-Object System.Drawing.Bitmap $iw, $ih
  $g2 = [System.Drawing.Graphics]::FromImage($bmp2)
  $g2.PageUnit = [System.Drawing.GraphicsUnit]::Pixel
  $g2.Clear([System.Drawing.Color]::White)
  $g2.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
  $g2.DrawString($inkText, $f, [System.Drawing.Brushes]::Black, 4, 4)
  $g2.Dispose()
  $lum2 = { param($x, $y) $c = $bmp2.GetPixel($x, $y)
            0.299 * $c.R + 0.587 * $c.G + 0.114 * $c.B }
  $ink = Sum-Ink $iw $ih $lum2
  $bmp2.Dispose(); $f.Dispose()

  # em is reported so a units-per-em difference can never masquerade as a
  # thickness difference: every ratio here assumes both fonts are 1000 upem.
  return @{ capH = $m.capH; bboxW = $m.bboxW; stems = $m.stems; ink = $ink
            advance = -1; lineSpacing = ($lsp * 1000.0 / $em); resolved = $resolved
            file = '' }
}

# --- DirectWrite ------------------------------------------------------------
function Probe-Dwrite($name, $sizePt) {
  $tf = Resolve-Typeface $name
  $gt = $null
  $file = if ($tf.TryGetGlyphTypeface([ref]$gt)) { $gt.FontUri.LocalPath } else { 'UNRESOLVED' }
  $lineSpacing = if ($gt) { $gt.Height * 1000.0 } else { -1 }

  $px = $sizePt * 96.0 / 72.0
  # The 6-argument FormattedText overload only. The overload that takes
  # pixelsPerDip throws on .NET Framework, which cost a debugging cycle once.
  $ftInk = New-Object System.Windows.Media.FormattedText(
    $inkText, [System.Globalization.CultureInfo]::InvariantCulture,
    [System.Windows.FlowDirection]::LeftToRight, $tf, $px,
    [System.Windows.Media.Brushes]::Black)
  $advance = $ftInk.WidthIncludingTrailingWhitespace

  function Render($ft, $w, $h) {
    $dv = New-Object System.Windows.Media.DrawingVisual
    $dc = $dv.RenderOpen()
    $dc.DrawRectangle([System.Windows.Media.Brushes]::White, $null,
                      (New-Object System.Windows.Rect(0, 0, $w, $h)))
    $dc.DrawText($ft, (New-Object System.Windows.Point(6, 6)))
    $dc.Close()
    $rtb = New-Object System.Windows.Media.Imaging.RenderTargetBitmap(
             $w, $h, 96, 96, [System.Windows.Media.PixelFormats]::Pbgra32)
    $rtb.Render($dv)
    $stride = $w * 4
    $buf = New-Object byte[] ($stride * $h)
    $rtb.CopyPixels([System.Windows.Int32Rect]::Empty, $buf, $stride, 0)
    return @{ buf = $buf; stride = $stride }
  }

  $gw = 40 + [int]($sizePt * 4); $gh = 40 + [int]($sizePt * 4)
  $ftG = New-Object System.Windows.Media.FormattedText(
    $probe, [System.Globalization.CultureInfo]::InvariantCulture,
    [System.Windows.FlowDirection]::LeftToRight, $tf, $px,
    [System.Windows.Media.Brushes]::Black)
  $r = Render $ftG $gw $gh
  $lum = { param($x, $y) $i = $y * $r.stride + $x * 4
           0.299 * $r.buf[$i + 2] + 0.587 * $r.buf[$i + 1] + 0.114 * $r.buf[$i] }
  $m = Measure-Glyph $gw $gh $lum

  $iw = 60 + [int]($sizePt * 22); $ih = 20 + [int]($sizePt * 3)
  $r2 = Render $ftInk $iw $ih
  $lum2 = { param($x, $y) $i = $y * $r2.stride + $x * 4
            0.299 * $r2.buf[$i + 2] + 0.587 * $r2.buf[$i + 1] + 0.114 * $r2.buf[$i] }
  $ink = Sum-Ink $iw $ih $lum2

  return @{ capH = $m.capH; bboxW = $m.bboxW; stems = $m.stems; ink = $ink
            advance = $advance; lineSpacing = $lineSpacing; resolved = $name
            file = $file }
}

foreach ($name in $fonts) {
  foreach ($sz in $sizes) {
    try {
      $p = if ($engine -eq 'gdi') { Probe-Gdi $name $sz } else { Probe-Dwrite $name $sz }
      'ROW' + "`t" + $engine + "`t" + $name + "`t" + $sz + "`t" + $p.capH + "`t" +
        $p.bboxW + "`t" + $p.stems + "`t" + $p.ink + "`t" + $p.advance + "`t" +
        $p.lineSpacing + "`t" + $p.resolved + "`t" + $p.file
    } catch {
      'ERR' + "`t" + $engine + "`t" + $name + "`t" + $sz + "`t" + $_.Exception.Message
    }
  }
}
'''

ENGINES = ("gdi", "dwrite")


def _ps_literal(value) -> str:
    """Render a Python value as a PowerShell literal."""
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "@(" + ", ".join(_ps_literal(v) for v in value) + ")"
    raise TypeError(f"cannot render {value!r} as PowerShell")


def _ps_hashtable(mapping):
    if not mapping:
        return "@{}"
    body = "; ".join(f"{_ps_literal(k)} = {_ps_literal(v)}"
                     for k, v in mapping.items())
    return "@{" + body + "}"


def _probe_engine(engine, fonts, sizes, ink_text, probe_glyph, dirs=None):
    """Run one engine in its own PowerShell process. See the note above _PS."""
    script = (_PS
              .replace("__DIRS__", _ps_hashtable(dirs or {}))
              .replace("__ENGINE__", _ps_literal(engine))
              .replace("__FONTS__", _ps_literal(list(fonts)))
              .replace("__SIZES__", _ps_literal(list(sizes)))
              .replace("__INKTEXT__", _ps_literal(ink_text))
              .replace("__PROBE__", _ps_literal(probe_glyph))
              .replace("__STEMFRAC__", _ps_literal(STEM_ROW_FRAC)))
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand", encoded],
            capture_output=True, text=True, timeout=900)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "powershell.exe not found on PATH — this probe measures the Windows "
            "renderer and cannot be satisfied from Linux") from exc

    rows, errors = [], []
    for line in out.stdout.splitlines():
        parts = line.rstrip("\r").split("\t")
        if parts[0] == "ROW" and len(parts) >= 12:
            rows.append({
                "engine": parts[1], "font": parts[2], "size": int(parts[3]),
                "capH": int(parts[4]), "bboxW": int(parts[5]),
                "stems": parts[6], "ink": float(parts[7]),
                "advance": float(parts[8]), "lineSpacing": float(parts[9]),
                "resolved": parts[10], "file": parts[11],
            })
        elif parts[0] == "ERR":
            errors.append("\t".join(parts[1:]))
    if not rows:
        raise RuntimeError(
            f"engine {engine!r} returned no measurements. stderr:\n"
            + (out.stderr or "(empty)") + "\nstdout:\n" + (out.stdout or "(empty)"))
    return rows, errors


def probe(fonts, sizes, ink_text=INK_TEXT, probe_glyph=PROBE_GLYPH,
          engines=ENGINES, dirs=None):
    """Measure `fonts` at `sizes` on Windows. Returns (rows, errors).

    Raises RuntimeError if powershell.exe is unreachable or an engine returns
    nothing, rather than reporting a pass on zero measurements.
    """
    rows, errors = [], []
    for engine in engines:
        r, e = _probe_engine(engine, fonts, sizes, ink_text, probe_glyph, dirs)
        rows.extend(r)
        errors.extend(e)
    return rows, errors


def compare(rows, pairs, ink_tol_pct=INK_TOL_PCT, word_boxes=None):
    """Check every TH face against its Latin source. Returns a list of failures."""
    index = {(r["engine"], r["font"], r["size"]): r for r in rows}
    word_boxes = word_boxes or {}
    fails = []
    for latin, merged in pairs:
        for (engine, name, size), row in sorted(index.items()):
            if name != merged:
                continue
            src = index.get((engine, latin, size))
            if src is None:
                fails.append(f"{engine} {size}pt: no {latin} measurement to compare against")
                continue

            where = f"{engine} {merged} {size}pt"
            if row["resolved"] != merged:
                fails.append(f"{where}: resolved to {row['resolved']!r}, not {merged!r} "
                             f"— the font is not installed and a fallback was measured")
                continue
            if row["advance"] >= 0 and src["advance"] >= 0 and \
                    abs(row["advance"] - src["advance"]) > 1e-6:
                fails.append(f"{where}: advance {row['advance']:.3f} vs "
                             f"{latin} {src['advance']:.3f} — metrics differ")
            # capH and bboxW are INK extents, so they shrink when the rasteriser
            # lays down less ink — a 1px delta here is the same defect the stem
            # check reports, not a size difference. Advance above is the size
            # check; it is exact and unaffected by edge rounding.
            for key in ("capH", "bboxW"):
                if row[key] != src[key]:
                    fails.append(f"{where}: {key} {row[key]}px vs {latin} "
                                 f"{src[key]}px — ink extent differs")
            if row["stems"] != src["stems"]:
                fails.append(f"{where}: stems [{row['stems']}] vs {latin} "
                             f"[{src['stems']}] px — this is the thickness defect")
            if src["ink"] > 0:
                delta = (row["ink"] / src["ink"] - 1) * 100
                if abs(delta) > ink_tol_pct:
                    fails.append(f"{where}: ink {delta:+.1f}% vs {latin} "
                                 f"(tolerance +/-{ink_tol_pct:.0f}%)")
        # Line box ONCE per pair, off the file rather than per engine row: the
        # box is a property of the font, and the two engines report two different
        # quantities for it (see the note on EXPECTED_LINE_RATIO). Compared
        # against this family's DOCUMENTED ratio, not against 1.0 — an
        # undocumented family defaults to 1.0, because a new merged face is meant
        # to match its Latin unless someone writes down why it does not.
        box, src_box = word_boxes.get(merged), word_boxes.get(latin)
        if box is None or src_box is None:
            fails.append(f"{merged}: no file to read the line box from — the "
                         f"probe reports a resolved path only for dwrite rows, "
                         f"so this needs the dwrite engine to have run")
        elif src_box["box"]:
            want = EXPECTED_LINE_RATIO.get(merged, 1.0)
            got = box["box"] / src_box["box"]
            if abs(got - want) > LINE_RATIO_TOL:
                fails.append(
                    f"{merged}: line box {box['box']:.0f} ({box['format']}, so "
                    f"Word leads off {box['field']}) vs {latin} "
                    f"{src_box['box']:.0f} ({src_box['format']}/"
                    f"{src_box['field']}) = {got:.3f}x, but the documented ratio "
                    f"is {want:.3f}x. Check the FORMAT first: a CFF face is led "
                    f"off usWin and a glyf face with USE_TYPO_METRICS ignores "
                    f"usWin entirely, so a format flip moves the box without "
                    f"touching a single metric. Otherwise the box drifted or the "
                    f"trade changed — if the trade, update EXPECTED_LINE_RATIO "
                    f"and say why.")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pair", nargs=2, action="append", metavar=("LATIN", "MERGED"),
                    help="a Latin source and the merged family that must match it "
                         "(repeatable; defaults to both ICHITA families)")
    ap.add_argument("--sizes", nargs="+", type=int, default=DEFAULT_SIZES,
                    help="point sizes to measure (default: 11 14 22)")
    ap.add_argument("--ink-tol", type=float, default=INK_TOL_PCT,
                    help="permitted ink deviation, percent (default: 3)")
    ap.add_argument("--from-dir", nargs=2, action="append",
                    metavar=("FAMILY", "DIR"),
                    help="measure FAMILY off disk from DIR instead of from the "
                         "installed fonts (repeatable). Verifies a freshly built "
                         "face without installing it, and bypasses the installed "
                         "layer, which goes stale silently. DirectWrite only — "
                         "GDI+ cannot load CFF off disk.")
    ap.add_argument("--json", action="store_true", help="dump raw measurements")
    args = ap.parse_args()

    dirs = {}
    for family, directory in (args.from_dir or []):
        win = subprocess.run(["wslpath", "-w", directory],
                             capture_output=True, text=True)
        path = win.stdout.strip() if win.returncode == 0 else directory
        dirs[family] = path if path.endswith("\\") else path + "\\"

    pairs = [tuple(p) for p in args.pair] if args.pair else DEFAULT_PAIRS
    fonts = []
    for latin, merged in pairs:
        for name in (latin, merged):
            if name not in fonts:
                fonts.append(name)

    engines = ("dwrite",) if dirs else ENGINES
    rows, errors = probe(fonts, args.sizes, engines=engines, dirs=dirs)
    if args.json:
        print(json.dumps(rows, indent=2))

    print(f"{'engine':7s} {'font':14s} {'pt':>3s} {'capH':>5s} {'bboxW':>6s} "
          f"{'stems':>8s} {'ink':>10s} {'advance':>8s} {'apiBox':>8s}  file")
    for r in sorted(rows, key=lambda r: (r["engine"], r["size"], r["font"])):
        adv = f"{r['advance']:8.3f}" if r["advance"] >= 0 else f"{'-':>8s}"
        print(f"{r['engine']:7s} {r['font']:14s} {r['size']:3d} {r['capH']:5d} "
              f"{r['bboxW']:6d} {r['stems']:>8s} {r['ink']:10,.0f} {adv} "
              f"{r['lineSpacing']:8.0f}  {r['file'] or '-'}")

    # apiBox above is what GDI+/WPF report and is NOT Word's line pitch. The box
    # Word leads off is read from the file, so it needs the path the probe
    # resolved — which only the dwrite rows carry.
    word_boxes = {}
    for r in rows:
        if r["font"] in word_boxes or not r["file"]:
            continue
        path = _wsl_path(r["file"])
        if path:
            box = word_line_box(path)
            if box:
                word_boxes[r["font"]] = box
    if word_boxes:
        print(f"\n{'font':14s} {'wordBox':>8s} {'field':>7s} {'fmt':>5s} "
              f"{'useTypo':>8s} {'hhea':>7s} {'sTypo':>7s} {'usWin':>7s}")
        for name in sorted(word_boxes):
            b = word_boxes[name]
            print(f"{name:14s} {b['box']:8.0f} {b['field']:>7s} {b['format']:>5s} "
                  f"{str(b['useTypo']):>8s} {b['hhea']:7.0f} {b['sTypo']:7.0f} "
                  f"{b['usWin']:7.0f}")

    for e in errors:
        print(f"ERROR  {e}")

    fails = compare(rows, pairs, args.ink_tol, word_boxes)
    print()
    if fails or errors:
        for f in fails:
            print(f"FAIL  {f}")
        print(f"\n{len(fails)} parity failure(s), {len(errors)} probe error(s)")
        return 1
    # The engine count is reported, not assumed. `--from-dir` silently drops to
    # DirectWrite alone, because GDI+ cannot load CFF off disk — so a hardcoded
    # "2 engines" would have claimed twice the coverage the run actually had.
    print(f"OK  Latin renders identically to its source across "
          f"{len(pairs)} famil{'y' if len(pairs) == 1 else 'ies'} "
          f"x {len(args.sizes)} size(s) x {len(engines)} engine(s) "
          f"({', '.join(engines)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
