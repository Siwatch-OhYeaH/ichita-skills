---
name: harfbuzz-cannot-validate-word
description: Linux/HarfBuzz font testing is structurally blind to the Word/Uniscribe defects this project keeps hitting; Windows is the acceptance target
metadata: 
  node_type: memory
  type: project
  originSessionId: d53cf7f9-f6b3-498c-b3de-1083b5f85c67
  modified: 2026-08-03T18:28:50.763Z
---

The delivery target for ICHITA fonts is Word on Windows, which uses Uniscribe and
DirectWrite. All local tooling renders through HarfBuzz and FreeType. They disagree in
ways that hide real defects:

- **HarfBuzz infers GDEF glyph classes from Unicode; Uniscribe trusts the font.** Bai
  Jamjuree leaves Thai spacing vowels at GDEF class 0, so `าาาาาาา` shaped perfectly
  under HarfBuzz and would not type at all in Word.
- **HarfBuzz tolerates a missing U+25CC; Word needs the glyph** to render an orphaned
  mark.
- **Line height differs by metric set.** LibreOffice honours `USE_TYPO_METRICS` and
  leads off `sTypo`; Word leads off `hhea`. A LibreOffice-rendered PDF measured the
  wrong renderer and pointed at the wrong root cause for a whole session.

**Why:** a green Linux suite says nothing about the shipping target for this class of
bug, and four sessions were lost to defects that were invisible locally.

**AMENDED 2026-08-04 — Windows is reachable, and this memory made it look like it
was not.** `powershell.exe` is on PATH from WSL, so GDI/Uniscribe, DirectWrite and
Word's own layout can all be measured in-session. The blindness is HarfBuzz's, not
the environment's. Treating "verify on Windows" as something only Siwatch could do
delayed the 2026-08-04 diagnosis by four wrong hypotheses. See
[[windows-text-measurement-from-wsl]] for the three probes and their traps.

**How to apply:** measure locally for speed, but never report a shaping, GDEF or
line-spacing fix as verified until it is confirmed on Windows. State the validation
scope explicitly — "measured on Linux, unverified in Word" — rather than implying
coverage. The Windows install path is `./scripts/fix-th-fonts.sh --apply-system
--restart`, and fonts there have gone stale silently more than once, so verify the
installed files hash-match the repo before trusting any Windows result. Related:
[[verify-what-the-test-asserts]].
