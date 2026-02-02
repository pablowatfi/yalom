"""
Scraper for loading transcripts from Kaggle dataset into database.
"""
import logging
from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .kaggle_loader import KaggleTranscriptLoader
from ..database import VideoTranscript

logger = logging.getLogger(__name__)


class KaggleScraper:
    """Scraper for loading Kaggle transcripts into database."""

    def __init__(
        self,
        session: Session,
        dataset_path: str
    ):
        """
        Initialize Kaggle scraper.

        Args:
            session: SQLAlchemy database session
            dataset_path: Path to extracted Kaggle dataset folder
        """
        self.session = session
        self.loader = KaggleTranscriptLoader(dataset_path)

    def scrape_all_transcripts(
        self,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Load all transcripts from Kaggle dataset and save to database.

        Args:
            skip_existing: Skip episodes already in database

        Returns:
            Dictionary with scraping statistics
        """
        logger.info(f"Loading transcripts from Kaggle dataset: {self.loader.dataset_path}")

        # Get all transcript metadata
        transcripts = self.loader.list_transcripts()

        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total': len(transcripts)
        }

        for i, transcript_info in enumerate(transcripts, 1):
            video_id = transcript_info['video_id']
            title = transcript_info['title']

            # Check if already exists
            if skip_existing:
                existing = self.session.query(VideoTranscript).filter_by(
                    video_id=video_id
                ).first()

                if existing:
                    logger.debug(f"[{i}/{len(transcripts)}] {video_id} already in DB, skipping")
                    stats['skipped'] += 1
                    continue

            logger.info(f"[{i}/{len(transcripts)}] Loading: {title[:60]}...")

            # Load transcript text
            transcript_text = self.loader.load_transcript(video_id)

            if not transcript_text:
                logger.warning(f"Failed to load transcript for {video_id}")
                stats['failed'] += 1
                continue

            # Save to database
            try:
                record = VideoTranscript(
                    video_id=video_id,
                    title=title,
                    channel_id=None,
                    channel_name="Huberman Lab",
                    upload_date=None,  # Not available in Kaggle dataset
                    duration=None,  # Not available in Kaggle dataset
                    view_count=None,  # Not available in Kaggle dataset
                    transcript_text=transcript_text,
                    transcript_language='en',
                    has_transcript=True,
                    error_message=None,
                    scraped_at=datetime.utcnow()
                )

                self.session.add(record)
                self.session.commit()

                logger.info(f"  ✓ Saved transcript ({len(transcript_text)} chars)")
                stats['success'] += 1

            except SQLAlchemyError as e:
                logger.error(f"Database error for {video_id}: {e}")
                self.session.rollback()
                stats['failed'] += 1

        logger.info(
            f"Scraping complete! Success: {stats['success']}, "
            f"Failed: {stats['failed']}, Skipped: {stats['skipped']}"
        )

        return stats

    def scrape_video(self, video_id: str) -> bool:
        """
        Load a single video by ID.

        Args:
            video_id: YouTube video ID

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading video {video_id} from Kaggle dataset")

        # Check if already exists
        existing = self.session.query(VideoTranscript).filter_by(
            video_id=video_id
        ).first()

        if existing:
            logger.warning(f"Video {video_id} already in database")
            return False

        # Load transcript
        transcript_text = self.loader.load_transcript(video_id)

        if not transcript_text:
            logger.error(f"Transcript not found for {video_id}")
            return False

        # Get title
        title = self.loader.get_video_title(video_id)

        # Save to database
        try:
            record = VideoTranscript(
                video_id=video_id,
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

            self.session.add(record)
            self.session.commit()

            logger.info(f"✓ Successfully loaded video {video_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            self.session.rollback()
            return False
