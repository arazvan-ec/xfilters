"""Generic record store for agent-run processes.

Agent-native processes (a Claude session running a skill) need somewhere to
persist their output *the same way the repo persists data* — not ad-hoc files
scattered around. This is that shared layer: a small, id-keyed, upsert store,
one **collection** per process (e.g. ``car_analyses``).

Two backends behind one interface, chosen by ``XBOOKMARKS_BACKEND``:

- ``ndjson`` (default): ``data/<collection>.ndjson`` — atomic writes, records
  emitted sorted by id so diffs stay stable. Mirrors ``xbookmarks/store.py``.
- ``supabase``: a Postgres table (one row per record) via the Supabase client.
  Implemented in ``xbookmarks/records_supabase.py`` and wired once the migration
  lands; until then selecting it raises a clear error.

The interface is intentionally the same shape as ``store.Store`` so processes and
tests don't care which backend is active:
    s = open_store("car_analyses")
    s.upsert({"id": "...", ...}); s.save()   # ndjson batches; supabase is immediate
    s.all(); s.get(id)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_DATA_DIR = Path("data")


class RecordStore:
    """NDJSON-backed, id-keyed record store for one collection."""

    def __init__(self, collection: str, *, data_dir: Path | str = DEFAULT_DATA_DIR,
                 id_field: str = "id") -> None:
        self.collection = collection
        self.id_field = id_field
        self.path = Path(data_dir) / f"{collection}.ndjson"
        self._by_id: dict[str, dict] = {}

    @classmethod
    def load(cls, collection: str, **kw) -> RecordStore:
        store = cls(collection, **kw)
        if store.path.exists():
            # Split on "\n" only — never str.splitlines(), which also breaks on
            # Unicode line separators (U+2028/U+2029/NEL/…) that live unescaped
            # inside valid JSON string values. (See the store.py regression.)
            for line in store.path.read_text(encoding="utf-8").split("\n"):
                if line.strip():
                    rec = json.loads(line)
                    rid = str(rec.get(store.id_field, ""))
                    if rid:
                        store._by_id[rid] = rec
        return store

    def all(self) -> list[dict]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def get(self, id_: str) -> dict | None:
        return self._by_id.get(str(id_))

    def upsert(self, record: dict) -> None:
        rid = str(record.get(self.id_field, ""))
        if not rid:
            raise ValueError(f"record is missing required id field {self.id_field!r}")
        self._by_id[rid] = record

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(self._by_id[k], ensure_ascii=False, sort_keys=True)
            for k in sorted(self._by_id)
        ]
        data = "\n".join(lines) + ("\n" if lines else "")
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(self.path)  # atomic on the same filesystem


def open_store(collection: str, *, backend: str | None = None, **kw):
    """Open the configured store backend for ``collection``.

    Backend precedence: explicit ``backend`` arg, then ``XBOOKMARKS_BACKEND`` env,
    then ``ndjson``. Keeping this factory as the single entry point means the
    Postgres cutover is a one-line default change, not a sweep across processes.
    """
    backend = (backend or os.environ.get("XBOOKMARKS_BACKEND", "ndjson")).lower()
    if backend == "ndjson":
        return RecordStore.load(collection, **kw)
    if backend == "supabase":
        from .records_supabase import SupabaseRecordStore

        # Building a real client needs the `supabase` package + SUPABASE_URL/KEY;
        # absent those, load() raises a clear RuntimeError (see records_supabase).
        return SupabaseRecordStore.load(collection, **kw)
    raise ValueError(f"unknown backend {backend!r} (expected 'ndjson' or 'supabase')")
