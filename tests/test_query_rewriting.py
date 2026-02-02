#!/usr/bin/env python3
"""
Test script to compare RAG performance with and without query rewriting.

Usage:
    poetry run python test_query_rewriting.py

This script runs the same questions with query rewriting ON and OFF,
showing the difference in retrieved sources and quality.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline


def test_query_comparison():
    """Compare RAG with and without query rewriting."""

    print("=" * 80)
    print("  Query Rewriting Performance Comparison")
    print("=" * 80)
    print()

    test_questions = [
        "sleep tips",
        "focus and concentration",
        "morning routines"
    ]

    for question in test_questions:
        print("\n" + "─" * 80)
        print(f"QUESTION: {question}")
        print("─" * 80)

        # Test WITHOUT query rewriting
        print("\n🔵 WITHOUT Query Rewriting:")
        print("-" * 40)
        rag_without = RAGPipeline(
            llm_provider="ollama",
            model_name="llama3.2",
            query_rewriting=False,  # Disabled
            top_k=6,
            verbose_sources=0
        )
        result_without = rag_without.ask(question)

        sources_without = set([s['title'] for s in result_without['sources']])
        print(f"Retrieved: {len(sources_without)} unique episodes")
        for i, title in enumerate(sorted(sources_without), 1):
            print(f"  {i}. {title[:70]}...")

        # Test WITH query rewriting
        print("\n🟢 WITH Query Rewriting:")
        print("-" * 40)
        rag_with = RAGPipeline(
            llm_provider="ollama",
            model_name="llama3.2",
            query_rewriting=True,  # Enabled
            top_k=6,
            verbose_sources=0
        )
        result_with = rag_with.ask(question)

        sources_with = set([s['title'] for s in result_with['sources']])
        print(f"Retrieved: {len(sources_with)} unique episodes")
        for i, title in enumerate(sorted(sources_with), 1):
            print(f"  {i}. {title[:70]}...")

        # Show difference
        only_with_rewriting = sources_with - sources_without
        if only_with_rewriting:
            print(f"\n✨ Additional episodes found with query rewriting: {len(only_with_rewriting)}")
            for title in sorted(only_with_rewriting):
                print(f"   + {title[:70]}...")

        print("\n📊 Summary:")
        print(f"   Without rewriting: {len(sources_without)} episodes")
        print(f"   With rewriting:    {len(sources_with)} episodes")
        print(f"   Improvement:       {len(sources_with) - len(sources_without):+d} episodes")

    print("\n" + "=" * 80)
    print("✅ Comparison complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_query_comparison()
