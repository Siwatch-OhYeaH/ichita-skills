# Windows font install — locked files, and two bugs in the fix for them

**Date:** 2026-08-02
**Scope:** `scripts/fix-th-fonts.sh`
**Commits:** `b5e288e` (the fix), on top of `ea0dce2` (the glyf rebuild)
**Status:** the two script defects are fixed and validated. The locked-file
deletion is **queued but not executed** — it runs at boot. See *Validation*.

---

## Summary

Installing the rebuilt TH-Aeonik / TH-Slussen fonts machine-wide left **20 of 38
stale `.otf` files physically on disk**. Windows memory-maps loaded font files,
so `Remove-Item` cannot delete a face the session has already touched, and
unregistering it does not release the mapping. Among the survivors was
`TH-Aeonik-Regular.otf` — sha `f64d54df4fb6`, 188,424 bytes, byte-identical to
the pre-fix blob every bad print has been embedding.

Fixed by queueing the survivors with
`MoveFileEx(..., MOVEFILE_DELAY_UNTIL_REBOOT)`, which the kernel executes at boot
before any font is loaded. The first implementation of that queue had two bugs,
one of which would have queued the *newly installed* fonts for deletion; it was
prevented only by the second bug making every call fail.

---

## Symptom

`./scripts/fix-th-fonts.sh --apply-system` reported per-file results. 18 files
deleted, **20 reported `STILL PRESENT`**:

```
file- TH-Aeonik-Regular.otf              STILL PRESENT
file- TH-Aeonik-Regular_0.otf            STILL PRESENT
file- TH-Aeonik-Light.otf                STILL PRESENT
file- TH-Slussen-Regular.otf             STILL PRESENT
...
file+ TH-Aeonik-Regular.ttf              ok
```

The registry layer came out clean — exactly 10 HKLM values, all pointing at the
new `.ttf`. The 10 new fonts installed successfully. Only the physical stale
files remained.

The pattern is diagnostic: `_1` and `_2`-suffixed copies deleted; the plain
`.otf` and `_0` copies survived. Those are the ones the font system had actually
loaded.

---

## Root cause

### The locked files

Windows memory-maps a font file when a face from it is loaded, and holds that
mapping for the life of the session — GDI/DirectWrite, the FontCache service and
every process that has rendered with the face. `Remove-Item` on a mapped file
fails with a sharing violation. The generated script used
`-ErrorAction SilentlyContinue`, so each failure was silent; only the explicit
`Test-Path` re-check after each delete surfaced it.

Deleting the HKLM registration first does not help. Registration controls *font
enumeration*, not the file mapping. The file stays mapped until the mapping is
released, which in practice means a reboot.

`MoveFileEx(src, NULL, MOVEFILE_DELAY_UNTIL_REBOOT)` writes the operation into
`HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations`,
which the Session Manager executes during boot, before the font subsystem loads
anything. A `NULL` destination means delete.

### Bug 1 — the queue was scoped to the wrong file set

```bash
for f in "${SYS_FILES[@]}"; do        # every TH-* file in C:\Windows\Fonts
    printf 'if (Test-Path ...) { [MV]::MoveFileEx(...) }'
done
```

`SYS_FILES` is populated at script start by scanning `C:\Windows\Fonts`. On the
**first** run that set is exactly the stale files. On any **subsequent** run it
also contains the 10 `.ttf` installed by the previous run — and the install step
runs earlier in the same script, so even within one run the newly copied files
are on disk by the time the queue is built.

The queue would therefore have scheduled the current build for deletion at boot.
The machine would have come back up with the fonts registered in HKLM and the
files gone.

### Bug 2 — `$null` is not `NULL`

```powershell
[MV]::MoveFileEx("C:\Windows\Fonts\X.otf", $null, 4)
```

PowerShell marshals `$null` to an **empty string** when the target parameter is
a .NET `string`. `MoveFileEx` received `""`, not `NULL`, and returned `false` for
every call. Zero entries were queued.

`[NullString]::Value` is the documented way to pass a real `NULL` to a `string`
parameter.

### Bug 3 — the Office guard matched process names, not open documents

```bash
tasklist.exe | grep -qiE '^(WINWORD|EXCEL|POWERPNT|OUTLOOK)\.EXE' && exit 1
```

This refused to run on a machine where the user had neither Word nor Outlook on
screen. Measured:

| Process | PID | `MainWindowHandle` | Title | Started |
|---|---|---|---|---|
| `OUTLOOK.EXE` | 5516 | 1707534 | *(none)* | Jul 31 09:59 |
| `WINWORD.EXE` | 35132 | **0** | *(none)* | Aug 1 21:16 |

Outlook lives in the tray. `WINWORD.EXE` had no window at all — an orphan left
by the previous session's print-to-PDF work at 21:16, which the handoff timestamps
at 21:14. Neither held an open document. The guard blocked the fix for the whole
session on a false signal.

---

## Why it produced the symptom

The stale files matter because of the original blocker: **DirectWrite/GDI
enumerate `C:\Windows\Fonts` as a directory**, and all copies declare the same
internal family name (`TH Aeonik`). A stale file with a colliding internal name
can win over the registry, which is why HKLM being clean was never sufficient —
the previous two sessions each measured one layer clean and concluded the fix
had landed.

`TH-Aeonik-Regular.otf` surviving is the whole problem in one file: it is the
188,424-byte pre-fix build, and it is exactly what `printpdf3.pdf` embedded.

Bug 2 masking bug 1 produced a specific false signal: the script reported success
(`exit=0`) while queueing nothing. Reading the log would have shown
`FAILED to queue` — but the log is created by the elevated process and is
Administrator-owned, so it was unreadable from WSL. The state was only
established by querying `PendingFileRenameOperations` directly.

---

## Fix

`b5e288e`.

1. **Queue only non-current files.** The loop now skips any basename that
   `INSTALL_ROWS` is about to reinstall:
   ```bash
   for row in "${INSTALL_ROWS[@]}"; do
       [ "$b" = "$(basename "${row%%$'\t'*}")" ] && keep=1 && break
   done
   [ "$keep" = 1 ] && continue
   ```
2. **`[NullString]::Value`** instead of `$null`, and
   `GetLastWin32Error()` reported on failure instead of a bare `FAILED`.
3. **Office guard checks for a real window** —
   `MainWindowHandle -ne 0 -and MainWindowTitle` — and blocks only then.
   Headless processes are reported and execution continues, because every
   deletion is individually verified anyway.

The `-WindowStyle Hidden` on the elevation call was also removed: it can suppress
or hide the UAC dialog, which is indistinguishable from the user declining it.
The first two attempts failed this way and were misreported as "UAC declined."

---

## How it was found

- **Repro:** deterministic. Every `--apply-system` run left the same 20 files.
- **What surfaced it:** the per-file `Test-Path` re-check emitted after each
  delete. Without it, `-ErrorAction SilentlyContinue` would have reported a clean
  run. This check existed from the first version specifically because the
  original blocker had twice been declared fixed on the strength of one layer
  measuring clean.
- **Bug 2 was found by measuring the queue, not by reading the log.** The script
  reported `exit=0`; `PendingFileRenameOperations` contained 68 entries, **none**
  matching `TH-`. That contradiction is what exposed it.
- **Bug 1 was found by reading the generated script after bug 2, not before.**
  It had already run twice.
- **Bug 3 was found by the user contradicting the tool** — "I am not open both
  word and outlook right now." Querying `MainWindowHandle` and `StartTime`
  confirmed it in one command.

---

## Why it slipped through

**Bug 1 — no assertion on the generated artifact.** The script writes a
PowerShell file and executes it elevated. Nothing checked *what it targeted*
before running. The set-difference between "files present" and "files we are
installing" is the entire correctness condition of that loop, and it was implicit.

**Bug 2 — a cross-language marshalling default.** `$null` → `""` for .NET string
parameters is PowerShell-specific behaviour with no diagnostic; the call returns
`false` and sets a Win32 error nobody read. The generated script discarded the
return value into a counter that was never checked against the expected count.

**Bug 3 — the guard encoded the wrong predicate.** "An Office process exists" is
not "a document is open." The distinction only becomes visible on a machine with
a tray-resident Outlook or a crashed Word, which is most real machines.

**The log was unreadable, so the failure mode was invisible.** The elevated
process creates `apply.log` as Administrator. Reading it from WSL as the normal
user fails with `Permission denied`, so the one artifact designed to report
per-operation results could not be read by the tool that generated it.

---

## Validation

**Validated:**

- 20 stale `.otf` are present in `PendingFileRenameOperations`, confirmed by
  reading the value back through `Get-ItemProperty` (not by trusting the script's
  own report, which was what bug 2 falsified).
- **0 `.ttf` are queued** — asserted directly against the generated script
  (`grep MoveFileEx apply.ps1 | grep -c '\.ttf'` → 0) *and* against the registry
  value. This is the assertion whose absence caused bug 1.
- HKLM holds exactly 10 `TH *` values, all pointing at `.ttf`.
- All 10 new `.ttf` are present in `C:\Windows\Fonts`.
- Office guard: re-run on the same machine with the tray Outlook and orphan Word
  still running; proceeds, and reports both as headless.

**NOT validated — this is the honest state:**

- **The deletions have not executed.** They run at boot. The 20 stale `.otf` are
  still on disk right now.
- **The print path is unverified.** No PDF has been produced since the install.
  `check_print_pdf.py` has not been run against a fresh artifact, so defect 3 is
  still not closed end-to-end — which is the thing three sessions have now failed
  to close.
- **Nothing has been seen in Word.** Thai rendering, paste behaviour, the
  TH-Slussen Medium/SemiBold font-picker entries, and TH-Slussen Latin at 9–11 pt
  (which lost its CFF stem hints in `ea0dce2`) are all unobserved.

---

## Action items

- **Reboot, then `./scripts/fix-th-fonts.sh`** — must report 10 files, all
  `[current]`, zero `.otf`. (User, next session.)
- **Reprint `TRR Sritep Resin Test Report - REV01.docx` and run
  `python3 scripts/check_print_pdf.py <new.pdf>`** — must flip STALE→CURRENT and
  BROKEN→OK, and the poppler `Mismatch between font type and embedded font file`
  warnings should disappear now the font really is TrueType. (User + next session.)
- **Word visual check** — Thai renders and pastes cleanly; TH-Slussen Medium and
  SemiBold appear as distinct picker entries; TH-Slussen Latin at 9–11 pt.
  (User; only checkable in Word.)
- **If a fresh print is still stale after the reboot**, the remaining suspect is
  `FNTCACHE.DAT` — stop the FontCache service, delete
  `C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache\*`, reboot.
  (Next session.)
- **Make `apply.log` readable by the invoking user**, or have the elevated script
  write its results somewhere the caller can read. The current arrangement hides
  exactly the diagnostics the script exists to produce. (Next session.)

---

## Learnings

**A generated script is an artifact to assert on, not just to run.** Bug 1 was a
one-line set-difference that was never expressed anywhere. It executed twice
before anyone read it. The check that now catches it —
"zero `.ttf` in the queue" — takes one grep and would have caught it the first
time.

**Two bugs can cancel each other and look like success.** `exit=0` with an empty
queue was the observable. Had bug 2 not existed, the machine would have booted
with the new fonts deleted. Neither bug was individually severe; the combination
was silent, and silence is what made it dangerous. The lesson is not "check the
return value" — it is that a script reporting success while producing no effect
should be as alarming as one reporting failure.

**When the user contradicts the tool, the tool is the hypothesis.** The Office
guard had blocked the fix for the entire session. The user said the applications
were not open. Measuring `MainWindowHandle` took one command and showed the guard
was matching the wrong predicate. This is the same failure the earlier
post-mortems recorded three times — *explaining a mechanism instead of measuring
the next layer* — recurring in the tooling rather than the font.

**Verify the queue, not the queuing code's opinion of itself.** The script
counted its own successes into `$pending` and reported them. That number came
from the same broken call it was measuring. The only trustworthy signal was
reading `PendingFileRenameOperations` back out of the registry — an independent
observation of the state, not a restatement of the intent.
