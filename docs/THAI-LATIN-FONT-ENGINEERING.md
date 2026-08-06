# Building a merged Thai + Latin font — the complete record

**This is the only font document you need to read.** It supersedes six post-mortems
and two plans covering 2026-08-01 → 2026-08-05, archived under `docs/archive/`. Those
files remain for provenance; nothing in them is required reading, and several of their
conclusions were later falsified — which is recorded here.

**Scope:** TH Aeonik (Aeonik Latin + Bai Jamjuree Thai, 14 faces) and TH Slussen
(Slussen + Bai, 4 faces). Everything below was measured on this machine unless marked
otherwise.

---

## 0. The rules that would have saved the most time

Nine sessions, roughly thirty defects. Every one of these was learned by losing a day
to it.

1. **Word on Windows is the acceptance renderer. Linux cannot validate it.** HarfBuzz
   infers what Uniscribe demands, and FreeType does not reproduce Windows'
   per-format rasterisers. A green Linux suite is not evidence. `powershell.exe` from
   WSL reaches GDI, DirectWrite and Office COM — measure there.
2. **Never read a metric field to predict leading.** Which field a renderer uses
   depends on the outline format and a bit. Use `win_latin_parity.word_line_box()`.
   §3 and §7.
3. **Look at the artifact.** Render it to PNG or PDF and *look*. Four separate defects
   were invisible to every numeric check and obvious on sight.
4. **A green test is a claim about the test, not the font.** The acceptance suite once
   passed *because* the font was wrong (§10). Before trusting a check, verify it fails
   on a known-bad input.
5. **An average cannot see a broken shape.** A median stem and a total-ink check both
   passed a glyph with hairline stems and an 8× bowl. Measure distributions.
6. **A comment asserting a property is a test that was never written.** Three times a
   comment stated the correct invariant directly above code violating it.
7. **Siwatch's visual reports are measurements to explain, not claims to verify.**
   Every one has been correct. When his report and a passing test disagree, the test
   is wrong.
8. **Rebuild all faces from one code state before running QC.** Committed fonts
   disagree with the committed builder, and a stale `~/.local/share/fonts` silently
   feeds the doc QC.
9. **Name the benchmark before moving a ratio.** "Too bold" and "too light" were both
   true — against Bai and against Aeonik respectively. Write down which two things
   were put side by side.
10. **Fix it in the font, not in a document setting.** The acceptance test is someone
    typing in plain Word, where no generator is around to set a paragraph property.
    The one genuine exception is PowerPoint (§7).

---

## 1. The product decision — the font follows the document's language

**Siwatch, 2026-08-05.** This is brand policy, recorded in
`assets/brand/ichita-defaults.md` §4 and `docx-standard.md`.

| Document | Face | Line box |
|---|---|---|
| English only | **Aeonik** | 1200 |
| Thai, or Thai + English mixed | **TH Aeonik** | **1537** |

**Why this exists.** Thai stacks a base consonant, an upper vowel and a tone above the
ascender, then hangs a below-vowel under the baseline. The worst combinations need
1537/1000 em against Aeonik's 1200. **One font has one `hhea`**, so "leads exactly like
Aeonik" and "keeps two Thai lines apart" are not jointly satisfiable. Three attempts:

- **2026-08-03** box 1540, sized to the Thai → Latin-only lines led 28% loose. Rejected.
- **2026-08-04** box 1200, Aeonik's exactly → worst Thai stacks overlapped 262 units
  (3.9 px at 11 pt). Shipped as an accepted cost.
- **2026-08-05** box 1537 **and English-only documents use actual Aeonik** → nothing
  has to match Aeonik's box, so nothing has to fit inside it. The conflict dissolves.

**Accepted cost, explicitly:** English-only paragraphs *inside a mixed document* lead
~28% wider. Do not "fix" this — fixing it is what produced the 08-04 defect.

**Two consequences that are easy to miss:**

- **Coverage must be identical between the two faces.** A character in one and absent
  in the other falls back to a system font depending only on whether the document
  happens to contain Thai. Hence `build_aeonik.py` (§5).
- **Never mix the two faces in one document** — different line boxes, so text reflows
  at the boundary.

---

## 2. The build pipeline, and why each step exists

`scripts/build_th_aeonik.py` / `build_th_slussen.py`. Each step below was added
because something broke without it.

```
0   CFF -> glyf            intermediate working format; every step is written against glyf
0a  thin/embolden Thai     changeWeight to hit the target stem
0b  scale Thai from ink    solve the factor from measured x-height, not the nominal
0c  apply the scale
0d  mark scale             1.000; do not change (§4)
1   copy Thai glyphs       cmap glyphs AND GSUB-only variants
2   merge GPOS/GDEF/GSUB   union, same-tag features merged into a fresh FeatureRecord
3   metadata               RIBBI naming, OS/2, per-weight nameID1
3b  Thai GDEF + U+25CC     Uniscribe prerequisites Bai does not supply (§8)
3c  seat Thai on baseline   changeWeight grows outlines DOWNWARD too
3d  raise upper marks      iterative lift to a 72/1000 em clearance target
4   Thai OS/2 range bits
4b  Greek/math coverage    scripts/th_greek.py (§5)
5   vertical metrics       hhea = sTypo = usWin, one box (§3)
6   sort Coverage tables   by glyph ID — spec requirement Uniscribe enforces
6a  clean Mac cmap         drop codes > 255 from the (1,0) subtable
6b  re-sync hmtx lsb       to xMin, BEFORE the CFF conversion
7   glyf -> CFF            the Latin source's own CFF table, Thai appended (§6)
7b  advance single-source   charstring width == hmtx everywhere
8   Thai clearance         per face, measured on the SAVED file
```

**Non-obvious ordering constraints:**

- **Step 6b must run before step 7, and not because CFF reads `lsb`.** fontTools' glyf
  glyph set applies the `(lsb − xMin)` offset *while drawing*, and the CFF pen draws
  through it. Deleting this step on the correct reasoning that "CFF ignores `hmtx`
  lsb" collapsed `ษ`'s counter from 55.2 to 3.9 — the loop filled in solid.
- **Step 0b re-solves the scale from ink per weight**, so a nominal 0.914 lands
  anywhere in 0.905–0.941. Anything downstream that assumes the nominal is wrong.
- **Step 7 takes the Latin's CFF table wholesale.** See §6.
- **Step 2's first two implementations were both wrong.** "Skip the script if it
  already exists" discarded Bai's entire Thai feature set on the italics (Aeonik's
  italics *do* declare a Thai script). "Append features alongside" produced two `mark`
  features in one LangSys; consumers take the first, so Aeonik's empty stub won and
  Thai mark positioning stayed dead.

---

## 3. Vertical metrics — the hardest part, and where most of the time went

### The rule, finally

**box = the Thai's measured need + margin, carried by `hhea` AND `sTypo` AND `usWin`.**

```
family      worst upper   worst tail   need   +margin   box    split
TH-Aeonik    1139 Black    341 AirIt   1462      1537   1537   1169/-368/0
TH-Slussen   1185 Bold     354 Reg     1539      1602   1602   1233/-369/0
```

`MARGIN = 75` is Leelawadee UI's own spare — the one Thai font that gets this right by
default — and is ~1 px at 11 pt / 96 dpi. Both families now sit at exactly +75.

**The worst upper stack and the worst lower tail are on DIFFERENT FACES**, and all
faces share one box (bolding a word must not change line height), so the split is
sized to the family envelope, never to one face.

**How the slack is spent:** grow the Latin source's own frame symmetrically, so a
Latin-only paragraph stays optically centred rather than sitting low. TH-Aeonik:
Aeonik's `1000/-200` + 169/168. TH-Slussen: that would give `1265/-337` and 337 is
below the Thai's 354, so the Thai binds and the slack goes proportional to demand
instead — costing the Latin 0.43 px of rise.

**`LINEGAP` is 0 and must stay 0.** `usWin` has no lineGap field, so
`hhea == sTypo == usWin` is only expressible with the gap folded into ascent/descent.
This is why Slussen's own 166-unit gap does not survive into the merged face.

### Why unifying all three is the whole cross-platform strategy

Which vertical field a renderer consults is **not fixed** (§7). Rather than learning
every renderer's rule, set all three to the same number so the font yields that number
whichever field is read. That is what makes Word, LibreOffice, Blink and (by
construction, unverified) CoreText agree.

### `usWin` is NOT a clip box

Believed for three sessions; false. Measured ink extent against `usWin` on installed
fonts: Tahoma +246, Segoe UI +379 — both draw well outside their own `usWin` and
neither clips in DirectWrite-era Word. **Thai marks are meant to overflow the line box
into the leading above**, where Latin ascenders leave the space empty. Sizing the box
to contain the ink cost 42% of extra leading (1710 against 1200) and was the
2026-08-02 defect.

Corollary: for a CFF face, a `usWin` wider than the line box is **not headroom, it is
silent extra leading**. TH-Slussen carried `usWin` 1980 against a 1625 box until
2026-08-05 — a latent +21.7% that the old `.ttf` hid because `glyf` ignores `usWin`.

### The falsified idea: shrink the marks to fit

`scripts/solve_mark_scale.py` swept the real builder:

```
mark scale   top   bottom   need   required(+75)
   1.00     1139    -323    1462       1537
   0.80     1096    -258    1354       1429
   0.70     1078    -258    1336       1411
   0.60     1061    -258    1319       1394
```

A **25% mark reduction buys 35 units.** Two floors, neither a mark: `raise_upper_marks`
re-lifts a smaller mark to hold its one-pixel target, and `bottom` floors on `ฐ`'s
**consonant tail**. The floor is ~1383. **1200 is unreachable for Thai at any mark
size.** `MARK_SCALE` stays 1.000 — shrinking costs tone-mark legibility (่ ้ ๊ ๋ differ
by small strokes) and buys nothing.

### Reference measurements

```
font            line box   worst stack   spare
TH-Slussen          1602          1527     +75
TH-Aeonik           1537          1462     +75
Leelawadee UI       1330          1255     +75
Sarabun             1300          1582    -282
Bai Jamjuree        1250          1564    -314
```

Sarabun — the nominated reference for correct Thai engineering — is *worse* than our
faces on pure geometry; it escapes because `ส` and `ซ` differ in width so the marks
miss sideways. Leelawadee buys its comfort with markedly smaller marks (upper vowel
201 vs our 273, tone 129 vs 158, lower vowel 182 vs 269), not a taller box.

---

## 4. Weight and size harmonisation

**The rule:** Thai is sized to the **Latin x-height** and weight-matched by **measured
stem** at ~0.89 of the Latin. **Aeonik's Latin is the benchmark, not Bai** — Siwatch
ruled on this, and Regular now runs ~+11% over Bai's own Regular by design.

**Weight is two constraints, not one.** Stem *and* counter aperture. TH-Aeonik-Bold
once shipped with 7.8 units of aperture — 0.11 px at 11 pt, i.e. `ฃ` and `ธ` as solid
blobs — while passing the stem check at 0.974 of the Latin. `APERTURE_FLOOR` exists
because emboldening buys stem and *spends* aperture. Below ~47 units (0.7 px) a
counter fills in under any rasteriser.

**The ladder is capped, and the cap is real.** Bai has nothing heavier than Bold, so
`qc_th_fonts.py` **check 6 (Thai Bold vs Black separation) fails on purpose. Expected
state is 19/20. Do not widen the tolerance.** Balanced per-weight and
Bold-distinct-from-Black are mutually exclusive from this source. The taper
(`WEIGHT_RATIO` 900 → .745) states the *reachable* number rather than a target the
counter floor forbids.

**`changeWeight` under-delivers on negative amounts** — roughly half the requested
thinning reaches the outline — so the embolden→stem slope differs by sign. It also
**grows outlines downward**, which drags Thai off the Latin baseline worse the bolder
the weight; hence step 3c. `solve_weight_table.py` iterates a secant on the shipped
measurement rather than modelling any of this.

**Never pair by weight name.** Matching Bai Regular to Aeonik Regular left Thai 25%
lighter than the Latin beside it. Pairing lives in `th_thai_prep.BUILD_TABLE`.

---

## 5. Glyph coverage — Greek and math

Aeonik v1.000 (desktop, the cut Word uses) lacks `Δ` U+0394, `μ` U+03BC, `Ω` U+03A9,
`Σ` U+03A3, `⌀` U+2300. This matters because **Word's Symbol dialog and
Insert→Equation emit the Greek codepoints**, and Excel pastes `µS/cm` with either — so
those characters fell back to a system font mid-line in the most technical documents
ICHITA produces.

`scripts/th_greek.py` is **detection-driven**: it reads the cmap and closes what is
actually missing. Slussen v1 already ships Δ μ Ω, so it gets only the two aliases, and
a `harvest_family` gate makes grafting an Aeonik outline into Slussen structurally
impossible.

**Measured, and Siwatch ruled against the cheap path:** in the web cut `uni0394` is
*point-identical* to `uni2206`, and `uni03BC` to `uni00B5` — CoType draws one glyph per
pair. An alias inside v1 would have been faithful at zero cost and no licence exposure.
He chose to harvest the web cut's outlines. `uni03A9` and `uni2126` genuinely differ
(19 vs 32 segments) but render indistinguishably (ink within 0.4%).

Result per family, 14 faces: 6 harvested verbatim, Medium interpolated, the rest
extrapolated **and verified**, 6 fell back to the alias. `Σ` and `⌀` are aliased to `∑`
and `Ø` as acknowledged shape compromises.

**`∆` and `µ` changed appearance** in the harvested faces, because a Greek letter and
its maths twin must share one outline. The harvested outline is written into the
**twin's existing glyph name**, so the source's own kern pairs and GSUB lookups keep
pointing at the glyph the reader now sees.

Specimen sheets are **not committed** — regenerate them, they take seconds:

```bash
python3 scripts/build_greek_specimen.py     # -> test-output/greek-aeonik-*.png
```

Sheet 1 is the grid of all five codepoints beside their twins at all 14 weights,
sheet 2 is running text (`Δp`, `µS/cm`, `m³/h`, `H₂O`, `±`, `≤`, `Ω`), sheet 3 is
before/after for the two glyphs that changed. FreeType render — **judge shape there,
never weight or leading**; for those use `win_latin_parity.py`.

### The extrapolation defect, and the check that catches it

First build shipped four faces whose `μ` had **hairline stems and a bowl 8× heavier**,
plus a truncated right stem. Two checks passed it:

- **median stem** — the 0.4–0.6 sample band crosses the bowl, so the median was on target;
- **total ink** — a heavy bowl and light stems cancel; Air measured 1.041 of the twin's.

`_stroke_spread()` — p90/p10 of every ink run in the whole glyph, against the twin's —
separates cleanly: kept 0.93–1.38, rejected 2.12–12.67. **It then found two more
nobody had spotted** (`Ω` at Air and AirItalic). Simple shapes survive long
extrapolation; `Δ` (9 points, all corners, three masters) is clean everywhere, `μ` has
a bowl and only a two-master basis.

**Two Aeonik cuts, and do not migrate wholesale.** v2 (web) has box **1140** vs v1's
1200 and respaces `x 1 5 S 3 4 8 @ €`; it covers only 6 of 14 faces. Only the five
codepoints were taken; every vertical metric and all Latin spacing stayed v1, asserted
by `build_aeonik.assert_untouched()`.

---

## 6. Format is part of the vertical metrics

**Ship the Latin source's own format.** Windows rasterises CFF and TrueType through
different engines, so a merged font in a different format from its source cannot
render that Latin identically no matter how exact the outlines are. Measured in
DirectWrite at 11 pt, identical outlines and advances:

```
Aeonik      .otf/CFF    stems 2,1 px   ink 11,056
TH Aeonik   .ttf/glyf   stems 1,1 px   ink  9,310   -15.8%
Slussen     .otf/CFF    stems 2,2 px   ink 12,485
TH Slussen  .ttf/glyf   stems 2,2 px   ink  9,940   -20.4%
```

Siwatch reported it as "TH Aeonik is slightly thinner than Aeonik, especially
Regular". **Nothing on Linux can see this.**

**Take the Latin's CFF table wholesale** (`th_cff.convert_to_cff`), appending only
Thai. A redraw loses three things: the charstrings themselves (0 of 656 outlines differ
taking the table, 656 of 656 differ on a redraw), the Private dict's **BlueValues**,
and **hint operators inside the charstrings** — Slussen carries 2712 across 1068
glyphs, which the format flip discarded outright. Aeonik carries zero, so it never had
anything to lose there.

**`thai_names` must be passed explicitly** and cannot be inferred from "absent from the
Latin CFF": Aeonik already owns `uni0E3F` (baht), so treating every known name as Latin
left Aeonik's baht charstring against Bai's advance — a 638-vs-622 disagreement. The
harvested Greek names must be in the same set for the same reason.

**Assert `charstring width == hmtx` everywhere.** CFF can state an advance twice.
Microsoft Print to PDF builds the `/W` array from the charstring, so a disagreement
renders correctly in Word and *shreds the printed PDF* — Thai marks carry a zero `hmtx`
advance, and given a real one in `/W` every tone mark detaches. `glyf` made this
unrepresentable; CFF makes it representable again, so it is asserted.

**Also:** Word's PDF **export** drops CFF — `.otf` substitutes to Calibri on export
only, while screen layout is fine. An embedded-font list is therefore not acceptance
evidence.

---

## 7. Which renderer reads which field — the table that matters

Measured 2026-08-05 across 15 installed families for Word, then extended.

| Renderer | Reads | Evidence |
|---|---|---|
| **Word**, CFF | `usWin` | Slussen 1595 (usWin 1596, hhea 1512); TH Aeonik pre-fix 1.504× = 1800/1200 |
| **Word**, glyf + USE_TYPO_METRICS | `sTypo` (== hhea here) | Bai 1250 with usWin **1786**; Sarabun 1300 with usWin 1853 |
| **Word**, glyf without the bit | `max(hhea, usWin)` | Arial 1150, DilleniaUPC 1305 (hhea only 600), Ink Free 1236 (usWin > hhea) |
| **LibreOffice** | `sTypo` | TH Aeonik 16.90 pt measured vs 16.91 predicted |
| **Blink** (Edge/Chrome) | `sTypo`/`hhea` | TH Aeonik **1540/em** vs 1537 declared |
| **PowerPoint** | **nothing** | fixed 1.2 em — see below |
| **Excel** | not modelled | autofit row height, with a padding term |
| **CoreText / macOS** | — | **UNVERIFIED — no Mac** |

Encoded in `win_latin_parity.word_line_box()`. **A format flip silently relocates the
spacing control.** Never read a field directly to predict leading.

### PowerPoint ignores font metrics entirely

Five installed families whose boxes span 1200–1697:

```
font            box    Word    PowerPoint
Aeonik         1200    1197          1200
Bai Jamjuree   1250    1250          1200
Segoe UI       1330    1329          1200
Slussen        1596    1598          1200
Gabriola       1697    1697          1200
```

Word tracks every box; PowerPoint returns 13.200 pt at 11 pt for all five — exactly
1.2 × the point size. `BoundHeight` is 13.200 / 26.400 / 79.200 for 1 / 2 / 6 lines in
every font: perfectly linear, no font-dependent term.

**Bound:** this proves `BoundHeight` carries no font-dependent term. Strong evidence
layout is 1.2 em, not proof — proof needs a rendered slide measured in pixels.

- **Good:** a mixed-language deck does not inherit the +28% leading.
- **Bad, and open:** **Thai in a deck at single spacing will collide** — 1200 against
  1537, the same shortfall that produced the 08-04 defect in Word. **The font cannot
  fix this**; a Thai deck needs explicit line spacing. This is the one place where
  "fix it in the document" is correct, and it is not a choice.

### Excel

Autofit row height: Aeonik **14.50 pt**, Slussen **21.00 pt** — ratio 1.448 against a
box ratio of 1.330. A padding or rounding term no metric field accounts for, so
`win_office_pitch.py` **reports** Excel and asserts only that a taller box does not
produce a shorter row. If the growth is unwelcome the fix is a **template row height,
not the font box**.

---

## 8. Uniscribe and Word-specific traps

- **Bai supplies no GDEF classes and no U+25CC.** Uniscribe needs an explicit GDEF
  class on every Thai glyph and a dotted circle to hang orphaned marks on; HarfBuzz
  infers both from Unicode and so is structurally blind to their absence. Without them
  an isolated or repeated `า` will not type. Step 3b.
- **Repeated vowels refusing to type is `Options.SequenceCheck`, not GDEF.** Word
  validates Thai sequences and rejects invalid ones. **Separate typing from rendering
  before diagnosing anything.**
- **Coverage tables must be sorted by glyph ID.** 29 were not. `fontTools.subset`
  emitted `Coverage is not sorted by glyph ids` ~60 times as a free oracle. This sort
  was *dead code* against the shipped fonts and became load-bearing the moment the
  lookup-union defect was fixed, because retaining the Latin lookups moved the glyph
  IDs the Coverage tables index. **A guard measuring 0 today is not evidence it can be
  dropped.**
- **`nameID2` may only be Regular / Bold / Italic / Bold Italic**, so a family sharing
  one `nameID1` holds at most four faces. Medium and SemiBold each need their own
  `nameID1`, with `nameID16/17` putting them back together. Three TH-Slussen weights
  once all announced `TH Slussen` + `Regular` and Windows could only offer one.
- **The ribbon font box cannot express a Latin/Complex-Script split** — it calls
  `Font.Name`, which overwrites both slots at once. Only Ctrl+D, a style, or COM can
  set them independently.
- **`NormalTemplate.OpenAsDocument()` hangs while Word is running** — no dialog, no
  error, blocks forever. Word holds `Normal.dotm` for the whole session.

---

## 9. Installing on Windows

**Siwatch installs via Windows Settings. Never prescribe
`fix-th-fonts.sh --apply-system --restart`.** `--check` is a fine read-only report.

- **`%LOCALAPPDATA%\Microsoft\Windows\Fonts` shadows `C:\Windows\Fonts`.** Give
  per-layer facts.
- **Close Word, PowerPoint AND Excel first.** A locked file is what produced
  `TH-Aeonik-Regular_0.ttf` and left a *stale file registered under the family name* —
  so a parity result measured against the wrong file. `win_latin_parity` reports the
  resolved path for exactly this reason.
- **Uninstall obsolete faces before installing**, including `_0` duplicates.
- Word caches font data per session; a full restart is required, not just a reopen.
- If a fresh print is still stale after a reboot, the remaining suspect is
  `FNTCACHE.DAT`.
- **`win_office_pitch.py` can leave orphaned Office processes, and they lock fonts.**
  The COM probe quits each application in a `finally`, but a hard error or a killed
  Python process orphans `WINWORD.EXE` / `POWERPNT.EXE` / `EXCEL.EXE` with **no window**
  — so they are invisible in the taskbar and Alt-Tab while still holding font files
  open. Encountered 2026-08-05: two orphaned `WINWORD.EXE` blocked a font install with
  the applications apparently closed. This is the same shape as the old install-script
  bug where the Office guard matched **process names rather than open documents**.
  **Check before every install, not after a failure:**

  ```bash
  powershell.exe -NoProfile -Command "Get-Process WINWORD,POWERPNT,EXCEL \
    -ErrorAction SilentlyContinue | Select Name,Id,MainWindowHandle"
  # MainWindowHandle 0 = orphan, safe to kill:
  powershell.exe -NoProfile -Command "Stop-Process -Name WINWORD,POWERPNT,EXCEL -Force"
  ```

  Font Cache service operations need admin, and an installed system-level font offers
  only *Hide* rather than *Delete* in Settings — so an orphan holding a lock is easier
  to hit than to diagnose.

Three bugs in the install tooling, worth remembering as a pattern: the pending-delete
queue was scoped to the wrong file set, `$null` was written where `NULL` was meant, and
the Office guard matched **process names rather than open documents** — blocking the fix
for a whole session while the user correctly said the applications were closed. **Two of
those bugs cancelled and produced `exit=0` with an empty queue.** A script reporting
success while producing no effect should be as alarming as one reporting failure.

---

## 10. How the tests failed — read this before writing a check

**The acceptance suite once asserted the defect.** `compare_th_*.py` measured merged
Thai against **Bai Jamjuree** and passed when they were pixel-identical. But Bai's Thai
is drawn to sit beside Bai's own Latin, so "identical to Bai" *is* the unscaled,
weight-mismatched state the pipeline exists to correct. **The tighter it passed, the
more wrong the font was**, and two post-mortems cite its "0 differing pixels" as proof
of success. The reference must be the Latin the Thai shares a line with.

Other test-design failures, each of which shipped a defect:

- **Measure over the reachable set, not the convenient one.** The clip box was sized
  from Thai ink over the **cmap**; the glyphs that overflowed were GSUB-only `.small`
  variants — invisible to any cmap walk, and the tallest glyphs in the font. "Which
  glyphs can appear" is answered by **shaping**.
- **Verify a guard fails before trusting it passes.** `check_cff_widths()` was run
  against the pre-fix fonts and confirmed to fail (363 bad glyphs) before being
  accepted. A guard never observed failing proves nothing.
- **Set a tolerance from the distribution you are bounding.** A Latin limit was set
  from a *mean across all glyphs* while the test compared *per glyph and size*, where
  p99 was 11.70 and max 16.12. It failed instantly on a correct build.
- **A test that cannot distinguish a defect from a format change is not a test.**
  Demanding pixel-exact Thai across a TrueType→CFF flip produced 3008 failures, nearly
  all noise, burying two real signals.
- **When one artifact's test gets stronger, re-run it against its siblings.** The clip
  check written for Slussen pointed back at TH-Aeonik — which had passed its own
  test — and caught `usWinAscent` 1050 against ink of +1225 on all six weights.
- **Pin both the number and the relationship.** Pinning only the number let the box sit
  337 units under the Thai with everything green. Pinning only the relationship is
  unreviewable — "the line box equals the Latin source's" read as a principle for two
  days while encoding a defect, and four checks asserted it. `assert_line_box()` +
  `assert_thai_clears()` now do both.
- **Report the coverage you achieved, not the coverage you asked for.**
  `win_office_pitch.py` once reported "OK across 3 applications" having measured one.

---

## 11. Tooling traps

- **`roundTolerance=0` in fontTools means `noRound`** — fractional coordinates, the
  opposite of what it reads like. Use `0.5` for integers.
- **`T2WidthExtractor`'s first argument is the LOCAL SUBRS index**, not the charstrings
  index. Passing charstrings made `callsubr` execute arbitrary glyph programs — which
  underflowed on Slussen and, worse, **silently PASSED on Aeonik**.
- **`TTGlyphPen`-built glyphs carry no bounds until `recalcBounds()`**, and both the
  lsb sync and the CFF conversion read `xMin`.
- **Loading WPF flips the PowerShell process to DPI-aware**, so on a 150%-scaled
  display every subsequent GDI+ measurement inflates by 144/96 — reading as "TH Aeonik
  is 50% bigger", a defect that does not exist. Measure each engine in **its own
  process**, and size GDI in pixels with `PageUnit = Pixel`.
- **PowerShell 5.1 mis-parses a `.ps1` without a UTF-8 BOM.** Pass
  `-EncodedCommand` (base64 UTF-16LE) — no file, so no encoding to get wrong.
- **`PrivateFontCollection` cannot load CFF on .NET Framework**, so off-disk
  measurement is DirectWrite-only. Not a real gap: DirectWrite is what Word 2016+ uses.
- **PowerShell writes its progress stream to stderr as CLIXML.** Not an error; treating
  it as one made every successful run report a probe failure.
- **`file://` `@font-face` is cross-origin in Blink** and refused even with
  `--allow-file-access-from-files`; and `@font-face` loads **asynchronously**. Serve
  over HTTP and await `document.fonts.load()`. **`document.fonts.check()` returns true
  for a fallback** — compare advance width against a deliberately bogus family instead.
  Getting this wrong reported the browser computing 1150/em (Arial's box) against a
  declared 1537, which was very nearly filed as a browser finding.
- **Use the system `python3`, never `venv_fonts/bin/python`** — the venv lacks numpy,
  scipy and fitz and cannot run the build at all.
- **`qc_check_th_font_doc.py` only READS `test-output/th-font-qc.pdf`.** Run
  `build_th_font_qc.py` first or you measure last night's font.

---

## 12. Ruled out — do not re-propose

- **The Latin/Complex-Script two-font split inside one document.** Siwatch: *"solve it
  with the font engineering, not by set up two separate fonts."* It works — measured,
  `ascii=Aeonik` + `cs=TH Aeonik` gives Latin-only 13.20 pt and mixed 16.92 pt — and
  he ruled against it. Superseded anyway by §1, which solves the same problem by
  choosing the face per document.
- **Shrinking Thai marks to fit a Latin box.** Measured; buys 35 units for a 25%
  reduction; floor ~1383 against 1200. §3.
- **Widening `qc_th_fonts` check 6's tolerance.** It fails on purpose. §4.
- **Sizing the line box to contain the Thai ink.** Cost 42% of extra leading. §3.
- **Migrating to the v2 web cut wholesale.** Box 1140, respaced digits, 6 of 14 faces. §5.
- **LibreOffice as a stand-in for the Windows print path.** Its print and export
  outputs were byte-identical — no signal, and it briefly suggested nothing was wrong.

---

## 13. Current state — 2026-08-05

**Shipping:** 14 TH-Aeonik + 4 TH-Slussen + 14 Aeonik faces, all `.otf`/CFF, rebuilt
from one code state.

```
scripts/thai_line_pitch.py --check   OK — both families spare +75
scripts/qc_th_fonts.py               19/20 — check 6 red ON PURPOSE
scripts/win_latin_parity.py          OK — Latin ink identical to the unit (149,221
                                     both), wordBox 1537 / 1602, ratios 1.281 / 1.004
scripts/qc_check_th_font_doc.py      4/4 — LibreOffice 16.90 pt vs 16.91 predicted
scripts/win_office_pitch.py          OK — 6 measurements, Word/PowerPoint/Excel
scripts/build_th_web.py --verify     OK — Blink 1540/em
scripts/build_aeonik.py              14/14, vertical metrics unchanged
generators                           Latin-only -> Aeonik + Bai (15.0 pt)
                                     mixed -> TH Aeonik alone (15.35 pt)
coverage parity                      all 5 codepoints in all 14 faces, both families
```

**Generators use the fonts as of 2026-08-05.** `TH_AEONIK_MODE = False` was hardcoded
until then, so five days of font work reached nothing generated. `html_to_docx` was
worse — it selected unified mode from *installation*, silently giving English-only
briefs the 1537 box. All three (`md_to_docx.py`, `html_to_docx.py`,
`docx_helpers.resolve_font()`) now select from content and **log the choice**.

### Directory layout, reconciled 2026-08-06

The font directories were renamed to a consistent `th-` prefix, and the Aeonik build
was promoted over its own source. Both had been left uncommitted, so 80 files showed
as deleted and every path constant in `scripts/` pointed at a directory that no longer
existed — `qc_th_fonts.py` could not run at all.

| Was | Is | Note |
|---|---|---|
| `aeonik-th/` | `th-aeonik/` | |
| `slussen-th/` | `th-slussen/` | |
| `aeonik-th-web/` | `th-aeonik-web/` | |
| `aeonik-woff/` | `aeonik-web/` | Greek harvest source only |
| `aeonik-fixed/` | `aeonik/` | the v1.001 build is now *the* Aeonik |
| `aeonik/` (v1.000) | **not in the repo** | pristine source, kept locally |

The last two rows are the one that can bite. `aeonik/` used to be CoType's pristine
v1.000 and is now our v1.001 Greek/math build, so `build_aeonik.py` would have read
its own output as its input.

**The pristine source is deliberately not committed** — Siwatch, 2026-08-06. Two
directories both named Aeonik, with identical filenames and the same family name,
is a coin-flip over which one somebody installs, and the wrong one has no Δ μ Ω.
It lives in a local folder and the old cuts are archived outside git.

`build_th_aeonik.AEONIK_LOCAL` therefore points at `assets/fonts/aeonik-v1000/`,
which is **git-ignored** — a drop point, not a tracked directory. Both builders
call `require_aeonik_source()` before doing any work and stop with the paths they
looked in. They must never fall back to `aeonik/`: an unavailable source is
recoverable, a quietly wrong one is not.

### Thai through PDF, measured 2026-08-06

Three results from building `skills/ichita-convert`, all on a Thai+Latin
fixture rendered from the current build.

**1. The May PDF's Thai corruption does not reproduce.** That file extracts
`น˗˓าตาล` for `น้ำตาล`, tone marks arriving as U+02D7/U+02D3. A DOCX rendered
through LibreOffice headless and extracted with pymupdf returns **311 of 311
Thai characters, NFC-identical to source**. The old build's glyph naming was
the cause, as suspected; the current build maps `U+0E49 → uni0E49` cleanly.
The check now runs on every inbound conversion
(`md_clean.assert_thai_intact`), so a regression fails loudly.

**2. LibreOffice embeds the merged faces as Type1C and gets the text layer
right.** Measured line pitch read back out of the PDF is **15.4 pt at 10 pt
body = 1.54 em**, against TH Aeonik's declared 1537 box — an independent
confirmation that the font's own metrics drive the layout, from a renderer
that is not Word.

It does re-resolve the Latin script slot: the DOCX sets `w:ascii`/`w:hAnsi`/
`w:cs` to `TH Aeonik` on every run, and the PDF embeds `Aeonik-Regular` for the
Latin runs anyway. TH Aeonik is installed and `fc-match` resolves it, so this
is LibreOffice's slot handling, not a missing font. Both are brand faces and
the pitch stays uniform, so it is noted, not chased — Word is the acceptance
renderer.

**3. weasyprint writes a wrong `ToUnicode` for Thai — and the render is
correct.** Every `า` (U+0E32) extracts as `ำ` (U+0E33). A 160 dpi crop shows
the glyphs are right; only the text layer is wrong, so search, copy-paste and
re-ingestion return corrupted Thai while the page looks perfect.

Mechanism: HarfBuzz decomposes ำ into ํ + า for shaping, so the า glyph is
reached from two source codepoints. `ToUnicode` is keyed by glyph id and the
last write wins — the whole subset ends up carrying one entry,
`<02c1> <0e33>`.

**Not the font.** TH Aeonik's cmap has exactly one codepoint per glyph and
**zero** Thai glyphs reachable from more than one, checked with fontTools.
**Pre-decomposing ำ to ํ + า in the source does not fix it** — the extracted
text then comes back decomposed and NFC will not recompose it, because U+0E33
has no canonical decomposition. 319 characters out for 311 in. Falsified; do
not re-propose.

Consequence: weasyprint is fine for English-only delivery and for Thai that
only has to be looked at. Use LibreOffice where the Thai must be searchable.

**4. Word COM is not automatable unattended from WSL.** Two attempts, both
hung past 100 s with `Visible = false` and both orphaned a windowless
`WINWORD.EXE` — the §9 failure exactly. Both cleaned up. Run it attended with
Word visible, and check for orphans before and after.

### Open items

1. **Install on Windows** (Siwatch) — 18 merged faces from
   `assets/fonts/{th-aeonik,th-slussen}`, plus **14 from `assets/fonts/aeonik`
   over the current Aeonik** (same family name; `nameID5` reads
   `Version 1.001; ICHITA Greek/math coverage`). §9 for the traps.
2. **Then re-run `win_office_pitch.py` and `win_latin_parity.py`** against the
   installed set. Word's 1537 is currently predicted from the file, not measured in Word.
3. **Review the specimen** — `test-output/greek-aeonik-*.png`. The `∆`/`µ` appearance
   change, and whether to also take the web cut's respaced `S 1 3 4 5 8 @ €` (not done;
   it covers only 6 of 14 faces and would split the family).
4. **Thai in PowerPoint** — expected to collide at single spacing. Verify visually; the
   fix is document-side. §7.
5. **macOS is UNVERIFIED** and stays that way until a Mac exists. The acceptance test
   is written in `docs/archive/2026-08-05-completion-and-cross-platform-acceptance.md`.
   The unified-metrics argument for CoreText is a **construction argument, not a
   measurement** — do not let it harden into a claim.
6. **Web fonts built and HELD, not served** — `assets/fonts/th-aeonik-web/`. Serving
   redistributes CoType's outlines merged with Bai; unresolved licence question, as is
   harvesting from the web cut in the first place.
7. **Unmeasured:** how often the worst Thai pairing occurs in real prose. The repo's
   only Thai PDF has 382 Thai characters. Matters much less at 1537 than at 1200.
8. **Slussen source is incomplete** at 4 faces; a fuller set (10 faces including Light
   and italics) exists in an old build on `D:`. Italics must not be synthesised by
   shearing uprights.

---

## 14. The scripts

| Script | Use |
|---|---|
| `build_th_aeonik.py` / `build_th_slussen.py` | build the merged families |
| `build_aeonik.py` | rebuild Aeonik itself with the Greek/math coverage |
| `th_greek.py` | resolve missing Greek/math per face; `--faces X` to dry-run |
| `th_thai_prep.py` | scale, embolden, GDEF, dotted circle |
| `th_cff.py` | glyf → CFF keeping the Latin verbatim |
| `th_metrics.py` | stem and counter-aperture probes |
| `th_mark_clearance.py`, `th_baseline.py` | mark lift, baseline seat |
| `thai_line_pitch.py --check` | what the Thai needs, per family |
| `qc_th_fonts.py` | the 20 acceptance checks (19/20 expected) |
| `build_th_font_qc.py` → `qc_check_th_font_doc.py` | document-level QC, in that order |
| `win_latin_parity.py` | Windows rasterisation + the box Word leads off |
| `win_office_pitch.py` | line pitch in Word, PowerPoint, Excel via COM |
| `build_th_web.py --verify` | WOFF2 + CSS + headless-browser line box |
| `build_greek_specimen.py` | specimen sheets for visual review |
| `solve_weight_table.py`, `solve_mark_scale.py` | solvers; report tables, edit nothing |
| `fix-th-fonts.sh --check` | read-only Windows install report |

**Standard sequence after any font change:**

```bash
python3 scripts/build_th_aeonik.py && python3 scripts/build_th_slussen.py
python3 scripts/build_aeonik.py
cp assets/fonts/{th-aeonik/TH-Aeonik,th-slussen/TH-Slussen}-*.otf \
   ~/.local/share/fonts/th-current/ && fc-cache -f
python3 scripts/thai_line_pitch.py --check
python3 scripts/qc_th_fonts.py
python3 scripts/build_th_font_qc.py && python3 scripts/qc_check_th_font_doc.py
python3 scripts/win_latin_parity.py --from-dir "TH Aeonik" assets/fonts/th-aeonik \
                                    --from-dir "TH Slussen" assets/fonts/th-slussen
```
