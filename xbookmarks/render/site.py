"""Render a self-contained, searchable static site (site/index.html).

Data is embedded as JSON in the page; search and tag filtering run client-side
with vanilla JS. No external requests, so it works offline and on GitHub Pages.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Bookmark

# Fields safe to publish in the static site (nothing internal like enrich_error).
_PUBLIC_FIELDS = (
    "id", "url", "text", "summary", "topic", "tags",
    "author_handle", "author_name", "created_at", "metrics",
)


def _safe_url(u: str) -> str:
    """Allow only http(s) URLs into the page; neutralize anything else."""
    return u if (u or "").lower().startswith(("http://", "https://")) else "#"


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bookmarks</title>
<style>
:root { color-scheme: light dark; --fg:#111; --muted:#666; --bg:#fff; --card:#f6f6f7; --accent:#1d9bf0; }
@media (prefers-color-scheme: dark) { :root { --fg:#e7e9ea; --muted:#8b98a5; --bg:#15181c; --card:#1f2328; } }
* { box-sizing: border-box; }
body { margin:0; font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; color:var(--fg); background:var(--bg); }
header { padding:24px 20px 8px; max-width:900px; margin:0 auto; }
h1 { margin:0 0 4px; font-size:22px; }
.count { color:var(--muted); font-size:14px; }
.controls { max-width:900px; margin:0 auto; padding:8px 20px; position:sticky; top:0; background:var(--bg); }
#q { width:100%; padding:10px 12px; font-size:15px; border:1px solid var(--muted); border-radius:8px; background:transparent; color:var(--fg); }
#sort { margin-top:8px; padding:6px 10px; font-size:13px; border:1px solid var(--muted); border-radius:8px; background:transparent; color:var(--fg); }
.card .metrics { color:var(--muted); font-size:12px; margin-top:6px; }
.tags { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.tag { cursor:pointer; padding:3px 10px; border-radius:999px; border:1px solid var(--muted); font-size:13px; color:var(--muted); background:transparent; }
.tag.active { background:var(--accent); border-color:var(--accent); color:#fff; }
main { max-width:900px; margin:0 auto; padding:8px 20px 60px; }
.card { background:var(--card); border-radius:12px; padding:14px 16px; margin:10px 0; }
.card .meta { color:var(--muted); font-size:13px; margin-bottom:4px; }
.card .summary { font-weight:600; margin:2px 0 6px; }
.card .text { white-space:pre-wrap; }
.card .chips { margin-top:8px; display:flex; flex-wrap:wrap; gap:6px; }
.chip { font-size:12px; color:var(--accent); }
a { color:var(--accent); text-decoration:none; }
.empty { color:var(--muted); text-align:center; padding:40px 0; }
</style>
</head>
<body>
<header>
  <h1>Bookmarks</h1>
  <div class="count"><span id="shown">__COUNT__</span> / __COUNT__ bookmarks</div>
</header>
<div class="controls">
  <input id="q" type="search" placeholder="Search text, author, tags…" autocomplete="off">
  <select id="sort">
    <option value="recent">Most recent</option>
    <option value="likes">Most liked</option>
    <option value="views">Most viewed</option>
  </select>
  <div class="tags" id="tags"></div>
</div>
<main id="list"></main>
<script type="application/json" id="bookmarks-data">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("bookmarks-data").textContent);
// Precompute the search haystack once so filtering doesn't rebuild it per keystroke.
DATA.forEach(b => { b._hay = [b.text, b.summary, b.topic, b.author_handle, b.author_name, (b.tags || []).join(" ")].join(" ").toLowerCase(); });
const listEl = document.getElementById("list");
const tagsEl = document.getElementById("tags");
const qEl = document.getElementById("q");
const sortEl = document.getElementById("sort");
const shownEl = document.getElementById("shown");
let activeTag = null;

function sortRows(rows) {
  const key = sortEl.value;
  const metric = (b, k) => (b.metrics && b.metrics[k]) || 0;
  const by = {
    likes: (a, b) => metric(b, "likes") - metric(a, "likes"),
    views: (a, b) => metric(b, "views") - metric(a, "views"),
    recent: (a, b) => (b.created_at || "").localeCompare(a.created_at || ""),
  }[key] || (() => 0);
  return rows.slice().sort(by);
}

const allTags = [...new Set(DATA.flatMap(b => b.tags || []))].sort();
for (const t of allTags) {
  const el = document.createElement("span");
  el.className = "tag"; el.textContent = t;
  el.onclick = () => { activeTag = (activeTag === t) ? null : t; render(); };
  el.dataset.tag = t;
  tagsEl.appendChild(el);
}

const _ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => _ESC[c]); }
function escAttr(s) { return esc(s); }
function safeUrl(u) { return /^https?:\\/\\//i.test(u || "") ? u : "#"; }

function matches(b, q) {
  if (activeTag && !(b.tags || []).includes(activeTag)) return false;
  if (!q) return true;
  return q.split(/\\s+/).every(w => b._hay.includes(w));
}

function render() {
  const q = qEl.value.trim().toLowerCase();
  const rows = sortRows(DATA.filter(b => matches(b, q)));
  shownEl.textContent = rows.length;
  for (const el of tagsEl.children) el.classList.toggle("active", el.dataset.tag === activeTag);
  listEl.innerHTML = rows.length ? rows.map(card).join("") : '<div class="empty">No matches.</div>';
}

function fmt(n) { return n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n); }

function metricsLine(m) {
  if (!m) return "";
  const parts = [];
  if (m.likes) parts.push("\\u2665 " + esc(fmt(m.likes)));
  if (m.views) parts.push("\\u25b6 " + esc(fmt(m.views)));
  if (m.bookmarks) parts.push("\\u2302 " + esc(fmt(m.bookmarks)));
  return parts.length ? '<div class="metrics">' + parts.join(" \\u00b7 ") + '</div>' : "";
}

function card(b) {
  const author = b.author_handle ? '@' + esc(b.author_handle) : '';
  const chips = (b.tags || []).map(t => '<span class="chip">#' + esc(t) + '</span>').join(" ");
  return '<article class="card">'
    + '<div class="meta">' + author + (b.topic ? ' \\u00b7 ' + esc(b.topic) : '') + '</div>'
    + (b.summary ? '<div class="summary">' + esc(b.summary) + '</div>' : '')
    + '<div class="text">' + esc(b.text) + '</div>'
    + metricsLine(b.metrics)
    + '<div class="chips">' + chips + ' <a href="' + escAttr(safeUrl(b.url)) + '" target="_blank" rel="noopener">open \\u2197</a></div>'
    + '</article>';
}

let _debounce;
qEl.addEventListener("input", () => { clearTimeout(_debounce); _debounce = setTimeout(render, 150); });
sortEl.addEventListener("change", render);
render();
</script>
</body>
</html>
"""


def render_site(bookmarks: list[Bookmark], out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = []
    for b in sorted(bookmarks, key=lambda x: x.id):
        rec = {k: getattr(b, k) for k in _PUBLIC_FIELDS}
        rec["url"] = _safe_url(rec["url"])
        data.append(rec)
    # Escape "<" so an embedded "</script>" in tweet text can't close our block.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    html = _TEMPLATE.replace("__DATA__", payload).replace("__COUNT__", str(len(data)))

    path = out_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path
