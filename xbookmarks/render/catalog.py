"""Render a Markdown catalog grouped by tag (a git-native, browsable view)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..models import Bookmark


def render_catalog(bookmarks: list[Bookmark], out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    by_tag: dict[str, list[Bookmark]] = defaultdict(list)
    for b in bookmarks:
        for tag in b.tags or ["untagged"]:
            by_tag[tag].append(b)

    lines = ["# Bookmarks catalog", "", f"{len(bookmarks)} bookmarks."]
    for tag in sorted(by_tag):
        lines += ["", f"## {tag}", ""]
        for b in sorted(by_tag[tag], key=lambda x: x.id):
            title = (b.summary or b.text or b.url).replace("\n", " ").strip()
            author = f"@{b.author_handle} — " if b.author_handle else ""
            lines.append(f"- {author}[{title}]({b.url}) `#{b.id}`")

    path = out_dir / "index.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
