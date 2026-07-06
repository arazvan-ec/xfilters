---
name: flywheel-help
description: Onboarding and command reference for the flywheel plugin — explains the nested loop, lists every /flywheel command with when to use it, and helps the user pick where to start. Use when someone is new to flywheel, asks how flywheel works or how to use it, or runs /flywheel-help.
argument-hint: "[optional: a topic, or a task you want to start]"
---

# /flywheel-help — onboarding & command map

Onboard the user to flywheel. Be friendly, concrete, and skimmable — not a wall of text. If `$ARGUMENTS` names a topic or a task, tailor the answer to it; otherwise give the full orientation below, in order.

## 1. What flywheel is — say it in 2–3 lines
A disciplined, self-verifying development loop. One unit of work flows through six gated phases — **spec → plan → work → verify → review → compound** — and inside `work` runs a tight *write-failing-test → implement → run → observe → fix* inner loop. Nothing advances on "seems right": `verify` runs the real app/tests, and each finished cycle deposits reusable lessons into a ledger that primes the next one.

## 2. The command map — show as a table
| Command | When to use it |
| --- | --- |
| `/flywheel-loop <task>` | **Start here.** Runs the whole cycle end to end, gating between phases. |
| `/flywheel-brainstorm <idea>` | The idea is fuzzy — sharpen it into agreed requirements first. |
| `/flywheel-spec <feature>` | Write the contract + one machine-checkable success metric. |
| `/flywheel-plan <spec>` | Turn a signed spec into ordered tasks, each with its own check. |
| `/flywheel-work <task>` | Implement with the iterate-until-green inner loop. |
| `/flywheel-debug <symptom>` | Something's broken — reproduce → isolate → fix → add a regression test. |
| `/flywheel-verify` | Objective PASS/FAIL gate; runs the real app/tests. |
| `/flywheel-review <ref>` | Parallel correctness / security / performance review. |
| `/flywheel-compound` | Capture this cycle's decisions and gotchas into the ledger. |
| `/flywheel-ship <title>` | Clean commit + push + PR. |
| `/flywheel-autoloop <goal>` | Hands-off: iterate autonomously until a metric is met or a budget runs out. |
| `/flywheel-sync <spec>` | Reconcile drift between a spec and the code. |

## 3. How to pick a starting point
- Clear feature/task in mind → `/flywheel-loop <task>` (it pauses at each gate for your sign-off).
- Idea still fuzzy → `/flywheel-brainstorm <idea>`, then `/flywheel-spec`.
- Just fixing a bug → `/flywheel-debug <symptom>`.
- Want it fully autonomous → `/flywheel-autoloop <goal>` (define a measurable goal first).

## 4. Good to know
- **State lives in this project** under `.claude/flywheel/`: specs in `specs/`, plus the compounding ledger `LEARNINGS.md`. The `SessionStart` hook reloads recent lessons each session, so knowledge carries forward.
- **Optional hard gate**: drop an executable `.claude/flywheel/gate.sh` (for example `npm test && npm run lint`). While it exists, the `Stop` hook blocks finishing a turn whenever it fails — so nothing is called "done" with checks red.
- Commands are namespaced `/flywheel-…` and also show up in `/help`.

## 5. Offer to start
Finish by asking one question: **"What do you want to build, fix, or explore right now?"** Based on the answer, recommend the exact command. If the user says go, invoke it for them (for example, run `/flywheel-loop <task>`). Never launch a `loop`, `autoloop`, or `ship` command without explicit confirmation.
