"""
Pinecone adapter for vector store operations.
Used for production/cloud deployment.
"""
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone

from .vector_store_interface import VectorStore, VectorSearchResult

logger = logging.getLogger(__name__)


class PineconeVectorStore(VectorStore):
    """Pinecone implementation of VectorStore interface."""

    def __init__(
        self,
        api_key: str,
        index_name: str = "yalom-transcripts",
        environment: str = "gcp-starter"
    ):
        """
        Initialize Pinecone client.

        Args:
            api_key: Pinecone API key
            index_name: Index name
            environment: Pinecone environment (default: gcp-starter for free tier)
        """
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment

        self.client = Pinecone(api_key=api_key)
        self.index = self.client.Index(index_name)

        logger.info(f"Connected to Pinecone: {index_name}")

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """Insert or update vectors."""
        # Pinecone format: (id, values, metadata)
        formatted_vectors = [
            (v['id'], v['values'], v.get('metadata', {}))
            for v in vectors
        ]

        # Batch upsert
        total_upserted = 0
        for i in range(0, len(formatted_vectors), batch_size):
            batch = formatted_vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            total_upserted += len(batch)

        logger.debug(f"Upserted {total_upserted} vectors to Pinecone")
        return total_upserted

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )

        return [
            VectorSearchResult(
                id=match['id'],
                score=match['score'],
                metadata=match.get('metadata', {})
            )
            for match in results['matches']
        ]

    def delete(self, ids: List[str]) -> int:
        """Delete vectors by IDs."""
        self.index.delete(ids=ids)
        return len(ids)

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        stats = self.index.describe_index_stats()
        return {
            'provider': 'pinecone',
            'index': self.index_name,
            'vectors_count': stats.get('total_vector_count', 0),
            'dimension': stats.get('dimension', 0),
            'namespaces': stats.get('namespaces', {})
        }

    def collection_exists(self) -> bool:
        """Check if index exists."""
        try:
            indexes = self.client.list_indexes()
            return self.index_name in [idx['name'] for idx in indexes]
        except Exception:
            return False

    def create_collection(self, dimension: int) -> None:
        """Create index if it doesn't exist."""
        if not self.collection_exists():
            self.client.create_index(
                name=self.index_name,
                dimension=dimension,
                metric='cosine',
                spec={
                    'serverless': {
                        'cloud': 'aws',
                        'region': 'us-east-1'
                    }
                }
            )
            logger.info(f"Created Pinecone index: {self.index_name}")
        else:
            logger.debug(f"Index already exists: {self.index_name}")

    @property
    def provider_name(self) -> str:
        return "pinecone"
