"""
Abstract interface for vector store operations.
Supports multiple backends: Qdrant (local), Pinecone (cloud).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Unified search result format across all vector stores."""
    id: str
    score: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'score': self.score,
            'metadata': self.metadata
        }


class VectorStore(ABC):
    """
    Abstract base class for vector store operations.

    Provides a unified interface for different vector database backends,
    following the Adapter pattern for clean architecture.
    """

    @abstractmethod
    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Insert or update vectors in the store.

        Args:
            vectors: List of dicts with 'id', 'values', 'metadata'
            batch_size: Number of vectors to upsert in one batch

        Returns:
            Number of vectors upserted
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of search results with scores and metadata
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """
        Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with stats (count, dimensions, etc.)
        """
        pass

    @abstractmethod
    def collection_exists(self) -> bool:
        """
        Check if collection/index exists.

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def create_collection(self, dimension: int) -> None:
        """
        Create collection/index if it doesn't exist.

        Args:
            dimension: Vector dimension size
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the vector store provider."""
        pass
