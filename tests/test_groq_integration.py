import src.rag.pipeline as pipeline_module
from src.rag.pipeline import RAGPipeline


class _FakeEmbeddings:
    pass


class _FakeQdrantClient:
    def __init__(self, *args, **kwargs):
        pass


class _FakeVectorStore:
    def __init__(self, *args, **kwargs):
        pass

    def as_retriever(self, *args, **kwargs):
        return object()


class _FakeChatGroq:
    def __init__(self, model, temperature, api_key):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key

    def invoke(self, _messages):
        class _Resp:
            content = "ok"

        return _Resp()


def test_groq_initializes_with_api_key(monkeypatch):
    monkeypatch.setattr(pipeline_module, "SimpleSentenceTransformerEmbeddings", _FakeEmbeddings)
    monkeypatch.setattr(pipeline_module, "QdrantClient", _FakeQdrantClient)
    monkeypatch.setattr(pipeline_module, "QdrantVectorStore", _FakeVectorStore)
    monkeypatch.setattr(pipeline_module, "ChatGroq", _FakeChatGroq)

    pipeline = RAGPipeline(
        llm_provider="groq",
        api_key="test-key",
        model_name=None,
        top_k=1,
        query_rewriting=False,
    )

    assert pipeline.llm_provider == "groq"
    assert pipeline.llm.api_key == "test-key"
    assert pipeline.model_name == "llama-3.3-70b-versatile"
