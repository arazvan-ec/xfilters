---
name: enrich-bookmarks
description: Enrich pending X bookmarks (summary / topic / tags) using the current Claude Code session instead of the Anthropic API — no ANTHROPIC_API_KEY needed. Use when you want Claude-quality enrichment but have no API key, or as a drop-in for `--enricher claude`.
argument-hint: "[--force] [--chunks N]"
allowed-tools: Bash, Read, Write, Agent
---

# /enrich-bookmarks — Claude-session enrichment (no API key)

`python -m xbookmarks enrich --enricher claude` calls the Anthropic API and
needs `ANTHROPIC_API_KEY`. You are already a Claude session, so you can produce
the same enrichment yourself and write it into the store — for free, offline.

Bridge script: `scripts/claude_enrich.py` (`dump` pending bookmarks → you enrich
→ `apply` writes them back with the normal semantics; manual tags are preserved).

## Steps

1. **Dump pending bookmarks into chunks.** Pick a chunk count so each chunk holds
   ~40 bookmarks (1 chunk if few). `$ARGUMENTS` may pass `--force` (redo all) and
   `--chunks N`.

   ```bash
   python scripts/claude_enrich.py dump --out-dir .enrich-work --chunks 6
   ```

2. **Enrich each chunk.** For many bookmarks, dispatch one `Agent` per chunk in
   parallel; for a handful, do it inline. Each agent reads its `chunk_NN.json`
   and writes `enrich_NN.json` — a JSON object mapping `id` → enrichment:

   ```json
   { "1893...": { "summary": "…", "topic": "…", "tags": ["…"] } }
   ```

   Field contract (matches `xbookmarks/enrich/ai.py`):
   - `summary` — 1–2 sentences, in the reader's language (Spanish for this repo).
   - `topic` — one short human-readable category. **Prefer a consistent
     vocabulary** so the site's topic grouping stays clean; reuse the categories
     in `xbookmarks/enrich/keyword.py` (e.g. "IA & Machine Learning",
     "Programación & Dev", "Diseño & UX", …) and only invent one if none fit.
   - `tags` — 2–5 lowercase kebab-case tags, specific to the tweet.

   Judge only from the tweet text/author/links given. Do not invent facts.

3. **Apply and render.**

   ```bash
   python scripts/claude_enrich.py apply .enrich-work/enrich_*.json
   python -m xbookmarks render
   ```

   `apply` prints `{"enriched": N, "errors": M}`. `errors > 0` means some pending
   ids had no enrichment (a chunk was missed) — re-run step 2 for those.

4. **Clean up** the scratch dir: `rm -rf .enrich-work`.

## Notes

- Nothing leaves the machine; no API key, no network.
- Idempotent: only *pending* bookmarks are enriched unless `--force`.
- Everything is local scratch except the store (`data/bookmarks.ndjson`) and the
  rendered `site/` + `catalog/`.
