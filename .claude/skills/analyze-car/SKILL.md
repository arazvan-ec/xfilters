---
name: analyze-car
description: Analyse a car (make/model/year, optionally trim + use-case + budget) and produce a structured buyer's analysis, persisted to the car_analyses collection. Use when the owner wants to evaluate or compare a car. The Claude session is the analysis engine.
argument-hint: "<make model year> [trim] [use-case/budget]"
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
---

# /analyze-car — car buyer's analysis (you are the backend)

Subject: **$ARGUMENTS**

You run this like a backend endpoint: fixed rules for a consistent, comparable
result, plus your judgment (and current web data) to make it genuinely useful.
Read `CLAUDE.md` first if this is a fresh session.

## Rules (fixed)

1. **Inputs.** Parse make, model, year from `$ARGUMENTS`; note trim, use-case and
   budget if given. If make+model+year can't be determined, ask once; otherwise
   proceed and state assumptions.
2. **id / slug.** `<make>-<model>-<year>` lowercased, kebab-case (e.g.
   `tesla-model-3-2024`). This is the record id — re-running updates in place.
3. **Freshness.** Prices, reliability recalls and safety ratings change — use
   `WebSearch`/`WebFetch` for current data and **cite sources** (url per claim
   group). Never invent figures; if unknown, say "sin dato" rather than guess.
4. **Required output fields** (all present, even if brief):
   `id, make, model, year, trim, use_case, overview, pros[], cons[],
   reliability, running_costs, safety, alternatives[], verdict, score` (score
   0–10 integer), plus `sources[]` and `analyzed_at` (ISO date — get it with
   `date -u +%FT%TZ`).
5. **Language.** Spanish, neutral and concrete. Pros/cons specific to this
   car, not generic.
6. **Objectivity.** Balanced — always give real cons and at least 2
   `alternatives`. If a use-case/budget is given, judge fit against it.

## Persistence

Store the result in the **`car_analyses`** collection through the shared store
(NDJSON today, Postgres once the migration lands — this command is unchanged
either way):

```bash
echo '<record json>' | python scripts/record.py -c car_analyses put
# read back:  python scripts/record.py -c car_analyses get  --id <slug>
#             python scripts/record.py -c car_analyses list
```

## Process (what you do)

1. Resolve the car and gather current data (specs, trims, reliability/recalls,
   safety rating, typical price and running costs, common owner complaints).
2. Reason about fit for the stated (or a default general) use-case; pick
   alternatives that a real buyer would cross-shop.
3. Assemble the record with every required field; set `analyzed_at`; collect
   `sources`.
4. Persist it via `scripts/record.py`, then give the owner a concise readout
   (verdict, score, top 3 pros/cons, alternatives) and the stored id.

## Maturation log

Append a dated entry after each run: what was thin or wrong, a rule/field worth
adding, a better source. Promote stable improvements into **Rules/Process**
above, and send cross-cutting lessons to `/flywheel-compound`.

- 2026-07-10 — created. Baseline rules and fields as above; nothing learned yet.
  First real run should sanity-check the field list and whether `running_costs`
  should split into fuel/insurance/maintenance.
