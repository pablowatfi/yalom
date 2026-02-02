"""
Vectorization module - Convert transcripts to embeddings and manage vector database.
"""

__all__ = [
    "chunk_transcript",
    "chunk_transcripts_batch",
    "get_chunking_config",
    "VectorStoreManager",
    "VectorizationPipeline",
]


def __getattr__(name):
    if name in {"chunk_transcript", "chunk_transcripts_batch", "get_chunking_config"}:
        from .chunking import chunk_transcript, chunk_transcripts_batch, get_chunking_config
        return {
            "chunk_transcript": chunk_transcript,
            "chunk_transcripts_batch": chunk_transcripts_batch,
            "get_chunking_config": get_chunking_config,
        }[name]
    if name == "VectorStoreManager":
        from .vector_store import VectorStoreManager
        return VectorStoreManager
    if name == "VectorizationPipeline":
        from .pipeline import VectorizationPipeline
        return VectorizationPipeline
    raise AttributeError(f"module 'src.vectorization' has no attribute {name}")
