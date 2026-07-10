from xbookmarks.enrich.keyword import categorize, keyword_enrich
from xbookmarks.models import Bookmark


def test_categorize_by_keyword():
    b = Bookmark(id="1", url="u", text="A thread about LLM agents and prompt engineering")
    tags = categorize(b)
    assert "IA & Machine Learning" in tags


def test_categorize_by_domain_scores_higher():
    b = Bookmark(id="1", url="u", text="great read", links=["https://github.com/a/b"])
    assert categorize(b)[0] == "Programación & Dev"


def test_categorize_journalism_domain():
    b = Bookmark(id="1", url="u", text="nota", links=["https://www.elconfidencial.com/x"])
    assert "Periodismo & Medios" in categorize(b)


def test_keyword_enrich_shape_matches_ai():
    out = keyword_enrich(Bookmark(id="1", url="u", text="fútbol y la liga de campeones"))
    assert set(out) == {"summary", "topic", "tags"}
    assert out["summary"] == ""  # keyword mode adds no summary
    assert out["topic"] == "Deportes"


def test_keyword_enrich_uncategorized():
    out = keyword_enrich(Bookmark(id="1", url="u", text="zzz qwerty"))
    assert out["tags"] == ["Sin categoría"]


def test_anchored_no_substring_false_positives():
    # Regression: bare words must not match inside longer words.
    cases = {
        "Facebook just announced a new ad platform": "Cultura & Entretenimiento",  # book
        "The Mongol empire expanded rapidly": "Deportes",  # gol
        "please continue reading the whole issue": "Política & Actualidad",  # ue
        "this offer seems totally legit": "Programación & Dev",  # git
    }
    for text, wrong in cases.items():
        assert wrong not in categorize(Bookmark(id="1", url="u", text=text)), text


def test_anchored_still_matches_whole_words():
    dev = categorize(Bookmark(id="1", url="u", text="learning rust and go"))
    assert "Programación & Dev" in dev
    assert "Deportes" in categorize(Bookmark(id="1", url="u", text="qué gol de locura"))
