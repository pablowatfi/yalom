#!/usr/bin/env python3
"""
Interactive CLI for asking questions about Huberman Lab transcripts.

Usage:
    poetry run python chat_cli.py

Features:
- Ask questions about any Huberman Lab episode
- Get answers with sources/citations
- Conversation history maintained during session
- Type 'quit', 'exit', or press Ctrl+C to exit
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag import RAGPipeline
from src.config import (
    RAG_TOP_K,
    RAG_TEMPERATURE,
    RAG_QUERY_REWRITING,
    RAG_RETRIEVAL_MULTIPLIER,
    RAG_SIMILARITY_THRESHOLD
)


def print_banner():
    """Print welcome banner."""
    print("=" * 80)
    print("  Huberman Lab AI Assistant")
    print("=" * 80)
    print()
    print("Ask questions about any Huberman Lab podcast episode!")
    print("The AI will search through all transcripts and provide answers with sources.")
    print()
    print("Commands:")
    print("  - Type your question and press Enter")
    print("  - 'reset' - Clear conversation history")
    print("  - 'quit' or 'exit' - Exit the chat")
    print()
    print("=" * 80)
    print()


def print_answer(result: dict):
    """Pretty print the answer with sources."""
    print("\n" + "─" * 80)
    print("ANSWER:")
    print("─" * 80)
    print(result["answer"])
    print()

    if result["sources"]:
        print("─" * 80)
        print(f"SOURCES ({len(result['sources'])} transcript excerpts):")
        print("─" * 80)

        # Group by title
        sources_by_title = {}
        for source in result["sources"]:
            title = source["title"]
            if title not in sources_by_title:
                sources_by_title[title] = []
            sources_by_title[title].append(source)

        for i, (title, sources) in enumerate(sources_by_title.items(), 1):
            print(f"\n{i}. {title}")
            print(f"   ({len(sources)} excerpt{'s' if len(sources) > 1 else ''})")

    print("=" * 80 + "\n")


def main():
    """Run interactive chat CLI."""
    print_banner()

    # Check for verbose sources flag
    verbose = 0
    if len(sys.argv) > 1 and sys.argv[1] in ['-v', '--verbose']:
        verbose = 1
        print("🔍 Verbose mode: Will show full transcript excerpts in logs\n")
    else:
        print("💡 Tip: Use -v or --verbose to see full transcript excerpts in logs\n")

    # Choose LLM provider
    print("Choose your LLM provider:")
    print("  1. Ollama (FREE, runs locally - recommended)")
    print("  2. OpenAI (requires API key, ~$0.001 per question)")
    print()

    choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"

    if choice == "1":
        # Ollama - Free and local
        print("\n🦙 Using Ollama (free, local)")
        print("   Make sure Ollama is installed and running:")
        print("   • Install: https://ollama.ai")
        print("   • Pull model: ollama pull llama3.2")
        print("   • Check running: ollama list")
        print()

        model = input("Model name (default=llama3.2): ").strip() or "llama3.2"

        try:
            rag = RAGPipeline(
                llm_provider="ollama",
                model_name=model,
                top_k=RAG_TOP_K,
                retrieval_multiplier=RAG_RETRIEVAL_MULTIPLIER,
                similarity_threshold=RAG_SIMILARITY_THRESHOLD,
                temperature=RAG_TEMPERATURE,
                verbose_sources=verbose,
                query_rewriting=RAG_QUERY_REWRITING
            )
        except Exception as e:
            print(f"\n❌ Failed to initialize Ollama: {e}")
            print("\n💡 Make sure Ollama is running:")
            print("   ollama serve")
            print(f"   ollama pull {model}")
            return 1

    elif choice == "2":
        # OpenAI - Requires API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️  OPENAI_API_KEY not found in environment variables")
            print("   Please set it:")
            print("   export OPENAI_API_KEY='your-api-key-here'")
            print()
            api_key = input("Or enter your OpenAI API key now: ").strip()
            if not api_key:
                print("\n❌ No API key provided. Exiting.")
                return 1

        print("\n🔧 Initializing OpenAI...")
        try:
            rag = RAGPipeline(
                llm_provider="openai",
                api_key=api_key,
                model_name="gpt-4o-mini",
                top_k=RAG_TOP_K,
                retrieval_multiplier=RAG_RETRIEVAL_MULTIPLIER,
                similarity_threshold=RAG_SIMILARITY_THRESHOLD,
                temperature=RAG_TEMPERATURE,
                verbose_sources=verbose,
                query_rewriting=RAG_QUERY_REWRITING
            )
        except Exception as e:
            print(f"\n❌ Failed to initialize OpenAI: {e}")
            return 1
    else:
        print("\n❌ Invalid choice")
        return 1

    print("✅ Ready! Ask your first question.\n")

    # Main chat loop
    while True:
        try:
            # Get user input
            question = input("You: ").strip()

            if not question:
                continue

            # Handle commands
            if question.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!\n")
                break

            if question.lower() == "reset":
                rag.reset_conversation()
                print("\n🔄 Conversation history cleared.\n")
                continue

            # Process question
            print("\n🤔 Searching transcripts and generating answer...\n")
            result = rag.ask(question)

            # Display answer
            print_answer(result)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
