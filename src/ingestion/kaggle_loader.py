"""
Load transcripts from Kaggle dataset.
"""
import logging
import json
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class KaggleTranscriptLoader:
    """Load transcripts from downloaded Kaggle dataset."""

    def __init__(self, dataset_path: str):
        """
        Initialize Kaggle transcript loader.

        Args:
            dataset_path: Path to extracted Kaggle dataset (HubermanLabTranscripts folder)
        """
        self.dataset_path = Path(dataset_path)
        self.text_dir = self.dataset_path / "text"
        self.video_id_file = self.dataset_path / "videoID.json"
        self.timestamped_dir = self.dataset_path / "TimestampedTranscriptions"

        # Load video ID mapping
        self.video_metadata = {}
        if self.video_id_file.exists():
            with open(self.video_id_file, 'r', encoding='utf-8') as f:
                self.video_metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.video_metadata)} videos")

    def list_transcripts(self) -> List[Dict]:
        """
        Get list of all available transcripts.

        Returns:
            List of dictionaries with transcript metadata
        """
        transcripts = []

        if not self.text_dir.exists():
            logger.error(f"Text directory not found: {self.text_dir}")
            return transcripts

        for filename in sorted(self.text_dir.glob("*.txt")):
            video_id = filename.stem
            title = self.video_metadata.get(video_id, f"Episode {video_id}")

            transcripts.append({
                'video_id': video_id,
                'title': title,
                'filepath': str(filename),
                'has_timestamps': self._has_timestamps(video_id)
            })

        logger.info(f"Found {len(transcripts)} transcripts in Kaggle dataset")
        return transcripts

    def _has_timestamps(self, video_id: str) -> bool:
        """Check if timestamped version exists."""
        if not self.timestamped_dir.exists():
            return False

        json_file = self.timestamped_dir / "json" / f"{video_id}.json"
        return json_file.exists()

    def load_transcript(self, video_id: str) -> Optional[str]:
        """
        Load transcript text.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if not found
        """
        filepath = self.text_dir / f"{video_id}.txt"

        if not filepath.exists():
            logger.error(f"Transcript file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            logger.info(f"Loaded transcript for {video_id} ({len(transcript_text)} chars)")
            return transcript_text

        except Exception as e:
            logger.error(f"Error reading transcript {video_id}: {e}")
            return None

    def load_timestamped_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """
        Load timestamped transcript segments.

        Args:
            video_id: YouTube video ID

        Returns:
            List of segments with timestamps, or None if not found
        """
        json_file = self.timestamped_dir / "json" / f"{video_id}.json"

        if not json_file.exists():
            logger.debug(f"Timestamped transcript not found: {json_file}")
            return None

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse JSON format - structure may vary, adapt as needed
            segments = []
            if isinstance(data, list):
                for item in data:
                    segments.append({
                        'start': item.get('start', 0),
                        'duration': item.get('duration', 0),
                        'text': item.get('text', '')
                    })
            elif isinstance(data, dict) and 'segments' in data:
                segments = data['segments']

            logger.info(f"Loaded {len(segments)} timestamped segments for {video_id}")
            return segments

        except Exception as e:
            logger.error(f"Error reading timestamped transcript {video_id}: {e}")
            return None

    def get_video_title(self, video_id: str) -> str:
        """Get video title from metadata."""
        return self.video_metadata.get(video_id, f"Episode {video_id}")

    def load_all_transcripts(self) -> List[Dict]:
        """
        Load all transcripts with metadata.

        Returns:
            List of dictionaries with video_id, title, transcript_text, and optional timestamps
        """
        transcripts = self.list_transcripts()
        results = []

        for transcript_info in transcripts:
            video_id = transcript_info['video_id']

            logger.info(f"Loading {transcript_info['title'][:60]}...")

            # Load plain text
            transcript_text = self.load_transcript(video_id)
            if not transcript_text:
                continue

            # Load timestamps if available
            timestamps = None
            if transcript_info['has_timestamps']:
                timestamps = self.load_timestamped_transcript(video_id)

            results.append({
                'video_id': video_id,
                'title': transcript_info['title'],
                'transcript_text': transcript_text,
                'timestamps': timestamps
            })

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
