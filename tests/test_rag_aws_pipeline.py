from types import SimpleNamespace

from src.rag.aws_pipeline import PineconeRAG


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, **kwargs):
        return SimpleNamespace(choices=[_FakeChoice(self._content)])


class _FakeGroqClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(completions=_FakeCompletions(content))


def _build_pipeline(index_results, llm_content="final answer"):
    pipeline = PineconeRAG.__new__(PineconeRAG)
    pipeline.model = "test-model"
    pipeline.groq_client = _FakeGroqClient(llm_content)
    pipeline.index = SimpleNamespace(query=lambda **kwargs: index_results)
    return pipeline


def test_query_returns_empty_sources_when_no_matches(monkeypatch):
    pipeline = _build_pipeline({"matches": []})
    monkeypatch.setattr("src.rag.aws_pipeline.embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr("src.rag.aws_pipeline.RAG_QUERY_REWRITING", False)

    result = pipeline.query("question")

    assert result == {"answer": "No relevant information found.", "sources": []}


def test_query_applies_similarity_filter_and_history_limit(monkeypatch):
    index_results = {
        "matches": [
            {"id": "a", "score": 0.9, "metadata": {"text": "alpha", "title": "A"}},
            {"id": "b", "score": 0.2, "metadata": {"text": "beta", "title": "B"}},
        ]
    }
    pipeline = _build_pipeline(index_results)
    monkeypatch.setattr("src.rag.aws_pipeline.embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr("src.rag.aws_pipeline.RAG_QUERY_REWRITING", False)
    monkeypatch.setattr("src.rag.aws_pipeline.RAG_SIMILARITY_THRESHOLD", 0.5)
    monkeypatch.setattr("src.rag.aws_pipeline.RAG_HISTORY_LIMIT", 1)
    monkeypatch.setattr("src.rag.aws_pipeline.get_active_prompt", lambda: {"system": "ctx={context}", "human": "{question}"})

    history = [{"role": "user", "content": "old"}, {"role": "assistant", "content": "latest"}]
    result = pipeline.query("question", history=history, top_k=2)

    assert result["answer"] == "final answer"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "A"


def test_query_returns_debug_payload(monkeypatch):
    index_results = {"matches": [{"id": "a", "score": 0.9, "metadata": {"text": "alpha", "title": "A"}}]}
    pipeline = _build_pipeline(index_results)
    monkeypatch.setattr("src.rag.aws_pipeline.embed_query", lambda q: [0.1, 0.2])
    monkeypatch.setattr("src.rag.aws_pipeline.RAG_QUERY_REWRITING", False)
    monkeypatch.setattr("src.rag.aws_pipeline.get_active_prompt", lambda: {"system": "ctx={context}", "human": "{question}"})

    result = pipeline.query("question", return_debug=True)

    assert "debug" in result
    assert result["debug"]["question"] == "question"
    assert len(result["debug"]["similarity_chunks"]) == 1


def test_rerank_matches_falls_back_on_model_error():
    matches = [{"id": "a", "score": 0.9, "metadata": {"text": "alpha"}}]
    pipeline = PineconeRAG.__new__(PineconeRAG)
    pipeline.model = "test-model"
    pipeline.groq_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("failed")))
        )
    )

    reranked = pipeline._rerank_matches("q", matches)

    assert reranked == matches
