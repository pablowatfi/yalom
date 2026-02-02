"""
Simple embeddings wrapper using OpenAI embeddings.
Shared implementation lives in src/embedding_service.py.
"""
from typing import List
from langchain_core.embeddings import Embeddings

from src.embedding_service import embed_documents as openai_embed_documents
from src.embedding_service import embed_query as openai_embed_query


class SimpleSentenceTransformerEmbeddings(Embeddings):
    """
    Simple wrapper for sentence-transformers that matches LangChain's embeddings interface.
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize the model.

        Args:
            model_name: OpenAI embedding model name
        """
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text documents

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        return openai_embed_documents(texts, model_name=self.model_name)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text

        Returns:
            Embedding as list of floats
        """
        return openai_embed_query(text, model_name=self.model_name)
