import importlib
import json
from unittest.mock import patch


class _FakeIndex:
    def __init__(self):
        self.upserts = []

    def upsert(self, vectors):
        self.upserts.append(vectors)


class _FakePinecone:
    def __init__(self, api_key):
        self.api_key = api_key
        self.index = _FakeIndex()

    def Index(self, name):
        return self.index


class _FakeS3:
    def __init__(self):
        self.objects = {}
        self.put_calls = []
        self.list_response = {"Contents": [], "IsTruncated": False}

    def list_objects_v2(self, **kwargs):
        return self.list_response

    def get_object(self, Bucket, Key):
        return {"Body": _FakeBody(self.objects[Key])}

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)


class _FakeBody:
    def __init__(self, payload: str):
        self._payload = payload

    def read(self):
        return self._payload.encode("utf-8")


class _FakeDynamoTable:
    def __init__(self):
        self.data = {}

    def get_item(self, Key):
        key = (Key["record_id"], Key["source"])
        if key in self.data:
            return {"Item": self.data[key]}
        return {}

    def put_item(self, Item):
        key = (Item["record_id"], Item["source"])
        self.data[key] = Item


class _FakeDynamoResource:
    def __init__(self, table):
        self._table = table

    def Table(self, name):
        return self._table


def _load_module(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    fake_s3 = _FakeS3()
    fake_table = _FakeDynamoTable()
    fake_pc = _FakePinecone("test-key")

    with patch("boto3.client", return_value=fake_s3), patch(
        "boto3.resource", return_value=_FakeDynamoResource(fake_table)
    ), patch("pinecone.Pinecone", return_value=fake_pc):
        module = importlib.import_module("src.ingestion.aws_handler")
        module = importlib.reload(module)

    module.s3 = fake_s3
    module.index = fake_pc.index
    module.ingestion_table = fake_table
    return module


def test_chunk_text_produces_overlapping_chunks(monkeypatch):
    handler = _load_module(monkeypatch)

    chunks = handler.chunk_text("abcdefghij", chunk_size=4, overlap=2)

    assert chunks == ["abcd", "cdef", "efgh", "ghij", "ij"]


def test_lambda_handler_youtube_ingests_and_marks_processed(monkeypatch):
    handler = _load_module(monkeypatch)
    monkeypatch.setattr(
        handler.YouTubeTranscriptApi,
        "get_transcript",
        lambda video_id: [{"text": "hello"}, {"text": "world"}],
    )
    monkeypatch.setattr(handler, "get_embeddings", lambda chunks: [[0.1, 0.2] for _ in chunks])

    response = handler.lambda_handler({"video_ids": ["v1"]}, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["processed"] == 1
    assert len(handler.index.upserts) == 1
    assert ("v1", "youtube") in handler.ingestion_table.data
    assert len(handler.s3.put_calls) == 1


def test_lambda_handler_manifest_path_ingests_records(monkeypatch):
    handler = _load_module(monkeypatch)
    handler.s3.list_response = {
        "Contents": [{"Key": "transcripts/_manifest.jsonl"}],
        "IsTruncated": False,
    }
    handler.s3.objects["transcripts/_manifest.jsonl"] = json.dumps(
        {"id": "r1", "table": "episodes", "key": "transcripts/r1.json"}
    )
    handler.s3.objects["transcripts/r1.json"] = json.dumps(
        {"text": "alpha beta gamma", "metadata": {"title": "Episode 1"}}
    )
    monkeypatch.setattr(handler, "get_embeddings", lambda chunks: [[0.1] for _ in chunks])

    response = handler.lambda_handler({}, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["processed"] == 1
    assert ("r1", "episodes") in handler.ingestion_table.data


def test_lambda_handler_returns_500_on_unhandled_error(monkeypatch):
    handler = _load_module(monkeypatch)
    monkeypatch.setattr(handler, "list_manifest_keys", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    response = handler.lambda_handler({}, None)

    assert response["statusCode"] == 500
    assert json.loads(response["body"]) == "Internal server error"
