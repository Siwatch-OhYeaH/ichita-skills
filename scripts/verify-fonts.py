#!/usr/bin/env python3
"""
verify-fonts.py — Ichita Font Validator
========================================
Validates TH-Aeonik fonts meet Ichita production requirements using fontTools.

Checks per TH-Aeonik font:
  1. Thai glyph coverage   — cmap contains U+0E00–U+0E7F glyphs
  2. OS/2 ulUnicodeRange   — bit 24 set (Thai)
  3. OS/2 usWinAscent      — >= 1550 (headroom for Thai diacritics)
  4. OS/2 ulCodePageRange  — CP874 set (Thai codepage, bit 16)
  5. GPOS table            — present (kerning/positioning)
  6. GDEF table            — present (glyph classification)
  7. name table RIBBI      — nameID 1, 2, 4, 6 present and non-empty
  8. fsSelection/macStyle  — Bold bit consistent between OS/2 and head

Also runs basic Thai coverage check on Bai Jamjuree fonts.

Usage:
  python3 verify-fonts.py
  python3 verify-fonts.py --path /path/to/fonts/

Exit codes:
  0 — all checks pass
  1 — one or more checks fail
"""

import argparse
import sys
from pathlib import Path

# ── fontTools import check ────────────────────────────────────────────────────
try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("ERROR: fontTools is not installed.")
    print("")
    print("Install it with:")
    print("  pip install fonttools")
    print("  # or: pip3 install fonttools")
    print("  # or: uv pip install fonttools  (if using uv)")
    sys.exit(1)


# ── Constants ─────────────────────────────────────────────────────────────────

# Thai Unicode block range
THAI_BLOCK_START = 0x0E00
THAI_BLOCK_END   = 0x0E7F

# We require at least this many Thai glyphs to consider coverage meaningful
THAI_GLYPH_MIN = 50

# OS/2 Unicode Range bit for Thai (bit 24 = the 25th bit)
UNICODE_RANGE_THAI_BIT = 24

# OS/2 Code Page Range bit for CP874 Thai (bit 16)
CP874_BIT = 16

# Minimum usWinAscent for Thai diacritics
MIN_WIN_ASCENT = 1550

# RIBBI name IDs
NAME_IDS = {
    1: "Family Name",
    2: "Subfamily (Style)",
    4: "Full Name",
    6: "PostScript Name",
}

# OS/2 fsSelection Bold bit = bit 5
FSSEL_BOLD_BIT = 5

# head macStyle Bold bit = bit 0
MACSTYLE_BOLD_BIT = 0


# ── Result helpers ────────────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def _bit(value: int, bit: int) -> bool:
    """Return True if the given bit is set in value."""
    return bool(value & (1 << bit))


# ── Individual checks ─────────────────────────────────────────────────────────

def check_thai_coverage(font: TTFont) -> tuple[str, str]:
    """Check cmap for glyphs in the Thai Unicode block (U+0E00–U+0E7F)."""
    cmap_table = font.getBestCmap()
    if cmap_table is None:
        return FAIL, "No cmap table found"

    thai_glyphs = [cp for cp in cmap_table if THAI_BLOCK_START <= cp <= THAI_BLOCK_END]
    count = len(thai_glyphs)

    if count == 0:
        return FAIL, "0 Thai glyphs in cmap (U+0E00–U+0E7F)"
    elif count < THAI_GLYPH_MIN:
        return WARN, f"Only {count} Thai glyphs (expected >= {THAI_GLYPH_MIN}) — partial coverage"
    else:
        return PASS, f"{count} Thai glyphs in cmap"


def check_unicode_range_thai(font: TTFont) -> tuple[str, str]:
    """Check OS/2 ulUnicodeRange bit 24 (Thai)."""
    if "OS/2" not in font:
        return FAIL, "No OS/2 table"

    os2 = font["OS/2"]
    val = os2.ulUnicodeRange1  # bits 0–31 live in ulUnicodeRange1
    # Bit 24 is within bits 0-31, so ulUnicodeRange1 is correct
    if _bit(val, UNICODE_RANGE_THAI_BIT):
        return PASS, f"ulUnicodeRange1 bit 24 set (Thai) — value: 0x{val:08X}"
    else:
        return FAIL, f"ulUnicodeRange1 bit 24 NOT set — value: 0x{val:08X}"


def check_win_ascent(font: TTFont) -> tuple[str, str]:
    """Check OS/2 usWinAscent >= 1550."""
    if "OS/2" not in font:
        return FAIL, "No OS/2 table"

    ascent = font["OS/2"].usWinAscent
    if ascent >= MIN_WIN_ASCENT:
        return PASS, f"usWinAscent = {ascent} (>= {MIN_WIN_ASCENT})"
    else:
        return FAIL, f"usWinAscent = {ascent} (< {MIN_WIN_ASCENT} — Thai diacritics may clip)"


def check_cp874(font: TTFont) -> tuple[str, str]:
    """Check OS/2 ulCodePageRange bit 16 (CP874 Thai codepage)."""
    if "OS/2" not in font:
        return FAIL, "No OS/2 table"

    os2 = font["OS/2"]
    # ulCodePageRange1 holds bits 0–31
    val = os2.ulCodePageRange1
    if _bit(val, CP874_BIT):
        return PASS, f"CP874 bit 16 set — ulCodePageRange1: 0x{val:08X}"
    else:
        return FAIL, f"CP874 bit 16 NOT set — ulCodePageRange1: 0x{val:08X}"


def check_gpos(font: TTFont) -> tuple[str, str]:
    """Check that GPOS table exists."""
    if "GPOS" in font:
        return PASS, "GPOS table present"
    else:
        return FAIL, "GPOS table missing (no kerning/positioning)"


def check_gdef(font: TTFont) -> tuple[str, str]:
    """Check that GDEF table exists."""
    if "GDEF" in font:
        return PASS, "GDEF table present"
    else:
        return FAIL, "GDEF table missing (no glyph classification)"


def check_name_ribbi(font: TTFont) -> tuple[str, str]:
    """Check name table for RIBBI entries (nameID 1, 2, 4, 6)."""
    if "name" not in font:
        return FAIL, "No name table"

    name_table = font["name"]
    missing = []

    for name_id, label in NAME_IDS.items():
        record = name_table.getDebugName(name_id)
        if not record or not record.strip():
            missing.append(f"nameID {name_id} ({label})")

    if missing:
        return FAIL, "Missing RIBBI names: " + ", ".join(missing)
    else:
        # Show the family name for confirmation
        family = name_table.getDebugName(1) or "?"
        style  = name_table.getDebugName(2) or "?"
        return PASS, f'nameID 1="{family}", 2="{style}"'


def check_bold_consistency(font: TTFont) -> tuple[str, str]:
    """Check Bold bit consistency between OS/2.fsSelection and head.macStyle."""
    if "OS/2" not in font:
        return FAIL, "No OS/2 table"
    if "head" not in font:
        return FAIL, "No head table"

    os2_bold  = _bit(font["OS/2"].fsSelection, FSSEL_BOLD_BIT)
    head_bold = _bit(font["head"].macStyle, MACSTYLE_BOLD_BIT)

    if os2_bold == head_bold:
        state = "Bold=ON" if os2_bold else "Bold=OFF"
        return PASS, f"fsSelection and macStyle consistent ({state})"
    else:
        return FAIL, (
            f"Mismatch: OS/2.fsSelection Bold={'ON' if os2_bold else 'OFF'}, "
            f"head.macStyle Bold={'ON' if head_bold else 'OFF'}"
        )


# ── Full TH-Aeonik validation ─────────────────────────────────────────────────

TH_AEONIK_CHECKS = [
    ("Thai glyph coverage",         check_thai_coverage),
    ("OS/2 Unicode Range Thai",     check_unicode_range_thai),
    ("OS/2 usWinAscent >= 1550",    check_win_ascent),
    ("OS/2 CP874 codepage",         check_cp874),
    ("GPOS table",                  check_gpos),
    ("GDEF table",                  check_gdef),
    ("RIBBI name entries",          check_name_ribbi),
    ("Bold bit consistency",        check_bold_consistency),
]


def validate_th_aeonik(font_path: Path) -> dict:
    """Run all TH-Aeonik checks on a single font file. Returns results dict."""
    results = {}
    try:
        font = TTFont(str(font_path), lazy=True)
    except Exception as e:
        # Fatal: can't open the file
        for name, _ in TH_AEONIK_CHECKS:
            results[name] = (FAIL, f"Cannot open font: {e}")
        return results

    for check_name, check_fn in TH_AEONIK_CHECKS:
        try:
            status, detail = check_fn(font)
        except Exception as e:
            status, detail = FAIL, f"Exception: {e}"
        results[check_name] = (status, detail)

    font.close()
    return results


# ── Basic Bai Jamjuree Thai coverage check ────────────────────────────────────

def validate_bai_jamjuree(font_path: Path) -> dict:
    """Run basic Thai coverage check on a Bai Jamjuree font."""
    results = {}
    try:
        font = TTFont(str(font_path), lazy=True)
        status, detail = check_thai_coverage(font)
        results["Thai glyph coverage"] = (status, detail)
        font.close()
    except Exception as e:
        results["Thai glyph coverage"] = (FAIL, f"Cannot open font: {e}")
    return results


# ── Table rendering ───────────────────────────────────────────────────────────

def _status_col(status: str) -> str:
    """Format status with padding."""
    return f"[{status}]".ljust(6)


def print_font_results(font_name: str, results: dict) -> bool:
    """Print a results block for one font. Returns True if all PASS."""
    all_pass = True
    print(f"\n  {font_name}")
    print(f"  {'─' * (len(font_name) + 2)}")
    for check_name, (status, detail) in results.items():
        if status == FAIL:
            all_pass = False
        col = _status_col(status)
        print(f"    {col} {check_name}")
        print(f"           {detail}")
    return all_pass


def print_summary_table(all_results: dict[str, dict]) -> bool:
    """
    Print a compact summary table: rows = fonts, columns = checks.
    Returns True if everything passes.
    """
    # Gather all unique check names in order
    check_names: list[str] = []
    for results in all_results.values():
        for name in results:
            if name not in check_names:
                check_names.append(name)

    # Column widths
    font_col_w = max((len(f) for f in all_results), default=10)
    col_w = 6  # "PASS  " or "FAIL  " or "WARN  "

    # Header
    print("")
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)

    # Check name header (abbreviated to 6 chars)
    header_abbrs = [c[:6].ljust(col_w) for c in check_names]
    print(f"  {'Font'.ljust(font_col_w)}  {'  '.join(header_abbrs)}")
    print(f"  {'-' * font_col_w}  {'  '.join(['-' * col_w] * len(check_names))}")

    global_pass = True
    for font_name, results in all_results.items():
        cells = []
        for check_name in check_names:
            if check_name in results:
                status = results[check_name][0]
                if status == FAIL:
                    global_pass = False
                cells.append(status.ljust(col_w))
            else:
                cells.append("N/A   ")
        print(f"  {font_name.ljust(font_col_w)}  {'  '.join(cells)}")

    print("")
    return global_pass


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Ichita fonts meet production requirements.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to the font directory (default: ../assets/fonts/ relative to this script)",
    )
    args = parser.parse_args()

    # Resolve font directory
    if args.path:
        font_dir = Path(args.path).resolve()
    else:
        script_dir = Path(__file__).parent.resolve()
        font_dir = (script_dir / ".." / "assets" / "fonts").resolve()

    if not font_dir.is_dir():
        print(f"ERROR: Font directory not found: {font_dir}", file=sys.stderr)
        return 1

    print(f"Ichita Font Validator")
    print(f"Font directory: {font_dir}")
    print(f"fontTools version: ", end="")
    try:
        import fontTools
        print(fontTools.version)
    except Exception:
        print("unknown")

    # ── TH-Aeonik (full validation) ───────────────────────────────────────────
    th_aeonik_dir = font_dir / "th-aeonik"
    th_aeonik_fonts = sorted(th_aeonik_dir.glob("TH-Aeonik-*.otf")) if th_aeonik_dir.is_dir() else []

    print(f"\n{'=' * 80}")
    print(f"TH-AEONIK VALIDATION ({len(th_aeonik_fonts)} fonts)")
    print(f"{'=' * 80}")

    if not th_aeonik_fonts:
        print(f"  WARNING: No TH-Aeonik-*.otf files found in {th_aeonik_dir}", file=sys.stderr)

    th_results: dict[str, dict] = {}
    for font_path in th_aeonik_fonts:
        results = validate_th_aeonik(font_path)
        th_results[font_path.name] = results
        print_font_results(font_path.name, results)

    th_pass = print_summary_table(th_results) if th_results else True

    # ── Bai Jamjuree (basic Thai coverage check) ──────────────────────────────
    bj_dir = font_dir / "bai-jamjuree"
    bj_fonts = sorted(bj_dir.glob("BaiJamjuree-*.ttf")) if bj_dir.is_dir() else []

    print(f"\n{'=' * 80}")
    print(f"BAI JAMJUREE — THAI COVERAGE CHECK ({len(bj_fonts)} fonts)")
    print(f"{'=' * 80}")

    if not bj_fonts:
        print(f"  WARNING: No BaiJamjuree-*.ttf files found in {bj_dir}", file=sys.stderr)

    bj_results: dict[str, dict] = {}
    for font_path in bj_fonts:
        results = validate_bai_jamjuree(font_path)
        bj_results[font_path.name] = results
        status, detail = results["Thai glyph coverage"]
        print(f"  {_status_col(status)} {font_path.name} — {detail}")

    bj_pass = all(
        res["Thai glyph coverage"][0] != FAIL
        for res in bj_results.values()
    ) if bj_results else True

    # ── Final verdict ─────────────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    overall = th_pass and bj_pass
    if overall:
        print("RESULT: ALL CHECKS PASSED")
    else:
        print("RESULT: SOME CHECKS FAILED — see details above")
    print(f"{'=' * 80}\n")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
