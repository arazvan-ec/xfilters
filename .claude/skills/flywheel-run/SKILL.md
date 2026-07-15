---
name: flywheel-run
description: Execute a defined agent-native process as the runtime — follow its fixed rules, apply judgment where the contract allows, persist the result to the repo's datastore (e.g. Postgres) per DATA.md, then reflect and mature the contract. Use to actually run an operation you defined with /flywheel-process (e.g. "run the car analysis for plate 1234ABC"). This is Claude acting as the backend, not calling one.
argument-hint: "[process-slug] [input...]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# /flywheel-run — execute a process (Claude as the backend)

Run this process against the given input: **$ARGUMENTS**

There is no static backend here — **you are the execution**. You follow the contract's fixed rules the way a service would, apply judgment only where the contract permits, and land the result in the repo's real datastore.

## 1. Load the contract and the data strategy

Parse the first token as the process slug and the rest as input. Read `.claude/flywheel/processes/<slug>.md`. If it is missing, stop and point the user to `/flywheel-process <description>` — do not improvise a contract. Read `.claude/flywheel/DATA.md` for the persistence access/conventions. Read the process's own **Persistence** section for any per-process override.

## 2. Execute against the fixed rules

Follow **Rules (fixed contract)** step by step on the given input. Within **Judgment latitude** — and only there — apply reasoning to make the result better than a rote script would; never let judgment override Rules, Output schema, or Guardrails. Produce a result that conforms **exactly** to the **Output schema** (every field, correct type). If an input is invalid or a rule cannot be satisfied, follow the Guardrails' partial-failure path and record it — do not fabricate fields to make the output look complete.

## 3. Persist per the repo's strategy — and prove it landed

Write the result to the store named in DATA.md / the contract's Persistence section, using the concrete tool it specifies (a `psql`/CLI command, a Postgres/Supabase MCP call, an ORM/repo script). Rules:

- **Idempotent** — upsert on the declared idempotency key; re-running the same input must not create duplicate rows.
- **Safe** — wrap multi-statement writes in a transaction; obey the destructive-operation ban (no `DROP`/`DELETE`/`TRUNCATE`/schema changes without explicit human confirmation).
- **Verified** — show the actual write (the SQL/tool call) and confirm it with evidence: affected-row count or a read-back of the row. A persist you did not observe landing does not count as done — the same standard `/flywheel-work` holds for tests.

If the process declares a `metric`, dispatch the `evaluator` agent to independently check the persisted result against it (as `/flywheel-autoloop` does) before reporting success, rather than trusting your own read.

## 4. Reflect and mature the contract

After a successful run, spend one short reflection on whether the contract should get sharper — but **only on evidence from this run**, at most one refinement, and never drift for its own sake:

- A rule was ambiguous and you had to make a call → tighten the rule so the next run is deterministic.
- A recurring input shape, edge case, or data-quality issue the Rules don't mention → note the guard.
- A judgment heuristic that measurably improved the output → promote it from ad-hoc to written latitude.

If (and only if) something qualifies, append a dated entry to the contract's **Improvement log**:

```
### <YYYY-MM-DD> — <one-line what changed>
<why, from this run's evidence>
```

If the refinement changes the fixed Rules, Output schema, or Persistence, also bump the contract's `version` and edit the relevant section — the Improvement log records *why*, the sections stay the source of truth. Most runs add nothing; that is correct. Stage the contract if you changed it.

## 5. Report

Report tersely: the input, the key output fields, **where it persisted** (table + row id/keys, with the read-back evidence), the evaluator verdict if one ran, and any maturation. If a durable, cross-process lesson emerged (not process-specific), suggest `/flywheel-compound`.
