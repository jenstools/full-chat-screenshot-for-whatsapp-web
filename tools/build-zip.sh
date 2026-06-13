#!/usr/bin/env bash
# Build a Chrome Web Store upload zip containing only the runtime files.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(node -p "require('./manifest.json').version")
OUT="dist/whatsapp-full-chat-screenshot-v${VERSION}.zip"
mkdir -p dist
rm -f "$OUT"

zip -r "$OUT" \
  manifest.json \
  background.js \
  content.js \
  popup.html \
  popup.js \
  icons/icon-16.png icons/icon-32.png icons/icon-48.png icons/icon-128.png \
  > /dev/null

echo "Built $OUT"
