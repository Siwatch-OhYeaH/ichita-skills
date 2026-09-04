---
name: font-follows-the-document-language
description: "Siwatch 2026-08-05 — English-only documents use Aeonik, mixed Thai/English use TH Aeonik; this dissolved the one-hhea conflict."
metadata: 
  node_type: memory
  type: project
  originSessionId: d621eeea-d5db-4286-bdb0-2b6325663e10
  modified: 2026-08-05T09:47:33.477Z
---

Siwatch's decision, 2026-08-05. **The face is a function of the document's
language**, not a single font serving both:

| document | face | box |
|---|---|---|
| English only | Aeonik | 1200 |
| Thai or mixed | TH Aeonik | 1537 |

This supersedes the second half of [[one-font-one-line-height]] and reverses the
2026-08-04 "TH Aeonik must be a drop-in Aeonik replacement" requirement. One font
still has one `hhea` — that never changed. What changed is that **no merged face
has to match Aeonik's box any more**, because English-only documents use actual
Aeonik. So the 262-unit Thai overlap that 1200 forced is retired rather than
tolerated, and both families are on one rule: box = the Thai's measured need +
margin, carried by `hhea`, `sTypo` **and** `usWin`. TH-Aeonik 1537, TH-Slussen 1602
— the same rule, not the same number.

**Accepted cost, explicitly:** English-only paragraphs *inside a mixed document*
lead ~28% wider. Do not "fix" this — fixing it is what produced the 08-04 defect.
It does not apply to decks; see [[powerpoint-ignores-font-metrics]].

Two things this implies that are easy to miss:

- **Coverage must match between the two faces.** Siwatch asked for Aeonik itself to
  be rebuilt with TH-Aeonik's Greek/math, because a character in one and not the
  other falls back to a system font depending only on whether the document happens
  to contain Thai. `scripts/build_aeonik.py` → `assets/fonts/aeonik-fixed/`.
- **Never mix the two faces in one document.** Different line boxes, so the text
  reflows at the boundary.

Selection is content-driven and **logged** in `md_to_docx.py`, `html_to_docx.py` and
`docx_helpers.resolve_font()` — any Thai codepoint (U+0E00–U+0E7F) selects TH Aeonik.
`html_to_docx` used to pick unified mode from *installation*, which silently gave
English-only briefs the 1537 box. Before this, `TH_AEONIK_MODE = False` was
hardcoded and none of the font work reached generated output at all — see
[[fix-the-layer-the-user-exercises]].

Recorded as brand policy in `assets/brand/ichita-defaults.md` §4 and
`docx-standard.md`, so it is not tribal knowledge.
