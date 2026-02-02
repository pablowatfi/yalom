"""
TapeSearch podcast scraping functionality.
"""
import logging
from time import sleep
from datetime import datetime
from typing import List, Dict, Optional
import random

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import DEFAULT_DELAY_SECONDS
from ..database import PodcastTranscript
from .tapesearch_fetcher import TapeSearchClient, TapeSearchError

logger = logging.getLogger(__name__)


class TapeSearchScraper:
    """Scraper for TapeSearch podcast transcripts."""

    def __init__(
        self,
        session: Session,
        api_key: str,
        delay: float = DEFAULT_DELAY_SECONDS
    ):
        """
        Initialize the TapeSearch scraper.

        Args:
            session: SQLAlchemy database session
            api_key: TapeSearch API key
            delay: Delay in seconds between episode fetches (to avoid rate limiting)
        """
        self.session = session
        self.client = TapeSearchClient(api_key)
        self.delay = delay

    def search_and_scrape_podcast(
        self,
        podcast_name: str,
        skip_existing: bool = True,
        max_episodes: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Search for a podcast and scrape all its episodes.

        Args:
            podcast_name: Name of the podcast to search for
            skip_existing: If True, skip episodes already in database
            max_episodes: Maximum number of episodes to process (None for all)

        Returns:
            Dictionary with scraping statistics
        """
        logger.info(f"Searching for podcast: {podcast_name}")

        try:
            # Search for the podcast
            podcasts = self.client.search_podcast(podcast_name)

            if not podcasts:
                logger.error(f"No podcast found matching '{podcast_name}'")
                return {'success': 0, 'failed': 0, 'skipped': 0, 'total': 0}

            # Use the first match (you can add logic to select the best match)
            podcast = podcasts[0]
            podcast_uid = podcast.get('uid')
            podcast_title = podcast.get('title', podcast_name)

            logger.info(f"Found podcast: {podcast_title} (UID: {podcast_uid})")

            # Scrape the podcast
            return self.scrape_podcast(
                podcast_uid=podcast_uid,
                podcast_title=podcast_title,
                skip_existing=skip_existing,
                max_episodes=max_episodes
            )

        except TapeSearchError as e:
            logger.error(f"Failed to search and scrape podcast: {e}")
            return {'success': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    def scrape_podcast(
        self,
        podcast_uid: str,
        podcast_title: Optional[str] = None,
        skip_existing: bool = True,
        max_episodes: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Scrape all episodes from a podcast and save transcripts to database.

        Args:
            podcast_uid: TapeSearch podcast UID
            podcast_title: Optional podcast title (will be fetched if not provided)
            skip_existing: If True, skip episodes already in database
            max_episodes: Maximum number of episodes to process (None for all)

        Returns:
            Dictionary with scraping statistics:
            - success: Number of transcripts successfully fetched
            - failed: Number of episodes without transcripts
            - skipped: Number of episodes skipped (already in DB)
            - total: Total number of episodes processed
        """
        logger.info(f"Starting podcast scrape: {podcast_uid}")

        try:
            # Get all episodes from podcast
            podcast_data = self.client.get_podcast_episodes(podcast_uid)
            episodes = podcast_data.get('episodes', [])

            if not episodes:
                logger.warning(f"No episodes found for podcast {podcast_uid}")
                return {'success': 0, 'failed': 0, 'skipped': 0, 'total': 0}

            # Get podcast title if not provided
            if not podcast_title:
                podcast_info = podcast_data.get('podcast', {})
                podcast_title = podcast_info.get('title', podcast_uid)

            # Limit number of episodes if specified
            if max_episodes:
                episodes = episodes[:max_episodes]
                logger.info(f"Limited to {max_episodes} episodes")

            # Process each episode
            stats = {
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'total': len(episodes)
            }

            for i, episode in enumerate(episodes, 1):
                episode_uid = episode.get('uid')

                if not episode_uid:
                    logger.warning(f"[{i}/{len(episodes)}] Episode missing UID, skipping")
                    stats['failed'] += 1
                    continue

                # Check if already exists
                if skip_existing:
                    existing = self.session.query(PodcastTranscript).filter_by(
                        episode_uid=episode_uid
                    ).first()

                    if existing:
                        logger.debug(f"[{i}/{len(episodes)}] Skipping {episode_uid} (already in DB)")
                        stats['skipped'] += 1
                        continue

                episode_title = episode.get('title', 'Unknown')
                logger.info(f"[{i}/{len(episodes)}] Processing: {episode_title[:60]}...")

                # Fetch transcript
                transcript, metadata, error = self.client.get_episode_transcript(episode_uid)

                # Create database record
                try:
                    record = PodcastTranscript(
                        episode_uid=episode_uid,
                        episode_title=episode_title,
                        podcast_uid=podcast_uid,
                        podcast_title=podcast_title,
                        published_date=episode.get('published'),
                        duration=metadata.get('duration') if metadata else None,
                        transcript_text=transcript,
                        has_transcript=transcript is not None,
                        error_message=error,
                        scraped_at=datetime.utcnow()
                    )

                    self.session.add(record)
                    self.session.commit()

                    if transcript:
                        logger.info(f"  ✓ Saved transcript ({len(transcript)} chars)")
                        stats['success'] += 1
                    else:
                        logger.warning(f"  ✗ No transcript: {error}")
                        stats['failed'] += 1

                except SQLAlchemyError as e:
                    logger.error(f"Database error for {episode_uid}: {e}")
                    self.session.rollback()
                    stats['failed'] += 1
                    continue

                # Rate limiting with random jitter (skip on last episode)
                if i < len(episodes):
                    jittered_delay = self.delay + random.uniform(0, 2)
                    sleep(jittered_delay)

            logger.info(
                f"Scraping complete! Success: {stats['success']}, "
                f"Failed: {stats['failed']}, Skipped: {stats['skipped']}"
            )

            return stats

        except TapeSearchError as e:
            logger.error(f"Failed to scrape podcast: {e}")
            return {'success': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    def scrape_episode(
        self,
        episode_uid: str,
        podcast_title: Optional[str] = None,
        podcast_uid: Optional[str] = None
    ) -> bool:
        """
        Scrape a single episode by UID.

        Args:
            episode_uid: TapeSearch episode UID
            podcast_title: Optional podcast title
            podcast_uid: Optional podcast UID

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Scraping single episode: {episode_uid}")

        # Check if already exists
        existing = self.session.query(PodcastTranscript).filter_by(
            episode_uid=episode_uid
        ).first()

        if existing:
            logger.warning(f"Episode {episode_uid} already exists in database")
            return False

        # Fetch transcript
        transcript, metadata, error = self.client.get_episode_transcript(episode_uid)

        # Create database record
        try:
            record = PodcastTranscript(
                episode_uid=episode_uid,
                episode_title=metadata.get('title') if metadata else 'Unknown',
                podcast_uid=podcast_uid or metadata.get('podcast_uid') if metadata else None,
                podcast_title=podcast_title or metadata.get('podcast_title') if metadata else None,
                published_date=metadata.get('published') if metadata else None,
                duration=metadata.get('duration') if metadata else None,
                transcript_text=transcript,
                has_transcript=transcript is not None,
                error_message=error,
                scraped_at=datetime.utcnow()
            )

            self.session.add(record)
            self.session.commit()

            if transcript:
                logger.info(f"✓ Successfully scraped episode {episode_uid}")
                return True
            else:
                logger.warning(f"✗ No transcript for episode {episode_uid}: {error}")
                return False

        except SQLAlchemyError as e:
            logger.error(f"Database error for {episode_uid}: {e}")
            self.session.rollback()
            return False
