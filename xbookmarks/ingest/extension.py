"""Ingest the rich JSON produced by the Chrome extension (extension/collector.js).

The extension captures X's Bookmarks GraphQL responses, so each record carries the
full tweet: nested ``author`` object, media (with video variants), engagement
``metrics``, hashtags, mentions and links. It emits either a bare array or the
``{"bookmarks": [...]}`` wrapper written by ``scripts/enrich.mjs``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Bookmark
from .base import extract_tweet_id


def _coerce_metrics(m) -> dict:
    """Keep only integer metric values — never let arbitrary strings into the store
    (they would otherwise reach the rendered site)."""
    out: dict = {}
    if isinstance(m, dict):
        for k, v in m.items():
            try:
                out[str(k)] = int(v)
            except (TypeError, ValueError):
                continue
    return out


def looks_like_extension(items: list) -> bool:
    """True if the records use the extension's nested shape (author dict / metrics)."""
    for it in items:
        if isinstance(it, dict) and (isinstance(it.get("author"), dict) or "metrics" in it):
            return True
    return False


class ExtensionIngestor:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[Bookmark]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            items = data.get("bookmarks") or data.get("data") or []
        else:
            items = data

        out: list[Bookmark] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            url = it.get("url", "")
            id_ = str(it.get("id") or extract_tweet_id(url))
            if not id_:
                continue
            author = it.get("author") or {}
            out.append(
                Bookmark(
                    id=id_,
                    url=url or f"https://x.com/i/status/{id_}",
                    author_handle=author.get("handle", ""),
                    author_name=author.get("name", ""),
                    text=it.get("text", ""),
                    created_at=it.get("created_at", ""),
                    lang=it.get("lang") or "",
                    media=it.get("media", []) or [],
                    hashtags=it.get("hashtags", []) or [],
                    mentions=it.get("mentions", []) or [],
                    links=it.get("links", []) or [],
                    metrics=_coerce_metrics(it.get("metrics")),
                    source="extension",
                )
            )
        return out
