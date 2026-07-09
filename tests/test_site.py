import json
import re

from xbookmarks.models import Bookmark
from xbookmarks.render.site import render_site


def _extract_data(html):
    m = re.search(r'id="bookmarks-data"[^>]*>(.*?)</script>', html, re.S)
    assert m, "embedded data block not found"
    return json.loads(m.group(1).replace("\\u003c", "<"))


def test_site_embeds_all_bookmarks(tmp_path):
    bms = [
        Bookmark(id="1", url="https://x.com/u/status/1", summary="s1", tags=["ai"]),
        Bookmark(id="2", url="https://x.com/u/status/2", summary="s2", tags=["python"]),
    ]
    html = render_site(bms, tmp_path / "site").read_text()
    assert "https://x.com/u/status/1" in html
    data = _extract_data(html)
    assert {d["id"] for d in data} == {"1", "2"}


def test_site_escapes_script_close(tmp_path):
    bms = [Bookmark(id="1", url="u", text="</script><b>pwn")]
    html = render_site(bms, tmp_path / "site").read_text()
    assert "</script><b>pwn" not in html  # the injected close tag is escaped
    # but the data still round-trips
    data = _extract_data(html)
    assert data[0]["text"] == "</script><b>pwn"
