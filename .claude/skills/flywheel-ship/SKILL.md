---
name: flywheel-ship
description: Close out a unit of work — a clean commit, push, and pull request — following the repo's conventions and the learnings ledger. Use at the very end of a cycle, after verify passes and compound is done.
disable-model-invocation: true
argument-hint: "[branch or PR title]"
allowed-tools: Read, Grep, Glob, Bash(git *)
---

# /flywheel-ship — close out the cycle

Finish and open a PR for: **$ARGUMENTS**

Pre-flight gates (stop if any fails):
- `/flywheel-verify` passed, and `/flywheel-review` has no unresolved Critical/High findings.
- You are on a feature branch, not the default branch. If on the default branch, create one first.

Then:
1. Review the diff (`git status`, `git diff`) — stage intentionally; do not sweep in unrelated files. Include the updated `.claude/flywheel/LEARNINGS.md` from `/flywheel-compound`.
2. Commit with a clear message: **what** changed and **why** (imperative subject; body for rationale/trade-offs).
3. Push the branch (`git push -u origin <branch>`).
4. Open a PR. Check for a PR template first (`.github/pull_request_template.md` and similar) and mirror its sections. Use whatever PR mechanism is available — the GitHub MCP `create_pull_request`, the `gh` CLI, or the web link git prints. Summarize the change and link the spec.
5. Report the PR URL.

Never push straight to the default branch. Never open a PR while a gate is red without an explicit waiver from the user.
