---
name: flywheel-process
description: Define (and later mature) an agent-native process — a reusable prompt-contract for a recurring domain operation that Claude executes as the runtime, instead of static backend code. Scaffolds fixed rules, an output schema, and the repo's data-persistence strategy. Use when the user wants a repeatable operation like "analyze a car", "score a lead", "ingest a report" turned into something /flywheel-run can execute over and over.
argument-hint: "[process description, e.g. 'analyze a car by registration plate']"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# /flywheel-process — define an agent-native process (Claude as the runtime)

Turn this recurring operation into a **process contract**, not one-off code: **$ARGUMENTS**

A *process* is a domain operation a traditional app would implement as a backend function. flywheel implements it instead as a **prompt-contract that Claude executes** (`/flywheel-run`): fixed rules the run must follow, a machine-checkable output schema, a persistence target in the repo's own datastore, and an improvement log that matures with every run. This is the agent-native pillar — the agent *is* the runtime, not a bolt-on (see `docs/research/agent-native-processes.md`).

First read `.claude/flywheel/LEARNINGS.md` and any existing `.claude/flywheel/processes/*.md` for prior art and house conventions.

## 1. Establish the repo's data strategy (once per repo)

Read `.claude/flywheel/DATA.md`. **If it is missing, create it first** — a process that cannot say where its results go is not done. Detect how this repo persists data before asking the user, by looking for (in order): `DATABASE_URL`/`*_DATABASE_URL` env or `.env(.example)`, `prisma/schema.prisma`, `drizzle.config.*`, `knexfile.*`, `sequelize`/`typeorm` config, `supabase/config.toml`, a `postgres`/`mysql` service in `docker-compose*.yml`, `*.sql` migrations, or an ORM in `package.json`/`requirements.txt`/`pyproject.toml`. Confirm the finding with the user; only ask open-ended if nothing is detectable.

Write `.claude/flywheel/DATA.md` with:
- **Store** — the backend (e.g. `PostgreSQL`).
- **Access** — exactly how a run writes to it: the concrete tool/command (`psql "$DATABASE_URL"`, a Postgres/Supabase MCP server + project ref, `npm run db:exec`, an ORM script…). Name the one a run should use.
- **Schema** — the tables/columns processes read and write, or a pointer to the migrations that define them.
- **Conventions** — idempotency key, timestamps, a `flywheel_runs` metadata table if the repo wants run bookkeeping, and safety rules (transactions; never `DROP`/`DELETE`/`TRUNCATE` without explicit human confirmation).

## 2. Interview for the fixed rules (only what's genuinely open)

Infer as much as you can from the description and the codebase; ask only what you cannot decide. Pin down: the inputs, the deterministic procedure, the exact output fields, and where results land.

## 3. Write the contract

Save to `.claude/flywheel/processes/<slug>.md` (slug = short kebab-case name), with this shape:

```
---
name: <slug>
kind: process
version: 1
created: <YYYY-MM-DD>          # from `date +%F`
persistence: <e.g. postgres:public.car_analyses — or "see DATA.md">
metric: <optional: a machine-checkable pass condition for one run>
---

# Process: <Title>

## Purpose
The operation and the backend function it replaces.

## Inputs
Each argument /flywheel-run takes — name, type, required/optional, example.

## Rules (fixed contract)
The deterministic, numbered procedure a run MUST follow. This is the part that
does NOT drift between runs. Be specific enough that two runs on the same input
produce the same structured result.

## Output schema
The exact structured result — field, type, constraint — mapped 1:1 to the
persistence columns. This is what makes a run checkable.

## Persistence
Table + column mapping, the idempotency key, and the connection/tool from
DATA.md. State the read-back or affected-rows check that proves the write landed.

## Judgment latitude
Where Claude is expected to apply reasoning BEYOND the fixed rules — the analysis
quality the user wants improved over time. Bounded: it enriches the output, it
never overrides Rules, Output schema, or Guardrails.

## Guardrails
Validation, PII handling, idempotency, what to do on partial failure, and the
destructive-operation ban from DATA.md.

## Improvement log
<!-- Append-only. /flywheel-run adds a dated entry when a run surfaces a durable
     refinement. Empty at creation. -->
```

Fill Rules, Output schema, and Persistence concretely — a vague contract yields a vague run. Leave **Improvement log** empty; `/flywheel-run` matures it.

## 4. Maturing an existing process

If `$ARGUMENTS` names a process that already exists, do not recreate it — treat this as a **deliberate revision**: read the contract and its Improvement log, apply the requested change to Rules/Output schema/Persistence, bump `version`, and record the change (what and why) in the Improvement log. Never silently rewrite the fixed rules.

GATE: present the contract (or the diff, when revising) and the data strategy, and get explicit sign-off. Then tell the user how to run it: `/flywheel-run <slug> <input>`. Stage the contract (and DATA.md) so it is committed with the work.
