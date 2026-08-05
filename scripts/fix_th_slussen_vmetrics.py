#!/usr/bin/env python3
"""
fix_th_slussen_vmetrics.py
Fix vertical metrics in TH-Slussen fonts to match original Slussen rendering.

Problem: Thai merge process changed these metrics, making Word render text
         at a different apparent size than original Slussen.

Changes:
  sTypoLineGap:  300  → 166   (restore original — controls line spacing when USE_TYPO_METRICS set)
  usWinAscent:   1550 → 1262  (restore original — Thai max Y is 1225, fits safely)
  usWinDescent:  561  → 561   (KEEP — Thai descenders reach -561 in Bold; changing would clip glyphs)
  fsSelection bit 7 (USE_TYPO_METRICS): already True on all fonts — no change needed

Reference values (original Slussen):
  sTypoAscender:  1074
  sTypoDescender: -272
  sTypoLineGap:    166
  usWinAscent:    1262
  usWinDescent:    334  ← cannot restore; Thai glyphs need 561

Thai glyph bounds analysis (across all 10 fonts):
  Max Y: 1225 (Bold) — fits within WinAscent 1262
  Min Y: -561 (Bold) — requires WinDescent >= 561
"""

from pathlib import Path
from fontTools.ttLib import TTFont

FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts" / "th-slussen"

TARGET_METRICS = {
    "sTypoLineGap": 166,    # Restore original
    "usWinAscent": 1262,    # Restore original (Thai max Y = 1225, fits)
    "usWinDescent": 561,    # Keep — Thai descenders reach 561 (Bold)
}

WEIGHTS = [
    "Regular", "Bold", "Light", "Medium", "Semibold",
    "RegularItalic", "BoldItalic", "LightItalic", "MediumItalic", "SemiboldItalic",
]


def read_metrics(os2):
    return {
        "sTypoAscender":  os2.sTypoAscender,
        "sTypoDescender": os2.sTypoDescender,
        "sTypoLineGap":   os2.sTypoLineGap,
        "usWinAscent":    os2.usWinAscent,
        "usWinDescent":   os2.usWinDescent,
        "USE_TYPO_METRICS": bool(os2.fsSelection & 0x80),
    }


def print_metrics_table(label, data):
    print(f"\n{'='*95}")
    print(f"  {label}")
    print(f"{'='*95}")
    print(f"{'Font':<32} {'TypoAsc':>8} {'TypoDsc':>8} {'TypoGap':>8} {'WinAsc':>8} {'WinDsc':>8} {'USE_TYPO':>10}")
    print("-" * 95)
    for name, m in data.items():
        print(
            f"{name:<32} {m['sTypoAscender']:>8} {m['sTypoDescender']:>8} "
            f"{m['sTypoLineGap']:>8} {m['usWinAscent']:>8} {m['usWinDescent']:>8} "
            f"{str(m['USE_TYPO_METRICS']):>10}"
        )


def main():
    fonts = {w: FONTS_DIR / f"TH-Slussen-{w}.otf" for w in WEIGHTS}

    # Verify all exist
    missing = [w for w, p in fonts.items() if not p.exists()]
    if missing:
        print(f"ERROR: Missing fonts: {missing}")
        return

    # --- BEFORE ---
    before = {}
    for weight, path in fonts.items():
        font = TTFont(path)
        before[weight] = read_metrics(font["OS/2"])
    print_metrics_table("BEFORE — Current TH-Slussen metrics", before)

    # --- FIX ---
    print(f"\n{'='*95}")
    print("  APPLYING FIXES")
    print(f"  sTypoLineGap: 300 → 166  (restore original)")
    print(f"  usWinAscent:  1550 → 1262  (restore original; Thai max Y = 1225)")
    print(f"  usWinDescent: 561 → 561  (no change; Thai min Y = -561 in Bold)")
    print(f"  fsSelection bit 7: already True — no change")
    print(f"{'='*95}")

    after = {}
    for weight, path in fonts.items():
        font = TTFont(path)
        os2 = font["OS/2"]

        changed = []
        for metric, target in TARGET_METRICS.items():
            current = getattr(os2, metric)
            if current != target:
                setattr(os2, metric, target)
                changed.append(f"{metric}: {current} → {target}")

        font.save(path)
        after[weight] = read_metrics(font["OS/2"])

        status = "  ".join(changed) if changed else "no changes"
        print(f"  {weight:<30} {status}")

    print_metrics_table("AFTER — Fixed TH-Slussen metrics", after)

    # --- DIFF SUMMARY ---
    print(f"\n{'='*95}")
    print("  DIFF SUMMARY")
    print(f"{'='*95}")
    metrics_to_diff = ["sTypoLineGap", "usWinAscent", "usWinDescent", "USE_TYPO_METRICS"]
    all_same = True
    for weight in WEIGHTS:
        for m in metrics_to_diff:
            b = before[weight][m]
            a = after[weight][m]
            if b != a:
                print(f"  {weight:<30} {m}: {b} → {a}")
                all_same = False
    if all_same:
        print("  No differences (already correct?)")

    print(f"\nDone. Fixed fonts saved to: {FONTS_DIR}")


if __name__ == "__main__":
    main()
