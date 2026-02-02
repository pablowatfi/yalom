"""
Database models for TapeSearch podcast transcripts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PodcastTranscript(Base):
    """Model for storing podcast episode transcripts from TapeSearch."""

    __tablename__ = 'podcast_transcripts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Episode identifiers
    episode_uid = Column(String(100), unique=True, nullable=False, index=True)
    episode_title = Column(String(500))

    # Podcast information
    podcast_uid = Column(String(100), index=True)
    podcast_title = Column(String(500))

    # Episode metadata
    published_date = Column(String(50))  # Store as string since format varies
    duration = Column(Integer)  # Duration in seconds

    # Transcript data
    transcript_text = Column(Text)
    has_transcript = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text)

    # Scraping metadata
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PodcastTranscript(episode_uid='{self.episode_uid}', title='{self.episode_title}')>"

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'episode_uid': self.episode_uid,
            'episode_title': self.episode_title,
            'podcast_uid': self.podcast_uid,
            'podcast_title': self.podcast_title,
            'published_date': self.published_date,
            'duration': self.duration,
            'transcript_text': self.transcript_text,
            'has_transcript': self.has_transcript,
            'error_message': self.error_message,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None
        }
