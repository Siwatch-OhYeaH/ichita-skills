---
name: rebuild-before-trusting-qc
description: "In this repo the committed fonts can disagree with the committed builder, and ~/.local/share/fonts/th-current silently feeds the document QC — rebuild and re-copy before believing any suite"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9884d45d-ea2f-47ee-9f6a-c1e96026a93a
  modified: 2026-08-03T16:59:01.802Z
---

Two artifact-vs-code gaps found on 2026-08-03, both of which had already scored a
green suite.

**The committed fonts were not built by the committed builder.** Building
`TH-Aeonik-Black` from HEAD gave counter aperture 46.9 binding on `ฮ`; the
committed `TH-Aeonik-Black.ttf` had 50.8 binding on `ฆ`. Same stem, same
`BUILD_TABLE` entry. Fix 6's faces were saved mid-iteration and never rebuilt
after its last edit, so its 20/20 was scored against artifacts its own code could
not produce — and Black's real margin over `APERTURE_FLOOR` was 0.4 units, not the
4.3 the shipped font showed.

**`~/.local/share/fonts/th-current/` is a second, silent input.** `md → DOCX →
PDF` goes through LibreOffice, which resolves fonts via fontconfig, not from
`assets/fonts/`. That directory was two builds behind (Slussen line box 1600 where
the repo had 1625), so `qc_check_th_font_doc.py` reported a Slussen pitch of 17.60
against its own prediction of 17.88 — reading as a font defect when it was a stale
copy.

**Why:** the fonts are binary build outputs committed alongside the code that
builds them, with nothing enforcing that they match. A green suite proves the
*artifact* is good, and says nothing about whether the artifact came from the code
you are about to hand over.

**How to apply:** rebuild all 18 faces from one code state before running any
suite, then `cp assets/fonts/*-th/*.ttf ~/.local/share/fonts/th-current/ &&
fc-cache -f` before anything that renders a document. If a QC number moves without
a code change explaining it, suspect these two before the font
([[verify-the-premise-against-the-artifact]]). Generated docs drift the same way —
`qc/th-font-qc.md` was still carrying 1600 from two builds back. Windows is a
third layer with the same problem: hash-compare against
`/mnt/c/Users/OhYeaH/AppData/Local/Microsoft/Windows/Fonts/`
([[siwatch-installs-fonts-via-settings]]).
