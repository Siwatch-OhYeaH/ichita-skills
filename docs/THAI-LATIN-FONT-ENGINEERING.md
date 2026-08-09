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

## 1b. The shipped family list — ten weights, one card (2026-08-09)

**This section is the current structure and it is BUILT.** §4b and §4c describe how the
faces are made and record two earlier structures that this supersedes — read them for
the reasoning, not for what ships. The face table below and `scripts/th_style_link.py`
are the only two places that say what ships, and they are checked against each other
every run.

### Approved sources

| Directory | Use |
|---|---|
| `assets/fonts/aeonik-web` | webfront only — Light & Regular, each with italic and bold |
| `assets/fonts/aeonik` | the desktop styles, mixed with our own build |
| `assets/fonts/bai-jamjuree` | ExtraLight (=Air), Light, Regular, Medium, SemiBold |

### The pairing rule, stated in glyphs

Latin and Thai must share **one baseline and one height**, checked on the letters that
have neither ascender nor descender:

```
Latin  a c o u n m r e s x z v
Thai   ก น ล บ ร ข ง ม อ แ า พ ห ย
```

Line spacing for Thai stays **~15xx**, not the 1200 that Latin alone needs.

### The families — TEN WEIGHTS, ONE CARD (Siwatch, 2026-08-09; BUILT)

Siwatch: *"I want one font deck for TH Aeonik that contains 10 font style with
according weight for Latin ... and build the thai font accordingly - follows the latin
one ... I know thai font has limitation for heavier size, so just let it gradually and
maximum at black."*

**20 files, 20 distinct outline sets, six `nameID1` families, one `nameID16`.**

| `nameID1` (Word's dropdown) | Regular slot | Bold slot | in the Settings card as |
|---|---|---|---|
| `TH Aeonik Air` | Air 100 | *none — synthesised* | Air |
| `TH Aeonik Thin` | Thin 200 | *none — synthesised* | Thin |
| `TH Aeonik Light` | Light 300 | ExtraBold 800 | Light, ExtraBold |
| `TH Aeonik Book` | Book 350 | SemiBold 600 | Book, SemiBold |
| `TH Aeonik` | Regular 400 | Bold 700 | Regular, Bold |
| `TH Aeonik Medium` | Medium 500 | Black 900 | Medium, Black |

Every face carries `nameID16 = "TH Aeonik"`, a distinct `nameID17`, and its own true
`usWeightClass`. `scripts/th_style_link.py` is the sole authority and its `--check`
now asserts the invariant the whole structure rests on: **no two shipped faces share a
(`usWeightClass`, slant)**.

**Measured 2026-08-09 on the built fonts.** `fc_family_probe.py` returns **zero
faults** — 12 bare family queries (six families x roman/italic), 8 `family:bold`
queries, 20 `TH Aeonik:weight=N` queries. `qc_th_fonts.py` 22/22.
`build_aeonik_semibold.py --check` green on all three ladders. The rendered
acceptance sheet embeds all 20 faces under their own names, which is the check that
caught the 08-07 defect (`TH-Aeonik-Air` embedded nowhere).

#### Why Air and Thin hold no bold slot

This is the decision that made one card possible, after the twelve-weight plan proved
it impossible. An unqualified fontconfig query defaults to fc 80 and the nearest
member of the `nameID1` family wins, so a family's plain face resolves only while it
sits closer to 80 than its own bold. Air is fc 0, distance 80; to beat that its bold
would need fc above 160, i.e. weight 600 or heavier — a jump from stem 7.8 to 130.9,
which is not a bold, it is a different typeface. Pairing Air with Thin was measured on
2026-08-07: bare `TH Aeonik Air` resolved to Thin, **+199.3% ink**.

So Air and Thin stand alone and Word synthesises their bold. §4b calls synthetic bold
the worst thing that can happen to this typeface, because double-striking spends
counter aperture and below ~47 units a Thai counter fills under any rasteriser. **That
reason does not reach these two:**

| face | counter aperture | `APERTURE_FLOOR` |
|---|---|---|
| Air | 113.3 | 46.5 |
| Thin | 97.7 | 46.5 |
| Bold | 50.8 | 46.5 — *why the rule exists* |

They are the only two weights in the family where synthesis costs nothing. The
exemption is asserted in both directions, so a third family losing its bold fails and
so does one of these gaining one.

#### Why Light bolds heavier than Book does

Light's bold is ExtraBold 800 and Book's is SemiBold 600, which reads backwards in the
table and is deliberate. fontconfig only requires each of their bolds to come from
{600, 800}; which gets which is a design choice, and Book 350 is the body weight for
Thai and mixed documents:

| pair | Latin | Thai |
|---|---|---|
| Regular 400 -> Bold 700 *(the reference)* | 85.9 -> 148.4, **1.73x** | 76.2 -> 130.9, **1.72x** |
| Book 350 -> SemiBold 600 | 74.2 -> 130.9, **1.76x** | 66.4 -> 118.2, **1.78x** |
| Book 350 -> ExtraBold 800 | 74.2 -> 166.0, 2.24x | rejected |
| Light 300 -> ExtraBold 800 | 52.7 -> 166.0, 3.15x | display weight, almost never bolded |

Ctrl+B on body copy has to land near the reference. The odd-looking rung goes where
nothing exercises it.

#### The top of the ladder is one Thai weight and three Latin weights

Bai Jamjuree Bold is the heaviest Thai this family has, and 2026-08-04 measured every
heavier Thai on the machine to confirm none buys stem without going under
`APERTURE_FLOOR`. So Bold, ExtraBold and Black are all Bai Bold at three embolden
amounts, and the whole ladder above 700 lives in 5.8 units of Thai:

```
            Latin              Thai            aperture
Bold  700   148.4              130.9              50.8
ExtraBold   166.0  +11.8%      134.8   +3.0%      46.9   ON THE FLOOR
Black 900   183.6  +10.6%      136.7   +1.4%      46.9   ON THE FLOOR
```

`WEIGHT_RATIO[800]` is **.806, not the .8175 the ratio ladder interpolates to**.
Interpolating puts the Thai at 135.7, one unit under Black — half a probe step, so the
two would measure as one weight and could invert on rounding. .806 splits the
available range evenly at 133.8 instead, ~1.5 probe steps per rung. That is the most
gradual ladder the source admits, which is what "just let it gradually and maximum at
black" asks for. **The top three still read as one Thai colour and three Latin
colours. Accepted, measured, not a defect to re-open.**

QC check 6 was rewritten for this. It used to carry a `LADDER_EXCLUDE` list that
dropped Black from the ladder entirely to stay green — asserting the defect. The rule
is now stated properly: a pair may fail the separation bar **only if the heavier face
is measured against `APERTURE_FLOOR`**, and check 12 then requires that pair to
separate in the Latin. "Bai has run out" is a number the shipped font proves every
run, not a name on an exclusion list.

#### What this replaced, and why the twelve-weight plan was abandoned

Approved 2026-08-07, measured 2026-08-08, **abandoned**: twelve weights in one card
put Light's bold at 450 and Air's at 200, and two of the six bare sub-family queries
broke — `TH Aeonik Air` -> AirBold +199.3%, `TH Aeonik Light` -> LightBold +92.5%. It
was structural, not a tuning error: within one `nameID1` family the plain face
resolves only while it is closer to fc 80 than its bold, and both of those families
had a bold by construction lighter than fc 160. Variant D (three cards, zero faults)
was offered as the middle option.

Siwatch chose neither. The ten-weight ladder dissolves the conflict instead of trading
around it, because dropping the bold slot is available once Thin is a weight in its
own right. It is also **cheaper**: one new Latin instead of three, and 20 files
instead of 24.

```
                        Settings cards      new Latin weights   bare query
before (08-07)          1 x 14 + 5 x 2 = 6  —                   clean
twelve weights          1 x 24         = 1  3 (450, 550, 800)   Air + Light BROKEN
variant D               1 x 20 + 2 x 2 = 3  2 (550, 800)        clean
TEN WEIGHTS (shipped)   1 x 20         = 1  1 (800)             clean
```

#### Metadata — ICHITA internal, with the attribution intact

Siwatch, 2026-08-09: *"modify to mark all ID as ICHITA internal use, so it not get
confuse."* Nine identity fields say ICHITA. `nameID0` does not, and that is the same
decision rather than an exception to it: it carries CoType's copyright, Bai
Jamjuree's notice verbatim as SIL OFL 1.1 clause 2 asks, and ICHITA's copyright on the
build. Writing ICHITA over that field would assert ownership of outlines we did not
draw. `nameID13` pointed at This Is Our Shop's EULA for nine builds — for a font that
is half OFL — and `nameID9` credited CoType's designers as the designers of our merged
font, which OFL clause 4 specifically discourages.

`nameID5` is `Version 1.000; build YYYY-MM-DD` — 1.000 because TH Aeonik has never
shipped, and the build date because every face read a bare `Version 1.000` across nine
rebuilds, which is why a stale install has twice been reported as a font defect. The
date is derived at build time rather than pinned to a constant somebody forgets to
bump, so `--check` asserts the shape and reports the date.

`OFL.txt` and `NOTICE.txt` now travel with the fonts. **Redistribution is held**: OFL
clause 5 requires a modified version to be distributed entirely under OFL, and the
Aeonik component is under a commercial licence that cannot allow it. One file cannot
satisfy both. Installing and embedding are use, not redistribution, and OFL permits
embedding explicitly — handing anyone the `.otf` files is the thing that is held.

### The two blockers, resolved

**1. "Same thickness as the Latin" is NOT ratio 1.0 — 0.89 is what "one font" measures.**
Siwatch's purpose, stated 2026-08-07: *"at one font face it should feel like they are
same font."* That is an optical target, and equal stem numbers do not meet it: Thai packs
more strokes and much tighter counters into the same height, so at ratio 1.0 it reads
**heavier** than the Latin beside it. The external check is the two Thai families whose
Thai and Latin were drawn together by one designer — **Leelawadee Bold .887, Sarabun Bold
.897**. `WEIGHT_RATIO` stays as it is; 1.0 is the target that made Bold unreadable on
2026-08-02 and it is not revisited.

**2. SemiBold stays, at weight 600.** Siwatch, 2026-08-07: *"we gonna have Medium weight
500 and Semi-bold weight 600."* Nothing is dropped.

### What the ratio question actually exposed

The rule was right and the **fonts were not on it**. Measured before the rebuild:

| face | ratio | target | off |
|---|---|---|---|
| Light | .926 | .905 | +1.1u |
| **Regular** | **.920** | **.890** | **+2.6u** |
| Medium | .890 | .890 | 0 |
| **Bold** | **.908** | **.890** | **+2.7u** |

Only Medium was on target, and check 2 passed all of it on a ±0.08 *ratio* band.

The cause was not drift. `solve_weight_table.py` — cited in `BUILD_TABLE` as the
authority for every value in it — **could not open a font** from 2026-08-04 to
2026-08-07 (stale `.ttf` extension after the CFF flip), so the table was hand-set while
its solver raised `cannot open resource` on every call. Three faces had been solved
against the **italic's** Latin stem: Light 54.7, Regular 87.9, Bold 150.4 are Aeonik's
italic figures; the romans measure 52.7, 85.9, 148.4. A target from a Latin ~2 units too
heavy asks the Thai for ~2 units it should not have.

Re-solved: Regular −8.4 → −11.2, Bold 13.4 → 8.1, Black 13.0 → 15.2.

**Bold is the one that mattered.** At 13.4 it sat on `APERTURE_FLOOR` (46.9) buying stem
it was never owed. Corrected it runs 130.9 at aperture **50.8** — ธ ฮ ฃ get their loops
back at text sizes, confirmed by eye on a rendered specimen, not only by the probe.

**A consequence worth stating: Thai Bold and Thai Black are no longer identical.** §4 and
check 12 recorded 134.8 for both and called it Bai's counter floor. Half of that was
true — Black IS on the floor. Bold was only there because it was over-emboldened. The gap
is now +4.5%, and check 12 was rewritten to assert what is actually load-bearing: **Black
must measure ON the floor**, which is what makes "Thai cannot separate further" a measured
limit of the source rather than a number nobody re-derived.

### Book, as built

Bai Jamjuree Regular ships **undistorted** — embolden `0.0`, the only such entry in
`BUILD_TABLE` — and the **Latin was drawn to fit it**, which is the reverse of every other
face. `usWeightClass` 350 is a declared sorting key for CSS and fontconfig, not a
measurement; the drawing is pinned by the Thai.

Its Latin could not be interpolated. **Aeonik is not interpolatable in any adjacent pair**
— Light→Regular 184 of 657 glyphs structurally incompatible, 6 of the 10 digits among
them; Regular→Medium 172; Medium→Bold 197. So Book is synthesised like SemiBold, but
**thinned** rather than grown, which makes it the safer of the two: thinning opens
counters, so the Light→Book→Regular→Medium counter ladder is monotonic by construction and
needs no `COUNTER_INVERSION_MAX` bound.

**Shipped 2026-08-09: Latin 74.2, Thai 66.4, ratio .895 against a .8975 target — −0.2
units, the tightest face in the family.** Those are the numbers the weight was
*defined* by: Bai Regular undistorted normalises to Thai stem 66.4, and
`WEIGHT_RATIO[350]` = .8975 pins the Latin at 66.4/.8975 = 74.0.

It did not measure that way on 2026-08-07. The first build came out Latin 72.3, Thai
64.0, and **the Latin target was lowered from 74.0 to 71.9 to keep the ratio** — which
treated a symptom. The Thai was short because `changeWeight` had shrunk Book's Latin
x-height to 496 against Regular's 510, and the merge scales the Thai to the Latin's
x-height. See §4c: the shrink is fixed at its source now, and the derived target went
back in.

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

### The falsified idea: adopt a Thai font that already has a 1200 box

**TH Baijam**, offered 2026-08-06 as a font that solves the leading problem. It does
have a 1200 Word box — the same as Aeonik's. **It is not a fix; 1200 is an artefact
of unit scale.** Do not re-propose it, and read the normalised table below before
comparing any two fonts by their boxes again.

First, what it is. Not a build, and *not related to Bai Jamjuree* despite the name —
`name` reads `IPTH: TH Baijam: 2006`, designer *[PITA] Rapee Suveeranont & Virot
Chiraphadhanakul*, v1.100, 497 glyphs, with legacy `morx`/`feat`/`PCLT`/`VDMX`
tables. Cadson Demak's Bai Jamjuree is 2017, 773 glyphs, `ttfautohint v1.6`. Similar
Thai words (ใบจาม / ใบจามจุรี), unrelated typefaces.

The box is 1200 because **the whole typeface is drawn at about two-thirds scale
inside the em**: x-height 339 against Aeonik's 510, cap 475 against 701. Normalise
for apparent size and the gain disappears:

```
set so the LATIN matches Aeonik @ 11 pt     pt    leading   vs Aeonik
Aeonik                                   11.00   13.20 pt      +0.0%
TH-Aeonik                                11.00   16.91 pt     +28.1%
TH Baijam                                16.55   19.86 pt     +50.4%   <- worse

set so the THAI matches TH-Aeonik @ 11 pt   pt    leading   vs TH-Aeonik
TH-Aeonik                                11.00   16.91 pt      +0.0%
TH Baijam                                14.17   17.00 pt      +0.6%   <- a wash
```

On pure geometry it is the *harder* font to fit, not the easier one — its Thai stack
needs **2.950** of its own Latin x-heights where TH-Aeonik's needs **2.820**. The
route it takes to 1200 is the one route the brand forbids: shrink the Latin. Aeonik
is the size reference (§4).

Blocking defects independent of the metrics: **Greek entirely absent** (0/144 — no
`μ`, `Δ`, `Ω`, and `μS/cm` is the unit ICHITA writes most; §5 exists for this), no
`→`; **no `GDEF`, no `mark`, no `mkmk`, no `ccmp`** — GPOS carries `kern` only, so
all mark placement falls to the shaper's Thai fallback; Thai/Latin stem ratio
**1.000** (Bold 1.014) against the measured rule of ~0.90 (§4); 4 weights; off-brand;
and no licence file shipped.

**The one thing it does prove** is in §7: a font whose worst stack is ≤ 1200 *can*
clear PowerPoint's fixed 1.2 em box. TH Baijam needs 1000 and has 200 spare where
TH-Aeonik is 238 short. The price is a Latin at 66% of Aeonik.

Its box is **predicted, not measured in Word** — glyf, `OS/2` v3, bit 7 clear, so
`max(hhea 1030, usWin 1200)`. `sTypo` is 1060, so a Word measurement would
discriminate the branches cleanly. The prediction is not bare: **DilleniaUPC is the
same configuration** — glyf, v3, bit 7 clear, `hhea` 584 / `sTypo` 1142 / `usWin`
1313 — and measured **1305** in the 15-family survey, i.e. `usWin`. 56 other
installed faces sit in that branch, eleven of them Thai.

### Reference measurements

```
font            line box   worst stack   spare
TH-Slussen          1602          1527     +75
TH-Aeonik           1537          1462     +75
Leelawadee UI       1330          1255     +75
Sarabun             1300          1582    -282
Bai Jamjuree        1250          1564    -314
TH Baijam           1200          1000    +200   <- see below, the spare is not a win
```

**A line box means nothing without the x-height it is drawn against.** The table
above ranks TH Baijam best and that ranking is false. Divide by each font's own
Latin x-height and the order inverts:

```
font            worst stack   x-height   stack/x-ht
TH-Aeonik              1438        510        2.820
TH Baijam              1000        339        2.950
Bai Jamjuree           1556        499        3.118
```

Boxes are only comparable between fonts drawn at the same scale. Ours are, because
they all carry Aeonik's or Slussen's Latin; a third-party font is not.

Sarabun — the nominated reference for correct Thai engineering — is *worse* than our
faces on pure geometry; it escapes because `ส` and `ซ` differ in width so the marks
miss sideways. Leelawadee buys its comfort with markedly smaller marks (upper vowel
201 vs our 273, tone 129 vs 158, lower vowel 182 vs 269), not a taller box.

---

## 4. Weight and size harmonisation

**The rule:** Thai is sized to the **Latin x-height** and weight-matched by **measured
stem** at ~0.89 of the Latin. **Aeonik's Latin is the benchmark, not Bai** — Siwatch
ruled on this, and Regular now runs ~+11% over Bai's own Regular by design.

**Width is a third constraint, and nothing controlled it until 2026-08-07.** The scale
is solved so ก's HEIGHT matches the Latin x-height (check 1, 1.000 on every face) and the
WIDTH simply inherits that factor. Each face pairs with a different Bai weight, thinned or
emboldened by a different amount, so each needs a different compensating scale — Air
.9509, Light .9086, Book .8889, Regular .9341 — and the Thai widths came out in whatever
order those accidents produced. Measured on one mixed line, Thai advance only:

```
          Latin    Thai            Latin    Thai
Air       12962   13105  <-- \     12962   12877
Light     13174   12665      |     13174   13164
Book      13229   12506  <-- inverted      13270
Regular   13320   13373            13320   13373
Medium    13486   13466            13486   13608
SemiBold  13627   13843  <-- \     13627   13753
Bold      13688   13458  <-- inverted      13897
             before                   after
```

The Latin column was already perfectly monotonic; only the Thai was out of order. **Siwatch
found it on the page, not in a number** — Air's line reached past Light's and Book's.

`normalise_thai_tracking()` pins every face to Regular's Thai/Latin advance ratio,
**1.3857**. Corrections run .976 to 1.064 and anything past 8% raises rather than being
absorbed, because a correction that large means the scale or the Bai pairing is wrong
upstream.

**It must be tracking, not a horizontal scale.** Scaling the Thai in x would fix the widths
and thicken every vertical stem by the same percentage — Book's Thai 64.0 -> 67.8, failing
check 2. Weight is the constraint that costs the most here, so the width fix must not touch
it. Outlines are not shifted either, so glyph-space GPOS anchors stay valid.

**Weight is two constraints, not one.** Stem *and* counter aperture. TH-Aeonik-Bold
once shipped with 7.8 units of aperture — 0.11 px at 11 pt, i.e. `ฃ` and `ธ` as solid
blobs — while passing the stem check at 0.974 of the Latin. `APERTURE_FLOOR` exists
because emboldening buys stem and *spends* aperture. Below ~47 units (0.7 px) a
counter fills in under any rasteriser.

**The ladder is capped, and the cap is real.** Bai has nothing heavier than Bold, so
Thai Bold and Thai Black measure **134.8 both** — identical, not merely close.
Balanced per-weight and Bold-distinct-from-Black are mutually exclusive from this
source. The taper (`WEIGHT_RATIO` 900 → .745) states the *reachable* number rather
than a target the counter floor forbids.

`qc_th_fonts.py` check 6 failed on purpose because of this, at 19/20, from 2026-08-03
to 2026-08-06. **It no longer does, and the tolerance was not widened** — §4b removed
Black from the ladder instead. Once Black became TH Aeonik Medium's *bold* rather than
the rung above Bold, a reader never meets the two as consecutive weights, so
"monotonic and distinct" stopped being the right question to ask of it. Check 12 asks
the right one: the Latin separation, +23.7%. **Expected state is now 22/22.**

**`changeWeight` under-delivers on negative amounts** — roughly half the requested
thinning reaches the outline — so the embolden→stem slope differs by sign. It also
**grows outlines downward**, which drags Thai off the Latin baseline worse the bolder
the weight; hence step 3c. `solve_weight_table.py` iterates a secant on the shipped
measurement rather than modelling any of this.

**Never pair by weight name.** Matching Bai Regular to Aeonik Regular left Thai 25%
lighter than the Latin beside it. Pairing lives in `th_thai_prep.BUILD_TABLE`.

---

---

## 4b. Style linking — why Word must never synthesise a bold

**Decided 2026-08-06 by Siwatch. This is a metadata-only change: not one outline
moves, and every write asserts it.**

Until then TH Aeonik inherited CoType's family layout — one RIBBI family plus five
weights each holding its own `nameID1` with only Regular and Italic. **Four of the six
families in Word's dropdown therefore had no bold member**, so Ctrl+B on `TH Aeonik
Light` made Word double-strike the outline.

That is the worst thing that can happen to this typeface. Synthetic bold spends
exactly the counter aperture §4 defends: below ~47 units the counters of ฃ ธ ฮ fill
under any rasteriser, and Bold already ships at 46.9. The reason it went unseen for
nine sessions is rule 10 in §0 — **the generators were never exposed to it.**
`md_to_docx.py` and `html_to_docx.py` write family `TH Aeonik` plus `w:b` and get the
real Bold face. The defect only ever reached the layer Siwatch actually exercises,
which is typing in plain Word.

### The shipped structure — superseded twice; §1b is current

This section records WHY Word must never synthesise a bold, which has not changed. The
face table that used to live here has moved to §1b, because it moved twice in three
days and two copies of it is how a stale one gets read.

The short history, because each step falsified the one before:

| date | structure | what broke it |
|---|---|---|
| 2026-08-06 | 5 families, bold slots at 700 with no `nameID16` | six Settings cards; Siwatch asked for one |
| 2026-08-07 | + SemiBold, + Book; 24 faces, 18 outline sets | 6 of 24 faces were duplicate outlines, so one card was impossible |
| 2026-08-09 | **10 weights, 20 faces, 20 outline sets, 6 families, one card** | current |

### A bold slot declares its true weight now — and why it used to lie

From 2026-08-06 to 2026-08-08 every bold slot declared `usWeightClass` 700 and `panose`
8 whatever its outlines weighed, and dropped `nameID16`/`nameID17`. Both halves are now
reversed. **The rule was not wrong; the condition it existed under is gone.**

It existed because bold slots were DUPLICATES — `TH Aeonik Light`'s bold and
`TH Aeonik Medium`'s Regular were the same file. Put both in the typographic family and
`TH Aeonik` holds several faces at weight 500, so a WeasyPrint or LibreOffice request
for 700 can resolve to Medium's outlines: a Thai PDF that silently renders one weight
light. Declaring 700 and hiding from `nameID16` was the way to keep one face per weight.

There are no duplicates left. The typographic family holds exactly one face per weight
because there IS exactly one face per weight, and the invariant is asserted directly
(`th_style_link.check()`: no two shipped faces share a (`usWeightClass`, slant)) rather
than enforced by a naming convention.

What links Word's Ctrl+B is `nameID1`/`nameID2` plus the `macStyle` bold bit, never
`usWeightClass`, and that is unchanged: `_face()` derives fsSelection and macStyle from
nameID2, so `TH-Aeonik-ExtraBold.otf` announces itself as "TH Aeonik Light Bold" to the
style linker and as "ExtraBold" to the Settings card. **Linux cannot confirm it.**
`scripts/build_style_link_doc.py` is the sheet that does, in Word.

**One measured consequence worth keeping.** On 2026-08-07, promoted faces kept their
true weight while aliases declared 700, and `fc-match "TH Aeonik Air"` returned
**AirBold** — Air declares 100 (fc 0) and its bold declared 200 (fc 40) against a
default request at fc 80, so the bold was the closer match. LibreOffice picked it for
the plain-Air row of the acceptance sheet and `TH-Aeonik-Air` embedded nowhere in the
PDF. **Asking for Air quietly got Thin.** Found by reading the embedded-font list of
the rendered artifact, not by any check. That is the defect §1b's Air/Thin decision
exists to prevent, and reading `pdffonts` on the acceptance sheet is now part of the
gate.

### A family name that ends in a weight word is re-parsed

**LibreOffice serves `TH Aeonik SemiBold` its family's BOLD for plain text.**
Measured 2026-08-07 on the acceptance sheet: the Regular row and the Ctrl+B row of
page 5 came out in the same face, `TH-Aeonik-SemiBoldBold`, and `TH-Aeonik-SemiBold`
embedded nowhere. It re-reads the token "SemiBold" in the family name as a weight
request. `Light` and `Medium` in the same position resolve correctly, so it is
specific to this keyword.

**fontconfig is not the culprit and the weight route is clean:**

```
fc-match "TH Aeonik SemiBold"     -> TH-Aeonik-SemiBold.otf      correct
fc-match "TH Aeonik:weight=180"   -> TH-Aeonik-SemiBold.otf      correct
weasyprint, ichita.css 500/600/700/900 -> Medium / SemiBold / Bold / MediumBold
```

So **the generators and every CSS path are unaffected** — they select family
`TH Aeonik` plus a weight or `w:b`, never the split family name. What is unresolved is
Word, which is the acceptance renderer and the only place a human picks
`TH Aeonik SemiBold` off a dropdown. It is called out on page 5 of the acceptance
sheet: the Regular row must be lighter than the Ctrl+B row. If Word does what
LibreOffice does, the fix is a family name with no weight word in it — do not tune
metrics to work around a name parser.

### Acceptance — measured in Word, not inferred

For each family the bolded run's Latin stem must equal its **named source face**, not
a double-strike of its own regular. Measured at 512 px/em over `STEM_LATIN`:

| family | plain Latin | bolded Latin must equal |
|---|---|---|
| `TH Aeonik Air` | 7.8 | 23.4 (Thin) |
| `TH Aeonik Light` | 52.7 | 115.2 (Medium) |
| `TH Aeonik` | 85.9 | 148.4 (Bold) |
| `TH Aeonik Medium` | 115.2 | 183.6 (Black) |
| `TH Aeonik SemiBold` | 130.9 | 183.6 (Black) |

A value near the regular's own stem plus one pixel means the style link failed.
`scripts/build_style_link_doc.py` builds the sheet: each bolded row sits directly
above the face it must equal, so it is read by eye at 100% with no instrument.

### Aeonik itself was deliberately not changed

Siwatch's call. `Aeonik Light` still synthesises its bold in an English-only document
while `TH Aeonik Light` gets a real Medium. The divergence is recorded in
`assets/fonts/README.md` so it reads as a decision rather than an oversight.

### Where it lives

`scripts/th_style_link.py` is the single authority on face naming — the 20-face table,
the metadata writer, the alias generator and a read-only `--check`. `build_th_aeonik.py`
imports `FACES` as its `WEIGHT_CONFIG` and calls `write_aliases()` at the end of a full
build; a **partial** build refuses to write aliases, because a half-linked family is
worse than an unlinked one (Word would take the real bold for upright text and
synthesise the italic).

**The build keys did not change.** `Air … Black` name the *outline recipe* — the Latin
source in `WEIGHTS`, the Thai pairing and embolden in `th_thai_prep.BUILD_TABLE`. Black
is still a build key though no shipped face is called Black. Renaming the identifier a
dozen modules key on is what broke 12 scripts on 2026-08-06; the shipped filename lives
in `cfg["file"]` instead.


---

## 4c. The three synthetic Latins — what shipping weights CoType never drew costs

**Siwatch, 2026-08-07 for SemiBold and Book, 2026-08-09 for ExtraBold, after being
shown the costs below: ship them.** Every other Latin glyph in this repo is CoType's
own charstrings — `th_cff.convert_to_cff` restores them verbatim after the merge and
`win_latin_parity.py` is the acceptance test for that.
`scripts/build_aeonik_semibold.py` breaks the invariant three times, deliberately, and
all six faces declare it in `nameID5` and `nameID10`.

### What was ruled out first

* **No Aeonik SemiBold, Book or ExtraBold exists.** Desktop v1.000 is Air/Thin/Light/
  Regular/Medium/Bold/Black; the v2.000 web cut is only Light/Regular/Bold.
* **Interpolation fails in EVERY adjacent pair.** Light→Regular has 184 of 657 glyphs
  with incompatible point structures, Regular→Medium 172, Medium→Bold 197 —
  `three` `five` `six` `dollar` `ampersand` `question` among them. The digits are in
  the broken set, which for ICHITA is disqualifying on its own.

### The targets, interpolated not chosen

Aeonik's real ladder gives 16.6 of stem and 118 of advance per 100 weight units
between 500 and 700, so weight 600 sits at **stem 131.8, advance 11516**. ExtraBold is
the 700/900 midpoint on the same arithmetic, measured 2026-08-09.

| weight | class | stem | advance | counter `e` | drawn by |
|---|---|---|---|---|---|
| Light | 300 | 52.7 | 11024 | 171.9 | CoType |
| **Book** | **350** | **74.2** | **11142** | **152.3** | **thinned from Regular** |
| Regular | 400 | 85.9 | 11206 | 136.7 | CoType |
| Medium | 500 | 115.2 | 11398 | 118.2 | CoType |
| **SemiBold** | **600** | **130.9** | **11515** | **93.8** | **grown from Medium** |
| Bold | 700 | 148.4 | 11634 | 97.7 | CoType |
| **ExtraBold** | **800** | **166.0** | **11750** | **93.8** | **thinned from Black** |
| Black | 900 | 183.6 | 11867 | 78.1 | CoType |

**Two of the three THIN, and that is the measured preference, not a coincidence.**
Thinning opens counters where growing spends them, so the thinned faces need no
`COUNTER_INVERSION_MAX` bound: Book sits cleanly between Light and Regular, and
ExtraBold's 93.8 sits between Bold's 97.7 and Black's 78.1. Only SemiBold, the one
grown face, inverts against the weight above it. Where a target can be reached from
either side, thin from the heavier neighbour.

### The two things synthesis gets wrong

**1. Fit is arithmetic, not drawn.** `changeWeight` has no model of letterfit.
Measured at the same stem, all three FontForge counter modes give the *identical*
counter and differ only in advance: `squish` 11398 (Medium's — cramped), `auto`
11930 and `retain` 11944 (**wider than Black**). None is the ~11516 the ladder wants,
so the build squishes and then scales advances, splitting the gain across both
sidebearings. Kerning is inherited from Medium, whose pairs were fitted for Medium's
sidebearings.

**2. Counters overshoot, and this one cannot be fixed.** A drawn SemiBold would
interpolate to ~108. `changeWeight` spends counter roughly 1:1 with the stem it adds
and never reopens a bowl, so the synthetic lands at 93.8 — **tighter than Bold's
97.7**, a non-monotonic counter ladder. `counter_type` moves sidebearings, not
counters, so this is the ceiling of the technique rather than an untuned knob. It is
~4% (≈0.06 px at 11 pt), which is why it ships, and it is **bounded at 10%** in
`build_aeonik_semibold.check()` rather than exempted. That bound is expected to pass;
it is not a red-on-purpose check.

### A trap that cost real glyphs

FontForge **renames glyphs on generate**, deriving the new name from the Unicode
value: `uni2126` → `Omega`, `summation` → `Sigma`, `a.ss01` → `a.salt`. Grafting by
name silently missed **147 of 657 glyphs** on the first build — every `.case`
punctuation, every oldstyle and tabular figure, the `fi` and `fl` ligatures, and all
four harvested Greek/math glyphs (µ ∆ Ω ∑). They would have shipped at **Medium
weight inside a SemiBold face**, and `fi`/`fl` fire in ordinary text.

Two cheaper fixes were measured and are worse: stripping the cmap makes FontForge
rename *everything* by index (656 of 657 unmappable), and matching by glyph order
fails because it inserts `.null` and `nonmarkingreturn` and the index offset is not
constant (−304..+5). The fix is to give every unencoded glyph a temporary Private Use
codepoint before the round trip, which makes the naming a function we control —
measured 656/656, a clean bijection.

**The check that would have caught it did not.** It asserted the Greek codepoints
were *present in the cmap*. They were — at the wrong weight. Presence is not the
property that mattered.

### The Thai half was ordinary

Bai Jamjuree has a real SemiBold, and the target (0.89 × 130.9 = 116.5) sits well
inside the range. Solved by measurement, and the pairing choice mattered:

```
Bai SemiBold +15.2  -> thai 117.2   aperture 48.3   CAP
Bai Bold     -10.0  -> thai 118.2   aperture 70.3
```

48.3 is 1.8 units off `APERTURE_FLOOR` on a weight *lighter* than Bold, and the
italic came out at 47.0 — one probe step from failing. Thinning opens counters,
emboldening spends them, so **Bai Bold thinned** is right and matches what the rest
of `BUILD_TABLE` already does (Regular←Medium, Medium←SemiBold).

`solve_weight_table.py` could not run at all when this started: it looked for
`{family}-{weight}.ttf`, an extension left stale by the 2026-08-04 CFF flip, so every
call raised `cannot open resource`. It is cited in `BUILD_TABLE` as the authority for
every value in it. Fixed to read the file map and `.otf`.

### Book: the same technique run backwards, and two artefacts it exposed

Book (350) thins Aeonik Regular instead of growing Medium, and the direction changes the
risk profile. `changeWeight` spends counter as it adds stem; run negative it **opens**
counters, so Book's counter sits at 152.3 between Light's 171.9 and Regular's 136.7 — a
monotonic ladder with no bound needed. Book is the safer synthesis.

Two things only the thinning direction revealed:

**1. Thinning shrinks the glyph AND lifts it off the baseline. Fixed 2026-08-09;
the 08-07 entry below treated the symptom.**

`changeWeight` insets the outline by roughly half the requested amount on **every**
edge, the horizontal ones included. Measured thinning Aeonik Black by −18.4:

```
glyph    Black         thinned        drift
x          0..516        9..507       baseline +9, x-height −9
H          0..700        9..691       baseline +9, cap      −9
```

Three hypotheses were tested and falsified before the fix was written:

* *the glyf intermediate loses the CFF blue zones* — it does, confirmed; passing
  `custom_zones` explicitly changes nothing;
* *"auto" mode ignores zones but "LCG" honours them* — both produce the identical
  9-unit inset, and so does running `changeWeight` on the pristine `.otf` with its
  BlueValues intact;
* *it is a cu2qu rounding artefact* — the inset is 9 units at −18.4 and 7 at −14.5,
  i.e. half the requested amount, not a rounding.

It is inherent to the tool, so `restore_vertical()` corrects it: the affine map that
makes the baseline and the x-height exact against the base face. Cap and descender
scale with it and land within ~2% rather than exactly — a constant inset is not an
affine transform, so no single map restores every extreme, and the x-height band is
the one the merge and the reader key on. It is a **no-op on a grown face** (SemiBold
measures the same band as Medium), which is asserted rather than assumed, and
`check()` now compares every synthesised face's band against its base with a 2-unit
tolerance.

**What it cost while it was unseen.** Aeonik-Book's `x` ink-top was **496 against
Regular's 510** and the whole face floated 7 units above the baseline.
`build_th_aeonik` sizes Thai to the Latin x-height (QC check 1), so the merged Thai
landed 64.5 where 66.4 was predicted — and on 2026-08-07 **the Latin target was
lowered 74.0 → 71.9 to keep the ratio**, which fixed the number and left the face
2.7% shorter than every other weight in the ladder. It went unseen because the merge
scales the Thai to the Latin, so both scripts agreed with each other inside the font
while both were wrong: nothing measured the Latin against its own base. With the
shrink fixed, Book's scale solves at exactly the nominal 0.9140, its Thai measures
66.4, and the derived target 74.0 goes back in at −0.2 units.

**Predict nothing here — measure the band.** Any future thinned weight does the same
thing, and `restore_vertical()` handles it, but the check is what makes that true.

**2. `sxHeight` and `sCapHeight` are inherited and were lying.** Aeonik-Book shipped
`sxHeight` 510 over ink topping out at 504. It did not show on SemiBold because
emboldening happened to leave Medium's 512 intact — the kind of accident that keeps a
stale field looking correct. `_name_face` now re-measures both from the outlines.

### The permanent fix

If CoType ships an Aeonik SemiBold — or a **variable** Aeonik, which would let us
instance a real 600 with drawn fit — replace this and delete the script. That is the
fix. Do not tune the numbers here.

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
  1537, the same shortfall that produced the 08-04 defect in Word. A Thai deck needs
  explicit line spacing. This is the one place where "fix it in the document" is
  correct, and for our faces it is not a choice.

  This used to read *"the font cannot fix this."* **Too strong** — corrected
  2026-08-06. PowerPoint's box is fixed at 1200, but that is a ceiling on the
  *stack*, not a claim that no font clears it. A font whose worst stack is ≤ 1200
  fits: **TH Baijam needs 1000 and has 200 spare** where TH-Aeonik needs 1438 and is
  238 short. So the accurate statement is *TH-Aeonik and TH-Slussen cannot fix this*,
  and the reason is their stack size, not a property of PowerPoint.

  It does not change what to do. Buying that headroom means a Latin at 66% of
  Aeonik's x-height, which is off-brand and re-spends the leading at the size you
  have to set it (§3). Document-side line spacing remains the answer for an ICHITA
  deck. But the bound belongs to the fonts we chose, not to the application.

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
- **Adopting a third-party Thai font because its line box is smaller.** TH Baijam,
  box 1200. The box is small because the typeface is drawn at ~2/3 scale in the em;
  at equal Thai size it leads 17.00 pt against TH-Aeonik's 16.91 — a wash — and at
  equal Latin size, 19.86 pt against 16.91. Also no Greek, no `GDEF`/`mark`/`mkmk`,
  and off-brand. §3.
- **Widening `qc_th_fonts` check 6's tolerance.** It fails on purpose. §4.
- **Sizing the line box to contain the Thai ink.** Cost 42% of extra leading. §3.
- **Migrating to the v2 web cut wholesale.** Box 1140, respaced digits, 6 of 14 faces. §5.
- **LibreOffice as a stand-in for the Windows print path.** Its print and export
  outputs were byte-identical — no signal, and it briefly suggested nothing was wrong.

---

## 13. Current state — 2026-08-09

**Shipping:** **20** TH-Aeonik faces from **20** outline sets in **6** families, ten
unique weights in ONE Windows Settings card (§1b) + 4 TH-Slussen + **20** Aeonik faces,
all `.otf`/CFF. Aeonik carries **three** synthetic pairs, §4c — Book (350, thinned from
Regular), SemiBold (600, grown from Medium) and ExtraBold (800, thinned from Black) —
the only Latin here that is not CoType's drawing.

**All faces were rebuilt 2026-08-09 from one code state**, into an emptied output
directory, then copied to `~/.local/share/fonts/th-current/` and `fc-cache -f` before
any check ran.

Two things this rebuild fixed that were not in the request:

* **`changeWeight` insets every edge, so thinned faces came out short and lifted off
  the baseline.** Book had been shipping 2.7% shorter than the ladder and floating 7
  units up since 2026-08-07, and the 08-07 response was to lower its Latin target
  rather than restore the height. `restore_vertical()` fixes it at source and
  `build_aeonik_semibold --check` now measures every synthesised face's vertical band
  against its base. §4c.
* **Nine builds shipped as a bare `Version 1.000`** inherited from CoType, so a stale
  install was invisible — which is how a stale install got reported as a font defect
  twice. `nameID5` now carries the build date and `nameID3` agrees with it.

```
scripts/thai_line_pitch.py --check   OK — both families spare +75
scripts/th_style_link.py --check     OK — 20 faces, 20 outline sets, 6 families,
                                     weights 100 200 300 350 400 500 600 700 800 900,
                                     no two faces sharing a (weight, slant). That last
                                     invariant is the whole point of the structure and
                                     nothing asserted it before 2026-08-09
scripts/fc_family_probe.py           OK, 0 faults — 12 bare family queries (roman AND
                                     italic), 8 family:bold, 20 weight queries. NEW
                                     2026-08-07: the fields being right is not the same
                                     as the matcher answering right, and twice it was
                                     not (§1b). The italic queries were added 08-09;
                                     roman-only would have passed a structure that gets
                                     emphasis wrong in half the cases. fontconfig only
                                     — Pango, WeasyPrint, soffice. Nothing about Word
scripts/verify-fonts.py              OK — asserts usWin == hhea == sTypo
scripts/qc_th_fonts.py               22/22. Check 6 was REWRITTEN 08-09: it used to
                                     carry a LADDER_EXCLUDE list dropping Black from
                                     the ladder to stay green, which is asserting the
                                     defect. A pair may now fail the separation bar
                                     only if the heavier face measures against
                                     APERTURE_FLOOR, and check 12 then requires that
                                     pair to separate in the LATIN. Check 12 also
                                     stopped naming Bold and Black and derives the
                                     capped run by measuring, so ExtraBold arriving
                                     between them is judged rather than ignored
scripts/build_aeonik_semibold.py     OK — THREE ladders: Light/Book/Regular/Medium,
                                     --check                Medium/SemiBold/Bold/Black
                                     and Bold/ExtraBold/Black, all monotonic in stem
                                     AND width. Counter inverts 4.2% at SemiBold,
                                     bounded 10%; the two thinned faces need no bound.
                                     Also asserts the vertical band per face
pdffonts on the acceptance sheet     OK — all 20 faces embedded under their own names.
                                     This is the check that caught the 08-07 AirBold
                                     defect, where TH-Aeonik-Air embedded nowhere
scripts/win_latin_parity.py          CANNOT VALIDATE THIS BUILD — it measures what is
                                     installed on WINDOWS, and that is stale: TH Aeonik
                                     resolves UNRESOLVED (substituted), TH Slussen to a
                                     pre-CFF-flip .TTF, which is the documented 16-20%
                                     lighter (§6). Re-run after installing the 24 faces
scripts/qc_check_th_font_doc.py      4/4 — LibreOffice 16.90 pt vs 16.91 predicted
scripts/win_office_pitch.py          OK — 6 measurements, Word/PowerPoint/Excel
scripts/build_th_web.py --verify     OK — Blink 1540/em
scripts/build_aeonik.py              14/14, vertical metrics unchanged
scripts/solve_weight_table.py        FIXED — it built trials into assets/fonts/ and
                                     silently replaced 16 shipped faces; trials now go
                                     to a temp dir, and build_th_slussen.build_font
                                     gained the out_dir it was missing
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

1. **Install on Windows** (Siwatch) — **24** merged faces from
   `assets/fonts/{th-aeonik,th-slussen}` (20 + 4), plus **16 from
   `assets/fonts/aeonik` over the current Aeonik** (same family name; `nameID5`
   reads `Version 1.001; ICHITA Greek/math coverage`). §9 for the traps.
   **Uninstall `TH Aeonik Black` AND `TH Aeonik Thin` first** — both are retired
   (§4b) and nothing overwrites them, so they would otherwise sit in the dropdown
   beside their replacements.
1b. **Then measure the style link in Word** — the acceptance table in §4b. Two
   assertions Linux cannot make: whether Word honours a bold slot whose
   `usWeightClass` (700) disagrees with its outlines, and **whether Word re-parses
   `TH Aeonik SemiBold` the way LibreOffice does** and serves the family's Bold for
   plain text. `test-output/th-style-link-acceptance.docx` is built for exactly
   these; page 5 is the SemiBold one.
2. **Then re-run `win_office_pitch.py` and `win_latin_parity.py`** against the
   installed set. Word's 1537 is currently predicted from the file, not measured in Word.
3. **Review the specimen** — `test-output/greek-aeonik-*.png`. The `∆`/`µ` appearance
   change, and whether to also take the web cut's respaced `S 1 3 4 5 8 @ €` (not done;
   it covers only 6 of 14 faces and would split the family).
4. **Thai in PowerPoint** — expected to collide at single spacing. Verify visually; the
   fix is document-side. §7.
   - Not measured: whether a ≤1200-stack Thai face (TH Baijam needs 1000) *visually*
     clears PowerPoint's box. Pitch cannot see a collision; that needs a rendered
     slide read as pixels. Only worth doing if a Thai-dominant deck ever justifies an
     off-brand Latin.
   - Not measured: TH Baijam's Word box. 1200 is predicted from the branch table and
     backed by DilleniaUPC in the same configuration, not observed. §3.
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
| `qc_th_fonts.py` | the 22 acceptance checks (22/22 expected) |
| `build_aeonik_semibold.py` | synthesise the Aeonik SemiBold; `--check` verifies the ladder |
| `build_style_link_doc.py` | the Word acceptance sheet for the bold slots |
| `th_style_link.py --check` | TH Aeonik's shipped family structure; the authority on face naming |
| `fc_family_probe.py` | which file a *matcher* returns, not which fields a face carries |
| `build_th_font_qc.py` → `qc_check_th_font_doc.py` | document-level QC, in that order |
| `win_latin_parity.py` | Windows rasterisation + the box Word leads off |
| `win_office_pitch.py` | line pitch in Word, PowerPoint, Excel via COM |
| `build_th_web.py --verify` | WOFF2 + CSS + headless-browser line box |
| `build_greek_specimen.py` | specimen sheets for visual review |
| `solve_weight_table.py`, `solve_mark_scale.py` | solvers; report tables, edit nothing |
| `fix-th-fonts.sh --check` | read-only Windows install report |

**Standard sequence after any font change:**

```bash
python3 scripts/build_aeonik_semibold.py     # BEFORE the merge — it is a Latin source
python3 scripts/build_th_aeonik.py && python3 scripts/build_th_slussen.py
python3 scripts/build_aeonik.py
python3 scripts/th_style_link.py --check     # 24 shipped faces, every family bolds
python3 scripts/fc_family_probe.py           # and every one of them RESOLVES
rm -f ~/.local/share/fonts/th-current/TH-Aeonik-{Black,Thin}*.otf   # retired, §4b
cp assets/fonts/{th-aeonik/TH-Aeonik,th-slussen/TH-Slussen}-*.otf \
   ~/.local/share/fonts/th-current/ && fc-cache -f
python3 scripts/thai_line_pitch.py --check
python3 scripts/qc_th_fonts.py
python3 scripts/build_th_font_qc.py && python3 scripts/qc_check_th_font_doc.py
python3 scripts/win_latin_parity.py --from-dir "TH Aeonik" assets/fonts/th-aeonik \
                                    --from-dir "TH Slussen" assets/fonts/th-slussen
```
