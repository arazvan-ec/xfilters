"""Command-line interface: ingest / enrich / render / build.

The ``cmd_*`` functions take explicit paths and accept injected ``fetcher``/``ai``
(via ``**kw``) so they can be driven deterministically and offline from tests.
``main`` wires them to argparse for real use.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .enrich import enrich_pending
from .ingest.base import autodetect
from .render.catalog import render_catalog
from .render.site import render_site
from .store import Store

DEFAULT_DATA = Path("data/bookmarks.ndjson")
DEFAULT_SITE = Path("site")
DEFAULT_CATALOG = Path("catalog")


def cmd_ingest(input_path: Path | str, data_path: Path | str = DEFAULT_DATA) -> int:
    store = Store.load(data_path)
    added = store.add_ingested(autodetect(input_path).load())
    store.save()
    return added


def cmd_enrich(
    data_path: Path | str = DEFAULT_DATA, *, limit=None, force=False, **kw
) -> dict:
    store = Store.load(data_path)
    stats = enrich_pending(store, limit=limit, force=force, **kw)
    store.save()
    return stats


def cmd_render(
    data_path: Path | str = DEFAULT_DATA,
    site_dir: Path | str = DEFAULT_SITE,
    catalog_dir: Path | str = DEFAULT_CATALOG,
) -> None:
    store = Store.load(data_path)
    render_site(store.all(), site_dir)
    render_catalog(store.all(), catalog_dir)


def cmd_build(
    data_path: Path | str = DEFAULT_DATA,
    site_dir: Path | str = DEFAULT_SITE,
    catalog_dir: Path | str = DEFAULT_CATALOG,
    *,
    limit=None,
    force=False,
    **kw,
) -> dict:
    store = Store.load(data_path)
    stats = enrich_pending(store, limit=limit, force=force, **kw)
    store.save()
    render_site(store.all(), site_dir)
    render_catalog(store.all(), catalog_dir)
    return stats


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="xbookmarks", description="X bookmarks catalog")
    p.add_argument("--data", type=Path, default=DEFAULT_DATA, help="NDJSON store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="import bookmarks from a JSON export or URL list")
    pi.add_argument("input", type=Path)

    pe = sub.add_parser("enrich", help="summarize/tag pending bookmarks with Claude")
    pe.add_argument("--limit", type=int)
    pe.add_argument("--force", action="store_true")

    pr = sub.add_parser("render", help="build the static site and Markdown catalog")
    pr.add_argument("--site", type=Path, default=DEFAULT_SITE)
    pr.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    pb = sub.add_parser("build", help="enrich pending + render")
    pb.add_argument("--limit", type=int)
    pb.add_argument("--force", action="store_true")
    pb.add_argument("--site", type=Path, default=DEFAULT_SITE)
    pb.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)

    args = p.parse_args(argv)

    if args.cmd == "ingest":
        n = cmd_ingest(args.input, args.data)
        print(f"ingested {n} new bookmark(s)")
    elif args.cmd == "enrich":
        s = cmd_enrich(args.data, limit=args.limit, force=args.force)
        print(f"enriched {s['enriched']}, errors {s['errors']}")
    elif args.cmd == "render":
        cmd_render(args.data, args.site, args.catalog)
        print("rendered site + catalog")
    elif args.cmd == "build":
        s = cmd_build(args.data, args.site, args.catalog, limit=args.limit, force=args.force)
        print(f"built: enriched {s['enriched']}, errors {s['errors']}")
