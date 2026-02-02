"""
Yalom - YouTube transcript scraper and analyzer.
"""
__version__ = "0.1.0"

__all__ = [
    "DATABASE_URL",
    "DEFAULT_DELAY_SECONDS",
    "init_db",
    "get_db_session",
    "db",
    "VideoTranscript",
    "ChannelScraper",
    "fetch_transcript",
]


def __getattr__(name):
    if name in {"DATABASE_URL", "DEFAULT_DELAY_SECONDS"}:
        from .config import DATABASE_URL, DEFAULT_DELAY_SECONDS
        return DATABASE_URL if name == "DATABASE_URL" else DEFAULT_DELAY_SECONDS
    if name in {"init_db", "get_db_session", "db", "VideoTranscript"}:
        from .database import init_db, get_db_session, db, VideoTranscript
        return {
            "init_db": init_db,
            "get_db_session": get_db_session,
            "db": db,
            "VideoTranscript": VideoTranscript,
        }[name]
    if name in {"ChannelScraper", "fetch_transcript"}:
        from .ingestion import ChannelScraper, fetch_transcript
        return {
            "ChannelScraper": ChannelScraper,
            "fetch_transcript": fetch_transcript,
        }[name]
    raise AttributeError(f"module 'src' has no attribute {name}")
