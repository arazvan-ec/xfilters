"""Unit tests for the pure Bookmarks-GraphQL normalizer.

Everything here runs offline against small synthetic payloads constructed inline —
no network, no Playwright. These mirror the structure X returns from its Bookmarks
GraphQL endpoint closely enough to exercise the port of ``collector.js``.
"""

from xbookmarks.ingest.graphql import (
    extract_tweet_results,
    normalize_payload,
    normalize_tweet_result,
)


def _tweet_result(
    *,
    rest_id="111",
    full_text="hello world",
    handle="jane",
    name="Jane Doe",
    use_core=True,
):
    """Build a minimal ``tweet_results.result`` object (author via user.core)."""
    user_core = {"screen_name": handle, "name": name} if use_core else {}
    user_legacy = {} if use_core else {"screen_name": handle, "name": name}
    return {
        "__typename": "Tweet",
        "rest_id": rest_id,
        "core": {
            "user_results": {
                "result": {
                    "core": user_core,
                    "legacy": {
                        **user_legacy,
                        "profile_image_url_https": "https://pbs.twimg.com/pic.jpg",
                    },
                    "avatar": {"image_url": "https://pbs.twimg.com/avatar.jpg"},
                }
            }
        },
        "legacy": {
            "id_str": rest_id,
            "full_text": full_text,
            "lang": "en",
            "created_at": "Wed Oct 10 20:19:24 +0000 2018",
            "favorite_count": 5,
            "retweet_count": 2,
            "reply_count": 1,
            "quote_count": 0,
            "bookmark_count": 7,
            "is_quote_status": False,
            "entities": {
                "hashtags": [{"text": "python"}],
                "user_mentions": [{"screen_name": "someone"}],
                "urls": [{"expanded_url": "https://example.com/a", "url": "https://t.co/x"}],
            },
        },
        "views": {"count": "1234"},
    }


def _wrap_timeline(*results):
    """Nest tweet results inside a timeline-ish envelope, as X does."""
    entries = [
        {
            "content": {
                "itemContent": {"tweet_results": {"result": r}},
            }
        }
        for r in results
    ]
    return {
        "data": {
            "bookmark_timeline_v2": {
                "timeline": {
                    "instructions": [{"type": "TimelineAddEntries", "entries": entries}]
                }
            }
        }
    }


def test_extract_finds_nested_results():
    payload = _wrap_timeline(_tweet_result(rest_id="1"), _tweet_result(rest_id="2"))
    results = extract_tweet_results(payload)
    assert len(results) == 2
    assert {r["rest_id"] for r in results} == {"1", "2"}


def test_extract_handles_cycles():
    payload = _wrap_timeline(_tweet_result(rest_id="1"))
    # Introduce a reference cycle; must not infinite-loop.
    payload["data"]["self"] = payload
    results = extract_tweet_results(payload)
    assert len(results) == 1


def test_normal_tweet_author_from_core():
    rec = normalize_tweet_result(_tweet_result(), captured_at="2026-07-10T00:00:00+00:00")
    assert rec is not None
    assert rec["id"] == "111"
    assert rec["url"] == "https://x.com/jane/status/111"
    assert rec["text"] == "hello world"
    assert rec["lang"] == "en"
    assert rec["author"] == {
        "name": "Jane Doe",
        "handle": "jane",
        "avatar": "https://pbs.twimg.com/avatar.jpg",
    }
    assert rec["created_at"].startswith("2018-10-10T20:19:24")
    assert rec["metrics"] == {
        "likes": 5,
        "retweets": 2,
        "replies": 1,
        "quotes": 0,
        "bookmarks": 7,
        "views": 1234,
    }
    assert rec["hashtags"] == ["python"]
    assert rec["mentions"] == ["someone"]
    assert rec["links"] == ["https://example.com/a"]
    assert rec["is_quote"] is False
    assert rec["captured_at"] == "2026-07-10T00:00:00+00:00"
    assert rec["source"] == "x-bookmarks"


def test_author_falls_back_to_user_legacy():
    rec = normalize_tweet_result(_tweet_result(use_core=False))
    assert rec is not None
    assert rec["author"]["handle"] == "jane"
    assert rec["author"]["name"] == "Jane Doe"


def test_note_tweet_long_text_wins():
    result = _tweet_result(full_text="short truncated…")
    long_text = "x" * 400
    result["note_tweet"] = {
        "note_tweet_results": {
            "result": {
                "text": long_text,
                "entity_set": {
                    "hashtags": [{"text": "longform"}],
                    "user_mentions": [],
                    "urls": [],
                },
            }
        }
    }
    rec = normalize_tweet_result(result)
    assert rec is not None
    assert rec["text"] == long_text
    # Entities come from the note's entity_set, not legacy.
    assert rec["hashtags"] == ["longform"]


def test_visibility_wrapper_is_unwrapped():
    inner = _tweet_result(rest_id="222", full_text="sensitive but shown")
    wrapped = {"__typename": "TweetWithVisibilityResults", "tweet": inner}
    rec = normalize_tweet_result(wrapped)
    assert rec is not None
    assert rec["id"] == "222"
    assert rec["text"] == "sensitive but shown"


def test_media_video_picks_highest_bitrate():
    result = _tweet_result(rest_id="333")
    result["legacy"]["extended_entities"] = {
        "media": [
            {
                "type": "video",
                "media_url_https": "https://pbs.twimg.com/thumb.jpg",
                "video_info": {
                    "variants": [
                        {"content_type": "application/x-mpegURL", "url": "https://v/playlist.m3u8"},
                        {"content_type": "video/mp4", "bitrate": 256000, "url": "https://v/low.mp4"},
                        {"content_type": "video/mp4", "bitrate": 2176000, "url": "https://v/hi.mp4"},
                        {"content_type": "video/mp4", "bitrate": 832000, "url": "https://v/mid.mp4"},
                    ]
                },
            }
        ]
    }
    rec = normalize_tweet_result(result)
    assert rec is not None
    assert rec["media"] == [
        {
            "type": "video",
            "url": "https://v/hi.mp4",
            "thumb": "https://pbs.twimg.com/thumb.jpg",
        }
    ]


def test_photo_media_uses_still_url():
    result = _tweet_result(rest_id="444")
    result["legacy"]["extended_entities"] = {
        "media": [{"type": "photo", "media_url_https": "https://pbs.twimg.com/photo.jpg"}]
    }
    rec = normalize_tweet_result(result)
    assert rec is not None
    assert rec["media"][0]["url"] == "https://pbs.twimg.com/photo.jpg"
    assert rec["media"][0]["thumb"] == "https://pbs.twimg.com/photo.jpg"


def test_returns_none_without_id():
    assert normalize_tweet_result({"legacy": {"full_text": "no id here"}}) is None
    assert normalize_tweet_result("not a dict") is None


def test_normalize_payload_dedupes_by_id():
    # Same tweet id appears twice (overlapping pages); one record only.
    payload = _wrap_timeline(
        _tweet_result(rest_id="900", full_text="first"),
        _tweet_result(rest_id="900", full_text="second"),
        _tweet_result(rest_id="901", full_text="other"),
    )
    records = normalize_payload(payload, captured_at="2026-07-10T00:00:00+00:00")
    ids = [r["id"] for r in records]
    assert ids == ["900", "901"]
    # First occurrence wins.
    assert records[0]["text"] == "first"
    assert all(r["captured_at"] == "2026-07-10T00:00:00+00:00" for r in records)


def test_normalize_payload_default_captured_at_is_empty():
    payload = _wrap_timeline(_tweet_result(rest_id="1"))
    rec = normalize_payload(payload)[0]
    assert rec["captured_at"] == ""
