"""Ingest a plain list of tweet URLs (newline-separated text or a JSON array).

Only id and url are known here; the rest of the content is filled in later by the
enrichment fetch step.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Bookmark
from .base import extract_tweet_id


class UrlListIngestor:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[Bookmark]:
        text = self.path.read_text(encoding="utf-8")
        try:
            data = json.loads(text)
            urls = [str(x) for x in data] if isinstance(data, list) else []
        except json.JSONDecodeError:
            urls = [line.strip() for line in text.splitlines() if line.strip()]

        out: list[Bookmark] = []
        for url in urls:
            id_ = extract_tweet_id(url)
            if not id_:
                continue
            out.append(Bookmark(id=id_, url=url, source="url-list"))
        return out
