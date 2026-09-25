#!/usr/bin/env python3
"""
md_clean — the shared post-processor for every inbound conversion.

One module, not per-route fixes. The bold-heading leak arrives from both the
docx and the html route, and two independent patches for it drift: the first
one to be forgotten stops firing, and nobody notices because the output is
still valid Markdown.

Every rule here corresponds to a defect measured on a real round trip, and
every rule has a test in tests/test_md_clean.py. If you add a rule without a
measurement, you are guessing.

Usage:
    python md_clean.py IN.md OUT.md [--source docx|html|pdf]
    from md_clean import clean
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

# Thai block. U+0E31 and the U+0E34–U+0E3A / U+0E47–U+0E4E ranges are the
# combining marks — the ones that get separated from their consonant.
THAI_ANY = r'\u0E00-\u0E7F'
THAI_MARK = '\u0E31\u0E34\u0E35\u0E36\u0E37\u0E38\u0E39\u0E3A' \
            '\u0E47\u0E48\u0E49\u0E4A\u0E4B\u0E4C\u0E4D\u0E4E'


# ── Rule 1: the bold-heading leak ────────────────────────────────────────────

def strip_heading_emphasis(text):
    """`# **Heading**` -> `# Heading`.

    md_to_docx bolds the runs inside a heading — deliberately, it is how the
    brand's headings look in Word. pandoc has no way to know the bold came from
    the style rather than the author, so it round-trips as literal `**`. Left
    alone this compounds: every extra pass adds another pair.
    """
    return re.sub(
        r'^(#{1,6}[ \t]+)\*\*(.+?)\*\*[ \t]*$',
        r'\1\2',
        text,
        flags=re.MULTILINE,
    )


# ── Rule 2: the ordered list that came back as a blockquote ──────────────────

def restore_ordered_lists(text):
    """A `> **1.** item` block -> a real ordered list.

    md_to_docx draws numbered lists by hand — a blue bold number plus a hanging
    indent — rather than using Word's numbering, because the blue number is the
    brand's. pandoc sees only the indent and reports a blockquote.

    Converts only when EVERY content line of the blockquote is a numbered item,
    so a genuine quotation that happens to start with a number is left alone.
    """
    out, block = [], []

    def flush():
        if not block:
            return
        items = [l for l in block if l.strip() != '>']
        pat = re.compile(r'^>[ \t]*\*\*(\d+)\.\*\*[ \t]+(.*)$')
        matches = [pat.match(l) for l in items]
        if items and all(matches):
            out.extend(f'{m.group(1)}. {m.group(2)}' for m in matches)
        else:
            out.extend(block)
        block.clear()

    for line in text.split('\n'):
        if line.startswith('>'):
            block.append(line)
        else:
            flush()
            out.append(line)
    flush()
    return '\n'.join(out)


# ── Rule 3: the blockquote italic leak ───────────────────────────────────────

def strip_blockquote_emphasis(text):
    """`> *quoted*` -> `> quoted`.

    Same shape as rule 1: the brand sets blockquotes in italic, and the italic
    survives the round trip as markup.
    """
    return re.sub(
        r'^(>[ \t]*)\*(?!\*)(.+?)\*[ \t]*$',
        r'\1\2',
        text,
        flags=re.MULTILINE,
    )


# ── Rule 4: table padding and bold header cells ──────────────────────────────

def _is_table_delimiter(line):
    s = line.strip()
    return bool(s.startswith('|') and re.fullmatch(r'\|[\s:|-]+\|', s))


def _split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def tidy_tables(text):
    """Un-pad pipe tables and drop the bold that the header style leaked in.

    pandoc pads every cell out to the column width. It is deterministic, so it
    round-trips, but it is dead weight in a file whose whole purpose is to be
    cheap to read — a 12-column table pays for the padding on every row.
    """
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        # A table is a row, a delimiter, then rows.
        if (i + 1 < len(lines)
                and lines[i].strip().startswith('|')
                and _is_table_delimiter(lines[i + 1])):
            header = _split_row(lines[i])
            # The header style is bold for every cell; that is the brand, not
            # the author's emphasis. Only strip when the WHOLE cell is bold.
            header = [re.sub(r'^\*\*(.+)\*\*$', r'\1', c) for c in header]
            delim = _split_row(lines[i + 1])
            out.append('| ' + ' | '.join(header) + ' |')
            out.append('|' + '|'.join(
                # Keep any alignment colons, drop the padding dashes.
                ('---' if ':' not in d else d.replace('-', '').replace(':', ':---:')
                 if d.startswith(':') and d.endswith(':')
                 else (':---' if d.startswith(':') else '---:'))
                for d in delim
            ) + '|')
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                out.append('| ' + ' | '.join(_split_row(lines[i])) + ' |')
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return '\n'.join(out)


# ── Rule 5: loose lists ──────────────────────────────────────────────────────

_LIST_ITEM = re.compile(r'^([ \t]*)([-*+]|\d+\.)[ \t]+\S')


def _ordered(marker):
    return marker[:-1].isdigit()


def tighten_lists(text):
    """Normalise the blank lines around list items.

    Two jobs, because they are the same walk:

    - Drop the blank line between adjacent items of the SAME kind. Word has no
      tight/loose distinction so everything comes back loose; the rendering is
      identical and the file is a third shorter.
    - Insert one where the kind CHANGES. A bullet list running straight into
      `1.` with no blank line is one list to a Markdown parser, and the numbers
      come out as literal text.
    """
    lines = text.split('\n')
    out = []
    for idx, line in enumerate(lines):
        nxt = lines[idx + 1] if idx + 1 < len(lines) else None

        if (line.strip() == '' and out and _LIST_ITEM.match(out[-1])
                and nxt is not None and _LIST_ITEM.match(nxt)):
            if _ordered(_LIST_ITEM.match(out[-1]).group(2)) == \
                    _ordered(_LIST_ITEM.match(nxt).group(2)):
                continue

        out.append(line)

        if (_LIST_ITEM.match(line) and nxt is not None and _LIST_ITEM.match(nxt)
                and _ordered(_LIST_ITEM.match(line).group(2))
                != _ordered(_LIST_ITEM.match(nxt).group(2))):
            out.append('')

    return '\n'.join(out)


# ── Rule 6: over-escaping ────────────────────────────────────────────────────

def unescape_spurious(text):
    """Drop backslash escapes pandoc adds where nothing needed escaping.

    Only the characters that are not special outside a table cell, and only
    outside fenced code, where a backslash may be the content.
    """
    out, in_fence = [], False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        s = line
        if not s.strip().startswith('|'):
            s = re.sub(r'\\([|$@%&<>~^"\'])', r'\1', s)
        out.append(s)
    return '\n'.join(out)


# ── Rule 7: Thai integrity ───────────────────────────────────────────────────

def repair_thai_runs(text):
    """Remove a space wedged between a Thai base and its combining mark.

    A combining mark after a space is never correct — it has nothing to attach
    to and renders on a dotted circle. PDF extraction produces these when the
    mark is positioned with its own text-showing operator.
    """
    return re.sub(f'(?<=[{THAI_ANY}])[ \t]+(?=[{THAI_MARK}])', '', text)


def rejoin_split_digits(text):
    """`2 5 6 9` -> `2569`.

    PDF text operators often emit a kerned number one digit at a time. Three or
    more single digits separated by single spaces is not prose in any document
    this company writes.

    Deliberately NOT run on docx or html — there "1 2 3" is a legitimate list of
    numbers, and this rule would silently corrupt it.
    """
    return re.sub(
        r'(?<![\d.,])(\d)(?: (\d)){2,}(?![\d.,])',
        lambda m: m.group(0).replace(' ', ''),
        text,
    )


def assert_thai_intact(before, after):
    """Raise if the Thai characters are not identical after NFC.

    Compares the Thai codepoints only — surrounding markup is expected to
    change, the text is not. Catches the U+0E49 -> U+02D7 class of corruption
    that the May branded PDF showed, which is silent otherwise: the output is
    still valid UTF-8 and still looks like Thai at a glance.
    """
    def thai_only(s):
        s = unicodedata.normalize('NFC', s)
        return ''.join(c for c in s if '\u0E00' <= c <= '\u0E7F')

    a, b = thai_only(before), thai_only(after)
    if a != b:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                ctx_a, ctx_b = a[max(0, i - 12):i + 12], b[max(0, i - 12):i + 12]
                raise ValueError(
                    f"Thai text changed at Thai-char {i}: "
                    f"{x!r} (U+{ord(x):04X}) -> {y!r} (U+{ord(y):04X})\n"
                    f"  before: {ctx_a}\n  after:  {ctx_b}"
                )
        raise ValueError(
            f"Thai text length changed: {len(a)} -> {len(b)} characters"
        )


# ── Rule 8: whitespace ───────────────────────────────────────────────────────

def drop_typesetting_glue(text):
    """No-break hyphen U+2011 -> '-', no-break space -> ' '.

    fix_thai_docx glues number + unit, "Mr Siwatch", "High-Value" so Word cannot break
    them (2026-09-25). That is typesetting, not content: the record keeps what the author
    wrote, and the next build glues it again. pandoc reads <w:noBreakHyphen/> as U+2011.
    """
    return text.replace('\u2011', '-').replace('\u00a0', ' ')


def normalise_blank_lines(text):
    """At most one blank line between blocks, exactly one trailing newline."""
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip('\n') + '\n'


# ── Entry point ──────────────────────────────────────────────────────────────

def clean(text, source='docx', check_thai=True):
    """Run every rule that applies to `source`.

    source: 'docx' | 'html' | 'pdf' — decides only whether the digit-rejoin
    rule runs, which is unsafe anywhere but PDF.
    """
    original = text
    text = unicodedata.normalize('NFC', text)

    text = strip_heading_emphasis(text)
    text = restore_ordered_lists(text)
    text = strip_blockquote_emphasis(text)
    text = tidy_tables(text)
    text = tighten_lists(text)
    text = unescape_spurious(text)
    text = repair_thai_runs(text)
    text = drop_typesetting_glue(text)
    if source == 'pdf':
        text = rejoin_split_digits(text)
    text = normalise_blank_lines(text)

    if check_thai:
        assert_thai_intact(original, text)
    return text


def main():
    ap = argparse.ArgumentParser(description="Clean converted Markdown.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    ap.add_argument("--source", default="docx", choices=["docx", "html", "pdf"])
    ap.add_argument("--no-thai-check", action="store_true")
    args = ap.parse_args()

    raw = args.input.read_text(encoding="utf-8")
    try:
        out = clean(raw, source=args.source, check_thai=not args.no_thai_check)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        args.output.write_text(out, encoding="utf-8")
        saved = len(raw) - len(out)
        print(f"  cleaned {args.input.name} -> {args.output.name} "
              f"({len(out):,} bytes, {saved:,} smaller than raw)")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
