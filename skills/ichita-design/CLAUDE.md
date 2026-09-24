# Project instructions — ICHITA Design System

## Brand facts that must never be got wrong

- **Website: `www.ichita.co.th`.** This is the only ICHITA URL. Use it on every surface —
  slides, documents, letterhead, business cards, email signatures, footers — Thai and
  international alike. The 2022 brand guidelines PDF prints `Ichitaglobal.com`; that is
  **superseded**. Never write `ichitaglobal.com` anywhere.
- **Email domains are `@ichitathailand.com` or `@srithepgroup.com`** — never
  `@ichita.co.th`. The web domain and the mail domains are different; do not derive an
  address from the website. When an address is needed and none is given, use
  `@ichitathailand.com`.
- Company name in full: **ICHITA Technology Co., Ltd.**
- Brand identity contact: `wathaipan@srithepgroup.com`

## Betatron is chapter numerals only

Betatron is hard to read. Use it in **exactly one place**: the large numeral on a chapter
or section divider (48 px minimum, in practice 120 px+). **Never** for KPIs, table figures,
measurements, percentages, dates, agenda or list numbers, page numbers, or any word or
label. Everything else — including every figure the reader must read or compare — is
**TH Aeonik Bold**, tracking −0.035em, tabular numerals.

## One family: TH Aeonik. The document picks a WEIGHT, not a face

Settled 10 Aug 2026 on the final 22-face build (`fonts.md` is the record). Aeonik is a
fallback only — no document is set in it. **English documents default to TH Aeonik
Regular 400; anything containing Thai defaults to TH Aeonik Book 350** (`data-typeset="en"`
/ `"mixed"`; in Word, the families *TH Aeonik* and *TH Aeonik Book*). Emphasis is SemiBold
600 in both. Thai stops following the Latin above 700, so **ExtraBold 800 and Black 900 are
Latin display weights** and Air 100 / Thin 200 have no document role at all.

Thai leading: ink collides at 1.35, floor 1.40, headings 1.55, body 1.75; the declared line
box is 1.536, so Office must use *Multiple*, never *Exactly*. Word's Single already is that box
(the 1.75 body is Multiple 1.14); PowerPoint uses a fixed 1.2 em, so Thai there needs Multiple ≥ 1.3. Never inherit
`line-height:normal`. Tracking on Thai is always 0.

**The family has no NBSP** (nor thin/figure/narrow space, ZWSP, soft hyphen): never write
`&nbsp;` — use a normal space inside `.ich-nowrap`. Greek is Δ Σ Ω μ π only; α β γ λ σ fall
back to a system font.

## Slides are read from across a room

On the 1280×720 frame, **nothing is smaller than 18 px and running text is never below
24 px**. Defaults: slide title **36 px** (32 px absolute floor), sub-title **26–28 px**,
card/column heading 28–30 px, body, bullets, table cells and insight bars **24–26 px**,
captions/footers/eyebrows 17–18 px. Cover and statement headlines 60–76 px, dividers
46–48 px. If content will not fit at these sizes, **cut it or split the slide** — never
shrink the type.

## The palette is closed — four states, four families

Settled 4 Aug 2026. Specified on the **Secondary & functional palette — FINAL** card
(`guidelines/colors-secondary.card.html`); tokens in `tokens/colors.css` and
`tokens/secondary.css`. Those are the only source of record.

**Two sets, two jobs, no shared hue.** Functional says what *state* something is in;
secondary says which *technology family* it belongs to. Never swap them.

**Functional — branded, replaced the stock Material triad.** Each has `-tint` `-light`
`-text` steps.

| Role | Core | Text | Was |
|---|---|---|---|
| **Success** Process Green 169 | `#2EA885` | `#07765B` | #34A853 |
| **Warning** Technical Amber 78 | `#E6A100` | `#855C01` | #FFA000 |
| **Error** Oxide Red 25 | `#D64545` | `#A43E3C` | #E83E3E |
| **Attention** Signal Orange 45 | `#E87033` | `#A14512` | *new* |

**Attention is NOT a status** — it is the "look here" marker for callouts, milestones and
action items. It sits 20° from Error, so it may never appear in the same legend, table or
status key as Error.

**Secondary — four category hues.** Each has `-tint` `-light` `-text` `-deep` and two
grounds (`data-ground="cyan-tint"` … `"bronze-deep"`). No mid-tone ground exists.

| Hue | Core | Text | Codes |
|---|---|---|---|
| **Cyan** 204 | `#02919C` | `#01676F` | Membrane · water treatment · brine/recycle recovery |
| **Bronze** 69 | `#8D7B68` | `#6A5743` | Ion exchange · resin · equipment · raw material |
| **Rose** 350 | `#CE6D9E` | `#973F6E` | Adsorbent · decolorization |
| **Violet** 292 | `#8370C7` | `#6552A3` | Chromatography / SMB · Pilot Center · R&D |

The **product stream** (liquid sugar, syrup, sweetener) has **no colour of its own** — it
is the output of all four families. Ichita Blue or Blue Grey. "Other/unclassified" is Blue
Grey 02.

**Three rules.** (1) **Core = fill** (3:1 graphics bar), **text step = type** (5.6:1+).
Never set type in a core. (2) **85 / 15** — primary neutrals and Ichita Blue hold ~85% of
any layout, everything else under ~15%. (3) No secondary exceeds oklch chroma **0.135**
against Ichita Blue's **0.215**.

**Never:** add a hue not in those tables; use a secondary on a cover, closing slide,
letterhead or logo; use a secondary as a status or a functional colour as a category; use
a secondary as ICHITA scope in a process flow (that is Ichita Blue); put white on a *core*
(use the `-text` step for filled pills and tags); or put more than one secondary on a
single surface.

**Closed — do not reopen.** No additional blues (nothing within 40° of hue 262 — "Water
Blue" and "Tech Blue" are the accent restated). No "Graphite" (that is Blue Grey). No
second red/green/orange (duplicates the functional set). Ice Cyan #32C5D2 and Coral Rose
#D96B78 are already absorbed — as `--ich-cyan-light` and as the Rose ramp at hue 350. Any
earlier sheet listing twelve or eight "functional accents", or the Teal/Brass/Ochre/Plum
proposal, is **superseded**.

## Background and text colour are chosen together, never separately

Any block with a background colour uses `data-ground="white|off-white|grey-01|steel|dark|
darkest|accent"` (`tokens/grounds.css`), which sets the field and rebinds
`--text-primary` / `--text-muted` / `--text-accent` inside it. Light grounds take Blue
Grey 03 type; dark grounds take White. `color:#fff` is legal only on a `dark`, `darkest`
or `accent` ground. **Never** white on White, white on Blue Grey 01, white on Blue Grey 02,
or body copy on an Ichita Blue field.

## Source of record

`design.md` is the page-by-page conversion of *ICHITA Visual Identity Guidelines V1.0*
(`uploads/Ichita_Brand_Guidelines_V1.0.pdf`, 41 pp) and is the primary specification.
`README.md` is the system overview. Anything not in the PDF is marked **[EXTENSION]**;
errors in the PDF are marked **[ERRATUM]**.

## Thai in Word — every .docx must be tagged Thai

Red-underlined Thai and letter-stretched justified lines in Word mean the runs are not
language-tagged Thai (generators default to `w:bidi="ar-SA"`), so Word has no Thai
dictionary and no Thai word-break points. Every Thai-containing .docx: `<w:lang w:bidi="th-TH"/>`
on docDefaults and every run, `w:cs` font set (never `w:cstheme`), `szCs`/`bCs` mirroring
`sz`/`b`, justified Thai paragraphs `w:jc="thaiDistribute"` (never `both`), no `<w:br/>`
inside running Thai. Spec and python-docx / docx.js code: `office/thai-in-word.md`.
Always finish by running `python office/fix_thai_docx.py` on the output.
