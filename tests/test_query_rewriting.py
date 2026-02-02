from src.rag.query_rewriter import QueryRewriter


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    def invoke(self, _messages):
        return _FakeResponse(next(self._responses))


def test_parse_queries_extracts_numbered_lines():
    llm = _FakeLLM([""])
    rewriter = QueryRewriter(llm=llm, enabled=True)

    response = """
Search Queries:
1. focus and concentration enhancement protocols
2. dopamine and attention improvement strategies
3. cognitive performance and mental clarity techniques
"""

    queries = rewriter._parse_queries(response)
    assert len(queries) == 3
    assert queries[0].startswith("focus and concentration")


def test_rewrite_includes_english_question_first(monkeypatch):
    llm = _FakeLLM([
        "1. focus and concentration enhancement protocols\n2. attention improvement strategies"
    ])
    rewriter = QueryRewriter(llm=llm, enabled=True)

    monkeypatch.setattr(rewriter, "_detect_language", lambda _text: "en")
    monkeypatch.setattr(rewriter, "_translate_to_english", lambda text, _lang: text)

    result = rewriter.rewrite("focus and concentration")

    assert result["language"] == "en"
    assert result["queries"][0] == "focus and concentration"
    assert len(result["queries"]) <= 3


def test_rewrite_disabled_passthrough(monkeypatch):
    llm = _FakeLLM([""])
    rewriter = QueryRewriter(llm=llm, enabled=False)

    monkeypatch.setattr(rewriter, "_detect_language", lambda _text: "en")
    monkeypatch.setattr(rewriter, "_translate_to_english", lambda text, _lang: text)

    result = rewriter.rewrite("sleep tips")
    assert result["queries"] == ["sleep tips"]
