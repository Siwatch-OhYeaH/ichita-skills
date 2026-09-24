# TH Aeonik — font analysis and setup

Final build, **22 faces**, pulled 10 Aug 2026 (build of 2026-08-09). Supersedes the 8-face
2026-08-05 set. Everything below is **measured on these exact files** — OpenType tables read
directly, and rendering measured in Chrome at 200 px. Nothing here is inherited from the
previous record.

Source of the binaries: local `fonts/th-aeonik/`. Installed here as `assets/fonts/TH-Aeonik-*.otf`
(all 22). Declared for use in `tokens/fonts.css`.

---

## 1. The setup

**One family, TH Aeonik, for every document.** What a document chooses is its default
*weight*, not its face.

| Document | Default | Emphasis | Headings | HTML | Word / PowerPoint family |
|---|---|---|---|---|---|
| English only | **Regular 400** | SemiBold 600 | Bold 700 | `data-typeset="en"` | **TH Aeonik** |
| Thai, or Thai + English | **Book 350** | SemiBold 600 | SemiBold 600 | `data-typeset="mixed"` | **TH Aeonik Book** |

```html
<body data-typeset="en">     <!-- Regular 400 -->
<body data-typeset="mixed">  <!-- Book 350 -->
```

`tokens/base.css` rebinds `--weight-body`, `--weight-strong` and `--weight-heading` from that
one attribute; `body`, `h1–h6`, `strong` and `b` already read those tokens, so nothing else
in a document needs to change.

**Why Book for bilingual.** Thai sets about 10% more ink per line than the Latin beside it,
and its bold is capped (§4). Book removes ~11% of the ink from the Latin — measured, not
estimated — so the two scripts hold one page grey instead of the Thai reading as a dark band.
The trade is real and small: Book's Latin is 0.58% narrower than Regular's, and it is an
ICHITA interpolation rather than a CoType drawing.

**Why SemiBold for emphasis.** In a bilingual file, Bold 700 separates 11% in the Latin but
only ~2% in the Thai, so a bolded Thai phrase barely reads as emphasis while the Latin shouts.
SemiBold 600 is also exactly what Word hands back when you press Ctrl+B inside *TH Aeonik
Book*: its "Book Bold" (usWeightClass 650) carries the **same outlines and the same advances
as SemiBold** — measured identical, glyph for glyph. So Word and the web agree without anyone
choosing anything.

**Headings in a bilingual file are SemiBold, not Bold. [EXTENSION]** This is the one judgement
call in the setup rather than a measurement: at 700 the Thai stem is 0.87 of the Latin against
0.89 at 600, and the Thai stops separating. A document that wants Bold headings overrides
`--weight-heading` locally.

**Declared vs held.** `tokens/fonts.css` declares 300, 350, 400, 500, 600, 700, 800, 900
(+ italics through 700). **Air 100 and Thin 200 are installed as assets and deliberately not
declared** — backdrop, footage and poster work has no rule set yet, and an undeclared weight
cannot be reached by accident. Book Bold 650 is not declared either: it is the same outlines
as 600.

---

## 2. Reliability

Everything in this section is a check that either passes or does not.

| Check | Result |
|---|---|
| All 22 faces parse and load as OTF/CFF | **Pass** |
| Vertical metrics agree — `hhea` = `sTypo` = `usWin` = 1169 / −368 / 0 | **Pass**, all 22 |
| `USE_TYPO_METRICS` (fsSelection bit 7) set | **Pass**, all 22 |
| Line box identical across all ten weights (1.536) | **Pass** — changing weight never reflows a paragraph |
| Thai combining marks carry zero advance | **Pass** — tone marks, sara-i, two-mark stacks all 0 |
| `GDEF` present; `GPOS` `mark` + `mkmk` registered under script `thai` | **Pass**, all 22 |
| `GSUB` `ccmp` / `locl` under script `thai` | **Pass**, all 22 |
| Thai coverage | **87 codepoints in all 22** — parity with Bai Jamjuree |
| Δ μ Ω Σ ⌀ coverage | **Pass**, all 22 — parity with Aeonik |
| `tnum` present | **Pass**, all 22 |
| Latin identical to CoType Aeonik | **Pass** on the drawn weights — a Latin string sets to 13.5070 em in both TH Aeonik Regular and Aeonik Regular, a 0.000% difference |
| `fsType` embedding | **0 — installable, unrestricted.** DOCX / PPTX / PDF embedding is safe |
| Italic angle | −10° on all eleven italics |

### Known limits — accepted, not defects

1. **Thai colour is capped above 700.** Bold, ExtraBold and Black all take Bai Jamjuree Bold
   at three embolden amounts. Measured Thai/Latin stem ratio: 0.909 (Light), 0.875 (Book),
   0.882 (Regular), 0.870 (Medium), 0.889 (SemiBold), 0.867 (Bold), 0.848 (ExtraBold),
   **0.757 (Black)**. Across 700 → 900 the Thai separates 2.3% while the Latin separates 11%.
   **800 and 900 are Latin display weights.** Do not set a Thai line in them beside Latin and
   expect a match.
2. **Three Latin weights are ICHITA interpolations** — Book 350, SemiBold 600, ExtraBold 800.
   CoType never drew them. Each says so in its own `nameID5`. They are dimensionally consistent
   (advances and x-heights interpolate monotonically) but they are not CoType's drawing.
3. **Book Bold 650 duplicates SemiBold 600.** By design — it fills Word's bold slot for the
   Book family. Never serve both on the web.
4. **Aeonik Light declares `usWeightClass` 250; TH Aeonik Light declares 300.** Match the two
   families by *name*, never by number.
5. **Betatron is `fsType` 4** — preview & print embedding only. An editable PPTX/DOCX that
   embeds it opens read-only on a machine without the font. Irrelevant for PDF export, which is
   how Betatron covers ship.
6. **File weight.** Each face is 200–242 KB of OTF. A page that uses four faces pulls ~850 KB.
   The WOFF2 cut exists but is **held** — OFL clause 5 and the Aeonik EULA cannot both be
   satisfied by one redistributable file.
7. **macOS is unverified.** No Mac has been measured. The argument that CoreText lands on the
   declared box (because `hhea`, `sTypo` and `usWin` all carry it) is construction, not
   measurement.
8. **The Thai italics are unverified as drawings.** All eleven carry −10°; whether the Thai is
   drawn or obliqued has not been checked. Use italics sparingly in Thai regardless — it is not
   a native Thai convention.

---

## 3. Spacing requirements

### Leading — where the ink actually collides

Ink extents measured on canvas at 200 px, worst-case Thai stack `ปั๊ญฐฎ`:

| Weight | Ascent | Descent | Ink touches at |
|---|---|---|---|
| Light 300 | 1.015 | 0.245 | **1.260** |
| Book 350 | 1.035 | 0.250 | **1.285** |
| Regular 400 | 1.055 | 0.260 | **1.315** |
| Medium 500 | 1.060 | 0.260 | **1.320** |
| Bold 700 | 1.090 | 0.255 | **1.345** |
| Black 900 | 1.095 | 0.255 | **1.350** |
| Latin only `Hpjgy` | 0.705–0.740 | 0.205–0.215 | **0.910–0.945** |
| Mixed line, Thai + Latin + figures | 1.035–1.095 | 0.215–0.240 | **1.260–1.330** |

So:

| Content | Hard floor | Use | Token |
|---|---|---|---|
| Thai body, running text | 1.40 | **1.75** | `--leading-thai` |
| Thai heading, 2+ lines | 1.40 | **1.55** | `--leading-thai-tight` |
| Mixed heading / caption | 1.40 | 1.55 | `--leading-thai-tight` |
| Latin body | 1.05 | 1.50 | `--leading-normal` |
| Latin display, single line | 1.05 | 1.08 | `--leading-tight` |

`--leading-thai-floor: 1.40` is new: it is the lowest value with air still in it. **1.35 is
where marks begin to touch descenders** — visible, not theoretical.

**The declared line box is 1.536 and does not change with weight.** Two consequences:

- **Word:** Single already gives the declared 1.536 box — Multiple *m* is *m* × 1.536 em, so
  the 1.75 em Thai body is Multiple 1.14. **PowerPoint** ignores the font and lays out at 1.2 em:
  Thai there needs Multiple 1.3 or more (1.536 ÷ 1.2 = 1.28). *Exactly* below 1.536 × the size
  clips the tone marks in both. Measured: `ichita-skills/docs/THAI-LATIN-FONT-ENGINEERING.md` §7.
- **Web:** never inherit `line-height: normal`. It resolves to **1.536** where TH Aeonik is
  installed and **1.200** where it falls back to Aeonik — a 28% difference in block height from
  the same stylesheet. Always set a `--leading-*` token.

### Tracking

| Use | Value | Token |
|---|---|---|
| Headings, Latin | −0.02em | `--tracking-tight` |
| Body | 0 | `--tracking-normal` |
| Figures — KPIs, table cells, measurements | **−0.035em**, Bold, `tabular-nums` | `--tracking-figure` / `.ich-figure` |
| Eyebrows and labels, uppercase | 0.14em | `--tracking-label` |
| **Any Thai run** | **0** | enforced by `:lang(th)` in `tokens/base.css` |

Thai has no inter-word spaces, so letter-spacing separates *words*, not letters. Mark
attachment survives it in Chrome — legibility does not. `tokens/base.css` now zeroes tracking
on `:lang(th)`, `.ich-th` and `.th`, which also overrides the `h1–h6` −0.02em default inside a
Thai heading.

### Figures

`tnum` holds a digit at **~0.600 em in every weight** (measured 0.594–0.606 across 100–900), so
a figure column keeps its width when the weight changes. Proportional figures do not: a "1" is
0.268 em at Air and 0.393 em at Black. Any number the reader reads or compares takes
`.ich-figure`. Betatron stays the chapter numeral and nothing else — its digits are monospaced
by design (0.644 em, no `tnum` needed).

### Size

Thai and Latin sit at the **same font-size** — inside TH Aeonik the Thai is already matched to
the Latin x-height (measured x-height 504–516/1000 across the range, cap 700–706). The
`--doc-thai-scale: 0.9` step applies **only** in split mode, where Thai is set in Bai Jamjuree
beside Aeonik.

---

## 4. The ten weights, measured

Advance of `H` in units/1000, x-height and cap-height from `OS/2`, Thai/Latin stem ratio from
rendered stems, and the width of a fixed Latin string in em.

| Face | usWeight | `H` | x-h | cap | Thai/Latin stem | Latin string (em) | Role |
|---|---|---|---|---|---|---|---|
| Air | 100 | 636 | 504 | 700 | — | 12.851 | asset only |
| Thin | 200 | 643 | 505 | 700 | 0.90 | 12.977 | asset only |
| Light | 300 | 657 | 507 | 700 | 0.909 | 13.231 | captions |
| **Book** | **350** | 668 | 510 | 705 | 0.875 | 13.429 | **bilingual body** |
| **Regular** | **400** | 672 | 510 | 700 | 0.882 | 13.507 | **English body** |
| Medium | 500 | 683 | 512 | 700 | 0.870 | 13.791 | labels, UI |
| SemiBold | 600 | 690 | 512 | 701 | 0.889 | 13.933 | emphasis, bilingual headings |
| *Book Bold* | *650* | *690* | *512* | *701* | *0.889* | *13.933* | *= SemiBold; Word's bold slot for Book* |
| Bold | 700 | 697 | 514 | 700 | 0.867 | 14.144 | English headings, figures |
| ExtraBold | 800 | 704 | 516 | 706 | 0.848 | 14.346 | display only |
| Black | 900 | 711 | 516 | 700 | 0.757 | 14.490 | display only |

Advances, x-heights and string widths increase monotonically with weight — the ladder is
dimensionally sound. Only the Thai stem ratio breaks, and only at 800 and 900.

---

## 5. Issues found — full audit of the 22 files

Audited 10 Aug 2026: name records, style-linking flags, PANOSE, vertical bounds against the
declared box, glyph coverage (Thai block, Latin-1, Latin Ext-A, Greek, punctuation, spaces),
duplicate-outline detection by `hmtx` signature and `CFF` length, and per-glyph ink extents.

### Blocking — none

Nothing in the build stops it being used. Everything below is a limit to design around.

### A. Coverage gaps

1. **No NBSP.** U+00A0 is absent from all 22 faces — and from Aeonik too. Also absent: thin
   space U+2009, figure space U+2007, narrow NBSP U+202F, zero-width space U+200B, soft hyphen
   U+00AD, non-breaking hyphen U+2011, word joiner U+2060. A `&nbsp;` therefore renders from a
   **fallback font**, so that one word space is a different width. Common in exactly the copy
   ICHITA writes: "20 mm", "Fig. 1", "±0.5 %". **Use a normal space inside `.ich-nowrap`.**
   *(U+2212 true minus IS present.)*
2. **Greek is five characters: Δ Σ Ω μ π.** α β γ λ σ ω and the rest of the block are missing.
   Anything like α-amylase, β-glucan, Δp, λ falls back to a system font mid-word. This is the
   one gap worth asking the foundry pipeline to close in the next build.
3. **No Vietnamese** (2 of 90 precomposed forms). Latin-1 94/96, Latin Ext-A 126/128 — Western
   and Central European are fine.
4. **Thai is complete**: 87/87 codepoints in all 22 faces, including ฿ ๆ ฯ ๏ ๚ ๛ and the Thai
   digits ๐–๙.

### B. Structure

5. **SemiBold 600 and Book Bold 650 are the same font.** Identical `hmtx` signature, identical
   `CFF` length (181 666 bytes), identical bounds — likewise SemiBold Italic and Book Bold
   Italic. Intentional (Book Bold fills Word's bold slot for the Book family) but never serve
   or install-count them as two weights.
6. **Every face reads `Version 1.000; build 2026-08-10`.** The version is *not* bumped relative
   to earlier builds, and — contrary to `NOTICE.txt` — the three interpolated Latin weights
   (Book, SemiBold, ExtraBold) do **not** declare that in `nameID5`. Consequence: Windows cannot
   tell this build from the previous one. **Delete every installed TH-Aeonik file before
   installing**, and check `%LOCALAPPDATA%\Microsoft\Windows\Fonts` as well as
   `C:\Windows\Fonts` — the per-user layer shadows the system one.
7. **Style linking is correct.** `TH Aeonik` carries Regular + a real Bold (fsSelection and
   macStyle bold bits both set); `TH Aeonik Book` carries Book + Book Bold; every other weight
   is a plain face in its own `nameID1` family, grouped under `nameID16 = "TH Aeonik"`. All 22
   PostScript names are unique. All eleven italics set the italic bit in both tables.
8. **PANOSE does not distinguish Book from Regular** — both 2.1.**5**.3.3.3. A PDF viewer or
   Office substituting by PANOSE rather than by name will treat Book as Regular. Cosmetic here,
   because we always name the face.

### C. Vertical

9. **The declared box has 0.038 em of slack, not much.** Deepest rendered ink across all 87 Thai
   glyphs plus the Latin is **0.330 em** below the baseline (the sara-u vowel) against a declared
   `usWinDescent` of 0.368 em; the tallest is 1.106 em against 1.169. Nothing clips today. But
   the `head` bounding box goes to −0.473 em, so **do not tighten `usWinDescent` and do not
   assume a stacked below-vowel plus a deep base will always fit** — re-measure if the Thai is
   ever redrawn.
10. **Line box 1.536 vs Aeonik's 1.200.** Any layout that inherits `line-height: normal` grows
    28% when it lands on TH Aeonik. Tokens exist for exactly this reason.

### D. Behaviour to design around

11. **Thai colour stops following the Latin above 700** (§2, limit 1) — the single biggest
    typographic constraint in the family.
12. **PowerPoint bilingual decks need the family switched, not the weight.** Book is reached in
    Office as the family *TH Aeonik Book*, so a bilingual deck must set the theme's major/minor
    font to it — changing the weight inside a "TH Aeonik" placeholder cannot get there.
13. **`font-weight: 350` is non-standard.** Browsers handle it; some PDF/PPTX conversion paths
    round it to 400, and any exporter that thinks in "regular/bold" will lose the distinction.
    Check bilingual exports at least once before shipping a template that relies on Book.
14. **`font-synthesis: none` is now set on `body`.** A face that fails to load shows as the wrong
    weight instead of a faked bold — visible, and therefore fixable.
15. **Each face is 200–242 KB and there is no WOFF2.** Four faces on a page is ~850 KB. The
    merged web cut exists but stays held: OFL clause 5 and the Aeonik EULA cannot both be
    satisfied by one redistributable file.
16. **macOS remains unmeasured**, and whether the Thai italics are drawn or mechanically
    obliqued has not been checked.

## 6. What changed in the system

- `tokens/fonts.css` — 22 faces installed, 13 declared (was 8). Aeonik demoted to fallback.
  Build notes rewritten against measurements from these files.
- `tokens/typography.css` — full weight-token set (`--weight-book` … `--weight-black`),
  `--weight-body` / `--weight-strong` / `--weight-heading`, `--leading-thai-floor: 1.40`,
  `--tracking-figure: −0.035em`. `--font-latin` is now an alias of `--font-sans`.
- `tokens/base.css` — `font-synthesis:none`, `.ich-nowrap`, `[data-typeset="en"|"mixed"]`, `strong`/`b` on `--weight-strong`,
  headings on `--weight-heading`, tracking zeroed on Thai, `tabular-nums` on `table`,
  `.ich-figure`.
- `guidelines/` — **Font setup**, **Weight ladder** and **Metrics & leading floors** cards
  rewritten or added.
- `README.md`, `design.md` — face-selection rule replaced by the weight-selection rule.

**Not changed, on purpose:** the slide and document type scales, the Betatron rule, split mode,
and Bai Jamjuree's role. Nothing in the palette or layout system is affected.
