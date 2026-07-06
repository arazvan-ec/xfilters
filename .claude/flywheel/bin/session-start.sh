#!/usr/bin/env bash
# flywheel — SessionStart hook.
# Contract: READ-ONLY and idempotent. It never mutates the working tree.
# Everything printed to stdout is injected into Claude's session context.
# It always exits 0 so a missing ledger can never block a session from starting.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER="${PROJECT_DIR}/.claude/flywheel/LEARNINGS.md"
MAX_LINES=50

echo "🎡 flywheel loaded — a nested loop for disciplined AI development."
echo "   Full cycle:  /flywheel-loop <feature>"
echo "   Phases:      brainstorm → spec → plan → work → verify → review → compound → ship"
echo "   Anytime:     /flywheel-debug (systematic) · /flywheel-autoloop (autonomous) · /flywheel-sync (spec↔code)"
echo ""

# Soft new-version notice for VENDORED installs only (the VERSION file exists
# only in repos vendored by install-vendored.sh; marketplace installs update
# via /plugin update). Fail-silent and bounded to 2s so it can never slow down
# or break session start. Opt out with FLYWHEEL_NO_UPDATE_CHECK=1.
VERSION_FILE="${PROJECT_DIR}/.claude/flywheel/VERSION"
if [ -f "${VERSION_FILE}" ] && [ -z "${FLYWHEEL_NO_UPDATE_CHECK:-}" ] && command -v curl >/dev/null 2>&1; then
  LOCAL_V="$(sed -n 's/^flywheel //p' "${VERSION_FILE}" 2>/dev/null | head -1)"
  REMOTE_V="$(curl -m 2 -fsSL https://raw.githubusercontent.com/arazvan-ec/xmarks/main/.claude-plugin/plugin.json 2>/dev/null \
    | sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
  if [ -n "${LOCAL_V}" ] && [ -n "${REMOTE_V}" ] && [ "${LOCAL_V}" != "${REMOTE_V}" ]; then
    echo "⬆️  flywheel ${REMOTE_V} is available (this repo carries ${LOCAL_V}) — run /flywheel-update to refresh."
    echo ""
  fi
fi

if [ -f "${LEDGER}" ]; then
  echo "📓 Recent flywheel learnings (newest first, from .claude/flywheel/LEARNINGS.md):"
  echo "------------------------------------------------------------------------------"
  head -n "${MAX_LINES}" "${LEDGER}" 2>/dev/null
  echo "------------------------------------------------------------------------------"
  echo "(Use these to avoid repeating past gotchas. /flywheel-compound appends new ones.)"
else
  echo "📓 No flywheel learnings yet. /flywheel-compound will create"
  echo "   .claude/flywheel/LEARNINGS.md at the end of your first cycle."
fi

exit 0
