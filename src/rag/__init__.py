"""
RAG (Retrieval-Augmented Generation) module for question answering.

This module handles:
- Retrieving relevant transcript chunks from vector database
- Sending context to LLM for answer generation
- Managing conversation history
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .pipeline import RAGPipeline as RAGPipeline


def __getattr__(name: str):
	if name == "RAGPipeline":
		from .pipeline import RAGPipeline
		return RAGPipeline
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["RAGPipeline"]
