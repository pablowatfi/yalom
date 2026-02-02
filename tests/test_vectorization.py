from src.vectorization.chunking import (
    chunk_transcript,
    chunk_transcripts_batch,
    get_chunking_config,
)


def test_chunk_transcript_adds_metadata_and_indices():
    text = "A B C D E F G H I J K L M N O P Q R S T U V"
    chunks = chunk_transcript(
        text=text,
        transcript_id="t1",
        metadata={"title": "Episode 1"},
        chunk_size=10,
        chunk_overlap=0,
        strategy="recursive",
    )

    assert len(chunks) > 1
    assert all("transcript_id" in c.metadata for c in chunks)
    assert chunks[0].metadata["transcript_id"] == "t1"
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["total_chunks"] == len(chunks)


def test_chunk_transcripts_batch_combines_results():
    transcripts = [
        {"text": "hello world from huberman lab", "transcript_id": "t1"},
        {"text": "another transcript with more words", "transcript_id": "t2"},
    ]
    chunks = chunk_transcripts_batch(transcripts, chunk_size=10, chunk_overlap=0, strategy="recursive")

    assert len(chunks) > 2
    ids = {c.metadata["transcript_id"] for c in chunks}
    assert ids == {"t1", "t2"}


def test_get_chunking_config_returns_copy():
    config = get_chunking_config("qa")
    assert config["chunk_size"] > 0
    config["chunk_size"] = 1
    assert get_chunking_config("qa")["chunk_size"] != 1
