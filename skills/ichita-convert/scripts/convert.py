#!/usr/bin/env python3
"""
ichita-convert — one entry point for every document conversion.

    python convert.py IN OUT [options]
    python convert.py reconcile EDITED.docx CURRENT.md [options]

The extension pair picks the route. Anything that is not a direct leg chains
through Markdown, because Markdown is the record — see reference/inbound.md.

    from \\ to   md              docx              html    pdf
    md          -               md_to_docx        direct  via html
    docx        pandoc          rebrand_docx      via md  via md
    html        markdownify     html_to_docx      -       html2pdf
    pdf         pymupdf         via md            via md  -

Two rules that are not obvious from the matrix:

  * Delivery PDFs must come from Print-to-PDF or one of the engines measured in
    reference/pdf-delivery.md. Word's Save-as-PDF silently substitutes Calibri
    for our CFF fonts and the file still lists them as embedded.
  * An edited DOCX is not the record. Convert it back, or the change is lost
    the next time the Markdown is rendered.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOCX_SKILL = REPO / "skills" / "ichita-docx" / "scripts"
BRIEF_SKILL = REPO / "skills" / "ichita-exe-brief" / "scripts"

sys.path.insert(0, str(HERE))

KNOWN = {"md", "markdown", "docx", "html", "htm", "pdf"}


def _ext(path):
    e = Path(path).suffix.lower().lstrip(".")
    return {"markdown": "md", "htm": "html"}.get(e, e)


def _run_script(script_dir, script, *args):
    """Run one of the sibling skills' scripts as a subprocess.

    A subprocess rather than an import on purpose: md_to_docx and html_to_docx
    both define module-level brand constants and mutate them from the CLI
    arguments, so importing two of them into one process would have the second
    silently reconfigure the first.
    """
    cmd = [sys.executable, str(Path(script_dir) / script), *map(str, args)]
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        print(f"ERROR: {script} exited {proc.returncode}", file=sys.stderr)
        sys.exit(proc.returncode)


# ── Direct legs ──────────────────────────────────────────────────────────────

def docx_to_md(src, dst, opts):
    from ingest_docx import docx_to_md as f
    f(src, dst, track_changes=opts.track_changes)


def html_to_md(src, dst, opts):
    from ingest_html import html_to_md as f
    f(src, dst)


def pdf_to_md(src, dst, opts):
    from ingest_pdf import pdf_to_md as f
    f(src, dst, figures=not opts.no_figures, dpi=opts.dpi)


def md_to_html(src, dst, opts):
    from emit_html import md_to_html as f
    f(src, dst, title=opts.title, link_css=opts.link_css)


def md_to_docx(src, dst, opts):
    extra = ["--font-mode", opts.font_mode] if opts.font_mode != "auto" else []
    _run_script(DOCX_SKILL, "md_to_docx.py", src, dst, *extra)
    # Provenance, written at the moment the two files agree. Without it a
    # returned DOCX can only be two-way diffed, which cannot tell an edit made
    # in Word from a change made to the Markdown since.
    from reconcile import write_sidecar
    car = write_sidecar(src, dst, font_mode=opts.font_mode,
                        timestamp=opts.timestamp)
    print(f"  provenance: {Path(car).name}")


def html_to_docx(src, dst, opts):
    _run_script(DOCX_SKILL, "html_to_docx.py", src, dst)


def html_to_pdf(src, dst, opts):
    _run_script(BRIEF_SKILL, "html2pdf.py", src, dst,
                "--fonts", REPO / "assets" / "fonts")


def docx_to_docx(src, dst, opts):
    _run_script(DOCX_SKILL, "rebrand_docx.py", src, dst)


DIRECT = {
    ("docx", "md"):   docx_to_md,
    ("html", "md"):   html_to_md,
    ("pdf", "md"):    pdf_to_md,
    ("md", "html"):   md_to_html,
    ("md", "docx"):   md_to_docx,
    ("html", "docx"): html_to_docx,
    ("html", "pdf"):  html_to_pdf,
    ("docx", "docx"): docx_to_docx,
}

# Everything else goes through Markdown, and md->pdf goes on through HTML.
CHAIN_HUB = "md"


def _plan(src_ext, dst_ext):
    """Return the list of hops from src_ext to dst_ext."""
    if (src_ext, dst_ext) in DIRECT:
        return [(src_ext, dst_ext)]
    if src_ext == "md" and dst_ext == "pdf":
        return [("md", "html"), ("html", "pdf")]
    hops = []
    if src_ext != CHAIN_HUB:
        if (src_ext, CHAIN_HUB) not in DIRECT:
            return None
        hops.append((src_ext, CHAIN_HUB))
    hops.extend(_plan(CHAIN_HUB, dst_ext) or [])
    return hops if hops and hops[-1][1] == dst_ext else None


def convert(src, dst, opts):
    src, dst = Path(src), Path(dst)
    se, de = _ext(src), _ext(dst)

    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        sys.exit(1)
    for e, what in ((se, "input"), (de, "output")):
        if e not in KNOWN:
            print(f"ERROR: unsupported {what} format '.{e}'. "
                  f"Known: md, docx, html, pdf", file=sys.stderr)
            sys.exit(1)

    plan = _plan(se, de)
    if not plan:
        print(f"ERROR: no route from .{se} to .{de}", file=sys.stderr)
        sys.exit(1)

    if len(plan) > 1:
        print(f"Route: {' -> '.join([plan[0][0]] + [h[1] for h in plan])}")

    before = src.stat().st_size
    with tempfile.TemporaryDirectory(prefix="ichita-convert-") as tmp:
        current = src
        for i, (a, b) in enumerate(plan):
            last = i == len(plan) - 1
            # Intermediate Markdown lands beside the final output, not in the
            # temp dir, when the user asked for Markdown-adjacent media: the
            # image references in it have to keep resolving.
            if last:
                out = dst
            elif b == "md":
                out = dst.parent / f"{dst.stem}.intermediate.md"
            else:
                out = Path(tmp) / f"step{i}.{b}"
            out.parent.mkdir(parents=True, exist_ok=True)
            DIRECT[(a, b)](current, out, opts)
            current = out

        # Keep the intermediate Markdown only when asked; it is a debugging
        # aid, and leaving it behind by default litters the output directory.
        stale = dst.parent / f"{dst.stem}.intermediate.md"
        if stale.exists() and stale != dst:
            if opts.keep_intermediate:
                print(f"  kept intermediate: {stale.name}")
            else:
                stale.unlink()
                media = dst.parent / f"{dst.stem}.intermediate-media"
                if media.exists():
                    shutil.rmtree(media, ignore_errors=True)

    after = dst.stat().st_size if dst.exists() else 0
    if de == "md" and after:
        print(f"  context cost: {before:,} B of {se.upper()} -> {after:,} B of "
              f"Markdown ({before / max(after, 1):.0f}x less to read)")


# ── Entry point ──────────────────────────────────────────────────────────────

def build_parser():
    ap = argparse.ArgumentParser(
        prog="convert.py",
        description="ICHITA document conversion. Markdown is the record.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Two rules")[0].split("The extension pair")[1],
    )
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("output", nargs="?", type=Path)
    ap.add_argument("--track-changes", default="accept",
                    choices=["accept", "reject", "all"],
                    help="docx input: how to treat Word revision marks")
    ap.add_argument("--no-figures", action="store_true",
                    help="pdf input: skip figure extraction")
    ap.add_argument("--dpi", type=int, default=200,
                    help="pdf input: figure render resolution")
    ap.add_argument("--title", default=None, help="html output: <title>")
    ap.add_argument("--link-css", action="store_true",
                    help="html output: link ichita.css instead of inlining")
    ap.add_argument("--font-mode", default="auto",
                    choices=["auto", "unified", "split"],
                    help="docx output: override the language-based face choice")
    ap.add_argument("--keep-intermediate", action="store_true",
                    help="keep the Markdown a chained route passes through")
    return ap


def main():
    from datetime import datetime, timezone

    # `reconcile` is dispatched before argparse rather than as a subparser.
    # A subparser and two optional positionals cannot coexist: argparse tries
    # the subcommand first and rejects `convert.py in.md out.docx` because
    # `in.md` is not a known command.
    if len(sys.argv) > 1 and sys.argv[1] == "reconcile":
        rec = argparse.ArgumentParser(
            prog="convert.py reconcile",
            description="Merge a hand-edited DOCX back into the Markdown record.")
        rec.add_argument("edited", type=Path)
        rec.add_argument("current", type=Path)
        rec.add_argument("--accept", choices=["theirs", "ours", "interactive"],
                         default=None)
        rargs = rec.parse_args(sys.argv[2:])
        from reconcile import reconcile as do_reconcile
        sys.exit(do_reconcile(rargs.edited, rargs.current, rargs.accept))

    ap = build_parser()
    args = ap.parse_args()
    args.timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if not args.input or not args.output:
        ap.print_help()
        sys.exit(2)

    convert(args.input, args.output, args)


if __name__ == "__main__":
    main()
