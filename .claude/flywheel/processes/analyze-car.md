---
name: analyze-car
kind: process
version: 2
created: 2026-07-10
persistence: records:car_analyses (see DATA.md)
metric: persisted car_analyses row for the input slug has every Output-schema field present, score in 0..10, and >=2 alternatives
---

# Process: Car buyer's analysis

## Purpose

Analyse a car and produce a structured buyer's analysis — the operation a
traditional app would serve from a backend endpoint. Here Claude is the runtime:
fixed rules for a consistent, comparable result, plus judgment (and current web
data) that a rote script could not provide.

## Inputs

| Arg | Type | Req | Example |
| --- | --- | --- | --- |
| make model year | string | yes | `Tesla Model 3 2024` |
| trim | string | no | `Long Range` |
| use_case / budget | string | no | `familia, 30k€, ciudad` |

If make+model+year can't be determined from the input, ask once; otherwise
proceed and state assumptions.

## Rules (fixed contract)

1. **Slug / id:** `<make>-<model>-<year>` lowercased kebab-case (e.g.
   `tesla-model-3-2024`). This is the record id — re-running updates in place.
2. **Freshness:** prices, reliability/recalls and safety ratings change — use
   `WebSearch`/`WebFetch` for current data and cite sources. Never invent
   figures; if unknown, write `"sin dato"`, do not guess.
3. **Language:** Spanish, neutral and concrete. Pros/cons specific to this car,
   not generic.
4. **Balance:** always give real `cons` and at least 2 `alternatives`. If a
   use_case/budget is given, judge fit against it.
5. Produce every Output-schema field, then persist, then read back.
6. **Region-specific costs:** insurance and some running costs vary by country. If
   the input names no region, report those as `"sin dato"` rather than a generic
   figure (added v2 — see Improvement log 2026-07-10).

## Output schema

Record stored in collection `car_analyses` (the `data` payload):

| Field | Type | Constraint |
| --- | --- | --- |
| `id` | string | slug (rule 1); idempotency key |
| `make`,`model` | string | required |
| `year` | int | required |
| `trim` | string | "" if unknown |
| `use_case` | string | "" if not given |
| `overview` | string | 1–3 sentences |
| `pros` | string[] | ≥3, specific |
| `cons` | string[] | ≥2, specific |
| `reliability` | string | incl. known recalls or "sin dato" |
| `running_costs` | string | consumo/mantenimiento; seguro = "sin dato" sin región (rule 6) |
| `safety` | string | rating (Euro NCAP…) or "sin dato" |
| `alternatives` | string[] | ≥2 cross-shopped models |
| `verdict` | string | 1–2 sentences |
| `score` | int | 0–10 |
| `sources` | string[] | urls backing the data |
| `analyzed_at` | string | ISO 8601 — `date -u +%FT%TZ` |

## Persistence

Collection `car_analyses`, backend per `DATA.md` (NDJSON default, Supabase when
`XBOOKMARKS_BACKEND=supabase`). Idempotency key = `id`. Write + verify:

```bash
echo '<record json>' | python scripts/record.py -c car_analyses put
python scripts/record.py -c car_analyses get --id <slug>   # read-back proof
```

The `put` prints `{"stored": 1, "ids": [...]}`; the `get` read-back is the
evidence the row landed (required by /flywheel-run).

## Judgment latitude

Beyond the fixed rules, apply reasoning to make the analysis genuinely useful:
weighing trade-offs for the stated use-case, choosing the alternatives a real
buyer would cross-shop, flagging model-year-specific gotchas. Bounded — judgment
enriches the output; it never overrides Rules, Output schema, or Guardrails.

## Guardrails

- Validate make/model/year before proceeding; on an unresolvable car, ask once,
  else stop — do not fabricate a car.
- Every Output-schema field must be present; use `"sin dato"` rather than invent.
- Idempotent upsert by `id`; never delete/overwrite other rows.
- Obey the destructive-operation ban in `DATA.md`.

## Improvement log

<!-- Append-only. /flywheel-run adds a dated entry when a run surfaces a durable
     refinement. -->

### 2026-07-10 — insurance/running costs are region-specific → rule 6 (v2)
First run (`tesla-model-3-2024`, persisted to Postgres, score 8). The Output
schema lumped `seguro` into `running_costs`, but with no region in the input the
only honest value for insurance was `"sin dato"` — a generic figure would have
been invented. Added rule 6 and narrowed the `running_costs` constraint so this
is deterministic rather than a per-run judgment call. Next candidate: an optional
`region` input that, when present, unlocks concrete insurance/tax/subsidy figures.
