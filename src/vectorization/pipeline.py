"""
End-to-end pipeline for vectorizing transcripts.

Process flow:
1. Fetch transcripts from PostgreSQL
2. Chunk text using LangChain
3. Generate embeddings
4. Store in Qdrant vector database
"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from ..database import VideoTranscript
from .chunking import chunk_transcript
from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class VectorizationPipeline:
    """Pipeline for converting transcripts to searchable vectors."""

    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "recursive"
    ):
        """
        Initialize vectorization pipeline.

        Args:
            vector_store_manager: Vector store manager instance
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            chunking_strategy: Chunking strategy ("recursive", "character", "token")
        """
        self.vector_store = vector_store_manager
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy

        logger.info(
            f"Initialized VectorizationPipeline: "
            f"chunk_size={chunk_size}, overlap={chunk_overlap}, "
            f"strategy={chunking_strategy}"
        )

    def process_transcript(
        self,
        transcript: VideoTranscript,
        additional_metadata: Optional[Dict] = None
    ) -> int:
        """
        Process a single transcript: chunk, embed, and store.

        Args:
            transcript: VideoTranscript from database
            additional_metadata: Extra metadata to attach to chunks

        Returns:
            Number of chunks created
        """
        # Use database id as transcript identifier
        transcript_id = str(transcript.id)
        logger.info(f"Processing transcript: {transcript.title[:60]}...")

        # Prepare metadata
        metadata = {
            "transcript_id": transcript.id,
            "title": transcript.title,
            "channel_name": transcript.channel_name,
        }
        if additional_metadata:
            metadata.update(additional_metadata)

        # Chunk the transcript
        chunks = chunk_transcript(
            text=transcript.transcript_text,
            transcript_id=transcript_id,
            metadata=metadata,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            strategy=self.chunking_strategy
        )

        # Add to vector store
        self.vector_store.add_documents(chunks)

        logger.info(f"Processed {len(chunks)} chunks for {transcript_id}")
        return len(chunks)

    def process_transcripts_batch(
        self,
        session: Session,
        transcript_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        skip_existing: bool = True
    ) -> Dict[str, int]:
        """
        Process multiple transcripts in batch.

        Args:
            session: SQLAlchemy database session
            transcript_ids: Optional list of specific transcript IDs to process
            limit: Maximum number of transcripts to process
            skip_existing: Skip transcripts already in vector store
        """
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_chunks": 0
        }

        # Build query
        query = session.query(VideoTranscript).filter(
            VideoTranscript.has_transcript
        )

        if transcript_ids:
            # transcript_ids can be titles or video_ids
            query = query.filter(
                (VideoTranscript.title.in_(transcript_ids)) |
                (VideoTranscript.video_id.in_(transcript_ids))
            )

        if limit:
            query = query.limit(limit)

        transcripts = query.all()
        logger.info(f"Found {len(transcripts)} transcripts to process")

        for i, transcript in enumerate(transcripts, 1):
            try:
                # Check if already processed (if skip_existing is True)
                if skip_existing and self.vector_store.transcript_exists(transcript.id):
                    logger.info(f"[{i}/{len(transcripts)}] Skipping (already exists): {transcript.title[:60]}...")
                    stats["skipped"] += 1
                    continue

                logger.info(f"[{i}/{len(transcripts)}] Processing: {transcript.title[:60]}...")

                num_chunks = self.process_transcript(transcript)

                stats["success"] += 1
                stats["total_chunks"] += num_chunks

            except Exception as e:
                import traceback
                print(f"Failed to process '{transcript.title[:60]}...': {e}")
                traceback.print_exc()
                logger.error(f"Failed to process {transcript.title}: {e}")
                stats["failed"] += 1

        logger.info(
            f"Batch processing complete: "
            f"success={stats['success']}, failed={stats['failed']}, "
            f"total_chunks={stats['total_chunks']}"
        )

        return stats

    def reprocess_transcript(
        self,
        session: Session,
        identifier: str
    ) -> bool:
        """
        Reprocess a specific transcript (delete old chunks and re-embed).

        Args:
            session: Database session
            identifier: Title, video_id, or db id (as 'db-123')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get transcript by title or video_id
            transcript = session.query(VideoTranscript).filter(
                (VideoTranscript.title == identifier) |
                (VideoTranscript.video_id == identifier)
            ).first()

            if not transcript:
                logger.error(f"Transcript not found: {identifier}")
                return False

            # Delete existing chunks using database ID
            self.vector_store.delete_by_transcript_id(str(transcript.id))

            # Reprocess
            self.process_transcript(transcript)
            logger.info(f"Successfully reprocessed {identifier}")
            return True

        except Exception as e:
            logger.error(f"Error reprocessing {identifier}: {e}")
            return False
