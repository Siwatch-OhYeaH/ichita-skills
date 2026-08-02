# TH fonts — the line box was sized to contain ink it never needed to contain

**Date:** 2026-08-02 (evening)
**Branch:** `docs/ichita-proposal-design`
**Follows:** [`2026-08-02-th-font-thai-latin-harmonisation.md`](2026-08-02-th-font-thai-latin-harmonisation.md)

## Summary

The morning's fix for Thai mark clipping raised the merged fonts' `hhea` line box
until it contained the full mark stack — TH-Aeonik to 1710 units against Aeonik's
1200, TH-Slussen to 1870 against Slussen's 1512. That added 42% and 24% of leading
to every paragraph set in the merged faces, including pure-Latin ones. It was an
over-correction: **Word does not clip at `hhea` in body text, and no Thai font sizes
its line box to the mark stack.** Fixed by separating the two boxes — `hhea`/`sTypo`
now equal the Latin source's exactly, and `usWin` alone is sized to the ink. Found
by Siwatch's manual QC in Word (`QC fonts.pdf`).

## Symptom

Same English paragraph, same point size, single line spacing, in a Word document:

| block | font | line pitch @ 11 pt | em |
|---|---|---|---|
| control | Aeonik | 13.20 pt | 1.200 |
| test | TH-Aeonik | 18.75 pt | 1.710 |

The specimen's own text stated the acceptance criterion: *"…between Aeonik TH and the
original one which should be identical."* They were 42% apart.

## Root cause

`build_th_aeonik.py::set_vertical_metrics` and its Slussen twin held one box for all
three metric sets and asserted it contained the ink:

```python
ASCENT, DESCENT, LINEGAP = 1160, -550, 0
WIN_ASCENT, WIN_DESCENT = ASCENT, -DESCENT

lo, hi = _ink_bounds(font)
if hi > ASCENT or lo < DESCENT:
    raise SystemExit("ink escapes the line box")
```

Two different quantities were being answered with one number:

- **`hhea` / `sTypo`** — how far apart consecutive baselines sit. Word leads off
  `hhea`; LibreOffice and browsers off `sTypo` when `USE_TYPO_METRICS` is on.
- **`usWin`** — the bound outside which GDI declines to draw.

The line box has no obligation to contain the ink. Thai above-vowels and tone marks
are drawn to overflow it into the leading of the line above, where Latin ascenders
leave the space empty. Measured on this machine:

| font | line box | worst shaped stack needs | overflow |
|---|---|---|---|
| Bai Jamjuree | 1250 | 1552 | 302 |
| Leelawadee UI | 1330 | — | — |
| Tahoma | 1207 | — | — |
| Leelawadee | 1196 | — | — |

Requiring containment forced the box to the tallest three-level stack in the family
(`อึ๋ม` at +1088, `ทุก` at −331) and dragged Latin-only text along with it.

## Why the morning's reasoning was wrong

The morning post-mortem argued: *"`usWin` was already 1250/570 and did contain the
ink, yet marks still clipped — so the clip is taken against `hhea`."*

The premise about the symptom was never verified against the artifact. `printpdf4.pdf`
is the build that section describes as clipping: `hhea` 1300, unscaled Thai with
shaped ink needing 1552, so 252 units outside the line box. Rendering page 2 at 200
dpi shows `น้ำเชื่อม`, `ทั้งนี้`, `ซึ่งระบุ`, `ประสิทธิภาพ` and `เกี๊ยะ`-class stacks
**all complete** — no clipped marks, and no collision with the line above.

So the clipping the manual QC warned about was not happening in body text at all. The
original report was phrased as a precaution — *"the top/bottom **may** get cut off, so
during font engineer you should put something to prevent this"* — and was read as an
observation of a present defect. Where clipping does bite is fixed-height table rows
and `w:lineRule="Exactly"`, both of which are document settings, not font metrics.

The other half of the morning's finding survives intact: Word does lead off `hhea`,
and `old_hhea/new_hhea` = 1.6238 against a measured pitch ratio of 1.6218 remains the
evidence for it.

## Why it produced the symptom

`hhea.ascender − hhea.descender + hhea.lineGap` is the single-spaced line pitch in
Word. 1710 vs Aeonik's 1200 is 1.425×, so at 11 pt: 18.81 predicted, 18.75 measured.
Every document set in TH-Aeonik gained 42% of leading against the same document set
in Aeonik — which is exactly the "layout I try to make go wrong" complaint, in the
opposite direction from the morning's 1300-unit build.

## Fix

Two boxes, two purposes.

**`scripts/build_th_aeonik.py`**

```python
ASCENT, DESCENT, LINEGAP = 1000, -200, 0        # == Aeonik-Regular.otf hhea
WIN_ASCENT, WIN_DESCENT = 1160, 560             # == measured ink + headroom
```

**`scripts/build_th_slussen.py`**

```python
ASCENT, DESCENT, LINEGAP = 1074, -272, 166      # == Slussen-Regular.otf hhea
WIN_ASCENT, WIN_DESCENT = 1310, 590
```

`assert_line_box_matches_latin()` reads the Latin source's `hhea` before the merge and
fails the build if it disagrees with the constants, so a font update cannot drift the
two apart silently. The ink assertion in `set_vertical_metrics()` now tests `usWin`
instead of `hhea`.

This addresses the root cause rather than the symptom because the line box is no
longer derived from the ink at all — it is copied from the face being merged into,
which is the same ICHITA pairing rule already applied to size and stem weight.

**Clearance is strictly better than the build already proven safe.** Worst shaped
overflow is now 87 up / 131 down = 218 units, against `printpdf4.pdf`'s 252, which
renders clean.

## How it was found

The reproducer was `QC fonts.pdf` — a Word document with the same paragraph set twice,
once per font. `pdftotext -bbox-layout` gave the pitch directly.

Hypotheses tried and rejected:

- *The merged Latin outlines differ from Aeonik's.* Rejected — a 600 dpi crop of the
  same word from both blocks shows identical letterforms and widths.
- *The merged font is being rendered at a different point size.* Rejected — poppler
  word heights are 11.04 pt and 18.88 pt for the same 11 pt runs, which is
  `(asc+desc)/upem × size` for each font's own metrics, not a size difference.
- *Thai ink genuinely requires the taller box.* Rejected by `printpdf4.pdf`: 252 units
  of overflow, nothing clipped.
- *Aeonik cannot be matched because Thai needs more room.* Rejected — Bai Jamjuree,
  Leelawadee UI, Tahoma and Leelawadee all ship 1.20–1.33 em with the same overflow.

The single experiment that settled it: render page 2 of `printpdf4.pdf` — the build
whose line box was *smaller* than the ink by 252 units — and look for a clipped mark.
There are none.

## A second finding: the control block was Calibri

The QC document's `[Aeonik]` block was not Aeonik. `pdffonts` lists no Aeonik in the
file at all; every run in that block is `BCDIEE+Calibri`, `BCDKEE+Calibri-Bold` and
`BCDLEE+Calibri-Italic`. Aeonik is installed (per-user, `%LOCALAPPDATA%\Microsoft\
Windows\Fonts`), so this was a silent substitution or an unapplied font, not a missing
one.

The 1.20 em figure the fix targets was therefore taken from the font file, not from
that block. The conclusion was right and the control was not — which is luck, not
method, and worth closing. `scripts/build_ab_test_doc.py` now generates an A/B sheet
that hard-sets `w:rFonts` `ascii`/`hAnsi`/`cs` and deletes the `w:*Theme` attributes
that outrank them, and `scripts/check_ab_test_pdf.py` fails if any requested family is
absent from the exported PDF.

## Why it slipped through

**Incomplete prior fix, built on an unverified premise.** The morning fix inferred the
clipping mechanism from two facts (`usWin` contained the ink; marks were reported cut
off) without ever opening the PDF that was supposed to show the clipping. The
inference was sound given the premise; the premise was never checked.

**The test encoded the same assumption.** `qc_th_fonts.py` check 3 demanded
`hhea == sTypo == usWin` and that the box contain the ink — so it passed the
over-corrected font and would have failed the correct one. This is the third inverted
assertion in this codebase in two days, and the second in a test written the same day
to replace an inverted one.

**Nothing measured the merged face against its Latin source for leading.** Every check
compared the merged font to itself or to the Thai source. The one quantity the user
cares about — does a paragraph reflow when I switch fonts — had no test.

## Validation

Measured on Linux (fontTools, uharfbuzz, LibreOffice rendering):

- `scripts/qc_th_fonts.py` — **14/14** across 18 faces. Check 3 now asserts line box
  == Latin source's; check 5 bounds shaped stacks against `usWin`.
- `scripts/qc_check_th_font_doc.py` — **4/4**. Measured pitch at 11 pt: TH Aeonik
  13.20 pt vs Aeonik 13.20 pt; TH Slussen 16.65 pt vs Slussen's 1.512 em. The line-box
  comparison against the Latin source is now a hard assertion, not informational.
- `scripts/check_ab_test_pdf.py` on a LibreOffice-exported A/B sheet — **2/2**.
  TH-Aeonik 13.20 vs Aeonik 13.20 (+0.00); TH-Slussen 16.65 vs Slussen 16.65 (+0.00).
- Ink containment: TH-Aeonik static −503..+1106 inside `usWin` −560..+1160;
  TH-Slussen −535..+1255 inside −590..+1310.
- Thai size and stem unchanged: `ก` height == Latin x-height at ratio 1.000 on all 18
  faces; stems 0.93–1.00.

**Not validated in Word.** Windows still carries the previous build — Word and
PowerPoint were open, so `--apply-system` was not run. Specifically unverified:
the 13.20 pt pitch under Uniscribe, and that no stack clips at the new box in a real
ICHITA document. The Linux figures predict both, and the overflow is smaller than a
build already observed clean, but that is inference, not measurement.

## Action items

- **Reinstall on Windows and re-measure.** `./scripts/fix-th-fonts.sh --apply-system
  --restart` with Office closed, then export the A/B sheet from Word and run
  `check_ab_test_pdf.py`. (Siwatch.)
- **Stale TH-Slussen on Windows.** `%LOCALAPPDATA%\Microsoft\Windows\Fonts` holds 10
  `.otf` faces from the old build (including Light and a full italic set) alongside 4
  current `.ttf` in `C:\Windows\Fonts`. Both declare "TH Slussen". `--apply-system`
  removes them. (Siwatch.)
- **Pin line spacing in the ICHITA template** with `w:lineRule="atLeast"` — `Exactly`
  is where clipping genuinely occurs. Now lower priority: the font no longer imposes
  unusual leading. (Open.)
- **`docx_helpers.py:208` still disables unified-font mode**, so the generator splits
  Aeonik + Bai and does not use these fonts. (Open.)
- **Full Slussen source is still missing** — 4 faces available, the old build had 10.
  Do not synthesise italics by shearing. (Open.)
