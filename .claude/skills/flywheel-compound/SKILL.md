---
name: flywheel-compound
description: Capture the reusable knowledge from this cycle — decisions, gotchas, and patterns — into the versioned learnings ledger so the next cycle starts smarter. Use at the end of a unit of work, after review.
allowed-tools: Read, Edit, Write, Bash(git *)
---

# /flywheel-compound — close the loop (learning capture)

This is what makes the loop *compound*: each cycle leaves knowledge that primes the next.

Append a terse, dated entry to the **top** (newest-first) of `.claude/flywheel/LEARNINGS.md` (create the file if missing, with a `# flywheel learnings` header). Keep it tight — this file is injected into every session by the SessionStart hook, so bloat costs context every single time.

Get today's date with `date +%F`. Entry format:

```
## <YYYY-MM-DD> — <feature/unit>
- Decision: <what was chosen + why, incl. the rejected alternative if notable>
- Gotcha: <trap hit this cycle + how to avoid it next time>
- Reusable: <pattern / snippet / command worth repeating>
```

Include only what a future cycle would genuinely benefit from — omit the obvious. Prefer 3–6 bullet lines over paragraphs.

Then stage the ledger (`git add .claude/flywheel/LEARNINGS.md`) so it is committed with the work. Report a one-line summary of what you compounded.
