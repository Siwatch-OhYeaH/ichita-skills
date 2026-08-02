# TH-Aeonik — five merge defects, root causes, and what the debugging taught us

**Date:** 2026-08-01
**Scope:** `scripts/build_th_aeonik.py`, `scripts/compare_th_aeonik.py`, `assets/fonts/aeonik-th/*.otf` (6 weights)
**Status:** all five fixed and validated. The customer-visible failure (Word → Print to PDF) is confirmed as defect 3, proven from a real artifact.

---

## Summary

TH-Aeonik merges Aeonik (Latin, CFF/OTF) with Bai Jamjuree (Thai, TrueType) into one family, so internal documents use a single font and export to PDF cleanly.

The shipped merge had five defects. One of them made every printed PDF unreadable. Another silently replaced Aeonik's entire Latin typography with Bai Jamjuree's and had gone unnoticed indefinitely — it produced no error, no missing glyph, and no bug report.

All five are fixed in `build_th_aeonik.py`. A new acceptance test, `compare_th_aeonik.py`, asserts the property that actually matters — **the merge must be invisible** — across 6 weights × 13 sizes.

| # | Defect | Blast radius |
|---|---|---|
| 3 | Thai CFF charstring widths off by `nominalWidthX` | **Every printed PDF unreadable** |
| 1 | Aeonik's Latin GSUB/GPOS discarded | All Latin kerning + ligatures wrong, everywhere, silently |
| 2 | 29/57 Coverage tables out of glyph-ID order | Thai shaping unreliable on Windows (Uniscribe/DirectWrite) |
| 4 | Three disagreeing vertical-metric sets | Line spacing differs ~2× between browsers and Word |
| 5 | Thai codepoints in the single-byte Mac cmap | Spec violation; no observed symptom |

---

## Defect 3 — the one that broke printed documents

### Symptom

Thai in `TRR Sritep Resin Test Report - REV01.docx` (1432 `TH Aeonik` runs) printed via **Microsoft Print to PDF** came out unreadable: glyphs flung apart (`ร า ย ง า น`), tone marks and vowels detached from their consonants, and adjacent runs colliding — `Acrylic และ Styrene` overprinting itself. Copy-paste returned shredded, interleaved fragments. **Word on screen was correct. Export as PDF was correct.**

### Root cause

```python
pen = T2CharStringPen(bai_glyph.width, bai_glyph_set)
bai_glyph.draw(pen)
charstring = pen.getCharString()
charstring.private = top_dict.Private     # nominalWidthX = 578
```

`T2CharStringPen` encodes the width operand assuming `nominalWidthX == 0`. Attaching Aeonik's Private DICT afterwards means the rasteriser decodes `nominalWidthX + operand`. 578 *is* Aeonik Regular's `nominalWidthX`.

Latin `A` encodes operand 80 (= 658 − 578, correct). Thai `uni0E01` encodes 602 — its absolute width, uncompensated — decoding as 1180 against `hmtx`'s 602. All 363 Thai glyphs affected.

### Why it produced that symptom

Microsoft Print to PDF builds the PDF `/W` advance-width array from the **CFF charstring widths, not from `hmtx`**. Measured directly in the customer's `printpdf.pdf`:

| Font | Glyph | PDF `/W` | Embedded `hmtx` | Delta |
|---|---|---|---|---|
| `CIDFont+F2` (TH Aeonik Regular) | `uni0E01` ก | 1180 | 602 | +578 |
| `CIDFont+F2` | `uni0E48` ่ | 578 | **0** | +578 |
| `CIDFont+F3` (TH Aeonik Bold) | `uni0E01` ก | 1242 | 636 | +606 |

64 of 123 `/W` entries wrong in Regular, 49 of 98 in Bold — each off by exactly that weight's `nominalWidthX`. Latin entries agree exactly, which is why `Acrylic` and `Styrene` survived intact.

**The combining marks are what made it unreadable.** All 13 Thai marks in `/W` — `uni0E31`, `uni0E34`–`uni0E39`, `uni0E47`–`uni0E49`, `uni0E4C`, `uni0E4D` — were declared 578 wide against a true advance of **0**. Thai marks stack above and below the base consonant and must consume no horizontal space. Giving each 0.578 em of advance detaches every mark from its consonant, spreads the line, and makes each run overrun into the next. That single fact explains both symptoms at once: the visual collision *and* the shredded copy-paste (extractors compute glyph boxes from `/W`).

Word renders correctly because Word lays out from `hmtx`. The two tables only diverge at PDF-production time — which is why this was invisible on screen, in browsers, and in export.

Embedded font sizes in the artifact (188,424 / 188,916 bytes) match the pre-fix OTFs exactly, confirming it predates the fix.

Two secondary observations, neither ours: Print to PDF declares `/Subtype /CIDFontType2` + `/FontFile2` (TrueType) while embedding an `OTTO`/CFF program — poppler's 32 `Mismatch between font type and embedded font file` warnings — and emits untagged PDF (`Tagged: no`), so there's no logical reading order to fall back on.

### Fix

`T2CharStringPen(bai_glyph.width - priv.nominalWidthX, ...)` — pre-compensate the operand.

---

## Defect 1 — Aeonik's Latin typography was thrown away

```python
aeonik_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
aeonik_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
```

Assignment, not merge. Aeonik's 44 GSUB and 6 GPOS lookups were discarded and replaced by Bai Jamjuree's 20 and 10. Latin glyphs stayed Aeonik's; every kerning pair, ligature and contextual alternate applied to them became Bai Jamjuree's.

Measured against Aeonik: `Ta` 475 vs 521, `To` 475 vs 501, `Ya` 527 vs 553, `Wo` 956 vs 947, plus `r`/`f`/`o`/`s` throughout. `fl` formed a ligature Aeonik deliberately lacks; `ffi` lost Aeonik's `f.calt` contextual alternate. 10 of 11 test strings differed.

**Fix — `_union_ot(base_table, add_table, take_scripts)`.** Aeonik's table becomes the base; Bai's lookups are appended with nested `SubstLookupRecord`/`PosLookupRecord` indices shifted by the offset; features are remapped; only the `thai` script is adopted, so `latn` and `DFLT` stay Aeonik's. This is safe because Thai glyphs are *appended* after Aeonik's, so Aeonik's own glyph IDs never move and its tables remain valid verbatim.

---

## Defect 2 — Coverage tables out of glyph-ID order

Both sources have zero unsorted Coverage tables. All six merged fonts had 29 of 57.

GSUB/GPOS are copied wholesale from Bai Jamjuree, where each `Coverage.glyphs` list is sorted against *Bai's* glyph IDs. Re-parented onto Aeonik's glyph order they are no longer ascending. fontTools serialises `.glyphs` verbatim; nothing re-sorts it. The spec requires ascending order because consumers **binary-search** Coverage — HarfBuzz tolerates violations, Uniscribe and DirectWrite do not.

| Subtable | Field | Count |
|---|---|---|
| `MarkBasePos` | `MarkCoverage`, `BaseCoverage` | 6 |
| `MarkMarkPos` | `Mark1Coverage`, `Mark2Coverage` | 8 |
| `PairPos` | `Coverage` | 5 |
| `ChainContextSubst` | `Backtrack`/`Input`/`LookAhead` | 10 |

21 of the 29 are **index-parallel** — the Coverage index selects an entry in a sibling array (`MarkArray`, `BaseArray`, `PairSet`). A wrong index binds a Thai mark to the wrong anchor. `MarkBasePos`/`MarkMarkPos` are precisely the tables that stack Thai above-vowels and tone marks, including two-level stacks like `น` + `ื` + `่`.

**The build script claimed to fix this and did not:**

```python
def ttx_roundtrip(font_path):
    f = TTFont(str(font_path)); f.saveXML(ttx_path)
    f2 = TTFont(); f2.importXML(ttx_path); f2.save(str(font_path))
    print(f"     [6] TTX roundtrip: coverage tables sorted")
```

A TTX round trip preserves list order verbatim. It sorted nothing and printed a success line asserting it had.

**Fix — `sort_coverage(font)`** restores ascending order and permutes each index-parallel sibling array with the same permutation. Pure-set coverages are sorted alone.

---

## Defects 4 and 5

**4 — three disagreeing vertical-metric sets.** sTypo 700/−200/300 (1.20 em) was inherited unchanged from Aeonik while `hhea` and `usWin` were overwritten to 1550/−561 (2.11 em). Browsers honour sTypo; Word and most PDF engines honour `hhea`/`usWin`. Same file, near-double line spacing depending on consumer. sTypo's 700 ascent also sits below Thai's real ink top of 987, so tone marks collided with the line above.
*Fix:* `hhea` and sTypo both 1000/−300/0, `USE_TYPO_METRICS` set. Thai ink runs +987/−364, Latin +898/−206.

**4b — the clipping box was set from the wrong measurement (found later, see below).** The same fix set `usWin` to 1050/400 under a comment reading `# must clear ink, never clipped`. It did not. `usWinAscent`/`usWinDescent` bound what GDI will draw, and they were sized against *cmap-reachable* Thai ink (+987/−364) when the font's actual ink runs to **+1225/−561**. The overflow is Bai Jamjuree's small tone-mark variants — `uni0E48.small`, `uni0E49.small`, `uni0E4C.small` — which exist precisely for two-level stacks and are reachable **only through GSUB, never through cmap**, so every measurement taken over the cmap missed them. Shaping `น้ำเชื่อม` puts `uni0E48.small` at +1136 and `ฟั้น` puts `uni0E49.small` at +1168 in Bold: 86 and 118 units of tone mark cut off, on all six weights.
*Fix:* `usWin` 1250/570, clearing raw ink with headroom. Line spacing is unaffected — `USE_TYPO_METRICS` is on, so spacing still comes from sTypo.
*Caught by:* porting the TH-Slussen clipping guard back to Aeonik. Nothing in the original test could see it — shaping and raster comparisons both pass on a font whose clipping box is too small, because neither FreeType nor HarfBuzz applies `usWin*`.

**5 — Macintosh cmap held codepoints above 255.** The `(1,0)` subtable is single-byte; the merge wrote raw Thai codepoints up to `U+0E5B`, 87 per font.
*Fix:* `fix_mac_cmap(font)` drops codes > 255.

---

## Why all this slipped through

**No test asserted the property that mattered.** Step 7 verified *presence* — Thai cmap count, Latin coverage percentage, GPOS lookup count, OS/2 bits, metric values. Every one passed on a font with all five defects. Nothing compared the *output* against the two source fonts, which is the only check that could have caught defect 1 at all.

**One step logged a success it never performed.** The build log was active evidence *against* investigating Coverage.

**Defects 1 and 3 are invisible to inspection.** Latin kept the right glyphs and merely spaced them wrong. Thai advances read correctly from `hmtx` while the CFF disagreed. Both required mechanical comparison against a reference to surface.

**The italics differ from the uprights in a way nothing documented.** Aeonik's italics ship a stub `thai` script record; the uprights do not. Two successive fix attempts were broken by that asymmetry.

---

## Learnings

Four of the wrong turns produced *confident, plausible, wrong* intermediate states. That is the pattern worth internalising: none of these felt like mistakes at the time.

### What worked

**Treat the build log as a claim, not evidence.** `coverage tables sorted` was false. Only reading the binary established truth. Any log line asserting success that isn't computed from a check is decoration.

**Treat the source comment as a claim too.** `# must clear ink, never clipped` sat on the line that set 1050/400, which cleared neither. The same pattern turned up again in `build_th_slussen.py`, where `# nameID1 must be unique for Windows font picker` sat directly above code setting it non-uniquely. Both comments correctly stated the invariant; neither was ever checked against the value beside it. A comment asserting a property is a test that was never written — either write it, or expect the code to drift away from it.

**Measure over the reachable set, not the convenient one.** The clipping box was sized from Thai ink measured over the cmap. The glyphs that overflowed it were GSUB-only variants, invisible to any cmap-based measurement, and they were the tallest glyphs in the font. When a font is merged, "which glyphs can actually appear" is answered by shaping, not by the character map.

**Borrow an unrelated tool as an oracle.** Running `fontTools.subset` over the font — as a stand-in for what a PDF producer does — emitted `Coverage is not sorted by glyph ids` ~60 times. The manual audit had no such check and never would have. Cheap way to find unknown-unknowns: run a foreign tool over your artifact and read its warnings.

**Isolate one variable before believing a fix.** The single most load-bearing result of the session: build a coverage-sort-only variant with metrics and widths untouched, render, pixel-diff against the original → **identical**. HarfBuzz tolerates unsorted order, so a *correct* permutation must not change its output; any difference would have meant the parallel-array reordering had broken mark attachment. Bundling the metrics change in would have masked that signal completely.

**Compare mechanically against the references, at many sizes, on every weight.** Defect 1 had no symptom and no report — nothing but comparison would have found it. Uprights passed 11/11 while italics failed 11/11; testing only `Regular` would have shipped broken italics twice.

**Verify a guard fails before trusting that it passes.** `check_cff_widths()` was run against the pre-fix fonts and confirmed to fail (363 bad glyphs, 68 broken marks) before being accepted as a regression test. A guard never observed failing proves nothing.

**Ask for the artifact.** A whole session of failing to reproduce the print bug synthetically was settled in minutes by one `printpdf.pdf`. When a symptom lives in an environment you cannot run, stop simulating and request the output.

### What didn't

**LibreOffice as a stand-in for the Windows GDI/XPS print path.** Its print and export outputs were byte-identical — no signal at all. Worse than useless: it briefly suggested nothing was wrong.

**Ranking a plausible mechanism instead of measuring.** With no repro, defect 2 was named the likely cause of the print failure on the strength of a genuinely good story — it *is* the textbook HarfBuzz-vs-Uniscribe divergence. The artifact showed the cause was defect 3. Both were real and both are fixed, so the outcome held, but a well-argued mechanism is still a guess. Rank candidates only to decide what to measure next; never let the ranking stand in for the measurement.

**Reading the symptom report too literally.** "View as image, not copy-paste text" was investigated as a text-extraction problem. The rendering was *also* broken, which reframed the diagnosis entirely. Rendering the page and simply looking at it should have preceded any analysis of the text layer.

**First `_union_ot`: skip the script if it already exists.** Rested on "Aeonik has no Thai" — true for uprights, false for italics. The guard silently discarded Bai's entire Thai feature set on all three italic weights. Caught by the test, not by reading the code.

**Second `_union_ot`: append features alongside the existing ones.** Produced two `mark` features in one LangSys. A LangSys must not list a tag twice; consumers take the first, so Aeonik's empty stub won and Thai mark positioning stayed dead. The fix clones and merges same-tag features into a fresh `FeatureRecord` rather than mutating the shared one, which would have leaked Thai lookups into `latn`.

**Setting the test's bar wrong.** The first acceptance test demanded pixel-exact Thai across a TrueType→CFF format change: 3008 failures, nearly all noise, burying the two real signals. A test that cannot distinguish a defect from a format change is not a test. Corrected bar: dimensions, advances and positions exact; edge antialiasing bounded.

**Assuming a residual difference is a defect.** 479 Thai mismatches after the union were entirely the shared `space` glyph — correctly Aeonik's 262 rather than Bai's 260. Confirmed non-regression by measuring the pre-fix build at the same sizes: 52/117 both before and after.

**One disproved hypothesis worth recording:** the Thai raster deviation was assumed to be coordinate rounding. `roundTolerance=0` made it *worse* (6.9% vs 6.5% of pixels). It is CFF-vs-TrueType scan conversion, and is not fixable without keeping the font TrueType.

---

## Validation

`scripts/compare_th_aeonik.py`, 6 weights × 13 sizes (8–144 px) — **PASS**:

- 6 CFF-width audits (charstring widths vs `hmtx`)
- 588 Coverage-order checks *(added after the TH-Slussen work — the original test had none)*
- 6 clipping-box audits (`usWin*` vs ink) *(added likewise; this is what caught defect 4b)*
- 2730 shaping comparisons (HarfBuzz glyph sequence + positions)
- 8112 raster comparisons (FreeType bitmaps, unhinted)
- Thai shapes and measures exactly as Bai Jamjuree
- Latin is **pixel-exact** to Aeonik — 215/215 glyph rasters, hinted and unhinted
- Mixed Thai/Latin: no `.notdef` at any size
- All five defects re-checked clean on all six weights

Two documented, intentional non-identities: `space` comes from Aeonik (262) not Bai (260), which is correct for mixed text; and Thai edge antialiasing drifts ≤ 17.2/255 from CFF-vs-TrueType rasterisation. Dimensions, advances and positions are exact.

**Coverage limits, stated plainly.** Validated on Linux via HarfBuzz and FreeType, plus direct inspection of a Windows-produced PDF. **Not** validated by reprinting on Windows with the rebuilt fonts installed. Only defect 3 was observed end-to-end in a real print; defects 1, 2, 4 and 5 have no Windows-side confirmation either way.

---

## Open items

- **Reprint on Windows to close the loop.** Install the rebuilt fonts, fully restart Word (it caches font data per session), reprint `TRR Sritep Resin Test Report - REV01.docx`. Check Thai renders correctly and a Thai paragraph pastes cleanly.
- **Stale copies:** `D:\Doccument\New Identity\ICHITA-Template-Generator-Setup\assets` still holds the pre-fix fonts. Re-copy from `assets/fonts/aeonik-th/`.
- ~~**TH-Slussen has defect 2:** 13 of 64 Coverage tables unsorted.~~ **Wrong — measured 0 of 57**, confirmed independently by `fontTools.subset` (zero `Coverage is not sorted` warnings on all four shipped weights). TH-Slussen instead had defects **1** (43 GSUB + 7 GPOS Slussen lookups discarded), **3** (124 glyphs/weight, 44 zero-advance marks), a variant of **4** (`usWinDescent` 334 vs Thai ink −561, clipping rather than disagreeing metric sets), and a **sixth defect not present in Aeonik**: Regular, Medium and Semibold all declared nameID1 `TH Slussen` + nameID2 `Regular`, so Windows could not distinguish them. All fixed; see `2026-08-01-th-slussen-merge.md`.
- **Line spacing is a judgment call.** 1000/−300/0 gives a 1.30 em line box (Aeonik intended 1.20, Bai 1.25). The extra room clears two-level Thai stacks. Tunable via `ASCENT`/`DESCENT` in the build script.
- **`compare_th_aeonik.py` needs `uharfbuzz`, `freetype-py`** (and `pikepdf` for PDF forensics), installed into `venv_fonts/` but not recorded in any requirements file.
- **Nothing is committed.** All work is uncommitted on `docs/ichita-proposal-design`.

---

# Addendum, 2026-08-02 — the format flip, and what the residual Thai drift actually was

**Scope:** `build_th_aeonik.py`, `build_th_slussen.py`, `compare_th_*.py`,
`build_font_specimen.py`, `check_print_pdf.py`, `fix-th-fonts.sh`.
Both families now ship as **TrueType (`glyf`), not CFF** — `.ttf`, not `.otf`.

## The question

*"If we do the font engineering right, we should be able to create an identical
font. What makes Bai Jamjuree work and TH Aeonik fail?"*

Right, with one constraint that turns out to be structural.

## What the residual drift was — and was not

The original post-mortem's last recorded hypothesis was correct and is now
measured: *"It is CFF-vs-TrueType scan conversion, and is not fixable without
keeping the font TrueType."* Three measurements close it:

1. **The outlines were already almost exact.** Max control-point deviation
   between Bai's Thai and TH-Aeonik's CFF copy: **0.7071 units** over 362 copied
   glyphs — precisely the ½-unit rounding of the quadratic→cubic control points.
   Zero advance-width mismatches.
2. **Curve precision was irrelevant.** Rebuilding at cu2qu `max_err` 1.0, 0.5,
   0.1 and 0.001 produced **byte-identical** rasters. If approximation were the
   cause, a 1000× tighter bound would have moved something.
3. **The lever is the format itself.** Same glyphs, CFF base: 8.36 % of pixels
   differ (mean Δ 6.83/255). `glyf` base: **0.00 %**.

So the difference was never data loss. It was FreeType's Adobe CFF engine versus
its TrueType engine. Bai Jamjuree "works" because it is rendered in the format it
was drawn in; the merged Thai was the same geometry handed to a different
rasteriser. **Identity is achievable for exactly one script at a time** — whichever
one keeps its native format.

| Build | Thai vs Bai Jamjuree | Latin vs Aeonik |
|---|---|---|
| CFF base (shipped through `5bac449`) | 8.36 % px, mean Δ 6.83/255 | **0.00 % — exact** |
| `glyf` base (now) | **0.00 % — exact** | 10.16 % px, mean Δ 3.90/255 |

## Why `glyf` was the right side to keep

Not just the pixels. **Defect 3 becomes unrepresentable.** `glyf` has no width
operand, so the CFF-charstring-width-vs-`hmtx` divergence that made every printed
PDF unreadable cannot be expressed at all. `check_cff_widths()` is retired and
replaced by `check_advance_source()`, which asserts the structural property
instead of re-checking the arithmetic. It also makes Print to PDF's
`/CIDFontType2` + `/FontFile2` declaration truthful — the source of poppler's 32
`Mismatch between font type and embedded font file` warnings.

Latin's drift is also *lower amplitude* than the Thai drift it replaces
(3.90 vs 6.83/255 mean), so total visual error went down, not sideways.

**Accepted cost, recorded rather than discovered later:** Slussen ships real CFF
stem hints (2–6 per Latin glyph) and they are dropped by the conversion, with no
TrueType instructions replacing them. Aeonik carries **zero** hint operators, so
it loses nothing. Nothing on Linux can measure the consequence; it is a Windows
small-size question.

## Defect 7 — stale `hmtx` lsb, harmless in CFF, a visible shift in `glyf`

The first `glyf` build put max Latin deviation at 37.34/255 with 8 advance
mismatches, all on glyph `'9'` in the italics. Every on-curve point of
`BoldItalic '9'` was displaced by **exactly +2 units in x** — a uniform
translation, which is not what curve approximation looks like.

`glyf` consumers position an outline at `(lsb - xMin)`. **CFF ignores `hmtx` lsb
entirely**, so Aeonik ships a handful of glyphs whose declared lsb disagrees with
their own outline — `BoldItalic '9'` says 33 against an xMin of 31. Inheriting
that translated the whole glyph the moment the font became TrueType. The italics
had 15–20 such glyphs each, the uprights 0–2 — which is exactly where the
outliers were.

*Fix:* re-sync `hmtx` lsb to each glyph's recalculated `xMin` after conversion.
Advance mismatches went 8 → **0**, max deviation 37.34 → **16.12/255**.

*Learning:* a value that one format ignores is a value nobody has ever validated.
Changing format promotes every such value from decoration to load-bearing.

## The test gap this exposed

`compare_th_*.py` reached glyphs through `get_char_index`, so it could only ever
see **cmap-mapped** ones — 87 of the 124 glyphs Thai text can actually reach. The
GSUB-only tone-mark variants (`uni0E47.narrow`, `uni0E48.small`, the
`uni0E4D0E49` ligatures) were **structurally invisible to every raster check ever
run**, and they are precisely the glyphs that appear in real two-level stacks.
This is the same lesson as defect 4b — *measure over the reachable set, not the
convenient one* — recurring in the test rather than in the build.

*Fix:* `check_thai_verbatim()` computes the GSUB closure and compares all 124
glyphs **byte-for-byte** (coordinates, flags, contour ends, components, `hmtx`)
against Bai Jamjuree. Stronger than any raster comparison, and it was confirmed
to fail on a 1-unit nudge of `uni0E48.small` — a defect the old test could not
have detected at any size.

## One difference that is real, inherent, and not a defect

The browser specimen showed a 1px vertical offset on the tone mark in `ป็`, where
HarfBuzz, FreeType-unhinted, GDEF, and the byte-level outline comparison all said
identical. Reproduced outside the browser: under **full grid-fitting**,
`uni0E47.narrow` at 26px is 10 rows tall in both merged families and 9 in Bai.

FreeType's autohinter derives its zones from the font as a whole, and **a merged
font's glyph set can never equal either source's**. The old CFF build showed the
identical 1px offset, so this is inherent to merging, not to the format change.
Unhinted, all three agree exactly.

Worth stating plainly because it is the one place where "the merge must be
invisible" cannot be literally true, and a future session will otherwise chase it.

## Also fixed: the specimen was grading a comparison it could never win

The specimen's Thai panels compared strings containing **spaces**. `space` is a
shared glyph that deliberately comes from the Latin source (Aeonik 262, Slussen
276, Bai Regular 260, Bai Bold 288), and browsers round each advance to a whole
pixel — so one space shifts everything after it. A TH-Slussen panel with 11
spaces read 11px wider than Bai purely from this. `compare_th_*.py` had excluded
`space` from the Thai comparison since it was written; the specimen never did.
Now uses space-free Thai for the graded panels.

## Learnings

**A uniform translation is never an approximation error.** Every point of `'9'`
moved by the same +2u. That single observation ruled out cu2qu, rounding and the
rasteriser in one step and pointed straight at a metric. Look at the *shape* of a
discrepancy before reaching for its most plausible cause.

**Set a tolerance from the distribution you are bounding, not the summary you
happen to have.** The Latin limit was first set to 10.0 from a 3.90 figure that
was the mean *across all glyphs*, while the test compares *per glyph and size*,
where p99 is 11.70 and max 16.12. The bar failed instantly on a correct build.

**Reproduce a browser-only symptom outside the browser before theorising.** The
`ป็` offset survived four wrong explanations (baseline, blue zones, `.narrow`
substitution, vertical metrics) and was settled in one command by rendering the
glyph at `TARGET_NORMAL` instead of unhinted.

**Check whether a difference is a regression before treating it as one.**
Restoring the pre-flip build from git showed the same 1px offset, which reframed
it from "the format change broke this" to "this has always been true of a merged
font."
