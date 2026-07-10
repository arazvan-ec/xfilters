#!/usr/bin/env bash
#
# Package the unpacked extension in extension/ into dist/xfilters-extension.zip.
#
# Why a zip at all? Desktop Chromium installs the folder directly (chrome://
# extensions -> Load unpacked), but Chromium-based *mobile* browsers (Kiwi /
# Lemur / Mises) can only install from a .zip. The committed dist zip is exactly
# what extension/README.md tells phone users to download via GitHub's
# "Download raw file", and CI attaches it to each GitHub release.
#
# manifest.json must sit at the ROOT of the archive (Chromium rejects a manifest
# nested under a folder), so we zip the *contents* of extension/, not the dir.
# README.md and dotfiles are excluded — Chromium ignores them and it keeps the
# package to just the extension's runtime files.
#
# Usage:
#   scripts/package-extension.sh            build dist/xfilters-extension.zip
#   scripts/package-extension.sh --check    verify the committed zip is in sync
#                                            with extension/ (used by CI); exits
#                                            non-zero on drift or if it's missing.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$root/extension"
out="$root/dist/xfilters-extension.zip"

# Build a zip of extension/'s contents at $1. Runs from a subshell so the caller's
# working directory is untouched. Excludes README.md and any dotfiles.
build() {
  local dest="$1"
  rm -f "$dest"
  ( cd "$src" && zip -X -r -9 -q "$dest" . -x 'README.md' -x '.*' -x '*/.*' )
}

if [[ "${1:-}" == "--check" ]]; then
  if [[ ! -f "$out" ]]; then
    echo "MISSING: $out is not committed. Run 'make package' and commit it." >&2
    exit 1
  fi
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  build "$tmp/fresh.zip"
  unzip -q "$out" -d "$tmp/committed"
  unzip -q "$tmp/fresh.zip" -d "$tmp/fresh"
  if ! diff -r "$tmp/committed" "$tmp/fresh" >/dev/null; then
    echo "OUT OF DATE: dist/xfilters-extension.zip does not match extension/." >&2
    echo "Run 'make package' and commit the updated zip." >&2
    diff -r "$tmp/committed" "$tmp/fresh" >&2 || true
    exit 1
  fi
  echo "OK: dist/xfilters-extension.zip is in sync with extension/."
  exit 0
fi

mkdir -p "$(dirname "$out")"
build "$out"
echo "Built ${out#"$root"/}"
unzip -l "$out"
