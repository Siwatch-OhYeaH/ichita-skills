# TH-Slussen — four merge defects, and the one the Aeonik post-mortem got wrong

**Date:** 2026-08-01
**Scope:** `scripts/build_th_slussen.py`, `scripts/compare_th_slussen.py`, `assets/fonts/slussen-th/*.otf` (4 weights)
**Status:** all four fixed and validated on Linux. Windows visual test pending.
**Companion:** [`2026-08-01-th-aeonik-merge.md`](2026-08-01-th-aeonik-merge.md) — same merge pipeline, same author, five defects.

---

## Summary

TH-Slussen merges Slussen (Latin, CFF/OTF) with Bai Jamjuree (Thai, TrueType). It was
built from a near-copy of the TH-Aeonik script, so it inherited most of the same
defects — but not the set the Aeonik post-mortem predicted.

| # | Defect | Present? | Blast radius |
|---|---|---|---|
| 3 | Thai CFF charstring widths off by `nominalWidthX` | **yes** — 124 glyphs/weight, 44 zero-advance marks | Every printed PDF unreadable |
| 1 | Slussen's Latin GSUB/GPOS discarded | **yes** — 43 GSUB + 7 GPOS lookups | All Latin kerning + ligatures wrong, silently |
| 6 | Three weights share one family+subfamily name | **yes** — new, not in Aeonik | Medium and SemiBold unselectable on Windows |
| 4 | `usWinDescent` 334 vs Thai ink −561 | **yes, as a variant** | Thai below-vowels clipped by GDI |
| 2 | Coverage tables out of glyph-ID order | **no** — 0/57, not 13/64 | — |
| 5 | Thai codepoints in the single-byte Mac cmap | **no** — 0 | — |

---

## Defect 3 — the one that breaks printed documents

Identical to Aeonik's, verbatim, including the comment-free two-line shape:

```python
pen = T2CharStringPen(bai_glyph.width, bai_glyph_set)
...
charstring.private = top_dict.Private     # nominalWidthX = 616 / 632 / ...
```

`T2CharStringPen` encodes the width operand assuming `nominalWidthX == 0`; attaching
Slussen's Private DICT afterwards means the rasteriser decodes `nominalWidthX + operand`.
Measured on the shipped Regular: `uni0E01` ก declares `hmtx=602`, charstring `1218` —
exactly +616, Slussen Regular's `nominalWidthX`. 124 glyphs per weight, of which **44
are zero-advance combining marks**, which is what makes it fatal rather than merely
loose: Microsoft Print to PDF builds the PDF `/W` array from charstrings, not `hmtx`,
so every tone mark and above-vowel gets a real advance and detaches from its consonant.

**Fix:** `T2CharStringPen(bai_glyph.width - priv.nominalWidthX, ...)`.

---

## Defect 1 — Slussen's Latin typography was thrown away

```python
slussen_font["GPOS"] = copy_mod.deepcopy(bai_font["GPOS"])
slussen_font["GSUB"] = copy_mod.deepcopy(bai_font["GSUB"])
```

Assignment, not merge. Slussen's 43 GSUB and 7 GPOS lookups were replaced by Bai
Jamjuree's 20 and 10. Latin glyphs stayed Slussen's; the spacing applied to them
became Bai Jamjuree's. Visible in the acceptance test as advance-width drift on
ordinary words — `Ichita` at 8px shaped `I=149 c=293 h=301 i=122 t=199` where Slussen
wants `132 / 285 / 286 / 112 / 197`.

**Fix:** `_union_ot()`, ported from the Aeonik build. Slussen's table is the base;
Bai's lookups are appended with nested `SubstLookupRecord`/`PosLookupRecord` indices
shifted; only the `thai` script is adopted, so `latn` and `DFLT` stay Slussen's.
After the fix: GSUB 63 (43+20), GPOS 17 (7+10).

Unlike Aeonik, **no Slussen weight ships a stub `thai` script record** — the asymmetry
that broke two Aeonik fix attempts does not exist here. The `absorb()` same-tag merge
path is retained anyway; it is the correct general behaviour.

---

## Defect 6 — three weights with the same name (new; Aeonik never had it)

```python
"Regular":  nameID1="TH Slussen",  nameID2="Regular"
"Medium":   nameID1="TH Slussen",  nameID2="Regular"   # collides
"Semibold": nameID1="TH Slussen",  nameID2="Regular"   # collides
```

`nameID2` may only be `Regular`/`Bold`/`Italic`/`Bold Italic`, so a family sharing one
`nameID1` holds at most four faces. Medium and SemiBold do not fit and needed their own
`nameID1`. As shipped, three of the four weights announced themselves identically and
Windows could not tell them apart.

The source comment above the Medium entry read *"Non-RIBBI weight: nameID1 must be
unique for Windows font picker"* — directly above code that did the opposite. Aeonik
got this right (`TH Aeonik Light` has a unique `nameID1`); the pattern was not carried
across when the script was copied.

**Fix:** unique `nameID1` for Medium and SemiBold, `nameID16`/`nameID17` left as
`TH Slussen` + weight name so typographically-aware applications regroup all four.
Output filename standardised to `TH-Slussen-SemiBold.otf`, matching what shipped.

---

## Defect 4 — clipping, not disagreeing metrics

Aeonik's defect 4 was three metric sets disagreeing. Slussen's `hhea` and `sTypo`
already agreed (1074/−272/166) and `USE_TYPO_METRICS` was set, so line spacing was
fine. The problem was narrower: `usWinAscent`/`usWinDescent` is the GDI **clipping**
box, and at 1262/334 it did not contain the merged ink of +1255/−561. Thai
below-vowels were cut off on Windows. The build script's own docstring described this
as intended — *"Keep vertical metrics IDENTICAL to original Slussen"*, *"Thai clipping
is acceptable"*.

**Fix:** line box untouched (it sets document line spacing in every existing file);
`usWinDescent` 334 → 570 to clear the ink. Because `USE_TYPO_METRICS` is on, consumers
still take spacing from `sTypo`, so this changes what is visible without changing how
far apart the lines sit.

---

## Defect 2 — the prediction that was wrong

The Aeonik post-mortem listed as an open item: *"TH-Slussen has defect 2: 13 of 64
Coverage tables unsorted."* Measured: **0 of 57**, on all four weights, confirmed
independently by running `fontTools.subset` over each font and counting
`Coverage is not sorted by glyph ids` warnings — zero. The same oracle emits 26 on a
pre-fix Aeonik Regular, so it was verified capable of firing before the negative
result was believed.

Whether re-parented Coverage survives sorted is a property of the two glyph orders
involved, not of the merge code — Aeonik's glyph order broke it, Slussen's did not.

**This flipped after the fix.** Retaining Slussen's own 43+7 lookups changes the merged
glyph layout, and the new build produces **27 unsorted Coverage tables per weight**.
`sort_coverage()` was ported in as a precaution against a defect that did not exist,
and turned out to be required by the fix for a different one.

Defect 5 (Thai codepoints in the single-byte Mac cmap) measured 0 in every weight;
`fix_mac_cmap()` was ported for symmetry and drops nothing.

---

## Validation

`scripts/compare_th_slussen.py`, 4 weights × 13 sizes (8–144 px) — **PASS**, from
372 failures before the fix to 0:

- 4 CFF-width audits (charstring widths vs `hmtx`)
- 344 Coverage-order checks
- 4 clipping-box audits (`usWin*` vs ink)
- 1820 shaping comparisons (HarfBuzz glyph sequence + positions)
- 5408 raster comparisons (FreeType bitmaps, unhinted)
- Latin is **pixel-exact** to Slussen; Thai edge antialiasing ≤ 17.2/255 (CFF-vs-TrueType
  scan conversion, not a defect — dimensions, advances and positions are exact)

Every structural guard was observed **failing** before being trusted: the CFF-width and
Coverage guards fire on pre-fix TH-Aeonik (363 and 29/57); the clipping guard fired on
the shipped TH-Slussen (`usWinDescent 334 < ink bottom 488`).

**Coverage limits, stated plainly.** Linux only — HarfBuzz and FreeType. Unlike the
Aeonik investigation there is **no Windows-produced artifact for TH-Slussen**: defect 3
is fixed by the same mechanism that was proven end-to-end on Aeonik, but that inference
is transferred, not observed here. Nothing in this repo can verify the Windows print
path.

---

## Learnings

**An open item in a post-mortem is a hypothesis, not an inventory.** "TH-Slussen has
defect 2, 13/64" was written from the same reasoning that made it true for Aeonik, and
carried the specificity of a measurement. It was never measured. Re-measure inherited
claims before acting on them — and note that acting on this one (porting
`sort_coverage()`) was still correct, for a reason nobody predicted.

**Fixing one defect can create another.** The Coverage sort was dead code against the
shipped fonts and became load-bearing the moment defect 1 was fixed, because retaining
Slussen's lookups moved the glyph IDs the Coverage tables index. A guard that measures
0 today is not evidence it can be dropped.

**Copied code carries copied defects, minus the fixes.** Four of the six defects here
are character-for-character identical to Aeonik's. The one genuinely new defect —
colliding family names — is one Aeonik had already solved correctly; the solution just
wasn't part of what got copied.

**The comment was right and the code was wrong.** `"nameID1 must be unique for Windows
font picker"` sat directly above code setting it non-uniquely. Worth reading comments
as assertions to check rather than as documentation to trust.

**The guards written here found a defect in the font that was already "done".** The
clipping-box check was added for Slussen, then pointed back at TH-Aeonik — which had
passed its own acceptance test — and caught `usWinAscent` 1050 against ink of +1225 on
all six weights, clipping the tone marks off real Thai text. Aeonik's test had no
Coverage or clipping check at all; the two families' tests had drifted to different
standards. Both now run the same guards. When one artifact's test gets stronger, re-run
it against its siblings before assuming they are still green.

---

## Open items

- **Windows visual test** — install the rebuilt fonts, fully restart Word (it caches
  font data per session), confirm Thai renders and pastes cleanly, and confirm Medium
  and SemiBold now appear as distinct choices.
- **Print to PDF on Windows** to close defect 3 end-to-end, as was done for Aeonik.
- **Stale copies:** any deployment holding pre-fix `slussen-th/` fonts needs re-copying.
- **`compare_th_slussen.py` needs `uharfbuzz`, `freetype-py`** — installed into
  `venv_fonts/`, still recorded in no requirements file.
- **Nothing is committed.** All work is uncommitted on `docs/ichita-proposal-design`.

---

# Addendum, 2026-08-02 — TH-Slussen is now TrueType

TH-Slussen was rebuilt on a `glyf` base alongside TH-Aeonik. The full reasoning,
measurements and the two new defects (stale `hmtx` lsb; the GSUB-only test gap)
are in the companion addendum to
[`2026-08-01-th-aeonik-merge.md`](2026-08-01-th-aeonik-merge.md). Slussen-specific
points only:

**Thai is now byte-identical to Bai Jamjuree** — all 124 reachable glyphs,
verified by `check_thai_verbatim()`, with 0 raster differences over 4 weights ×
13 sizes. Latin's residue is *smaller* than Aeonik's: mean Δ p50 2.69, p99 9.05,
**max 11.51/255**, zero advance mismatches (Aeonik's max is 16.12).

**Slussen's CFF stem hints are gone, and this family is the one that had them.**
Measured before the change: 2–6 hint operators on `A`/`a`/`o`/`n`. Aeonik carries
zero, so it gave up nothing; Slussen gave up real hinting and no TrueType
instructions replace it. `compare_th_slussen.py` runs FreeType unhinted and
therefore **cannot see this** — it is a Windows question at 9–11 pt, and it is the
single most likely place this change is noticed. It is listed as an open item for
that reason.

**Defect 7 (stale lsb) was worse here than in Aeonik:** 42–49 glyphs per weight
needed `hmtx` lsb re-synced to `xMin`, against 0–2 on the Aeonik uprights.

**Output is `TH-Slussen-*.ttf`.** The extension change is deliberate: it makes a
new build impossible to confuse with a pre-fix `.otf` still sitting in
`C:\Windows\Fonts`.
