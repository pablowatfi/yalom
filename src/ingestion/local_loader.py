#!/usr/bin/env python3
"""
Load local transcript files from /data folder into the database.
"""
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..database import db, VideoTranscript

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_LOCAL_TRANSCRIPTS_DIR = "data/transcripts"


def extract_episode_number(filename: str) -> Optional[int]:
    """Extract episode number from filename like 'Episode-1.txt'"""
    match = re.search(r'Episode-(\d+)', filename)
    if match:
        return int(match.group(1))
    return None


def load_local_transcripts(data_folder: str = DEFAULT_LOCAL_TRANSCRIPTS_DIR) -> None:
    """
    Load all local transcript files into the database.

    Args:
        data_folder: Path to folder containing transcript files
    """
    logger.info("Connecting to database...")
    db.connect()
    session = db.get_session()

    # Get all transcript files
    data_path = Path(data_folder)
    if not data_path.exists():
        logger.error(f"Data folder not found: {data_folder}")
        return

    transcript_files = sorted(data_path.glob("Episode-*.txt"))
    logger.info(f"Found {len(transcript_files)} transcript files")

    stats = {
        'success': 0,
        'skipped': 0,
        'failed': 0
    }

    for i, filepath in enumerate(transcript_files, 1):
        episode_num = extract_episode_number(filepath.name)

        if episode_num is None:
            logger.warning(f"Could not extract episode number from {filepath.name}")
            stats['failed'] += 1
            continue

        # Create title for this episode
        title = f"Huberman Lab Episode {episode_num}"

        # Check if already exists by title
        existing = session.query(VideoTranscript).filter_by(title=title).first()
        if existing:
            logger.debug(f"[{i}/{len(transcript_files)}] Episode {episode_num} already exists, skipping")
            stats['skipped'] += 1
            continue

        logger.info(f"[{i}/{len(transcript_files)}] Loading Episode {episode_num}...")

        try:
            # Read transcript file
            with open(filepath, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            # Create database record
            record = VideoTranscript(
                video_id=None,  # Local files don't have YouTube video IDs
                title=title,
                channel_id=None,
                channel_name="Huberman Lab",
                upload_date=None,
                duration=None,
                view_count=None,
                transcript_text=transcript_text,
                transcript_language='en',
                has_transcript=True,
                error_message=None,
                scraped_at=datetime.utcnow()
            )

            session.add(record)
            session.commit()

            logger.info(f"  ✓ Saved Episode {episode_num} ({len(transcript_text)} chars)")
            stats['success'] += 1

        except Exception as e:
            logger.error(f"  ✗ Error loading Episode {episode_num}: {e}")
            session.rollback()
            stats['failed'] += 1

    logger.info(
        "Local transcripts load complete",
        extra={
            "success": stats["success"],
            "skipped": stats["skipped"],
            "failed": stats["failed"],
            "total_files": len(transcript_files),
        },
    )

    # Show current database totals
    total_count = session.query(VideoTranscript).filter(
        VideoTranscript.has_transcript
    ).count()
    logger.info("Current transcript total", extra={"total_transcripts": total_count})

    session.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Load local transcript files into database'
    )
    parser.add_argument(
        '--folder',
        default=DEFAULT_LOCAL_TRANSCRIPTS_DIR,
        help='Path to folder containing transcript files'
    )

    args = parser.parse_args()

    load_local_transcripts(args.folder)
