#!/usr/bin/env python3
"""
Test vectorization pipeline with a sample transcript.

This script:
1. Connects to PostgreSQL to get a transcript
2. Chunks the text using LangChain
3. Generates embeddings
4. Stores in Qdrant
5. Tests semantic search
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import db, VideoTranscript
from src.vectorization.vector_store import VectorStoreManager
from src.vectorization.pipeline import VectorizationPipeline

def main():
    print("="*70)
    print("  Vectorization Pipeline Test")
    print("="*70)
    print()

    # Connect to database
    print("1. Connecting to PostgreSQL...")
    db.connect()
    session = db.get_session()

    # Get a sample transcript
    transcript = session.query(VideoTranscript).filter(
        VideoTranscript.has_transcript == True
    ).first()

    if not transcript:
        print("❌ No transcripts found in database!")
        return

    print(f"   ✓ Found transcript: {transcript.title}")
    print(f"   Transcript ID: {transcript.video_id}")
    print(f"   Length: {len(transcript.transcript_text)} characters")
    print()

    # Initialize vector store
    print("2. Initializing Qdrant vector store...")
    vector_store = VectorStoreManager(
        collection_name="huberman_test",
        qdrant_url="http://localhost:6333",
        embedding_model="text-embedding-3-small"
    )

    # Create collection
    vector_store.create_collection(recreate=True)
    print("   ✓ Collection created")
    print()

    # Initialize pipeline
    print("3. Setting up vectorization pipeline...")
    pipeline = VectorizationPipeline(
        vector_store_manager=vector_store,
        chunk_size=1000,
        chunk_overlap=200,
        chunking_strategy="recursive"
    )
    print("   ✓ Pipeline ready")
    print()

    # Process transcript
    print("4. Processing transcript (chunking + embedding)...")
    num_chunks = pipeline.process_transcript(transcript)
    print(f"   ✓ Created and stored {num_chunks} chunks")
    print()

    # Test semantic search
    print("5. Testing semantic search...")
    test_queries = [
        "sleep and circadian rhythm",
        "dopamine and motivation",
        "stress management techniques"
    ]

    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = vector_store.search(query, k=3)

        for i, doc in enumerate(results, 1):
            print(f"   [{i}] {doc.page_content[:100]}...")
            print(f"       Transcript: {doc.metadata.get('transcript_id')}")
            print(f"       Chunk: {doc.metadata.get('chunk_index')}/{doc.metadata.get('total_chunks')}")

    print()

    # Get collection info
    info = vector_store.get_collection_info()
    print("6. Collection Statistics:")
    print(f"   Name: {info.get('name')}")
    print(f"   Points: {info.get('points_count')}")
    print(f"   Vectors: {info.get('vectors_count')}")
    print(f"   Status: {info.get('status')}")

    print()
    print("="*70)
    print("✅ Test completed successfully!")
    print("="*70)

    session.close()


if __name__ == "__main__":
    main()
