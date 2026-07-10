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
endpoint is paid-only, so acquisition happens client-side in your own browser — via
pluggable adapters, so an API/automation adapter can be added later without touching
the rest.

**Option A — Chrome extension (recommended, richest data).** Load [`extension/`](extension/)
unpacked (`chrome://extensions` → Developer mode → *Load unpacked*), open
`https://x.com/i/bookmarks`, and click *Iniciar captura*. It intercepts X's Bookmarks
GraphQL responses (far more robust than DOM scraping) and downloads a JSON with full
text, author, media, links **and engagement metrics**. See [`extension/README.md`](extension/README.md).

**Option B — browser-console snippet.** Paste [`scripts/export-bookmarks.js`](scripts/export-bookmarks.js)
into the DevTools console on your bookmarks page — a lighter, no-install fallback (scrapes
the DOM, so no metrics).

**Option C — a list of URLs.** A `.txt` with one tweet URL per line (or a JSON array of
URLs); the content is filled in during enrichment.

Ingest any of them (the format is autodetected — extension capture, JSON export, or URL list):

```bash
python -m xbookmarks ingest x-bookmarks-2024-01-01.json   # or: make ingest INPUT=<file>
```

Ingestion is additive and idempotent: re-importing the same bookmarks changes nothing and
never overwrites enrichment or manual edits.

## 2. Enrich + render

Two enrichers — pick per run with `--enricher`:

- **`keyword`** (default) — fast, free, offline. Keyword/domain rules assign a category
  (`topic`) and tags (ES/EN categories tuned for this project; edit them in
  `xbookmarks/enrich/keyword.py`). No API key needed.
- **`claude`** — richer: a Claude-generated summary, topic and open-ended tags. Needs an
  API key.

```bash
# free / offline (default)
make build                                    # == python -m xbookmarks build --enricher keyword

# richer, with Claude
export ANTHROPIC_API_KEY=sk-...
python -m xbookmarks build --enricher claude
```

- `enrich` only processes records not yet enriched (`--force` to redo, `--limit N` to cap
  API calls / cost). Tags you set by hand (`tags_source: "manual"`) are never overwritten.
- Output: `site/index.html` (open it directly — search, tag filters, sort by recency /
  likes / views) and `catalog/index.md` (grouped by tag, browsable on GitHub).

### Commands

| Command | Does |
| --- | --- |
| `python -m xbookmarks ingest <file>` | import an extension capture, JSON export, or URL list |
| `python -m xbookmarks enrich [--enricher keyword\|claude] [--limit N] [--force]` | categorize/tag pending bookmarks |
| `python -m xbookmarks render [--site DIR] [--catalog DIR]` | (re)build the site + catalog |
| `python -m xbookmarks build [--enricher keyword\|claude]` | `enrich` pending + `render` |

Global: `--data PATH` sets the NDJSON store (default `data/bookmarks.ndjson`).

## Configuration

| Env var | Purpose | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key — only for `--enricher claude` (never commit it) | — |
| `XBOOKMARKS_MODEL` | Claude enrichment model | `claude-sonnet-5` |

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

> **Privacy:** committing `data/bookmarks.ndjson` and publishing `site/` makes the full
> text of your bookmarked tweets public and permanent in git history — including tweets
> later deleted or made private. Keep the repo private, or curate what you publish.
>
> Not affiliated with X. Use your own bookmarks and respect X's Terms of Service.
