import json

from xbookmarks.ingest.base import autodetect
from xbookmarks.ingest.extension import ExtensionIngestor, looks_like_extension

SAMPLE = [
    {
        "id": "123",
        "url": "https://x.com/user/status/123",
        "text": "a tweet about python",
        "created_at": "2024-01-01T00:00:00Z",
        "lang": "en",
        "author": {"handle": "user", "name": "User", "avatar": "http://a"},
        "media": [{"type": "photo", "url": "http://img", "thumb": "http://t"}],
        "metrics": {"likes": 10, "views": 100, "bookmarks": 3},
        "hashtags": ["python"],
        "mentions": ["someone"],
        "links": ["https://github.com/x/y"],
    }
]


def test_extension_maps_nested_shape(tmp_path):
    p = tmp_path / "cap.json"
    p.write_text(json.dumps(SAMPLE))
    b = ExtensionIngestor(p).load()[0]
    assert b.id == "123"
    assert b.author_handle == "user" and b.author_name == "User"
    assert b.source == "extension"
    assert b.metrics["likes"] == 10
    assert b.hashtags == ["python"] and b.links == ["https://github.com/x/y"]
    assert b.media[0]["url"] == "http://img"


def test_extension_wrapped_shape(tmp_path):
    p = tmp_path / "cap.json"
    p.write_text(json.dumps({"bookmarks": SAMPLE, "count": 1}))
    assert ExtensionIngestor(p).load()[0].id == "123"


def test_autodetect_picks_extension(tmp_path):
    p = tmp_path / "cap.json"
    p.write_text(json.dumps(SAMPLE))
    assert isinstance(autodetect(p), ExtensionIngestor)


def test_looks_like_extension():
    assert looks_like_extension([{"author": {"handle": "x"}}])
    assert looks_like_extension([{"metrics": {}}])
    assert not looks_like_extension([{"author_handle": "flat"}])


def test_metrics_are_coerced_to_int(tmp_path):
    # A tampered capture with a non-numeric metric must not enter the store.
    p = tmp_path / "cap.json"
    p.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "url": "https://x.com/u/status/1",
                    "author": {"handle": "u"},
                    "metrics": {"likes": "0</div><img src=x onerror=alert(1)>", "views": 50},
                }
            ]
        )
    )
    m = ExtensionIngestor(p).load()[0].metrics
    assert m == {"views": 50}  # the malicious string is dropped, the int kept
