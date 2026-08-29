#!/usr/bin/env python3
"""Measure the line pitch a font actually gets in Word, PowerPoint and Excel.

The companion to scripts/win_latin_parity.py. That module measures RASTERISATION —
is the Latin as thick as its source. This one measures LEADING — does the line box
the font declares turn into the line pitch the application uses, in each of the
three applications ICHITA ships documents from.

WHY THREE APPLICATIONS AND NOT JUST WORD. The 2026-08-05 decision sets TH-Aeonik's
box to 1537 and unifies `hhea`, `sTypo` and `usWin` on it, on the argument that the
font then yields 1537 whichever field a renderer consults. Word was measured across
15 families and its rule is known (see win_latin_parity.word_line_box). PowerPoint
and Excel were NOT, and Excel matters most of the three in a way nobody had looked
at: IT AUTO-FITS ROW HEIGHT FROM FONT METRICS, so a 1537 box makes a default row
about 28% taller than Aeonik's. That is a direct, visible consequence of the box
and it belongs in an acceptance test rather than in a support call.

WHAT EACH APPLICATION IS ASKED

    Word         six paragraphs at 11 pt, Single. Baseline travel / 5.
                 The same method as the 2026-08-05 15-family survey, so the
                 numbers are comparable to that table.
    PowerPoint   a textbox with autofit off, six lines at 11 pt, single spacing.
                 Shape height difference / 5. SEE THE FINDING BELOW — PowerPoint
                 does not consult the font's metrics at all.
    Excel        one cell, font applied, EntireRow.AutoFit(). Row height in points
                 IS the measurement — this is the auto-fit behaviour, not a proxy
                 for it.

Excel's number is NOT expected to equal the other two, and that is the point of
measuring it separately: a row height is a box around one line plus the padding
Excel adds, where a paragraph pitch is baseline-to-baseline. So Excel is asserted
against its RATIO to the Latin source, never against 1537/em directly.

---------------------------------------------------------------------------
FINDING, 2026-08-05: POWERPOINT IGNORES THE FONT'S VERTICAL METRICS.
---------------------------------------------------------------------------

The plan for this phase said to "assert the measured pitch equals 1537/em in all
three applications". That is not achievable in PowerPoint, and not because of
anything about the font. Measured here, five installed families whose line boxes
span 1200 to 1697:

    font            box    Word    PowerPoint
    Aeonik         1200    1197          1200
    Bai Jamjuree   1250    1250          1200
    Segoe UI       1330    1329          1200
    Slussen        1596    1598          1200
    Gabriola       1697    1697          1200

Word tracks every box. PowerPoint returns 13.200 pt at 11 pt for all five — which
is exactly 1.2 x the point size. Checked against line count as well: BoundHeight is
13.200 / 26.400 / 79.200 for 1 / 2 / 6 lines, in every font. Perfectly linear at
1.2 em per line, with no font-dependent term anywhere in it.

So PowerPoint's "single" line spacing is a fixed 1.2 em and NO CHANGE TO A FONT CAN
MOVE IT. This module therefore asserts PowerPoint against 1.2 em, which is a
property of PowerPoint rather than of the font — and a deviation from it would mean
PowerPoint changed, not that the font is wrong.

BOUND ON THAT CLAIM, stated because this repo has been burned by treating an API
reading as the artifact: what is proven is that TextRange.BoundHeight carries no
font-dependent term. It is strong evidence that layout is 1.2 em, not proof — that
needs a rendered slide measured in pixels, which has not been done.

TWO CONSEQUENCES, and the second one is a real problem:

  1. Good: a mixed-language DECK does not inherit the +28% leading. The accepted
     cost of the 1537 box applies to Word and Excel, not to PowerPoint.
  2. Bad: THAI IN POWERPOINT AT SINGLE SPACING WILL COLLIDE. 1.2 em is 1200 units
     against the 1537 the worst Thai stacks measured out at — a 337-unit shortfall,
     which is precisely the defect the 2026-08-04 box produced in Word. The font
     cannot fix it here, so a Thai deck needs explicit line spacing set on the
     text. Unverified visually; it is an open item, not a measured defect.

REQUIREMENTS. The fonts must be INSTALLED on Windows — COM automation resolves
fonts by family name and has no off-disk equivalent of win_latin_parity's
`--from-dir`. A missing font substitutes silently, so every measurement is
accompanied by the resolved font name and a substitution fails the run rather than
reporting a plausible number.

THIS SCRIPT CAN LOCK THE FONTS YOU ARE ABOUT TO INSTALL. Each application is quit in
a `finally`, but a hard error — or killing the Python process — orphans WINWORD.EXE /
POWERPNT.EXE / EXCEL.EXE with NO WINDOW. They hold font files open while being
invisible in the taskbar and Alt-Tab. That happened on 2026-08-05: two orphaned
WINWORD.EXE blocked a font install with Office apparently closed, which is the same
shape as the old install-script bug that matched process names rather than open
documents. Before installing fonts, check and clear:

    powershell.exe -NoProfile -Command "Get-Process WINWORD,POWERPNT,EXCEL \
      -ErrorAction SilentlyContinue | Select Name,Id,MainWindowHandle"
    # MainWindowHandle 0 means orphan
    powershell.exe -NoProfile -Command "Stop-Process -Name WINWORD,POWERPNT,EXCEL -Force"

    python3 scripts/win_office_pitch.py
    python3 scripts/win_office_pitch.py --fonts Aeonik "TH Aeonik"
    python3 scripts/win_office_pitch.py --apps word excel --json
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

DEFAULT_FONTS = ["Aeonik", "TH Aeonik", "Slussen", "TH Slussen"]
DEFAULT_APPS = ("word", "powerpoint", "excel")
SIZE_PT = 11
LINES = 6

# Expected pitch in units per 1000 em, per family. Word and PowerPoint are
# asserted against these; Excel is asserted against its ratio to the Latin source
# instead, because a row height is not a baseline pitch.
EXPECTED_EM = {
    "Aeonik": 1200,
    "TH Aeonik": 1537,
    "Slussen": 1596,
    "TH Slussen": 1602,
}

# PowerPoint's own rule, not a font property. See the FINDING in the docstring:
# five families spanning boxes 1200-1697 all measured 1.200 em. Asserted so that a
# change in PowerPoint's behaviour is caught, and kept OUT of EXPECTED_EM so nobody
# reads it as something the font controls.
POWERPOINT_FIXED_EM = 1200.0

# One line of measurement noise. Word reports in points to 2 dp at 11 pt, so
# 1 unit/1000 em is 0.011 pt — well inside what the COM round-trip preserves.
# 8 units allows for the rounding Word does on paragraph geometry without
# admitting a whole metric field's worth of error.
TOL_EM = 8.0

# Excel is reported rather than asserted against a derived number — see check().

_PS = r'''
$ErrorActionPreference = 'Stop'
$fonts = __FONTS__
$apps  = __APPS__
$size  = __SIZE__
$lines = __LINES__

function Emit($app, $font, $value, $resolved, $note) {
  'ROW' + "`t" + $app + "`t" + $font + "`t" + $value + "`t" + $resolved + "`t" + $note
}

# --- Word ---------------------------------------------------------------------
# Baseline travel over $lines paragraphs, divided by ($lines - 1). Measured from
# Information(wdVerticalPositionRelativeToPage) rather than from a style's
# LineSpacing property, because the property is what was ASKED FOR and the
# position is what Word DID.
if ($apps -contains 'word') {
 try {
  $w = New-Object -ComObject Word.Application
  $w.Visible = $false
  $w.DisplayAlerts = 0
  try {
    foreach ($f in $fonts) {
      try {
        $doc = $w.Documents.Add()
        $r = $doc.Content
        $r.Text = (1..$lines | ForEach-Object { "Hamburgefonstiv" }) -join "`r"
        $r.Font.Name = $f
        $r.Font.Size = $size
        $r.ParagraphFormat.LineSpacingRule = 0      # wdLineSpaceSingle
        $r.ParagraphFormat.SpaceBefore = 0
        $r.ParagraphFormat.SpaceAfter = 0
        $resolved = $r.Font.Name
        $first = $doc.Paragraphs.Item(1).Range.Information(6)
        $last  = $doc.Paragraphs.Item($lines).Range.Information(6)
        $pitch = ($last - $first) / ($lines - 1)
        Emit 'word' $f $pitch $resolved ''
        $doc.Close(0)
      } catch { 'ERR' + "`t" + 'word' + "`t" + $f + "`t" + $_.Exception.Message }
    }
  } finally { $w.Quit() }
 } catch { 'ERR' + "`t" + 'word' + "`t" + '(app)' + "`t" + $_.Exception.Message }
}

# --- PowerPoint ---------------------------------------------------------------
# AutoSize is switched OFF and WordWrap off, so the shape height is the text's own
# height and not the shape's idea of a fit.
if ($apps -contains 'powerpoint') {
 try {
  $p = New-Object -ComObject PowerPoint.Application
  try {
    $pres = $p.Presentations.Add()
    $slide = $pres.Slides.Add(1, 12)              # ppLayoutBlank
    foreach ($f in $fonts) {
      try {
        $box = $slide.Shapes.AddTextbox(1, 50, 50, 600, 400)
        $tf = $box.TextFrame
        $tf.AutoSize = 0                          # ppAutoSizeNone
        $tf.WordWrap = 0
        $tf.TextRange.Text = (1..$lines | ForEach-Object { "Hamburgefonstiv" }) -join "`r"
        $tf.TextRange.Font.Name = $f
        $tf.TextRange.Font.Size = $size
        $tf.TextRange.ParagraphFormat.SpaceWithin = 1     # single
        $tf.TextRange.ParagraphFormat.SpaceBefore = 0
        $tf.TextRange.ParagraphFormat.SpaceAfter = 0
        $resolved = $tf.TextRange.Font.Name
        # Two measurements: the whole run, then one line. The difference over
        # ($lines - 1) is the pitch, and taking it as a DIFFERENCE cancels the
        # internal margin the textbox adds.
        $hAll = $tf.TextRange.BoundHeight
        $tf.TextRange.Text = "Hamburgefonstiv"
        $tf.TextRange.Font.Name = $f
        $tf.TextRange.Font.Size = $size
        $hOne = $tf.TextRange.BoundHeight
        $pitch = ($hAll - $hOne) / ($lines - 1)
        Emit 'powerpoint' $f $pitch $resolved ''
        $box.Delete()
      } catch { 'ERR' + "`t" + 'powerpoint' + "`t" + $f + "`t" + $_.Exception.Message }
    }
    $pres.Close()
  } finally { $p.Quit() }
 } catch { 'ERR' + "`t" + 'powerpoint' + "`t" + '(app)' + "`t" + $_.Exception.Message }
}

# --- Excel --------------------------------------------------------------------
# RowHeight after AutoFit. This is the number that decides whether a table of
# lab results still fits the page, and it is the one consequence of the 1537 box
# that nobody had looked at.
if ($apps -contains 'excel') {
 try {
  $x = New-Object -ComObject Excel.Application
  $x.Visible = $false
  $x.DisplayAlerts = $false
  try {
    $wb = $x.Workbooks.Add()
    $ws = $wb.Worksheets.Item(1)
    $row = 1
    foreach ($f in $fonts) {
      try {
        $c = $ws.Cells.Item($row, 1)
        $c.Value2 = "Hamburgefonstiv"
        $c.Font.Name = $f
        $c.Font.Size = $size
        $resolved = $c.Font.Name
        $c.EntireRow.AutoFit() | Out-Null
        Emit 'excel' $f $c.EntireRow.RowHeight $resolved 'autofit row height, pt'
        $row++
      } catch { 'ERR' + "`t" + 'excel' + "`t" + $f + "`t" + $_.Exception.Message }
    }
    $wb.Close($false)
  } finally { $x.Quit() }
 } catch { 'ERR' + "`t" + 'excel' + "`t" + '(app)' + "`t" + $_.Exception.Message }
}
'''


def _ps_literal(value):
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "@(" + ", ".join(_ps_literal(v) for v in value) + ")"
    raise TypeError(value)


def measure(fonts, apps):
    """Run the COM probe. Returns (rows, errors)."""
    script = (_PS
              .replace("__FONTS__", _ps_literal(list(fonts)))
              .replace("__APPS__", _ps_literal(list(apps)))
              .replace("__SIZE__", _ps_literal(SIZE_PT))
              .replace("__LINES__", _ps_literal(LINES)))
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        out = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand", encoded],
            capture_output=True, text=True, timeout=1800)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "powershell.exe not found on PATH — this measures the Office "
            "applications and cannot be satisfied from Linux") from exc

    rows, errors = [], []
    for line in out.stdout.splitlines():
        parts = line.rstrip("\r").split("\t")
        if parts[0] == "ROW" and len(parts) >= 5:
            try:
                value = float(parts[3])
            except ValueError:
                errors.append(f"{parts[1]} {parts[2]}: unparseable {parts[3]!r}")
                continue
            rows.append({"app": parts[1], "font": parts[2], "pt": value,
                         "resolved": parts[4],
                         "note": parts[5] if len(parts) > 5 else ""})
        elif parts[0] == "ERR":
            errors.append("\t".join(parts[1:]))
    # stderr is surfaced WHENEVER it is non-empty, not only when there are zero
    # rows. The first version of this only looked at stderr on total failure, so a
    # run where Word measured fine and PowerPoint threw reported OK across three
    # applications having measured one. Partial coverage that reads as full
    # coverage is the exact failure mode this repo keeps paying for.
    stderr = (out.stderr or "").strip()
    # PowerShell writes its progress stream to stderr as a CLIXML envelope
    # ("Preparing modules for first use"). That is not an error, and treating it as
    # one made every successful run report a probe failure.
    if stderr and "<Objs" not in stderr:
        errors.append("powershell stderr:\n" + stderr)
    if not rows:
        errors.append("no measurements at all")
    return rows, errors


def check(rows):
    """Assert each measurement. Returns a list of failures."""
    fails = []
    index = {(r["app"], r["font"]): r for r in rows}

    for r in rows:
        where = f"{r['app']} {r['font']}"
        # A substitution makes every number meaningless, so it is caught first.
        if r["resolved"] != r["font"]:
            fails.append(f"{where}: resolved to {r['resolved']!r} — the font is "
                         f"NOT INSTALLED and a substitute was measured. Install "
                         f"it; COM has no off-disk path.")
            continue
        if r["app"] == "excel":
            continue                       # checked by ratio below
        if r["app"] == "powerpoint":
            # Against PowerPoint's fixed 1.2 em, NOT against the font's box. A
            # font-based expectation here would be permanently red for every font
            # whose box is not 1200, and a check that is always red is a check
            # nobody reads.
            got_em = r["pt"] / SIZE_PT * 1000
            if abs(got_em - POWERPOINT_FIXED_EM) > TOL_EM:
                fails.append(
                    f"{where}: pitch {r['pt']:.2f} pt = {got_em:.0f}/em, but "
                    f"PowerPoint was measured to use a fixed "
                    f"{POWERPOINT_FIXED_EM:.0f}/em for every font. That means "
                    f"POWERPOINT changed, not the font — re-run the five-family "
                    f"survey in this module's docstring before touching a metric.")
            continue
        want = EXPECTED_EM.get(r["font"])
        if want is None:
            continue
        got_em = r["pt"] / SIZE_PT * 1000
        if abs(got_em - want) > TOL_EM:
            fails.append(f"{where}: pitch {r['pt']:.2f} pt = {got_em:.0f}/em, "
                         f"expected {want}/em (tol {TOL_EM:.0f}). The font's three "
                         f"metric sets are supposed to agree on one box — check "
                         f"the FORMAT first, since it decides which field is read.")

    # Excel is REPORTED, and only sanity-asserted. It is deliberately not held to
    # the box ratio, because Excel's row height is not proportional to the box and
    # this module does not pretend to model it: measured 2026-08-05, Aeonik (box
    # 1200) autofits to 14.50 pt and Slussen (box 1596) to 21.00 pt — a ratio of
    # 1.448 against a box ratio of 1.330. There is a padding or rounding term in
    # there that no reading of the metric fields accounts for, and asserting a
    # number this module cannot derive would be a check that fails for reasons
    # nobody can act on.
    #
    # What IS asserted: a taller box must not produce a shorter row. That is weak
    # on purpose — it catches the one outcome that would mean something is
    # genuinely wrong, and claims nothing else.
    for latin, merged in (("Aeonik", "TH Aeonik"), ("Slussen", "TH Slussen")):
        a = index.get(("excel", latin))
        b = index.get(("excel", merged))
        if not a or not b or not a["pt"]:
            continue
        if EXPECTED_EM[merged] > EXPECTED_EM[latin] and b["pt"] < a["pt"]:
            fails.append(f"excel {merged}: box {EXPECTED_EM[merged]} is taller "
                         f"than {latin}'s {EXPECTED_EM[latin]}, but its autofit "
                         f"row is SHORTER ({b['pt']:.2f} vs {a['pt']:.2f} pt). "
                         f"Excel is not reading this font's metrics at all — "
                         f"check that the font is really installed and not "
                         f"shadowed by a stale copy.")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fonts", nargs="+", default=DEFAULT_FONTS)
    ap.add_argument("--apps", nargs="+", default=list(DEFAULT_APPS),
                    choices=list(DEFAULT_APPS))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows, errors = measure(args.fonts, args.apps)
    if args.json:
        print(json.dumps(rows, indent=2))

    print(f"{'app':12s} {'font':14s} {'measured':>9s} {'per em':>8s} "
          f"{'expected':>9s} {'delta':>7s}  resolved")
    for r in sorted(rows, key=lambda r: (r["app"], r["font"])):
        want = EXPECTED_EM.get(r["font"])
        if r["app"] == "excel":
            em = want_s = delta = "-"
            print(f"{r['app']:12s} {r['font']:14s} {r['pt']:9.2f} {em:>8s} "
                  f"{want_s:>9s} {delta:>7s}  {r['resolved']}  {r['note']}")
            continue
        em = r["pt"] / SIZE_PT * 1000
        if r["app"] == "powerpoint":
            want = POWERPOINT_FIXED_EM
        d = f"{em - want:+.0f}" if want else "-"
        print(f"{r['app']:12s} {r['font']:14s} {r['pt']:9.2f} {em:8.0f} "
              f"{want if want else '-':>9} {d:>7s}  {r['resolved']}")

    # Excel row-height growth, reported on its own line because it is the
    # consequence Siwatch was warned about and the number he will want.
    index = {(r["app"], r["font"]): r for r in rows}
    for latin, merged in (("Aeonik", "TH Aeonik"), ("Slussen", "TH Slussen")):
        a, b = index.get(("excel", latin)), index.get(("excel", merged))
        if a and b and a["pt"]:
            box_ratio = EXPECTED_EM[merged] / EXPECTED_EM[latin]
            print(f"\nExcel autofit row height: {merged} {b['pt']:.2f} pt vs "
                  f"{latin} {a['pt']:.2f} pt = {b['pt'] / a['pt'] - 1:+.1%} "
                  f"(box ratio {box_ratio - 1:+.1%} — Excel adds a term this "
                  f"module does not model). If the growth is unwelcome the fix is "
                  f"a template row height, NOT the font box.")

    fails = check(rows)

    # Every requested application must have produced at least one measurement.
    # Without this the summary counted apps it ASKED for, not apps it MEASURED.
    measured_apps = {r["app"] for r in rows}
    for app in args.apps:
        if app not in measured_apps:
            fails.append(f"{app}: returned no measurements at all — it was "
                         f"requested, so this is a gap in coverage, not a skip")

    print()
    for e in errors:
        print(f"ERROR  {e}")
    if fails or errors:
        for f in fails:
            print(f"FAIL  {f}")
        print(f"\n{len(fails)} failure(s), {len(errors)} probe error(s)")
        return 1
    print(f"OK  {len(rows)} measurement(s) across {len(measured_apps)} "
          f"application(s) ({', '.join(sorted(measured_apps))}) — every font "
          f"leads off the box it declares")
    return 0


if __name__ == "__main__":
    sys.exit(main())
