#!/usr/bin/env python3
"""
Compare two DOCX generation pathways:
  Path A: md_to_docx.py  (Markdown -> branded DOCX directly)
  Path B: pandoc + rebrand_docx.py  (Markdown -> plain DOCX -> rebrand)

Outputs: test-path-A.docx, test-path-B.docx, comparison report
"""

import os
import sys
import subprocess
import zipfile
from lxml import etree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SCRIPTS = os.path.join(REPO_ROOT, "skills", "ichita-docx", "scripts")

INPUT_MD = os.path.join(SCRIPT_DIR, "test-bilingual.md")
OUTPUT_A = os.path.join(SCRIPT_DIR, "test-path-A.docx")
OUTPUT_B_PLAIN = os.path.join(SCRIPT_DIR, "test-path-B-plain.docx")
OUTPUT_B = os.path.join(SCRIPT_DIR, "test-path-B.docx")

NSMAP = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def run_path_a():
    """Path A: md_to_docx.py directly."""
    print("\n=== Path A: md_to_docx.py ===")
    cmd = [sys.executable, os.path.join(SCRIPTS, "md_to_docx.py"),
           INPUT_MD, OUTPUT_A, "--no-logo"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    return True


def run_path_b():
    """Path B: pandoc -> plain DOCX, then rebrand."""
    print("\n=== Path B: pandoc + rebrand_docx.py ===")

    # Step 1: pandoc to plain DOCX
    cmd = ["pandoc", INPUT_MD, "-o", OUTPUT_B_PLAIN, "--wrap=none"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"pandoc ERROR: {result.stderr}")
        return False
    print(f"  pandoc -> {OUTPUT_B_PLAIN}")

    # Step 2: rebrand
    cmd = [sys.executable, os.path.join(SCRIPTS, "rebrand_docx.py"),
           OUTPUT_B_PLAIN, OUTPUT_B]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"rebrand ERROR: {result.stderr}")
        return False
    return True


def extract_font_info(docx_path, label):
    """Extract font names and sizes from document.xml runs."""
    print(f"\n=== Font Analysis: {label} ===")

    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml")

    root = etree.fromstring(xml)
    body = root.find(".//w:body", NSMAP)

    stats = {
        "runs_total": 0,
        "runs_with_cs_font": 0,
        "runs_with_szCs": 0,
        "latin_fonts": set(),
        "cs_fonts": set(),
        "sz_values": set(),
        "szCs_values": set(),
        "samples": [],
    }

    for p in body.findall(".//w:p", NSMAP):
        for r in p.findall(".//w:r", NSMAP):
            stats["runs_total"] += 1
            rPr = r.find("w:rPr", NSMAP)
            t = r.find("w:t", NSMAP)
            text = t.text[:30] if t is not None and t.text else ""

            if rPr is not None:
                rFonts = rPr.find("w:rFonts", NSMAP)
                if rFonts is not None:
                    ascii_f = rFonts.get(f'{{{NSMAP["w"]}}}ascii', '')
                    cs_f = rFonts.get(f'{{{NSMAP["w"]}}}cs', '')
                    if ascii_f:
                        stats["latin_fonts"].add(ascii_f)
                    if cs_f:
                        stats["cs_fonts"].add(cs_f)
                        stats["runs_with_cs_font"] += 1

                sz = rPr.find("w:sz", NSMAP)
                szCs = rPr.find("w:szCs", NSMAP)
                sz_val = sz.get(f'{{{NSMAP["w"]}}}val', '') if sz is not None else ''
                szCs_val = szCs.get(f'{{{NSMAP["w"]}}}val', '') if szCs is not None else ''

                if sz_val:
                    stats["sz_values"].add(sz_val)
                if szCs_val:
                    stats["szCs_values"].add(szCs_val)
                    stats["runs_with_szCs"] += 1

                if text and len(stats["samples"]) < 5:
                    stats["samples"].append({
                        "text": text,
                        "ascii": ascii_f if rFonts is not None else '',
                        "cs": cs_f if rFonts is not None else '',
                        "sz": sz_val,
                        "szCs": szCs_val,
                    })

    print(f"  Total runs: {stats['runs_total']}")
    print(f"  Runs with cs font: {stats['runs_with_cs_font']} "
          f"({100*stats['runs_with_cs_font']/max(stats['runs_total'],1):.0f}%)")
    print(f"  Runs with szCs: {stats['runs_with_szCs']} "
          f"({100*stats['runs_with_szCs']/max(stats['runs_total'],1):.0f}%)")
    print(f"  Latin fonts: {stats['latin_fonts']}")
    print(f"  CS fonts: {stats['cs_fonts']}")
    print(f"  sz values (half-pt): {sorted(stats['sz_values'])}")
    print(f"  szCs values (half-pt): {sorted(stats['szCs_values'])}")
    print(f"  Sample runs:")
    for s in stats["samples"]:
        print(f"    '{s['text']}' -> ascii={s['ascii']}, cs={s['cs']}, "
              f"sz={s['sz']}({int(s['sz'])//2 if s['sz'] else '?'}pt), "
              f"szCs={s['szCs']}({int(s['szCs'])//2 if s['szCs'] else '?'}pt)")

    return stats


def compare(stats_a, stats_b):
    """Compare font stats between two documents."""
    print("\n=== COMPARISON ===")
    issues = []

    # Check Thai font coverage
    if stats_a["runs_with_cs_font"] == 0:
        issues.append("Path A: NO runs have cs (Thai) font set!")
    if stats_b["runs_with_cs_font"] == 0:
        issues.append("Path B: NO runs have cs (Thai) font set!")

    if stats_a["runs_with_szCs"] == 0:
        issues.append("Path A: NO runs have szCs (Thai size) set!")
    if stats_b["runs_with_szCs"] == 0:
        issues.append("Path B: NO runs have szCs (Thai size) set!")

    # Check font names
    if "Bai Jamjuree" not in stats_a["cs_fonts"]:
        issues.append("Path A: Bai Jamjuree NOT in cs fonts!")
    if "Bai Jamjuree" not in stats_b["cs_fonts"]:
        issues.append("Path B: Bai Jamjuree NOT in cs fonts!")

    if "Aeonik" not in stats_a["latin_fonts"] and "Calibri" not in stats_a["latin_fonts"]:
        issues.append("Path A: Neither Aeonik nor Calibri in latin fonts!")

    # Check sz/szCs are different (Thai scale applied)
    if stats_a["sz_values"] == stats_a["szCs_values"] and stats_a["szCs_values"]:
        issues.append("Path A: sz == szCs (Thai scale NOT applied!)")
    if stats_b["sz_values"] == stats_b["szCs_values"] and stats_b["szCs_values"]:
        issues.append("Path B: sz == szCs (Thai scale NOT applied!)")

    if issues:
        print("  ISSUES FOUND:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  All checks passed!")

    return issues


def main():
    if not os.path.exists(INPUT_MD):
        print(f"ERROR: {INPUT_MD} not found")
        sys.exit(1)

    ok_a = run_path_a()
    ok_b = run_path_b()

    if ok_a:
        stats_a = extract_font_info(OUTPUT_A, "Path A (md_to_docx)")
    if ok_b:
        stats_b = extract_font_info(OUTPUT_B, "Path B (pandoc + rebrand)")

    if ok_a and ok_b:
        issues = compare(stats_a, stats_b)
        if not issues:
            print("\nSUCCESS: Both paths produce correctly formatted documents!")
        else:
            print(f"\nFAILED: {len(issues)} issue(s) found")
            sys.exit(1)


if __name__ == "__main__":
    main()
