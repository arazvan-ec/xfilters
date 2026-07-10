"""Pure normalization of X's Bookmarks GraphQL responses.

This module is a faithful Python port of the extraction / normalization logic in
``extension/collector.js`` (``findTweetResults``, ``normalizeTweet``,
``bestVideoUrl``). It is intentionally **pure**: no network access, no Playwright,
no clock reads. Given a decoded GraphQL JSON payload it returns normalized bookmark
records that match the schema emitted by the Chrome extension, so the output is
interchangeable with an extension capture and can be fed straight to
``python -m xbookmarks ingest <file>``.

Keeping this dependency-free means it imports (and unit-tests) without Playwright
installed; the impure live-capture edge lives in ``scripts/capture_playwright.py``.

Emitted record schema (per tweet)::

    {
      "id": str,
      "url": str,
      "text": str,
      "lang": str | None,
      "created_at": str | None,   # ISO 8601
      "author": {"name": str, "handle": str, "avatar": str},
      "media": [{"type": str, "url": str, "thumb": str}],
      "metrics": {"likes", "retweets", "replies", "quotes", "bookmarks", "views"},
      "hashtags": [str],
      "mentions": [str],
      "links": [str],
      "is_quote": bool,
      "captured_at": str,         # caller-supplied (impure edge)
      "source": "x-bookmarks",
    }
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime


def extract_tweet_results(payload: dict) -> list[dict]:
    """Recursively collect every ``tweet_results.result`` object in ``payload``.

    Port of ``findTweetResults`` in ``extension/collector.js``, including cycle
    protection (objects already visited are skipped via ``id()`` identity).
    """
    out: list[dict] = []
    seen: set[int] = set()

    def walk(node: object) -> None:
        if not isinstance(node, (dict, list)):
            return
        marker = id(node)
        if marker in seen:
            return
        seen.add(marker)

        if isinstance(node, dict):
            tw = node.get("tweet_results")
            if isinstance(tw, dict) and isinstance(tw.get("result"), dict):
                out.append(tw["result"])
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        else:  # list
            for value in node:
                if isinstance(value, (dict, list)):
                    walk(value)

    walk(payload)
    return out


def _best_video_url(media: dict) -> str:
    """Port of ``bestVideoUrl``: pick the highest-bitrate mp4 variant, else fall
    back to the still image."""
    video_info = media.get("video_info") or {}
    variants = video_info.get("variants") or []
    mp4 = [v for v in variants if v.get("content_type") == "video/mp4"]
    mp4.sort(key=lambda v: v.get("bitrate") or 0, reverse=True)
    if mp4 and mp4[0].get("url"):
        return mp4[0]["url"]
    return media.get("media_url_https") or ""


def _to_iso(created_at: str) -> str | None:
    """Parse an X ``legacy.created_at`` timestamp (RFC 2822 style) to ISO 8601.

    Mirrors ``new Date(legacy.created_at).toISOString()`` in the extension.
    Returns ``None`` if the value can't be parsed.
    """
    if not created_at:
        return None
    try:
        dt = parsedate_to_datetime(created_at)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        # Fall back to ISO-ish inputs (e.g. already-normalized captures).
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt.isoformat()


def normalize_tweet_result(result: dict, captured_at: str = "") -> dict | None:
    """Normalize one ``tweet_results.result`` object into a bookmark record.

    Port of ``normalizeTweet``. Returns ``None`` when no tweet id can be found.

    ``captured_at`` is passed in by the caller (default ``""``) so this function
    stays pure — it never reads the clock.
    """
    if not isinstance(result, dict):
        return None

    # Unwrap tweets that arrive inside a visibility wrapper.
    t = result
    if t.get("__typename") == "TweetWithVisibilityResults" and isinstance(t.get("tweet"), dict):
        t = t["tweet"]

    legacy = t.get("legacy") or {}
    id_ = t.get("rest_id") or legacy.get("id_str")
    if not id_:
        return None

    # Author (X has been migrating fields from user.legacy -> user.core).
    core = t.get("core") or {}
    user_results = core.get("user_results") or {}
    user = user_results.get("result") or {}
    u_legacy = user.get("legacy") or {}
    u_core = user.get("core") or {}
    handle = u_core.get("screen_name") or u_legacy.get("screen_name") or ""
    name = u_core.get("name") or u_legacy.get("name") or ""
    avatar = (
        (user.get("avatar") or {}).get("image_url")
        or u_legacy.get("profile_image_url_https")
        or ""
    )

    # Text: long-form "note tweet" wins over the truncated legacy text.
    note = None
    note_tweet = t.get("note_tweet")
    if isinstance(note_tweet, dict):
        note_results = note_tweet.get("note_tweet_results") or {}
        note = note_results.get("result")
    note = note if isinstance(note, dict) else None
    text = (note and note.get("text")) or legacy.get("full_text") or legacy.get("text") or ""

    entities = (note and note.get("entity_set")) or legacy.get("entities") or {}
    hashtags = [h.get("text") for h in (entities.get("hashtags") or []) if h.get("text")]
    mentions = [
        m.get("screen_name") for m in (entities.get("user_mentions") or []) if m.get("screen_name")
    ]
    links = [
        u.get("expanded_url") or u.get("url")
        for u in (entities.get("urls") or [])
        if (u.get("expanded_url") or u.get("url"))
    ]

    extended = legacy.get("extended_entities") or {}
    legacy_entities = legacy.get("entities") or {}
    media_list = extended.get("media") or legacy_entities.get("media") or []
    media = [
        {
            "type": m.get("type"),  # photo | video | animated_gif
            "url": m.get("media_url_https") if m.get("type") == "photo" else _best_video_url(m),
            "thumb": m.get("media_url_https"),
        }
        for m in media_list
    ]

    created_at = _to_iso(legacy.get("created_at") or "")

    views = t.get("views") or {}
    try:
        view_count = int(views.get("count"))
    except (TypeError, ValueError):
        view_count = 0
    metrics = {
        "likes": legacy.get("favorite_count") or 0,
        "retweets": legacy.get("retweet_count") or 0,
        "replies": legacy.get("reply_count") or 0,
        "quotes": legacy.get("quote_count") or 0,
        "bookmarks": legacy.get("bookmark_count") or 0,
        "views": view_count,
    }

    return {
        "id": str(id_),
        "url": (
            f"https://x.com/{handle}/status/{id_}"
            if handle
            else f"https://x.com/i/status/{id_}"
        ),
        "text": text,
        "lang": legacy.get("lang") or None,
        "created_at": created_at,
        "author": {"name": name, "handle": handle, "avatar": avatar},
        "media": media,
        "metrics": metrics,
        "hashtags": hashtags,
        "mentions": mentions,
        "links": links,
        "is_quote": bool(legacy.get("is_quote_status")),
        "captured_at": captured_at,
        "source": "x-bookmarks",
    }


def normalize_payload(payload: dict, captured_at: str = "") -> list[dict]:
    """Extract, normalize and de-dupe (by id) every tweet in a GraphQL payload.

    One record per id: the first occurrence wins, matching the extension's
    "skip if already stored" behavior. Order follows first appearance.
    """
    records: dict[str, dict] = {}
    for result in extract_tweet_results(payload):
        rec = normalize_tweet_result(result, captured_at=captured_at)
        if rec and rec["id"] and rec["id"] not in records:
            records[rec["id"]] = rec
    return list(records.values())
