"""
Migration script to use title for deduplication instead of transcript_id.

This script:
1. Makes video_id nullable (only for YouTube videos)
2. Adds unique constraint on title
3. Creates index on title for fast lookups
"""
import sys
from sqlalchemy import text

from src.database import db, VideoTranscript


def migrate():
    """Run the migration."""
    db.connect()
    session = db.get_session()

    try:
        print("Starting migration to use title for deduplication...")

        # Step 1: Remove NOT NULL constraint from video_id
        print("\n1. Making video_id nullable...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ALTER COLUMN video_id DROP NOT NULL;
            """))
            session.commit()
            print("   ✓ video_id is now nullable")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 2: Add unique constraint on title
        print("\n2. Adding unique constraint on title...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ADD CONSTRAINT video_transcripts_title_key
                UNIQUE (title);
            """))
            session.commit()
            print("   ✓ Unique constraint added on title")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 3: Create index on title if not exists
        print("\n3. Creating index on title...")
        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_title
                ON video_transcripts(title);
            """))
            session.commit()
            print("   ✓ Index created on title")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 4: Verify migration
        print("\n4. Verifying migration...")
        total = session.query(VideoTranscript).count()
        with_title = session.query(VideoTranscript).filter(
            VideoTranscript.title.isnot(None)
        ).count()
        with_video_id = session.query(VideoTranscript).filter(
            VideoTranscript.video_id.isnot(None)
        ).count()

        print(f"\n   Total transcripts: {total}")
        print(f"   With title: {with_title}")
        print(f"   With video_id (YouTube): {with_video_id}")
        print(f"   Without video_id (local/GitHub): {total - with_video_id}")

        # Check for duplicate titles
        from sqlalchemy import func
        dupes = session.query(
            VideoTranscript.title,
            func.count(VideoTranscript.title)
        ).group_by(
            VideoTranscript.title
        ).having(
            func.count(VideoTranscript.title) > 1
        ).all()

        if dupes:
            print(f"\n   ⚠️  Warning: {len(dupes)} duplicate titles found!")
            for title, count in dupes[:5]:
                print(f"      {count}x: {title[:70]}")
        else:
            print("   ✓ All titles are unique")

        if with_title == total and len(dupes) == 0:
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("  - All loaders now check for duplicates by title")
            print("  - video_id is only set for YouTube videos")
            print("  - Title is the primary deduplication key")
            return True
        else:
            print("\n⚠️  Warning: Some issues detected")
            return False

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
