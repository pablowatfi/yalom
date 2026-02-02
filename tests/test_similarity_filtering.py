#!/usr/bin/env python3
"""
Test similarity threshold filtering to show how it improves quality.

This demonstrates:
1. Retrieving more candidates (21 instead of 7)
2. Filtering by similarity threshold (≥0.5)
3. Returning only high-quality matches
"""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline
from src.config import (
    RAG_TOP_K,
    RAG_RETRIEVAL_MULTIPLIER,
    RAG_SIMILARITY_THRESHOLD
)

# Enable INFO logging to see filtering stats
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

print("=" * 80)
print("  Similarity Threshold Filtering Test")
print("=" * 80)
print()

# Initialize pipeline
print("Initializing RAG pipeline...")
print(f"  - Top K (final): {RAG_TOP_K}")
print(f"  - Retrieval candidates: {RAG_TOP_K * RAG_RETRIEVAL_MULTIPLIER}")
print(f"  - Similarity threshold: {RAG_SIMILARITY_THRESHOLD}")
print()

rag = RAGPipeline(
    llm_provider="ollama",
    model_name="llama3.2",
    query_rewriting=True,
    verbose_sources=0,
    top_k=RAG_TOP_K,
    retrieval_multiplier=RAG_RETRIEVAL_MULTIPLIER,
    similarity_threshold=RAG_SIMILARITY_THRESHOLD
)

print("\n" + "=" * 80)
print("TEST 1: Good Match (Specific Topic)")
print("=" * 80)
question1 = "What are Huberman's recommendations for sleep optimization?"
print(f"Question: {question1}\n")

result1 = rag.ask(question1)

print(f"\nAnswer length: {len(result1['answer'])} chars")
print(f"Sources returned: {len(result1['sources'])} episodes")
print(f"Answer preview: {result1['answer'][:200]}...")

print("\n" + "=" * 80)
print("TEST 2: Vague Query (May filter more)")
print("=" * 80)
question2 = "quantum physics"
print(f"Question: {question2}\n")

result2 = rag.ask(question2)

print(f"\nAnswer length: {len(result2['answer'])} chars")
print(f"Sources returned: {len(result2['sources'])} episodes")
print(f"Answer preview: {result2['answer'][:200]}...")

print("\n" + "=" * 80)
print("TEST 3: Very Specific (Should get high-quality matches)")
print("=" * 80)
question3 = "dopamine fasting protocol recommendations"
print(f"Question: {question3}\n")

result3 = rag.ask(question3)

print(f"\nAnswer length: {len(result3['answer'])} chars")
print(f"Sources returned: {len(result3['sources'])} episodes")
print(f"Answer preview: {result3['answer'][:200]}...")

print("\n" + "=" * 80)
print("✅ Similarity filtering test complete!")
print("=" * 80)
print("\nKey improvements:")
print("  - Retrieves 3x more candidates for better coverage")
print("  - Filters out weak matches (< 0.5 similarity)")
print("  - Returns 1-7 sources based on actual relevance")
print("  - Prevents misleading information from unrelated topics")
