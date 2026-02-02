"""
Qdrant adapter for vector store operations.
Used for local development with Docker.
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from .vector_store_interface import VectorStore, VectorSearchResult

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    """Qdrant implementation of VectorStore interface."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "huberman_transcripts",
        api_key: Optional[str] = None
    ):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL
            collection_name: Collection name
            api_key: Optional API key for Qdrant Cloud
        """
        self.url = url
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key)
        logger.info(f"Connected to Qdrant: {url}/{collection_name}")

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """Insert or update vectors."""
        points = [
            PointStruct(
                id=v['id'],
                vector=v['values'],
                payload=v.get('metadata', {})
            )
            for v in vectors
        ]

        # Batch upsert
        total_upserted = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            total_upserted += len(batch)

        logger.debug(f"Upserted {total_upserted} vectors to Qdrant")
        return total_upserted

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filter_dict
        )

        return [
            VectorSearchResult(
                id=str(result.id),
                score=result.score,
                metadata=result.payload or {}
            )
            for result in results
        ]

    def delete(self, ids: List[str]) -> int:
        """Delete vectors by IDs."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )
        return len(ids)

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        info = self.client.get_collection(self.collection_name)
        return {
            'provider': 'qdrant',
            'collection': self.collection_name,
            'vectors_count': info.points_count,
            'status': info.status.value
        }

    def collection_exists(self) -> bool:
        """Check if collection exists."""
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def create_collection(self, dimension: int) -> None:
        """Create collection if it doesn't exist."""
        if not self.collection_exists():
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        else:
            logger.debug(f"Collection already exists: {self.collection_name}")

    @property
    def provider_name(self) -> str:
        return "qdrant"
