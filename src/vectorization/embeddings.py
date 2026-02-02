"""
Embedding generation for text chunks.

Supports multiple embedding providers:
- OpenAI (text-embedding-3-small, text-embedding-3-large)
- Sentence Transformers (open-source models)
- Cohere
- HuggingFace
"""
import logging
from typing import List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (list of floats)
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the embedding model."""
        pass


class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider using sentence-transformers (local, open-source)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence-transformers provider.

        Args:
            model_name: Name of the sentence-transformers model
                       Popular choices:
                       - all-MiniLM-L6-v2 (384 dim, fast, good quality)
                       - all-mpnet-base-v2 (768 dim, slower, better quality)
                       - multi-qa-mpnet-base-dot-v1 (768 dim, optimized for QA)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self._model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

        logger.info(f"Loaded sentence-transformers model: {model_name} (dim={self._dimension})")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers."""
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


class OpenAIProvider(EmbeddingProvider):
    """Embedding provider using OpenAI API."""

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI embedding provider.

        Args:
            model_name: OpenAI model name
                       - text-embedding-3-small (1536 dim, $0.02/1M tokens)
                       - text-embedding-3-large (3072 dim, $0.13/1M tokens)
                       - text-embedding-ada-002 (1536 dim, legacy)
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai not installed. "
                "Install with: pip install openai"
            )

        import os
        self._model_name = model_name
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Set dimension based on model
        self._dimension = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }.get(model_name, 1536)

        logger.info(f"Initialized OpenAI embedding provider: {model_name} (dim={self._dimension})")

    def embed(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings using OpenAI API with batching."""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self._model_name
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            logger.debug(f"Embedded batch {i//batch_size + 1} ({len(batch)} texts)")

        return all_embeddings

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


# TODO: Add more providers
# - CohereProvider
# - HuggingFaceProvider
# - VoyageAIProvider


def get_embedding_provider(
    provider: str = "sentence-transformers",
    model_name: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """
    Factory function to get an embedding provider.

    Args:
        provider: Provider name ("sentence-transformers", "openai")
        model_name: Optional model name (uses defaults if not provided)
        **kwargs: Additional provider-specific arguments

    Returns:
        EmbeddingProvider instance
    """
    if provider == "sentence-transformers":
        model = model_name or "all-MiniLM-L6-v2"
        return SentenceTransformerProvider(model_name=model)

    elif provider == "openai":
        model = model_name or "text-embedding-3-small"
        return OpenAIProvider(model_name=model, **kwargs)

    else:
        raise ValueError(f"Unknown provider: {provider}")
