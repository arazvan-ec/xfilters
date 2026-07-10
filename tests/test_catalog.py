from xbookmarks.models import Bookmark
from xbookmarks.render.catalog import render_catalog


def test_catalog_groups_by_tag(tmp_path):
    bms = [
        Bookmark(id="1", url="https://x.com/u/status/1", summary="First", tags=["ai"]),
        Bookmark(id="2", url="https://x.com/u/status/2", summary="Second", tags=["ai", "python"]),
        Bookmark(id="3", url="https://x.com/u/status/3"),  # untagged
    ]
    md = render_catalog(bms, tmp_path / "catalog").read_text()
    assert "## ai" in md and "## python" in md and "## untagged" in md
    assert "`#1`" in md
    assert "https://x.com/u/status/2" in md
    assert md.count("`#2`") == 2  # under both ai and python


def test_catalog_empty(tmp_path):
    p = render_catalog([], tmp_path / "catalog")
    assert p.exists()
    assert "0 bookmarks" in p.read_text()
