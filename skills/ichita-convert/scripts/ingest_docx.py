#!/usr/bin/env python3
"""
docx -> markdown, via pandoc.

pandoc is the engine here for one reason that nothing else offers:
`--track-changes` reads Word's revision marks, so we can see what a human
actually changed rather than diffing two rendered documents and guessing. That
is the whole basis of the reconcile leg.

Usage:
    python ingest_docx.py IN.docx OUT.md [--track-changes all|accept|reject]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_clean import clean  # noqa: E402


def require_pandoc():
    if not shutil.which("pandoc"):
        print("ERROR: pandoc not found. See requirements.txt / install.sh.",
              file=sys.stderr)
        sys.exit(1)


def docx_to_md(src, dst, track_changes="accept", media_dir=None, quiet=False):
    """Convert a DOCX to cleaned GitHub-flavoured Markdown.

    track_changes:
      accept  — the document as the editor meant it to read (default)
      reject  — the document as it was before they touched it
      all     — every insertion and deletion marked inline; what reconcile uses

    Returns the markdown text.
    """
    require_pandoc()
    src, dst = Path(src), Path(dst)
    media = Path(media_dir) if media_dir else dst.parent / f"{dst.stem}-media"

    cmd = [
        "pandoc", "-f", "docx", "-t", "gfm",
        "--wrap=none",                     # or every paragraph arrives at 72 cols
        f"--track-changes={track_changes}",
        f"--extract-media={media}",
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"ERROR: pandoc failed:\n{proc.stderr}", file=sys.stderr)
        sys.exit(1)

    text = clean(proc.stdout, source="docx")

    # pandoc creates the media directory even when the document has no images.
    if media.exists() and not any(media.rglob("*")):
        media.rmdir()
    elif media.exists() and not quiet:
        n = sum(1 for p in media.rglob("*") if p.is_file())
        print(f"  extracted {n} media file(s) -> {media}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

    if not quiet:
        before = src.stat().st_size
        after = dst.stat().st_size
        print(f"  {src.name} -> {dst.name}  "
              f"{before:,} B -> {after:,} B  ({before / max(after, 1):.0f}x smaller)")
        if track_changes != "accept":
            print(f"  track-changes: {track_changes}")
    return text


def main():
    ap = argparse.ArgumentParser(description="DOCX -> Markdown.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--track-changes", default="accept",
                    choices=["accept", "reject", "all"])
    ap.add_argument("--media-dir", default=None)
    args = ap.parse_args()
    docx_to_md(args.input, args.output, args.track_changes, args.media_dir)


if __name__ == "__main__":
    main()
