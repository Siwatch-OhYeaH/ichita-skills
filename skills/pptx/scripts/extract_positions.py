"""Extract element positions from unpacked PPTX slides.

Usage:
    python extract_positions.py <unpacked_dir> [slide_numbers...]

Examples:
    python extract_positions.py /tmp/unpack              # All slides
    python extract_positions.py /tmp/unpack 2 3 4        # Specific slides
    python extract_positions.py /tmp/unpack 2-7          # Range

Output: tab-separated table of element positions (inches).
"""
import sys, os, glob
import xml.etree.ElementTree as ET

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}
EMU = 914400  # EMU per inch


def extract_slide(path, slide_num):
    tree = ET.parse(path)
    shapes = tree.findall('.//p:sp', NS)
    rows = []
    for sp in shapes:
        texts = sp.findall('.//a:t', NS)
        text = ' '.join(t.text for t in texts if t.text)[:60] or '(shape)'
        off = sp.find('.//p:spPr/a:xfrm/a:off', NS)
        ext = sp.find('.//p:spPr/a:xfrm/a:ext', NS)
        if off is not None and ext is not None:
            x = int(off.get('x', 0)) / EMU
            y = int(off.get('y', 0)) / EMU
            w = int(ext.get('cx', 0)) / EMU
            h = int(ext.get('cy', 0)) / EMU
            rows.append((slide_num, text, x, y, w, h))
    return rows


def parse_slide_args(args, slide_dir):
    """Parse slide number arguments (e.g., '2', '3', '2-7')."""
    all_slides = sorted(
        int(os.path.basename(f).replace('slide', '').replace('.xml', ''))
        for f in glob.glob(os.path.join(slide_dir, 'slide*.xml'))
    )
    if not args:
        return all_slides

    nums = set()
    for a in args:
        if '-' in a:
            lo, hi = a.split('-', 1)
            nums.update(range(int(lo), int(hi) + 1))
        else:
            nums.add(int(a))
    return sorted(n for n in nums if n in all_slides)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    unpacked = sys.argv[1]
    slide_dir = os.path.join(unpacked, 'ppt', 'slides')
    slide_nums = parse_slide_args(sys.argv[2:], slide_dir)

    print(f"{'Slide'}\t{'Text':<60}\t{'x':>6}\t{'y':>6}\t{'w':>6}\t{'h':>6}")
    print('-' * 110)

    for n in slide_nums:
        path = os.path.join(slide_dir, f'slide{n}.xml')
        if not os.path.exists(path):
            continue
        for slide, text, x, y, w, h in extract_slide(path, n):
            print(f"{slide}\t{text:<60}\t{x:6.2f}\t{y:6.2f}\t{w:6.2f}\t{h:6.2f}")


if __name__ == '__main__':
    main()
