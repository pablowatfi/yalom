import importlib
import sys
import types
from types import SimpleNamespace


def _load_pipeline_module():
    fake_chunking = types.ModuleType("src.vectorization.chunking")
    fake_chunking.chunk_transcript = lambda **kwargs: []
    sys.modules["src.vectorization.chunking"] = fake_chunking
    module = importlib.import_module("src.vectorization.pipeline")
    return importlib.reload(module)


def test_process_transcript_chunks_and_stores(monkeypatch):
    module = _load_pipeline_module()
    pipeline = module.VectorizationPipeline.__new__(module.VectorizationPipeline)
    pipeline.vector_store = SimpleNamespace(add_documents=lambda docs: setattr(pipeline, "_docs", docs))
    pipeline.chunk_size = 100
    pipeline.chunk_overlap = 10
    pipeline.chunking_strategy = "recursive"

    fake_chunks = [SimpleNamespace(metadata={"chunk_index": 0}), SimpleNamespace(metadata={"chunk_index": 1})]
    monkeypatch.setattr(module, "chunk_transcript", lambda **kwargs: fake_chunks)

    transcript = SimpleNamespace(
        id=1,
        title="Episode",
        channel_name="Huberman",
        transcript_text="text",
        video_id="vid-1",
    )
    count = pipeline.process_transcript(transcript)

    assert count == 2
    assert pipeline._docs == fake_chunks


def test_process_transcripts_batch_tracks_success_skip_and_fail(monkeypatch):
    module = _load_pipeline_module()
    pipeline = module.VectorizationPipeline.__new__(module.VectorizationPipeline)
    pipeline.vector_store = SimpleNamespace(transcript_exists=lambda tid: tid == 2)
    calls = {"processed": 0}

    def _process_transcript(transcript):
        if transcript.id == 3:
            raise RuntimeError("boom")
        calls["processed"] += 1
        return 4

    pipeline.process_transcript = _process_transcript

    transcripts = [
        SimpleNamespace(id=1, title="A", video_id="a"),
        SimpleNamespace(id=2, title="B", video_id="b"),
        SimpleNamespace(id=3, title="C", video_id="c"),
    ]
    query = SimpleNamespace(filter=lambda *args, **kwargs: query, limit=lambda _: query, all=lambda: transcripts)
    session = SimpleNamespace(query=lambda model: query)

    stats = pipeline.process_transcripts_batch(session, skip_existing=True)

    assert calls["processed"] == 1
    assert stats["success"] == 1
    assert stats["skipped"] == 1
    assert stats["failed"] == 1
    assert stats["total_chunks"] == 4


def test_reprocess_transcript_returns_false_when_missing():
    module = _load_pipeline_module()
    pipeline = module.VectorizationPipeline.__new__(module.VectorizationPipeline)
    pipeline.vector_store = SimpleNamespace(delete_by_transcript_id=lambda transcript_id: None)
    pipeline.process_transcript = lambda transcript: 1

    query = SimpleNamespace(filter=lambda *args, **kwargs: query, first=lambda: None)
    session = SimpleNamespace(query=lambda model: query)

    assert pipeline.reprocess_transcript(session, "missing-id") is False


def test_reprocess_transcript_reembeds_existing():
    calls = {"deleted": None, "processed": 0}
    module = _load_pipeline_module()
    pipeline = module.VectorizationPipeline.__new__(module.VectorizationPipeline)
    pipeline.vector_store = SimpleNamespace(delete_by_transcript_id=lambda transcript_id: calls.update({"deleted": transcript_id}))
    pipeline.process_transcript = lambda transcript: calls.update({"processed": calls["processed"] + 1}) or 1

    transcript = SimpleNamespace(id=42, title="Episode 42", video_id="v42")
    query = SimpleNamespace(filter=lambda *args, **kwargs: query, first=lambda: transcript)
    session = SimpleNamespace(query=lambda model: query)

    assert pipeline.reprocess_transcript(session, "Episode 42") is True
    assert calls["deleted"] == "42"
    assert calls["processed"] == 1
