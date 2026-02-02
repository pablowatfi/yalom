"""
Factory for creating vector store instances.
Implements the Factory pattern for clean dependency injection.
"""
import os
import logging
from typing import Optional

from .vector_store_interface import VectorStore
from .qdrant_adapter import QdrantVectorStore
from .pinecone_adapter import PineconeVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory for creating vector store instances based on configuration."""

    @staticmethod
    def create(
        provider: Optional[str] = None,
        **kwargs
    ) -> VectorStore:
        """
        Create a vector store instance.

        Args:
            provider: 'qdrant' or 'pinecone' (defaults to VECTOR_STORE env var)
            **kwargs: Provider-specific configuration

        Returns:
            VectorStore instance

        Example:
            # From environment
            store = VectorStoreFactory.create()

            # Explicit Qdrant
            store = VectorStoreFactory.create('qdrant', url='http://localhost:6333')

            # Explicit Pinecone
            store = VectorStoreFactory.create('pinecone', api_key='your-key')
        """
        if provider is None:
            provider = os.getenv('VECTOR_STORE', 'qdrant').lower()

        if provider == 'qdrant':
            return VectorStoreFactory._create_qdrant(**kwargs)
        elif provider == 'pinecone':
            return VectorStoreFactory._create_pinecone(**kwargs)
        else:
            raise ValueError(
                f"Unsupported vector store provider: {provider}. "
                f"Use 'qdrant' or 'pinecone'"
            )

    @staticmethod
    def _create_qdrant(**kwargs) -> QdrantVectorStore:
        """Create Qdrant vector store."""
        url = kwargs.get('url') or os.getenv('QDRANT_URL', 'http://localhost:6333')
        collection_name = kwargs.get('collection_name') or os.getenv(
            'QDRANT_COLLECTION',
            'huberman_transcripts'
        )
        api_key = kwargs.get('api_key') or os.getenv('QDRANT_API_KEY')

        logger.info(f"Creating Qdrant vector store: {url}/{collection_name}")
        return QdrantVectorStore(
            url=url,
            collection_name=collection_name,
            api_key=api_key
        )

    @staticmethod
    def _create_pinecone(**kwargs) -> PineconeVectorStore:
        """Create Pinecone vector store."""
        api_key = kwargs.get('api_key') or os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError(
                "Pinecone requires api_key parameter or PINECONE_API_KEY environment variable"
            )

        index_name = kwargs.get('index_name') or os.getenv(
            'PINECONE_INDEX',
            'yalom-transcripts'
        )
        environment = kwargs.get('environment') or os.getenv(
            'PINECONE_ENVIRONMENT',
            'gcp-starter'
        )

        logger.info(f"Creating Pinecone vector store: {index_name}")
        return PineconeVectorStore(
            api_key=api_key,
            index_name=index_name,
            environment=environment
        )
