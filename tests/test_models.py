from xbookmarks.models import Bookmark


def test_round_trip_serialization():
    b = Bookmark(
        id="123",
        url="https://x.com/user/status/123",
        author_handle="user",
        text="hello",
        tags=["ai", "python"],
        tags_source="manual",
    )
    line = b.to_json_line()
    assert Bookmark.from_json_line(line) == b


def test_enrichment_defaults():
    b = Bookmark(id="1", url="u")
    assert b.enriched is False
    assert b.tags == []
    assert b.media == []
    assert b.summary == ""


def test_from_dict_ignores_unknown_keys():
    b = Bookmark.from_dict({"id": "1", "url": "u", "not_a_field": 42})
    assert b.id == "1"
    assert b.url == "u"


def test_json_line_is_deterministic():
    b = Bookmark(id="1", url="u", tags=["b", "a"])
    assert b.to_json_line() == b.to_json_line()
    # keys sorted -> stable diffs
    assert '"author_handle"' in b.to_json_line()
