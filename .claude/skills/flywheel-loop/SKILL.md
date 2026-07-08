---
name: flywheel-loop
description: Run the full flywheel development cycle end to end (spec → plan → work → verify → review → compound) for one unit of work, gating between phases. Use this to start a new feature or task with the disciplined loop instead of ad-hoc coding.
disable-model-invocation: true
argument-hint: "[feature or task description]"
---

# /flywheel-loop — the outer development loop

You are running the flywheel cycle for: **$ARGUMENTS**

The cycle has six phases, each with an entry gate. Do not enter a phase until the previous gate is green. If a gate fails, stop and report — do not paper over it.

0. **Prime.** Read `.claude/flywheel/LEARNINGS.md` (if it exists) and skim related specs in `.claude/flywheel/specs/`. Reuse past decisions; avoid known gotchas.
1. **spec** → run `/flywheel-spec`. Produces a REASONS contract + a single machine-checkable success metric. GATE: the spec is signed off before planning.
2. **plan** → run `/flywheel-plan`. Ordered tasks, each with its own check. GATE: plan approved; no coding before this.
3. **work** → run `/flywheel-work`. Implement task by task using the inner iterate-until-green loop. GATE: every task's local check is green.
4. **verify** → run `/flywheel-verify`. Objective PASS/FAIL against the success metric, running the real app/tests. GATE: must be PASS to continue.
5. **review** → run `/flywheel-review`. Parallel multi-specialist review. GATE: no unresolved Critical/High findings.
6. **compound** → run `/flywheel-compound`. Append the cycle's decisions, gotchas, and reusable patterns to the ledger.

Rules:
- Announce each phase as you enter it and state whether the prior gate passed.
- Never skip verify or review to "save time" — they are what make the loop trustworthy.
- For larger work, loop steps 3–4 per task, then do a single review pass at the end.
- Close with a one-paragraph summary: what shipped, the metric result, and what got compounded.
