"""
YouTube channel scraping functionality.
"""
import logging
from time import sleep
from datetime import datetime
from typing import List, Dict, Optional
import random

import yt_dlp
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import YT_DLP_OPTIONS, DEFAULT_DELAY_SECONDS
from ..database import VideoTranscript
from .youtube_fetcher import fetch_transcript

logger = logging.getLogger(__name__)


class ChannelScraper:
    """Scraper for YouTube channel transcripts."""

    def __init__(self, session: Session, delay: float = DEFAULT_DELAY_SECONDS):
        """
        Initialize the scraper.

        Args:
            session: SQLAlchemy database session
            delay: Delay in seconds between video fetches (to avoid rate limiting)
        """
        self.session = session
        self.delay = delay

    def get_channel_videos(self, channel_url: str) -> List[Dict]:
        """
        Fetch all video metadata from a YouTube channel.

        Args:
            channel_url: YouTube channel URL (e.g., 'https://www.youtube.com/@channelname')

        Returns:
            List of dictionaries containing video metadata

        Raises:
            yt_dlp.utils.DownloadError: If channel cannot be accessed
        """
        logger.info(f"Fetching videos from channel: {channel_url}")

        ydl_opts = {
            **YT_DLP_OPTIONS,
            'extract_flat': 'in_playlist',  # Get all videos from playlists
            'playlistend': None,  # Get all videos
        }

        videos = []

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Add /videos to get the videos tab specifically
                videos_url = channel_url.rstrip('/') + '/videos'

                logger.debug(f"Fetching from: {videos_url}")
                info = ydl.extract_info(videos_url, download=False)

                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            # Skip if it's a channel ID (starts with UC)
                            video_id = entry.get('id')
                            if video_id and not video_id.startswith('UC'):
                                videos.append({
                                    'video_id': video_id,
                                    'title': entry.get('title'),
                                    'duration': entry.get('duration'),
                                    'upload_date': entry.get('upload_date'),
                                    'view_count': entry.get('view_count'),
                                    'channel_id': entry.get('channel_id'),
                                    'url': f"https://www.youtube.com/watch?v={video_id}"
                                })
                return videos

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Failed to fetch channel videos: {e}")
            raise

    def scrape_channel(
        self,
        channel_url: str,
        skip_existing: bool = True,
        max_videos: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Scrape all videos from a channel and save transcripts to database.

        Args:
            channel_url: YouTube channel URL
            skip_existing: If True, skip videos already in database
            max_videos: Maximum number of videos to process (None for all)

        Returns:
            Dictionary with scraping statistics:
            - success: Number of transcripts successfully fetched
            - failed: Number of videos without transcripts
            - skipped: Number of videos skipped (already in DB)
            - total: Total number of videos processed
        """
        logger.info(f"Starting channel scrape: {channel_url}")

        # Extract channel name from URL
        channel_name = channel_url.rstrip('/').split('/')[-1]

        # Get all videos from channel
        try:
            videos = self.get_channel_videos(channel_url)
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            raise

        # Limit number of videos if specified
        if max_videos:
            videos = videos[:max_videos]
            logger.info(f"Limited to {max_videos} videos")

        # Process each video
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total': len(videos)
        }

        for i, video in enumerate(videos, 1):
            video_id = video['video_id']

            # Check if already exists by title
            if skip_existing:
                existing = self.session.query(VideoTranscript).filter_by(
                    title=video['title']
                ).first()

                if existing:
                    logger.debug(f"[{i}/{len(videos)}] Skipping {video_id} (already in DB)")
                    stats['skipped'] += 1
                    continue

            logger.info(f"[{i}/{len(videos)}] Processing: {video['title'][:60]}...")

            # Fetch transcript
            transcript, lang, error = fetch_transcript(video_id)

            # Create database record
            try:
                record = VideoTranscript(
                    video_id=video_id,
                    title=video['title'],
                    channel_id=video.get('channel_id'),
                    channel_name=channel_name,
                    upload_date=video.get('upload_date'),
                    duration=video.get('duration'),
                    view_count=video.get('view_count'),
                    transcript_text=transcript,
                    transcript_language=lang,
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
                logger.error(f"Database error for {video_id}: {e}")
                self.session.rollback()
                stats['failed'] += 1
                continue

            # Rate limiting with random jitter (skip on last video)
            if i < len(videos):
                jittered_delay = self.delay + random.uniform(0, 5)
                sleep(jittered_delay)

        logger.info(
            f"Scraping complete! Success: {stats['success']}, "
            f"Failed: {stats['failed']}, Skipped: {stats['skipped']}"
        )

        return stats

    def scrape_video(
        self,
        video_id: str,
        video_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Scrape a single video by ID.

        Args:
            video_id: YouTube video ID
            video_metadata: Optional metadata dict (if not provided, will be fetched)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Scraping single video: {video_id}")

        # Check if already exists by title
        video_title = video_metadata.get('title') if video_metadata else None
        if video_title:
            existing = self.session.query(VideoTranscript).filter_by(
                title=video_title
            ).first()
        else:
            existing = None

        if existing:
            logger.warning(f"Video {video_id} already exists in database")
            return False

        # Fetch transcript
        transcript, lang, error = fetch_transcript(video_id)

        # Get metadata if not provided
        if not video_metadata:
            video_metadata = self._get_video_metadata(video_id)

        # Create database record
        try:
            record = VideoTranscript(
                video_id=video_id,
                title=video_metadata.get('title'),
                channel_id=video_metadata.get('channel_id'),
                channel_name=video_metadata.get('channel_name'),
                upload_date=video_metadata.get('upload_date'),
                duration=video_metadata.get('duration'),
                view_count=video_metadata.get('view_count'),
                transcript_text=transcript,
                transcript_language=lang,
                has_transcript=transcript is not None,
                error_message=error,
                scraped_at=datetime.utcnow()
            )

            self.session.add(record)
            self.session.commit()

            if transcript:
                logger.info(f"✓ Successfully scraped video {video_id}")
                return True
            else:
                logger.warning(f"✗ No transcript for video {video_id}: {error}")
                return False

        except SQLAlchemyError as e:
            logger.error(f"Database error for {video_id}: {e}")
            self.session.rollback()
            return False

    def _get_video_metadata(self, video_id: str) -> Dict:
        """Fetch metadata for a single video."""
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            **YT_DLP_OPTIONS,
            'skip_download': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                return {
                    'title': info.get('title'),
                    'channel_id': info.get('channel_id'),
                    'channel_name': info.get('channel'),
                    'upload_date': info.get('upload_date'),
                    'duration': info.get('duration'),
                    'view_count': info.get('view_count'),
                }
        except Exception as e:
            logger.error(f"Failed to get metadata for {video_id}: {e}")
            return {}
