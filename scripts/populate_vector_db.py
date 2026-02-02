#!/usr/bin/env python3
"""
Populate Qdrant vector database with all transcripts from PostgreSQL.

This script:
1. Connects to PostgreSQL
2. Initializes Qdrant collection
3. Processes all transcripts in batches
4. Generates embeddings and stores vectors

Usage:
    poetry run python populate_vector_db.py          # Skip existing transcripts
    poetry run python populate_vector_db.py --recreate  # Clear and re-vectorize all
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db, VideoTranscript
from src.vectorization.vector_store import VectorStoreManager
from src.vectorization.pipeline import VectorizationPipeline
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, CHUNKING_STRATEGY, EMBEDDING_MODEL, EMBEDDING_DIMENSION


def main():
    # Check for --recreate flag
    recreate = '--recreate' in sys.argv or '-r' in sys.argv

    print("="*80)
    print("  Populating Qdrant Vector Database")
    print("="*80)
    print()

    if recreate:
        print("⚠️  RECREATE MODE: Will delete existing collection and re-vectorize all")
    else:
        print("📝 INCREMENTAL MODE: Will skip already vectorized transcripts")
        print("   (Use --recreate to clear and re-vectorize all)")
    print()

    # Using OpenAI embeddings
    print(f"Using OpenAI embeddings ({EMBEDDING_MODEL})")
    print(f"  - {EMBEDDING_DIMENSION} dimensions")
    print("  - Requires OPENAI_API_KEY")
    print()

    # Connect to database
    print("1. Connecting to PostgreSQL...")
    db.connect()
    session = db.get_session()

    # Get transcript count
    total = session.query(VideoTranscript).count()
    with_transcript = session.query(VideoTranscript).filter(
        VideoTranscript.has_transcript == True
    ).count()

    print(f"   ✓ Connected")
    print(f"   Total records: {total}")
    print(f"   With transcripts: {with_transcript}")
    print()

    if with_transcript == 0:
        print("❌ No transcripts found to process!")
        return 1

    # Initialize vector store
    print("2. Initializing Qdrant vector store...")
    vector_store = VectorStoreManager(
        collection_name="huberman_transcripts",
        qdrant_url="http://localhost:6333",
        embedding_dimension=EMBEDDING_DIMENSION
    )

    # Check if collection exists
    try:
        info = vector_store.get_collection_info()
        existing_points = info.get('points_count', 0)

        if existing_points > 0:
            if recreate:
                print(f"   🗑️  Deleting existing collection with {existing_points} vectors...")
                vector_store.create_collection(recreate=True)
                print("   ✓ Collection recreated")
            else:
                print(f"   ✓ Collection exists with {existing_points} vectors")
                print("   Will skip already vectorized transcripts")
        else:
            vector_store.create_collection(recreate=False)
            print("   ✓ Collection created")
    except Exception as e:
        print(f"   Creating new collection...")
        vector_store.create_collection(recreate=True)
        print("   ✓ Collection created")

    print()
    # Initialize pipeline
    print("3. Setting up vectorization pipeline...")
    pipeline = VectorizationPipeline(
        vector_store_manager=vector_store,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        chunking_strategy=CHUNKING_STRATEGY
    )
    print("   ✓ Pipeline ready")
    print(f"   Chunk size: {CHUNK_SIZE} characters")
    print(f"   Chunk overlap: {CHUNK_OVERLAP} characters")
    print(f"   Strategy: {CHUNKING_STRATEGY}")
    print()

    # Process all transcripts
    print("4. Processing transcripts...")
    print()

    # Ask for batch size
    try:
        batch_input = input(f"   Process how many transcripts? (Enter number or 'all' for all {with_transcript}): ").strip()

        if batch_input.lower() == 'all':
            limit = None
            print(f"   Processing all {with_transcript} transcripts...")
        else:
            limit = int(batch_input)
            print(f"   Processing {limit} transcripts...")
    except (ValueError, KeyboardInterrupt):
        print("\n   Cancelled.")
        return 0

    print()

    # Run batch processing
    stats = pipeline.process_transcripts_batch(
        session=session,
        limit=limit,
        skip_existing=not recreate  # Don't skip if recreating
    )

    print()
    print("="*80)
    print("  Processing Complete")
    print("="*80)
    print(f"  ✓ Success: {stats['success']}")
    print(f"  ✗ Failed: {stats['failed']}")
    print(f"  ○ Skipped: {stats['skipped']}")
    print(f"  📊 Total chunks created: {stats['total_chunks']}")
    print()

    # Get final collection info
    info = vector_store.get_collection_info()
    print("  Collection Statistics:")
    print(f"  - Name: {info.get('name')}")
    print(f"  - Total vectors: {info.get('points_count')}")
    print(f"  - Status: {info.get('status')}")
    print()
    print()
    print("="*80)
    print("✅ Vector database population complete!")
    print()
    print("Next steps:")
    print("  - Test search: poetry run python test_search.py")
    print("  - View dashboard: http://localhost:6333/dashboard")
    print("="*80)

    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
