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
| `th-aeonik/` | TH Aeonik = Aeonik Latin + Bai Thai, **20 faces**, ten weights, one Settings card | **BUILT — install**; delete EVERY installed TH-Aeonik file first |
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

Aeonik, 20 faces: Air 100, Thin 200, Light 300, Book 350, Regular 400, Medium 500,
SemiBold 600, Bold 700, ExtraBold 800, Black 900, plus an italic of each. TH Slussen,
4 faces: Regular, Medium, SemiBold, Bold. Betatron is Regular only.

**TH Aeonik ships 20 faces from 20 outline sets — ten unique weights, one Windows
Settings card.** Every face carries `nameID16 = "TH Aeonik"` with a distinct
`nameID17`, and its own true `usWeightClass`. There are no duplicate outlines: the six
faces that used to exist only to fill a bold slot were replaced by weights somebody
drew (Siwatch, 2026-08-09).

**Its structure is Arial's.** `TH Aeonik` holds Regular + Bold and is the only family
with a real bold; every other weight is a plain face in its own dropdown family,
grouped into one card by `nameID16`. That is how Windows ships Arial (`Arial Black` is
a plain face, not Arial's bold) and Segoe UI (Light, Semilight, Semibold likewise).

| Family in Word | weight | Ctrl+B |
|---|---|---|
| `TH Aeonik Air` | Air 100 | Word synthesises |
| `TH Aeonik Thin` | Thin 200 | Word synthesises |
| `TH Aeonik Light` | Light 300 | Word synthesises |
| `TH Aeonik Book` | Book 350 | Word synthesises |
| `TH Aeonik` | Regular 400 + **Bold 700** | the drawn Bold |
| `TH Aeonik Medium` | Medium 500 | Word synthesises |
| `TH Aeonik SemiBold` | SemiBold 600 | **nothing** |
| `TH Aeonik ExtraBold` | ExtraBold 800 | **nothing** |
| `TH Aeonik Black` | Black 900 | **nothing** |

**Word decides Ctrl+B from `usWeightClass` alone**, measured on Windows 2026-08-09:
below 600 it thickens the outline itself by a constant +23/1000 em; at 600 and above it
refuses and hands back the face unchanged, the same as `Arial Black`. So the ratio a
synthesised bold produces falls as the weight rises — 1.50x at Light, 1.29x at Book,
1.17x at Medium, 1.00x at SemiBold and above. Only `TH Aeonik` reaches a drawn bold, at
1.73x.

**Bold 700 is the only weight not in the dropdown**, because it is the core family's
bold slot — exactly as `Arial Bold` is not in Windows' own dropdown.

**Bold, ExtraBold and Black share one Thai colour.** Bai Jamjuree Bold is the heaviest
Thai available and all three are it, at three embolden amounts; they separate ~2.3% in
the Thai against ~11% in the Latin. Documented cap, accepted explicitly — not a defect.

**Three Latin weights are synthetic.** CoType never drew Book 350, SemiBold 600 or
ExtraBold 800, so `scripts/build_aeonik_semibold.py` derives them. Every other Latin in
this repo is CoType's own bytes, and all six faces say so in `nameID5`. See §4c of
`docs/THAI-LATIN-FONT-ENGINEERING.md` for what that costs.

**Aeonik itself was deliberately left alone**, so bolding `Aeonik Light` in an
English-only document still synthesises while `TH Aeonik Light` gets a real ExtraBold.
Siwatch's call, 2026-08-06 and again 2026-08-09 — the Latin is CoType's and this repo
alters it only for Greek coverage and the three weights above.

**These fonts are INTERNAL.** `NOTICE.txt` and `OFL.txt` ship beside them. They may be
installed and embedded; they may not be handed to anyone outside ICHITA, because OFL
1.1 clause 5 and the Aeonik EULA cannot both be satisfied by one file.

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

- **20** from `aeonik/` — **over** the existing Aeonik. Same family name, so it *is*
  Aeonik to Word; `nameID5` reads `Version 1.001; ICHITA Greek/math coverage`.
- **20** from `th-aeonik/` — **delete every installed TH-Aeonik file first.** Six
  filenames from the previous structure no longer exist (`-AirBold`, `-LightBold`,
  `-BookBold`, `-MediumBold`, `-SemiBoldBold` and their italics), so nothing
  overwrites them and they would sit in the font menu declaring weights that now
  belong to different outlines. Windows Settings should end up showing ONE card
  called TH Aeonik with ten styles in it
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
