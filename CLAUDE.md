# CLAUDE.md — how to operate on this repo

This repo is being steered toward an **agent-native** design
([every.to/go-agent-native](https://every.to/go-agent-native)): the AI agent
(you, Claude, in a Claude Code session) is the **runtime**, not just an author of
static backend code. Processes are executed *by a session*, not by a service.
This file is the operating contract — read it at the start of every session and
keep it current.

flywheel (vendored, ≥ 0.15.0) provides the two pillars this repo runs on: the
**build** loop (`/flywheel-spec → plan → work → verify → review → compound`) and
the **operate** runtime (`/flywheel-process` + `/flywheel-run`). Use them — don't
reinvent a parallel mechanism.

## The contract (what the owner asked for)

1. **Develop ideas with flywheel.** New features/ideas go through the build loop
   (`/flywheel-brainstorm` → `spec` → `plan` → `work` → `verify` → `review` →
   `compound`). Don't free-code a substantial idea; run it through the loop and
   deposit learnings.

2. **Sessions are the backend.** A request like "analyse a car" is served by a
   **process contract** (`/flywheel-process`) that a Claude session **executes**
   (`/flywheel-run`), the way a backend endpoint serves a request — fixed rules
   AND your judgment layered on top to beat a static script.

3. **No static code backend for the "thinking" work.** Deterministic plumbing
   (I/O, parsing, persistence, rendering) stays as code; the reasoning/analysis
   step is **you at runtime**, invoked through `/flywheel-run`. Prefer
   "Claude-as-process" over "write a fixed algorithm" whenever the task benefits
   from judgment.

4. **Persist via the repo's storage strategy** — defined once in
   **`.claude/flywheel/DATA.md`**; every process writes there, never to ad-hoc
   files. Concretely: a generic id-keyed **record store**
   (`xbookmarks/records.open_store`, CLI `scripts/record.py`) with two backends —
   **NDJSON** (`data/<collection>.ndjson`, the default/offline/test backend) and
   **Supabase/Postgres** (`records` table, project `tweets`, selected by
   `XBOOKMARKS_BACKEND=supabase`; cloud cutover gated — see
   `.claude/flywheel/specs/postgres-persistence.md`). The original bookmarks
   pipeline keeps its typed `xbookmarks/store.py` store. A new process **reuses
   this layer**; it never invents a parallel format.

5. **Every process is a self-maturing contract.** For each new process/idea,
   run `/flywheel-process` to scaffold `.claude/flywheel/processes/<slug>.md` —
   fixed **Rules**, an **Output schema**, a **Persistence** target (per DATA.md),
   bounded **Judgment latitude**, and an append-only **Improvement log**. Running
   it with `/flywheel-run <slug> <input>` executes the contract, persists the
   result, and matures the contract from that run's evidence. Fixed rules for
   consistency + a process you sharpen run over run.

6. **North star:** an agent-native repo — capabilities exposed as agent-invokable
   process contracts backed by real persistence, and the agent (you) is the
   execution engine that also improves the process.

## The process-contract shape

Don't hand-author these — `/flywheel-process` scaffolds them. Reference example:
**`.claude/flywheel/processes/analyze-car.md`** (run: `/flywheel-run analyze-car
"Tesla Model 3 2024"`), persisting to the `car_analyses` collection via
`scripts/record.py`. The contract carries `Rules (fixed)` · `Output schema` ·
`Persistence` · `Judgment latitude` · `Guardrails` · `Improvement log`.

After a run, `/flywheel-run` appends at most one evidence-based refinement to the
contract's Improvement log; send cross-cutting lessons to `/flywheel-compound`
(`.claude/flywheel/LEARNINGS.md`).

## Practical notes

- Verify before declaring done: `make test` (pytest) and `make lint` (ruff) must
  be green; the repo also has an opt-in flywheel completion gate.
- Keep deterministic edges (parsing, dedupe, persistence) pure and unit-tested;
  keep the judgment at runtime (you).
- `/enrich-bookmarks` stays a skill (a bookmarks-pipeline stage, tied to the
  `Bookmark` model), not a `/flywheel-run` process — that split is intentional.
- Data written by your runs (`data/`, `site/`, `catalog/`) contains real bookmark
  content — the owner has chosen to commit it here, but treat it as their data.
