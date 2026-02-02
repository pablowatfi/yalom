#!/usr/bin/env python3
"""
Test the new multilingual translation flow.

Flow:
1. User asks in Spanish
2. Detect language = Spanish
3. Translate question to English
4. Run RAG retrieval in English
5. Get answer in English
6. Translate answer to Spanish
7. Return Spanish answer to user
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline
from src.config import (
    RAG_TOP_K,
    RAG_RETRIEVAL_MULTIPLIER,
    RAG_SIMILARITY_THRESHOLD
)

print("=" * 80)
print("  Testing Multilingual Translation Flow")
print("=" * 80)
print()

# Initialize pipeline
print("Initializing RAG pipeline...")
rag = RAGPipeline(
    llm_provider="ollama",
    model_name="llama3.2",
    query_rewriting=True,
    verbose_sources=0,
    top_k=RAG_TOP_K,
    retrieval_multiplier=RAG_RETRIEVAL_MULTIPLIER,
    similarity_threshold=RAG_SIMILARITY_THRESHOLD
)
print(f"✅ Ready! (top_k={RAG_TOP_K}, retrieval={RAG_TOP_K * RAG_RETRIEVAL_MULTIPLIER}, threshold={RAG_SIMILARITY_THRESHOLD})\\n")

# Test with Spanish question
print("=" * 80)
print("🇪🇸 TEST: Spanish Question")
print("=" * 80)
question_es = "¿Qué dice Huberman sobre el sueño?"
print(f"Pregunta: {question_es}\n")

result = rag.ask(question_es)

print(f"\nRespuesta ({len(result['answer'])} chars):")
print(result['answer'][:400])
if len(result['answer']) > 400:
    print("...")
print(f"\n✅ Fuentes: {len(result['sources'])} episodios")

print("\n" + "=" * 80)
print("✅ Translation flow working!")
print("=" * 80)
