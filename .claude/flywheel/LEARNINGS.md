# flywheel learnings

## decision: intercept X's Bookmarks GraphQL instead of scraping the DOM
<!-- fw: type=decision; date=2026-07-09; files=extension/collector.js,xbookmarks/ingest/extension.py; spec=x-bookmarks-catalog; branch=claude/flywheel-plugin-check-7o6230 -->

For capture, patching `fetch`/`XHR` to read X's Bookmarks GraphQL responses (a Chrome
MV3 content script in the MAIN world) beats DOM scraping: X obfuscates the DOM but the
GraphQL payload is structured and rich (full text, note-tweets, media variants,
engagement metrics). This came from a parallel PR (#2) and was merged in because the
pluggable `Ingestor` seam let it drop in as one more adapter. Lesson: when two branches
solve the same problem, compare and fuse the strongest part of each rather than picking a
winner — the decoupled architecture is what made the fusion cheap.

## decision: decouple bookmark acquisition behind pluggable ingesters
<!-- fw: type=decision; date=2026-07-09; files=xbookmarks/ingest/base.py,xbookmarks/cli.py; spec=x-bookmarks-catalog; branch=claude/flywheel-plugin-check-7o6230 -->

X's data archive omits bookmarks and the API's bookmarks endpoint is paid-only, so
acquisition is inherently fragile/costly. We put ingestion behind an `Ingestor`
protocol (JSON export + URL list adapters) so the valuable stages (enrich/store/
render) never depend on how bookmarks were obtained; an API/automation adapter can
be added later without touching the rest. Rejected: integrating the paid X API v2
directly (couples the whole tool to a ~$100/mo provider).

## gotcha: HTML-escape-for-text-content does NOT escape quotes in attribute context
<!-- fw: type=gotcha; date=2026-07-09; files=xbookmarks/render/site.py; spec=x-bookmarks-catalog; branch=claude/flywheel-plugin-check-7o6230 -->

The `div.textContent=s; return div.innerHTML` trick only escapes `& < >` (text-node
serialization), NOT `"`. Using it for a value placed inside `href="..."` let a tweet
URL break out of the attribute (confirmed DOM XSS in a real browser). Guard: for any
attacker-influenced URL, allowlist the scheme (http/https only, else `#`) AND
attribute-escape the quote — do both, and prefer setting `a.href` as a DOM property
over string concatenation. Also project a minimal public field set into the published
page (don't `asdict()` the whole record — it leaks `enrich_error` etc.).

## gotcha: a JSON string value gets iterated character-by-character in Python
<!-- fw: type=gotcha; date=2026-07-09; files=xbookmarks/enrich/ai.py; spec=x-bookmarks-catalog; branch=claude/flywheel-plugin-check-7o6230 -->

When parsing model output like `{"tags": "a,b"}`, `for t in data.get("tags")` silently
iterates the string's characters instead of failing, and the record is marked enriched
with garbage tags. Guard: `isinstance(x, list)` before iterating any model-provided
collection, defaulting to `[]` (or raising so it lands in `enrich_error`).

## pattern: keep flywheel's own verify/review offline and deterministic
<!-- fw: type=pattern; date=2026-07-09; files=xbookmarks/enrich/fetch.py,xbookmarks/enrich/ai.py,tests/test_cli.py; spec=x-bookmarks-catalog; branch=claude/flywheel-plugin-check-7o6230 -->

Network + LLM calls are injectable (`fetcher=`, `ai=`, `client=`) so the whole test
suite (and the success-metric test) runs offline with fakes. For the one piece of real
integration that can't be asserted offline (the syndication `_token`/base36 logic), add
a characterization test on known small inputs so a regression can't slip through green.
Real-browser checks (Playwright + the pre-installed Chromium at /opt/pw-browsers) are
for one-off security verification, not the committed suite — don't add playwright as a
project dependency.
