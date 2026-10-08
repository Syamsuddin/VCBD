#!/usr/bin/env bash
# kemas.sh — buat satu zip per skill di dist/ untuk diunggah ke claude.ai (Settings → Skills).
# Jalankan dari root repo: bash scripts/kemas.sh
set -euo pipefail

cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist

for d in skills/*/; do
  name=$(basename "$d")
  [ -f "$d/SKILL.md" ] || { echo "lewati $name (tanpa SKILL.md)"; continue; }
  (cd skills && zip -qr "../dist/$name.zip" "$name" -x '*/__pycache__/*' '*.pyc' '*/.DS_Store')
  echo "dist/$name.zip"
done
