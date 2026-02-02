"""
Scraper for loading transcripts from GitHub repositories into database.
"""
import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .github_loader import GitHubTranscriptLoader
from ..database import VideoTranscript

logger = logging.getLogger(__name__)


class GitHubScraper:
    """Scraper for loading GitHub transcripts into database."""

    def __init__(
        self,
        session: Session,
        repo: str = "prakhar625/huberman-podcasts-transcripts"
    ):
        """
        Initialize GitHub scraper.

        Args:
            session: SQLAlchemy database session
            repo: GitHub repository in format 'owner/repo'
        """
        self.session = session
        self.loader = GitHubTranscriptLoader(repo)

    def scrape_all_transcripts(
        self,
        start_episode: Optional[int] = None,
        end_episode: Optional[int] = None,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Load all transcripts from GitHub and save to database.

        Args:
            start_episode: Start episode number (None for first)
            end_episode: End episode number (None for last)
            skip_existing: Skip episodes already in database

        Returns:
            Dictionary with scraping statistics
        """
        logger.info(f"Loading transcripts from GitHub: {self.loader.repo}")

        # Get all transcript metadata
        transcripts = self.loader.list_transcripts()

        # Filter by episode range
        if start_episode is not None:
            transcripts = [t for t in transcripts if t['episode_number'] >= start_episode]
        if end_episode is not None:
            transcripts = [t for t in transcripts if t['episode_number'] <= end_episode]

        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total': len(transcripts)
        }

        for i, transcript_info in enumerate(transcripts, 1):
            video_id = transcript_info.get('video_id')
            episode_num = transcript_info['episode_number']
            title = transcript_info['title']

            # Check if already exists by title
            if skip_existing:
                existing = self.session.query(VideoTranscript).filter_by(
                    title=title
                ).first()

                if existing:
                    logger.debug(f"[{i}/{len(transcripts)}] Episode {episode_num} already in DB, skipping")
                    stats['skipped'] += 1
                    continue

            logger.info(f"[{i}/{len(transcripts)}] Loading episode {episode_num}: {title[:60]}...")

            # Load transcript text
            transcript_text = self.loader.load_transcript(transcript_info['transcript_path'])

            if not transcript_text:
                logger.warning(f"Failed to load transcript for episode {episode_num}")
                stats['failed'] += 1
                continue

            # Parse upload date (format: DD/MM/YY)
            try:
                upload_date_str = transcript_info['upload_date']
                date_parts = upload_date_str.split('/')
                # Convert YY to YYYY (assuming 2000s)
                year = int('20' + date_parts[2])
                month = int(date_parts[1])
                day = int(date_parts[0])
                upload_date = f"{year:04d}{month:02d}{day:02d}"
            except (IndexError, ValueError):
                upload_date = None

            # Save to database
            try:
                record = VideoTranscript(
                    video_id=video_id if video_id else None,
                    title=title,
                    channel_id=None,  # Not available in GitHub repo
                    channel_name="Huberman Lab",
                    upload_date=upload_date,
                    duration=transcript_info['duration'],
                    view_count=None,  # Not available in GitHub repo
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
                logger.error(f"Database error for episode {episode_num}: {e}")
                self.session.rollback()
                stats['failed'] += 1

        logger.info(
            f"Scraping complete! Success: {stats['success']}, "
            f"Failed: {stats['failed']}, Skipped: {stats['skipped']}"
        )

        return stats

    def scrape_episode(self, episode_number: int) -> bool:
        """
        Load a single episode by number.

        Args:
            episode_number: Episode number to load

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Loading episode {episode_number} from GitHub")

        data = self.loader.load_transcript_by_episode(episode_number)

        if not data:
            logger.error(f"Episode {episode_number} not found")
            return False

        video_id = data.get('video_id')
        if not video_id:
            logger.error(f"No video ID for episode {episode_number}")
            return False

        # Check if already exists
        existing = self.session.query(VideoTranscript).filter_by(
            video_id=video_id
        ).first()

        if existing:
            logger.warning(f"Episode {episode_number} already in database")
            return False

        # Parse upload date
        try:
            upload_date_str = data['upload_date']
            date_parts = upload_date_str.split('/')
            year = int('20' + date_parts[2])
            month = int(date_parts[1])
            day = int(date_parts[0])
            upload_date = f"{year:04d}{month:02d}{day:02d}"
        except (IndexError, ValueError):
            upload_date = None

        # Save to database
        try:
            record = VideoTranscript(
                video_id=video_id,
                title=data['title'],
                channel_id=None,
                channel_name="Huberman Lab",
                upload_date=upload_date,
                duration=data['duration'],
                view_count=None,
                transcript_text=data['transcript_text'],
                transcript_language='en',
                has_transcript=True,
                error_message=None,
                scraped_at=datetime.utcnow()
            )

            self.session.add(record)
            self.session.commit()

            logger.info(f"✓ Successfully loaded episode {episode_number}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            self.session.rollback()
            return False
