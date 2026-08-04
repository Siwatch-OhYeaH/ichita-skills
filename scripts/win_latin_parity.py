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
    lineSpacing  the font's own line box on the real renderer. This is the
                 assertion for the second half of the 2026-08-04 work (box
                 1540 -> Aeonik's 1200); Word and PowerPoint both lead off it.

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
# These two families deliberately differ, so a single "must equal the Latin"
# assertion would be permanently red for one of them — and a check that is always
# red is a check nobody reads.
#
#   TH Aeonik  1.000 — Siwatch 2026-08-04: it must be a drop-in Aeonik
#              replacement, so the box is Aeonik's 1200 to the unit. The Thai
#              knowingly does not fit (worst stacks overlap by 262 units); the
#              Latin/Complex-Script split that satisfies both was ruled out and
#              shrinking the marks was measured and cannot close the gap.
#   TH Slussen 1.207 — still carries the 2026-08-03 trade: box 1625 against
#              Slussen's 1346, so two Thai lines clear. NOT changed on 2026-08-04
#              because only TH Aeonik was in scope. Whether Slussen should follow
#              Aeonik is an open decision, not an oversight.
#
# Pinning the ratio rather than the relationship is deliberate: "the line box
# equals the Latin source's" read as a principle in this repo for two days while
# encoding a defect, and four separate checks asserted it.
EXPECTED_LINE_RATIO = {
    "TH Aeonik": 1.000,
    "TH Slussen": 1.207,
}

# The box is an integer count of font units, so a ratio can only land within
# rounding of the documented value.
LINE_RATIO_TOL = 0.002

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


def compare(rows, pairs, ink_tol_pct=INK_TOL_PCT):
    """Check every TH face against its Latin source. Returns a list of failures."""
    index = {(r["engine"], r["font"], r["size"]): r for r in rows}
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
            # Line box against this family's DOCUMENTED ratio, not against 1.0.
            # An undocumented family defaults to 1.0 — a new merged face is meant
            # to match its Latin unless someone writes down why it does not.
            want = EXPECTED_LINE_RATIO.get(merged, 1.0)
            got = row["lineSpacing"] / src["lineSpacing"] if src["lineSpacing"] else 0
            if abs(got - want) > LINE_RATIO_TOL:
                fails.append(
                    f"{where}: line box {row['lineSpacing']:.0f} vs {latin} "
                    f"{src['lineSpacing']:.0f} = {got:.3f}x, but the documented "
                    f"ratio is {want:.3f}x. Either the box drifted or the trade "
                    f"changed — if the latter, update EXPECTED_LINE_RATIO and say "
                    f"why.")
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
          f"{'stems':>8s} {'ink':>10s} {'advance':>8s} {'lineBox':>8s}  file")
    for r in sorted(rows, key=lambda r: (r["engine"], r["size"], r["font"])):
        adv = f"{r['advance']:8.3f}" if r["advance"] >= 0 else f"{'-':>8s}"
        print(f"{r['engine']:7s} {r['font']:14s} {r['size']:3d} {r['capH']:5d} "
              f"{r['bboxW']:6d} {r['stems']:>8s} {r['ink']:10,.0f} {adv} "
              f"{r['lineSpacing']:8.0f}  {r['file'] or '-'}")

    for e in errors:
        print(f"ERROR  {e}")

    fails = compare(rows, pairs, args.ink_tol)
    print()
    if fails or errors:
        for f in fails:
            print(f"FAIL  {f}")
        print(f"\n{len(fails)} parity failure(s), {len(errors)} probe error(s)")
        return 1
    print(f"OK  Latin renders identically to its source across "
          f"{len(pairs)} famil{'y' if len(pairs) == 1 else 'ies'} "
          f"x {len(args.sizes)} size(s) x 2 engines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
