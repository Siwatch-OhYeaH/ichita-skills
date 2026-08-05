#!/usr/bin/env python3
"""
Merge a hand-edited DOCX back into the Markdown record.

The workflow this serves: we emit a branded DOCX, a human edits it in Word
because the template is already there, and they may print and deliver straight
from Word. The Markdown is still the record — but only if their edits come
back. This is how they come back.

The model is Word's own: show the difference and let the human decide. Nothing
is overwritten silently, because the failure mode of a silent merge is losing
an edit nobody knew about until the client asked why it was missing.

    python reconcile.py EDITED.docx CURRENT.md [--accept theirs|ours|interactive]
"""

import base64
import difflib
import gzip
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SIDECAR_SUFFIX = ".ichita-convert.json"
TOOL_VERSION = 1

# Anything that opens a Markdown block; a line starting with one of these is
# never a soft-wrap continuation of the line above.
_BLOCK = __import__("re").compile(
    r'^(?:[ \t]*$|#{1,6}[ \t]|>|[-*+][ \t]|\d+\.[ \t]|\||```|:::|---+[ \t]*$)')


def normalise_wrap(text):
    """Join soft-wrapped lines so a diff shows edits, not line breaks.

    A human writes Markdown wrapped at 90 columns; every inbound conversion
    emits it unwrapped. Diffed as-is, one changed word reports the whole
    document as rewritten and the actual edit is invisible in the noise. The
    comparison has to be on content, so both sides are unwrapped first.
    """
    out, para = [], []

    def flush():
        if para:
            out.append(" ".join(para))
            para.clear()

    for line in text.split("\n"):
        if _BLOCK.match(line):
            flush()
            out.append(line)
        else:
            para.append(line.strip())
    flush()
    return "\n".join(out).strip("\n") + "\n"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sidecar_path(docx):
    return Path(docx).with_suffix(Path(docx).suffix + SIDECAR_SUFFIX)


def write_sidecar(md, docx, font_mode="auto", timestamp=None):
    """Record where a DOCX came from, plus a snapshot of the source.

    Provenance is hashes and paths. The one thing stored beyond that is a
    gzipped copy of the Markdown as it was when the DOCX was written — the
    merge base. Without it a three-way merge is impossible and the best this
    tool could do is a two-way diff that cannot tell an edit from a revert.

    Note what is deliberately NOT here: any model of the DOCX's formatting. A
    formatting-delta sidecar would be a second schema of the brand's styling,
    kept in step with both the Markdown and the emitter, and the first time it
    drifted it would produce a confidently-wrong restore.
    """
    md, docx = Path(md), Path(docx)
    base = md.read_bytes()
    data = {
        "tool_version": TOOL_VERSION,
        "timestamp": timestamp,
        "md": {"path": str(md), "sha256": hashlib.sha256(base).hexdigest()},
        "docx": {"path": str(docx), "sha256": sha256(docx)},
        "font_mode": font_mode,
        "base_md_gz_b64": base64.b64encode(gzip.compress(base)).decode("ascii"),
    }
    p = sidecar_path(docx)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def read_sidecar(docx):
    p = sidecar_path(docx)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _base_text(car):
    blob = car.get("base_md_gz_b64")
    if not blob:
        return None
    return gzip.decompress(base64.b64decode(blob)).decode("utf-8")


def _show_diff(a, b, a_name, b_name, limit=60):
    lines = list(difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile=a_name, tofile=b_name, lineterm="", n=2))
    if not lines:
        print(f"  (no difference between {a_name} and {b_name})")
        return 0
    for line in lines[:limit]:
        print("  " + line)
    if len(lines) > limit:
        print(f"  ... {len(lines) - limit} more diff line(s)")
    return sum(1 for l in lines if l.startswith(("+", "-"))
               and not l.startswith(("+++", "---")))


def three_way(base, ours, theirs):
    """Merge line-wise. Returns (merged_text, conflicts).

    Non-overlapping hunks from both sides are taken. Where both sides changed
    the same region, the region is emitted with conflict markers and counted.
    """
    b, o, t = base.splitlines(), ours.splitlines(), theirs.splitlines()
    sm_o = difflib.SequenceMatcher(None, b, o, autojunk=False)
    sm_t = difflib.SequenceMatcher(None, b, t, autojunk=False)

    # Map each base line range to what each side did with it.
    def opmap(sm):
        m = {}
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            m[(i1, i2)] = (tag, j1, j2)
        return m

    out, conflicts = [], 0
    ops_o, ops_t = opmap(sm_o), opmap(sm_t)

    # Walk the base in the union of both sides' block boundaries.
    bounds = sorted({i for r in list(ops_o) + list(ops_t) for i in r})
    for start, end in zip(bounds, bounds[1:]):
        def side(ops, text_lines):
            for (i1, i2), (tag, j1, j2) in ops.items():
                if i1 <= start and end <= i2:
                    if tag == "equal":
                        return b[start:end], False
                    span = text_lines[j1:j2]
                    return span, True
            return b[start:end], False

        o_lines, o_changed = side(ops_o, o)
        t_lines, t_changed = side(ops_t, t)

        if o_changed and t_changed and o_lines != t_lines:
            conflicts += 1
            out.append("<<<<<<< ours (the Markdown record)")
            out.extend(o_lines)
            out.append("=======")
            out.extend(t_lines)
            out.append(">>>>>>> theirs (edited in Word)")
        elif t_changed:
            out.extend(t_lines)
        else:
            out.extend(o_lines)

    return "\n".join(out) + "\n", conflicts


def reconcile(edited_docx, current_md, accept=None):
    from ingest_docx import docx_to_md

    edited_docx, current_md = Path(edited_docx), Path(current_md)
    for p in (edited_docx, current_md):
        if not p.exists():
            print(f"ERROR: {p} not found", file=sys.stderr)
            return 1

    car = read_sidecar(edited_docx)

    with tempfile.TemporaryDirectory(prefix="ichita-reconcile-") as tmp:
        theirs_path = Path(tmp) / "theirs.md"
        # --track-changes=all so a tracked-but-unaccepted edit is visible here
        # rather than silently dropped. It is the only way to see what a human
        # changed in Word rather than inferring it from the rendered result.
        theirs = docx_to_md(edited_docx, theirs_path,
                            track_changes="all", quiet=True)

    ours = ours_raw = current_md.read_text(encoding="utf-8")

    if car is None:
        print(f"No sidecar for {edited_docx.name} — this DOCX was not emitted "
              f"by convert.py, or the {SIDECAR_SUFFIX} file was not kept "
              f"beside it.")
        print("Falling back to a two-way diff. This is LESS RELIABLE: without "
              "the merge base there is no way to tell an edit in Word from a "
              "change made to the Markdown since.\n")
        n = _show_diff(ours, theirs, str(current_md), f"{edited_docx.name} (as markdown)")
        if accept == "theirs":
            current_md.write_text(theirs, encoding="utf-8")
            print(f"\n  --accept theirs: wrote {current_md} ({n} changed line(s))")
            return 0
        print("\nNothing written. Re-run with --accept theirs to take the "
              "Word version wholesale.")
        return 1 if n else 0

    base = _base_text(car)
    if base is not None:
        # Compare and merge on unwrapped text. The hash check below still uses
        # the raw bytes — whether the record moved is a fact about the file,
        # not about its wrapping.
        base, theirs = normalise_wrap(base), normalise_wrap(theirs)
        ours = normalise_wrap(ours)
    if base is None:
        print(f"Sidecar for {edited_docx.name} predates merge-base storage "
              f"(tool_version {car.get('tool_version')}). Two-way diff only.\n")
        _show_diff(ours, theirs, str(current_md), edited_docx.name)
        return 1

    # Hashed on the raw bytes, not the unwrapped text: whether the record moved
    # is a fact about the file on disk.
    ours_moved = (hashlib.sha256(ours_raw.encode()).hexdigest()
                  != car["md"]["sha256"])
    theirs_moved = theirs.strip() != base.strip()

    if not theirs_moved:
        print(f"  {edited_docx.name} matches the Markdown it was made from. "
              f"Nothing to reconcile.")
        return 0

    if not ours_moved:
        # Fast-forward: the record has not moved, so the Word edits are the
        # only change and there is nothing to conflict with.
        print(f"Fast-forward: {current_md.name} is unchanged since "
              f"{edited_docx.name} was emitted.\n")
        n = _show_diff(base, theirs, "base", f"{edited_docx.name} (as markdown)")
        if accept == "ours":
            print("\n  --accept ours: discarded the Word edits, wrote nothing.")
            return 0
        current_md.write_text(theirs, encoding="utf-8")
        print(f"\n  wrote {current_md} ({n} changed line(s))")
        return 0

    # Both sides moved.
    merged, conflicts = three_way(base, ours, theirs)
    print(f"Both sides changed since {edited_docx.name} was emitted.\n")
    print(f"--- what changed in the Markdown record ({current_md.name}) ---")
    _show_diff(base, ours, "base", str(current_md))
    print(f"\n--- what changed in Word ({edited_docx.name}) ---")
    _show_diff(base, theirs, "base", edited_docx.name)
    print(f"\n{conflicts} conflicting hunk(s).")

    if accept == "theirs":
        current_md.write_text(theirs, encoding="utf-8")
        print(f"  --accept theirs: wrote {current_md}")
        return 0
    if accept == "ours":
        print("  --accept ours: kept the Markdown, discarded the Word edits.")
        return 0
    if accept == "interactive":
        current_md.write_text(merged, encoding="utf-8")
        print(f"  --accept interactive: wrote {current_md} with "
              f"{conflicts} conflict marker block(s). Resolve them by hand.")
        return 0

    print("\nNothing written. Choose with "
          "--accept theirs | ours | interactive.")
    return 1


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Merge an edited DOCX into the record.")
    ap.add_argument("edited", type=Path)
    ap.add_argument("current", type=Path)
    ap.add_argument("--accept", choices=["theirs", "ours", "interactive"],
                    default=None)
    args = ap.parse_args()
    sys.exit(reconcile(args.edited, args.current, args.accept))


if __name__ == "__main__":
    main()
