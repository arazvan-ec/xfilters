import json

import pytest

from xbookmarks.records import RecordStore, open_store


def test_upsert_get_all_sorted(tmp_path):
    s = RecordStore.load("things", data_dir=tmp_path)
    s.upsert({"id": "b", "v": 2})
    s.upsert({"id": "a", "v": 1})
    s.save()

    s2 = RecordStore.load("things", data_dir=tmp_path)
    assert [r["id"] for r in s2.all()] == ["a", "b"]  # sorted by id
    assert s2.get("a") == {"id": "a", "v": 1}
    assert s2.get("missing") is None


def test_upsert_replaces_by_id(tmp_path):
    s = RecordStore.load("things", data_dir=tmp_path)
    s.upsert({"id": "x", "v": 1})
    s.upsert({"id": "x", "v": 2})  # same id -> replace
    s.save()
    assert RecordStore.load("things", data_dir=tmp_path).get("x") == {"id": "x", "v": 2}


def test_missing_id_raises(tmp_path):
    s = RecordStore.load("things", data_dir=tmp_path)
    with pytest.raises(ValueError):
        s.upsert({"no_id": 1})


def test_custom_id_field(tmp_path):
    s = RecordStore.load("cars", data_dir=tmp_path, id_field="slug")
    s.upsert({"slug": "tesla-model-3", "score": 8})
    s.save()
    reloaded = RecordStore.load("cars", data_dir=tmp_path, id_field="slug")
    assert reloaded.get("tesla-model-3")["score"] == 8


def test_roundtrip_survives_unicode_line_separators(tmp_path):
    # Same hazard as the bookmarks store: a value with U+2028 must not be split.
    s = RecordStore.load("things", data_dir=tmp_path)
    s.upsert({"id": "1", "text": "a b c"})
    s.upsert({"id": "2", "text": "ok"})
    s.save()
    s2 = RecordStore.load("things", data_dir=tmp_path)
    assert [r["id"] for r in s2.all()] == ["1", "2"]
    assert s2.get("1")["text"] == "a b c"


def test_open_store_default_is_ndjson(tmp_path, monkeypatch):
    monkeypatch.delenv("XBOOKMARKS_BACKEND", raising=False)
    assert isinstance(open_store("things", data_dir=tmp_path), RecordStore)


def test_open_store_supabase_not_wired_yet(monkeypatch):
    monkeypatch.setenv("XBOOKMARKS_BACKEND", "supabase")
    with pytest.raises(NotImplementedError):
        open_store("things")


def test_open_store_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("XBOOKMARKS_BACKEND", "mysql")
    with pytest.raises(ValueError):
        open_store("things")


def test_ndjson_is_valid_and_sorted_on_disk(tmp_path):
    s = RecordStore.load("things", data_dir=tmp_path)
    s.upsert({"id": "2"})
    s.upsert({"id": "1"})
    s.save()
    lines = (tmp_path / "things.ndjson").read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["id"] for x in lines] == ["1", "2"]
