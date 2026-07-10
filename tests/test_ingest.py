import json

import pytest

from xbookmarks.ingest.base import autodetect, extract_tweet_id
from xbookmarks.ingest.json_export import JsonExportIngestor
from xbookmarks.ingest.url_list import UrlListIngestor


def test_extract_tweet_id():
    assert extract_tweet_id("https://x.com/user/status/123") == "123"
    assert extract_tweet_id("https://twitter.com/u/status/999?s=20") == "999"
    assert extract_tweet_id("not a url") == ""


def test_json_export_list(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "url": "https://x.com/u/status/1",
                    "author_handle": "u",
                    "text": "hi",
                    "media": [{"type": "photo"}],
                }
            ]
        )
    )
    bms = JsonExportIngestor(p).load()
    assert len(bms) == 1
    assert bms[0].id == "1"
    assert bms[0].source == "json-export"
    assert bms[0].text == "hi"
    assert bms[0].media == [{"type": "photo"}]


def test_json_export_wrapped_and_id_from_url(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(json.dumps({"bookmarks": [{"url": "https://x.com/u/status/7", "text": "x"}]}))
    bms = JsonExportIngestor(p).load()
    assert bms[0].id == "7"


def test_url_list_text(tmp_path):
    p = tmp_path / "u.txt"
    p.write_text("https://x.com/u/status/1\nhttps://x.com/u/status/2\n\n")
    bms = UrlListIngestor(p).load()
    assert [b.id for b in bms] == ["1", "2"]
    assert all(b.source == "url-list" for b in bms)


def test_url_list_json_array(tmp_path):
    p = tmp_path / "u.json"
    p.write_text(json.dumps(["https://x.com/u/status/5"]))
    assert UrlListIngestor(p).load()[0].id == "5"


def test_autodetect(tmp_path):
    j = tmp_path / "a.json"
    j.write_text(json.dumps([{"id": "1", "url": "https://x.com/u/status/1"}]))
    assert isinstance(autodetect(j), JsonExportIngestor)

    u = tmp_path / "b.json"
    u.write_text(json.dumps(["https://x.com/u/status/1"]))
    assert isinstance(autodetect(u), UrlListIngestor)

    t = tmp_path / "c.txt"
    t.write_text("https://x.com/u/status/1")
    assert isinstance(autodetect(t), UrlListIngestor)


def test_json_export_skips_non_dict_items(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(json.dumps([{"url": "https://x.com/u/status/1"}, "garbage", 5]))
    assert [b.id for b in JsonExportIngestor(p).load()] == ["1"]


def test_json_export_non_list_raises(tmp_path):
    p = tmp_path / "e.json"
    p.write_text(json.dumps("just a string"))
    with pytest.raises(ValueError):
        JsonExportIngestor(p).load()


def test_json_export_data_wrapper_does_not_crash(tmp_path):
    # A {"data": [...]} export (non-extension) must load, not KeyError.
    p = tmp_path / "e.json"
    p.write_text(json.dumps({"data": [{"url": "https://x.com/u/status/9", "text": "hi"}]}))
    assert [b.id for b in JsonExportIngestor(p).load()] == ["9"]
