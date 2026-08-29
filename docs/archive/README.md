# Archive — superseded font documents

**Everything here is superseded by [`../THAI-LATIN-FONT-ENGINEERING.md`](../THAI-LATIN-FONT-ENGINEERING.md).**
Read that instead. These files are kept for provenance only: they carry the
measurements, the dated decisions and the failed hypotheses that the consolidated
document distils.

**Do not act on a conclusion from this directory without checking it against the
consolidated document first.** Several were correct when written and were later
falsified — that is the main reason they are archived rather than deleted.

| File | Was about | Status |
|---|---|---|
| `2026-08-01-th-aeonik-merge.md` | five merge defects; the CFF/glyf addendum | historical |
| `2026-08-01-th-slussen-merge.md` | the same defects in Slussen, plus colliding family names | historical |
| `2026-08-02-th-font-thai-latin-harmonisation.md` | scale/weight harmonisation; the inverted acceptance test | historical |
| `2026-08-02-th-font-line-box-overcorrection.md` | the 42% leading defect + 4 addenda | **conclusions reversed twice** |
| `2026-08-02-windows-font-install.md` | locked files, and three bugs in the fix | still accurate; distilled into §9 |
| `2026-08-04-th-aeonik-latin-parity-and-line-pitch.md` | the format flip and `usWin` | **`usWin` claim later bounded** — it holds for CFF only |
| `2026-08-05-th-aeonik-line-box-reversal-and-cross-platform.md` | the plan for the final reversal | executed |
| `2026-08-10-changeweight-vertical-inset.md` | `changeWeight` insets every edge; the defect that shipped in Book | still accurate; distilled into §4c |
| `2026-08-05-completion-and-cross-platform-acceptance.md` | what that execution found | contains the **macOS acceptance test**, which has not been run |

Two specific traps for anyone reading these:

- The 08-02 line-box document argues at length that the line box must **not** be
  sized to the Thai, then reverses itself in Addendum 4. Both positions were
  wrong; see §1 and §3 of the consolidated document.
- The 08-01 and 08-02 merge documents cite `compare_th_*.py` "0 differing pixels"
  as proof of correctness. That test asserted the defect — §10.
