#!/usr/bin/env python3
"""Capture your X bookmarks with Playwright — an alternative to the Chrome extension.

Same idea, same Terms-of-Service posture as ``extension/collector.js``: it opens a
real browser window and waits for **you** to log into X yourself. It never handles
usernames, passwords, cookies or tokens — it drives a browser that already carries
*your own* interactive session. As you (and then the auto-scroller) page through
``x.com/i/bookmarks``, X's own web app fetches its "Bookmarks" GraphQL endpoint; this
script only *reads* those JSON responses as they arrive and normalizes them with the
pure ``xbookmarks.ingest.graphql`` module — exactly the tweet objects the extension
intercepts. Nothing is sent anywhere; the only output is a local JSON file.

The output is byte-compatible with an extension capture, so feed it straight into the
pipeline::

    python -m xbookmarks ingest x-bookmarks-YYYY-MM-DD.json

Usage::

    pip install -e ".[capture]"     # installs Playwright (optional extra)
    python -m playwright install chromium
    python scripts/capture_playwright.py            # writes ./x-bookmarks-<date>.json
    python scripts/capture_playwright.py --out mine.json --user-data-dir ~/.xcapture

A persistent Chromium profile (``--user-data-dir``) keeps you logged in between runs,
so you only sign in once. The browser window stays visible on purpose — this is your
session, driven in front of you.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Import the PURE normalizer eagerly — it has no heavy deps and importing this
# module should not require Playwright to be installed.
from xbookmarks.ingest.graphql import normalize_payload

BOOKMARKS_URL = "https://x.com/i/bookmarks"
# Matches e.g. /graphql/<queryId>/Bookmarks — same regex the extension uses.
BOOKMARKS_RE = re.compile(r"/graphql/[^/]+/Bookmarks\b")

# Auto-scroll tuning (mirrors collector.js).
SCROLL_PAUSE_S = 1.4
STAGNANT_LIMIT = 6


def _now_iso() -> str:
    """Real wall-clock capture time — the impure edge, deliberately kept here."""
    return datetime.now(UTC).isoformat()


def _default_out_path() -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    return Path.cwd() / f"x-bookmarks-{stamp}.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Capture X bookmarks via your own logged-in browser (Playwright).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: ./x-bookmarks-YYYY-MM-DD.json).",
    )
    p.add_argument(
        "--user-data-dir",
        type=Path,
        default=None,
        help="Persistent browser profile dir so you stay logged in between runs "
        "(default: a folder under the OS temp dir).",
    )
    p.add_argument(
        "--max-idle",
        type=int,
        default=STAGNANT_LIMIT,
        help=f"Stop after this many scrolls with no new bookmarks (default {STAGNANT_LIMIT}).",
    )
    return p.parse_args(argv)


def run(out_path: Path, user_data_dir: Path, max_idle: int) -> int:
    """Drive the browser and write the capture. Returns the number of bookmarks."""
    # Guarded import: keep Playwright a runtime-only, optional dependency so the
    # pure module and this script both *import* without it.
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Playwright is not installed. Install the optional extra:\n"
            '    pip install -e ".[capture]"\n'
            "    python -m playwright install chromium"
        ) from exc

    store: dict[str, dict] = {}

    def handle_response(response) -> None:
        if not BOOKMARKS_RE.search(response.url):
            return
        try:
            payload = response.json()
        except Exception:
            return
        added = 0
        for rec in normalize_payload(payload, captured_at=_now_iso()):
            rid = rec["id"]
            if rid and rid not in store:
                store[rid] = rec
                added += 1
        if added:
            print(f"  +{added} (total {len(store)})", flush=True)

    with sync_playwright() as pw:
        user_data_dir.mkdir(parents=True, exist_ok=True)
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.on("response", handle_response)

        print(f"Opening {BOOKMARKS_URL} …")
        page.goto(BOOKMARKS_URL, wait_until="domcontentloaded")

        print(
            "\nLog into X in the opened window if you aren't already, then make sure your\n"
            "Bookmarks page is showing. Press Enter here to start auto-scrolling…"
        )
        try:
            input()
        except EOFError:
            # Non-interactive shell: give the user a moment to log in, then proceed.
            print("(no TTY — waiting 30s for you to log in, then scrolling)")
            time.sleep(30)

        _auto_scroll(page, store, max_idle)

        context.close()

    records = sorted(store.values(), key=lambda r: (r.get("created_at") or ""), reverse=True)
    out_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(records)


def _auto_scroll(page, store: dict[str, dict], max_idle: int) -> None:
    """Scroll to the bottom repeatedly until both the bookmark count and the page
    height stop growing for ``max_idle`` iterations (port of collector.js's loop)."""
    stagnant = 0
    last_count = -1
    last_height = -1

    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.8)

    while True:
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        time.sleep(SCROLL_PAUSE_S)

        height = page.evaluate("document.documentElement.scrollHeight")
        grew = len(store) > last_count
        height_grew = height > last_height
        last_count = len(store)
        last_height = height

        if not grew and not height_grew:
            stagnant += 1
            print(f"  checking for end… ({stagnant}/{max_idle})", flush=True)
            # Nudge up then down to shake loose any lazy loading.
            page.evaluate("window.scrollBy(0, -400)")
            time.sleep(0.4)
        else:
            stagnant = 0

        if stagnant >= max_idle:
            print(f"Done: {len(store)} bookmarks captured.")
            break


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_path = args.out or _default_out_path()
    user_data_dir = args.user_data_dir or (
        Path(tempfile.gettempdir()) / "xfilters-capture-profile"
    )

    count = run(out_path, user_data_dir, args.max_idle)

    print(f"\nWrote {count} bookmarks to {out_path}")
    print(f"Next: python -m xbookmarks ingest {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
