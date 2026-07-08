#!/usr/bin/env bash
# flywheel — SessionStart hook.
# Contract: READ-ONLY and idempotent. It never mutates the working tree.
# Everything printed to stdout is injected into Claude's session context.
# It always exits 0 so a missing ledger — or any parsing hiccup — can never
# block a session from starting.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER="${PROJECT_DIR}/.claude/flywheel/LEARNINGS.md"
INJECT_N="${FLYWHEEL_LEARNINGS_INJECT:-12}"
case "${INJECT_N}" in ''|*[!0-9]*) INJECT_N=12 ;; esac

echo "🎡 flywheel loaded — a nested loop for disciplined AI development."
echo "   Full cycle:  /flywheel-loop <feature>"
echo "   Phases:      brainstorm → spec → plan → work → verify → review → compound → ship"
echo "   Anytime:     /flywheel-debug (systematic) · /flywheel-autoloop (autonomous) · /flywheel-sync (spec↔code) · /flywheel-recall (search learnings)"
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

if [ ! -f "${LEDGER}" ]; then
  echo "📓 No flywheel learnings yet. /flywheel-compound will create"
  echo "   .claude/flywheel/LEARNINGS.md at the end of your first cycle."
  exit 0
fi

# --- Relevance context (best-effort). Any command below that fails just
# yields an empty value, which degrades to "this signal scores 0" — the
# ranking still runs, it's just less targeted. Never allowed to abort. ---
BRANCH="$(cd "${PROJECT_DIR}" 2>/dev/null && git branch --show-current 2>/dev/null)"
DEFAULT_BRANCH="$(cd "${PROJECT_DIR}" 2>/dev/null && git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
CHANGED_FILES="$(cd "${PROJECT_DIR}" 2>/dev/null && {
    git diff --name-only "${DEFAULT_BRANCH}...HEAD" 2>/dev/null
    git diff --name-only 2>/dev/null
    git diff --name-only --cached 2>/dev/null
  } | sort -u)"
SPEC="$(ls -t "${PROJECT_DIR}"/.claude/flywheel/specs/*.md 2>/dev/null | head -1 | xargs -n1 basename 2>/dev/null | sed 's/\.plan\.md$//; s/\.md$//')"
CUTOFF="$(date -d '-30 days' +%F 2>/dev/null)"

echo "📓 Relevant flywheel learnings (branch=${BRANCH:-?}${SPEC:+, spec=${SPEC}}):"
echo "------------------------------------------------------------------------------"
LEARNINGS_OUT="$(BRANCH="${BRANCH}" SPEC="${SPEC}" CUTOFF="${CUTOFF}" CHANGED_FILES="${CHANGED_FILES}" INJECT_N="${INJECT_N}" \
  awk '
    function save_entry(   ) {
      if (!started || entry == "") return
      n++
      body[n] = entry
      date_arr[n] = ent_date
      files_arr[n] = ent_files
      branch_arr[n] = ent_branch
      spec_arr[n] = ent_spec
      entry = ""
    }
    function files_match(i,    nf, farr, k) {
      if (files_arr[i] == "") return 0
      nf = split(files_arr[i], farr, ",")
      for (k = 1; k <= nf; k++) {
        gsub(/^ +| +$/, "", farr[k])
        if (farr[k] in changed) return 1
      }
      return 0
    }
    BEGIN {
      n = 0; entry = ""; started = 0
      split(ENVIRON["CHANGED_FILES"], cf_lines, "\n")
      for (i in cf_lines) if (cf_lines[i] != "") changed[cf_lines[i]] = 1
      branch = ENVIRON["BRANCH"]
      spec = ENVIRON["SPEC"]
      cutoff = ENVIRON["CUTOFF"]
      inject_n = ENVIRON["INJECT_N"] + 0
      if (inject_n <= 0) inject_n = 12
    }
    /^## / {
      if (started) save_entry()
      started = 1
      entry = $0 "\n"
      header = $0
      meta_seen = 0
      ent_date = ""; ent_files = ""; ent_branch = ""; ent_spec = ""
      next
    }
    {
      if (!started) next
      if (!meta_seen) {
        meta_seen = 1
        if ($0 ~ /^<!-- fw: /) {
          metaline = $0
          sub(/^<!-- fw: /, "", metaline)
          sub(/ -->[[:space:]]*$/, "", metaline)
          nkv = split(metaline, kvs, "; ")
          for (k = 1; k <= nkv; k++) {
            split(kvs[k], pair, "=")
            if (pair[1] == "date") ent_date = pair[2]
            else if (pair[1] == "files") ent_files = pair[2]
            else if (pair[1] == "branch") ent_branch = pair[2]
            else if (pair[1] == "spec") ent_spec = pair[2]
          }
        } else if (header ~ /^## [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] /) {
          ent_date = substr(header, 4, 10)
        }
      }
      entry = entry $0 "\n"
    }
    END {
      save_entry()
      for (i = 1; i <= n; i++) {
        s = 0
        if (files_match(i)) s += 3
        if ((branch_arr[i] != "" && branch_arr[i] == branch) || (spec_arr[i] != "" && spec_arr[i] == spec)) s += 2
        if (cutoff != "" && date_arr[i] != "" && date_arr[i] >= cutoff) s += 1
        score[i] = s
        order[i] = i
      }
      for (i = 1; i <= n; i++) {
        for (j = i + 1; j <= n; j++) {
          oi = order[i]; oj = order[j]
          if (score[oj] > score[oi] || (score[oj] == score[oi] && date_arr[oj] > date_arr[oi])) {
            tmp = order[i]; order[i] = order[j]; order[j] = tmp
          }
        }
      }
      shown = (inject_n < n ? inject_n : n)
      for (i = 1; i <= shown; i++) printf "%s", body[order[i]]
      remaining = n - shown
      if (remaining > 0) {
        printf "\n... %d more learning%s -- run /flywheel-recall <query> to pull specifics.\n", remaining, (remaining == 1 ? "" : "s")
      }
    }
  ' "${LEDGER}" 2>/dev/null)"
if [ -n "${LEARNINGS_OUT}" ]; then
  printf '%s\n' "${LEARNINGS_OUT}"
else
  echo "(ledger exists but has no readable entries yet)"
fi
echo "------------------------------------------------------------------------------"
echo "(Use these to avoid repeating past gotchas. /flywheel-recall <query> pulls anything not shown here. /flywheel-compound appends new ones.)"

exit 0
