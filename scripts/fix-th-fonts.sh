#!/usr/bin/env bash
# fix-th-fonts.sh — repair TH-Aeonik / TH-Slussen font resolution on Windows,
#                   driven entirely from WSL. No PowerShell script, no admin.
#
# WHY THIS EXISTS
#   Word kept embedding the pre-fix fonts in printed PDFs even after the rebuilt
#   files were installed. The machine-wide store was fine — HKLM already pointed
#   at the current files. The problem was the PER-USER font store:
#
#     HKLM  "TH Aeonik (TrueType)" -> TH-Aeonik-Regular_2.otf                (current)
#     HKCU  "TH Aeonik (TrueType)" -> %LOCALAPPDATA%\...\TH-Aeonik-Regular.otf (Mar 24, pre-fix)
#
#   Per-user registrations win over machine-wide ones, so every application
#   resolved "TH Aeonik" to the stale per-user copy. Deleting those per-user
#   registrations and files makes Windows fall through to the correct HKLM
#   entries — which is a user-level operation, so no elevation is required and
#   it can all be done from WSL through reg.exe and /mnt/c.
#
# USAGE
#   ./scripts/fix-th-fonts.sh              # dry run — shows what it would do
#   ./scripts/fix-th-fonts.sh --apply      # do it
#   ./scripts/fix-th-fonts.sh --check      # just report current resolution
#
#   Close Word/Office first — it locks font files and caches font data for the
#   life of the process. Afterwards, verify a fresh print with:
#     python3 scripts/check_print_pdf.py <newly-printed.pdf>

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HKCU_FONTS='HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
HKLM_FONTS='HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
PATTERN='TH Aeonik|TH Slussen'

MODE=check
case "${1:-}" in
    --apply) MODE=apply ;;
    --check|"") MODE=check ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (use --apply, --check)" >&2; exit 2 ;;
esac

command -v reg.exe >/dev/null 2>&1 || {
    echo "reg.exe not reachable — WSL interop is required (is interop disabled?)" >&2
    exit 1
}

WINUSER="$(cmd.exe /c 'echo %USERNAME%' 2>/dev/null | tr -d '\r\n')"
USERFONTS="/mnt/c/Users/${WINUSER}/AppData/Local/Microsoft/Windows/Fonts"

# ---------------------------------------------------------------- current build
declare -A CUR
for f in "$REPO"/assets/fonts/aeonik-th/*.otf "$REPO"/assets/fonts/slussen-th/*.otf; do
    [ -f "$f" ] && CUR["$(basename "$f")"]="$(sha256sum "$f" | cut -c1-12)"
done
[ ${#CUR[@]} -eq 0 ] && { echo "no built fonts under $REPO/assets/fonts — build them first" >&2; exit 1; }

state() {  # $1 = path to a font file -> "current" | "stale" | "missing"
    [ -f "$1" ] || { echo missing; return; }
    local b base h
    b="$(basename "$1")"
    base="$(echo "$b" | sed 's/_[0-9]*\.otf$/.otf/; s/(1)//')"
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
echo "[machine-wide: HKLM  ->  C:\\Windows\\Fonts]"
hklm_stale=0
while IFS=$'\t' read -r name file; do
    [ -z "${name:-}" ] && continue
    st="$(state "/mnt/c/Windows/Fonts/${file}")"
    [ "$st" != current ] && hklm_stale=$((hklm_stale+1))
    printf '  %-8s %-40s -> %s\n' "[$st]" "$name" "$file"
done < <(reg_lines "$HKLM_FONTS")

# ------------------------------------------------------------------ report HKCU
echo
echo "[per-user: HKCU  ->  %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts]"
echo "  these SHADOW the machine-wide entries above"
mapfile -t HKCU_ROWS < <(reg_lines "$HKCU_FONTS")
if [ ${#HKCU_ROWS[@]} -eq 0 ]; then
    echo "  (none — nothing shadowing, good)"
else
    for row in "${HKCU_ROWS[@]}"; do
        name="${row%%$'\t'*}"; file="${row#*$'\t'}"
        wp="$(echo "$file" | sed 's|^[A-Za-z]:|/mnt/c|; s|\\|/|g')"
        printf '  %-8s %-40s -> %s\n' "[$(state "$wp")]" "$name" "$(basename "$file")"
    done
fi

# ------------------------------------------------------------------- leftovers
mapfile -t ORPHAN_FILES < <(find "$USERFONTS" -maxdepth 1 \
    \( -name 'TH-Aeonik-*.otf' -o -name 'TH-Slussen-*.otf' \) 2>/dev/null | sort)

if [ ${#HKCU_ROWS[@]} -eq 0 ] && [ ${#ORPHAN_FILES[@]} -eq 0 ]; then
    echo
    echo "Nothing to clean. Applications should resolve to the machine-wide files."
    [ "$hklm_stale" -gt 0 ] && echo "Note: $hklm_stale machine-wide entry(ies) are stale — see below."
    exit 0
fi

# ------------------------------------------------------------------- dry run
if [ "$MODE" = check ]; then
    echo
    echo "--- would remove (re-run with --apply) ---"
    for row in "${HKCU_ROWS[@]}"; do
        echo "  reg delete HKCU value : ${row%%$'\t'*}"
    done
    for f in "${ORPHAN_FILES[@]}"; do echo "  delete file           : $f"; done
    echo
    echo "Close Word first, then: $0 --apply"
    exit 0
fi

# --------------------------------------------------------------------- apply
if tasklist.exe 2>/dev/null | tr -d '\r' | grep -qiE '^(WINWORD|EXCEL|POWERPNT|OUTLOOK)\.EXE'; then
    echo
    echo "!! Office is running. Close Word/Excel/PowerPoint/Outlook and re-run —" >&2
    echo "   it locks the font files and caches font data per process." >&2
    exit 1
fi

echo
echo "--- removing per-user registrations ---"
for row in "${HKCU_ROWS[@]}"; do
    name="${row%%$'\t'*}"
    if reg.exe delete "$HKCU_FONTS" /v "$name" /f >/dev/null 2>&1; then
        echo "  removed  $name"
    else
        echo "  FAILED   $name" >&2
    fi
done

echo
echo "--- removing per-user font files ---"
for f in "${ORPHAN_FILES[@]}"; do
    if rm -f "$f" 2>/dev/null && [ ! -f "$f" ]; then
        echo "  deleted  $(basename "$f")"
    else
        echo "  LOCKED   $f" >&2
    fi
done

# tell running applications the font table changed (no elevation needed)
powershell.exe -NoProfile -Command '
Add-Type @"
using System;using System.Runtime.InteropServices;
public class FC{[DllImport("user32.dll")]public static extern IntPtr SendMessageTimeout(
IntPtr h,uint m,IntPtr w,IntPtr l,uint f,uint t,out IntPtr r);}
"@
$r=[IntPtr]::Zero
[void][FC]::SendMessageTimeout([IntPtr]0xffff,0x1D,[IntPtr]::Zero,[IntPtr]::Zero,2,1000,[ref]$r)
' >/dev/null 2>&1

echo
echo "=== done ==="
echo "Re-run '$0' to confirm the per-user list is empty."
echo "Then reprint and verify with:"
echo "  python3 scripts/check_print_pdf.py <newly-printed.pdf>"
if [ "$hklm_stale" -gt 0 ]; then
    cat <<'EOF'

Optional, needs Administrator (orphan machine-wide entries from an older
10-weight TH-Slussen — harmless, but they clutter the font list). To clear them,
run this from WSL; it will raise a UAC prompt:

  powershell.exe -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-Command','
    Get-Item ''HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'' |
      Select-Object -Expand Property |
      Where-Object { $_ -match ''TH Slussen (Light|Italic|Medium Italic|Semibold Italic|Bold Italic)'' } |
      ForEach-Object { Remove-ItemProperty -Path ''HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'' -Name $_ }'"
EOF
fi
