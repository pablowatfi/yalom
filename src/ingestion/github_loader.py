"""
Load transcripts from GitHub repositories.
"""
import logging
import re
from typing import List, Dict, Optional
import requests

from ..config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class GitHubTranscriptLoader:
    """Load transcripts from GitHub repositories."""

    def __init__(self, repo: str = "prakhar625/huberman-podcasts-transcripts"):
        """
        Initialize GitHub transcript loader.

        Args:
            repo: GitHub repository in format 'owner/repo'
        """
        self.repo = repo
        self.base_url = f"https://raw.githubusercontent.com/{repo}/main"

    def list_transcripts(self) -> List[Dict]:
        """
        Get list of all available transcripts from README.

        Returns:
            List of dictionaries with transcript metadata
        """
        try:
            # Fetch README
            readme_url = f"{self.base_url}/README.md"
            response = requests.get(readme_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            readme_content = response.text
            transcripts = []

            # Parse markdown table
            # Format: | 04/01/21 | [Title](youtube_url) | 3751 | 1 | [Link](/transcripts/1/1__transcript.txt) |
            pattern = r'\|\s*(\d{2}/\d{2}/\d{2})\s*\|\s*\[([^\]]+)\]\(([^\)]+)\)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\[Link\]\(([^\)]+)\)'

            for match in re.finditer(pattern, readme_content):
                upload_date = match.group(1)
                title = match.group(2)
                youtube_url = match.group(3)
                duration = int(match.group(4))
                episode_num = int(match.group(5))
                transcript_path = match.group(6)

                # Extract video ID from YouTube URL
                video_id = None
                vid_match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', youtube_url)
                if vid_match:
                    video_id = vid_match.group(1)

                transcripts.append({
                    'episode_number': episode_num,
                    'title': title.strip(),
                    'upload_date': upload_date,
                    'duration': duration,
                    'youtube_url': youtube_url,
                    'video_id': video_id,
                    'transcript_path': transcript_path,
                    'github_raw_url': f"{self.base_url}{transcript_path}"
                })

            logger.info(f"Found {len(transcripts)} transcripts in {self.repo}")
            return transcripts

        except requests.RequestException as e:
            logger.error(f"Failed to fetch README: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing README: {e}", exc_info=True)
            return []

    def load_transcript(self, transcript_path: str) -> Optional[str]:
        """
        Load transcript text from GitHub.

        Args:
            transcript_path: Path to transcript file (e.g., '/transcripts/1/1__transcript.txt')

        Returns:
            Transcript text or None if failed
        """
        try:
            url = f"{self.base_url}{transcript_path}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            transcript_text = response.text
            logger.info(f"Loaded transcript from {transcript_path} ({len(transcript_text)} chars)")
            return transcript_text

        except requests.RequestException as e:
            logger.error(f"Failed to load transcript from {transcript_path}: {e}")
            return None

    def load_transcript_by_episode(self, episode_number: int) -> Optional[Dict]:
        """
        Load transcript by episode number.

        Args:
            episode_number: Episode number

        Returns:
            Dictionary with metadata and transcript text, or None if not found
        """
        transcripts = self.list_transcripts()

        for transcript in transcripts:
            if transcript['episode_number'] == episode_number:
                text = self.load_transcript(transcript['transcript_path'])
                if text:
                    transcript['transcript_text'] = text
                    return transcript

        logger.warning(f"Episode {episode_number} not found")
        return None

    def load_all_transcripts(
        self,
        start_episode: Optional[int] = None,
        end_episode: Optional[int] = None
    ) -> List[Dict]:
        """
        Load multiple transcripts.

        Args:
            start_episode: Start episode number (inclusive), None for first
            end_episode: End episode number (inclusive), None for last

        Returns:
            List of dictionaries with metadata and transcript text
        """
        transcripts = self.list_transcripts()
        results = []

        for transcript in transcripts:
            episode_num = transcript['episode_number']

            # Filter by episode range
            if start_episode is not None and episode_num < start_episode:
                continue
            if end_episode is not None and episode_num > end_episode:
                continue

            logger.info(f"Loading episode {episode_num}: {transcript['title'][:60]}...")

            text = self.load_transcript(transcript['transcript_path'])
            if text:
                transcript['transcript_text'] = text
                results.append(transcript)
            else:
                logger.warning(f"Failed to load episode {episode_num}")

        logger.info(f"Successfully loaded {len(results)} transcripts")
        return results

    def search_transcripts(self, query: str) -> List[Dict]:
        """
        Search for episodes by title.

        Args:
            query: Search query string

        Returns:
            List of matching transcript metadata
        """
        transcripts = self.list_transcripts()
        query_lower = query.lower()

        matches = [
            t for t in transcripts
            if query_lower in t['title'].lower()
        ]

        logger.info(f"Found {len(matches)} episodes matching '{query}'")
        return matches
