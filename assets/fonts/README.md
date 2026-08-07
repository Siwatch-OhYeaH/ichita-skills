# ICHITA Brand Fonts

**Which face to use is decided by the document's language** — Siwatch, 2026-08-05:

| Document | Face | Line box |
|---|---|---|
| English only | **Aeonik** (`aeonik/`) | 1200 |
| Thai, or Thai + English mixed | **TH Aeonik** (`th-aeonik/`) | 1537 |

Never mix the two in one document; they have different line boxes, so the text reflows
at the boundary. The generators pick automatically from the source text and log the
choice. Rationale in `assets/brand/ichita-defaults.md` §4.

**Before changing anything in this directory, read
[`docs/THAI-LATIN-FONT-ENGINEERING.md`](../../docs/THAI-LATIN-FONT-ENGINEERING.md).**
It is the complete record: what the metrics mean, why each build step exists, which
renderer reads which field, and roughly thirty defects not to repeat.

---

## What is in here

| Directory | Contents | Status |
|---|---|---|
| `aeonik/` | Aeonik v1.001 = v1.000 + Greek/math, 14 faces + a **synthetic** SemiBold pair | **BUILT — install this. It is the only Aeonik here.** |
| `th-aeonik/` | TH Aeonik = Aeonik Latin + Bai Thai, **20 faces** from 16 outline sets | **BUILT — install**; uninstall `TH Aeonik Black` and `TH Aeonik Thin` first |
| `slussen/` | Slussen desktop, 4 faces | pristine source; incomplete (a 10-face set exists in an old `D:` build) |
| `th-slussen/` | TH Slussen = Slussen + Bai Thai, 4 faces | **BUILT — install**; no documented brand role yet |
| `aeonik-web/` | Aeonik v2.000 web cut, 6 faces | source for the Greek harvest **only** — box 1140, respaced digits, do not migrate to |
| `th-aeonik-web/` | TH Aeonik WOFF2 + WOFF + CSS, 8 faces | **BUILT AND HELD — do not serve**, licence unresolved |
| `bai-jamjuree/` | Bai Jamjuree, 12 faces (OFL) | Thai source for the merges; also the split-mode Thai font |
| `betatron/` | Betatron Regular | display numerals only — never body text |

### The Aeonik source is not in this repo

`assets/fonts/aeonik/` is our **v1.001** build — `nameID5` reads
`Version 1.001; ICHITA Greek/math coverage`. CoType's pristine **v1.000**, which
is what `build_aeonik.py` and `build_th_aeonik.py` read, is kept locally and
archived by Siwatch rather than committed. Two directories both called Aeonik,
with identical filenames and the same family name, is a coin-flip over which
one someone installs — and the wrong one has no Δ μ Ω.

To rebuild, put the 14 original faces in either:

```
/mnt/d/Doccument/New Identity/Aeonik-font-download/Aeonik-font-download/
assets/fonts/aeonik-v1000/          # git-ignored
```

The builders check for it up front and stop with that message if it is missing.
**They will not fall back to `aeonik/`** — that would run this pipeline over
its own output.

Generated directories are rebuilt by `scripts/build_aeonik.py`, `build_th_aeonik.py`,
`build_th_slussen.py` and `build_th_web.py`. All merged output is **`.otf`/CFF**
deliberately: a merged font must ship its Latin source's outline format or Windows
renders the Latin 16–20% lighter through a different rasteriser.

### Weights

Aeonik, 14 faces: Air, Thin, Light, Regular, Medium, Bold, Black, plus an italic of
each. TH Slussen, 4 faces: Regular, Medium, SemiBold, Bold. Betatron is Regular only.

**TH Aeonik ships 20 faces from those same 14 outline sets**, and its family structure
diverged from Aeonik's on 2026-08-06. Every family now holds a real bold, because the
alternative is Word synthesising one — a double-strike, which spends the counter
aperture that keeps ฃ ธ ฮ open at text sizes.

| Family in Word | Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|
| `TH Aeonik Air` | Air | Air Italic | Thin | Thin Italic |
| `TH Aeonik Light` | Light | Light Italic | *Medium* | *Medium Italic* |
| `TH Aeonik` | Regular | Italic | Bold | Bold Italic |
| `TH Aeonik Medium` | Medium | Medium Italic | Black | Black Italic |
| `TH Aeonik SemiBold` | SemiBold | SemiBold Italic | *Black* | *Black Italic* |

*Italics in that table are the same outlines shipped a second time under a bold name.*

`TH Aeonik Black` and `TH Aeonik Thin` no longer exist. Their outlines ship as
Medium's and Air's bold — `TH-Aeonik-MediumBold.otf` and `TH-Aeonik-AirBold.otf`.
Black's Thai is identical to Bold's (both pinned to Bai's counter floor at 134.8);
in the Latin it is 24% heavier, which is why it still ships.

**SemiBold's Latin is synthetic.** CoType never drew an Aeonik SemiBold, so
`scripts/build_aeonik_semibold.py` derives one from Medium. Every other Latin in
this repo is CoType's own bytes. Both faces say so in `nameID5`. See §4c of
`docs/THAI-LATIN-FONT-ENGINEERING.md` for what that costs.

**Aeonik itself was deliberately left alone**, so bolding `Aeonik Light` in an
English-only document still synthesises while `TH Aeonik Light` gets a real Medium.
Siwatch's call, 2026-08-06 — the Latin is CoType's and this repo alters it only for
Greek coverage.

Bai Jamjuree ships 12 faces but only the ones named in
`scripts/th_thai_prep.BUILD_TABLE` are used — **pairing is by measured stem, not by
weight name**. Matching Bai Regular to Aeonik Regular once left Thai 25% lighter than
the Latin beside it.

---

## Installing

### Windows — the one that matters

**Uninstall the obsolete faces first**, then install. **Close Word, PowerPoint AND
Excel before either step**: a locked file is what produced `TH-Aeonik-Regular_0.ttf` and
left a stale file registered under the family name, so measurements ran against the
wrong file for a day.

Install through **Windows Settings → Personalisation → Fonts**. Do **not** run
`scripts/fix-th-fonts.sh --apply-system --restart`; `--check` is a fine read-only
report.

`%LOCALAPPDATA%\Microsoft\Windows\Fonts` (per-user) **shadows** `C:\Windows\Fonts`
(system), so a stale per-user copy silently wins. Check both layers.

Word caches font data per session; a full restart is required, not just reopening the
document.

What to install:

- **16** from `aeonik/` — **over** the existing Aeonik. Same family name, so it *is*
  Aeonik to Word; `nameID5` reads `Version 1.001; ICHITA Greek/math coverage`.
- **20** from `th-aeonik/` — remove any installed `TH Aeonik Black` and
  `TH Aeonik Thin` first, or the retired families stay in the dropdown alongside
  their replacements
- 4 from `th-slussen/`
- `bai-jamjuree/` and `betatron/` if not already present

### Linux — for the QC suites only

```bash
mkdir -p ~/.local/share/fonts/th-current
cp assets/fonts/th-aeonik/TH-Aeonik-*.otf \
   assets/fonts/th-slussen/TH-Slussen-*.otf ~/.local/share/fonts/th-current/
cp assets/fonts/bai-jamjuree/*.ttf assets/fonts/betatron/*.otf ~/.local/share/fonts/
fc-cache -f
```

Install into `th-current/` and **rebuild before running QC** — a stale copy here feeds
the document QC and has produced false passes.

### macOS — **UNVERIFIED**

```bash
cp assets/fonts/{aeonik,th-aeonik,th-slussen}/*.otf ~/Library/Fonts/
cp assets/fonts/bai-jamjuree/*.ttf assets/fonts/betatron/*.otf ~/Library/Fonts/
```

Nothing on macOS has been measured — there is no Mac. The position that CoreText lands
on the declared box because `hhea`, `sTypo` and `usWin` all carry it is a **construction
argument, not a measurement**. The acceptance test to run is in
`docs/archive/2026-08-05-completion-and-cross-platform-acceptance.md`.

---

## Coverage

Both Aeonik and TH Aeonik carry **Δ μ Ω Σ ⌀** across all 14 faces, added 2026-08-05.
Coverage parity between the two is a requirement, not a nicety: a character present in
one and absent in the other falls back to a system font depending only on whether the
document happens to contain Thai.

`Σ` → `∑` and `⌀` → `Ø` are aliases and **genuine shape compromises** — `∑` is drawn for
maths and sits wider than a Greek sigma; `Ø` is a letter where `⌀` is a symbol. Revisit
only if a real document reads wrong.

`∆` U+2206 and `µ` U+00B5 carry the web cut's redrawn outline in the harvested faces,
because a Greek letter and its maths twin must share one outline.

Specimen sheets are not committed — regenerate with
`python3 scripts/build_greek_specimen.py` (→ `test-output/greek-aeonik-*.png`).

## Usage in brand

Per `assets/brand/ichita-defaults.md`:

- **Headings** Aeonik Bold / Medium — **Body** Aeonik Regular — **Captions** Aeonik Light
- **Display numerals** Betatron Regular. **Never** for body text, labels or sentences.
- **Thai** comes from TH Aeonik in a mixed document, or Bai Jamjuree at 0.9× in split
  mode. Thai is sized to the Latin **x-height** and weight-matched by measured stem at
  ~0.89 of the Latin, with **Aeonik as the benchmark, not Bai**.
