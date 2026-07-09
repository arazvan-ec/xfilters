import httpx
import pytest

from xbookmarks.enrich.fetch import FetchError, fetch_tweet


class FakeResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._json


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, *args, **kwargs):
        item = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


def test_fetch_parses_content():
    data = {
        "text": "hi",
        "user": {"screen_name": "u", "name": "U"},
        "created_at": "2024-01-01",
        "mediaDetails": [{"type": "photo", "media_url_https": "http://img"}],
    }
    res = fetch_tweet("1", client=FakeClient([FakeResp(200, data)]))
    assert res["text"] == "hi"
    assert res["author_handle"] == "u"
    assert res["author_name"] == "U"
    assert res["media"] == [{"type": "photo", "url": "http://img"}]


def test_fetch_404_returns_none():
    assert fetch_tweet("1", client=FakeClient([FakeResp(404)])) is None


def test_fetch_retries_then_raises():
    c = FakeClient([httpx.ConnectError("x")] * 3)
    with pytest.raises(FetchError):
        fetch_tweet("1", client=c, retries=3, sleep=lambda _s: None)
    assert c.calls == 3


def test_fetch_retries_then_succeeds():
    c = FakeClient([httpx.ConnectError("x"), FakeResp(200, {"text": "ok", "user": {}})])
    res = fetch_tweet("1", client=c, retries=3, sleep=lambda _s: None)
    assert res["text"] == "ok"
    assert c.calls == 2
