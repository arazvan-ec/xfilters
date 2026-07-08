---
name: flywheel-debug
description: Systematic debugging runbook — reproduce reliably, form one explicit hypothesis, instrument, isolate by bisection, fix the root cause, and confirm with a regression test. Use when something is broken, a test fails mysteriously, or behavior is wrong — especially fragile failures like web-scraping selectors. Not for green-field feature work.
argument-hint: "[what's broken]"
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# /flywheel-debug — systematic debugging

Bug / symptom: **$ARGUMENTS**

Work the loop in order — do not jump to a fix:

1. **Reproduce reliably.** Find the smallest command/steps that trigger it every time. If you cannot reproduce it, getting a reliable repro IS the first task.
2. **One hypothesis.** State a single, specific hypothesis about the cause ("X is null because Y"). Not a list — the most likely one.
3. **Instrument.** Add logging / asserts / breakpoints that would confirm or kill the hypothesis. Run it and read the actual evidence.
4. **Isolate.** Narrow to the smallest failing surface — `git bisect`, comment-out, or a minimal repro. Confirm the culprit.
5. **Fix the root cause** — not the symptom. Then add a regression test that fails without the fix and passes with it.
6. **Confirm.** Re-run the repro: it passes. Re-run the suite: still green.

**Banned:** shotgun changes hoping something sticks; "fixing" by masking the symptom; declaring it fixed without re-running the repro. If the evidence kills your hypothesis, go back to step 2 with what you learned — don't cling to it.
