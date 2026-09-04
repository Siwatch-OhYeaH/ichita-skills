---
name: fonttools-and-dwrite-traps
description: "Four API traps that produce confident wrong font measurements — roundTolerance=0 means noRound, the glyf glyph set applies lsb-xMin while drawing, WPF init flips process DPI awareness, T2WidthExtractor's first arg is local subrs"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6df22ab0-8c6c-4b78-97e9-a0dbc4e3417f
  modified: 2026-08-04T09:24:58.380Z
---

Four APIs whose behaviour is the opposite of how they read. Each cost a cycle on
2026-08-04 and each failed *silently* or, worse, passed for the wrong reason.

**`T2CharStringPen(..., roundTolerance=0)` does NOT round.** `roundFunc(0)`
returns `noRound`, so charstrings keep floats — quad control points land on exact
thirds like 95.66666667 and get written as 16.16 fixed point. Use **0.5**, which
maps to `otRound`. The bloat is the tell: one face went 342 KB -> 208 KB.

**fontTools' glyf glyph set applies the `(lsb - xMin)` offset WHILE DRAWING.**
So a stale `hmtx` lsb translates whatever a pen records, not just what a TrueType
rasteriser shows. I deleted a `lsb`-to-`xMin` sync reasoning "CFF ignores lsb" —
true of the format, false of the pen — and `TH-Aeonik-BoldItalic`'s `ษ` counter
collapsed from 55.2 to 3.9, i.e. the loop filled solid. Sync lsb BEFORE any
pen-based conversion.

**Loading WPF flips the process to DPI-aware**, the moment the first WPF object is
constructed — not at `Add-Type`. On a 150%-scaled display GDI+ then reports DpiX
144 and every Point-sized font renders 1.5x larger. In one mixed process the first
GDI measurement was right and every later one was inflated by exactly 144/96,
reading as "TH Aeonik is 50% bigger than Aeonik". Measure GDI and DirectWrite in
**separate processes**, and size GDI in Pixel units with `PageUnit = Pixel`.

**`T2WidthExtractor`'s first argument is the LOCAL SUBRS index, not CharStrings.**
Passing charstrings makes `callsubr` execute arbitrary glyph programs: it
underflows the operand stack on a subr-heavy font (Slussen, 357 global subrs) and
**silently passes** on a light one, because the extractor usually satisfies
`gotWidth` before reaching any subroutine call. Take the private dict off the
charstring itself so an FDArray resolves correctly.

**Why:** all four produce a *confident* wrong answer, and two of them produce a
PASS. The Aeonik width guard passed for weeks-worth of reasons before Slussen
crashed it into the open.

**How to apply:** none of these is caught by reading the code — they are caught by
sabotaging an artifact and confirming the check FAILS
([[verify-what-the-test-asserts]]), and by re-running any measurement whose
magnitude surprises you against a second font. Related:
[[windows-text-measurement-from-wsl]], [[font-format-is-the-rasteriser]].
