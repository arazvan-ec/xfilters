import pytest

from xbookmarks.enrich import enrich_pending
from xbookmarks.models import Bookmark
from xbookmarks.store import Store


def fake_ai_ok(_b):
    return {"summary": "sum", "topic": "top", "tags": ["t1"]}


def fake_fetch_ok(_id):
    return {
        "text": "fetched",
        "author_handle": "a",
        "author_name": "A",
        "created_at": "2024",
        "media": [],
    }


def _store(tmp_path, bookmarks):
    s = Store.load(tmp_path / "b.ndjson")
    s.add_ingested(bookmarks)
    return s


def test_enriches_pending(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", text="has text")])
    stats = enrich_pending(s, fetcher=fake_fetch_ok, ai=fake_ai_ok, now=lambda: "NOW")
    b = s.get("1")
    assert b.enriched and b.summary == "sum" and b.tags == ["t1"]
    assert b.tags_source == "auto" and b.enriched_at == "NOW"
    assert stats == {"enriched": 1, "errors": 0}


def test_fetches_when_text_missing(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", source="url-list")])
    enrich_pending(s, fetcher=fake_fetch_ok, ai=fake_ai_ok, now=lambda: "NOW")
    assert s.get("1").text == "fetched"
    assert s.get("1").author_handle == "a"


def test_preserves_manual_tags(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", text="x", tags=["mine"], tags_source="manual")])
    enrich_pending(s, fetcher=fake_fetch_ok, ai=fake_ai_ok, now=lambda: "NOW")
    assert s.get("1").tags == ["mine"]
    assert s.get("1").tags_source == "manual"
    assert s.get("1").summary == "sum"  # summary still applied


def test_error_does_not_abort_batch(tmp_path):
    s = _store(
        tmp_path,
        [Bookmark(id="1", url="u", source="url-list"), Bookmark(id="2", url="u2", text="ok")],
    )
    stats = enrich_pending(s, fetcher=lambda _id: None, ai=fake_ai_ok, now=lambda: "NOW")
    assert s.get("1").enrich_error and not s.get("1").enriched
    assert s.get("2").enriched
    assert stats == {"enriched": 1, "errors": 1}


def test_limit(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", text="a"), Bookmark(id="2", url="u", text="b")])
    stats = enrich_pending(s, limit=1, fetcher=fake_fetch_ok, ai=fake_ai_ok, now=lambda: "NOW")
    assert stats["enriched"] == 1


def test_ai_exception_marks_error(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", text="x")])

    def ai_boom(_b):
        raise RuntimeError("boom")

    stats = enrich_pending(s, fetcher=fake_fetch_ok, ai=ai_boom, now=lambda: "NOW")
    assert s.get("1").enrich_error == "boom"
    assert stats["errors"] == 1


def test_negative_limit_raises(tmp_path):
    s = _store(tmp_path, [Bookmark(id="1", url="u", text="x")])
    with pytest.raises(ValueError):
        enrich_pending(s, limit=-1, fetcher=fake_fetch_ok, ai=fake_ai_ok)
