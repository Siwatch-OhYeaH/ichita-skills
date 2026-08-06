#!/usr/bin/env bash
# =============================================================================
# install-fonts.sh — Ichita Font Installer
# =============================================================================
# Installs all Ichita branded fonts system-wide:
#   - TH Aeonik (6 files)  — unified Thai+Latin primary brand font
#   - Aeonik (14 files)    — Latin-only original
#   - Bai Jamjuree (12 files) — Thai fallback font
#   - Betatron (1 file)    — special/display font
#
# Usage:
#   ./install-fonts.sh            — install fonts (default)
#   ./install-fonts.sh --check    — verify fonts are installed, don't install
#   ./install-fonts.sh --uninstall — remove installed fonts
#
# Exit codes:
#   0 — success (or all fonts present on --check)
#   1 — error
#   2 — fonts missing (--check mode only)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/../assets/fonts"

# ── Mode flag ─────────────────────────────────────────────────────────────────
MODE="install"
if [[ "${1:-}" == "--check" ]]; then
    MODE="check"
elif [[ "${1:-}" == "--uninstall" ]]; then
    MODE="uninstall"
elif [[ -n "${1:-}" ]]; then
    echo "ERROR: Unknown flag: ${1}" >&2
    echo "Usage: $0 [--check | --uninstall]" >&2
    exit 1
fi

# ── Detect OS and set target directory ───────────────────────────────────────
detect_platform() {
    local os
    os="$(uname -s)"
    case "$os" in
        Linux)
            FONT_DEST="$HOME/.local/share/fonts/ichita"
            IS_WSL=false
            if grep -qi microsoft /proc/version 2>/dev/null; then
                IS_WSL=true
            fi
            ;;
        Darwin)
            FONT_DEST="$HOME/Library/Fonts"
            IS_WSL=false
            ;;
        *)
            echo "ERROR: Unsupported OS: $os" >&2
            exit 1
            ;;
    esac
}

# ── Collect all font files from subdirectories ───────────────────────────────
collect_fonts() {
    FONT_FILES=()
    local count=0

    # Verify the assets directory exists
    if [[ ! -d "$ASSETS_DIR" ]]; then
        echo "ERROR: Font assets directory not found: $ASSETS_DIR" >&2
        echo "       Run this script from within the ichita-skills repo." >&2
        exit 1
    fi

    # Collect .otf and .ttf from all subdirectories EXCEPT the build source.
    #
    # aeonik-v1000/ is CoType's pristine v1.000 — the input to build_aeonik.py,
    # never installed. It is git-ignored, so it is absent on a fresh clone, but
    # anyone who rebuilds the fonts will have dropped it there. Its faces share
    # both the family name AND the filenames of the v1.001 build in aeonik/,
    # and this loop flattens everything to one destination by basename, so
    # including it would leave sort order deciding which Aeonik the machine
    # ends up with — and v1.000 has no Greek. That is the stale-file-wins
    # failure in THAI-LATIN-FONT-ENGINEERING.md §9.
    while IFS= read -r -d '' f; do
        FONT_FILES+=("$f")
        count=$((count + 1))
    done < <(find "$ASSETS_DIR" -type d -name "aeonik-v1000" -prune -o \
                  \( -name "*.otf" -o -name "*.ttf" \) -type f -print0 | sort -z)

    if [[ $count -eq 0 ]]; then
        echo "ERROR: No .otf or .ttf files found under $ASSETS_DIR" >&2
        exit 1
    fi

    FONT_COUNT=$count
}

# ── Install fonts ─────────────────────────────────────────────────────────────
do_install() {
    echo "Ichita Font Installer"
    echo "Target: $FONT_DEST"
    echo "Source: $ASSETS_DIR"
    echo ""

    mkdir -p "$FONT_DEST"

    local installed=0
    local skipped=0
    local errors=0

    for src in "${FONT_FILES[@]}"; do
        local filename
        filename="$(basename "$src")"
        local dest="$FONT_DEST/$filename"

        if [[ -f "$dest" ]]; then
            # Already exists — check if identical
            if cmp -s "$src" "$dest"; then
                echo "  [SKIP] $filename (already up to date)"
                ((skipped=$((skipped + 1))))
                continue
            else
                echo "  [UPDATE] $filename"
            fi
        else
            echo "  [INSTALL] $filename"
        fi

        if cp "$src" "$dest"; then
            ((installed=$((installed + 1))))
        else
            echo "  [ERROR] Failed to copy $filename" >&2
            ((errors=$((errors + 1))))
        fi
    done

    echo ""
    echo "Summary: $installed installed, $skipped skipped, $errors errors"
    echo ""

    if [[ $errors -gt 0 ]]; then
        echo "ERROR: $errors font(s) failed to install." >&2
        exit 1
    fi

    # Refresh font cache
    refresh_cache

    # Verify installation
    verify_installation
}

# ── Refresh font cache ────────────────────────────────────────────────────────
refresh_cache() {
    case "$(uname -s)" in
        Linux)
            echo "Refreshing font cache (fc-cache -fv)..."
            fc-cache -fv "$FONT_DEST" 2>&1 | tail -5
            echo ""
            ;;
        Darwin)
            # macOS does not need manual cache refresh — fonts in ~/Library/Fonts
            # are immediately available. atsutil databases -removeUser is deprecated.
            echo "macOS: fonts installed. Restart apps to use new fonts."
            echo ""
            ;;
    esac

    # WSL2 — also install on Windows side
    if [[ "${IS_WSL:-false}" == "true" ]]; then
        install_windows
    fi
}

# ── Windows installation via WSL2 ─────────────────────────────────────────────
install_windows() {
    echo "WSL2 detected — also installing on Windows side..."

    # Detect Windows username
    local win_user="${WIN_USER:-}"
    if [[ -z "$win_user" ]]; then
        win_user=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r' || true)
    fi
    if [[ -z "$win_user" ]]; then
        win_user=$(ls /mnt/c/Users/ 2>/dev/null | grep -vE 'Public|Default|All Users|defaultuser' | head -1 || true)
    fi

    if [[ -z "$win_user" ]]; then
        echo "  WARNING: Cannot detect Windows username." >&2
        echo "           Set WIN_USER=YourWindowsUsername and re-run." >&2
        return 0
    fi

    local win_fonts="/mnt/c/Users/$win_user/AppData/Local/Microsoft/Windows/Fonts"
    mkdir -p "$win_fonts" 2>/dev/null || true

    local win_installed=0
    local win_errors=0

    for src in "${FONT_FILES[@]}"; do
        local filename
        filename="$(basename "$src")"
        if cp "$src" "$win_fonts/$filename" 2>/dev/null; then
            ((win_installed=$((installed + 1))))
        else
            echo "  WARNING: Could not copy $filename to Windows — close Office apps and retry." >&2
            ((win_errors=$((errors + 1))))
        fi
    done

    # Register fonts in Windows registry so Office apps can see them
    if [[ $win_installed -gt 0 ]]; then
        powershell.exe -Command "
            \$fontDir  = \"\$env:LOCALAPPDATA\\Microsoft\\Windows\\Fonts\"
            \$regPath  = 'HKCU:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts'
            Get-ChildItem \"\$fontDir\" -Include '*.otf','*.ttf' | ForEach-Object {
                \$name = \$_.BaseName -replace '-', ' '
                Set-ItemProperty -Path \$regPath -Name \"\$name (OpenType)\" -Value \$_.FullName
            }
        " 2>/dev/null && echo "  Windows registry updated."
    fi

    echo "  Windows: $win_installed installed, $win_errors errors"
    echo ""
}

# ── Verify installation ───────────────────────────────────────────────────────
verify_installation() {
    echo "Verifying font installation..."
    echo ""

    local families=("TH Aeonik" "Aeonik" "Bai Jamjuree" "Betatron")
    local patterns=("aeonik" "aeonik" "jamjuree" "betatron")
    local all_ok=true

    case "$(uname -s)" in
        Linux)
            for i in "${!families[@]}"; do
                local family="${families[$i]}"
                local pattern="${patterns[$i]}"
                local hits
                hits=$(fc-list 2>/dev/null | grep -ic "$pattern" || echo 0)
                if [[ "$hits" -gt 0 ]]; then
                    printf "  [OK] %-20s — %d variant(s) found\n" "$family" "$hits"
                else
                    printf "  [MISSING] %-20s — not found in fc-list\n" "$family"
                    all_ok=false
                fi
            done
            ;;
        Darwin)
            # On macOS use system_profiler or just check file presence
            for src in "${FONT_FILES[@]}"; do
                local filename
                filename="$(basename "$src")"
                if [[ -f "$FONT_DEST/$filename" ]]; then
                    echo "  [OK] $filename"
                else
                    echo "  [MISSING] $filename"
                    all_ok=false
                fi
            done
            ;;
    esac

    echo ""
    if [[ "$all_ok" == "true" ]]; then
        echo "All Ichita fonts verified."
    else
        echo "WARNING: Some fonts were not detected. Try running fc-cache -fv and retry." >&2
    fi
}

# ── Check mode (--check) ──────────────────────────────────────────────────────
do_check() {
    echo "Ichita Font Check"
    echo ""

    local missing=0
    local found=0

    case "$(uname -s)" in
        Linux)
            echo "Running fc-list check..."
            local hits
            hits=$(fc-list 2>/dev/null | grep -ic "aeonik\|jamjuree\|betatron" || echo 0)
            echo "  Fonts matching Ichita patterns: $hits"

            # Also check files on disk
            echo ""
            echo "Checking installed files at $FONT_DEST:"
            for src in "${FONT_FILES[@]}"; do
                local filename
                filename="$(basename "$src")"
                if [[ -f "$FONT_DEST/$filename" ]]; then
                    echo "  [OK]      $filename"
                    ((found=$((found + 1))))
                else
                    echo "  [MISSING] $filename"
                    ((missing=$((missing + 1))))
                fi
            done
            ;;
        Darwin)
            echo "Checking installed files at $FONT_DEST:"
            for src in "${FONT_FILES[@]}"; do
                local filename
                filename="$(basename "$src")"
                if [[ -f "$FONT_DEST/$filename" ]]; then
                    echo "  [OK]      $filename"
                    ((found=$((found + 1))))
                else
                    echo "  [MISSING] $filename"
                    ((missing=$((missing + 1))))
                fi
            done
            ;;
    esac

    echo ""
    echo "Summary: $found found, $missing missing (out of $FONT_COUNT total)"

    if [[ $missing -gt 0 ]]; then
        echo ""
        echo "Run without flags to install missing fonts: $0"
        exit 2
    else
        echo "All Ichita fonts are installed."
        exit 0
    fi
}

# ── Uninstall mode (--uninstall) ──────────────────────────────────────────────
do_uninstall() {
    echo "Ichita Font Uninstaller"
    echo "Target: $FONT_DEST"
    echo ""

    if [[ ! -d "$FONT_DEST" ]]; then
        echo "Font directory does not exist: $FONT_DEST"
        echo "Nothing to uninstall."
        exit 0
    fi

    local removed=0
    local not_found=0

    for src in "${FONT_FILES[@]}"; do
        local filename
        filename="$(basename "$src")"
        local dest="$FONT_DEST/$filename"
        if [[ -f "$dest" ]]; then
            rm "$dest"
            echo "  [REMOVED] $filename"
            ((removed=$((removed + 1))))
        else
            echo "  [NOT FOUND] $filename"
            ((not_found=$((found + 1))))
        fi
    done

    # Clean up directory if empty
    if [[ -d "$FONT_DEST" ]] && [[ -z "$(ls -A "$FONT_DEST" 2>/dev/null)" ]]; then
        rmdir "$FONT_DEST"
        echo ""
        echo "Removed empty directory: $FONT_DEST"
    fi

    echo ""
    echo "Summary: $removed removed, $not_found not found"

    # Refresh cache after removal
    case "$(uname -s)" in
        Linux)
            echo ""
            echo "Refreshing font cache..."
            fc-cache -fv 2>&1 | tail -3
            ;;
    esac

    echo ""
    echo "Uninstall complete. Restart apps to apply changes."
}

# ── Main ──────────────────────────────────────────────────────────────────────
detect_platform
collect_fonts

echo ""
echo "Found $FONT_COUNT font files across all Ichita families."
echo ""

case "$MODE" in
    install)   do_install ;;
    check)     do_check ;;
    uninstall) do_uninstall ;;
esac
