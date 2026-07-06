#!/usr/bin/env bash
# flywheel — deterministic completion gate (Stop hook).
#
# OPT-IN: this gate only does anything if the project defines an executable
#   "$CLAUDE_PROJECT_DIR/.claude/flywheel/gate.sh"
# containing the project's own verification command, e.g.:
#   #!/usr/bin/env bash
#   npm test && npm run lint
#
# When that file exists, this hook runs it whenever Claude tries to finish a
# turn. If it fails, the turn is blocked (exit 2, output fed back to Claude)
# so work isn't declared "done" with checks red. When it doesn't exist, this
# is a no-op — projects that haven't opted in are never affected.
#
# Safety: bounded to MAX consecutive blocks (escape valve so you're never
# trapped), and fail-open on any internal error.

# Drain stdin (the hook receives JSON we don't need); ignore failures.
cat >/dev/null 2>&1 || true

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
GATE="${PROJECT_DIR}/.claude/flywheel/gate.sh"
STATE="${PROJECT_DIR}/.claude/flywheel/.gate-state"
MAX=3

# Not opted in → allow (no-op).
if [ ! -x "${GATE}" ]; then
  rm -f "${STATE}" 2>/dev/null
  exit 0
fi

# Run the project's verification command from the project root; capture output.
OUT="$( cd "${PROJECT_DIR}" && bash "${GATE}" 2>&1 )"
CODE=$?

if [ "${CODE}" -eq 0 ]; then
  rm -f "${STATE}" 2>/dev/null   # gate green → reset counter and allow the turn to end
  exit 0
fi

# Gate failed. Bound consecutive blocks so we never trap the user.
COUNT=0
[ -f "${STATE}" ] && COUNT="$(tr -dc '0-9' < "${STATE}" 2>/dev/null)"
[ -z "${COUNT}" ] && COUNT=0

if [ "${COUNT}" -ge "${MAX}" ]; then
  rm -f "${STATE}" 2>/dev/null
  {
    echo "flywheel gate: still failing after ${MAX} attempts — bypassing so you aren't blocked."
    echo "Fix these before shipping:"
    echo "${OUT}" | tail -n 40
  } >&2
  exit 0   # fail-open escape valve
fi

echo $((COUNT + 1)) > "${STATE}" 2>/dev/null

{
  echo "flywheel gate FAILED (.claude/flywheel/gate.sh exited ${CODE}). Do not finish until this is green — fix and re-run:"
  echo "${OUT}" | tail -n 40
} >&2
exit 2   # block the turn from ending; stderr is fed back to Claude
