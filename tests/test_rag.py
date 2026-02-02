#!/usr/bin/env python3
"""
Simple test of the RAG pipeline with a single question.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline


def main():
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        return 1

    print("Initializing RAG pipeline...")
    rag = RAGPipeline(api_key=api_key, top_k=5)

    print("\nAsking test question...")
    question = "What are Andrew Huberman's recommendations for improving sleep quality?"

    result = rag.ask(question)

    print("\n" + "=" * 80)
    print("QUESTION:", question)
    print("=" * 80)
    print("\nANSWER:")
    print(result["answer"])
    print("\n" + "=" * 80)
    print(f"SOURCES ({len(result['sources'])} excerpts):")
    print("=" * 80)

    for i, source in enumerate(result["sources"], 1):
        print(f"\n{i}. {source['title']}")
        print(f"   {source['content']}")

    print("\n✅ Test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
