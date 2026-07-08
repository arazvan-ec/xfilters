---
name: flywheel-review
description: Adversarial multi-specialist code review — dispatch correctness, security, and performance reviewers in parallel over the current diff and synthesize prioritized findings. Use before finishing a unit of work (after verify passes).
argument-hint: "[diff ref, e.g. HEAD~1, main, or a path]"
allowed-tools: Task, Bash(git *), Read, Grep, Glob
---

# /flywheel-review — parallel multi-specialist review

Determine the diff to review from **$ARGUMENTS** (default: uncommitted changes plus commits on this branch vs. its base). Use `git diff` / `git log` to assemble it.

Dispatch these three specialist reviewers **in parallel** — launch them in a single batch of Task calls — giving each the diff and the spec if available:
- `reviewer-correctness` — logic bugs, edge cases, error handling, test adequacy, maintainability.
- `reviewer-security` — secret/credential handling, injection, authz, unsafe input, data exposure.
- `reviewer-performance` — hot paths, N+1 queries, unnecessary work, resource use.

Synthesize their findings into one prioritized list: deduplicated and sorted by severity (Critical → High → Medium → Low). For each finding give `file:line`, a one-line problem statement, and a concrete fix.

GATE: unresolved **Critical/High** findings block `/flywheel-compound` and shipping — either fix them (loop back to `/flywheel-work`) or get an explicit waiver from the user with a stated reason. Medium/Low can be logged as follow-ups.
