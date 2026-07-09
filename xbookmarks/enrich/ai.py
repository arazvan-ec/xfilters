"""Generate summary / topic / tags for a bookmark using Claude.

The client is injectable so tests never hit the network. The default model is
``claude-sonnet-5`` (override with the ``XBOOKMARKS_MODEL`` env var). The API key
is read from the environment by the Anthropic SDK (``ANTHROPIC_API_KEY``).
"""

from __future__ import annotations

import json
import os

from ..models import Bookmark

DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM = (
    "You categorize a saved tweet (a bookmark). Respond with ONLY a JSON object "
    "with keys: summary (a 1-2 sentence string), topic (a short string), tags "
    "(an array of 1-6 lowercase kebab-case strings). No prose, no code fences."
)


def _client():
    import anthropic

    return anthropic.Anthropic()


def _prompt(b: Bookmark) -> str:
    parts = []
    if b.author_handle:
        parts.append(f"Author: @{b.author_handle} ({b.author_name})".strip())
    parts.append(f"URL: {b.url}")
    parts.append(f"Text: {b.text}")
    return "\n".join(parts)


def _parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):  # tolerate accidental code fences
        text = text.strip("`")
        brace = text.find("{")
        if brace != -1:
            text = text[brace:]
    data = json.loads(text)
    raw_tags = data.get("tags")
    raw_tags = raw_tags if isinstance(raw_tags, list) else []
    tags = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
    return {
        "summary": str(data.get("summary", "")).strip(),
        "topic": str(data.get("topic", "")).strip(),
        "tags": tags,
    }


def generate_enrichment(b: Bookmark, *, client=None, model: str | None = None) -> dict:
    client = client or _client()
    model = model or os.environ.get("XBOOKMARKS_MODEL", DEFAULT_MODEL)
    resp = client.messages.create(
        model=model,
        max_tokens=400,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _prompt(b)}],
    )
    return _parse(resp.content[0].text)
