# DATA.md — how processes persist in this repo

The data-persistence strategy that `/flywheel-run` follows. Every agent-run
process writes its result here — never to ad-hoc files.

## Store

A single, id-keyed **record store** with two interchangeable backends, chosen by
the `XBOOKMARKS_BACKEND` env var:

- **`ndjson`** (default) — `data/<collection>.ndjson`, atomic writes, one record
  per line, sorted by id. Offline, free, the test backend.
- **`supabase`** — a Postgres table `public.records(collection, id, data jsonb,
  updated_at)` in the Supabase project **`tweets`** (`gwmcfndhxxjnlwqhkace`, org
  `claude-org`, region eu-west-3). One row per record; `data` holds the whole
  record. **Live:** project active, schema applied (`0001_records.sql`), and the
  `bookmarks` collection backfilled (260 rows). **RLS is enabled with no
  policies**, so `SUPABASE_KEY` must be the **`service_role`** key (client-facing
  anon/publishable keys are denied all access). See
  `.claude/flywheel/specs/postgres-persistence.md`.

The seam is `xbookmarks/records.open_store(collection)` — switching backends is a
one-env-var change, no process code touched.

## Access — how a run writes

Preferred (language-agnostic), from the repo root:

```bash
# upsert one record (JSON object) or many (JSON array), from stdin or --file
echo '<record json>' | python scripts/record.py -c <collection> put
# read back
python scripts/record.py -c <collection> get  --id <record-id>
python scripts/record.py -c <collection> list
```

From Python: `from xbookmarks.records import open_store; s = open_store("<collection>"); s.upsert(rec); s.save()`.

To use Postgres for a run: `export XBOOKMARKS_BACKEND=supabase`, `SUPABASE_URL`,
and `SUPABASE_KEY` (the **service_role** key — RLS denies anon/publishable) before
the command. NDJSON→Postgres backfill: `python scripts/migrate_ndjson_to_pg.py
<collection>`. Never commit the service_role key; keep it in the environment.

## Schema

- **Generic records** (all `/flywheel-run` processes): `records(collection text,
  id text, data jsonb, updated_at timestamptz, primary key (collection, id))` —
  DDL in `supabase/migrations/0001_records.sql`. In NDJSON mode the same records
  live at `data/<collection>.ndjson`.
- **Bookmarks** (the original pipeline, not a `/flywheel-run` process):
  `data/bookmarks.ndjson` via the typed `xbookmarks/store.py` `Store` + `Bookmark`
  model. Left as-is; it predates the generic store.

Known collections: `car_analyses` (see `processes/analyze-car.md`).

## Conventions

- **Idempotency key:** each record's `id` field (Postgres PK is `(collection,
  id)`). Writes are upserts — re-running a process on the same input updates the
  row, never duplicates.
- **Timestamps:** processes stamp their own domain time (e.g. `analyzed_at`);
  Postgres also keeps `updated_at` via trigger.
- **Safety / destructive-op ban:** never `DROP`/`DELETE`/`TRUNCATE` or change
  schema without explicit human confirmation. Supabase writes should be verified
  by read-back (the `record.py get` above) as `/flywheel-run` requires.
- **Secrets:** DB credentials come only from the environment; never commit them
  (`.env` is gitignored).
