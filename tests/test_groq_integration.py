#!/usr/bin/env python3
"""
Test script to verify Groq integration with the RAG pipeline.

Usage:
    export GROQ_YALOM_API_KEY=gsk_your_key_here
    poetry run python test_groq_integration.py
"""
import os
import sys
from src.rag.pipeline import RAGPipeline

def test_groq():
    """Test Groq integration."""

    # Check API key
    api_key = os.getenv("GROQ_YALOM_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_YALOM_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export GROQ_YALOM_API_KEY=gsk_your_key_here")
        print("\nGet your API key from: https://console.groq.com")
        sys.exit(1)

    print("✅ API key found:", api_key[:10] + "..." + api_key[-4:])
    print("\n" + "="*60)
    print("Testing Groq Integration")
    print("="*60 + "\n")

    try:
        # Initialize RAG pipeline with Groq
        print("🔧 Initializing RAG pipeline with Groq...")
        pipeline = RAGPipeline(
            llm_provider="groq",
            model_name="llama-3.1-70b-versatile",
            api_key=api_key,
            top_k=3,
            query_rewriting=False,  # Disable for faster testing
            verbose_sources=1
        )
        print("✅ Pipeline initialized successfully!\n")

        # Test query
        print("📝 Testing query: 'What is neuroplasticity?'\n")
        result = pipeline.ask("What is neuroplasticity?")

        print("="*60)
        print("ANSWER:")
        print("="*60)
        print(result['answer'])
        print("\n" + "="*60)
        print(f"SOURCES: {len(result['sources'])} chunks")
        print("="*60)

        for i, source in enumerate(result['sources'][:3], 1):
            metadata = source.metadata
            print(f"\n{i}. {metadata.get('title', 'Unknown')}")
            print(f"   Score: {metadata.get('score', 'N/A'):.4f}")
            print(f"   Excerpt: {source.page_content[:150]}...")

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_groq()
