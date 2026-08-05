# TH-Aeonik: the Latin rendered thinner and led wider than Aeonik

**Date:** 2026-08-04 (validated and bounded 2026-08-05)
**Branch:** `docs/ichita-proposal-design`
**Fix:** `a1f43b8` — *fix(fonts): give usWin the Latin's box — Word leads off it, not hhea*
**Offending change (defect A):** `ea0dce2` (2026-08-02) — *rebuild TH-Aeonik/TH-Slussen on a glyf base*
**Reported by:** Siwatch, on Windows, in Word
**Status:** TH-Aeonik fixed and verified in the acceptance renderer. TH-Slussen built but **not installed** — see Action items.

---

## Summary

Siwatch reported two defects in the merged TH-Aeonik family on 2026-08-04, both about
the **Latin** half, which is supposed to be Aeonik unchanged: it rendered noticeably
thinner, and it led about 50% wider than Aeonik at the same size. Neither was an outline
bug — TH-Aeonik's Latin outlines were dimensionally identical to Aeonik's, and every
Linux, HarfBuzz and outline-level check in the repo was green throughout.

Two independent root causes:

- **A — thinner.** The 2026-08-02 format flip (`ea0dce2`) moved both merged families from
  CFF to `glyf`. Windows rasterises the two formats through different engines, so
  byte-identical outlines rendered **−15.8% ink** (TH-Aeonik) and **−20.4%** (TH-Slussen).
- **B — wider leading.** `usWinAscent`/`usWinDescent` were sized to *contain the Thai ink*
  (1800/1000 em) on the recorded belief that `usWin` does not affect line spacing. For a
  **CFF** face, Word takes its line pitch from `usWinAscent + usWinDescent`, so the box
  named like a clipping bound was the spacing control.

`a1f43b8` fixed both: both families now ship `.otf`, appending Thai to the Latin's *own*
`CFF ` table via the shared `scripts/th_cff.py` so the Latin is bit-identical, and all
three vertical metric sets carry Aeonik's `1000 / -200 / 0`. Verified 2026-08-05 in the
shipping renderer: TH-Aeonik's Latin ink matches Aeonik **to the unit** in both engines,
and Word leads both at **13.200 pt** at 11 pt Single.

A 2026-08-05 follow-up measurement **bounded root cause B**: "Word leads off usWin" as
committed is over-general and true only for CFF faces. The fix is unaffected — see
[Bounding root cause B](#bounding-root-cause-b-2026-08-05).

---

## Symptom

Two reports, both against freshly installed faces, both Latin-only text:

> "TH Aeonik is slightly thinner than Aeonik, especially Regular"

> "the only left issue is line spacing when using latin alone is not equal to aeonik
> when typing the same."

Measured at 11 pt in DirectWrite, before the fix:

| font | format | stems (px) | ink | advance |
|---|---|---|---|---|
| Aeonik | `.otf` / CFF | 2,1 | 11,056 | 9.857 |
| TH Aeonik | `.ttf` / `glyf` | 1,1 | 9,310 | 9.857 |
| Slussen | `.otf` / CFF | 2,2 | 12,485 | 11.293 |
| TH Slussen | `.ttf` / `glyf` | 2,2 | 9,940 | 11.293 |

TH-Aeonik lost a whole stem pixel and 15.8% of its ink; advances were exact. Regular
shows it worst because the gap is largest at text sizes. TH-Slussen kept its stem pixel
count and was still 20.4% lighter — which is why *ink* and *stems* are separate
assertions.

Line pitch, measured in Word via COM on the same paragraph, five lines each:

```
Aeonik      75.80 pt / 5 = 15.16 pt per line
TH Aeonik  114.00 pt / 5 = 22.80 pt per line     ratio 1.504
```

1.504 is `usWin` 1800/1200. It is not `hhea` 1200/1200 = 1.000, and `hhea` and `sTypo`
were both already Aeonik's exactly. (Those absolute figures were taken at Word's default
*Multiple 1.15*, not *Single* — 15.16 = 1200/em × 1.15 × 11 pt. The multiplier cancels in
the ratio, so 1.504 stands; only the absolutes are not directly comparable to the *Single*
figures elsewhere in this document.)

---

## Root cause A — the format flip relocated the rasteriser

`ea0dce2` rebuilt both merged families on a `glyf` base. That change was sound on its own
terms and fixed real defects: Bai Jamjuree's Thai became byte-identical to its source
(0.00% of pixels differing, against 8.36% in the CFF build), and CFF charstring widths
disagreeing with `hmtx` — which Print to PDF turned into the `/W` array and which made
every printed PDF unreadable — became structurally unrepresentable.

Its accepted cost was recorded as *"Slussen's CFF stem hints (2-6/glyph) are dropped;
Aeonik had none. Unmeasurable from Linux — open item for the Windows visual test."*

**The recorded cost named the wrong mechanism.** Dropped hints were not what Siwatch saw.
Aeonik carries *no* CFF hints at all and TH-Aeonik still lost 15.8% of its ink. The cause
is the **format itself**: Windows rasterises CFF and `glyf` through different engines, and
identical outlines therefore land different amounts of ink. Identity across the two
formats is achievable for exactly one script at a time, and `ea0dce2` chose Thai.

Nothing on Linux can see this. FreeType's engines do not reproduce Windows' per-format
behaviour, so a green HarfBuzz/FreeType suite says nothing about it — the same structural
blindness this project has hit repeatedly.

## Root cause B — `usWin` is the line-pitch control for a CFF face

`build_th_aeonik.py` set `WIN_ASCENT`/`WIN_DESCENT` to 1240/560 to contain the Thai ink,
on a comment that asserted the opposite of the truth:

> "widening this does not touch line spacing — Word leads off hhea and LibreOffice off
> sTypo, neither of which is usWin."

For the CFF faces this repo ships, that is false. Word led TH-Aeonik 1.504× Aeonik while
`hhea` and `sTypo` were already correct to the unit. Every Linux and outline-level check
stayed green while the shipping renderer was 50% out on the one property Siwatch was
looking at.

### Bounding root cause B (2026-08-05)

`a1f43b8` recorded the conclusion unconditionally: *"Word leads off usWinAscent +
usWinDescent."* Word's pitch was then measured for **15 installed families** (six
paragraphs, 11 pt, *Single*, `SpaceBefore/After = 0`, baseline travel ÷ 5, via Word COM)
and compared against each file's three metric sets. **No single field fits more than four
of them.** Three branches fit all fifteen:

| format | `USE_TYPO_METRICS` | field Word uses | evidence |
|---|---|---|---|
| CFF | set | **`usWin`** | Slussen 1595 (`usWin` 1596, `hhea` 1512); pre-fix TH-Aeonik 1.504× = 1800/1200 |
| `glyf` | set | **`sTypo`** (`== hhea` in every font measured) | Bai Jamjuree 1250 (`usWin` **1786**), Sarabun 1300 (`usWin` **1853**), Noto Sans 1364, Gabriola 1700, Sitka Text 1250, Ubuntu Mono 1123, TH Slussen 1627 |
| `glyf` | clear | **max(`hhea`, `usWin`)** | Arial 1150 (`hhea` 1150 > `usWin` 1117), Times 1150, Ebrima 1359, Segoe Print 1764, DilleniaUPC 1305 (`hhea` only 600), Ink Free 1236 (`usWin` 1238 > `hhea` 1200) |

Two things follow, and neither weakens the fix:

1. **The fix is correct for the format it ships.** TH-Aeonik ships CFF, so `usWin` really
   is its spacing control. The fix is *also* robust beyond its stated reason: it set
   `hhea`, `sTypo` and `usWin` all to 1200, so it lands on 1200 in every branch above.
   That robustness was a side effect of unifying the metric sets, not a designed property.
2. **The format is part of the vertical metrics.** A format flip silently relocates the
   spacing control without touching a single metric field. This is the same
   `ea0dce2` → defect chain as root cause A, in a second dimension.

The `USE_TYPO_METRICS` branch is only partly resolved: in every `glyf` font measured,
`sTypo` and `hhea` agreed, so *which* of the two the set-bit branch reads is **not
established** — only that `usWin` is not it. Slussen is the single measured CFF face where
`usWin ≠ hhea`, so the CFF branch rests on it plus the pre-fix TH-Aeonik observation.

---

## Why it produced the symptom

Both defects presented on **Latin-only** text, which is the half of the merged font nobody
had reason to suspect — the Thai is the part that gets engineered, and the Latin is
supposed to be a pass-through. Both were caused by properties that are invisible to
outline comparison:

- **A:** the outlines were never wrong, so every check that compared outlines, advances,
  bounding boxes or rasters *on Linux* was correctly green. The defect lived entirely in
  which Windows engine drew them.
- **B:** the field that was wrong (`usWin`) is documented as a clipping bound and was
  actively believed not to affect spacing, so it was excluded from the line-spacing
  investigation by assumption. The two fields that *were* checked (`hhea`, `sTypo`) were
  already exactly right, which made the font look innocent.

---

## Fix

`a1f43b8`, both halves:

- **Format.** Both families ship `.otf`. Thai glyphs are appended to the Latin source's
  *own* `CFF ` table through the new shared `scripts/th_cff.py`, rather than the merged
  font being re-generated in a chosen format. The Latin is therefore bit-identical to its
  source by construction, not by tolerance. Slussen's 2712 CFF hint operations —
  explicitly given up by `ea0dce2` — are restored.
- **Metrics.** `ASCENT, DESCENT, LINEGAP = 1000, -200, 0` and
  `WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT`, so `hhea`, `sTypo` and `usWin` all carry
  Aeonik's 1200 box. The Thai ink is now deliberately allowed *outside* the box.

Letting ink escape `usWin` is what Windows' own fonts do — measured on this machine, ink
extent against `usWin`: Tahoma **+246**, Segoe UI **+379**, TH-Aeonik **+391**. Neither
Windows font clips in Word, so `usWin` is not a clip bound in DirectWrite-era Word.

**Accepted, documented cost:** the Thai does not fit the 1200 box. The worst Thai-over-Thai
stacks overlap by 262 units (3.9 px at 11 pt). This was not chosen blind:

- `scripts/solve_mark_scale.py` proved shrinking the marks cannot close the gap — 25%
  smaller marks buy ~35 units, because `raise_upper_marks` re-lifts them and the lower
  floor is `ฐ`'s consonant tail, not a mark. The floor is ~1383 against 1200, so **1200 is
  unreachable for Thai at any mark size.** `MARK_SCALE` stays 1.000.
- The clean fix for per-script line height — Word's separate Latin / Complex-Script font
  slots, measured and working in `2e41d41` (Latin-only 13.20 pt, with Thai 16.92 pt) — was
  **ruled out by Siwatch**: *"solve it with the font engineering, not by set up two
  separate fonts."* One font has one line box, so the single-font answer is the Latin's box
  with the Thai overlapping. Do not re-propose the split.

### Instrument added

`scripts/win_latin_parity.py` — asserts a merged family renders its Latin exactly like the
Latin it merged, *through the shipping renderer*. This is the test whose absence let a 16%
ink deficit ship: every prior check compared outlines, and the outlines were never wrong.
`powershell.exe` is on PATH from WSL, so GDI and DirectWrite are directly measurable.
It asserts `advance` (metric identity), `capH`/`bboxW` (glyph size, to separate "smaller"
from "thinner"), `stems` (what a reader perceives as weight), `ink` (total darkness), and
the line box — and it reports the font *file* Windows resolved, because a parity result
measured against a stale installed file is worthless.

---

## How it was found

1. **Repro.** Both defects reproduce deterministically by typing Latin-only text in Word
   at 11 pt and comparing against Aeonik in the same document. Neither needs Thai.
2. **Word COM from WSL.** `powershell.exe` reaches GDI, DirectWrite and Word COM, so the
   acceptance renderer is measurable locally. This is what separated the two defects: same
   advance, different ink ⇒ a rasteriser problem, not a metrics problem; correct `hhea`
   and `sTypo`, wrong pitch ⇒ a metrics problem in a field nobody was looking at.
3. **Hypotheses rejected, defect A:**
   - *Outline drift from the CFF→`glyf` conversion.* Rejected — outlines matched to 0.7071
     units and `cu2qu max_err` down to 0.001 gave byte-identical rasters.
   - *Dropped CFF stem hints.* Rejected — Aeonik has no hints and lost 15.8% anyway.
   - *Synthetic weight / emboldening.* Rejected — the Latin is never emboldened; only the
     Thai is.
4. **Hypotheses rejected, defect B:** `hhea` and `sTypo` were each measured and found
   already exact. The experiment that nailed it was arithmetic on the ratio: 1.504 is
   exactly 1800/1200, which is the `usWin` ratio and nothing else in the font.
5. **The 2026-08-05 bound** came from asking the same question of fonts nobody had
   engineered: measuring Word's pitch for 15 installed families against their metric
   fields. Bai Jamjuree (`usWin` 1786, pitch 1250) and Sarabun (`usWin` 1853, pitch 1300)
   falsify the unconditional rule immediately.

---

## Why it slipped through

- **Defect A — an accepted risk that was never closed.** `ea0dce2` correctly identified
  that a residual existed and correctly stated it was *unmeasurable from Linux*, filing it
  as "open item for the Windows visual test." That item was still open when the build
  shipped to Siwatch, and it named the wrong mechanism (hints rather than the format), so
  the eventual measurement was aimed at the wrong thing. The gap is not the trade — the
  trade was reasonable — it is that a known-unmeasurable residual reached the acceptance
  renderer only by way of the user.
- **Defect B — a false belief written down as a comment, then relied on.** The `usWin`
  comment asserted "Word leads off hhea"; four checks encoded the surrounding reasoning.
  No test measured line pitch on Windows, so nothing could contradict it.
- **CI/tooling gap common to both.** Every check compared **outlines on Linux**. Both
  defects were properties of the *Windows rasteriser and its metric-field selection*,
  which outline comparison cannot express. This is the third session in which "green on
  Linux, wrong in Word" has been the shape of the bug.
- **The 2026-08-05 over-generalisation** slipped through for one measurement's worth of
  reasoning: the conclusion was drawn from a single font pair and stated as a general rule
  about Word. Both fonts in that pair happened to be CFF.

---

## Validation

Measured 2026-08-05 against the **installed** faces, at 11 pt.

**TH-Aeonik — fixed, verified in the shipping renderer.**

`scripts/win_latin_parity.py --sizes 11`:

| engine | font | capH | bboxW | stems | ink | advance | box |
|---|---|---|---|---|---|---|---|
| dwrite | Aeonik | 11 | 8 | 2,1 | 149,221 | 137.430 | 1200 |
| dwrite | TH Aeonik | 11 | 8 | 2,1 | **149,221** | 137.430 | 1200 |
| gdi | Aeonik | 10 | 8 | 1,2 | 128,744 | — | 1200 |
| gdi | TH Aeonik | 10 | 8 | 1,2 | **128,744** | — | 1200 |

Ink is identical to the unit in both engines, not merely within tolerance. The resolved
file is `TH-AEONIK-REGULAR.OTF` and its bytes match the repo build.

Word line pitch (six paragraphs, 11 pt, *Single*, no space before/after, baseline
travel ÷ 5):

```
Aeonik      13.200 pt/line      TH Aeonik   13.200 pt/line
```

Exactly equal, and 13.200 pt = 1200/em — the box Aeonik itself carries.

**Other suites:** `scripts/qc_th_fonts.py` **19/20**. Check 6 (Thai Bold vs Black
separation) is red **on purpose** — Bai Jamjuree has nothing heavier than Bold, so
balanced-per-weight and Bold-distinct-from-Black are mutually exclusive from this source.
Do not widen that tolerance.

**Coverage stated honestly:**

- Validated on **TH-Aeonik Regular at 11 pt**, both engines, plus Word pitch. Not
  re-measured across all 14 faces or at 14/22 pt in this pass.
- **TH-Slussen is NOT validated and is currently failing.** The repo ships four `.otf`
  faces; the installed files are still the superseded `.ttf`. The probe resolves
  `TH-SLUSSEN-REGULAR.TTF` and reports ink **−18.8%** (dwrite) / **−17.1%** (gdi) and
  stems 1,1 against Slussen's 2,2. **Every one of those failures has the single cause that
  the built `.otf` is not installed** — they are not a code regression.
- Word's PDF **export** substitutes `.otf` faces to Calibri, so an embedded-font list from
  an exported PDF is not acceptance evidence for this work. Screen layout is unaffected.
- The 2026-08-05 branch table is measured for 15 families on **one machine, one Word
  version**. The `sTypo`-vs-`hhea` question inside the `glyf`+`USE_TYPO_METRICS` branch is
  unresolved by construction (they agreed in every font available).

---

## Action items

1. **Install the built faces on Windows before any further QC.** 21 obsolete `.ttf` must
   be uninstalled first (including stale Regular/Medium and three `_0` duplicates), then
   the 18 `.otf` installed from `assets/fonts/{aeonik-th,slussen-th}`. Close **Word and
   PowerPoint** first — a locked file is what produced `TH-Aeonik-Regular_0.ttf` and left
   a stale file registered under the family name. Install via Windows Settings; do **not**
   run `fix-th-fonts.sh --apply-system --restart` (`--check` is a fine read-only report).
   *Owner: Siwatch.*
2. **Confirm or falsify the TH-Slussen line-box prediction, at install time.** The built
   `.otf` carries `usWin` 1980 against `hhea`/`sTypo` 1625. Under the CFF branch, Word will
   lead it off `usWin` — a jump from today's measured **17.900 pt** to a predicted
   **≈21.8 pt (+21.7%)**, caused purely by the format flip. `EXPECTED_LINE_RATIO["TH
   Slussen"]` is pinned at the predicted **1.241** and is red until this is settled. If the
   prediction holds, the +24% box is a decision to make deliberately, not to inherit.
   *This is the open "does TH-Slussen follow TH-Aeonik to an exact Latin box?" question,
   now with a deadline: installing the `.otf` changes its line spacing whether or not
   anyone decides.*
3. **Resolve `sTypo` vs `hhea` in the `glyf` + `USE_TYPO_METRICS` branch.** Build one
   throwaway face with the two deliberately disagreeing and measure it in Word. Until then
   `word_line_box()` reads `sTypo` for that branch on spec grounds, not measured grounds.
4. **Generators still do not use these fonts.** `docx_helpers.py:208` and
   `md_to_docx.TH_AEONIK_MODE = False` remain on the split-font path, so none of this work
   reaches generated DOCX output yet. Pre-existing, tracked separately.
5. **Correct the two 2026-08-01 post-mortems.** Both still cite the inverted acceptance
   test as proof of correctness. *Not done in this pass.*
6. **Unmeasured:** how often the worst Thai-over-Thai pairing actually occurs in real
   prose. Needs a Thai-heavy corpus; the repo's only Thai PDF has 382 Thai characters.

### Landed with this document (2026-08-05)

- `scripts/win_latin_parity.py`: added `word_line_box()`, which derives the box Word
  actually leads off from the resolved file, with the three-branch rule and its evidence.
  The line-box assertion now runs on that, once per family.
- Same file: the old assertion compared **WPF's** line box for a family against **GDI+'s**
  for the same family across two engine rows. Those are different quantities — WPF omits
  `hhea.lineGap`, GDI+ includes it — so Slussen's 166-unit `lineGap` made one identical
  font score 1.207× in dwrite and 1.075× in gdi, and one of the two was permanently red
  for reasons unrelated to the font. The `apiBox` column is now labelled as reference only
  and nothing is asserted against it.
- `scripts/build_th_aeonik.py`: the `usWin` comment block no longer states "Word leads off
  usWin" unconditionally, and the ink-vs-`usWin` table is marked as evidence about
  **clipping only** — all four Windows fonts in it are `glyf`, so none of them is led off
  `usWin` at all.
