# ichita-convert — document conversion with markdown as the centre

**Status:** COMPLETE 2026-08-06. All phases delivered; see the
"Outcome" section at the end for what was measured and what was left open.
**Owner decision of record:** Siwatch, 2026-08-06.

---

## Context

Font engineering is finished. The next job is the apply layer: moving content between the
four formats ICHITA actually uses — Word, Markdown, PDF, HTML — without losing brand
integrity or burning context.

Today the repo can only go **outbound**, and only from two sources: `md_to_docx.py`,
`html_to_docx.py`, `html2pdf.py`, `rebrand_docx.py`. Every inbound leg is missing. There is
no way to get a client RFP, a returned hand-edited DOCX, or a supplier PDF back into a form
Claude can read cheaply. That gap is why a 40-page DOCX currently costs a fortune to work
with: without conversion, the OOXML lands in context.

### The workflow this serves

```
inbound   docx ┐
          html ├──►  MARKDOWN  ──►  the record, in git
          pdf  ┘     (truth)
                          │
outbound                  ├──► docx   internal work
                          ├──► html   Claude-designed layouts
                          └──► pdf    what leaves the building
```

Markdown is the source of truth. A human may hand-edit the emitted DOCX — text and images,
the template is already there — and may Print-to-PDF and deliver straight from Word. To get
those edits back into the record they have to be converted to markdown. When the two
disagree, **show the difference and let the human decide** — Word's accept/reject model, not
a silent overwrite.

---

## Findings that shape the design

Measured 2026-08-06 unless marked otherwise.

**1. Word's Save-as-PDF cannot embed CFF.** Microsoft policy, not a bug — Office refuses
OpenType-CFF, so our `.otf` fonts silently become Calibri while the file still lists
embedded fonts. (`docs/THAI-LATIN-FONT-ENGINEERING.md:339`)
→ *Save-as-PDF is banned for delivery.* Microsoft **Print to PDF** is a different path — a
print driver that bypasses Office's embedding subsystem, and the one the font work
hardened (§9 of the font doc). This rule applies to any presentation deliverable.

**2. Thai extracted from the May branded PDF is corrupted** — `น˗˓าตาล` for `น้ำตาล`, marks
arriving as U+02D7 / U+02D3.
→ Current fonts map U+0E49 → `uni0E49` cleanly, so the likely cause is the glyph naming in
the old build. **Unverified — measure first.** Gates the whole inbound PDF leg.

**3. Every page of our PDFs carries 1 raster image** (the logo, same xref repeated) **and
26–77 vector paths.** Charts, KPI cards and rules are all vector.
→ A `get_images()`-based extractor recovers the logo and not a single chart. Figure
extraction must cluster `get_drawings()` and crop-render.

**4. pandoc `docx→gfm` round-trips structure well but leaks `# **Heading**`** (md_to_docx
bolds heading runs), grid-pads tables, over-escapes `|`, wraps at 72 cols.
→ A **shared** post-processor is required, not per-route hacks — two routes compound the
bold leak.

**5. pandoc has `--track-changes=accept|reject|all` and `--extract-media`.**
→ pandoc is the docx→md engine — the only one that can tell us what a human changed in Word.

**6. `check_ab_test_pdf.check_no_substitution()` and `measured_pitch()`, and
`check_print_pdf.audit()`, already implement most PDF acceptance checks.**
→ The delivery bake-off harness is ~80% written.

**7. Both existing briefs declare `font-family: 'AeonikTH', 'Sarabun', sans-serif`** — a
family name that no longer exists, falling back to a non-brand font.
→ Those briefs render off-brand today. Fix by extracting one shared brand stylesheet.

**8. Font directories were renamed uncommitted** (`aeonik-th`→`th-aeonik`,
`slussen-th`→`th-slussen`, `aeonik-woff`→`aeonik-web`); 80 files showed deleted.
`qc_th_fonts.py`, `build_greek_specimen.py`, `check_print_pdf.py` and the READMEs pointed at
dead paths. `assets/fonts/aeonik/` now holds the fixed build.
→ The QC suite could not run. **Phase 0.**

### Out of scope

Scanned PDFs / OCR — born-digital only.

**Do not delegate extraction to other models.** For born-digital PDFs pymupdf reads the
exact character stream; a model would paraphrase, drop table cells and re-type numbers. The
hard part is deterministic code; captioning a correctly-cropped chart is the easy half.

---

## Phase 0 — Reconcile the font-directory rename (prerequisite) — **DONE**

Not conversion work, but it blocked QC and the paths.

- [x] `git add -A assets/fonts` so the rename is recorded (77 files, tracked as renames)
- [x] Fix the dead paths in `scripts/qc_th_fonts.py`, `build_greek_specimen.py`,
      `check_print_pdf.py`, `assets/fonts/README.md`, `assets/brand/ichita-defaults.md`,
      `docs/THAI-LATIN-FONT-ENGINEERING.md` — 26 files, 60 references
- [x] `build_th_aeonik.AEONIK_LOCAL` no longer points at `assets/fonts/aeonik/`, so
      `build_aeonik.py` cannot read its own output as its input. The pristine v1.000
      source is **kept out of the repo** (Siwatch, 2026-08-06) — one Aeonik directory,
      no coin-flip over which to install. `require_aeonik_source()` stops both builders
      up front if it is missing rather than falling back
- [x] `install-fonts.sh` prunes the git-ignored `aeonik-v1000/` drop point — it flattens
      by basename, and the pristine faces share both filenames and family name with the
      shipping build
- [x] **Gate:** `qc_th_fonts.py` → 19/20, check 6 red on purpose.
      `thai_line_pitch.py --check` → OK, both families spare +75
- [x] Recorded in §13 of the font doc, not a new post-mortem (per CLAUDE.md)

Known leftover, **not** font work: the asset table in `assets/brand/ichita-defaults.md`
(lines 87–91, 531–541) points at `assets/ichita/...`, a layout that does not exist, and
names several files that do not exist. Fix in Phase 1 while extracting `ichita.css`.

---

## Phase 1 — The spine

New skill. One command, small surface.

```
skills/ichita-convert/
  SKILL.md              # target <500 words: the matrix, the two hard rules, pointers
  reference/
    inbound.md          # docx/html/pdf → md, figure extraction
    outbound.md         # md → html/docx/pdf
    reconcile.md        # three-way merge, provenance
    pdf-delivery.md     # Print-to-PDF vs Save-as-PDF, the bake-off numbers
  scripts/
    convert.py          # single entry point, dispatch on the extension pair
    md_clean.py         # shared post-processor
  requirements.txt
  install.sh
```

`python scripts/convert.py IN OUT [options]` — the extension pair selects the route;
anything not a direct leg chains through markdown.

| from ↓ / to → | md | docx | html | pdf |
|---|---|---|---|---|
| **md** | — | `md_to_docx.py` (exists) | new | chain md→html→weasyprint |
| **docx** | new (pandoc) | `rebrand_docx.py` (exists) | chain | bake-off, Phase 4 |
| **html** | new | `html_to_docx.py` (exists) | — | `html2pdf.py` (exists) |
| **pdf** | new (pymupdf) | chain | chain | — |

Genuinely new: four converters, figure extraction, reconcile. Everything else is wiring
around code that already works.

**Where the token saving comes from**, in priority order:

1. The conversion itself — OOXML and PDF bytes never land in context.
2. One command shape instead of six scripts, so `SKILL.md` stays small.
3. Progressive disclosure — `reference/*.md` read only when the route needs them.
4. `convert.py` prints a before/after size estimate on inbound, so the saving is visible.

**Also Phase 1:** extract `assets/brand/ichita.css` — brand tokens, correct `@font-face`
family names, print rules — from the two bespoke briefs. It becomes the single source of
truth so `ichita-exe-brief` and hand-designed HTML import it instead of re-declaring fonts.
Fixes finding 7.

---

## Phase 2 — Inbound

**`ingest_docx.py`** — `pandoc -f docx -t gfm --wrap=none --extract-media`, then
`md_clean.py`. Expose `--track-changes` (default `all` for reconcile, `accept` otherwise).

**`ingest_html.py`** — markdownify, then `md_clean.py`. Must handle arbitrary hand-designed
markup — layout divs, inline styles, grid — not just our own templates.

**`ingest_pdf.py`** — pymupdf text extraction + `pdf_figures.py`. **Gate before anything
else in this phase:** regenerate a Thai PDF with current fonts, extract, and assert the text
is byte-identical to source after NFC normalisation. If finding 2 reproduces, root-cause it
before building on top.

**`pdf_figures.py`** — the part with no prior art here:

1. `get_images(full=True)`, dedupe by xref; drop any xref present on ≥80% of pages as brand
   furniture (the logo).
2. `get_drawings()`, cluster by bbox proximity; drop full-width sub-6pt rects
   (rules/accents) and clusters under an area threshold.
3. Render each survivor: `page.get_pixmap(clip=rect, dpi=200)` → PNG in `media/`.
4. Emit `![](media/p1-fig1.png)` inline at the right point. **Captioning is a separate
   opt-in pass, never automatic** — it costs tokens.

**`md_clean.py`** — every item measured today, each with a test: strip the `# **Heading**`
bold leak; grid tables → pipe tables; un-escape spurious pipes; rejoin digit-split artefacts
(`2 5 6 9` → `2569`); assert Thai combining marks survive an NFC round-trip and that no
space is inserted inside Thai runs.

---

## Phase 3 — Outbound

**`emit_html.py`** — markdown → branded HTML against `assets/brand/ichita.css`. This is also
the route to md→PDF: chain into the existing `html2pdf.py`.

Wire `md_to_docx.py` in **unchanged**. It already selects the face from the document's
language via `select_fonts_for_source()` — **do not touch that path**; per the font doc the
English-only paragraphs in a mixed document lead ~28% wider and that is the accepted cost.

---

## Phase 4 — PDF delivery bake-off

Three engines, measured, on one fixture: Thai + Latin, a table, a figure, tone marks over
ascenders.

1. **LibreOffice headless** — `soffice --headless --convert-to pdf`. Scriptable; embeds CFF
   as Type1C, so it may be the only engine that gets our fonts into a PDF at all. It
   re-lays out the document, and the claim that it agrees with Word is a **construction
   argument, not a measurement**.
2. **Microsoft Print to PDF via Word COM from WSL.** Word's own layout — what humans use.
   Windows-only, needs Word, and can orphan `WINWORD.EXE` and lock the fonts — run the §9
   pre-check first.
3. **md→html→weasyprint** — full brand control, reuses `html2pdf.py`, discards Word layout.

Acceptance per engine, reusing what exists:

| Check | Where |
|---|---|
| No Calibri substitution | `check_ab_test_pdf.check_no_substitution()` |
| Which build actually embedded, `/W` sanity | `check_print_pdf.audit()` |
| Line pitch measured from the PDF | `check_ab_test_pdf.measured_pitch()` |
| Thai text byte-identical after NFC | new, ~20 lines |
| Page/line count vs the Word reference | new |
| Look at the rendered PNG | `pdftoppm`, by eye |

Record the numbers in `reference/pdf-delivery.md`; font findings go to §13 of the font doc.
Word's Save-as-PDF is measured **once**, to document the failure.

---

## Phase 5 — Reconcile

**`reconcile.py`** — provenance sidecar plus three-way merge.

Sidecar (`.ichita-convert.json`, a few hundred bytes): md path and sha256, emitted docx path
and sha256, timestamp, tool version, font mode. **Provenance only, deliberately.** A
formatting-delta sidecar would have to model DOCX styling in a second schema kept in step
with both the markdown and the branded emitter, and when it drifts you get a
confidently-wrong restore.

`convert.py reconcile edited.docx current.md`:

- ingest the DOCX with `--track-changes=all`
- look up the base markdown we emitted from
- base unchanged → fast-forward
- both moved → print both diffs, name the conflicting hunks, **write nothing** without
  `--accept theirs|ours|interactive`
- no sidecar → say so and fall back to a two-way diff, labelled as less reliable

---

## Phase 6 — Fixtures and colleague documentation

Fixture corpus in `skills/ichita-convert/tests/fixtures/`: a Thai-mixed document, a
table-heavy doc, a figure-heavy PDF, a Claude-designed HTML page. Round-trip test asserting
md → docx → md is stable **and idempotent on the second pass** — that is exactly the class
of bug that only shows on pass two.

`README.md` + `SKILL.md` carry the two rules colleagues will otherwise get wrong:

- **Print to PDF, never Save as PDF.** Save-as-PDF silently substitutes the fonts and the
  file still looks fine.
- **Hand your file back if you want the change kept.** Markdown is the record; a DOCX edited
  and left on someone's desktop is not.

---

## Verification

```bash
# Phase 0 gate
python3 scripts/qc_th_fonts.py                    # 19/20, check 6 red on purpose
python3 scripts/thai_line_pitch.py --check        # both families spare +75

# Inbound gate — must pass before Phase 2 continues
python3 scripts/convert.py fixtures/thai-mixed.pdf /tmp/out.md
#   → extracted Thai byte-identical to source after NFC normalisation

# Round trip, twice — catches the compounding bold leak
python3 scripts/convert.py fixtures/mixed.md /tmp/a.docx
python3 scripts/convert.py /tmp/a.docx           /tmp/b.md
python3 scripts/convert.py /tmp/b.md             /tmp/c.docx
python3 scripts/convert.py /tmp/c.docx           /tmp/d.md
diff /tmp/b.md /tmp/d.md                          # must be empty

# Delivery bake-off
python3 scripts/check_print_pdf.py   /tmp/deliver-<engine>.pdf
python3 scripts/check_ab_test_pdf.py /tmp/deliver-<engine>.pdf
pdftoppm -jpeg -r 150 /tmp/deliver-<engine>.pdf /tmp/pg    # and look at it

# Reconcile
python3 scripts/convert.py reconcile fixtures/edited.docx fixtures/base.md
#   → expect a diff, no write
```

**Every phase ends by looking at the artifact, not by a green test** — because CLAUDE.md
says so, and because the font work produced four separate defects that passed their tests.

---

## Sequencing

Phase 0 first (unblocks QC) — **done**. Then 1 → 2 → 3 as the usable core. Phase 4 can run
in parallel with 2–3 once a Thai fixture DOCX exists. Phase 5 depends on 1–3. This is a
measured project — each phase gates on a measurement, and the Phase 2 Thai gate may send us
back to the fonts.

---

## Outcome — 2026-08-06

All six phases delivered. `skills/ichita-convert/` exists with one entry point,
16 end-to-end tests and 27 unit tests, all green.

### Gates

| Gate | Result |
|---|---|
| Phase 0 — `qc_th_fonts.py` | 19/20, check 6 red on purpose |
| Phase 0 — `thai_line_pitch.py --check` | OK, both families spare +75 |
| **Phase 2 — Thai byte-identical through PDF** | **PASS, 311/311 after NFC** |
| Round trip, twice — `b.md == d.md` | identical |
| md → PDF embeds only brand fonts | PASS |

### Findings that changed the design

- **Finding 2 does not reproduce.** The May PDF's Thai corruption was the old
  build's glyph naming. The current build round-trips Thai exactly. This gate
  could have sent the whole project back to the fonts; it did not.
- **Four defects were in `md_to_docx.py`, not in the conversion.** Soft-wrapped
  source lines became separate Word paragraphs; bullets used a PUA codepoint in
  `Symbol`, which LibreOffice substituted and embedded as OpenSymbol. Both
  fixed at the source. Bold headings, italic blockquotes and hand-drawn
  numbered lists are brand choices, so those are undone in `md_clean` instead.
- **weasyprint's Thai text layer is wrong while the render is right** — every
  `า` extracts as `ำ`. This decides the delivery engine: LibreOffice for Thai.
  §13 of the font doc has the mechanism and the falsified fix.
- **Word COM hangs unattended from WSL** and orphans `WINWORD.EXE`. Measured
  twice, cleaned up both times, and now skipped by the bake-off with the reason
  attached.
- **The reconcile sidecar carries the merge base**, a gzipped snapshot of the
  Markdown. The plan said provenance only; without the base there is no
  three-way merge, and a snapshot cannot drift the way a formatting model
  would. Documented in `reference/reconcile.md`.

### Left open, deliberately

1. **`assets/brand/ichita-defaults.md` asset table is stale** — lines 87–91 and
   531–541 point at `assets/ichita/…`, a layout that does not exist, and name
   several files that exist nowhere. The font row was corrected; the rest needs
   someone who knows which assets were intended.
2. **The two existing briefs in `skills/ichita-exe-brief/output/` still declare
   `AeonikTH`** and render off-brand. `assets/brand/ichita.css` is the
   replacement, but rebuilding those two documents against it is its own job.
3. **Inline emphasis is not recovered from PDF** — see the limitations section
   of `reference/inbound.md`.
4. **Word Print-to-PDF is unmeasured.** Needs an attended run.
