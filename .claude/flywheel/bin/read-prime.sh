#!/usr/bin/env bash
# flywheel — PreToolUse hook on Read (P3): advisory read-priming.
#
# Before an expensive file read, surface any ledger entries whose typed
# `files=` metadata (see docs/research/git-native-memory-design.md §6) names
# the target file, as cheap prior context.
#
# Contract: ADVISORY ONLY — never blocks the read (unlike claude-mem's File
# Read Gate). Fast and fail-open: no ledger, no match, not a git repo, missing
# python3, or any parse error all produce no output and exit 0.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER="${PROJECT_DIR}/.claude/flywheel/LEARNINGS.md"

# Drain stdin (the PreToolUse hook input is JSON: {"tool_input": {"file_path": …}, …}).
INPUT="$(cat 2>/dev/null)"

[ -f "${LEDGER}" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

FW_LEDGER="${LEDGER}" FW_PROJECT_DIR="${PROJECT_DIR}" FW_HOOK_INPUT="${INPUT}" python3 - <<'PY' 2>/dev/null
import json, os, re, sys

ledger_path = os.environ["FW_LEDGER"]
project_dir = os.environ["FW_PROJECT_DIR"]

try:
    payload = json.loads(os.environ.get("FW_HOOK_INPUT", "") or "{}")
    target = payload.get("tool_input", {}).get("file_path", "")
except Exception:
    target = ""

if not target:
    sys.exit(0)

# Match the ledger's `files=` entries (repo-relative) against the absolute or
# relative path the tool was called with.
target_abs = os.path.normpath(os.path.join(project_dir, target) if not os.path.isabs(target) else target)
try:
    target_rel = os.path.relpath(target_abs, project_dir)
except ValueError:
    target_rel = target

candidates = {target, target_abs, target_rel, os.path.basename(target)}

with open(ledger_path, encoding="utf-8", errors="replace") as fh:
    text = fh.read()

parts = re.split(r"(?m)^(?=## )", text)
entries = [p for p in parts if p.lstrip().startswith("## ")]
meta_re = re.compile(r"^<!--\s*fw:\s*(.*?)\s*-->", re.M)
title_re = re.compile(r"^## (.*)$", re.M)

matches = []
for entry in entries:
    m = meta_re.search(entry)
    if not m:
        continue
    kv = {}
    for pair in m.group(1).split(";"):
        pair = pair.strip()
        if "=" in pair:
            k, v = pair.split("=", 1)
            kv[k.strip()] = v.strip()
    files = {f.strip() for f in kv.get("files", "").split(",") if f.strip()}
    if files & candidates:
        title_m = title_re.search(entry)
        title = title_m.group(1).strip() if title_m else "untitled"
        date = kv.get("date", "")
        matches.append(f"- {title}" + (f" ({date})" if date else ""))

if matches:
    n = len(matches)
    noun = "learning" if n == 1 else "learnings"
    verb = "touches" if n == 1 else "touch"
    print(f"flywheel: {n} prior {noun} {verb} this file — run /flywheel-recall to see the rest:")
    for line in matches:
        print(line)
PY

exit 0
