import importlib
import sys
import types


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


class _FakeChatPromptTemplate:
    @staticmethod
    def from_messages(_messages):
        return _FakeChatPromptTemplate()

    def format_messages(self, **kwargs):
        return [{"role": "system", "content": kwargs.get("context", "")}, {"role": "user", "content": kwargs.get("question", "")}]


def _import_pipeline_with_stubs():
    fake_prompts = types.ModuleType("langchain_core.prompts")
    fake_prompts.ChatPromptTemplate = _FakeChatPromptTemplate
    sys.modules["langchain_core.prompts"] = fake_prompts

    fake_messages = types.ModuleType("langchain_core.messages")
    fake_messages.HumanMessage = type("HumanMessage", (), {"__init__": lambda self, content: setattr(self, "content", content)})
    fake_messages.AIMessage = type("AIMessage", (), {"__init__": lambda self, content: setattr(self, "content", content)})
    sys.modules["langchain_core.messages"] = fake_messages

    fake_openai = types.ModuleType("langchain_openai")
    fake_openai.ChatOpenAI = type("ChatOpenAI", (), {"__init__": lambda self, **kwargs: None})
    sys.modules["langchain_openai"] = fake_openai

    fake_ollama = types.ModuleType("langchain_ollama")
    fake_ollama.ChatOllama = type("ChatOllama", (), {"__init__": lambda self, **kwargs: None})
    sys.modules["langchain_ollama"] = fake_ollama

    fake_groq = types.ModuleType("langchain_groq")
    fake_groq.ChatGroq = _FakeChatGroq
    sys.modules["langchain_groq"] = fake_groq

    fake_qdrant = types.ModuleType("langchain_qdrant")
    fake_qdrant.QdrantVectorStore = _FakeVectorStore
    sys.modules["langchain_qdrant"] = fake_qdrant

    fake_qdrant_client = types.ModuleType("qdrant_client")
    fake_qdrant_client.QdrantClient = _FakeQdrantClient
    sys.modules["qdrant_client"] = fake_qdrant_client

    fake_embeddings_module = types.ModuleType("src.vectorization.simple_embeddings")
    fake_embeddings_module.SimpleSentenceTransformerEmbeddings = _FakeEmbeddings
    sys.modules["src.vectorization.simple_embeddings"] = fake_embeddings_module

    fake_query_rewriter_module = types.ModuleType("src.rag.query_rewriter")
    fake_query_rewriter_module.QueryRewriter = type(
        "QueryRewriter",
        (),
        {"__init__": lambda self, llm, enabled: None, "rewrite": lambda self, q: {"queries": [q], "language": "en", "english_question": q, "original_question": q}},
    )
    sys.modules["src.rag.query_rewriter"] = fake_query_rewriter_module

    module = importlib.import_module("src.rag.pipeline")
    return importlib.reload(module)


def test_groq_initializes_with_api_key(monkeypatch):
    pipeline_module = _import_pipeline_with_stubs()
    monkeypatch.setattr(pipeline_module, "ChatGroq", _FakeChatGroq)

    pipeline = pipeline_module.RAGPipeline(
        llm_provider="groq",
        api_key="test-key",
        model_name=None,
        top_k=1,
        query_rewriting=False,
    )

    assert pipeline.llm_provider == "groq"
    assert pipeline.llm.api_key == "test-key"
    assert pipeline.model_name == "llama-3.3-70b-versatile"
