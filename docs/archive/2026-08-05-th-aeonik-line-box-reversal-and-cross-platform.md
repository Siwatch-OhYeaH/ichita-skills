# Plan — TH Aeonik as the mixed-language face, plus Greek/math and cross-platform acceptance

**Date:** 2026-08-05
**Branch:** `docs/ichita-proposal-design`
**Decided by:** Siwatch, in the 2026-08-05 grilling session
**Supersedes:** the 2026-08-04 "TH Aeonik must be a drop-in Aeonik replacement" requirement,
and with it `EXPECTED_LINE_RATIO["TH Aeonik"] = 1.000`.

---

## The decision that drives everything

**Two fonts, chosen by the document's language, not one font that serves both.**

| document | font | line box | Latin leading |
|---|---|---|---|
| English only | **Aeonik** | 1200 | native |
| Thai + English mixed | **TH Aeonik** | **1537** | +28% vs Aeonik, accepted |

This reverses 2026-08-04. It is not a regression — it dissolves the conflict that produced
that day's defect. TH-Aeonik's box was forced to Aeonik's 1200 so that Latin-only text in a
TH-Aeonik document would lead like Aeonik; the cost was Thai lines overlapping by 262 units
(3.9 px at 11 pt). Once English-only documents use *actual Aeonik*, that requirement
evaporates and the box is free to be sized to what the Thai needs.

**Confirmed consequence, accepted:** in a mixed document, English-only paragraphs also lead
+28% wider than the same text in an Aeonik document. Siwatch accepted this explicitly.

**Bonus:** at 1537 the Thai *line-clearance* requirement is met with the 75-unit margin, so
the 262-unit overlap that was logged as a permanent accepted cost is retired.

### Where 1537 comes from

`scripts/thai_line_pitch.py --check`, worst face per family:

```
family      worst face              top   bottom   need    margin   box
TH-Aeonik   TH-Aeonik-Black.otf    1139    -323    1462     +75    1537
TH-Slussen  TH-Slussen-SemiBold    1178    -349    1527     +75    1602
```

`need = worst_upper_stack + |worst_lower_tail|`; `MARGIN = 75` is Leelawadee UI's own spare,
about one pixel at 11 pt / 96 dpi.

---

## Decisions recorded (do not re-litigate)

| # | Decision | Rationale |
|---|---|---|
| 1 | TH-Aeonik box → **1537**, `hhea` = `sTypo` = `usWin` all carry it | Sized to Thai's measured need + margin. Unifying all three sets is what makes the font robust across renderers — see below. |
| 2 | TH-Slussen gets the **full parity treatment now**: box → **1602**, `usWin` unified, 4 faces rebuilt and revalidated | Siwatch chose the consistent rule over the cheap fix, despite Slussen having no documented brand role. |
| 3 | Greek/math gaps closed by **harvesting the web cut's outlines**, not by cmap aliasing | Siwatch's call. Licence assumption noted below. |
| 4 | Missing weights: **interpolate Medium**; **extrapolate Air/Thin/Black, verify against each face's own measured stem, auto-fall-back to alias** per face that misses tolerance | Interpolation everywhere it is sound; no face ships a distorted glyph. |
| 5 | Word generators **auto-detect**: Latin-only → Aeonik, any Thai → TH-Aeonik | The generator has the whole document; making a human declare it invites the wrong answer. |
| 6 | **pptx skills out of scope** — claude-design owns decks now | The font must still *render* correctly in PowerPoint; the generator code is not touched. |
| 7 | macOS: **specify only, marked UNVERIFIED** | No Mac available. Engineered for CoreText by construction, not measured. |
| 8 | Web: **build WOFF2, hold it, do not serve** | Licence position unresolved — see Risks. |

### Why unifying all three metric sets is the whole cross-platform strategy

Measured 2026-08-05 across 15 installed families: which vertical field a renderer uses is
not fixed. Word takes CFF line pitch from `usWin`, `glyf`+USE_TYPO_METRICS from `sTypo`,
and `glyf` without the bit from `max(hhea, usWin)`. CoreText and browsers make their own
choices again.

So the plan does not try to learn every renderer's rule. It sets
`hhea = sTypo = usWin = 1537` so the font yields 1537 **whichever field is consulted**.
That is the property that makes Word, PowerPoint, Excel, CoreText and browsers agree, and
it is why decision 1 specifies all three rather than just the box.

---

## Sequencing — one rebuild, one install

**The pending "install the .otf on Windows" step from the previous handoff is now obsolete
and should NOT be done first.** Decision 1 changes the metrics of all 14 TH-Aeonik faces,
so installing the current build would mean uninstalling and reinstalling 18 fonts twice.
All build changes land first; then one rebuild of all 18 faces from one code state; then
one install.

```
Phase 1  metrics    TH-Aeonik box -> 1537            build_th_aeonik.py
Phase 2  metrics    TH-Slussen box -> 1602           build_th_slussen.py
Phase 3  glyphs     Greek/math, 5 codepoints         new scripts/th_greek.py
         -------- one rebuild, 18 faces, one code state --------
Phase 4  install    uninstall old, install 18 .otf   Siwatch, via Settings
Phase 5  acceptance Word / PPT / Excel / web / macOS spec
Phase 6  generators Word font selection logic
Phase 7  record     brand docs, post-mortem, memory
```

Phases 1–3 are independent of each other and can be built in any order; they share a single
rebuild because `qc_th_fonts.py` and the parity suite must run against faces built from one
code state (a stale `~/.local/share/fonts/th-current/` has fed the doc QC before).

---

## Phase 1 — TH-Aeonik line box 1200 → 1537

**Files:** `scripts/build_th_aeonik.py`, `scripts/win_latin_parity.py`, `scripts/qc_th_fonts.py`

1. `ASCENT`, `DESCENT`, `LINEGAP` → a 1537 box. `WIN_ASCENT/WIN_DESCENT` continue to mirror
   them.
   **The ascent/descent split is a measurement, not a preference.** The box must cover the
   worst upper stack (1139) and the worst lower tail (323); the 75-unit margin protects the
   junction between one line's tail and the next line's marks and can sit on either side.
   Candidate `1177 / -360`; to be set by measuring where the first baseline lands in Word
   and confirming Latin does not sit visibly low in its line.
2. **Invert `assert_line_box_matches_latin()` for the third time — and make it assert both
   halves this time.** It currently requires the box to equal Aeonik's 1200 exactly. It must
   now assert *both*:
   - the **number** 1537, so the value is reviewable on sight; and
   - the **relationship** `box >= required_pitch(face) + MARGIN` for every face, so a future
     Thai change that needs more room fails here rather than silently overlapping.
   Pinning only the number is what let a defect read as a principle for two days; pinning
   only the relationship is unreviewable. This repo has been burned by each in turn.
3. `EXPECTED_LINE_RATIO["TH Aeonik"]` 1.000 → **1.281** (1537/1200), with the comment
   rewritten: TH-Aeonik is no longer a drop-in Aeonik replacement, by decision.
4. `qc_th_fonts.py` checks 3 and 5 currently assert `usWin == the line box` for TH-Aeonik
   and record the ink overflow. The equality still holds. **Re-measure the overflow** —
   `TH-Aeonik-Regular` has `head.yMax/yMin` of 1120/−471 = 1591 raw glyph extent, which is
   larger than 1537, so ink may still exceed the box even though *line clearance* is now
   satisfied. These are two different questions and the second one must not be assumed from
   the first.

**Acceptance:** `thai_line_pitch --check` shows `spare` ≥ 0 for every TH-Aeonik face (today
it is −262). Word measures 1537/em = **16.91 pt at 11 pt Single**.

## Phase 2 — TH-Slussen full parity

**Files:** `scripts/build_th_slussen.py`, `scripts/win_latin_parity.py`

1. Box 1625 → **1602** (need 1527 + margin 75), and `usWin` 1980 → **1602**.
   The `usWin` unification is the important half: today the built `.otf` carries `usWin`
   1980 against a 1625 box, so installing it as CFF would have Word lead it at 1980 —
   a silent +21.7% that has nothing to do with the outlines.
2. `EXPECTED_LINE_RATIO["TH Slussen"]` → **1.004** (1602 / Slussen's `usWin` 1596). Replaces
   the currently-pinned 1.241, which was a *prediction* and is labelled as such.
3. Same both-halves assertion as Phase 1, against Slussen's own required pitch.

**Note:** TH-Aeonik lands at 1537 and TH-Slussen at 1602. "Slussen follows the Aeonik
decision" means *the same rule* — box = Thai need + margin, all three metric sets unified —
not the same number. Slussen's Thai is taller, so its box is bigger.

## Phase 3 — Greek and math coverage

**New file:** `scripts/th_greek.py`, called from both builders.

Five codepoints are missing from the desktop cut. All five have shapes already present under
a different codepoint, and three of them are *the same outline* in the web cut:

| missing | web cut | existing twin in v1 |
|---|---|---|
| `Δ` U+0394 | `uni0394`, w679, bounds (25,0,654,700) | `∆` U+2206, w670 |
| `μ` U+03BC | `uni03BC`, w571 | `µ` U+00B5, w564 |
| `Ω` U+03A9 | `uni03A9`, w735 | `Ω` U+2126 ohm, w741 |
| `Σ` U+03A3 | **absent** | `∑` U+2211 n-ary sum |
| `⌀` U+2300 | **absent** | `Ø` U+00D8 |

Why this matters in practice: Word's Symbol dialog and Insert→Equation emit the Greek
codepoints, and lab data pasted from Excel usually carries `μS/cm` with U+03BC — so today
those characters fall back to a system font mid-line.

1. **Harvest** `uni0394`, `uni03BC`, `uni03A9` from `assets/fonts/aeonik-woff/` for the six
   faces the web cut ships: Light, Regular, Bold and their italics.
2. **`Σ` and `⌀` cannot be harvested** — absent from every cut, including the web one and
   Slussen. Alias them to `∑` U+2211 and `Ø` U+00D8, and flag that both are genuine shape
   compromises rather than true equivalents. Revisit only if a real document reads wrong.
3. **Medium** — interpolate between the harvested Regular and Bold.
4. **Air, Thin, Black** (and italics) — extrapolate beyond the masters, then **measure the
   result's stem against that face's own `∆`/`µ`/`Ω` twin** and compare against the same
   tolerance discipline as `solve_weight_table.py`. Any face that misses tolerance falls
   back to the alias **for that face only**, and the measured number is recorded.
5. **Twin consistency within a face.** If `Δ` comes from the web cut (w679) while `∆` stays
   v1 (w670), two characters that should be identical render 9 units apart in the same word.
   In every harvested face, both codepoints must point at the same outline. This means `∆`
   changes appearance slightly in Light/Regular/Bold — a visible change to an existing
   glyph, flagged for Siwatch's review on the specimen.

**Acceptance:** a specimen sheet showing all five characters beside their twins at all 14
weights, plus `Δp`, `µS/cm`, `m³/h`, `H₂O`, `±`, `≤`, `Ω` in running text.

## Phase 4 — Install (Siwatch)

Uninstall the obsolete faces first — 21 `.ttf` including the stale Regular/Medium and the
three `_0` duplicates — then install the 18 `.otf`. **Close Word, PowerPoint and Excel
first**; a locked file is what produced `TH-Aeonik-Regular_0.ttf` and left a stale file
registered under the family name. Install through Windows Settings. Do **not** run
`fix-th-fonts.sh --apply-system --restart`; `--check` is a fine read-only report.
Remember `%LOCALAPPDATA%\Microsoft\Windows\Fonts` shadows `C:\Windows\Fonts`.

## Phase 5 — Cross-platform acceptance

**Windows Office (measurable here, via COM):**

- Extend the parity suite to **PowerPoint** and **Excel** alongside Word. Excel deserves
  particular attention: it auto-fits row height from font metrics, so a 1537 box makes
  default rows ~28% taller than Aeonik's. Nobody has looked at that yet and it is a direct,
  visible consequence of decision 1.
- Assert the measured pitch equals 1537/em in all three applications.

**Web:**

- Build **WOFF2** (+ WOFF fallback) for TH-Aeonik beside the `.otf`, with a CSS snippet and
  `unicode-range`. Verify computed line-height in headless Chrome. **Do not deploy** — see
  Risks.

**macOS — specified, UNVERIFIED:**

- Write the acceptance test and record that it has not been run. The engineering position is
  that unifying all three metric sets makes CoreText land on 1537 by construction; that is a
  construction argument, not a measurement, and must be labelled as such wherever it appears.

## Phase 6 — Word generator font selection

**Files:** `scripts/docx_helpers.py` (the brand config at ~line 208), `md_to_docx.py`

Replace the `TH_AEONIK_MODE = False` split-font path with content-driven selection: scan the
source for Thai codepoints (U+0E00–U+0E7F); any hit → TH-Aeonik throughout the document;
none → Aeonik. Provide an explicit override, and **log which font was chosen** in the build
output so the decision is never silent.

Note this is the first change in this whole effort that makes generated documents actually
use these fonts — until now `TH_AEONIK_MODE = False` meant none of the font work reached
generated DOCX output at all.

## Phase 7 — Record

- `assets/brand/ichita-defaults.md` and `docx-standard.md`: document the two-font rule so it
  is brand policy, not tribal knowledge — English-only → Aeonik, mixed → TH-Aeonik.
- Update `CLAUDE.md`: the "ruled out, do not re-propose" entry about the Latin/Complex-Script
  split stays valid, but the reasoning changes — per-script line height is now solved by
  choosing the font per document, not by one font serving both.
- Post-mortem is not needed (no defect); a plan-completion note and a memory update are.

---

## Risks and open items

1. **CoType licence, harvesting.** Extracting outlines from the web `.woff` into a desktop
   `.otf` is modification plus format conversion of a webfont-licensed asset. Decision 3 was
   taken knowing this. **Assumption recorded, not verified:** that ICHITA's desktop and web
   licences together permit it. Worth a written answer from CoType before this ships
   externally.
2. **CoType licence, serving.** Serving TH-Aeonik as a webfont redistributes Aeonik outlines
   merged with Bai Jamjuree. This is why Phase 5 builds but does not deploy.
3. **macOS is unverified** and will stay that way until a Mac exists. Do not let the
   construction argument harden into a claim.
4. **Excel row heights** may be an unwelcome surprise at +28%. If it is, the fix is a
   template row-height setting, not a font change — do not re-open the box.
5. **`Σ` and `⌀` aliases** are shape compromises. `∑` is drawn for math and is typically
   larger than `Σ`; `Ø` is a letter, `⌀` a symbol.
6. **Thai-heavy corpus still missing.** How often the worst Thai pairing occurs in real
   prose is unmeasured; the repo's only Thai PDF has 382 Thai characters. At 1537 this
   matters much less than it did at 1200, since clearance is now satisfied.
7. **Third flip of the line-box assertion.** 1610 → 1200 → 1537. The assertion design in
   Phase 1 step 2 exists specifically so the next flip fails loudly instead of quietly.
8. **QC check 6 stays red on purpose** (Thai Bold vs Black separation). Bai has nothing
   heavier than Bold. Do not widen the tolerance.
