"""
AWS Lambda handler for ingesting Huberman Lab podcast transcripts.
Runs weekly via EventBridge cron.
Uses OpenAI embeddings (text-embedding-3-small).
"""
import json
import os
from datetime import datetime, timezone

import boto3
from pinecone import Pinecone
from youtube_transcript_api import YouTubeTranscriptApi

from src.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DDB_TABLE,
    PINECONE_INDEX,
    S3_BUCKET,
    S3_PREFIX,
    YOUTUBE_TRANSCRIPTS_PREFIX,
)
from src.embedding_service import embed_documents

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(PINECONE_INDEX)

ingestion_table = dynamodb.Table(DDB_TABLE) if DDB_TABLE else None


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def get_embeddings(texts):
    """Generate embeddings using shared local embedding service."""
    return embed_documents(texts)


def list_manifest_keys(bucket: str, prefix: str):
    keys = []
    continuation_token = None
    while True:
        params = {
            "Bucket": bucket,
            "Prefix": f"{prefix}/",
        }
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**params)
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/_manifest.jsonl"):
                keys.append(key)

        if response.get("IsTruncated"):
            continuation_token = response.get("NextContinuationToken")
        else:
            break
    return keys


def iter_manifest_items(bucket: str, manifest_key: str):
    response = s3.get_object(Bucket=bucket, Key=manifest_key)
    body = response["Body"].read().decode("utf-8")
    for line in body.splitlines():
        if line.strip():
            yield json.loads(line)


def get_s3_json(bucket: str, key: str):
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read().decode("utf-8"))


def is_processed(record_id: str, source: str) -> bool:
    if not ingestion_table:
        return False
    response = ingestion_table.get_item(Key={"record_id": record_id, "source": source})
    return "Item" in response


def mark_processed(record_id: str, source: str, extra: dict) -> None:
    if not ingestion_table:
        return
    item = {
        "record_id": record_id,
        "source": source,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    ingestion_table.put_item(Item=item)


def lambda_handler(event, context):
    """
    Ingestion handler.
    - If event.video_ids is provided, fetches from YouTube.
    - Otherwise, reads S3 manifests and ingests missing transcripts.
    """
    try:
        event = event or {}
        video_ids = event.get("video_ids", [])
        processed_count = 0
        skipped_count = 0
        error_count = 0

        if video_ids:
            for video_id in video_ids:
                try:
                    if is_processed(video_id, "youtube"):
                        skipped_count += 1
                        continue

                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    full_text = " ".join([entry["text"] for entry in transcript])
                    if not full_text.strip():
                        skipped_count += 1
                        continue

                    chunks = chunk_text(full_text)
                    embeddings = get_embeddings(chunks)

                    vectors = []
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        vectors.append({
                            "id": f"{video_id}_{i}",
                            "values": embedding,
                            "metadata": {
                                "record_id": video_id,
                                "source": "youtube",
                                "video_id": video_id,
                                "chunk_index": i,
                                "text": chunk,
                            },
                        })

                    index.upsert(vectors=vectors)

                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=f"{YOUTUBE_TRANSCRIPTS_PREFIX}/{video_id}.json",
                        Body=json.dumps({
                            "video_id": video_id,
                            "transcript": full_text,
                            "chunks": len(chunks),
                        }),
                    )

                    mark_processed(video_id, "youtube", {"chunks": len(chunks)})
                    processed_count += 1

                except Exception as video_error:
                    print(f"Error processing {video_id}: {str(video_error)}")
                    error_count += 1
                    continue
        else:
            manifest_prefix = event.get("s3_manifest_prefix", S3_PREFIX)
            manifest_keys = list_manifest_keys(S3_BUCKET, manifest_prefix)

            if not manifest_keys:
                result = {
                    "message": "No manifests found in S3",
                    "processed": 0,
                    "skipped": 0,
                    "errors": 0,
                }
                print(json.dumps(result))
                return {
                    "statusCode": 200,
                    "body": json.dumps(result),
                }

            for manifest_key in manifest_keys:
                for item in iter_manifest_items(S3_BUCKET, manifest_key):
                    record_id = str(item.get("id"))
                    source = item.get("table") or "s3"
                    s3_key = item.get("key")

                    if not record_id or not s3_key:
                        skipped_count += 1
                        continue

                    if is_processed(record_id, source):
                        skipped_count += 1
                        continue

                    try:
                        payload = get_s3_json(S3_BUCKET, s3_key)
                        text = payload.get("text") or ""
                        if not text.strip():
                            skipped_count += 1
                            continue

                        metadata = payload.get("metadata", {})
                        chunks = chunk_text(text)
                        embeddings = get_embeddings(chunks)

                        vectors = []
                        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                            vector_metadata = {
                                "record_id": record_id,
                                "source": source,
                                "chunk_index": i,
                                "text": chunk,
                                **{k: v for k, v in metadata.items() if v is not None},
                            }
                            vectors.append({
                                "id": f"{record_id}_{i}",
                                "values": embedding,
                                "metadata": vector_metadata,
                            })

                        index.upsert(vectors=vectors)
                        mark_processed(record_id, source, {
                            "chunks": len(chunks),
                            "s3_key": s3_key,
                        })
                        processed_count += 1

                    except Exception as s3_error:
                        print(f"Error processing {s3_key}: {str(s3_error)}")
                        error_count += 1
                        continue

        result = {
            "message": "Ingestion completed",
            "processed": processed_count,
            "skipped": skipped_count,
            "errors": error_count,
        }
        print(json.dumps(result))
        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error: {str(e)}"),
        }
