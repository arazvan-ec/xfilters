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

**Independent stop check.** Before keeping/discarding an ambiguous result (step 4) or declaring the target met (step 5), dispatch the `evaluator` agent with the metric command, the target, your claimed score, and the prior score. This is not a `/goal`-style transcript judge — a read-only re-read of your own output would indeed be redundant with the metric command you already ran. Instead the evaluator **re-runs the metric command itself**, independently of you, which is a genuine cross-check against a different failure mode: the same agent that makes a change also grading it (self-report drift, a stale/no-op metric command, or an honest-but-wrong reading of the output). On a `CONTINUE` verdict, keep looping even if you believed you were done; log the evaluator's reason alongside the iteration.

Keep a running log of `iteration | change | score | evaluator verdict | kept?`. Never ask the human mid-loop (AskUserQuestion is disabled). When you stop, report the trajectory, the final score, whether the target was met, and — if not — the most promising next direction.

**Safety:** work on a branch; only revert changes *you* made this run; never discard pre-existing uncommitted work.

**Token discipline:**
- The **budget is the stop criterion** — `max-iterations` bounds runaway spend as tightly as the metric bounds runaway drift. Refuse to run unbounded; a missing budget defaults to 10, not infinite.
- **Pilot before scaling.** On an unfamiliar metric or codebase, start with a small budget (3–5 iterations) to see the change/score trend before committing a large one.
- Check **`/usage`** afterward (or mid-run, between iterations) to see actual spend by skill/subagent — use it to judge whether the per-iteration cost matches the metric's value.
- For **turn-based** loops that outlive one autoloop run (recurring checks, not "iterate now"), prefer `/goal` or `/loop` over re-invoking `autoloop` — see [`docs/research/claude-code-loops.md`](../../docs/research/claude-code-loops.md) for when each fits, and match the interval to how often the underlying state actually changes.
- If a single iteration needs more than a handful of subagents, that's a sign to move it to a **workflow** (`/workflows` for live per-agent token totals) instead of inflating autoloop's own turn.
