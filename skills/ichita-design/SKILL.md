---
name: ichita-design
description: Use this skill to generate well-branded interfaces and assets for ICHITA, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

---

## What is in this copy, and what is not

Generated in Claude Design (project `fda88ae7-cd85-4730-9e30-c9e02004756a`) from the
Brand Guidelines V1.0 PDF, this repository, and thirteen real ICHITA decks and reports.
**Only the written system came across.** The runtime the documents describe did not:

| Described in these files | In this repo |
|---|---|
| `tokens/*.css` — base, colors, fonts, typography, patterns, grounds, shape, spacing, motion, secondary | ✗ — values are stated in full in `design.md`, so they can be re-derived |
| `components/` — core, brand, data, charts, diagrams, forms, icons | ✗ — specified, not implemented |
| `assets/imagery/` — 49 ICHITA photographs | ✗ — stays in the Design project |
| `_ds_bundle.js`, `support.js` | ✗ |
| Logos, font binaries, `ichita-defaults.md`, `docx-standard.md` | ✓ — `assets/` in this repo, which is where the Design project read them from |

So: read these files as the **specification**, and build against `assets/` here. Do not
`@import` a `tokens/` path — it does not resolve. The one stylesheet this repo ships for
HTML and print is `assets/brand/ichita.css`, which arrives with the `ichita-convert`
branch (PR #7) — until that merges, take the values from `ichita-defaults.md`.

Where this file and `assets/brand/ichita-defaults.md` disagree, `ichita-defaults.md`
wins — it is the operational spec the generators read at run time.
