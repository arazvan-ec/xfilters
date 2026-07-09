"""Ingestor protocol, tweet-id parsing, and input autodetection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Protocol

from ..models import Bookmark

_ID_RE = re.compile(r"/status/(\d+)")


class Ingestor(Protocol):
    def load(self) -> list[Bookmark]: ...


def extract_tweet_id(url: str) -> str:
    """Return the numeric tweet id from a status URL, or '' if none."""
    m = _ID_RE.search(url or "")
    return m.group(1) if m else ""


def autodetect(path: Path | str) -> Ingestor:
    """Pick an ingestor from the input's shape.

    - a JSON list of strings, or a non-JSON newline file -> URL list
    - a JSON list of objects, or ``{"bookmarks": [...]}`` -> JSON export
    """
    from .json_export import JsonExportIngestor
    from .url_list import UrlListIngestor

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return UrlListIngestor(path)

    if isinstance(data, list) and all(isinstance(x, str) for x in data):
        return UrlListIngestor(path)
    return JsonExportIngestor(path)
