# Deck audit — eleven real ICHITA presentations, measured

Every file in `uploads/*.pdf` that is a presentation was opened, its text extracted, and its
**fonts and fill colours read out of the PDF itself** (not eyeballed). This is the evidence
base for the standardisation rules in `README.md`, and the checklist for converting an
existing deck onto the system.

All eleven decks are built on a **960 × 540** frame. The system's 1280 × 720 kit is the
same 16:9 at 1.333×, so every layout maps one-to-one; type sizes in this system are stated
at 1280 and divide by 1.333 for a 960 master.

---

## 1. What was measured

| Deck | pp | Fonts embedded | Dominant non-black fills |
|---|---|---|---|
| How to improve RO system to >90% recovery | 21 | Calibri, Calibri Bold, Arial, **Poppins**, **Aptos Narrow** (+Bold) | #66CCFF · #29B8FF · #A3E0FF · #008BD0 · #595959 · #333333 |
| What 10 Years of Fieldwork in Rayong Taught Us | 20 | Calibri, Calibri Bold | #44546A · #FF0000 · #EAEDF2 |
| Practical Strategies for Real-World Situations | 24 | Calibri, Calibri Bold, Arial | #66CCFF · #CDEEFF · #FFB9B9 · #FFF2CC · #FF822D · #00B0F0 · #DAE3F3 · #FF7C80 · #B4C7E7 · #FFA161 · #767171 · #D0CECE |
| Membrane Technology in Sugar and Sweetener Process | 27 | Calibri (+Bold), Arial, **TH Sarabun New** | #FF0000 · #4472C4 · #A5A5A5 · #0070C0 · #ED7D31 · #7030A0 · #92D050 · #BDD7EE |
| High Value Product Diversification | 31 | Calibri (4 cuts), Arial (3 cuts), **TH Sarabun New** (+Bold), Courier New, Cambria Math | #4472C4 · #FF0000 · #FFD966 · #F8CBAD · #00B050 · #7030A0 · #843C0C · #0563C1 |
| Derivative Production Technology | 32 | Calibri (+Bold), Arial | #44546A · #AFABAB · #7F7F7F · **#2978FF** · #3B3838 · #404040 · #F8CBAD · #FF0000 · #00B050 · #7030A0 |
| StraPack system and Brine recovery system | 31 | Calibri (+Bold), Arial, **TH Sarabun New**, **Angsana New** (+Bold), Wingdings | #FFD966 · #843C0C · #F4B183 · #1428F0 · #4472C4 · #203864 · #B4C7E7 · #ED7D31 |
| WTP Proposal — KSL Sa Kaeo | 23 | Calibri (+Bold), Arial, **TH Sarabun New** (+Bold), **Browallia UPC** (+Bold), Wingdings, Wingdings 3, Symbol | #333F50 · #5B9BD5 · #8497B0 · #C55A11 · #D6DCE5 · #ADB9CA |
| Sugar derivatives opportunity — TSMC seminar | 21 | *(see `company.md`)* | mixed third-party market graphics |
| ICHITA Company Profile 26 Jun 2024 | 20 | — | dark cover + photography, closest to brand |
| ICHITA Company Profile 28 Mar (A4 brochure) | 12 | — | pre-V1.0 diagonal chevron system |

### The three findings that matter

1. **Not one deck uses the brand typeface.** Aeonik and TH Aeonik appear zero times in
   eleven files. Calibri appears in all of them. Betatron appears nowhere — which is
   *correct behaviour by accident*, since Betatron is chapter numerals only.
2. **Four different Thai faces are in circulation** — TH Sarabun New, Angsana New,
   Browallia UPC, and the Thai fallback inside Calibri. All four must become TH Aeonik,
   which carries Thai itself on every surface as of the 2026-08-05 build.
3. **Twenty-four distinct non-brand hexes**, and exactly one brand hex in the whole
   corpus: `#2978FF`, thirty times, in *Derivative Production Technology*. That deck is
   the furthest along the conversion; use it as the starting point, not the others.

---

## 2. Colour conversion map

Everything left of the arrow was measured in a real deck. Replace on sight.

| Found | Where it came from | Replace with |
|---|---|---|
| `#4472C4`, `#5B9BD5`, `#0070C0`, `#0563C1`, `#1428F0` | Office `accent1` and hand-picked blues | `--ich-blue` #2978FF (fills) · `--ich-blue-text` #1A56C4 (type) |
| `#66CCFF`, `#29B8FF`, `#00B0F0`, `#A3E0FF`, `#CDEEFF`, `#BDD7EE`, `#B4C7E7`, `#DAE3F3` | someone approximating brand blue, then tinting it | `--ich-blue-light` #82B0FF, or `--chart-seq-1…5` when it is an intensity ramp |
| `#44546A`, `#333F50`, `#203864` | Office `dk2` and its shades | `--ich-blue-grey-03` #263338 |
| `#8497B0`, `#ADB9CA`, `#A5A5A5`, `#AFABAB`, `#D0CECE`, `#767171`, `#7F7F7F`, `#595959`, `#898989` | Office `accent3` and the grey ladder | `--ich-blue-grey-02` #788F9C · `--ich-blue-grey-01` #CFD9DB · `--ich-rule` #A0B0B8 |
| `#D6DCE5`, `#EAEDF2` | Office light tints used as card fills | `--surface-card` #F8FAFB or `--ich-blue-grey-01` |
| `#ED7D31`, `#FF822D`, `#FFA161`, `#F4B183`, `#F8CBAD`, `#C55A11`, `#843C0C` | Office `accent2` orange family | `--chart-2` #F08C00 in charts · `--ich-warning` #E6A100 only when it means *watch this* |
| `#FFD966`, `#FFF2CC`, `#FDFADC`, `#F6F0E4` | Office `accent4` yellow tints as highlighter | delete — highlight with **Bold** or an Ichita Blue keyword, not a wash |
| `#7030A0`, `#D1196C`, `#92D050` | ad-hoc extra series colours | `--chart-5` #7A5AF8 · `--chart-6` #00857A · `--chart-4` |
| `#FF0000`, `#FF3300`, `#FF7C80`, `#FFB9B9`, `#FFE1E1` | red for the problem | `--ich-error` #D64545 for marks and fills · `--ich-error-text` #A43E3C for type |
| `#00B050`, `#003300` | green for the achieved figure | `--ich-success` #2EA885 · `--ich-success-text` #07765B for type |
| `#3B3838`, `#404040`, `#333333`, `#191919` | near-blacks | `--ich-blue-grey-03` #263338 · `--ich-blue-black` #171C21 |

**Keep the semantics, change the hue.** The decks already use red for the failing figure
and green for the achieved one, and they are right to. Only the values change.

## 3. Type conversion map

| Found | Replace with |
|---|---|
| Calibri, Calibri Bold, Arial, Aptos Narrow, Poppins | **TH Aeonik** — Regular for body, Bold for headings and every figure |
| TH Sarabun New, Angsana New, Browallia UPC | **TH Aeonik** — it renders Thai itself; set Thai runs at the same size as the Latin, leading ≥1.55 |
| Cambria Math, Courier New | TH Aeonik; formulae set inline, not in a maths face |
| Wingdings ✓, Wingdings 3 ➢, Symbol • | `Icon` `check` / `chevron-right`, or a plain disc bullet |
| Betatron | *(absent — and it should stay absent except on chapter dividers)* |

---

## 4. The engineering seminar arc

`README.md` documents the **product-sell** arc and the **teaching deck**. These eight decks
are a third, tighter shape — the technical seminar, run by an ICHITA engineer for an
audience of plant people. Ten acts, and six of the eight follow it almost exactly.

1. **Cover with the presenter named.** Title, subtitle, then name and role — "Siwatch
   Chomchai, Product development manager". These are personal talks; sign them.
2. **Today's topics.** Four to six plain bullets. Not the numbered agenda — this is a
   spoken contents list.
3. **The system everyone already runs**, drawn once, with the figures under each unit.
4. **The loss, in money.** The same drawing, with the water or salt loss marked and priced:
   *"600 m³/day · 7,560,000 THB/year"*. This is the act that makes the room listen, and it
   is the one most often missing from ICHITA's own proposals.
5. **How the industry normally deals with it** — and why that caps out. Honest about the
   conventional answer before selling the better one.
6. **Divider**, then **the ICHITA concept** as a drawing with nothing on it but the idea.
7. **The concept with the numbers on it** — the same drawing again, percentages added.
8. **A named case.** One plant, before and after, the same drawing a third time, the
   changed figures in green.
9. **The money derived on screen** — saving per m³ × annual volume = annual saving;
   investment ÷ saving = payback. Never a bare "ROI 3.3 years".
10. **Summary as spoken sentences**, then Thank you / Q&A.

Two structural habits worth copying verbatim: **one drawing carries the whole deck** (the
RO deck redraws the same balance nine times, changing one thing each time), and **the
specification travels with the stream** (flow, conductivity, TDS pinned at every node) so
before → after is read off the diagram, never out of a separate table.

---

## 5. Recurring slide types, and what now serves them

The eight decks between them repeat twelve slide types. Six were already in the kit; the
other eight are new layouts added because of this audit.

| Recurring slide | Seen in | Layout |
|---|---|---|
| Stream/mass balance with specs at every node | RO, Membrane, StraPack, KSL, Practical | **`23-mass-balance.html`** *(new)* |
| Operating-cost split with a THB/m³ figure | Practical (×3), RO | **`24-cost-breakdown.html`** *(new)* |
| Investment, annual saving, payback | RO, Practical | **`25-investment-payback.html`** *(new)* |
| Priced options against two variables | KSL | **`26-option-matrix.html`** *(new)* |
| Inlet vs guaranteed outlet quality | KSL, Practical | **`27-design-basis.html`** *(new)* |
| Numbered method, one step active per slide | StraPack (×5), Membrane | **`28-method-rail.html`** *(new)* |
| Small-multiple parameter trends | Rayong (whole deck) | **`29-small-multiples.html`** *(new)* |
| Reference plants with duty and year | Membrane, StraPack, Profile | **`30-reference-plants.html`** *(new)* |
| Section divider | all eight | `02-divider.html` |
| Process train | all eight | `08-process-flow.html` |
| Two-system comparison with a verdict | Practical, StraPack, Membrane | `10-comparison.html` |
| Pilot/measured data with a spec line | Membrane, Derivative Production | `09-data.html` |

---

## 6. Defects to fix on sight

- **Nine-point body text.** The dense flow slides (KSL options, Derivative Production
  possibility map) run type far below the 18 px floor at 960 × 540. Those are two slides,
  or a hand-out — not one slide.
- **Slide numbers set as bare "4", "9", "20"** in the top-left corner of several decks —
  keep page numbers bottom-right, 17–18 px, muted.
- **Highlighter yellow** (`#FFD966`, `#FFF2CC`) used to emphasise a row. Emphasis is Bold
  or an Ichita Blue keyword.
- **Two changes on one diagram.** *Practical Strategies* p14 moves the RO unit *and*
  recolours the cycle figure in one step; the audience cannot tell which is the point.
- **Third-party market graphics pasted at screen resolution** (prebiotic market charts,
  competitor packshots). Rebuild the data with `Chart`; a competitor's packshot needs a
  reason to be there.
- **`ichitaglobal.com` / no URL at all.** Every deck footer is `www.ichita.co.th`.
