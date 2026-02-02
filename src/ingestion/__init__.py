"""
Data loaders for various transcript sources.
"""
from .youtube_scraper import ChannelScraper
from .youtube_fetcher import fetch_transcript
from .github_scraper import GitHubScraper
from .github_loader import GitHubTranscriptLoader
from .kaggle_scraper import KaggleScraper
from .kaggle_loader import KaggleTranscriptLoader
from .tapesearch_scraper import TapeSearchScraper
from .tapesearch_fetcher import TapeSearchClient

__all__ = [
    'ChannelScraper',
    'fetch_transcript',
    'GitHubScraper',
    'GitHubTranscriptLoader',
    'KaggleScraper',
    'KaggleTranscriptLoader',
    'TapeSearchScraper',
    'TapeSearchClient',
]
