"""Enrichment orchestration: fetch missing content, then summarize/tag with Claude.

Failures on a single bookmark are recorded on that record (``enrich_error``) and
never abort the batch. Manual tags (``tags_source == "manual"``) are preserved.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from ..store import Store
from .ai import generate_enrichment
from .fetch import fetch_tweet

__all__ = ["enrich_pending"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def enrich_pending(
    store: Store,
    *,
    limit: int | None = None,
    force: bool = False,
    fetcher: Callable = fetch_tweet,
    ai: Callable = generate_enrichment,
    now: Callable[[], str] = _utcnow,
) -> dict:
    """Enrich pending (or, with ``force``, all) bookmarks. Returns counts."""
    targets = store.all() if force else store.pending()
    if limit is not None:
        targets = targets[:limit]

    stats = {"enriched": 0, "errors": 0}
    for b in targets:
        try:
            if not b.text:
                content = fetcher(b.id)
                if content is None:
                    b.enrich_error = "tweet not found"
                    store.upsert(b)
                    stats["errors"] += 1
                    continue
                b.text = content.get("text", b.text)
                b.author_handle = b.author_handle or content.get("author_handle", "")
                b.author_name = b.author_name or content.get("author_name", "")
                b.created_at = b.created_at or content.get("created_at", "")
                if not b.media:
                    b.media = content.get("media", [])
            result = ai(b)
        except Exception as exc:  # a single failure must not abort the batch
            b.enrich_error = str(exc) or exc.__class__.__name__
            store.upsert(b)
            stats["errors"] += 1
            continue

        b.summary = result.get("summary", "")
        b.topic = result.get("topic", "")
        if b.tags_source != "manual":
            b.tags = result.get("tags", [])
            b.tags_source = "auto"
        b.enriched = True
        b.enrich_error = ""
        b.enriched_at = now()
        store.upsert(b)
        stats["enriched"] += 1

    return stats
