#!/usr/bin/env python3
"""
One test per rule in md_clean, each written from a defect measured on a real
round trip on 2026-08-06. A rule without a test here is a rule somebody guessed.

    python3 tests/test_md_clean.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import md_clean as mc  # noqa: E402


class HeadingEmphasis(unittest.TestCase):
    def test_strips_whole_heading_bold(self):
        self.assertEqual(
            mc.strip_heading_emphasis("## **1. Executive Summary**"),
            "## 1. Executive Summary")

    def test_all_levels(self):
        src = "\n".join(f"{'#' * n} **H{n}**" for n in range(1, 7))
        want = "\n".join(f"{'#' * n} H{n}" for n in range(1, 7))
        self.assertEqual(mc.strip_heading_emphasis(src), want)

    def test_leaves_partial_emphasis_alone(self):
        # The author meant this one; only a fully-bold heading is the leak.
        src = "## Rated **2569** m3/day"
        self.assertEqual(mc.strip_heading_emphasis(src), src)

    def test_is_idempotent(self):
        once = mc.strip_heading_emphasis("# **T**")
        self.assertEqual(mc.strip_heading_emphasis(once), once)


class OrderedListRecovery(unittest.TestCase):
    def test_blockquote_of_numbers_becomes_a_list(self):
        src = ("> **1.** Detailed design\n"
               ">\n"
               "> **2.** Fabrication")
        self.assertEqual(mc.restore_ordered_lists(src),
                         "1. Detailed design\n2. Fabrication")

    def test_real_quotation_is_left_alone(self):
        src = "> **1.** is the clause number, and the rest is prose\n> not a list"
        self.assertEqual(mc.restore_ordered_lists(src), src)

    def test_quote_without_numbers_untouched(self):
        src = "> Installation by ICHITA-trained technicians only."
        self.assertEqual(mc.restore_ordered_lists(src), src)


class BlockquoteEmphasis(unittest.TestCase):
    def test_strips_whole_quote_italic(self):
        self.assertEqual(mc.strip_blockquote_emphasis("> *quoted text*"),
                         "> quoted text")

    def test_leaves_bold_alone(self):
        src = "> **bold** stays"
        self.assertEqual(mc.strip_blockquote_emphasis(src), src)


class Tables(unittest.TestCase):
    def test_unpads_and_unbolds_header(self):
        src = ("| **Parameter**      | **Design** |\n"
               "|--------------------|------------|\n"
               "| Feed flow          | 2569       |")
        self.assertEqual(
            mc.tidy_tables(src),
            "| Parameter | Design |\n|---|---|\n| Feed flow | 2569 |")

    def test_keeps_alignment(self):
        src = ("| A | B |\n"
               "|:---|---:|\n"
               "| 1 | 2 |")
        out = mc.tidy_tables(src).split("\n")[1]
        self.assertEqual(out, "|:---|---:|")

    def test_non_table_pipes_untouched(self):
        src = "The command is `a | b` in a sentence."
        self.assertEqual(mc.tidy_tables(src), src)


class Lists(unittest.TestCase):
    def test_tightens_same_kind(self):
        self.assertEqual(mc.tighten_lists("- a\n\n- b\n\n- c"), "- a\n- b\n- c")

    def test_separates_bullets_from_numbers(self):
        # Without the blank line these are one list and the numbers render
        # as literal text.
        self.assertEqual(mc.tighten_lists("- a\n1. b"), "- a\n\n1. b")

    def test_paragraph_between_items_survives(self):
        src = "- a\n\nA paragraph.\n\n- b"
        self.assertEqual(mc.tighten_lists(src), src)


class Escaping(unittest.TestCase):
    def test_unescapes_outside_tables(self):
        self.assertEqual(mc.unescape_spurious(r"a \| b"), "a | b")

    def test_leaves_table_rows_alone(self):
        src = r"| a \| b | c |"
        self.assertEqual(mc.unescape_spurious(src), src)

    def test_leaves_code_fences_alone(self):
        src = "```\ngrep \\| file\n```"
        self.assertEqual(mc.unescape_spurious(src), src)


class Thai(unittest.TestCase):
    def test_removes_space_before_a_combining_mark(self):
        # A mark after a space has nothing to attach to and renders on a
        # dotted circle. PDF extraction produces these.
        self.assertEqual(mc.repair_thai_runs("น้ำ"), "น้ำ")
        self.assertEqual(mc.repair_thai_runs("น ้ำ"), "น้ำ")

    def test_rejoins_split_digits(self):
        self.assertEqual(mc.rejoin_split_digits("2 5 6 9 m3"), "2569 m3")

    def test_leaves_two_digit_pairs_alone(self):
        # Two digits is a legitimate pair far more often than a split number.
        self.assertEqual(mc.rejoin_split_digits("page 1 2"), "page 1 2")

    def test_assert_thai_intact_passes_on_markup_change(self):
        mc.assert_thai_intact("## **หัวข้อ**", "## หัวข้อ")

    def test_assert_thai_intact_catches_mark_corruption(self):
        # The exact failure the May branded PDF showed: U+0E49 -> U+02D7.
        with self.assertRaises(ValueError) as cm:
            mc.assert_thai_intact("น้ำตาล", "น˗ำตาล")
        self.assertIn("0E49", str(cm.exception))

    def test_clean_normalises_to_nfc(self):
        # Decomposed SARA E + consonant must survive as the same Thai text.
        src = "# หัวข้อ\n"
        self.assertEqual(mc.clean(src), src)


class Whitespace(unittest.TestCase):
    def test_collapses_runs_of_blank_lines(self):
        self.assertEqual(mc.normalise_blank_lines("a\n\n\n\nb"), "a\n\nb\n")

    def test_strips_trailing_spaces(self):
        self.assertEqual(mc.normalise_blank_lines("a   \nb"), "a\nb\n")


class EndToEnd(unittest.TestCase):
    def test_clean_is_idempotent(self):
        # The compounding failure: two passes must not add a second layer.
        src = ("# **Title**\n\n"
               "| **A**  | **B**  |\n"
               "|--------|--------|\n"
               "| 1      | 2      |\n\n"
               "- x\n\n- y\n\n"
               "> **1.** step one\n>\n> **2.** step two\n")
        once = mc.clean(src)
        self.assertEqual(mc.clean(once), once)
        self.assertIn("# Title", once)
        self.assertIn("| A | B |", once)
        self.assertIn("1. step one", once)


if __name__ == "__main__":
    unittest.main(verbosity=2)
