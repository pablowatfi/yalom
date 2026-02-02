"""Check if titles are unique in the database."""
from sqlalchemy import func
from src.database import db, VideoTranscript

db.connect()
session = db.get_session()

# Check if titles are unique
total = session.query(VideoTranscript).count()
unique_titles = session.query(func.count(func.distinct(VideoTranscript.title))).scalar()

print(f'Total records: {total}')
print(f'Unique titles: {unique_titles}')
print(f'Duplicates: {total - unique_titles}')

print('\n--- Sample titles from different sources ---')

# YouTube (has video_id that's not "episode-X")
yt = session.query(VideoTranscript).filter(
    VideoTranscript.video_id.like('%-%')
).filter(
    ~VideoTranscript.video_id.like('episode-%')
).first()
if yt:
    print(f'YouTube: video_id={yt.video_id}, title={yt.title[:80]}')

# Local (episode-X format)
local = session.query(VideoTranscript).filter(
    VideoTranscript.video_id.like('episode-%')
).first()
if local:
    print(f'Local: video_id={local.video_id}, title={local.title[:80]}')

# Check for any duplicate titles
dupes = session.query(
    VideoTranscript.title,
    func.count(VideoTranscript.title)
).group_by(
    VideoTranscript.title
).having(
    func.count(VideoTranscript.title) > 1
).all()

if dupes:
    print(f'\n--- Found {len(dupes)} duplicate titles ---')
    for title, count in dupes[:10]:
        print(f'{count}x: {title[:80]}')
        # Show the video_ids for these duplicates
        records = session.query(VideoTranscript).filter(
            VideoTranscript.title == title
        ).all()
        for r in records:
            print(f'    -> video_id: {r.video_id}')
else:
    print('\n✅ All titles are unique!')

session.close()
