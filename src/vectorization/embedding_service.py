"""
Compatibility re-export for shared embedding helpers.
"""
from ..embedding_service import embed_documents, embed_query

__all__ = ["embed_documents", "embed_query"]
