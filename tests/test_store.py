from xbookmarks.models import Bookmark
from xbookmarks.store import Store


def mk(id_, **kw):
    return Bookmark(id=id_, url=f"https://x.com/u/status/{id_}", **kw)


def test_add_ingested_is_idempotent(tmp_path):
    p = tmp_path / "b.ndjson"
    s = Store.load(p)
    assert s.add_ingested([mk("1"), mk("2")]) == 2
    s.save()
    first = p.read_text()

    s2 = Store.load(p)
    assert s2.add_ingested([mk("1"), mk("2")]) == 0  # already present
    s2.save()
    assert p.read_text() == first  # 0 changes on re-run


def test_preserves_manual_tags_on_reingest(tmp_path):
    p = tmp_path / "b.ndjson"
    s = Store.load(p)
    s.add_ingested([mk("1", tags=["kept"], tags_source="manual", enriched=True)])
    s.save()

    s2 = Store.load(p)
    s2.add_ingested([mk("1")])  # raw re-ingest, no tags
    assert s2.get("1").tags == ["kept"]
    assert s2.get("1").tags_source == "manual"
    assert s2.get("1").enriched is True


def test_atomic_write_creates_parent_and_valid_file(tmp_path):
    p = tmp_path / "nested" / "b.ndjson"
    s = Store.load(p)
    s.add_ingested([mk("1")])
    s.save()
    lines = p.read_text().splitlines()
    assert len(lines) == 1
    assert Bookmark.from_json_line(lines[0]).id == "1"


def test_pending_excludes_enriched_and_errored(tmp_path):
    s = Store.load(tmp_path / "b.ndjson")
    s.add_ingested([mk("1"), mk("2", enriched=True), mk("3", enrich_error="boom")])
    assert [b.id for b in s.pending()] == ["1"]


def test_all_is_sorted_by_id(tmp_path):
    s = Store.load(tmp_path / "b.ndjson")
    s.add_ingested([mk("3"), mk("1"), mk("2")])
    assert [b.id for b in s.all()] == ["1", "2", "3"]


def test_roundtrip_text_with_unicode_line_separators(tmp_path):
    # Tweet text can contain U+2028/U+2029/NEL/VT/FF. json.dumps leaves these
    # unescaped, and str.splitlines() would wrongly treat them as record
    # boundaries and corrupt the record. The store must round-trip them as a
    # single record. Regression for load() splitting on "\n" only.
    p = tmp_path / "b.ndjson"
    text = "one two threefourfivesix"
    s = Store.load(p)
    s.add_ingested([mk("1", text=text), mk("2")])
    s.save()

    s2 = Store.load(p)
    assert [b.id for b in s2.all()] == ["1", "2"]  # still two records, not split
    assert s2.get("1").text == text
