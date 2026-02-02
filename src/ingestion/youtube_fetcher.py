"""
YouTube transcript fetching functionality.
"""
import json
import re
import logging
import time
import random
from typing import Optional, Tuple

import yt_dlp
import requests

from ..config import YT_DLP_OPTIONS, DEFAULT_LANGUAGE, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, RETRY_COOLDOWN

logger = logging.getLogger(__name__)


class TranscriptFetchError(Exception):
    """Custom exception for transcript fetching errors."""
    pass


def fetch_transcript(
    video_id: str,
    language: str = DEFAULT_LANGUAGE
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Fetch transcript for a single YouTube video.

    Args:
        video_id: YouTube video ID
        language: Language code for transcript (default: 'en')

    Returns:
        Tuple of (transcript_text, language_info, error_message)
        - transcript_text: Full transcript as string, or None if failed
        - language_info: Language description (e.g., 'en (auto)'), or None if failed
        - error_message: Error description if failed, or None if successful
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        **YT_DLP_OPTIONS,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [language],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.debug(f"Extracting info for video: {video_id}")
            info = ydl.extract_info(video_url, download=False)

            # Try to get subtitles
            subtitle_info = None
            lang_info = None

            if 'subtitles' in info and language in info['subtitles']:
                subtitle_info = info['subtitles'][language]
                lang_info = f'{language} (manual)'
                logger.debug(f"Found manual subtitles for {video_id}")
            elif 'automatic_captions' in info and language in info['automatic_captions']:
                subtitle_info = info['automatic_captions'][language]
                lang_info = f'{language} (auto)'
                logger.debug(f"Found automatic captions for {video_id}")
            else:
                logger.warning(f"No transcript available for {video_id}")
                return None, None, f"No transcript available in {language}"

            # Find best format (prefer json3)
            subtitle_url = _get_subtitle_url(subtitle_info)

            # Fetch and parse transcript
            transcript_text = _fetch_and_parse_subtitle(subtitle_url)

            logger.info(f"Successfully fetched transcript for {video_id} ({len(transcript_text)} chars)")
            return transcript_text, lang_info, None

    except yt_dlp.utils.DownloadError as e:
        error_msg = f"yt-dlp download error: {str(e)}"
        logger.error(f"Failed to fetch {video_id}: {error_msg}")
        return None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Failed to fetch {video_id}: {error_msg}", exc_info=True)
        return None, None, error_msg


def _get_subtitle_url(subtitle_info: list) -> str:
    """
    Extract the best subtitle URL from subtitle info.

    Args:
        subtitle_info: List of subtitle format dictionaries

    Returns:
        URL string for the subtitle file
    """
    # Prefer json3 format
    for fmt in subtitle_info:
        if fmt.get('ext') == 'json3':
            return fmt['url']

    # Fallback to first available format
    return subtitle_info[0]['url']


def _fetch_and_parse_subtitle(url: str) -> str:
    """
    Fetch and parse subtitle content from URL with retry logic.

    Args:
        url: Subtitle file URL

    Returns:
        Parsed transcript text

    Raises:
        TranscriptFetchError: If fetching or parsing fails after retries
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Try parsing as JSON (json3 format)
            try:
                data = json.loads(response.text)
                return _parse_json3_transcript(data)
            except json.JSONDecodeError:
                # Try parsing as XML
                logger.debug("JSON parsing failed, trying XML")
                return _parse_xml_transcript(response.content)

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit hit - use exponential backoff
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 10)
                    logger.warning(f"Rate limit hit (429), retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    last_error = e
                    continue
                else:
                    # Exhausted all retries - apply cooldown before raising
                    logger.warning(f"Exhausted all retries for rate limit. Cooling down for {RETRY_COOLDOWN}s")
                    time.sleep(RETRY_COOLDOWN)
            last_error = e
            break
        except requests.RequestException as e:
            last_error = e
            break

    raise TranscriptFetchError(f"Failed to fetch subtitle: {last_error}")
def _parse_json3_transcript(data: dict) -> str:
    """
    Parse JSON3 format transcript.

    Args:
        data: Parsed JSON data

    Returns:
        Transcript text as string
    """
    text_parts = []

    if 'events' in data:
        for event in data['events']:
            if 'segs' in event:
                for seg in event['segs']:
                    if 'utf8' in seg:
                        text_parts.append(seg['utf8'])

    transcript_text = " ".join(text_parts).strip()
    # Clean up extra whitespace
    transcript_text = re.sub(r'\s+', ' ', transcript_text)

    return transcript_text


def _parse_xml_transcript(content: bytes) -> str:
    """
    Parse XML format transcript.

    Args:
        content: XML content as bytes

    Returns:
        Transcript text as string
    """
    from xml.etree import ElementTree

    root = ElementTree.fromstring(content)
    text_parts = [
        elem.text.strip()
        for elem in root.findall('.//text')
        if elem.text
    ]

    transcript_text = " ".join(text_parts)
    # Clean up extra whitespace
    transcript_text = re.sub(r'\s+', ' ', transcript_text)

    return transcript_text
