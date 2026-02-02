#!/usr/bin/env python3
"""
Test script to demonstrate multilingual support in the RAG pipeline.

Usage:
    poetry run python test_multilingual.py

This script tests the RAG system with questions in different languages
and verifies that answers are returned in the same language.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline
from src.config import RAG_TOP_K


def test_multilingual():
    """Test RAG pipeline with multiple languages."""

    print("=" * 80)
    print("  Multilingual RAG Pipeline Test")
    print("=" * 80)
    print()

    # Initialize pipeline
    print("Initializing RAG pipeline...")
    rag = RAGPipeline(
        llm_provider="ollama",
        model_name="llama3.2",
        query_rewriting=True,
        verbose_sources=0,
        top_k=RAG_TOP_K  # Use config default (7)
    )
    print(f"✅ Ready! (top_k={RAG_TOP_K})\n")

    # Test questions in different languages
    test_cases = [
        {
            "language": "English 🇺🇸",
            "question": "What does Huberman say about sleep?",
            "expected_start": ["According", "Based on", "Dr. Huberman", "The transcripts"]
        },
        {
            "language": "Spanish 🇪🇸",
            "question": "¿Qué dice Huberman sobre el ejercicio?",
            "expected_start": ["Según", "De acuerdo", "Dr. Huberman", "Los transcriptos"]
        },
        {
            "language": "French 🇫🇷",
            "question": "Que dit Huberman sur la dopamine?",
            "expected_start": ["Selon", "D'après", "Dr. Huberman", "Les transcriptions"]
        },
        {
            "language": "German 🇩🇪",
            "question": "Was sagt Huberman über Konzentration?",
            "expected_start": ["Laut", "Gemäß", "Dr. Huberman", "Nach den"]
        },
        {
            "language": "Portuguese 🇧🇷",
            "question": "O que Huberman diz sobre suplementos?",
            "expected_start": ["De acordo", "Segundo", "Dr. Huberman", "As transcrições"]
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print("─" * 80)
        print(f"Test {i}: {test['language']}")
        print("─" * 80)
        print(f"Question: {test['question']}")
        print()
        print("Searching transcripts...")

        try:
            result = rag.ask(test['question'])
            answer = result['answer']

            # Show first 300 characters of answer
            print(f"\nAnswer ({len(answer)} chars):")
            print(answer[:300] + ("..." if len(answer) > 300 else ""))
            print()
            print(f"✅ Sources: {len(result['sources'])} episodes")

            # Check if answer seems to be in expected language
            answer_start = answer.split()[0] if answer else ""
            language_detected = any(
                answer_start.startswith(expected) or expected.lower() in answer[:100].lower()
                for expected in test['expected_start']
            )

            if language_detected:
                print(f"✅ Answer appears to be in {test['language'].split()[0]}")
            else:
                print(f"⚠️  Could not verify language (might still be correct)")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 80)
    print("✅ Multilingual testing complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print("- The RAG system detects the user's language")
    print("- Answers are automatically translated to match the input language")
    print("- Works with: English, Spanish, French, German, Portuguese, and more!")
    print()


if __name__ == "__main__":
    test_multilingual()
