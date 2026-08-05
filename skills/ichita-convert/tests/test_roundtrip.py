#!/usr/bin/env python3
"""
End-to-end conversion tests. Slow — they run pandoc, LibreOffice and
weasyprint against real fixtures.

    python3 tests/test_roundtrip.py

The one that matters most is test_docx_roundtrip_is_idempotent. Every defect
this pipeline has had compounds: a bold heading gains another `**` on each
pass, so a single round trip looks fine and the bug only appears on the second.
Pass one is not a test of anything.
"""

import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
CONVERT = ROOT / "scripts" / "convert.py"

sys.path.insert(0, str(ROOT / "scripts"))


def convert(src, dst, *extra):
    proc = subprocess.run(
        [sys.executable, str(CONVERT), str(src), str(dst), *extra],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise AssertionError(f"convert {src} -> {dst} failed:\n{proc.stderr}")
    return proc.stdout


def thai_only(s):
    s = unicodedata.normalize("NFC", s)
    return "".join(c for c in s if "฀" <= c <= "๿")


class DocxRoundTrip(unittest.TestCase):
    """md -> docx -> md -> docx -> md must be stable from pass two on."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ichita-rt-"))
        src = FIXTURES / "mixed.md"
        convert(src, cls.tmp / "a.docx")
        convert(cls.tmp / "a.docx", cls.tmp / "b.md")
        convert(cls.tmp / "b.md", cls.tmp / "c.docx")
        convert(cls.tmp / "c.docx", cls.tmp / "d.md")
        cls.src = src.read_text(encoding="utf-8")
        cls.b = (cls.tmp / "b.md").read_text(encoding="utf-8")
        cls.d = (cls.tmp / "d.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_idempotent_on_second_pass(self):
        self.assertEqual(self.b, self.d)

    def test_thai_survives_nfc(self):
        self.assertEqual(thai_only(self.src), thai_only(self.b))

    def test_no_bold_leak_in_headings(self):
        for line in self.b.splitlines():
            if line.startswith("#"):
                self.assertNotIn("**", line, f"bold leaked into: {line}")

    def test_ordered_list_survives_as_a_list(self):
        self.assertIn("1. Detailed design", self.b)
        self.assertNotIn("> **1.**", self.b)

    def test_table_survives(self):
        self.assertIn("| Feed flow | 2569 | 2400 | m³/day |", self.b)

    def test_sentences_are_not_split_at_the_source_wrap(self):
        # md_to_docx used to emit one Word paragraph per source LINE, baking
        # the author's 90-column wrapping into the document.
        self.assertIn("replacing the existing carbon-only", self.b)

    def test_sidecar_is_written(self):
        self.assertTrue((self.tmp / "a.docx.ichita-convert.json").exists())


class TableHeavy(unittest.TestCase):
    def test_every_table_survives_the_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = FIXTURES / "table-heavy.md"
            convert(src, tmp / "t.docx")
            convert(tmp / "t.docx", tmp / "t.md")
            out = (tmp / "t.md").read_text(encoding="utf-8")
            for tag in ("ME-201", "P-201", "CT-204"):
                self.assertIn(tag, out)
            # Three tables in, three tables out. Counted by delimiter ROWS —
            # counting the substring `|---|` finds several per row, because
            # the separators share their pipes.
            delims = [l for l in out.splitlines()
                      if set(l.strip()) <= set("|-: ") and l.strip().startswith("|")]
            self.assertEqual(len(delims), 3, delims)


class DesignedHtml(unittest.TestCase):
    def test_card_markup_becomes_readable_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "d.md"
            convert(FIXTURES / "designed.html", out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("**2569**", text)          # not \*\*2569\*\*
            self.assertNotIn("\\*", text)
            self.assertIn("## 01. Positioning", text)
            self.assertIn("| Siam Refinery |", text)
            self.assertNotIn("Print / Save PDF", text)   # chrome dropped


@unittest.skipUnless(shutil.which("soffice"), "LibreOffice not installed")
class PdfLeg(unittest.TestCase):
    """The Phase 2 gate: Thai must survive a real PDF, byte for byte."""

    def test_thai_survives_pdf_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = FIXTURES / "mixed.md"
            convert(src, tmp / "a.docx")
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf",
                 "--outdir", str(tmp), str(tmp / "a.docx")],
                capture_output=True, timeout=300)
            pdf = tmp / "a.pdf"
            self.assertTrue(pdf.exists(), "LibreOffice produced no PDF")
            convert(pdf, tmp / "back.md")
            got = (tmp / "back.md").read_text(encoding="utf-8")
            self.assertEqual(thai_only(src.read_text(encoding="utf-8")),
                             thai_only(got))

    def test_no_space_inside_a_wrapped_thai_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            convert(FIXTURES / "mixed.md", tmp / "a.docx")
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf",
                 "--outdir", str(tmp), str(tmp / "a.docx")],
                capture_output=True, timeout=300)
            convert(tmp / "a.pdf", tmp / "back.md")
            got = (tmp / "back.md").read_text(encoding="utf-8")
            self.assertIn("ใช้พลังงานจำเพาะ", got)


class Figures(unittest.TestCase):
    """The measured fact this exists for: ICHITA's charts are vector.

    Every page of an ICHITA PDF carries one raster image — the logo — and
    26 to 77 vector paths. A get_images() extractor recovers the logo and not
    a single chart, which is why the figures are found in get_drawings().
    """

    def test_vector_charts_are_found_and_placed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pdf = tmp / "figures.pdf"
            subprocess.run(
                [sys.executable,
                 str(REPO / "skills" / "ichita-exe-brief" / "scripts" / "html2pdf.py"),
                 str(FIXTURES / "figures.html"), str(pdf)],
                capture_output=True, timeout=300)
            self.assertTrue(pdf.exists())

            import fitz
            page = fitz.open(pdf)[0]
            self.assertEqual(len(page.get_images(full=True)), 0,
                             "fixture should have no raster images")
            self.assertGreater(len(page.get_drawings()), 10)

            out = tmp / "figures.md"
            convert(pdf, out)
            text = out.read_text(encoding="utf-8")
            self.assertEqual(text.count("!["), 2, text)
            media = tmp / "figures-media"
            self.assertEqual(len(list(media.glob("*.png"))), 2)

            # Placed in reading order: each figure follows its own heading.
            i1 = text.index("Figure 1")
            i2 = text.index("Figure 2")
            f1 = text.index("p1-fig1.png")
            f2 = text.index("p1-fig2.png")
            self.assertLess(i1, f1)
            self.assertLess(f1, i2)
            self.assertLess(i2, f2)


class HtmlAndPdfOutput(unittest.TestCase):
    def test_md_to_pdf_embeds_only_brand_fonts(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o.pdf"
            convert(FIXTURES / "mixed.md", out)
            doc = fitz.open(out)
            fonts = {f[3].split("+")[-1] for p in doc for f in p.get_fonts(True)}
            off_brand = [f for f in fonts if not any(
                b in f for b in ("Aeonik", "Betatron", "Slussen"))]
            self.assertEqual(off_brand, [], f"non-brand fonts embedded: {fonts}")

    def test_html_output_declares_the_right_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o.html"
            convert(FIXTURES / "mixed.md", out)
            html = out.read_text(encoding="utf-8")
            self.assertIn("doc-th", html)            # source has Thai
            self.assertIn("--ichita-font: 'TH Aeonik'", html)
            # `AeonikTH` is the family the two hand-built briefs declared and
            # that has never existed. Match the DECLARATION, not the string —
            # ichita.css names it in a comment saying not to use it.
            self.assertNotIn("font-family: 'AeonikTH'", html)
            self.assertNotIn("@font-face { font-family: 'AeonikTH'", html)


class Reconcile(unittest.TestCase):
    def test_fast_forward_takes_the_word_edit(self):
        from docx import Document
        from reconcile import write_sidecar
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            record = tmp / "record.md"
            record.write_text(
                (FIXTURES / "mixed.md").read_text(encoding="utf-8"),
                encoding="utf-8")
            convert(record, tmp / "a.docx")

            doc = Document(tmp / "a.docx")
            for p in doc.paragraphs:
                for r in p.runs:
                    if "30/60/10" in r.text:
                        r.text = r.text.replace("30/60/10", "40/50/10")
            doc.save(tmp / "edited.docx")
            write_sidecar(record, tmp / "edited.docx", timestamp="test")

            proc = subprocess.run(
                [sys.executable, str(CONVERT), "reconcile",
                 str(tmp / "edited.docx"), str(record)],
                capture_output=True, text=True, timeout=300)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("Fast-forward", proc.stdout)
            self.assertIn("40/50/10", record.read_text(encoding="utf-8"))

    def test_conflict_writes_nothing_without_accept(self):
        from docx import Document
        from reconcile import write_sidecar
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            record = tmp / "record.md"
            record.write_text(
                (FIXTURES / "mixed.md").read_text(encoding="utf-8"),
                encoding="utf-8")
            convert(record, tmp / "a.docx")

            doc = Document(tmp / "a.docx")
            for p in doc.paragraphs:
                for r in p.runs:
                    if "60 days" in r.text:
                        r.text = r.text.replace("60 days", "90 days")
            doc.save(tmp / "edited.docx")
            write_sidecar(record, tmp / "edited.docx", timestamp="test")

            # Move the record too, in the same place.
            before = record.read_text(encoding="utf-8")
            record.write_text(before.replace("60 days", "45 days"),
                              encoding="utf-8")
            moved = record.read_text(encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(CONVERT), "reconcile",
                 str(tmp / "edited.docx"), str(record)],
                capture_output=True, text=True, timeout=300)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("conflicting hunk", proc.stdout)
            self.assertEqual(record.read_text(encoding="utf-8"), moved,
                             "reconcile wrote without being told to")


if __name__ == "__main__":
    unittest.main(verbosity=2)
