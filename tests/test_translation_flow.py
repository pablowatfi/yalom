from src.rag.query_rewriter import QueryRewriter


class _FailingLLM:
    def invoke(self, _messages):
        raise RuntimeError("LLM unavailable")


def test_translate_to_english_fallback_on_error(monkeypatch):
    rewriter = QueryRewriter(llm=_FailingLLM(), enabled=True)
    monkeypatch.setattr(rewriter, "_detect_language", lambda _text: "es")

    translated = rewriter._translate_to_english("¿Qué dice Huberman sobre el sueño?", "es")
    assert translated == "¿Qué dice Huberman sobre el sueño?"


def test_translate_answer_fallback_on_error():
    rewriter = QueryRewriter(llm=_FailingLLM(), enabled=True)
    translated = rewriter.translate_answer("English answer", "es", "Spanish")
    assert translated == "English answer"
