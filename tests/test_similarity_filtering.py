from dataclasses import dataclass

from src.rag.pipeline import RAGPipeline


@dataclass
class _Doc:
    page_content: str
    metadata: dict


class _FakeVectorStore:
    def __init__(self, docs_with_scores):
        self._docs_with_scores = docs_with_scores

    def similarity_search_with_score(self, _query, k):
        return self._docs_with_scores[:k]


class _FakeQueryRewriter:
    def rewrite(self, question):
        return {
            "queries": [question],
            "language": "en",
            "original_question": question,
            "english_question": question,
        }

    def translate_answer(self, text, _lang, _name):
        return text


class _FakePrompt:
    def format_messages(self, context, question):
        return [{"role": "system", "content": context}, {"role": "user", "content": question}]


class _FakeLLM:
    def invoke(self, _messages):
        class _Resp:
            content = "unit-test-answer"

        return _Resp()


def _make_pipeline(docs_with_scores, top_k=2, threshold=0.5):
    pipeline = RAGPipeline.__new__(RAGPipeline)
    pipeline.top_k = top_k
    pipeline.retrieval_multiplier = 3
    pipeline.similarity_threshold = threshold
    pipeline.verbose_sources = 0
    pipeline.vector_store = _FakeVectorStore(docs_with_scores)
    pipeline.query_rewriter = _FakeQueryRewriter()
    pipeline.prompt = _FakePrompt()
    pipeline.llm = _FakeLLM()
    pipeline.chat_history = []
    return pipeline


def test_similarity_filtering_applies_threshold():
    docs_with_scores = [
        (_Doc("A", {"title": "t1", "transcript_id": "1"}), 0.9),
        (_Doc("B", {"title": "t2", "transcript_id": "2"}), 0.4),
        (_Doc("C", {"title": "t3", "transcript_id": "3"}), 0.7),
    ]
    pipeline = _make_pipeline(docs_with_scores, top_k=2, threshold=0.6)

    result = pipeline.ask("test question")

    assert len(result["sources"]) == 2
    assert result["sources"][0]["title"] in {"t1", "t3"}


def test_similarity_filtering_falls_back_when_no_docs_pass():
    docs_with_scores = [
        (_Doc("A", {"title": "t1", "transcript_id": "1"}), 0.2),
        (_Doc("B", {"title": "t2", "transcript_id": "2"}), 0.1),
    ]
    pipeline = _make_pipeline(docs_with_scores, top_k=2, threshold=0.6)

    result = pipeline.ask("test question")

    assert len(result["sources"]) == 2
