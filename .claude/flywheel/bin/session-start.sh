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
