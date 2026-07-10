#!/usr/bin/env python3
"""Enrich bookmarks with a Claude Code session — no ANTHROPIC_API_KEY needed.

The API enricher (`python -m xbookmarks enrich --enricher claude`) calls the
Anthropic API and needs a key. But when you are already *inside* a Claude Code
session, Claude itself can produce the same summary/topic/tags. This script is
the bridge, driven by the `/enrich-bookmarks` skill:

  dump   Write pending bookmarks (id/url/author/text/links/hashtags) to one or
         more chunk files for the session to read and enrich.
  apply  Read the session's enrichment JSON ({id: {summary, topic, tags}}, or a
         list of such objects) and write it into the store using the normal
         enrichment semantics — manual tags (`tags_source == "manual"`) are
         preserved, `enriched`/`enriched_at` are set. Then run
         `python -m xbookmarks render` to (re)build the site + catalog.

Everything stays local; no network call and no API key are involved.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from xbookmarks.enrich import enrich_pending  # noqa: E402
from xbookmarks.store import Store  # noqa: E402

DEFAULT_DATA = Path("data/bookmarks.ndjson")


def _targets(store: Store, force: bool):
    return store.all() if force else store.pending()


def cmd_dump(args: argparse.Namespace) -> int:
    store = Store.load(args.data)
    records = [
        {
            "id": b.id,
            "url": b.url,
            "author_handle": b.author_handle,
            "author_name": b.author_name,
            "text": b.text,
            "hashtags": b.hashtags,
            "links": b.links,
        }
        for b in _targets(store, args.force)
    ]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = max(1, args.chunks)
    # Round-robin split keeps chunks balanced in size and topic mix.
    written = []
    for i in range(n):
        chunk = records[i::n]
        if not chunk:
            continue
        p = out_dir / f"chunk_{i:02d}.json"
        p.write_text(json.dumps(chunk, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(p))
    print(json.dumps({"pending": len(records), "chunks": written}, ensure_ascii=False))
    return 0


def _load_map(paths: list[str]) -> dict[str, dict]:
    """Load enrichment JSON into {id: {summary, topic, tags}}.

    Accepts either an object keyed by id (values are enrichment objects, the id
    is the key) or a list of objects each carrying its own ``id`` field.
    """
    mapping: dict[str, dict] = {}
    for path in paths:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    mapping[str(key)] = value
        elif isinstance(data, list):
            for e in data:
                if isinstance(e, dict) and e.get("id"):
                    mapping[str(e["id"])] = e
    return mapping


def cmd_apply(args: argparse.Namespace) -> int:
    mapping = _load_map(args.inputs)
    if not mapping:
        print("no enrichments found in inputs", file=sys.stderr)
        return 1

    def ai(b):
        e = mapping.get(b.id)
        if e is None:
            raise ValueError("no enrichment provided for this id")
        raw_tags = e.get("tags") or []
        tags = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
        return {
            "summary": str(e.get("summary", "")).strip(),
            "topic": str(e.get("topic", "")).strip(),
            "tags": tags,
        }

    def no_fetch(_id):  # all records already carry text; never hit the network
        raise RuntimeError("fetch disabled; record is missing text")

    store = Store.load(args.data)
    stats = enrich_pending(store, force=args.force, ai=ai, fetcher=no_fetch)
    store.save()
    print(json.dumps(stats))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="claude_enrich", description=__doc__)
    p.add_argument("--data", type=Path, default=DEFAULT_DATA, help="NDJSON store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd = sub.add_parser("dump", help="write pending bookmarks to chunk files")
    pd.add_argument("--out-dir", required=True, help="directory for chunk_NN.json files")
    pd.add_argument("--chunks", type=int, default=1, help="number of chunk files")
    pd.add_argument("--force", action="store_true", help="dump all, not just pending")

    pa = sub.add_parser("apply", help="write session-produced enrichments into the store")
    pa.add_argument("inputs", nargs="+", help="enrichment JSON file(s)")
    pa.add_argument("--force", action="store_true", help="re-enrich all, not just pending")

    args = p.parse_args(argv)
    if args.cmd == "dump":
        return cmd_dump(args)
    if args.cmd == "apply":
        return cmd_apply(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
