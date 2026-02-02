#!/usr/bin/env python3
"""
Clean timestamps from transcripts in both PostgreSQL and Qdrant.

Timestamps appear in formats like:
- "3011.26 So things like..."
- "0.35 - Welcome to..."
- "1234.567 text here"

This script will:
1. Clean timestamps from all transcripts in PostgreSQL
2. Re-vectorize the cleaned transcripts in Qdrant
"""
import re
import logging

from src.database.connection import Database
from src.database.models import VideoTranscript
from src.vectorization.vector_store import VectorStoreManager
from src.vectorization.pipeline import VectorizationPipeline
from src.config import CHUNK_SIZE, CHUNK_OVERLAP, CHUNKING_STRATEGY

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_timestamps(text: str) -> str:
    """
    Remove timestamps from transcript text.

    Patterns to remove:
    - "3011.26 " at start of lines
    - "0.35 - " at start of lines
    - Any "number.number " pattern at line starts

    Args:
        text: Original transcript text with timestamps

    Returns:
        Cleaned text without timestamps
    """
    if not text:
        return text

    # Pattern: Remove timestamps at start of lines
    # Matches: "3011.26 ", "0.35 - ", "1234.567 "
    # \d+ = one or more digits
    # \.\d+ = decimal point + digits
    # \s* = optional whitespace
    # -?\s* = optional dash and whitespace
    pattern = r'^\d+\.\d+\s*-?\s*'

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Remove timestamp from start of line
        cleaned_line = re.sub(pattern, '', line.strip())
        if cleaned_line:  # Only add non-empty lines
            cleaned_lines.append(cleaned_line)

    return '\n'.join(cleaned_lines)


def main():
    """Clean timestamps from all transcripts."""
    logger.info("=" * 80)
    logger.info("TIMESTAMP CLEANING SCRIPT")
    logger.info("=" * 80)

    # Connect to database
    logger.info("Connecting to database...")
    db = Database()
    db.connect()
    session = db.SessionLocal()

    # Get all transcripts with text
    logger.info("Fetching transcripts...")
    transcripts = session.query(VideoTranscript).filter(
        VideoTranscript.transcript_text.isnot(None)
    ).all()

    logger.info(f"Found {len(transcripts)} transcripts to clean")

    # Ask for confirmation
    print("\nThis will:")
    print("1. Clean timestamps from all transcripts in PostgreSQL")
    print("2. Delete and recreate the Qdrant collection")
    print("3. Re-vectorize all cleaned transcripts")
    print(f"\nTotal transcripts to process: {len(transcripts)}")

    response = input("\nProceed? (yes/no): ").strip().lower()
    if response != 'yes':
        logger.info("Aborted by user")
        session.close()
        return

    # Step 1: Clean timestamps in database
    logger.info("\nStep 1: Cleaning timestamps in PostgreSQL...")
    cleaned_count = 0

    for i, transcript in enumerate(transcripts, 1):
        original_text = transcript.transcript_text
        cleaned_text = clean_timestamps(original_text)

        if original_text != cleaned_text:
            transcript.transcript_text = cleaned_text
            cleaned_count += 1

            if i % 50 == 0:
                logger.info(f"Processed {i}/{len(transcripts)} transcripts...")

    session.commit()
    logger.info(f"✅ Cleaned {cleaned_count} transcripts in database")

    # Step 2: Re-vectorize in Qdrant
    logger.info("\nStep 2: Re-vectorizing in Qdrant...")

    # Clear and recreate collection
    vector_store = VectorStoreManager()
    logger.info("Clearing old collection and recreating...")
    vector_store.clear_collection()

    # Vectorize all cleaned transcripts
    logger.info("Vectorizing cleaned transcripts...")
    logger.info(f"Using chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}, strategy={CHUNKING_STRATEGY}")
    pipeline = VectorizationPipeline(
        vector_store_manager=vector_store,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        chunking_strategy=CHUNKING_STRATEGY
    )

    vectorized_count = 0
    for i, transcript in enumerate(transcripts, 1):
        if transcript.transcript_text:
            try:
                # Pass the VideoTranscript object directly
                pipeline.process_transcript(transcript)
                vectorized_count += 1

                if i % 10 == 0:
                    logger.info(f"Vectorized {i}/{len(transcripts)} transcripts ({vectorized_count} total)...")
            except Exception as e:
                logger.error(f"Error vectorizing {transcript.title}: {e}")

    session.close()

    logger.info("=" * 80)
    logger.info("CLEANING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Cleaned: {cleaned_count} transcripts")
    logger.info(f"Vectorized: {vectorized_count} transcripts")
    logger.info("All timestamps removed from both PostgreSQL and Qdrant")


if __name__ == "__main__":
    main()
