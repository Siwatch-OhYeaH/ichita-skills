---
name: word-leads-off-uswin
description: "Which field Word takes line pitch from depends on the font FORMAT — usWin for CFF, sTypo for glyf with USE_TYPO_METRICS, max(hhea,usWin) without it"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9a53e104-c414-4086-8afa-b77c1ac8fb8a
  modified: 2026-08-05T06:38:19.445Z
---

**BOUNDED 2026-08-05.** This note used to say, flatly, "Word leads off
`usWinAscent + usWinDescent`." That is true only for **CFF** faces. Word's pitch was
measured for 15 installed families (six paragraphs, 11 pt, Single, `SpaceBefore/After=0`,
baseline travel ÷ 5, Word COM). No single field fits more than four of them. Three
branches fit all fifteen:

    format  USE_TYPO_METRICS   field Word uses    evidence
    CFF     set                usWin              Slussen 1595 (usWin 1596, hhea 1512)
    glyf    set                sTypo (==hhea)     Bai Jamjuree 1250 with usWin 1786!
                                                  Sarabun 1300 with usWin 1853
    glyf    clear              max(hhea, usWin)   Arial 1150 (hhea>usWin); Ink Free 1236,
                                                  DilleniaUPC 1305 (hhea only 600)

So **the format is part of the vertical metrics.** A CFF→glyf flip relocates the spacing
control without touching a single metric field — which is exactly how this bit us twice
from one change (`ea0dce2`). In the glyf+bit7 branch `sTypo` and `hhea` agreed in every
font available, so which of the two is read is NOT established — only that `usWin` isn't.

The original 2026-08-04 measurement stands and is the CFF branch:

    Aeonik      75.80 pt / 5 = 15.16 pt per line
    TH Aeonik  114.00 pt / 5 = 22.80 pt per line     ratio 1.504 = usWin 1800/1200

Both had `hhea` = `sTypo` = 1200 exactly, so `usWin` was the only box that differed.
`build_th_aeonik.py` had claimed the opposite in a comment and sized usWin to contain the
Thai ink; every Linux and outline check stayed green while the shipping renderer was 50%
out. The fix — all three boxes carry the Latin's numbers — is correct for the CFF faces we
ship, and robust by side effect: with hhea = sTypo = usWin = 1200 it lands on 1200 in
every branch above.

usWin is still not a clip bound in the DirectWrite era: ink extent vs usWin measures
Tahoma +246, Segoe UI +379, TH Aeonik +391, and neither Windows font clips in Word. But
read that table for CLIPPING only — all those fonts are glyf, so their usWin is not their
line box.

**Why:** three metric sets, and which one wins is chosen by the outline format, not by the
spec's names. A rule derived from one font pair is a rule about that pair — both fonts in
the pair that produced the flat claim happened to be CFF.

**How to apply:** `scripts/win_latin_parity.word_line_box()` encodes the branch; use it
rather than reading a field. To measure leading, use paragraph height ÷ line count in Word
COM — `Information(6)` at paragraph starts, and force `LineSpacingRule=Single` with
`SpaceBefore/After=0` or Word's default Multiple 1.15 inflates every absolute (it cancels
in a ratio). Do NOT use `Information(7)` for vertical position; it returned identical
values for two fonts with a 1.5x pitch difference. Related: [[one-font-one-line-height]],
[[font-format-is-the-rasteriser]], [[thai-line-clearance-is-a-document-setting]],
[[word-pdf-export-drops-cff]], [[verify-the-premise-against-the-artifact]].
