"""
Text chunking using LangChain's text splitters.

LangChain provides battle-tested, production-ready text splitting strategies.
"""
import logging
from typing import List, Optional, Dict

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def chunk_transcript(
    text: str,
    transcript_id: str,
    metadata: Optional[Dict] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    strategy: str = "recursive"
) -> List[Document]:
    """
    Chunk transcript text using LangChain text splitters.

    Args:
        text: Transcript text to chunk
        transcript_id: Unique transcript identifier
        metadata: Additional metadata to attach to chunks
        chunk_size: Target size for each chunk (in characters or tokens)
        chunk_overlap: Number of characters/tokens to overlap between chunks
        strategy: Chunking strategy to use:
            - "recursive": RecursiveCharacterTextSplitter (recommended)
            - "character": CharacterTextSplitter (simple splitting)
            - "token": TokenTextSplitter (splits by tokens)

    Returns:
        List of LangChain Document objects with text and metadata
    """
    # Prepare metadata
    chunk_metadata = metadata or {}
    chunk_metadata["transcript_id"] = transcript_id
    if strategy == "recursive":
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    elif strategy == "character":
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator="\n"
        )
    elif strategy == "token":
        text_splitter = TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

    # Split text and create documents
    chunks = text_splitter.create_documents(
        texts=[text],
        metadatas=[chunk_metadata]
    )

    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)

    logger.info(
        f"Chunked transcript {transcript_id} into {len(chunks)} chunks "
        f"using {strategy} strategy (size={chunk_size}, overlap={chunk_overlap})"
    )

    return chunks


def chunk_transcripts_batch(
    transcripts: List[Dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    strategy: str = "recursive"
) -> List[Document]:
    """
    Chunk multiple transcripts in batch.

    Args:
        transcripts: List of dicts with 'text', 'transcript_id', and optional 'metadata'
        chunk_size: Target size for each chunk
        chunk_overlap: Overlap between chunks
        strategy: Chunking strategy

    Returns:
        List of all chunks from all transcripts
    """
    all_chunks = []

    for transcript in transcripts:
        chunks = chunk_transcript(
            text=transcript["text"],
            transcript_id=transcript["transcript_id"],
            metadata=transcript.get("metadata"),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy
        )
        all_chunks.extend(chunks)

    logger.info(f"Chunked {len(transcripts)} transcripts into {len(all_chunks)} total chunks")
    return all_chunks


# Recommended chunking configurations for different use cases
CHUNKING_CONFIGS = {
    "qa": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "strategy": "recursive",
        "description": "Good for Q&A systems - balances context and granularity"
    },
    "search": {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "strategy": "recursive",
        "description": "Optimized for semantic search - shorter, focused chunks"
    },
    "summary": {
        "chunk_size": 2000,
        "chunk_overlap": 200,
        "strategy": "recursive",
        "description": "For summarization - larger context windows"
    },
    "fine_grained": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "strategy": "recursive",
        "description": "Very granular chunks for precise retrieval"
    }
}


def get_chunking_config(use_case: str) -> Dict:
    """
    Get recommended chunking configuration for a use case.

    Args:
        use_case: One of "qa", "search", "summary", "fine_grained"

    Returns:
        Configuration dict with chunk_size, chunk_overlap, strategy
    """
    if use_case not in CHUNKING_CONFIGS:
        raise ValueError(
            f"Unknown use case: {use_case}. "
            f"Available: {list(CHUNKING_CONFIGS.keys())}"
        )

    return CHUNKING_CONFIGS[use_case].copy()
