"""Offline tests for the Supabase record-store backend, using a fake client.

No network and no `supabase` package required — the store talks to an injected
client that implements the tiny slice of the supabase-py API we use:
    client.table(T).select("data").eq("collection", c).execute().data
    client.table(T).upsert(rows, on_conflict="collection,id").execute()
"""

from types import SimpleNamespace

import pytest

from xbookmarks.records_supabase import TABLE, SupabaseRecordStore


class FakeTable:
    def __init__(self, backing: dict, calls: dict):
        self._backing = backing  # {(collection, id): row}
        self._calls = calls
        self._eqs: dict = {}
        self._op = None
        self._rows = None

    def select(self, *_cols):
        self._op = "select"
        return self

    def eq(self, col, val):
        self._eqs[col] = val
        return self

    def upsert(self, rows, on_conflict=None):
        self._op = "upsert"
        self._rows = rows
        self._calls["on_conflict"] = on_conflict
        return self

    def execute(self):
        if self._op == "select":
            coll = self._eqs.get("collection")
            data = [
                {"data": row["data"]}
                for key, row in self._backing.items()
                if key[0] == coll
            ]
            return SimpleNamespace(data=data)
        # upsert
        for r in self._rows:
            self._backing[(r["collection"], r["id"])] = r
        self._calls["upserts"] = self._calls.get("upserts", 0) + len(self._rows)
        return SimpleNamespace(data=self._rows)


class FakeClient:
    def __init__(self):
        self.backing: dict = {}
        self.calls: dict = {}
        self.tables_opened: list[str] = []

    def table(self, name):
        self.tables_opened.append(name)
        return FakeTable(self.backing, self.calls)


def test_upsert_save_then_load_roundtrips():
    c = FakeClient()
    s = SupabaseRecordStore.load("car_analyses", client=c)
    assert s.all() == []
    s.upsert({"id": "tesla-model-3", "score": 8})
    s.upsert({"id": "byd-atto-3", "score": 6})
    s.save()

    # A fresh load from the same backing store sees both rows, sorted by id.
    s2 = SupabaseRecordStore.load("car_analyses", client=c)
    assert [r["id"] for r in s2.all()] == ["byd-atto-3", "tesla-model-3"]
    assert s2.get("tesla-model-3") == {"id": "tesla-model-3", "score": 8}
    assert c.tables_opened and set(c.tables_opened) == {TABLE}


def test_save_uses_composite_on_conflict():
    c = FakeClient()
    s = SupabaseRecordStore.load("things", client=c)
    s.upsert({"id": "x"})
    s.save()
    assert c.calls["on_conflict"] == "collection,id"


def test_upsert_replaces_by_id():
    c = FakeClient()
    s = SupabaseRecordStore.load("things", client=c)
    s.upsert({"id": "x", "v": 1})
    s.save()
    s.upsert({"id": "x", "v": 2})
    s.save()
    assert SupabaseRecordStore.load("things", client=c).get("x") == {"id": "x", "v": 2}


def test_collections_are_isolated():
    c = FakeClient()
    a = SupabaseRecordStore.load("cars", client=c)
    a.upsert({"id": "1"})
    a.save()
    b = SupabaseRecordStore.load("bikes", client=c)
    b.upsert({"id": "1"})
    b.save()
    assert [r["id"] for r in SupabaseRecordStore.load("cars", client=c).all()] == ["1"]
    assert [r["id"] for r in SupabaseRecordStore.load("bikes", client=c).all()] == ["1"]


def test_save_noop_when_clean():
    c = FakeClient()
    s = SupabaseRecordStore.load("things", client=c)
    s.save()  # nothing dirty
    assert "upserts" not in c.calls


def test_missing_id_raises():
    c = FakeClient()
    s = SupabaseRecordStore.load("things", client=c)
    with pytest.raises(ValueError):
        s.upsert({"no_id": 1})


def test_custom_id_field():
    c = FakeClient()
    s = SupabaseRecordStore.load("cars", client=c, id_field="slug")
    s.upsert({"slug": "vw-id3", "score": 7})
    s.save()
    assert SupabaseRecordStore.load("cars", client=c, id_field="slug").get("vw-id3")["score"] == 7
