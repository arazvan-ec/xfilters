"""Supabase/Postgres backend for the shared record store.

Mirrors ``xbookmarks.records.RecordStore`` (``load/all/get/upsert/save``) but
persists to a single generic Postgres table instead of NDJSON::

    records(collection text, id text, data jsonb, updated_at timestamptz,
            primary key (collection, id))

One row per record; ``data`` holds the whole record (including its id field).
Selected via ``XBOOKMARKS_BACKEND=supabase`` through ``records.open_store`` — no
process code changes when switching backends.

The ``supabase`` package is imported lazily (only when a real client is built),
so this module imports fine without it and tests can inject a fake client. See
``.claude/flywheel/specs/postgres-persistence.md``.
"""

from __future__ import annotations

import os

TABLE = "records"


def _make_client():
    """Build a real Supabase client from the environment (lazy, optional dep)."""
    try:
        from supabase import create_client
    except ImportError as exc:
        raise RuntimeError(
            "the 'supabase' package is required for the supabase backend "
            "(pip install -e '.[supabase]')"
        ) from exc
    try:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "set SUPABASE_URL and SUPABASE_KEY to use the supabase backend"
        ) from exc
    return create_client(url, key)


class SupabaseRecordStore:
    """Postgres-backed, id-keyed store for one collection."""

    def __init__(self, collection: str, *, client=None, id_field: str = "id", **_ignored) -> None:
        self.collection = collection
        self.id_field = id_field
        self._client = client  # built lazily from env if None
        self._by_id: dict[str, dict] = {}
        self._dirty: set[str] = set()

    @property
    def client(self):
        if self._client is None:
            self._client = _make_client()
        return self._client

    @classmethod
    def load(
        cls, collection: str, *, client=None, id_field: str = "id", **_ignored
    ) -> SupabaseRecordStore:
        store = cls(collection, client=client, id_field=id_field)
        resp = (
            store.client.table(TABLE)
            .select("data")
            .eq("collection", collection)
            .execute()
        )
        for row in (getattr(resp, "data", None) or []):
            rec = row.get("data") or {}
            rid = str(rec.get(id_field, ""))
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
        self._dirty.add(rid)

    def save(self) -> None:
        """Batch-upsert the records changed since the last save."""
        if not self._dirty:
            return
        rows = [
            {"collection": self.collection, "id": rid, "data": self._by_id[rid]}
            for rid in sorted(self._dirty)
        ]
        self.client.table(TABLE).upsert(rows, on_conflict="collection,id").execute()
        self._dirty.clear()
