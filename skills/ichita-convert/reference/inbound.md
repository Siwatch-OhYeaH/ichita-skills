# Inbound — getting a document into the record

Everything here produces Markdown, then runs it through `md_clean.py`. The
cleaner is shared on purpose: the bold-heading leak arrives from both the DOCX
and the HTML route, and two independent patches for one defect drift until the
forgotten one stops firing.

Measured on 2026-08-06 against `tests/fixtures/mixed.md` unless stated.

---

## Why convert at all

| Source | Size | As Markdown | Ratio |
|---|---|---|---|
| Branded DOCX, 2 pages | 49,397 B | 2,437 B | 20× |
| Same document as PDF | 128,796 B | 2,421 B | 53× |
| Hand-designed HTML brief | 4,520 B | 1,264 B | 4× |

That is the whole argument for this skill. Without it the OOXML or the PDF
byte stream lands in context and a 40-page proposal costs a fortune to work
with. `convert.py` prints the ratio on every inbound conversion so the saving
is visible rather than assumed.

---

## docx → md

`pandoc -f docx -t gfm --wrap=none --extract-media`, then `md_clean`.

pandoc is the engine for one reason nothing else offers: `--track-changes`
reads Word's revision marks.

```bash
--track-changes accept   # default — the document as the editor meant it to read
--track-changes reject   # as it was before they touched it
--track-changes all      # every insertion and deletion inline; reconcile uses this
```

### What the round trip does to a branded DOCX

Five defects, all measured, all now handled by `md_clean`:

| Defect | Cause | Rule |
|---|---|---|
| `# **Heading**` | the brand bolds heading runs; pandoc cannot tell style from emphasis | `strip_heading_emphasis` |
| Numbered list arrives as `> **1.** item` | the brand draws numbers by hand in blue; pandoc sees only the indent | `restore_ordered_lists` |
| `> *quote*` | the brand sets blockquotes in italic | `strip_blockquote_emphasis` |
| Table cells padded to column width, header bold | pandoc's grid alignment plus the header style | `tidy_tables` |
| Every list loose | Word has no tight/loose distinction | `tighten_lists` |

Each compounds. A single round trip looks fine and the second adds another
layer, which is why `test_roundtrip.py` converts twice.

### One defect that was fixed at the source instead

`md_to_docx.py` emitted **one Word paragraph per source line**, so a Markdown
file wrapped at 90 columns became a DOCX with paragraph breaks mid-sentence,
and Word would not reflow across them. That is a bug in the document, not in
the conversion, so it was fixed in the emitter (`_starts_block`) rather than
papered over here. 33 paragraphs → 26 on the test fixture.

---

## html → md

`markdownify`, after a preprocessing pass that turns brand card markup into
prose. This leg has to survive markup nobody here wrote — a client's Word
export, or a Claude-designed brief where the content lives in class names
rather than in headings.

What the preprocessor does:

- drops `style`, `script`, `svg`, `title`, and the page chrome
  (`.print-btn`, `.footer`, `.logo-block`)
- `.stat-card` → `**2569** m³/day — Installed capacity`, built as real
  `<strong>` nodes; a string containing `**` comes out as `\*\*2569\*\*`
  because markdownify escapes literal asterisks
- `.section-header` (number chip + title) → one `##`
- `.info-box-title`, `.cap-title`, `.init-title` → `###`
- `.header-title` → `#`
- inline `data:` images → `*[image: alt]*`. The ICHITA logo alone is ~40 KB of
  base64 repeated on every page of a brief.

---

## pdf → md

`pymupdf`. **Born-digital only** — a scanned page has no character stream, and
the extractor says so rather than guessing.

> Do not delegate this to a model. pymupdf returns the exact codepoints the
> producer wrote. A model paraphrases, drops table cells and re-types numbers,
> and every one of those is invisible in the result.

There are no headings, paragraphs or lists in a PDF — only glyphs at
coordinates. Everything is inference, and each rule keys on something stated:

| Inference | Keys on |
|---|---|
| heading level | line size ÷ modal body size: ≥1.55 → h1, ≥1.28 → h2, ≥1.12 → h3, bold and ≥1.04 → h4 |
| paragraph break | vertical gap > 1.75 × size, an x-indent shift > 6 pt, or the previous line ending short of the column |
| running header/footer | within 9% of a page edge AND repeated on ≥60% of pages |
| table | `page.find_tables()`; its region is then removed from the text flow |
| list item | line starts with a bullet character, including **U+F0B7**, the PUA bullet Word emits for a Symbol-font marker |

### Two traps worth knowing

**A bullet sorts after its own text.** pymupdf reports the marker and the words
as separate objects, and the marker's box often starts a couple of points
lower. Sorting by y alone put every bullet on its own line with the text
orphaned above it. Lines are grouped into visual rows by vertical overlap
first, then ordered by x.

**Thai must not be joined with a space.** Thai does not space its words, so a
wrapped Thai line joined with `" "` puts one inside a word — `ใช้ พลังงาน` for
`ใช้พลังงาน`. `_join()` checks both sides and concatenates directly when both
are Thai.

### The Thai gate

Before anything else in this leg was built, the question was whether Thai
survives a PDF at all — the May 2026 branded PDF extracts `น˗˓าตาล` for
`น้ำตาล`, with tone marks arriving as U+02D7 and U+02D3.

**It does not reproduce with the current fonts.** A Thai DOCX rendered through
LibreOffice and extracted returns **311 of 311 Thai characters, identical
after NFC**. The old build's glyph naming was the cause, as suspected; the
current build maps `U+0E49 → uni0E49` cleanly.

`md_clean.assert_thai_intact()` runs on every inbound conversion so a
regression fails loudly instead of shipping.

---

## Figures

`pdf_figures.py`. The measured fact that shapes it:

> Every page of an ICHITA PDF carries **1 raster image** — the logo, the same
> xref repeated — and **26–77 vector paths**. Charts, KPI cards and rules are
> all vector.

A `get_images()`-based extractor therefore recovers the logo and not one
chart. The algorithm:

1. `get_images(full=True)`, and drop any xref appearing on ≥80% of pages as
   brand furniture.
2. `get_drawings()`, dropping full-width rects under 6 pt tall (accent rules,
   table borders) and anything thinner than 2 pt.
3. Cluster what remains by bbox proximity within 9 pt — a chart arrives as
   dozens of separate path objects.
4. Keep clusters ≥24×24 pt and ≥2400 pt², render each with
   `page.get_pixmap(clip=…, dpi=200)`.
5. Emit `![](name-media/p1-fig1.png)` at the point in the text where it sits.

**Captioning is a separate opt-in pass, never automatic.** It costs tokens and
most figures do not need one.

---

## Known limitations

- **Inline emphasis is not recovered from PDF.** Bold and italic exist in the
  span data, but most PDFs bold whole table cells and headers, so inferring
  `**` from it adds more noise than meaning. Headings are recovered; run-in
  emphasis is not.
- **Multi-column PDF layouts are not detected.** Fragments more than 3 × the
  font size apart on one baseline stay separate, which stops two columns being
  welded together, but the reading order across columns is still top-to-bottom.
- **`rejoin_split_digits` runs on PDF sources only.** In a DOCX or HTML,
  `1 2 3` is a legitimate list of numbers and the rule would corrupt it.
