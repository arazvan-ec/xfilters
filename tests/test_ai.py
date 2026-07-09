from types import SimpleNamespace

from xbookmarks.enrich.ai import _parse, generate_enrichment
from xbookmarks.models import Bookmark


class FakeMessages:
    def __init__(self, text):
        self._text = text
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text=self._text)])


class FakeClient:
    def __init__(self, text):
        self.messages = FakeMessages(text)


def test_generate_enrichment_parses_and_passes_model():
    c = FakeClient('{"summary":"A tweet about AI.","topic":"AI","tags":["ai","llm"]}')
    out = generate_enrichment(Bookmark(id="1", url="u", text="x"), client=c, model="m")
    assert out["summary"].startswith("A tweet")
    assert out["topic"] == "AI"
    assert out["tags"] == ["ai", "llm"]
    assert c.messages.kwargs["model"] == "m"


def test_parse_tolerates_code_fence_and_lowercases_tags():
    out = _parse('```json\n{"summary":"s","topic":"t","tags":["AI","LLM"]}\n```')
    assert out["tags"] == ["ai", "llm"]


def test_parse_missing_fields_default_empty():
    out = _parse('{"summary":"s"}')
    assert out["topic"] == ""
    assert out["tags"] == []
