import os

import pytest

import src.vectorization.factory as factory_module
from src.vectorization.factory import VectorStoreFactory


class _FakeQdrantStore:
    def __init__(self, url, collection_name, api_key=None):
        self.url = url
        self.collection_name = collection_name
        self.api_key = api_key


class _FakePineconeStore:
    def __init__(self, api_key, index_name, environment):
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment


def test_factory_creates_qdrant_from_env(monkeypatch):
    monkeypatch.setattr(factory_module, "QdrantVectorStore", _FakeQdrantStore)
    os.environ["VECTOR_STORE"] = "qdrant"
    os.environ["QDRANT_URL"] = "http://localhost:6333"
    os.environ["QDRANT_COLLECTION"] = "huberman_transcripts"

    store = VectorStoreFactory.create()
    assert isinstance(store, _FakeQdrantStore)
    assert store.url == "http://localhost:6333"
    assert store.collection_name == "huberman_transcripts"


def test_factory_creates_pinecone_with_explicit_args(monkeypatch):
    monkeypatch.setattr(factory_module, "PineconeVectorStore", _FakePineconeStore)

    store = VectorStoreFactory.create(
        "pinecone",
        api_key="key",
        index_name="index",
        environment="env",
    )

    assert isinstance(store, _FakePineconeStore)
    assert store.api_key == "key"
    assert store.index_name == "index"
    assert store.environment == "env"


def test_factory_invalid_provider_raises():
    with pytest.raises(ValueError):
        VectorStoreFactory.create("weaviate")
