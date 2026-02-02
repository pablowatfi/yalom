#!/usr/bin/env python3
"""
Ingest S3-exported transcripts into Pinecone using local embeddings (FastEmbed).
Skips records already marked in DynamoDB.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Iterable, List, Optional

import boto3
from pinecone import Pinecone

from src.embedding_service import embed_documents


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def list_manifest_keys(s3, bucket: str, prefix: str) -> List[str]:
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


def iter_manifest_items(s3, bucket: str, manifest_key: str) -> Iterable[Dict[str, Any]]:
    response = s3.get_object(Bucket=bucket, Key=manifest_key)
    body = response["Body"].read().decode("utf-8")
    for line in body.splitlines():
        if line.strip():
            yield json.loads(line)


def get_s3_json(s3, bucket: str, key: str) -> Dict[str, Any]:
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read().decode("utf-8"))


def is_processed(table, record_id: str, source: str) -> bool:
    if not table:
        return False
    response = table.get_item(Key={"record_id": record_id, "source": source})
    return "Item" in response


def mark_processed(table, record_id: str, source: str, extra: Optional[Dict[str, Any]] = None) -> None:
    if not table:
        return
    item = {
        "record_id": record_id,
        "source": source,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    table.put_item(Item=item)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest S3 transcripts into Pinecone using local embeddings")
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET"))
    parser.add_argument("--prefix", default=os.getenv("S3_PREFIX", "transcripts"))
    parser.add_argument("--table", default="", help="Filter manifest items by table name")
    parser.add_argument("--limit", type=int, default=0, help="Max records to ingest")
    parser.add_argument("--model", default=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--batch", type=int, default=64, help="Embedding batch size")
    parser.add_argument("--skip-ddb", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.bucket:
        raise SystemExit("S3_BUCKET is required (env var or --bucket)")

    pinecone_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_key:
        raise SystemExit("PINECONE_API_KEY is required")

    index_name = os.getenv("PINECONE_INDEX", "yalom-transcripts")
    ddb_table_name = os.getenv("DDB_TABLE")

    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")
    ddb_table = None if args.skip_ddb or not ddb_table_name else dynamodb.Table(ddb_table_name)

    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(index_name)

    manifest_keys = list_manifest_keys(s3, args.bucket, args.prefix)
    if not manifest_keys:
        print("No manifests found.")
        return

    processed = 0
    skipped = 0
    errors = 0

    for manifest_key in manifest_keys:
        for item in iter_manifest_items(s3, args.bucket, manifest_key):
            if args.limit and processed >= args.limit:
                break

            record_id = str(item.get("id"))
            source = item.get("table") or "s3"
            s3_key = item.get("key")

            if args.table and source != args.table:
                continue

            if not record_id or not s3_key:
                skipped += 1
                continue

            if is_processed(ddb_table, record_id, source):
                skipped += 1
                continue

            try:
                payload = get_s3_json(s3, args.bucket, s3_key)
                text = payload.get("text") or ""
                if not text.strip():
                    skipped += 1
                    continue

                metadata = payload.get("metadata", {})
                chunks = chunk_text(text, chunk_size=args.chunk_size, overlap=args.overlap)

                vectors = []
                for i in range(0, len(chunks), args.batch):
                    batch = chunks[i:i + args.batch]
                    embeddings = embed_documents(batch, model_name=args.model)

                    for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                        chunk_index = i + j
                        vector_metadata = {
                            "record_id": record_id,
                            "source": source,
                            "chunk_index": chunk_index,
                            "text": chunk,
                            **{k: v for k, v in metadata.items() if v is not None},
                        }
                        vectors.append({
                            "id": f"{record_id}_{chunk_index}",
                            "values": embedding,
                            "metadata": vector_metadata,
                        })

                if args.dry_run:
                    print(f"DRY RUN: would upsert {len(vectors)} vectors for {record_id}")
                else:
                    index.upsert(vectors=vectors)
                    mark_processed(ddb_table, record_id, source, {
                        "chunks": len(chunks),
                        "s3_key": s3_key,
                    })

                processed += 1

            except Exception as exc:
                print(f"Error processing {s3_key}: {exc}")
                errors += 1
                continue

    print(json.dumps({
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
    }))


if __name__ == "__main__":
    main()
