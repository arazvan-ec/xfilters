---
name: flywheel-work
description: Implement plan tasks with a tight iterate-until-green inner loop — write a failing test, implement the minimum, run tests + linter, observe, fix, repeat — and never declare a task done until its objective check is green. Use when executing tasks from an approved plan.
argument-hint: "[task or plan-slug]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
---

# /flywheel-work — the inner loop (iterate until green)

Execute the plan's tasks one at a time. For **each** task, run this loop and do not exit it until the task's local check passes:

1. **Red** — write (or identify) the smallest failing test / check that captures the task. Run it; confirm it fails for the right reason.
2. **Green** — implement the minimum to make it pass. No extra scope.
3. **Check** — run the tests and the linter/formatter. When behavior is user-visible, also exercise the real thing (run the app / hit the endpoint / run the script).
4. **Observe** — read the actual output. If not green, diagnose from the evidence and fix, then go back to step 2.
5. **Advance** — only when the check is green, move to the next task.

**Standing rule:** "done" means the objective check is green *and you have seen it be green*. Never report a task complete on the basis of reasoning alone.

**Anti-rationalization — these are banned:**

| Excuse | Reality |
| --- | --- |
| "The test is probably fine, I won't run it." | Run it. Unrun tests don't count. |
| "I'll verify everything at the end." | Verify each task; end-only verification hides which change broke things. |
| "Linter warnings are just noise." | Fix them, or justify each one explicitly in the spec's Norms. |
| "It's a small change, no test needed." | Small changes break things too — add the smallest check. |
| "It works on my reasoning." | Reasoning is a hypothesis; the run is the evidence. |

When all tasks are green, hand off to `/flywheel-verify` for the objective gate against the spec's success metric. Do not self-certify the whole feature here.
