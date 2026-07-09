# xfilters — X bookmarks catalog

Import your X (Twitter) bookmarks, store them as versioned NDJSON, enrich them with
Claude (summary / topic / tags), and present them as a searchable static site + a
Markdown catalog.

Pipeline: **ingest → enrich → store → render** (each stage decoupled and idempotent).

> Work in progress — see `.claude/flywheel/specs/x-bookmarks-catalog.md` for the contract.

## Quick start

```bash
make install                         # pip install -e ".[dev]"
make ingest INPUT=bookmarks.json     # import from a JSON export or a URL list
export ANTHROPIC_API_KEY=sk-...      # required for enrichment
make build                           # enrich pending + render site & catalog
```

More docs (how to export your bookmarks, the console snippet, configuration) land in T10.
