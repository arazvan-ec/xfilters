---
name: flywheel-compound
description: Capture the reusable knowledge from this cycle — decisions, gotchas, and patterns — into the versioned learnings ledger so the next cycle starts smarter. Use at the end of a unit of work, after review.
allowed-tools: Read, Edit, Write, Bash(git *)
---

# /flywheel-compound — close the loop (learning capture)

This is what makes the loop *compound*: each cycle leaves knowledge that primes the next.

Prepend one **typed entry per distinct learning** to the **top** (newest-first) of `.claude/flywheel/LEARNINGS.md` (create the file if missing, with a `# flywheel learnings` header). Keep it tight — the SessionStart hook injects only a relevance-scored, budgeted subset of this file, and `/flywheel-recall` greps the rest, but every entry still costs something the moment it's selected.

Include only what a future cycle would genuinely benefit from — omit the obvious. One cycle typically yields 0–3 entries, not one per bullet point you can think of.

## Entry format

Get today's date with `date +%F` and the current branch with `git branch --show-current`. For each distinct learning:

```
## <type>: <one-line title>
<!-- fw: type=<type>; date=<YYYY-MM-DD>; files=<comma-separated touched files>; spec=<spec-slug>; pr=<PR number>; branch=<branch> -->

<what/why/fix, as 2-5 sentences of prose: the trap and the guard for a gotcha, the
choice and rejected alternative for a decision, the reusable snippet/command for a
pattern, the root cause and the regression test for a bugfix.>
```

- `type` is one of `decision`, `gotcha`, `pattern`, `bugfix`.
- The metadata comment is a **single line**: `key=value` pairs separated by `; `.
  `type` and `date` are required; omit a key entirely when it doesn't apply (no
  `pr=` key at all, not `pr=;`).
- `files` should list the paths most relevant to *finding this entry again* — this
  is what `scripts/session-start.sh` matches against the current branch's changed
  files to decide relevance, so keep it to the handful that actually matter.

Old free-prose entries already in the ledger are untouched — this format only applies going forward; the SessionStart hook and `/flywheel-recall` both still load them (as always-eligible, low-priority entries).

Then stage the ledger (`git add .claude/flywheel/LEARNINGS.md`) so it is committed with the work. Report a one-line summary of what you compounded.
