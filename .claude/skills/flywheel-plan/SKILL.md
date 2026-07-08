---
name: flywheel-plan
description: Turn an approved REASONS spec into an ordered implementation plan where every task carries its own pass/fail check. Use after /flywheel-spec is signed off and before writing code.
argument-hint: "[spec-slug]"
allowed-tools: Read, Grep, Glob, Write
---

# /flywheel-plan — sequenced plan with per-task gates

Read the approved spec at `.claude/flywheel/specs/$ARGUMENTS.md` (or the most recent spec if no slug is given). If there is no approved spec, STOP and tell the user to run `/flywheel-spec` first — do not plan from a vague request.

Produce a plan and save it to `.claude/flywheel/specs/<slug>.plan.md`:

1. Decompose the work into small, ordered tasks (aim for 2–15 min each). For each task state:
   - what it changes (files/functions), and
   - its **local check** — the concrete test/command/observation that proves the task is done.
2. Identify the files to create/modify, new dependencies, and the single riskiest step.
3. Mark which tasks are test-first (where the inner loop applies).
4. Re-check against the spec's Safeguards — make sure the plan addresses each one.

GATE: present the plan for approval. No code is written until the plan is approved. Then hand off to `/flywheel-work`.
