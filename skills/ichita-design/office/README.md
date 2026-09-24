# Office templates

Generated from the same tokens as the rest of this system, so a document made in Word or
PowerPoint matches one made in HTML.

## `ICHITA-Presentation-Template.pptx`

16:9, 10 × 5.63 in. One slide master carrying seven ICHITA layouts, each with a sample slide
already populated — duplicate the sample or pick the layout from **Home → Layout**:

| Layout | What it is |
|---|---|
| `ICH_COVER` | Blue Grey 03 cover, 6 pt blue top band, keyword emphasis |
| `ICH_AGENDA` | Numbered contents |
| `ICH_DIVIDER` | Blue Grey 01 with a large Betatron section numeral |
| `ICH_CONTENT` | Header band, body area, Off White insight bar |
| `ICH_KPI` | Blue Grey 02 ground, three TH Aeonik Bold figures |
| `ICH_DENSE` | Two-column technical appendix — table left, chart right |
| `ICH_CLOSING` | Dark closing with contact line |

The theme carries the brand: theme fonts **TH Aeonik** (headings and body, Latin and Thai
slots), theme colours Blue Grey 03 / White / Blue Black / Blue Grey 01, then Ichita Blue,
Blue Light, Blue Grey 02 and the three functional colours as accents 1–6. Text typed into a
new box is on-brand without touching it. For a **bilingual deck**, change the theme fonts to
**TH Aeonik Book** (Design → Variants → Fonts) — PowerPoint reaches Book by family, not weight.

KPI and dense layouts use **TH Aeonik Bold** for figures, not Betatron — Betatron appears
only as the divider numeral.

**Thai on a slide needs line spacing set by hand.** PowerPoint ignores the font's line box
and lays every line out at 1.2 em; TH Aeonik's Thai needs 1.536. Set Thai paragraphs to
Multiple **1.3** or more (1.536 ÷ 1.2 = 1.28), 1.46 for the 1.75 em body leading. Measured:
`ichita-skills/docs/THAI-LATIN-FONT-ENGINEERING.md` §7.

## `ICHITA-Report-Template.docx`

A4, **25 mm margins** all round — the document standard in `README.md`. Repeating header
(wordmark over a 0.75 pt Ichita Blue rule, document reference on the right); footer
`ICHITA Technology Co., Ltd. · www.ichita.co.th` with `n / total` bottom-right.

| Style | Spec (space above / below) |
|---|---|
| `Title` | 26 pt Bold, centred, over a 3 pt Ichita Blue rule · 0 / 16 pt |
| `Heading 1` | 15 pt Bold, Blue Grey 03, 3 pt Ichita Blue left bar, 6 pt inset · 34 / 10 pt |
| `Heading 2` | 12 pt Bold, Ichita Blue text step #1A56C4 · 24 / 8 pt |
| `Heading 3` | 10.5 pt Bold Italic, #1A56C4 · 18 / 6 pt |
| `Heading 4` | Kept for old documents; not part of the standard ladder — avoid |
| `Normal` | 10 pt, Blue Grey 03 · 0 / 8 pt |
| `ICHITA Thai Body` | Same as `Normal` — kept so older documents keep their style name |
| `ICHITA Eyebrow` | 8 pt uppercase, tracked 0.12em, Blue Grey 02 text step #4F6472 |
| `ICHITA Caption` | 9 pt #4F6472, under the table · 6 / 8 pt |
| `ICHITA Key Finding` | Off White field, 4 pt Ichita Blue left bar, 10 pt italic · 20 / 20 pt |
| `ICHITA Data Table` (table) | 9 pt · Blue Grey 03 header row, white Bold · banded #F0F4F5 · 0.5 pt #A0B0B8 hairlines · padding 2 / 5.4 pt |

Space follows the rhythm ladder in `design.md` §9.5: the gap between two groups is always
larger than any gap inside one.

**Line spacing.** Body is Multiple **1.14** (`w:line="273"`) — 1.75 em, the Thai body leading,
because Word's Single already is TH Aeonik's 1.536 em box and Multiple *m* gives *m* × 1.536 em.
For an English-only report, set `Normal` to Single (1.536 em — the 1.5 em Latin leading plus
the box's own margin). Never *Exactly* below 1.536 × the point size; it clips the tone marks.

## Thai in Word

Generating a .docx outside these templates? Follow `thai-in-word.md`, then run
`python fix_thai_docx.py file.docx` — it fixes red-underlined Thai and letter-stretched
justified lines. The Report template has already been through it.

## Fonts

**One family, TH Aeonik. The document picks a weight, not a face** (`fonts.md`, settled
10 Aug 2026). In Word and PowerPoint the weight is reached by family name:

| Document | Word / PowerPoint family | Body | Emphasis / headings |
|---|---|---|---|
| English only | **TH Aeonik** | Regular 400 | SemiBold 600 / Bold 700 |
| Thai, or Thai + English | **TH Aeonik Book** | Book 350 | Ctrl+B = Book Bold 650 (SemiBold's ink) |

The Report template ships set in **TH Aeonik Book**, because ICHITA output is usually
bilingual; for an English-only report change the font on `Normal` and the heading styles to
**TH Aeonik** and everything follows. The deck ships in **TH Aeonik** (its sample text is
English). Aeonik is a fallback for machines without TH Aeonik, never a document face.

Both files also name **Betatron**; install every face on each machine that opens the
templates, or Office will substitute. TH Aeonik is 22 faces — ten weights with italics, plus
Book Bold — in one Windows Settings card. Delete every earlier `TH-Aeonik-*` file before
installing: the build number did not change, so Windows cannot tell old from new.
