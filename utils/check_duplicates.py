#!/usr/bin/env python3
"""Check for duplicate episodes in the database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import db, VideoTranscript
from sqlalchemy import func

db.connect()
session = db.get_session()

# Check for duplicate titles
print("Checking for duplicate episode titles...")
print()

duplicates = session.query(
    VideoTranscript.title,
    func.count(VideoTranscript.title).label('count')
).group_by(VideoTranscript.title).having(func.count(VideoTranscript.title) > 1).all()

if duplicates:
    print(f'❌ Found {len(duplicates)} duplicate episode titles:\n')
    for title, count in duplicates:
        print(f'  "{title}" appears {count} times')
        # Show the video_ids for each duplicate
        episodes = session.query(VideoTranscript).filter(VideoTranscript.title == title).all()
        for ep in episodes:
            print(f'    - video_id: {ep.video_id}, scraped: {ep.scraped_at}')
        print()
else:
    print('✅ No duplicate episode titles found!')

print()
print("="*60)

# Show distribution by source
print('Distribution by source:')
episode_prefix = session.query(VideoTranscript).filter(VideoTranscript.video_id.like('episode-%')).count()
youtube_ids = session.query(VideoTranscript).filter(~VideoTranscript.video_id.like('episode-%')).count()

print(f'  - Local episodes (episode-N): {episode_prefix}')
print(f'  - YouTube/GitHub (video IDs): {youtube_ids}')
print(f'  - Total: {episode_prefix + youtube_ids}')

session.close()
