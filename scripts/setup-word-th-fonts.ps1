# Configure Word so TH Aeonik supplies Thai while Aeonik keeps the Latin.
#
# WHY THIS EXISTS, and why it is not a font fix:
#
# A font carries ONE set of vertical metrics, so it produces ONE line height for
# every line it sets. TH Aeonik leads 1540/1000 em because that is the measured
# minimum for two consecutive Thai lines to clear at Word's Single spacing —
# Aeonik's 1200 is 262 units short. So any document whose LATIN is set in
# TH Aeonik gets +28.3% line spacing on Latin-only lines. Measured in Word at
# 11 pt Single, baselines read off Word's own PDF export:
#
#   Aeonik                                  Latin-only  13.20 pt
#   TH Aeonik (both slots)                  every line  16.92 pt   +28.2%
#   ascii=Aeonik + cs=TH Aeonik             Latin-only  13.20 pt   identical
#   ascii=Aeonik + cs=TH Aeonik             with Thai   16.92 pt   widens, fits
#
# Word takes a line's height from the fonts actually used in that line, and
# resolves Latin and Complex Script through separate slots. The bottom row is
# what Siwatch asked for: Aeonik spacing on Latin, wider only when Thai appears.
#
# THE RIBBON CANNOT EXPRESS IT. Setting the font from the ribbon font box calls
# Font.Name, which overwrites the Latin AND the Complex Script slot (verified
# 2026-08-04), putting you straight back to 16.92 pt. That is why this is a
# script and not an instruction to click something.
#
# SizeBi is also set, because it is INDEPENDENT of Size and Word's default left
# it at 14 against a Size of 11 — so Thai was typing two points larger than the
# Latin and in a fallback face, bypassing the harmonisation entirely.
#
#   powershell -ExecutionPolicy Bypass -File setup-word-th-fonts.ps1 -ActiveDocument
#   powershell -ExecutionPolicy Bypass -File setup-word-th-fonts.ps1 -Template   (Word CLOSED)
#
# -ActiveDocument converts the document already open: it sets the Complex Script
# font and leaves the Latin ALONE, so an existing Aeonik document keeps its Latin
# byte-for-byte and merely gains Thai support. That is the correct way to "add
# Thai" to an old document — do NOT restyle its Latin to TH Aeonik.

param(
    [string]$LatinFont = "Aeonik",
    [string]$ThaiFont  = "TH Aeonik",
    [switch]$ActiveDocument,
    [switch]$Template
)

$ErrorActionPreference = "Stop"

try {
    $w = [Runtime.InteropServices.Marshal]::GetActiveObject("Word.Application")
    $attached = $true
} catch {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    $attached = $false
}

function Set-Slots($font, $label) {
    # Order matters: set the Latin slots first, then the complex-script slot,
    # because assigning Font.Name (which we never do here) would clobber both.
    $font.NameAscii = $LatinFont
    $font.NameOther = $LatinFont
    $font.NameBi    = $ThaiFont
    if ($font.Size -gt 0) { $font.SizeBi = $font.Size }
    "  {0,-28} Latin={1}  ComplexScript={2}  Size={3} SizeBi={4}" -f `
        $label, $font.NameAscii, $font.NameBi, $font.Size, $font.SizeBi
}

if ($Template) {
    # --- the default template, so NEW documents need no setup at all ---
    #
    # ONLY with Word closed. Word holds Normal.dotm open for its whole session,
    # and OpenAsDocument() on it then blocks indefinitely with no dialog and no
    # error — it hung here on 2026-08-04 and had to be killed. Word's own
    # Font dialog > Set As Default writes the same thing safely while running,
    # so that is the recommended route; this branch is for unattended setup.
    if (Get-Process WINWORD -ErrorAction SilentlyContinue) {
        throw "Close Word first: it holds Normal.dotm open and this will hang. " +
              "Or use Ctrl+D > Set As Default > All documents instead."
    }
    $ntPath = $w.NormalTemplate.FullName
    $backup = [IO.Path]::ChangeExtension($ntPath, "beforeTH.dotm")
    if (-not (Test-Path $backup)) {
        Copy-Item $ntPath $backup
        "Backed up Normal.dotm -> $backup"
    } else {
        "Backup already present at $backup (left as-is)"
    }

    # Styles on NormalTemplate are only reachable once it is open as a document.
    $doc = $w.NormalTemplate.OpenAsDocument()
    "Normal.dotm:"
    foreach ($name in @("Normal")) {
        Set-Slots $doc.Styles.Item($name).Font $name
    }
    $doc.Save()
    $doc.Close(0)
    "Saved. New documents will now type Latin in $LatinFont and Thai in $ThaiFont."
}

if ($ActiveDocument -or -not $Template) {
    try {
        $d = $w.ActiveDocument
        "$($d.Name):"
        Set-Slots $d.Styles.Item("Normal").Font "style Normal"
        # Direct formatting on existing runs overrides the style, so the body has
        # to be touched too — Latin slots included, since a document already set
        # in TH Aeonik must be put BACK onto Aeonik for the Latin.
        Set-Slots $d.Content.Font "body text"
        "Converted. Latin is $LatinFont, Thai is $ThaiFont — save to keep it."
    } catch {
        "(no document open to convert: $($_.Exception.Message))"
    }
}

if (-not $attached) { $w.Quit() }
