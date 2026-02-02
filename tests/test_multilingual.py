from src.rag.query_rewriter import QueryRewriter


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    def invoke(self, _messages):
        return _FakeResponse(next(self._responses))


def test_translate_answer_passthrough_for_english():
    llm = _FakeLLM(["should not be used"])
    rewriter = QueryRewriter(llm=llm, enabled=True)

    assert rewriter.translate_answer("hello", "en", "English") == "hello"


def test_translate_answer_uses_llm_for_non_english():
    llm = _FakeLLM(["Respuesta en Español"])
    rewriter = QueryRewriter(llm=llm, enabled=True)

    translated = rewriter.translate_answer("English answer", "es", "Spanish")
    assert translated == "Respuesta en Español"


def test_rewrite_translates_then_rewrites(monkeypatch):
    llm = _FakeLLM([
        "sleep optimization protocols",  # translation to English
        "1. sleep hygiene recommendations\n2. circadian rhythm strategies",  # rewrite
    ])
    rewriter = QueryRewriter(llm=llm, enabled=True)

    monkeypatch.setattr(rewriter, "_detect_language", lambda _text: "es")

    result = rewriter.rewrite("¿Qué dice Huberman sobre el sueño?")

    assert result["language"] == "es"
    assert result["english_question"] == "sleep optimization protocols"
    assert result["queries"][0] == "sleep optimization protocols"
    assert len(result["queries"]) <= 3
