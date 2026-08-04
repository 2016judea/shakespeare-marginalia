#!/bin/bash
# Print an annotated-play HTML file (from render_annotated_play.py) to PDF via
# headless Chrome/Chromium. No installs needed beyond a Chromium-based browser
# already on your machine.
#
# Usage: ./print_pdf.sh input.html output.pdf
set -e
IN="$1"
OUT="$2"
if [ -z "$IN" ] || [ -z "$OUT" ]; then
  echo "Usage: $0 input.html output.pdf" >&2
  exit 1
fi

# Override by exporting CHROME_BIN yourself if your browser lives elsewhere.
CANDIDATES=(
  "$CHROME_BIN"
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  "/Applications/Chromium.app/Contents/MacOS/Chromium"
  "$(command -v google-chrome || true)"
  "$(command -v chromium || true)"
  "$(command -v chromium-browser || true)"
)
CHROME=""
for c in "${CANDIDATES[@]}"; do
  if [ -n "$c" ] && [ -x "$c" ]; then
    CHROME="$c"
    break
  fi
done
if [ -z "$CHROME" ]; then
  echo "No Chrome/Chromium binary found. Set CHROME_BIN=/path/to/chrome and rerun." >&2
  exit 1
fi

# --no-pdf-header-footer is REQUIRED or Chrome stamps a date/URL/page-number
# header+footer on every page.
"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT" "file://$(cd "$(dirname "$IN")" && pwd)/$(basename "$IN")"
echo "wrote $OUT"
