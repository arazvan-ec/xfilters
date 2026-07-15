#!/usr/bin/env python3
"""Copy an NDJSON collection into the Supabase `records` table (idempotent).

Reads `data/<collection>.ndjson` (the current NDJSON backend) and upserts every
record into Postgres via SupabaseRecordStore. Upsert-by-PK means re-running never
duplicates. Requires SUPABASE_URL / SUPABASE_KEY and the `supabase` package.

  python scripts/migrate_ndjson_to_pg.py bookmarks
  python scripts/migrate_ndjson_to_pg.py car_analyses --id-field id

Run only after the schema migration (supabase/migrations/0001_records.sql) has
been applied to the target project.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xbookmarks.records import RecordStore  # noqa: E402
from xbookmarks.records_supabase import SupabaseRecordStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("collection", help="collection name (== data/<collection>.ndjson)")
    p.add_argument("--id-field", default="id")
    p.add_argument("--data-dir", default="data")
    args = p.parse_args(argv)

    src = RecordStore.load(args.collection, data_dir=args.data_dir, id_field=args.id_field)
    records = src.all()
    if not records:
        print(f"nothing to migrate: data/{args.collection}.ndjson is empty or absent")
        return 0

    dst = SupabaseRecordStore(args.collection, id_field=args.id_field)
    for rec in records:
        dst.upsert(rec)
    dst.save()
    print(f"migrated {len(records)} record(s) from {args.collection} NDJSON -> Postgres")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
