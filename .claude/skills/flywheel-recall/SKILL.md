---
name: flywheel-recall
description: On-demand search over the flywheel learnings ledger — list matching entries cheaply by type/title/files/branch, then expand one on request. Use when you want a past decision, gotcha, or pattern that the SessionStart hook's budgeted injection didn't surface, especially when working on a file or topic the ledger has entries about.
argument-hint: "<query>"
allowed-tools: Read, Grep
---

# /flywheel-recall — on-demand ledger search

`scripts/session-start.sh` only injects a relevance-scored, budgeted subset of `.claude/flywheel/LEARNINGS.md` at the start of a session. Anything else is one `/flywheel-recall` away — this is the progressive-disclosure layer that keeps that injection small.

Query: **$ARGUMENTS**

## Layer 1 — cheap list

Grep `.claude/flywheel/LEARNINGS.md` for `$ARGUMENTS`, matching against entry headers (`## <type>: <title>`) and metadata comments (`<!-- fw: type=…; date=…; files=…; spec=…; pr=…; branch=… -->` — so a query can match a type, a file, a spec slug, or a branch name, not just title words). Also match old free-prose `## <date> — <feature>` headers.

Print a numbered list, newest first, cheapest possible per line:

```
1. gotcha: logout didn't clear the session cookie (2026-07-08, files: src/auth/login.ts,src/auth/session.ts)
2. decision: use markdown ledger over SQLite (2026-07-01)
```

If nothing matches, say so plainly — don't guess or expand an unrelated entry to compensate.

## Layer 2 — expand on demand

When the user (or you, when the next step clearly needs it) picks a number or names an entry, read the full body from that entry's `## ` header up to the next `## ` header (or end of file) and print it verbatim, metadata comment included.

Don't dump every matching entry's full body up front — list first, expand only what's asked for. That's what keeps this cheaper than reloading the whole ledger.
