"""Fetch a tweet's content from X's public syndication endpoint (no auth).

This is the riskiest external dependency: the endpoint is undocumented and can
change. It is mocked in tests, and callers treat failures as recoverable
(marking ``enrich_error`` and moving on) rather than aborting the batch.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable

import httpx

SYNDICATION_URL = "https://cdn.syndication.twimg.com/tweet-result"
_ALPHA = "0123456789abcdefghijklmnopqrstuvwxyz"


class FetchError(RuntimeError):
    """Raised when a tweet could not be fetched after all retries."""


def _js_base36(x: float) -> str:
    """Replicate JavaScript ``Number.prototype.toString(36)`` for x >= 0."""
    int_part = int(x)
    frac = x - int_part
    if int_part == 0:
        s = "0"
    else:
        digits = []
        n = int_part
        while n > 0:
            digits.append(_ALPHA[n % 36])
            n //= 36
        s = "".join(reversed(digits))
    if frac > 0:
        s += "."
        for _ in range(20):
            frac *= 36
            d = int(frac)
            s += _ALPHA[d]
            frac -= d
            if frac == 0:
                break
    return s


def _token(id_: str) -> str:
    """The syndication endpoint's ``token`` param, derived from the tweet id."""
    n = (int(id_) / 1e15) * math.pi
    return _js_base36(n).replace("0", "").replace(".", "")


def _parse(data: dict) -> dict:
    user = data.get("user") or {}
    media = [
        {"type": m.get("type", ""), "url": m.get("media_url_https", "")}
        for m in (data.get("mediaDetails") or [])
    ]
    return {
        "text": data.get("text", ""),
        "author_handle": user.get("screen_name", ""),
        "author_name": user.get("name", ""),
        "created_at": data.get("created_at", ""),
        "media": media,
    }


def fetch_tweet(
    id_: str,
    *,
    client: httpx.Client | None = None,
    retries: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> dict | None:
    """Return parsed tweet content, ``None`` if not found, or raise on failure.

    Transient errors are retried with exponential backoff; a 404 (deleted or
    protected tweet) returns ``None``; exhausting retries raises ``FetchError``.
    """
    own = client is None
    client = client or httpx.Client(timeout=10.0)
    try:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                resp = client.get(
                    SYNDICATION_URL,
                    params={"id": id_, "token": _token(id_), "lang": "en"},
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
                return _parse(data) if data else None
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < retries - 1:
                    sleep(2**attempt)
        raise FetchError(f"failed to fetch tweet {id_}: {last_exc}")
    finally:
        if own:
            client.close()
