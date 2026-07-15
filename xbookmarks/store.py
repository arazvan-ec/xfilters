"""NDJSON-backed store for bookmarks, keyed by tweet id.

The store is the source of truth (``data/bookmarks.ndjson``). Writes are atomic
(temp file + rename) and records are emitted sorted by id so diffs stay stable.
"""

from __future__ import annotations

from pathlib import Path

from .models import Bookmark


class Store:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._by_id: dict[str, Bookmark] = {}

    @classmethod
    def load(cls, path: Path | str) -> Store:
        store = cls(path)
        if store.path.exists():
            # Split only on "\n" — the record separator save() writes. Do NOT use
            # str.splitlines(), which also breaks on Unicode line separators
            # (U+2028/U+2029/U+0085, \v, \f, …) that occur unescaped inside valid
            # JSON string values (e.g. tweet text), corrupting those records.
            for line in store.path.read_text(encoding="utf-8").split("\n"):
                if line.strip():
                    b = Bookmark.from_json_line(line)
                    store._by_id[b.id] = b
        return store

    def all(self) -> list[Bookmark]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def get(self, id_: str) -> Bookmark | None:
        return self._by_id.get(id_)

    def add_ingested(self, raw: list[Bookmark]) -> int:
        """Add only ids not already present; leave existing records untouched.

        Ingestion is additive, so re-importing the same bookmarks is a no-op and
        never clobbers enrichment or manual edits. Returns the number added.
        """
        added = 0
        for b in raw:
            if b.id not in self._by_id:
                self._by_id[b.id] = b
                added += 1
        return added

    def upsert(self, bookmark: Bookmark) -> None:
        """Replace a record by id (used by enrichment write-back)."""
        self._by_id[bookmark.id] = bookmark

    def pending(self) -> list[Bookmark]:
        """Records not yet enriched and not previously errored."""
        return [b for b in self.all() if not b.enriched and not b.enrich_error]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [b.to_json_line() for b in self.all()]
        data = "\n".join(lines) + ("\n" if lines else "")
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(self.path)  # atomic on the same filesystem
