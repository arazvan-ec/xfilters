"""Ingest a JSON export produced by the browser-console snippet (scripts/export-bookmarks.js).

Accepts either a top-level list of bookmark objects or ``{"bookmarks": [...]}``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Bookmark
from .base import extract_tweet_id


class JsonExportIngestor:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[Bookmark]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        items = data["bookmarks"] if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise ValueError("unsupported export format: expected a list of bookmark objects")

        out: list[Bookmark] = []
        for it in items:
            if not isinstance(it, dict):
                continue  # skip malformed entries rather than crashing the ingest
            url = it.get("url", "")
            id_ = str(it.get("id") or extract_tweet_id(url))
            if not id_:
                continue
            out.append(
                Bookmark(
                    id=id_,
                    url=url or f"https://x.com/i/status/{id_}",
                    author_handle=it.get("author_handle", ""),
                    author_name=it.get("author_name", ""),
                    text=it.get("text", ""),
                    created_at=it.get("created_at", ""),
                    media=it.get("media", []) or [],
                    source="json-export",
                )
            )
        return out
