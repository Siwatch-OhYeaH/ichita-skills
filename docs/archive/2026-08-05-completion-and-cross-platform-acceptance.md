# Completion note — TH Aeonik as the mixed-language face, plus Greek/math and cross-platform

**Date:** 2026-08-05
**Branch:** `docs/ichita-proposal-design`
**Plan:** `docs/plans/2026-08-05-th-aeonik-line-box-reversal-and-cross-platform.md`
**Status:** Phases 1, 2, 3, 3b, 6 and 7 complete. Phase 5 complete except the two
items that need a machine nobody has. Phase 4 is Siwatch's install and is next.

No post-mortem: this was a decision reversal, not a defect. The two defects found
*during* the work are recorded below under "What went wrong on the way", because
both were cases of a green check hiding a broken artifact and that is this repo's
recurring failure mode.

---

## What shipped

| Phase | Outcome |
|---|---|
| 1 | TH-Aeonik box **1200 → 1537**, split `1169/-368/0`, all three metric sets |
| 2 | TH-Slussen box **1625 → 1602**, `usWin` **1980 → 1602** — a live latent defect |
| 3 | Δ μ Ω harvested, Σ ⌀ aliased, across all 14 faces |
| 3b | **Aeonik itself** rebuilt to the same coverage — Siwatch's mid-session request |
| 5 | Word / PowerPoint / Excel measured; WOFF2 built and verified in Blink; macOS specified |
| 6 | Generators select the font from the document's language, and say which they picked |
| 7 | Two-font rule recorded as brand policy in `ichita-defaults.md` and `docx-standard.md` |

Rebuilt from one code state: **14 TH-Aeonik + 4 TH-Slussen + 14 Aeonik = 32 faces.**

### The line box, and why the two families differ

One rule, two numbers. `box = the Thai's measured need + margin`, carried by `hhea`,
`sTypo` **and** `usWin`.

```
family      worst face                top   tail   need   +margin   box   spare
TH-Aeonik   Black / AirItalic        1139    341   1462      1537  1537     +75
TH-Slussen  Bold / Regular           1185    354   1539      1602  1602     +75
```

Both families now sit at **exactly Leelawadee UI's own spare of +75** — the one Thai
font that gets this right by default, and the font `MARGIN` was derived from. The
262-unit worst-case Thai overlap logged on 08-04 as a permanent accepted cost is
retired.

**The worst upper stack and the worst lower tail are on different faces** in both
families, and all faces share one box, so each split is sized to the family
envelope rather than to any one face. That was not in the plan's framing and it
changes how the split is derived:

- **TH-Aeonik `1169/-368`** — Aeonik's own frame (`1000/-200`) grown symmetrically,
  +169 above and +168 below, so a Latin-only paragraph in a mixed document stays
  optically centred instead of sitting low. Clears the Thai by 30 above, 27 below.
- **TH-Slussen `1233/-369`** — the symmetric growth of Slussen's frame (`usWin`
  `1262/-334`) would be `1265/-337`, and 337 is *below* the Thai's 354, so the Thai
  binds on the bottom and the Latin cannot stay centred. The 63 units of slack go
  over the Thai envelope in proportion to demand. Cost to the Latin: its baseline
  sits 29 units — 0.43 px at 11 pt — higher than in Slussen itself.

`LINEGAP` is 0 in both and must stay 0: `usWin` has no lineGap field, so
`hhea == sTypo == usWin` is only expressible with the gap folded in.

### TH-Slussen's `usWin` was a live latent defect, not tidiness

The built `.otf` carried `usWin` 1980 against a 1625 box, left over from when
`usWin` was read as an ink-containing clip box. **This family has shipped CFF since
08-04, and Word leads a CFF face off `usWin`** — so installing it would have had
Word lead TH Slussen at 1980, a silent **+21.7%** with nothing to do with the
outlines and no decision behind it. The old `.ttf` hid it because the `glyf` branch
ignores `usWin` entirely, which is why the installed font measured 1627 and looked
fine.

---

## Phase 5 — cross-platform acceptance, measured

New: `scripts/win_office_pitch.py` (Word/PowerPoint/Excel via COM),
`scripts/build_th_web.py` (WOFF2 + CSS + headless-browser check).

| Renderer | Reads | TH-Aeonik | Verdict |
|---|---|---|---|
| Word (CFF) | `usWin` | 1537/em expected | harness verified on Aeonik 1197, Slussen 1598 — **needs the install** |
| LibreOffice | `sTypo` | **16.90 pt** at 11 pt vs 16.91 predicted | **PASS**, doc QC 4/4 |
| Blink (Edge headless) | `sTypo`/`hhea` | **1540/em** vs 1537 declared | **PASS** |
| PowerPoint | **nothing** | fixed 1.200 em | see finding |
| Excel | not modelled | autofit row height | reported, not asserted |
| CoreText / macOS | — | — | **UNVERIFIED — no Mac** |

### FINDING: PowerPoint ignores the font's vertical metrics entirely

The plan asked for "the measured pitch equals 1537/em in all three applications".
**That is not achievable in PowerPoint and no font change can make it so.** Five
installed families whose boxes span 1200–1697:

```
font            box    Word    PowerPoint
Aeonik         1200    1197          1200
Bai Jamjuree   1250    1250          1200
Segoe UI       1330    1329          1200
Slussen        1596    1598          1200
Gabriola       1697    1697          1200
```

Word tracks every box. PowerPoint returns 13.200 pt at 11 pt for all five — exactly
1.2 × the point size. Checked against line count too: `BoundHeight` is
13.200 / 26.400 / 79.200 for 1 / 2 / 6 lines in every font. Perfectly linear at
1.2 em per line with no font-dependent term.

**Bound on the claim:** what is proven is that `TextRange.BoundHeight` carries no
font-dependent term. That is strong evidence layout is 1.2 em, not proof — proof
needs a rendered slide measured in pixels, which has not been done.

Two consequences:

1. **Good** — a mixed-language *deck* does not inherit the +28% leading. The
   accepted cost applies to Word and Excel only.
2. **Bad, and open** — **Thai in PowerPoint at single spacing will collide.**
   1.2 em is 1200 units against the 1537 the Thai needs: a 337-unit shortfall,
   precisely the defect the 08-04 box produced in Word. The font cannot fix it, so
   a Thai deck needs explicit line spacing on the text. Not yet verified visually.

### Excel row heights

Measured, autofit: Aeonik **14.50 pt**, Slussen **21.00 pt** — a ratio of 1.448
against a box ratio of 1.330. There is a padding or rounding term no reading of the
metric fields accounts for, so `win_office_pitch.py` **reports** Excel and asserts
only that a taller box does not produce a shorter row. Asserting a number the module
cannot derive would fail for reasons nobody could act on.

The plan's warning stands: if the growth is unwelcome the fix is a template row
height, **not** the font box.

### macOS — the acceptance test, and it has NOT been run

The engineering position is that unifying `hhea`, `sTypo` and `usWin` on 1537 makes
CoreText land on 1537 by construction. **That is a construction argument, not a
measurement**, and it must be labelled that way wherever it appears. The strongest
available evidence for it is Blink agreeing at 1540/em — a different engine that
makes its own choice of field — plus LibreOffice at 16.90 pt. Neither is CoreText.

To run when a Mac exists:

1. Install the 18 `.otf` via Font Book. Confirm no duplicate-family warning.
2. **Pages** — type `สูง` / newline / `ซึ่ง` at 11 pt, default spacing. The lower
   vowel of line 1 must be visibly clear of the upper vowel + tone of line 2.
3. **Pages** — six lines at 11 pt, single. Baseline travel / 5 must be
   **16.91 pt** (1537/em). Anything else falsifies the construction argument.
4. **TextEdit** — same measurement. TextEdit and Pages do not always agree.
5. **Keynote** — the PowerPoint question, restated: does Keynote take its line
   pitch from the font, or use a fixed multiple like PowerPoint does?
6. **Safari** — load `assets/fonts/aeonik-th-web/th-aeonik.css` and compare the
   computed line box against Blink's 1540/em.
7. Record every number. If CoreText disagrees, the unified-metrics strategy is
   wrong and needs re-deriving — do not write it off as a platform quirk.

### Web — built and held

`assets/fonts/aeonik-th-web/`: 8 faces × WOFF2 + WOFF, ~70 KB each, plus
`th-aeonik.css` with `unicode-range` split latin / greek-math / thai.

**NOT CLEARED FOR SERVING.** Publishing it redistributes CoType's Aeonik outlines
merged with Bai Jamjuree to every visitor — a different permission from embedding
them in a PDF. Unresolved; see the plan's Risks 1 and 2.

---

## Phase 3 / 3b — Greek and math

Five codepoints were missing from Aeonik v1.000: `Δ` U+0394, `μ` U+03BC, `Ω` U+03A9,
`Σ` U+03A3, `⌀` U+2300. They matter because Word's Symbol dialog and Insert→Equation
emit the *Greek* codepoints and Excel pastes `µS/cm` with either — so those
characters fell back to a system font mid-line.

`scripts/th_greek.py` is detection-driven, not table-driven: it reads the font's cmap
and closes whatever is actually missing. Slussen v1 already ships Δ μ Ω, so it gets
only the two aliases, and a `harvest_family` gate makes it structurally impossible to
graft an Aeonik outline into Slussen.

**Measurement Siwatch was shown and ruled against:** in the web cut `uni0394` is
point-identical to `uni2206`, and `uni03BC` to `uni00B5` — CoType draws one glyph per
pair — so a cmap alias inside the desktop cut would have been faithful at zero cost
and with no licence exposure. He chose the harvest. Recorded because the code no
longer shows the alternative.

Per face, 14 faces × 3 harvestable codepoints: **6 harvested verbatim** (the web
cut's own faces), **Medium interpolated**, the rest **extrapolated and verified**,
and **6 fell back to the alias** because their derived outline failed the shape gate.

`∆` and `µ` **change appearance** in the harvested faces, because a Greek letter and
its maths twin must share one outline. The harvested outline is written into the
*twin's existing glyph name*, so the source's own kern pairs and GSUB lookups keep
pointing at the glyph the reader now sees.

Specimen for review — `test-output/greek-aeonik-{1-grid,2-running,3-before-after}.png`.
Σ→∑ and ⌀→Ø remain genuine shape compromises and are visible on sheet 2.

### Open question for Siwatch on the specimen

The web cut also **respaces and redraws S, 1, 3, 4, 5, 8, @ and €**, and it exists
for only 6 of the 14 faces. Importing that would put six faces on v2 spacing and
eight on v1 — internally inconsistent, worse than either cut alone. **Not done.**
Coverage only; every vertical metric and all Latin spacing untouched, asserted by
`build_aeonik.assert_untouched()`.

---

## What went wrong on the way

Both were green checks over a broken artifact. Recording them because that is the
pattern, not the specifics.

**1. A stem measurement cannot see a broken outline.** The first build of
`th_greek.py` shipped four faces whose extrapolated `μ` had hairline stems and a bowl
**8× heavier**, plus a truncated right stem. Two checks passed it:

- the **median stem**, because the 0.4–0.6 sample band crosses the bowl, so the
  median landed on target;
- **total ink**, because a too-heavy bowl and too-light stems cancel — Air measured
  1.041 of the twin's ink.

What is wrong is not the average weight, it is that weight is not *consistent within*
the glyph. `_stroke_spread()` — p90/p10 of every run in the whole glyph, against the
twin's — separates cleanly: kept faces 0.93–1.38, rejected 2.12–12.67.

**The check then found two more nobody had spotted:** `Ω` at Air and AirItalic. The
eye that reviewed the specimen went to the four broken `μ` and missed them. A check
that only confirms what someone already saw is not doing any work.

**2. Two harness bugs that each read as a font defect.**

- `win_office_pitch.py` reported "OK across 3 applications" having measured **one** —
  PowerPoint threw outside its `try` and killed the script before Excel, and stderr
  was only surfaced when there were *zero* rows. Partial coverage read as full
  coverage. Now every requested app must return a measurement or the run fails.
- `build_th_web.py` reported the browser computing **1150/em** against the declared
  1537 — which is Arial's box, because a `file://` `@font-face` is cross-origin in
  Blink and `@font-face` loads asynchronously. `document.fonts.check()` returns true
  for a *fallback*, so the load guard passed too. Fixed by serving over HTTP, awaiting
  `document.fonts.load()`, and comparing advance width against a deliberately bogus
  family. Real answer: **1540/em, PASS.** I nearly filed my own bug as a browser
  finding.

---

## Verification state

```
scripts/thai_line_pitch.py --check      OK — both families spare +75
scripts/qc_th_fonts.py                  19/20 — check 6 red ON PURPOSE
scripts/win_latin_parity.py             OK — Latin ink identical to the unit
                                        (149,221 both), wordBox 1537 / 1602,
                                        ratios 1.281 / 1.004
scripts/qc_check_th_font_doc.py         4/4
scripts/win_office_pitch.py             OK — 6 measurements, 3 applications
scripts/build_th_web.py --verify        OK — Blink 1540/em
scripts/build_aeonik.py                 14/14, vertical metrics unchanged
generators                              Latin-only -> Aeonik + Bai, 15.0 pt
                                        mixed -> TH Aeonik alone, 15.35 pt
```

`qc_th_fonts` check 6 (Thai Bold vs Black separation) fails on purpose — Bai has
nothing heavier than Bold. **Do not widen the tolerance.**

---

## Next

1. **Phase 4 — install (Siwatch).** Uninstall the obsolete faces first, then install.
   Close Word, PowerPoint **and Excel** first; a locked file is what produced
   `TH-Aeonik-Regular_0.ttf` and left a stale file registered under the family name.
   Install through Windows Settings. Do **not** run
   `fix-th-fonts.sh --apply-system --restart`; `--check` is a fine read-only report.
   `%LOCALAPPDATA%\Microsoft\Windows\Fonts` shadows `C:\Windows\Fonts`.
   - 18 merged faces from `assets/fonts/{aeonik-th,slussen-th}`
   - **14 Aeonik faces from `assets/fonts/aeonik-fixed`, over the current Aeonik.**
     Same family name; `nameID5` reads `Version 1.001; ICHITA Greek/math coverage`.
2. **Then re-run** `win_office_pitch.py` and `win_latin_parity.py` against the
   installed set — Word's 1537 is currently predicted from the file, not measured
   in Word.
3. **Review the specimen** — the `∆`/`µ` appearance change, and the S/1/3/4/5/8/@/€
   spacing question above.
4. **Thai in PowerPoint.** Set two Thai lines at single spacing in a deck and look.
   Expected to collide; the fix is document-side, not font-side.
5. **Commit and push.** The branch has never been pushed past `52b4160`.
6. Still unmeasured: how often the worst Thai pairing occurs in real prose. Matters
   much less at 1537 than at 1200, since clearance is now satisfied.
