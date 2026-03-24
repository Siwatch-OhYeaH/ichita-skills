#!/bin/bash
# Install TH-Aeonik fonts (Aeonik Latin + Bai Jamjuree Thai)
# Works on: Linux (WSL2/native) + Windows (via WSL2)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FONT_DIR="$SCRIPT_DIR/../assets/fonts/aeonik-th"
FONTS=(TH-Aeonik-Regular.otf TH-Aeonik-Bold.otf TH-Aeonik-Light.otf TH-Aeonik-RegularItalic.otf TH-Aeonik-BoldItalic.otf TH-Aeonik-LightItalic.otf)

echo "🔤 TH-Aeonik Font Installer"
echo ""

# Check fonts exist
if [ ! -f "$FONT_DIR/TH-Aeonik-Regular.otf" ]; then
  echo "❌ Fonts not found at $FONT_DIR"
  echo "   Run from ichita-skills repo root: ./scripts/install-fonts.sh"
  exit 1
fi

# --- Linux ---
install_linux() {
  local dest="$HOME/.local/share/fonts"
  mkdir -p "$dest"
  for f in "${FONTS[@]}"; do
    cp "$FONT_DIR/$f" "$dest/"
  done
  fc-cache -f "$dest"
  echo "✅ Linux: ${#FONTS[@]} fonts installed → $dest"
}

# --- Windows (from WSL2) ---
install_windows() {
  local win_fonts="/mnt/c/Users/$WIN_USER/AppData/Local/Microsoft/Windows/Fonts"

  # Detect Windows username
  if [ -z "$WIN_USER" ]; then
    WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r' || true)
  fi
  if [ -z "$WIN_USER" ]; then
    WIN_USER=$(ls /mnt/c/Users/ | grep -v -E 'Public|Default|All' | head -1)
  fi

  if [ -z "$WIN_USER" ]; then
    echo "⚠️  Cannot detect Windows username. Set WIN_USER=YourName and retry."
    return 1
  fi

  win_fonts="/mnt/c/Users/$WIN_USER/AppData/Local/Microsoft/Windows/Fonts"
  mkdir -p "$win_fonts" 2>/dev/null || true

  local installed=0
  for f in "${FONTS[@]}"; do
    if cp "$FONT_DIR/$f" "$win_fonts/" 2>/dev/null; then
      ((installed++))
    else
      echo "⚠️  $f — close Word/PowerPoint first, then retry"
    fi
  done

  # Register in registry
  if [ $installed -gt 0 ]; then
    powershell.exe -Command "
      \$fontDir = \"\$env:LOCALAPPDATA\\Microsoft\\Windows\\Fonts\"
      \$regPath = 'HKCU:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts'
      Get-ChildItem \"\$fontDir\\TH-Aeonik-*.otf\" | ForEach-Object {
        \$name = \$_.BaseName -replace '-', ' '
        Set-ItemProperty -Path \$regPath -Name \"\$name (OpenType)\" -Value \$_.FullName
      }
    " 2>/dev/null
    echo "✅ Windows: $installed fonts installed + registered → $win_fonts"
  fi

  if [ $installed -lt ${#FONTS[@]} ]; then
    echo "⚠️  $(( ${#FONTS[@]} - installed )) fonts failed — close Office apps and retry"
  fi
}

# --- macOS ---
install_macos() {
  local dest="$HOME/Library/Fonts"
  mkdir -p "$dest"
  for f in "${FONTS[@]}"; do
    cp "$FONT_DIR/$f" "$dest/"
  done
  echo "✅ macOS: ${#FONTS[@]} fonts installed → $dest"
}

# Detect OS
case "$(uname -s)" in
  Linux)
    install_linux
    # If WSL2, also install on Windows
    if grep -qi microsoft /proc/version 2>/dev/null; then
      echo ""
      install_windows
    fi
    ;;
  Darwin)
    install_macos
    ;;
  *)
    echo "❌ Unsupported OS: $(uname -s)"
    exit 1
    ;;
esac

echo ""
echo "📋 Installed fonts:"
echo "   TH Aeonik Regular / Bold / Light + Italics"
echo ""
echo "💡 Restart Word/PowerPoint to see the font."
echo "   Look for 'TH Aeonik' in the font list."
