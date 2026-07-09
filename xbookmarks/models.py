"""The Bookmark domain object and its NDJSON (de)serialization."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields


@dataclass
class Bookmark:
    """A single X bookmark plus its enrichment. Keyed by tweet ``id``."""

    id: str
    url: str
    author_handle: str = ""
    author_name: str = ""
    text: str = ""
    created_at: str = ""  # ISO 8601
    media: list[dict] = field(default_factory=list)
    thread_ids: list[str] = field(default_factory=list)
    source: str = ""  # json-export | url-list
    imported_at: str = ""

    # enrichment
    summary: str = ""
    topic: str = ""
    tags: list[str] = field(default_factory=list)
    tags_source: str = ""  # auto | manual | hybrid
    enriched: bool = False
    enriched_at: str = ""
    enrich_error: str = ""

    def to_json_line(self) -> str:
        """Serialize to a single, deterministic JSON line (sorted keys)."""
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json_line(cls, line: str) -> Bookmark:
        return cls.from_dict(json.loads(line))

    @classmethod
    def from_dict(cls, data: dict) -> Bookmark:
        """Build from a dict, ignoring unknown keys (forward-compatible)."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
