"""
SQLAlchemy database models for YouTube transcripts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VideoTranscript(Base):
    """
    Model for storing YouTube video transcripts and metadata.

    Attributes:
        id: Primary key
        video_id: YouTube video ID (unique)
        title: Video title
        channel_id: YouTube channel ID
        channel_name: Channel name/handle
        upload_date: Video upload date (YYYYMMDD format)
        duration: Video duration in seconds
        view_count: Number of views
        transcript_text: Full transcript text
        transcript_language: Language code of transcript
        has_transcript: Boolean indicating if transcript was successfully fetched
        error_message: Error message if transcript fetch failed
        scraped_at: Timestamp when the record was created
    """
    __tablename__ = 'video_transcripts'

    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), unique=True, nullable=True, index=True)  # Only for YouTube videos
    title = Column(String(500), unique=True, nullable=False, index=True)  # Use title for deduplication
    channel_id = Column(String(100))
    channel_name = Column(String(200), index=True)
    upload_date = Column(String(10))
    duration = Column(Integer)
    view_count = Column(Integer)
    transcript_text = Column(Text)
    transcript_language = Column(String(10))
    has_transcript = Column(Boolean, default=False, index=True)
    error_message = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<VideoTranscript(id={self.id}, title='{self.title[:50]}...')>"

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'upload_date': self.upload_date,
            'duration': self.duration,
            'view_count': self.view_count,
            'transcript_text': self.transcript_text,
            'transcript_language': self.transcript_language,
            'has_transcript': self.has_transcript,
            'error_message': self.error_message,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
        }
