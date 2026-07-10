import json
from pathlib import Path

from xbookmarks import cli
from xbookmarks.store import Store

FIXTURE = Path(__file__).parent / "fixtures" / "sample_bookmarks.json"


def fake_ai(b):
    return {"summary": f"Summary of {b.id}.", "topic": "misc", "tags": [f"tag{b.id[-1]}"]}


def fake_fetch(id_):
    return {"text": f"text {id_}", "author_handle": "a", "author_name": "A",
            "created_at": "2024", "media": []}


def test_build_meets_success_metric(tmp_path):
    data = tmp_path / "data" / "bookmarks.ndjson"
    site = tmp_path / "site"
    catalog = tmp_path / "catalog"

    assert cli.cmd_ingest(FIXTURE, data) == 5

    stats = cli.cmd_build(data, site, catalog, fetcher=fake_fetch, ai=fake_ai, now=lambda: "NOW")
    assert stats == {"enriched": 5, "errors": 0}

    # 1) exactly 5 records, each with a non-empty summary and >=1 tag
    recs = Store.load(data).all()
    assert len(recs) == 5
    assert all(r.summary and len(r.tags) >= 1 for r in recs)

    # 2) the site contains all 5 tweet ids
    html = (site / "index.html").read_text()
    assert all(r.id in html for r in recs)
    assert (catalog / "index.md").exists()

    # 3) a second build changes 0 lines in the NDJSON store (idempotent)
    before = data.read_text()
    cli.cmd_build(data, site, catalog, fetcher=fake_fetch, ai=fake_ai, now=lambda: "NOW")
    assert data.read_text() == before


def test_build_with_keyword_enricher_is_offline(tmp_path):
    # extension-shape capture + keyword enricher -> no network, no API key needed
    src = tmp_path / "cap.json"
    src.write_text(
        json.dumps(
            [
                {
                    "id": "9001",
                    "url": "https://x.com/u/status/9001",
                    "text": "thread on LLM agents and prompt engineering",
                    "author": {"handle": "u", "name": "U"},
                    "metrics": {"likes": 42, "views": 900},
                    "links": [],
                }
            ]
        )
    )
    data = tmp_path / "data" / "bookmarks.ndjson"
    site = tmp_path / "site"
    catalog = tmp_path / "catalog"

    assert cli.cmd_ingest(src, data) == 1
    stats = cli.cmd_build(data, site, catalog, enricher="keyword", now=lambda: "NOW")
    assert stats == {"enriched": 1, "errors": 0}

    rec = Store.load(data).all()[0]
    assert rec.enriched and rec.topic == "IA & Machine Learning"
    assert rec.metrics["likes"] == 42

    html = (site / "index.html").read_text()
    assert "Most liked" in html  # popularity sort control shipped


def test_main_ingest_and_render_offline(tmp_path):
    data = tmp_path / "bookmarks.ndjson"
    site = tmp_path / "site"
    catalog = tmp_path / "catalog"

    cli.main(["--data", str(data), "ingest", str(FIXTURE)])
    assert len(Store.load(data).all()) == 5

    cli.main(["--data", str(data), "render", "--site", str(site), "--catalog", str(catalog)])
    assert (site / "index.html").exists()
    assert (catalog / "index.md").exists()
