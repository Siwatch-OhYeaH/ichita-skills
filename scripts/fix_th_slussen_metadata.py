#!/usr/bin/env python3
"""Fix TH-Slussen metadata — 5 fixes per Sibyl QA."""

import sys
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_DIR = Path("/mnt/c/Users/OhYeaH/OneDrive/Documents/fonts/fonts")

# fsSelection bits
ITALIC = 1 << 0
BOLD = 1 << 5
REGULAR = 1 << 6
USE_TYPO = 1 << 7

# head.macStyle bits
MAC_BOLD = 1 << 0
MAC_ITALIC = 1 << 1

WEIGHT_CONFIG = {
    "Regular": {
        "nameID6": "TH-Slussen-Regular",
        "fsSelection": REGULAR | USE_TYPO,
        "macStyle": 0,
        "weightClass": 400,
    },
    "Bold": {
        "nameID6": "TH-Slussen-Bold",
        "fsSelection": BOLD | USE_TYPO,
        "macStyle": MAC_BOLD,
        "weightClass": 700,
    },
    "Light": {
        "nameID6": "TH-Slussen-Light",
        "fsSelection": REGULAR | USE_TYPO,
        "macStyle": 0,
        "weightClass": 300,  # FIX: was 400
    },
    "Medium": {
        "nameID6": "TH-Slussen-Medium",
        "fsSelection": REGULAR | USE_TYPO,
        "macStyle": 0,
        "weightClass": 500,
    },
    "Semibold": {
        "nameID6": "TH-Slussen-Semibold",
        "fsSelection": REGULAR | USE_TYPO,
        "macStyle": 0,
        "weightClass": 600,
    },
    "RegularItalic": {
        "nameID6": "TH-Slussen-RegularItalic",
        "fsSelection": ITALIC | USE_TYPO,  # FIX: add ITALIC bit
        "macStyle": MAC_ITALIC,            # FIX: add italic
        "weightClass": 400,
    },
    "BoldItalic": {
        "nameID6": "TH-Slussen-BoldItalic",
        "fsSelection": BOLD | ITALIC | USE_TYPO,
        "macStyle": MAC_BOLD | MAC_ITALIC,
        "weightClass": 700,
    },
    "LightItalic": {
        "nameID6": "TH-Slussen-LightItalic",
        "fsSelection": ITALIC | USE_TYPO,  # FIX: add ITALIC bit
        "macStyle": MAC_ITALIC,            # FIX: add italic
        "weightClass": 300,                # FIX: was 400
    },
    "MediumItalic": {
        "nameID6": "TH-Slussen-MediumItalic",
        "fsSelection": ITALIC | USE_TYPO,  # FIX: add ITALIC bit
        "macStyle": MAC_ITALIC,            # FIX: add italic
        "weightClass": 500,
    },
    "SemiboldItalic": {
        "nameID6": "TH-Slussen-SemiboldItalic",
        "fsSelection": ITALIC | USE_TYPO,  # FIX: add ITALIC bit
        "macStyle": MAC_ITALIC,            # FIX: add italic
        "weightClass": 600,
    },
}


def fix_font(weight_name):
    cfg = WEIGHT_CONFIG[weight_name]
    path = FONT_DIR / f"TH-Slussen-{weight_name}.otf"

    if not path.exists():
        print(f"     !! Not found: {path}")
        return False

    font = TTFont(str(path))
    os2 = font["OS/2"]

    # Fix 1: fsType = 0 (installable)
    old_fstype = os2.fsType
    os2.fsType = 0

    # Fix 2: fsSelection
    old_fssel = os2.fsSelection
    os2.fsSelection = cfg["fsSelection"]

    # Fix 3: head.macStyle
    old_mac = font["head"].macStyle
    font["head"].macStyle = cfg["macStyle"]

    # Fix 4: weightClass
    old_wt = os2.usWeightClass
    os2.usWeightClass = cfg["weightClass"]

    # Fix 5: CFF fontName
    old_cff_name = None
    if "CFF " in font:
        old_cff_name = font["CFF "].cff.fontNames[0]
        font["CFF "].cff.fontNames[0] = cfg["nameID6"]

    font.save(str(path))

    print(f"     [fix] fsType: {old_fstype} -> 0")
    print(f"     [fix] fsSelection: 0x{old_fssel:04X} -> 0x{cfg['fsSelection']:04X}")
    print(f"     [fix] macStyle: {old_mac} -> {cfg['macStyle']}")
    print(f"     [fix] weightClass: {old_wt} -> {cfg['weightClass']}")
    if old_cff_name is not None:
        print(f"     [fix] CFF fontName: '{old_cff_name}' -> '{cfg['nameID6']}'")

    return True


def verify_font(weight_name):
    cfg = WEIGHT_CONFIG[weight_name]
    path = FONT_DIR / f"TH-Slussen-{weight_name}.otf"

    if not path.exists():
        print(f"     [verify] SKIP — file not found")
        return False

    font = TTFont(str(path))
    os2 = font["OS/2"]
    checks = []
    ok = True

    # Check fsType
    if os2.fsType == 0:
        checks.append("fsType=OK")
    else:
        checks.append(f"fsType=FAIL({os2.fsType})")
        ok = False

    # Check fsSelection
    if os2.fsSelection == cfg["fsSelection"]:
        checks.append(f"fsSel=OK(0x{os2.fsSelection:04X})")
    else:
        checks.append(f"fsSel=FAIL(got 0x{os2.fsSelection:04X} want 0x{cfg['fsSelection']:04X})")
        ok = False

    # Check macStyle
    mac = font["head"].macStyle
    if mac == cfg["macStyle"]:
        checks.append(f"macStyle=OK({mac})")
    else:
        checks.append(f"macStyle=FAIL(got {mac} want {cfg['macStyle']})")
        ok = False

    # Check weightClass
    if os2.usWeightClass == cfg["weightClass"]:
        checks.append(f"wt=OK({os2.usWeightClass})")
    else:
        checks.append(f"wt=FAIL(got {os2.usWeightClass} want {cfg['weightClass']})")
        ok = False

    # Check CFF fontName
    if "CFF " in font:
        cff_name = font["CFF "].cff.fontNames[0]
        if cff_name == cfg["nameID6"]:
            checks.append(f"CFF=OK('{cff_name}')")
        else:
            checks.append(f"CFF=FAIL(got '{cff_name}' want '{cfg['nameID6']}')")
            ok = False

    status = "PASS" if ok else "FAIL"
    print(f"     [verify] {status}: {' | '.join(checks)}")
    return ok


def main():
    print("\n" + "=" * 70)
    print("  TH-SLUSSEN METADATA FIX")
    print("  5 fixes: fsType, fsSelection, macStyle, weightClass, CFF fontName")
    print("=" * 70)

    success = 0
    verify_ok = 0
    total = len(WEIGHT_CONFIG)

    for weight_name in WEIGHT_CONFIG:
        print(f"\n  === {weight_name} ===")
        if fix_font(weight_name):
            success += 1
            if verify_font(weight_name):
                verify_ok += 1
        else:
            print(f"     [verify] SKIP — fix failed")

    print(f"\n{'=' * 70}")
    status = "PASS" if verify_ok == total else "FAIL"
    print(f"  {status}: {verify_ok}/{total} fonts fixed and verified")
    print(f"  Source: {FONT_DIR}")
    print(f"{'=' * 70}\n")

    return 0 if verify_ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
