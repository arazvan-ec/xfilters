---
name: flywheel-autoloop
description: Autonomous iterate-until-metric loop — repeatedly change → measure → keep-if-better / discard-if-worse against a single machine-checkable metric, within a fixed budget of iterations, without pausing for human input between iterations. Use only for well-specified, objectively measurable goals (get the suite green, tune a scraper until it extracts all items, drive a lint-error count to zero).
disable-model-invocation: true
disallowed-tools: AskUserQuestion
argument-hint: "[goal] [max-iterations, default 10]"
---

# /flywheel-autoloop — autonomous metric-driven loop

Goal: **$ARGUMENTS**

This runs hands-off. Preconditions — refuse and point the user to `/flywheel-loop` if either is missing:
- a **single machine-checkable metric** (a command whose output is an objective score / pass count / error count), and
- a **budget** (max iterations; default 10).

Loop:
1. **Measure baseline** — run the metric command; record the score. If already at target, stop and report.
2. **Hypothesize + change** — make the smallest change you believe improves the metric. Record what you changed.
3. **Re-measure** — run the metric command again.
4. **Keep or discard** — if the score improved, keep the change; if it regressed or stalled, revert it (`git checkout` / `git stash`) and try a different change.
5. Repeat until the metric hits target or the budget is exhausted.

Keep a running log of `iteration | change | score | kept?`. Never ask the human mid-loop (AskUserQuestion is disabled). When you stop, report the trajectory, the final score, whether the target was met, and — if not — the most promising next direction.

**Safety:** work on a branch; only revert changes *you* made this run; never discard pre-existing uncommitted work.
