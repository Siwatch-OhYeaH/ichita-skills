---
name: ichita-design
description: Use this skill to generate well-branded interfaces and assets for ICHITA, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

Brand facts that must never be got wrong — the one URL, the mail domains, Betatron, the
closed palette, grounds, the weight rule — are in `CLAUDE.md` in this folder. Read it first.

**Any diagram, schematic or process figure follows the schematic grammar** — see the
SCHEMATIC DRAWING section of README.md and the *Schematic drawing* guidelines card before
drawing one. In short: equipment is a `ProcessGlyph` / `Unit`, never a labelled rectangle;
every connector is orthogonal with r=8 bends and its label sits 6–10px off the stroke in an
opaque mask; several connectors on one edge get fanned attach points; the legend is a
hairline strip at the bottom of the figure, never floating inside it; nothing is set below
18px and node names run 24–26px; twelve nodes at full treatment, up to 24 only when every
one sits in a labelled zone; one secondary hue per canvas, and only where it encodes a
technology family. `_ds_bundle.js` implements all of it — start from `Figure` and place
`Zone`, `Unit`, `Block` and `Connector` inside it, or use `Sankey`, `Timeline`, `Matrix`
and `OrgChart` for those shapes. The `guidelines/schematic-*.card.html` files are worked
examples that load it.

**Any Word (.docx) output containing Thai** must be language-tagged Thai or Word will
underline every Thai word red and stretch justified lines letter by letter. Follow
`office/thai-in-word.md` (`w:bidi="th-TH"` on every run, `w:cs` font, `szCs`/`bCs`,
`thaiDistribute` alignment), then run
`python skills/ichita-docx/scripts/fix_thai_docx.py OUTPUT.docx --inplace` on the result —
whatever produced the file. `md_to_docx.py`, `html_to_docx.py` and `rebrand_docx.py`
already run it after saving.

Word and PowerPoint templates: `office/ICHITA-Report-Template.docx`,
`office/ICHITA-Presentation-Template.pptx` — see `office/README.md`.

---

## Rendering a document

`scripts/md_to_document.py` builds an A4 document to the standard in
`README.md` — running header, the type ramp, the callout and the table style —
and hands the HTML to `ichita-exe-brief/scripts/html2pdf.py`:

```bash
python3 scripts/md_to_document.py IN.md OUT.html --eyebrow "ICHITA Technology"
python3 ../ichita-exe-brief/scripts/html2pdf.py OUT.html OUT.pdf
```

It is **not** a second `ichita-convert`. That skill renders the *record* — one
source, a DOCX and a PDF that lay out the same, and a reconcile path back from
a hand-edited DOCX. This designs the *artefact*. Reach for ichita-convert when
the point is the content and the round trip; reach for this when the document
leaves the building.

It reads `assets/brand/ichita.css` for the @font-face block and the colour tokens
rather than declaring its own.

---

## What is in this copy, and what is not

Generated in Claude Design (project `fda88ae7-cd85-4730-9e30-c9e02004756a`) from the
Brand Guidelines V1.0 PDF, this repository, and thirteen real ICHITA decks and reports.
Export of 2026-09-24, corrected here before re-upload (see *Decisions* below).

| In the Design project | In this repo |
|---|---|
| Written system — `README.md`, `design.md`, `fonts.md`, `company.md`, `deck-audit.md`, `CLAUDE.md` | ✓ |
| `guidelines/` — 39 spec cards | ✓ — the 45 `slides/`, `ui_kits/` and component cards the manifest also lists were not exported |
| `_ds_bundle.js` — all 32 components, compiled (namespace `ICHITADesignSystem_106280`) | ✓ — loads React 18 and Babel from unpkg, so it needs network |
| `_ds_manifest.json` — every token with its value, and the card / component index | ✓ |
| `tokens/*.css` | ✓ **rebuilt** by `scripts/build_tokens.py` from the manifest. Custom properties are verbatim; the few non-token rules (ground paint, typeset hook, Thai leading, `.ich-figure`, `.ich-nowrap`, the four patterns) are reconstructed from the written spec. **Never upload these back** — Design's own `tokens/` are the originals |
| `components/*.jsx` source, `templates/`, `slides/`, `ui_kits/` | ✗ — not exported |
| `assets/imagery/` — brand photographs | ✗ — stays in the Design project |
| `support.js`, `image-slot.js`, `_adherence.oxlintrc.json` | ✗ — Claude Design's own runtime and lint rules; they work only inside Design |
| Logos, font binaries, `ichita-defaults.md`, `docx-standard.md` | ✓ — `assets/` at the repo root. The cards look for `../assets/` beside themselves, with the Design project's file names, so **the brand cards' logos and photographs do not resolve here**; the fonts do (`tokens/fonts.css` points at `assets/fonts/`, installed faces first) |

`styles.css` is the entry point; link it and the cards, the bundle and your own HTML get
the whole system. For print, `assets/brand/ichita.css` is still the one stylesheet the
generators use.

## Decisions — Siwatch, 2026-09-24

Two conflicts inside the export were decided by him when this copy was corrected:

1. **Font: the 10-Aug weight rule governs.** One family, TH Aeonik; English-only documents
   run *TH Aeonik* Regular 400, Thai or mixed run *TH Aeonik Book* 350. (Chosen over the
   2026-08-05 face rule, English → Aeonik.)
2. **A4: the Design document standard governs** — 25 mm margins and the ladder in README.md
   *The document standard* and design.md §9.5. (Chosen over the PDF's and
   `docx-standard.md`'s 2 cm.)

On those two points this folder wins over `assets/brand/ichita-defaults.md` §4 and
`docx-standard.md`, which — with the `ichita-docx` generators — still implement the 08-05
face rule and 2 cm, and are **behind** until brought in line. Everywhere else,
`ichita-defaults.md` remains the operational spec the generators read at run time.
