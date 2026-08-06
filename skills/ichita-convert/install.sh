#!/usr/bin/env bash
# Install ichita-convert's dependencies and report what is missing.
#
# The three system tools are not pip-installable and each one silently changes
# what the skill can do, so this reports rather than assumes:
#
#   pandoc     docx -> md. Without it the inbound DOCX leg does not run at all.
#   soffice    LibreOffice. The delivery PDF engine — see reference/pdf-delivery.md.
#   pdftoppm   poppler-utils. Renders a page to PNG so you can look at the artifact.
set -e
cd "$(dirname "$0")"

pip install -r requirements.txt

# Playwright ships the package and the browser separately. Without this step
# pip reports success and rendering raises at the first scripted or Thai
# document — so do it here, loudly, rather than leaving it to surprise someone.
echo
echo "Chromium for the PDF engine (~150 MB on first install):"
python3 -m playwright install chromium

echo
echo "System tools:"
missing=0
for tool in pandoc soffice pdftoppm; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf "  %-10s OK\n" "$tool"
    else
        printf "  %-10s MISSING\n" "$tool"
        missing=1
    fi
done

if [ "$missing" -eq 1 ]; then
    echo
    echo "Install the missing ones:"
    echo "  Debian/Ubuntu  sudo apt install pandoc libreoffice-writer poppler-utils"
    echo "  macOS          brew install pandoc poppler && brew install --cask libreoffice"
    echo
    echo "The skill runs without them, but the legs that need them will exit"
    echo "with an error rather than degrade quietly."
fi

echo
echo "Verify:"
echo "  python3 tests/test_md_clean.py      # 27 unit tests"
echo "  python3 tests/test_roundtrip.py     # 23 end-to-end"
