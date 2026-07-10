#!/usr/bin/env python3
"""Persist process output through the repo's shared record store.

The bridge a Claude session uses to save what it produced — so every agent-run
process stores data the same way (see xbookmarks/records.py), and swaps to
Postgres centrally later. Backend follows XBOOKMARKS_BACKEND (default ndjson).

  put   Upsert one record (JSON object) or many (JSON array) into a collection,
        read from --file or stdin. Each record needs an id field (default "id").
  get   Print one record by id.
  list  Print all records in a collection as a JSON array.

Examples:
  echo '{"id":"tesla-model-3","verdict":"..."}' | python scripts/record.py put -c car_analyses
  python scripts/record.py get  -c car_analyses --id tesla-model-3
  python scripts/record.py list -c car_analyses
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xbookmarks.records import open_store  # noqa: E402


def _read_input(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()


def cmd_put(args: argparse.Namespace) -> int:
    data = json.loads(_read_input(args.file))
    records = data if isinstance(data, list) else [data]
    store = open_store(args.collection, id_field=args.id_field)
    ids = []
    for rec in records:
        if not isinstance(rec, dict):
            print("each record must be a JSON object", file=sys.stderr)
            return 1
        store.upsert(rec)
        ids.append(str(rec.get(args.id_field, "")))
    store.save()
    print(json.dumps({"stored": len(ids), "ids": ids}, ensure_ascii=False))
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    store = open_store(args.collection, id_field=args.id_field)
    rec = store.get(args.id)
    if rec is None:
        print(f"no record {args.id!r} in {args.collection!r}", file=sys.stderr)
        return 1
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = open_store(args.collection, id_field=args.id_field)
    print(json.dumps(store.all(), ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="record", description=__doc__)
    p.add_argument("-c", "--collection", required=True, help="collection name")
    p.add_argument("--id-field", default="id", help="record id field (default: id)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("put", help="upsert record(s) from --file or stdin")
    pp.add_argument("--file", help="path to JSON (object or array); default stdin")

    pg = sub.add_parser("get", help="print one record by id")
    pg.add_argument("--id", required=True)

    sub.add_parser("list", help="print all records as a JSON array")

    args = p.parse_args(argv)
    return {"put": cmd_put, "get": cmd_get, "list": cmd_list}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
