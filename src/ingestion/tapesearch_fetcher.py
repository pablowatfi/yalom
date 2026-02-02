"""
TapeSearch API integration for fetching podcast transcripts.
"""
import logging
from typing import Optional, List, Dict, Tuple
import requests

from ..config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class TapeSearchError(Exception):
    """Custom exception for TapeSearch API errors."""
    pass


class TapeSearchClient:
    """Client for interacting with TapeSearch API."""

    def __init__(self, api_key: str):
        """
        Initialize TapeSearch client.

        Args:
            api_key: TapeSearch API key
        """
        self.api_key = api_key
        self.base_url = "https://api.tapesearch.com/v1/public"
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def search_podcast(self, query: str) -> List[Dict]:
        """
        Search for podcasts by title or publisher.

        Args:
            query: Search query string

        Returns:
            List of podcast dictionaries with details

        Raises:
            TapeSearchError: If API request fails
        """
        url = f"{self.base_url}/podcast_search"
        params = {"query": query}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"Found {len(data)} podcasts matching '{query}'")
            return data

        except requests.RequestException as e:
            error_msg = f"Failed to search podcasts: {e}"
            logger.error(error_msg)
            raise TapeSearchError(error_msg)

    def get_podcast_episodes(self, podcast_uid: str) -> Dict:
        """
        Get all episodes for a podcast.

        Args:
            podcast_uid: Unique podcast identifier from TapeSearch

        Returns:
            Dictionary with podcast details and episode list

        Raises:
            TapeSearchError: If API request fails
        """
        url = f"{self.base_url}/podcast"
        params = {"uid": podcast_uid}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            episodes = data.get('episodes', [])
            logger.info(f"Found {len(episodes)} episodes for podcast {podcast_uid}")
            return data

        except requests.RequestException as e:
            error_msg = f"Failed to fetch podcast episodes: {e}"
            logger.error(error_msg)
            raise TapeSearchError(error_msg)

    def get_episode_transcript(
        self,
        episode_uid: str
    ) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Fetch full transcript for a podcast episode.

        Args:
            episode_uid: Unique episode identifier from TapeSearch

        Returns:
            Tuple of (transcript_text, episode_metadata, error_message)
            - transcript_text: Full transcript as string, or None if failed
            - episode_metadata: Episode metadata dict, or None if failed
            - error_message: Error description if failed, or None if successful
        """
        url = f"{self.base_url}/episode"
        params = {"uid": episode_uid}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            episode_data = data.get('e', {})
            transcript_segments = episode_data.get('transcript', [])

            if not transcript_segments:
                logger.warning(f"No transcript available for episode {episode_uid}")
                return None, episode_data, "No transcript available"

            # Combine transcript segments into full text
            transcript_text = ' '.join(
                segment.get('text', '') for segment in transcript_segments
            )

            logger.info(f"Successfully fetched transcript for {episode_uid} ({len(transcript_text)} chars)")
            return transcript_text, episode_data, None

        except requests.RequestException as e:
            error_msg = f"Failed to fetch episode transcript: {e}"
            logger.error(error_msg)
            return None, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg, exc_info=True)
            return None, None, error_msg

    def search_episodes(
        self,
        query: str,
        podcast_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search for episodes containing specific text.

        Args:
            query: Search query string
            podcast_filter: Optional podcast name to filter results
            limit: Maximum number of results (default: 100)

        Returns:
            List of episode dictionaries with highlights

        Raises:
            TapeSearchError: If API request fails
        """
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "limit": limit
        }

        if podcast_filter:
            params["podcast"] = podcast_filter

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            logger.info(f"Found {len(results)} episodes matching '{query}'")
            return results

        except requests.RequestException as e:
            error_msg = f"Failed to search episodes: {e}"
            logger.error(error_msg)
            raise TapeSearchError(error_msg)

    def get_database_counts(self) -> Dict:
        """
        Get counts of podcasts, episodes, and transcripts in database.

        Returns:
            Dictionary with database statistics

        Raises:
            TapeSearchError: If API request fails
        """
        url = f"{self.base_url}/count"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            error_msg = f"Failed to get database counts: {e}"
            logger.error(error_msg)
            raise TapeSearchError(error_msg)
