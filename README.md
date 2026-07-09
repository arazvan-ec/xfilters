# xfilters — X bookmarks catalog

Import your X (Twitter) bookmarks, store them as versioned NDJSON, enrich them with
Claude (summary / topic / tags), and present them as a **searchable static site** plus a
**Markdown catalog**.

Pipeline — each stage is decoupled and idempotent:

```
ingest ──▶ store (data/bookmarks.ndjson) ──▶ enrich (Claude) ──▶ render (site + catalog)
```

## Install

```bash
python -m venv .venv && source .venv/bin/activate
make install          # pip install -e ".[dev]"
```

## 1. Get your bookmarks

X's official data archive does **not** include bookmarks and the API's bookmarks
endpoint is paid-only, so v1 imports from a file you provide — via a pluggable adapter,
so an API/automation adapter can be added later without touching the rest.

**Option A — browser-console export (recommended).** Open `https://x.com/i/bookmarks`
while logged in, open DevTools → Console, paste [`scripts/export-bookmarks.js`](scripts/export-bookmarks.js),
and press Enter. It auto-scrolls, then copies a JSON array to your clipboard. Save it as
`bookmarks.json`. It uses your own session — no API key, no stored credentials.

**Option B — a list of URLs.** A `.txt` with one tweet URL per line (or a JSON array of
URLs). The missing content is filled in during enrichment.

Ingest either one (the format is autodetected):

```bash
python -m xbookmarks ingest bookmarks.json      # or: make ingest INPUT=bookmarks.json
```

Ingestion is additive and idempotent: re-importing the same bookmarks changes nothing and
never overwrites enrichment or manual edits.

## 2. Enrich + render

```bash
export ANTHROPIC_API_KEY=sk-...     # required for enrichment
make build                          # enrich pending + render site & catalog
```

- `enrich` only processes records not yet enriched (use `--force` to redo, `--limit N` to
  cap API calls / cost). Tags you set by hand (`tags_source: "manual"`) are never overwritten.
- Output: `site/index.html` (open it directly — search box + tag filters, no server needed)
  and `catalog/index.md` (grouped by tag, browsable on GitHub).

### Commands

| Command | Does |
| --- | --- |
| `python -m xbookmarks ingest <file>` | import a JSON export or URL list into the store |
| `python -m xbookmarks enrich [--limit N] [--force]` | summarize/tag pending bookmarks with Claude |
| `python -m xbookmarks render [--site DIR] [--catalog DIR]` | (re)build the site + catalog |
| `python -m xbookmarks build` | `enrich` pending + `render` |

Global: `--data PATH` sets the NDJSON store (default `data/bookmarks.ndjson`).

## Configuration

| Env var | Purpose | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key (never commit it) | — |
| `XBOOKMARKS_MODEL` | enrichment model | `claude-sonnet-5` |

## Publish (optional)

`site/index.html` is a single self-contained file. Commit `site/` and enable GitHub Pages
(Settings → Pages → deploy from branch, `/` or `/docs`) to host your catalog for free.

## Editing tags by hand

Open `data/bookmarks.ndjson`, set a record's `"tags"` and `"tags_source": "manual"`.
Future `enrich`/`build` runs keep your tags and only (re)generate the summary/topic.

## Develop

```bash
make test     # pytest — fetch + Claude calls are mocked, so tests run offline
make lint     # ruff
```

The design contract and plan live in `.claude/flywheel/specs/x-bookmarks-catalog.md`.

> Not affiliated with X. Use your own bookmarks and respect X's Terms of Service.
