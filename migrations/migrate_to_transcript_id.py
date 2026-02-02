"""
Migration script to add transcript_id column and populate from existing video_id data.

This script:
1. Adds the transcript_id column to the database (if not exists)
2. Populates transcript_id from existing video_id values
3. Updates video_id to NULL for non-YouTube transcripts
"""
import sys
from sqlalchemy import text

from src.database import db, VideoTranscript


def migrate():
    """Run the migration."""
    db.connect()
    session = db.get_session()

    try:
        print("Starting migration to transcript_id...")

        # Step 1: Add transcript_id column if it doesn't exist
        print("\n1. Adding transcript_id column...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ADD COLUMN IF NOT EXISTS transcript_id VARCHAR(100);
            """))
            session.commit()
            print("   ✓ Column added")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 2: Populate transcript_id from video_id
        print("\n2. Populating transcript_id from video_id...")
        session.execute(text("""
            UPDATE video_transcripts
            SET transcript_id = video_id
            WHERE transcript_id IS NULL;
        """))
        session.commit()

        count = session.query(VideoTranscript).filter(
            VideoTranscript.transcript_id.isnot(None)
        ).count()
        print(f"   ✓ Updated {count} records")

        # Step 3: Add unique constraint and index on transcript_id
        print("\n3. Adding constraints...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ADD CONSTRAINT video_transcripts_transcript_id_key
                UNIQUE (transcript_id);
            """))
            session.commit()
            print("   ✓ Unique constraint added")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_transcript_id
                ON video_transcripts(transcript_id);
            """))
            session.commit()
            print("   ✓ Index added")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 4: Remove NOT NULL constraint from video_id
        print("\n4. Removing NOT NULL constraint from video_id...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ALTER COLUMN video_id DROP NOT NULL;
            """))
            session.commit()
            print("   ✓ NOT NULL constraint removed from video_id")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 5: Set video_id to NULL for non-YouTube transcripts
        print("\n5. Cleaning up video_id for non-YouTube transcripts...")
        result = session.execute(text("""
            UPDATE video_transcripts
            SET video_id = NULL
            WHERE transcript_id LIKE 'episode-%'
               OR transcript_id NOT LIKE '%-___________'
            RETURNING transcript_id;
        """))
        updated_ids = result.fetchall()
        session.commit()
        print(f"   ✓ Cleared video_id for {len(updated_ids)} non-YouTube transcripts")

        # Step 6: Make transcript_id NOT NULL
        print("\n6. Setting transcript_id to NOT NULL...")
        try:
            session.execute(text("""
                ALTER TABLE video_transcripts
                ALTER COLUMN transcript_id SET NOT NULL;
            """))
            session.commit()
            print("   ✓ NOT NULL constraint added")
        except Exception as e:
            print(f"   Note: {e}")
            session.rollback()

        # Step 6: Verify migration
        print("\n6. Verifying migration...")
        total = session.query(VideoTranscript).count()
        with_transcript_id = session.query(VideoTranscript).filter(
            VideoTranscript.transcript_id.isnot(None)
        ).count()
        youtube_videos = session.query(VideoTranscript).filter(
            VideoTranscript.video_id.isnot(None)
        ).count()

        print(f"\n   Total transcripts: {total}")
        print(f"   With transcript_id: {with_transcript_id}")
        print(f"   YouTube videos (with video_id): {youtube_videos}")
        print(f"   Non-YouTube transcripts: {total - youtube_videos}")

        if with_transcript_id == total:
            print("\n✅ Migration completed successfully!")
            return True
        else:
            print(f"\n⚠️  Warning: {total - with_transcript_id} records missing transcript_id")
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
