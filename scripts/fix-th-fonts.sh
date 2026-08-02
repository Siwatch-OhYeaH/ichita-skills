#!/usr/bin/env bash
# fix-th-fonts.sh — repair TH-Aeonik / TH-Slussen font resolution on Windows,
#                   driven entirely from WSL. No PowerShell script in the repo.
#
# WHY THIS EXISTS
#   Word kept embedding the pre-fix fonts in printed PDFs even after the rebuilt
#   files were installed. There are three independent layers, and each was
#   diagnosed only after the one above it was measured clean:
#
#   1. PER-USER registrations (HKCU + %LOCALAPPDATA%\...\Fonts) shadow the
#      machine-wide ones, so a stale per-user copy wins over a correct HKLM
#      entry. Cleaning this is a user-level operation — no elevation.
#
#   2. STALE FILES IN C:\Windows\Fonts. Windows never overwrites a registered
#      font file; it installs alongside as _0, _1, _2. All copies declare the
#      same internal name ("TH Aeonik"), and DirectWrite/GDI enumerate the
#      *directory*, so the oldest plain .otf wins no matter what HKLM says.
#      Measured 2026-08-01: 24 TH-Aeonik-* files where 6 belong, 14 TH-Slussen-*
#      where 4 belong. Cleaning this needs Administrator.
#
#   3. FNTCACHE.DAT, if 1 and 2 are both clean and a fresh print is still stale.
#      Stop the FontCache service, delete the file, reboot.
#
#   Deleting only the *stale* files is not enough: it leaves _2-suffixed
#   survivors that collide again on the next install. --apply-system therefore
#   removes every TH-Aeonik-*/TH-Slussen-* file and registry value, then
#   reinstalls the current build under plain, unsuffixed names.
#
# USAGE
#   ./scripts/fix-th-fonts.sh                 # report all layers + both plans
#   ./scripts/fix-th-fonts.sh --apply         # clean the per-user layer (no admin)
#   ./scripts/fix-th-fonts.sh --apply-system  # wipe + reinstall machine-wide (UAC)
#
#   Close Word/Office first — it locks font files and caches font data for the
#   life of the process. Afterwards, verify a fresh print with:
#     python3 scripts/check_print_pdf.py <newly-printed.pdf>
#   Never judge this by eye; the embedded font is what matters, not the screen.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HKCU_FONTS='HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
HKLM_FONTS='HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
PATTERN='TH Aeonik|TH Slussen'
WINFONTS=/mnt/c/Windows/Fonts

MODE=check
case "${1:-}" in
    --apply) MODE=apply ;;
    --apply-system) MODE=apply-system ;;
    --check|"") MODE=check ;;
    -h|--help) sed -n '2,45p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (use --apply, --apply-system, --check)" >&2; exit 2 ;;
esac

command -v reg.exe >/dev/null 2>&1 || {
    echo "reg.exe not reachable — WSL interop is required (is interop disabled?)" >&2
    exit 1
}

WINUSER="$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\r\n')"
USERFONTS="/mnt/c/Users/${WINUSER}/AppData/Local/Microsoft/Windows/Fonts"

# ---------------------------------------------------------------- current build
# Both extensions: the families ship as .otf today and as .ttf after the glyf
# rebuild. Accepting both lets this script clean up across that transition.
declare -A CUR
BUILT=()
for f in "$REPO"/assets/fonts/aeonik-th/*.otf "$REPO"/assets/fonts/aeonik-th/*.ttf \
         "$REPO"/assets/fonts/slussen-th/*.otf "$REPO"/assets/fonts/slussen-th/*.ttf; do
    [ -f "$f" ] || continue
    CUR["$(basename "$f")"]="$(sha256sum "$f" | cut -c1-12)"
    BUILT+=("$f")
done
[ ${#CUR[@]} -eq 0 ] && { echo "no built fonts under $REPO/assets/fonts — build them first" >&2; exit 1; }

state() {  # $1 = path to a font file -> "current" | "stale" | "missing"
    [ -f "$1" ] || { echo missing; return; }
    local b base h
    b="$(basename "$1")"
    base="$(echo "$b" | sed -E 's/_[0-9]+\.(otf|ttf)$/.\1/; s/\(1\)//')"
    h="$(sha256sum "$1" | cut -c1-12)"
    [ "$h" = "${CUR[$base]:-}" ] && echo current || echo stale
}

reg_lines() {  # $1 = hive key -> "name<TAB>value"
    reg.exe query "$1" 2>/dev/null | tr -d '\r' \
      | grep -E "    REG_SZ" | grep -Ei "$PATTERN" \
      | sed -E 's/^ +//; s/    REG_SZ    /\t/'
}

echo
echo "=== TH font resolution — Windows user: ${WINUSER} ==="

# ------------------------------------------------------------------ report HKLM
echo
echo "[layer 2 — machine-wide: HKLM  ->  C:\\Windows\\Fonts]"
mapfile -t HKLM_ROWS < <(reg_lines "$HKLM_FONTS")
hklm_stale=0
for row in "${HKLM_ROWS[@]}"; do
    name="${row%%$'\t'*}"; file="${row#*$'\t'}"
    st="$(state "${WINFONTS}/${file}")"
    [ "$st" != current ] && hklm_stale=$((hklm_stale+1))
    printf '  %-9s %-40s -> %s\n' "[$st]" "$name" "$file"
done

# ------------------------------------------------------------------ report HKCU
echo
echo "[layer 1 — per-user: HKCU  ->  %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts]"
echo "  these SHADOW the machine-wide entries above"
mapfile -t HKCU_ROWS < <(reg_lines "$HKCU_FONTS")
if [ ${#HKCU_ROWS[@]} -eq 0 ]; then
    echo "  (none — nothing shadowing, good)"
else
    for row in "${HKCU_ROWS[@]}"; do
        name="${row%%$'\t'*}"; file="${row#*$'\t'}"
        wp="$(echo "$file" | sed 's|^[A-Za-z]:|/mnt/c|; s|\\|/|g')"
        printf '  %-9s %-40s -> %s\n' "[$(state "$wp")]" "$name" "$(basename "$file")"
    done
fi

mapfile -t ORPHAN_FILES < <(find "$USERFONTS" -maxdepth 1 \
    \( -name 'TH-Aeonik-*' -o -name 'TH-Slussen-*' \) 2>/dev/null | sort)

# --------------------------------------------------- report physical file layer
echo
echo "[layer 2b — physical files in C:\\Windows\\Fonts]"
mapfile -t SYS_FILES < <(find "$WINFONTS" -maxdepth 1 \
    \( -name 'TH-Aeonik-*' -o -name 'TH-Slussen-*' \) 2>/dev/null | sort)
sys_stale=0
for f in "${SYS_FILES[@]}"; do
    st="$(state "$f")"
    [ "$st" != current ] && sys_stale=$((sys_stale+1))
done
echo "  ${#SYS_FILES[@]} file(s) present, ${sys_stale} stale, ${#BUILT[@]} in the current build"
echo "  DirectWrite/GDI enumerate this directory, so ANY stale file with the same"
echo "  internal family name can win over the registry. All of them must go."

# ============================================================ per-user cleanup
if [ ${#HKCU_ROWS[@]} -gt 0 ] || [ ${#ORPHAN_FILES[@]} -gt 0 ]; then
    if [ "$MODE" = apply ]; then
        if tasklist.exe 2>/dev/null | tr -d '\r' | grep -qiE '^(WINWORD|EXCEL|POWERPNT|OUTLOOK)\.EXE'; then
            echo; echo "!! Office is running. Close it and re-run." >&2; exit 1
        fi
        echo; echo "--- removing per-user registrations ---"
        for row in "${HKCU_ROWS[@]}"; do
            name="${row%%$'\t'*}"
            reg.exe delete "$HKCU_FONTS" /v "$name" /f >/dev/null 2>&1 \
                && echo "  removed  $name" || echo "  FAILED   $name" >&2
        done
        echo; echo "--- removing per-user font files ---"
        for f in "${ORPHAN_FILES[@]}"; do
            rm -f "$f" 2>/dev/null && [ ! -f "$f" ] \
                && echo "  deleted  $(basename "$f")" || echo "  LOCKED   $f" >&2
        done
    else
        echo; echo "--- per-user layer: would remove (--apply) ---"
        for row in "${HKCU_ROWS[@]}"; do echo "  reg delete HKCU value : ${row%%$'\t'*}"; done
        for f in "${ORPHAN_FILES[@]}"; do echo "  delete file           : $f"; done
    fi
else
    echo
    echo "Per-user layer is clean — nothing shadowing."
fi

# ======================================================== machine-wide cleanup
# Registry value name comes from the font's own nameID4 (full font name), which
# is what Windows itself writes. Deriving it from the file rather than hardcoding
# keeps this correct when weights are added or renamed.
mapfile -t INSTALL_ROWS < <(
    python3 - "${BUILT[@]}" <<'PY' 2>/dev/null
import sys
from fontTools.ttLib import TTFont
for p in sys.argv[1:]:
    f = TTFont(p, lazy=True)
    n = f["name"].getName(4, 3, 1, 0x0409) or f["name"].getName(4, 1, 0, 0)
    kind = "TrueType" if p.endswith(".ttf") else "OpenType"
    print(f"{p}\t{n.toUnicode()} ({kind})")
PY
)
if [ ${#INSTALL_ROWS[@]} -ne ${#BUILT[@]} ]; then
    echo >&2
    echo "!! could not read font names (needs fontTools on system python3)." >&2
    echo "   Try: venv_fonts/bin/python — or install fonttools for python3." >&2
    exit 1
fi

echo
echo "--- machine-wide plan (needs Administrator) ---"
echo "  DELETE ${#SYS_FILES[@]} file(s) from C:\\Windows\\Fonts:"
for f in "${SYS_FILES[@]}"; do printf '    - %s  [%s]\n' "$(basename "$f")" "$(state "$f")"; done
echo "  DELETE ${#HKLM_ROWS[@]} HKLM value(s):"
for row in "${HKLM_ROWS[@]}"; do printf '    - %s\n' "${row%%$'\t'*}"; done
echo "  INSTALL ${#INSTALL_ROWS[@]} current file(s) under plain names:"
for row in "${INSTALL_ROWS[@]}"; do
    printf '    + %-32s as "%s"\n' "$(basename "${row%%$'\t'*}")" "${row#*$'\t'}"
done

if [ "$MODE" != apply-system ]; then
    echo
    echo "Dry run. Close Word/Office, then: $0 --apply-system"
    exit 0
fi

# --------------------------------------------------------------------- apply
if tasklist.exe 2>/dev/null | tr -d '\r' | grep -qiE '^(WINWORD|EXCEL|POWERPNT|OUTLOOK)\.EXE'; then
    echo
    echo "!! Office is running. Close Word/Excel/PowerPoint/Outlook and re-run —" >&2
    echo "   it locks the font files and caches font data per process." >&2
    exit 1
fi

# Stage the current build somewhere the elevated session can read without
# touching \\wsl$ (the elevated token has no WSL network drive mapping).
STAGE_WIN="C:\\Windows\\Temp\\th-fonts-stage"
STAGE="/mnt/c/Windows/Temp/th-fonts-stage"
rm -rf "$STAGE" 2>/dev/null
mkdir -p "$STAGE" || { echo "cannot create $STAGE" >&2; exit 1; }
for f in "${BUILT[@]}"; do cp -f "$f" "$STAGE/"; done

# Generate the elevated payload at runtime. It is a temp file, not a repo
# artifact: baking the literal paths in beats nested Start-Process quoting,
# which is unreviewable and silently truncates on the first stray quote.
PS1="$STAGE/apply.ps1"
{
    echo '$ErrorActionPreference = "Continue"'
    echo '$log = "C:\Windows\Temp\th-fonts-stage\apply.log"'
    echo 'function L($m){ $m | Tee-Object -FilePath $log -Append }'
    echo 'L "=== TH font machine-wide repair ==="'
    echo 'Stop-Service FontCache -Force -ErrorAction SilentlyContinue'
    echo '$K = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"'
    for row in "${HKLM_ROWS[@]}"; do
        printf 'Remove-ItemProperty -Path $K -Name "%s" -Force -ErrorAction SilentlyContinue; L "reg-  %s"\n' \
            "${row%%$'\t'*}" "${row%%$'\t'*}"
    done
    for f in "${SYS_FILES[@]}"; do
        b="$(basename "$f")"
        printf 'if (Test-Path "C:\\Windows\\Fonts\\%s") { Remove-Item "C:\\Windows\\Fonts\\%s" -Force -ErrorAction SilentlyContinue }\n' "$b" "$b"
        printf 'L ("file- %-34s " + $(if (Test-Path "C:\\Windows\\Fonts\\%s") {"STILL PRESENT"} else {"gone"}))\n' "$b" "$b"
    done
    for row in "${INSTALL_ROWS[@]}"; do
        src="$(basename "${row%%$'\t'*}")"; name="${row#*$'\t'}"
        printf 'Copy-Item "%s\\%s" "C:\\Windows\\Fonts\\%s" -Force\n' "$STAGE_WIN" "$src" "$src"
        printf 'New-ItemProperty -Path $K -Name "%s" -Value "%s" -PropertyType String -Force | Out-Null\n' "$name" "$src"
        printf 'L ("file+ %-34s " + $(if (Test-Path "C:\\Windows\\Fonts\\%s") {"ok"} else {"FAILED"}))\n' "$src" "$src"
    done
    echo 'Start-Service FontCache -ErrorAction SilentlyContinue'
    echo 'Add-Type @"'
    echo 'using System;using System.Runtime.InteropServices;'
    echo 'public class FC{[DllImport("user32.dll")]public static extern IntPtr SendMessageTimeout('
    echo 'IntPtr h,uint m,IntPtr w,IntPtr l,uint f,uint t,out IntPtr r);}'
    echo '"@'
    echo '$r=[IntPtr]::Zero'
    echo '[void][FC]::SendMessageTimeout([IntPtr]0xffff,0x1D,[IntPtr]::Zero,[IntPtr]::Zero,2,1000,[ref]$r)'
    echo 'L "=== done ==="'
} > "$PS1"

echo
echo "--- elevating (accept the UAC prompt) ---"
rm -f "$STAGE/apply.log"
powershell.exe -NoProfile -Command \
    "Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','${STAGE_WIN}\\apply.ps1'" \
    2>/dev/null

echo
if [ -f "$STAGE/apply.log" ]; then
    sed 's/^/  /' "$STAGE/apply.log"
else
    echo "  !! no log produced — UAC was probably declined." >&2
    exit 1
fi

echo
echo "=== done ==="
echo "Re-run '$0' to confirm every file reads [current] and the count is ${#BUILT[@]}."
echo "Then fully restart Word, reprint, and verify with:"
echo "  python3 scripts/check_print_pdf.py <newly-printed.pdf>"
echo
echo "If a fresh print STILL embeds a stale font, the remaining suspect is layer 3:"
echo "  FNTCACHE.DAT — stop the FontCache service, delete"
echo "  C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\*, reboot."
