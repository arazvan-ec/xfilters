---
name: new-process
description: Scaffold a new agent-run process as a self-maturing skill. Use whenever the owner asks for a new kind of task/analysis on this repo ("let's be able to analyse X"). Turns the request into a .claude/skills/<slug>/SKILL.md with fixed rules + a maturation log, persisting through the shared record store.
argument-hint: "<what the process should do>"
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# /new-process — turn an idea into a self-maturing process skill

The owner wants this repo to be **agent-native** (see `CLAUDE.md`): every new
kind of request becomes a skill that a Claude session *runs* as the backend,
with fixed rules plus a process you improve over time. This skill builds that
skill.

Requested process: **$ARGUMENTS**

## Steps

1. **Pin down the contract.** From `$ARGUMENTS`, decide:
   - a **slug** (kebab-case, e.g. `analyze-car`) and one-line description;
   - the **inputs** the process needs (and sensible defaults);
   - the **fixed rules** — the invariant steps/guardrails that must not drift;
   - the **output record shape** and a stable **id** (a slug of the subject);
   - the **collection** name for persistence (e.g. `car_analyses`).

   If any of these is genuinely ambiguous and would change the design, ask the
   owner with `AskUserQuestion` (max one short round). Otherwise pick sensible
   defaults and state them.

2. **Decide if it needs a flywheel spec first.** If the process is a big or
   architectural change (new storage, external services, cross-cutting), stop and
   run `/flywheel-brainstorm` / `/flywheel-spec` before scaffolding. Small,
   self-contained processes can be scaffolded directly.

3. **Write `.claude/skills/<slug>/SKILL.md`** using the standard template
   (frontmatter: `name`, `description`, `argument-hint`, `allowed-tools`), with
   these body sections — copy the shape from `.claude/skills/analyze-car/SKILL.md`:

   ```
   ## Rules (fixed)          the invariant contract
   ## Persistence            the collection + how to store (see below)
   ## Process (what you do)   the reasoning/plan you run as the backend
   ## Maturation log          dated entries you append after each run
   ```

4. **Wire persistence through the shared store** — never invent a new file
   format. The process stores its result with:

   ```bash
   echo '<record json>' | python scripts/record.py -c <collection> put
   ```

   which routes through `xbookmarks/records.open_store` (NDJSON today, Postgres
   once the migration lands — the process doesn't change either way).

5. **Seed the Maturation log** with one entry: today's date and "created;
   nothing learned yet."

6. **Tell the owner** the new command name (`/<slug>`), its inputs, and where it
   persists. Remind them it will sharpen its own rules each run.

## The maturation principle (bake this into every generated skill)

After a process runs, it must **append to its own Maturation log** what would make
the next run better, and edit its Rules/Process when an improvement is stable.
That is the whole point: fixed rules for consistency, plus a process that gets
smarter every execution. Cross-cutting learnings also go to
`/flywheel-compound` → `.claude/flywheel/LEARNINGS.md`.
