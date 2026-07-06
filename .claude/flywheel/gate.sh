#!/usr/bin/env bash
# xfilters verification gate — run by flywheel's Stop hook before a turn ends.
# This project has no test framework, so the gate does what's real and cheap:
# every tracked JS/MJS file parses, every tracked JSON file is valid, and the
# seams between files (index.html <-> data/bookmarks.js, extension manifest
# <-> its assets) haven't silently drifted apart. Extend this if the project
# ever gains real tests or a linter.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

fail=0

while IFS= read -r f; do
  out="$(node --check "$f" 2>&1)" || { echo "FAIL: $f does not parse"; echo "$out"; fail=1; }
done < <(git ls-files '*.js' '*.mjs')

while IFS= read -r f; do
  out="$(node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$f" 2>&1)" \
    || { echo "FAIL: $f is not valid JSON"; echo "$out"; fail=1; }
done < <(git ls-files '*.json')

grep -q 'data/bookmarks\.js' index.html \
  || { echo "FAIL: index.html no longer references data/bookmarks.js"; fail=1; }
grep -q '"manifest_version": *3' extension/manifest.json \
  || { echo "FAIL: extension/manifest.json no longer declares manifest_version 3"; fail=1; }
[ -f extension/icon.png ] \
  || { echo "FAIL: extension/icon.png is missing (referenced from extension/manifest.json)"; fail=1; }

# Kiwi/Chrome only loads a zip's manifest.json if it sits at the archive root.
if [ -f dist/xfilters-extension.zip ] && command -v python3 >/dev/null 2>&1; then
  python3 -c "
import zipfile, sys
names = zipfile.ZipFile('dist/xfilters-extension.zip').namelist()
sys.exit(0 if 'manifest.json' in names else 1)
" || { echo "FAIL: dist/xfilters-extension.zip must contain manifest.json at its root"; fail=1; }
fi

if [ "$fail" -ne 0 ]; then
  exit 1
fi

echo "gate OK: $(git ls-files '*.js' '*.mjs' | wc -l | tr -d ' ') JS/MJS files parse, $(git ls-files '*.json' | wc -l | tr -d ' ') JSON files valid, file references check out"
