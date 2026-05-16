#!/usr/bin/env bash
set -euo pipefail

rm -f source-bundle.zip
zip -qr source-bundle.zip . \
  -x "*.git*" \
  -x "node_modules/*" \
  -x "reports/*" \
  -x ".venv/*" \
  -x "__pycache__/*"

