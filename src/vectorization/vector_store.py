"""
Vector store operations using Qdrant with LangChain integration.

Handles:
- Creating and managing Qdrant collections
- Storing document embeddings
- Semantic search and retrieval
"""
import logging
from typing import List, Optional, Dict, Any
import os

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Manage Qdrant vector store for transcript embeddings.
    """

    def __init__(
        self,
        collection_name: str = "huberman_transcripts",
        qdrant_url: str = "http://localhost:6333",
        embeddings = None,  # Accept custom embeddings provider
        embedding_dimension: int = None,
    ):
        """
        Initialize vector store manager.

        Args:
            collection_name: Name of the Qdrant collection
            qdrant_url: Qdrant server URL
            embeddings: LangChain embeddings provider (default: OpenAI)
            embedding_dimension: Dimension of embedding vectors
        """
        if embedding_dimension is None:
            embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url
        self.embedding_dimension = embedding_dimension

        # Initialize Qdrant client
        self.client = QdrantClient(url=qdrant_url)

        # Initialize embeddings - use OpenAI embeddings by default
        if embeddings is None:
            from .simple_embeddings import SimpleSentenceTransformerEmbeddings
            self.embeddings = SimpleSentenceTransformerEmbeddings(
                model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            )
            logger.info("Using OpenAI embeddings")
        else:
            self.embeddings = embeddings
            logger.info("Using custom embeddings provider")

        logger.info(
            f"Initialized VectorStoreManager: collection={collection_name}, "
            f"dimension={embedding_dimension}"
        )

    def create_collection(self, recreate: bool = False) -> None:
        """
        Create Qdrant collection if it doesn't exist.

        Args:
            recreate: If True, delete existing collection and recreate
        """
        if recreate:
            try:
                self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception as e:
                logger.debug(f"Collection doesn't exist or couldn't be deleted: {e}")

        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.info(f"Collection already exists or error: {e}")

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to vector store.

        Args:
            documents: List of LangChain Document objects
            batch_size: Number of documents to process at once

        Returns:
            List of document IDs
        """
        logger.info(f"Adding {len(documents)} documents to {self.collection_name}")

        # Create vector store
        QdrantVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            url=self.qdrant_url,
            collection_name=self.collection_name,
            force_recreate=False
        )

        logger.info(f"Successfully added {len(documents)} documents")
        return [doc.metadata.get("id", "") for doc in documents]

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """
        Semantic search for similar documents.

        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {"transcript_id": "episode-1"})

        Returns:
            List of matching Documents
        """
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

        if filter_dict:
            results = vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vector_store.similarity_search(query=query, k=k)

        logger.info(f"Search query: '{query[:50]}...' returned {len(results)} results")
        return results

    def search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[tuple[Document, float]]:
        """
        Semantic search with relevance scores.

        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of (Document, score) tuples
        """
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

        if filter_dict:
            results = vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
        else:
            results = vector_store.similarity_search_with_score(query=query, k=k)

        logger.info(
            f"Search with scores: {query[:50]}... returned {len(results)} results"
        )
        return results

    def delete_by_transcript_id(self, transcript_id: str) -> None:
        """
        Delete all chunks for a specific transcript.

        Args:
            transcript_id: Transcript identifier
        """
        # Qdrant filtering to delete by metadata
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.transcript_id",
                        match=MatchValue(value=transcript_id)
                    )
                ]
            )
        )
        logger.info(f"Deleted all chunks for transcript: {transcript_id}")

    def transcript_exists(self, transcript_id: int) -> bool:
        """
        Check if a transcript already has vectors in the collection.

        Args:
            transcript_id: Database transcript ID

        Returns:
            True if transcript exists, False otherwise
        """
        try:
            # Search for any point with this transcript_id
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.transcript_id",
                            match=MatchValue(value=transcript_id)
                        )
                    ]
                ),
                limit=1
            )
            # results is a tuple: (points, next_page_offset)
            return len(results[0]) > 0
        except Exception as e:
            logger.debug(f"Error checking transcript existence: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count if hasattr(info, 'vectors_count') else info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def clear_collection(self) -> None:
        """
        Delete all documents from the collection.
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.create_collection()
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")

