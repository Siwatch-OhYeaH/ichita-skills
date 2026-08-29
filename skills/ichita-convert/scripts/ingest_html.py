#!/usr/bin/env python3
"""
html -> markdown.

This one has to survive markup we did not write. A client's RFP is a Word
export full of `<o:p>` and nested tables; a Claude-designed brief is a grid of
absolutely-positioned divs with the content in `<div class="stat-num">`. Neither
is a document tree in any useful sense, so the job is to strip the chrome down
to the reading order and let md_clean tidy what is left.

Usage:
    python ingest_html.py IN.html OUT.md [--keep-images]
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_clean import clean  # noqa: E402

# Elements that never carry reading content. `style` and `script` are obvious;
# the others are page furniture that repeats on every page of a branded brief
# and would otherwise appear a dozen times in the markdown.
DROP_TAGS = ["style", "script", "noscript", "svg", "iframe", "template",
             "title", "meta", "link"]
DROP_CLASSES = ["print-btn", "no-print", "footer", "header-meta", "logo-block"]


def _preprocess(soup):
    """Turn brand-specific card markup into headings and paragraphs.

    A `.stat-card` is a number, a unit and a label. Left alone, markdownify
    emits three bare lines with no relationship between them. Rendering it as
    `**2569** m³/day — Design flow` keeps the meaning in one line.
    """
    for tag in soup.find_all(DROP_TAGS):
        tag.decompose()

    for cls in DROP_CLASSES:
        for tag in soup.find_all(class_=cls):
            tag.decompose()

    # Stat cards -> a single emphasised line.
    #
    # Built as real <strong>/text nodes, not as a string containing `**`.
    # markdownify escapes literal asterisks in text, so the shortcut emits
    # `\*\*2569\*\*` — the number arrives in the record wearing backslashes.
    for card in soup.find_all(class_="stat-card"):
        num = card.find(class_="stat-num")
        unit = card.find(class_="stat-unit")
        label = card.find(class_="stat-label")

        p = soup.new_tag("p")
        if num:
            strong = soup.new_tag("strong")
            strong.string = num.get_text(strip=True)
            p.append(strong)
        if unit:
            p.append(" " + unit.get_text(strip=True))
        if label:
            p.append(" — " + label.get_text(strip=True))
        card.replace_with(p)

    # Section headers: the number chip plus the title are one heading.
    for hdr in soup.find_all(class_="section-header"):
        num = hdr.find(class_="section-num")
        title = hdr.find(class_="section-title")
        if title:
            h = soup.new_tag("h2")
            prefix = f"{num.get_text(strip=True)}. " if num else ""
            h.string = prefix + title.get_text(strip=True)
            hdr.replace_with(h)

    # Card titles are headings, not bold paragraphs.
    for cls, level in (("info-box-title", "h3"), ("cap-title", "h3"),
                       ("init-title", "h3"), ("vision-label", "h3")):
        for tag in soup.find_all(class_=cls):
            tag.name = level

    # The page title of a branded brief lives in .header-title.
    for tag in soup.find_all(class_="header-title"):
        tag.name = "h1"

    return soup


def html_to_md(src, dst, keep_images=True, quiet=False):
    try:
        from bs4 import BeautifulSoup
        from markdownify import markdownify
    except ImportError:
        print("ERROR: needs beautifulsoup4 and markdownify. See requirements.txt.",
              file=sys.stderr)
        sys.exit(1)

    src, dst = Path(src), Path(dst)
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")
    soup = _preprocess(soup)

    text = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
        strip=None if keep_images else ["img"],
    )

    # markdownify leaves a blank line for every stripped div; collapse before
    # md_clean so its blank-line rule is not fighting a wall of them.
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Base64 images inline are the single biggest cost in a branded brief —
    # the ICHITA logo alone is ~40 KB of data: URI repeated on every page.
    n_inline = len(re.findall(r'!\[[^\]]*\]\(data:', text))
    if n_inline:
        text = re.sub(r'!\[([^\]]*)\]\(data:[^)]*\)', r'*[image: \1]*', text)

    text = clean(text, source="html")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

    if not quiet:
        before, after = src.stat().st_size, dst.stat().st_size
        print(f"  {src.name} -> {dst.name}  "
              f"{before:,} B -> {after:,} B  ({before / max(after, 1):.0f}x smaller)")
        if n_inline:
            print(f"  replaced {n_inline} inline data: image(s) with a placeholder")
    return text


def main():
    ap = argparse.ArgumentParser(description="HTML -> Markdown.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--keep-images", action="store_true", default=True)
    args = ap.parse_args()
    html_to_md(args.input, args.output, args.keep_images)


if __name__ == "__main__":
    main()
