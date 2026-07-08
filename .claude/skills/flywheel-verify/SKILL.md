---
name: flywheel-verify
description: The objective PASS/FAIL gate — actually run the app and the test suite and check the result against the spec's success metric, with evidence. Use before review/ship, or any time you need to confirm a change really works rather than assuming it does.
context: fork
agent: verifier
argument-hint: "[what to verify / spec-slug]"
allowed-tools: Bash, Read, Grep, Glob
---

# /flywheel-verify — objective gate

You are the verification gate for: **$ARGUMENTS**

Load the spec's **Success metric** from `.claude/flywheel/specs/` if available. Then gather objective evidence:

1. Run the full test suite. Capture pass/fail counts and any failures.
2. Run the linter / type-checker / formatter check.
3. Build the project if it has a build.
4. If the change is user-visible, **run the real thing** and observe actual behavior against the metric (start the server and hit it, run the CLI, execute the import and count rows, etc.).

Then emit a verdict:
- **PASS** — only if the success metric is objectively met. Include the evidence (commands run, exit codes, key output).
- **FAIL** — otherwise. State exactly what failed and the smallest signal that would flip it to PASS.

Do not rationalize a FAIL into a PASS. A phase does not advance on a FAIL. Make the verdict the last line: `VERDICT: PASS` or `VERDICT: FAIL — <reason>`.
