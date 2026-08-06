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

import os
import re
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
BRIEF = REPO / "skills" / "ichita-exe-brief" / "scripts"

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


def pdf_text(pdf):
    import fitz
    return "".join(p.get_text() for p in fitz.open(pdf))


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


class PdfEngineSelection(unittest.TestCase):
    """The html -> pdf leg picks its engine from the document.

    Reported by Miipan, 2026-08-06. weasyprint was hard-wired, and it neither
    executes JavaScript nor writes a correct Thai text layer — so the one route
    meant for "Claude-designed layouts" silently produced empty PDFs, and the
    one meant for Thai produced unsearchable ones.
    """

    def test_js_built_document_is_rendered_not_skipped(self):
        # weasyprint renders the loading placeholder and exits 0. The whole
        # point of this test is that a green exit code proved nothing.
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "js.pdf"
            subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"),
                 str(FIXTURES / "js-shell.html"), str(out)],
                capture_output=True, text=True, timeout=300)
            self.assertTrue(out.exists())
            text = "".join(p.get_text() for p in fitz.open(out))
            for figure in ("1,000.00", "805.71", "928.94", "6,318.37", "Beer Thai"):
                self.assertIn(figure, text, "scripted content missing")
            self.assertNotIn("requires JavaScript", text)

    def test_weasyprint_alone_still_fails_the_js_shell(self):
        # Guards the guard: if this ever starts passing, weasyprint gained a JS
        # engine and the routing rule can be revisited. Until then it documents
        # why the rule exists.
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "js-weasy.pdf"
            subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"),
                 str(FIXTURES / "js-shell.html"), str(out),
                 "--engine", "weasyprint"],
                capture_output=True, text=True, timeout=300)
            text = "".join(p.get_text() for p in fitz.open(out))
            # The behavioural backstop should have caught it and re-rendered.
            self.assertIn("1,000.00", text,
                          "the shell backstop did not re-render with chromium")

    def test_thai_html_text_layer_is_nfc_identical(self):
        import fitz
        from bs4 import BeautifulSoup
        src_html = (FIXTURES / "thai-static.html").read_text(encoding="utf-8")
        want = thai_only(" ".join(
            p.get_text() for p in
            BeautifulSoup(src_html, "html.parser").find_all("p")))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "thai.pdf"
            subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"),
                 str(FIXTURES / "thai-static.html"), str(out)],
                capture_output=True, text=True, timeout=300)
            got = thai_only("".join(p.get_text() for p in fitz.open(out)))
            self.assertEqual(want, got)

    def test_english_only_still_uses_weasyprint(self):
        # weasyprint stays the default for what it is good at: a real CID-CFF
        # font program and a smaller file.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "en.pdf"
            proc = subprocess.run(
                [sys.executable, str(CONVERT),
                 str(FIXTURES / "table-heavy.md"), str(out)],
                capture_output=True, text=True, timeout=300)
            self.assertIn("Engine: weasyprint", proc.stdout)

    def test_content_wider_than_the_page_is_reported(self):
        # A wide landscape diagram gets clipped at the right edge, and
        # prefer_css_page_size cannot help. Must not pass silently.
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "wide.html"
            src.write_text(
                "<!DOCTYPE html><html><body><script>"
                "document.addEventListener('DOMContentLoaded',()=>{"
                "document.body.innerHTML="
                "'<div style=\"width:1700px\">wide diagram content</div>'});"
                "</script></body></html>", encoding="utf-8")
            out = Path(tmp) / "wide.pdf"
            proc = subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"), str(src), str(out)],
                capture_output=True, text=True, timeout=300)
            self.assertIn("cut off the right edge", proc.stderr)
            # ~1700 plus the body's default margin; assert the magnitude, not
            # a literal, or the test breaks on a UA stylesheet change.
            m = re.search(r"content lays out (\d+) px wide", proc.stderr)
            self.assertIsNotNone(m, proc.stderr)
            self.assertGreater(int(m.group(1)), 1600)

    def test_declaring_page_does_not_exempt_wide_content(self):
        """Declaring `@page` is not a promise that the content fits.

        The check used to read a `@page` rule as "the author has handled page
        geometry" and skip. `ichita.css` declares one and `emit_html.py`
        inlines it by default, so every branded document exempted itself and
        lost its right-hand columns at exit 0 — the same silent-substitution
        class this engine exists to prevent.
        """
        css = (REPO / "assets" / "brand" / "ichita.css").read_text(
            encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "wide-branded.html"
            src.write_text(
                '<meta charset="utf-8"><style>' + css + "</style>"
                '<div style="width:1700px;display:flex;'
                'justify-content:space-between">'
                "<span>LEFTEDGE</span><span>RIGHTEDGE</span></div>"
                "<p>" + ("Body text past the shell threshold. " * 8) + "</p>",
                encoding="utf-8")
            out = Path(tmp) / "wide-branded.pdf"
            proc = subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"), str(src), str(out),
                 "--engine", "chromium"],
                capture_output=True, text=True, timeout=300)
            self.assertIn("cut off the right edge", proc.stderr)
            # And the warning is true: the right-hand span really is gone.
            self.assertIn("LEFTEDGE", pdf_text(out))
            self.assertNotIn("RIGHTEDGE", pdf_text(out))

    def test_a_document_that_fits_is_not_flagged(self):
        """The converse, and the reason the margin is resolved in three states.

        `designed.html` links the brand stylesheet instead of inlining it, so
        `cssRules` throws SecurityError on `file://` and the real `margin: 0`
        is unreadable. Assuming our own 6 mm there reported 46 px of clipping
        that does not exist.
        """
        for fixture in ("designed.html", "thai-static.html", "figures.html"):
            with self.subTest(fixture=fixture):
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "fits.pdf"
                    proc = subprocess.run(
                        [sys.executable, str(BRIEF / "html2pdf.py"),
                         str(FIXTURES / fixture), str(out),
                         "--engine", "chromium"],
                        capture_output=True, text=True, timeout=300)
                    self.assertNotIn("cut off the right edge", proc.stderr)

    def test_shell_backstop_is_fatal_without_pymupdf(self):
        """The backstop must not disable itself.

        `pdf_text()` returns None when pymupdf is missing and the shell test
        read that as "not a shell", so the safety net for silent failure
        failed silently and shipped the 41-character placeholder at exit 0.
        """
        with tempfile.TemporaryDirectory() as tmp:
            shim = Path(tmp) / "shim"
            shim.mkdir()
            (shim / "fitz.py").write_text(
                'raise ImportError("pymupdf absent")\n', encoding="utf-8")
            env = dict(os.environ, PYTHONPATH=str(shim))
            out = Path(tmp) / "shell.pdf"
            proc = subprocess.run(
                [sys.executable, str(BRIEF / "html2pdf.py"),
                 str(FIXTURES / "js-shell.html"), str(out),
                 "--engine", "weasyprint"],
                capture_output=True, text=True, timeout=300, env=env)
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertIn("pymupdf", proc.stderr)


class HtmlAndPdfOutput(unittest.TestCase):
    def test_md_to_pdf_uses_only_brand_fonts(self):
        """No substitution — asked of whichever engine actually rendered.

        Chromium's Skia backend emits Type 3 fonts, which carry no name, so a
        PDF-side name check is impossible on that path. Chromium is asked
        directly instead, which is the better question anyway: it reports the
        font that was USED, not the one that was requested, so a @font-face
        that silently failed to load shows up.
        """
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o.pdf"
            stdout = convert(FIXTURES / "mixed.md", out)

            if "Engine: chromium" in stdout:
                self.assertIn("Fonts used: TH Aeonik", stdout)
                self.assertNotIn("non-brand font", stdout)
            else:
                doc = fitz.open(out)
                fonts = {f[3].split("+")[-1] for p in doc for f in p.get_fonts(True)}
                off_brand = [f for f in fonts if not any(
                    b in f for b in ("Aeonik", "Betatron", "Slussen"))]
                self.assertEqual(off_brand, [], f"non-brand fonts: {fonts}")

    def test_md_to_pdf_thai_text_layer_survives(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o.pdf"
            convert(FIXTURES / "mixed.md", out)
            got = thai_only("".join(p.get_text() for p in fitz.open(out)))
            want = thai_only((FIXTURES / "mixed.md").read_text(encoding="utf-8"))
            self.assertEqual(want, got)

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
