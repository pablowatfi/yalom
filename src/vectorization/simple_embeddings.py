"""
Simple embeddings wrapper using FastEmbed (ONNX runtime).
Keeps Lambda packages small (no torch) and runs locally for free.
"""
from typing import List
from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings


class SimpleSentenceTransformerEmbeddings(Embeddings):
    """
    Simple wrapper for sentence-transformers that matches LangChain's embeddings interface.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize the model.

        Args:
            model_name: HuggingFace model name
        """
        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text documents

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = list(self.model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text

        Returns:
            Embedding as list of floats
        """
        embedding = next(self.model.embed([text]))
        return embedding.tolist()
