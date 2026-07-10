# CLAUDE.md — how to operate on this repo

This repo is being steered toward an **agent-native** design
([every.to/go-agent-native](https://every.to/go-agent-native)): the AI agent
(you, Claude, in a Claude Code session) is the **runtime**, not just an author of
static backend code. Processes are executed *by a session*, not by a service.
This file is the operating contract — read it at the start of every session and
keep it current.

## The contract (what the owner asked for)

1. **Develop ideas with flywheel.** New features/ideas go through the flywheel
   loop (`/flywheel-brainstorm` → `spec` → `plan` → `work` → `verify` → `review`
   → `compound`). Don't free-code a substantial idea; run it through the loop and
   deposit learnings.

2. **Sessions are the backend.** A request like "analyse a car" is served by a
   skill that a Claude session runs, the way a backend endpoint would serve a
   request — with fixed rules AND your judgment layered on top to make the
   analysis better than a static script could.

3. **No static code backend for the "thinking" work.** Deterministic plumbing
   (I/O, parsing, persistence, rendering) stays as code; the reasoning/analysis
   step is **you at runtime**, invoked through a skill. Prefer "Claude-as-process"
   over "write a fixed algorithm" whenever the task benefits from judgment.

4. **Persist via the repo's storage strategy.** Every session-run process must
   save its output the way this repo persists data — not to ad-hoc files.
   - **Current reality:** persistence is **NDJSON** (`data/bookmarks.ndjson`),
     an append/upsert-by-id store (see `xbookmarks/store.py`). There is **no
     Postgres in this repo yet.** (The owner referred to Postgres as the target;
     a Supabase/Postgres MCP is available in-session. Migrating the store to
     Postgres is a tracked idea — until it lands, write through `Store`, and when
     it lands, route every process through the DB the same way.)
   - Rule of thumb: a new process **reuses the existing store layer**; it does not
     invent a parallel storage format.

5. **Every process becomes a self-maturing skill.** For each new process/idea the
   owner asks for, create a **skill** under `.claude/skills/<name>/SKILL.md` that:
   - carries a **fixed prompt + rules** (the invariant contract for that process),
     and
   - carries a **maturation log** you extend with your own thoughts, refining the
     prompt/rules **after each execution** so the process gets better over time.

   So every request = fixed rules + an owner-visible process that you improve run
   over run. Do not throw a process away after running it — capture what would
   make the next run sharper.

6. **North star:** an agent-native repo — capabilities are exposed as
   agent-invokable skills/prompts backed by real persistence, and the agent (you)
   is the execution engine that also improves the process.

## The skill shape (use this template for every process)

`.claude/skills/<process-name>/SKILL.md`, YAML frontmatter (`name`,
`description`, `argument-hint`, `allowed-tools`) + body with these sections:

```
## Rules (fixed)          # the invariant contract — inputs, steps, guardrails
## Persistence            # exactly how/where results are stored (via Store today)
## Process (what you do)  # the prompt/plan you execute as the runtime
## Maturation log         # dated notes you APPEND after each run to improve it
```

After running a process: append a dated entry to its **Maturation log** (what was
learned, what to change), and edit **Rules/Process** if the improvement is stable.
Also run `/flywheel-compound` to record cross-cutting learnings in
`.claude/flywheel/LEARNINGS.md`.

Existing example to copy from: `.claude/skills/enrich-bookmarks/SKILL.md` — a
session runs the enrichment (no API key), writing back through `Store`.

## Practical notes

- Verify before declaring done: `make test` (pytest) and `make lint` (ruff) must
  be green; the repo also has an opt-in flywheel completion gate.
- Keep deterministic edges (parsing, dedupe, persistence) pure and unit-tested;
  keep the judgment at runtime (you).
- Data written by your runs (`data/`, `site/`, `catalog/`) contains real bookmark
  content — the owner has chosen to commit it here, but treat it as their data.
