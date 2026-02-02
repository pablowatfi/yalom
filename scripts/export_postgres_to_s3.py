#!/usr/bin/env python3
"""
Export transcript data from local Postgres to S3 with a structured schema.

Outputs one JSON object per transcript:
s3://<bucket>/<prefix>/<table>/year=<YYYY>/<id>.json

Also writes a manifest file per table:
<bucket>/<prefix>/<table>/_manifest.jsonl
"""
import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Iterable, List

import boto3
import psycopg2
from psycopg2.extras import RealDictCursor


def extract_year(date_str: str) -> str:
    if not date_str:
        return "unknown"
    match = re.search(r"(\d{4})", str(date_str))
    return match.group(1) if match else "unknown"


def row_to_payload(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    if table == "video_transcripts":
        record_id = row.get("video_id") or row.get("transcript_id") or str(row.get("id"))
        metadata = {
            "video_id": row.get("video_id"),
            "transcript_id": row.get("transcript_id"),
            "episode_name": row.get("title"),
            "podcast_name": row.get("channel_name"),
            "channel_id": row.get("channel_id"),
            "upload_date": row.get("upload_date"),
            "duration": row.get("duration"),
            "view_count": row.get("view_count"),
            "language": row.get("transcript_language"),
        }
        text = row.get("transcript_text") or ""
    elif table == "podcast_transcripts":
        record_id = row.get("episode_uid") or str(row.get("id"))
        metadata = {
            "episode_uid": row.get("episode_uid"),
            "episode_name": row.get("episode_title"),
            "podcast_uid": row.get("podcast_uid"),
            "podcast_name": row.get("podcast_title"),
            "published_date": row.get("published_date"),
            "duration": row.get("duration"),
        }
        text = row.get("transcript_text") or ""
    else:
        record_id = str(row.get("id"))
        metadata = {}
        text = row.get("transcript_text") or ""

    payload = {
        "id": record_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {k: v for k, v in metadata.items() if v is not None},
        "text": text,
    }
    return payload


def iter_rows(conn, table: str, limit: int = 0) -> Iterable[Dict[str, Any]]:
    query = f"SELECT * FROM {table} WHERE has_transcript = true"
    if limit > 0:
        query += f" LIMIT {limit}"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        for row in cur:
            yield row


def upload_json(s3, bucket: str, key: str, data: Dict[str, Any]) -> None:
    body = json.dumps(data, ensure_ascii=False)
    s3.put_object(Bucket=bucket, Key=key, Body=body.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export transcripts from Postgres to S3")
    parser.add_argument("--tables", nargs="*", default=["video_transcripts", "podcast_transcripts"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET"))
    parser.add_argument("--prefix", default=os.getenv("S3_PREFIX", "transcripts"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.bucket:
        raise SystemExit("S3_BUCKET is required (env var or --bucket)")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    s3 = boto3.client("s3")

    with psycopg2.connect(database_url) as conn:
        for table in args.tables:
            manifest: List[Dict[str, Any]] = []
            for row in iter_rows(conn, table, limit=args.limit):
                payload = row_to_payload(table, row)
                date_str = row.get("upload_date") or row.get("published_date")
                year = extract_year(date_str)
                key = f"{args.prefix}/{table}/year={year}/{payload['id']}.json"

                if args.dry_run:
                    print(f"DRY RUN: s3://{args.bucket}/{key}")
                else:
                    upload_json(s3, args.bucket, key, payload)

                manifest.append({
                    "id": payload["id"],
                    "key": key,
                    "table": table,
                    "year": year,
                })

            # Upload manifest
            if not args.dry_run:
                manifest_key = f"{args.prefix}/{table}/_manifest.jsonl"
                manifest_body = "\n".join(json.dumps(item) for item in manifest)
                s3.put_object(
                    Bucket=args.bucket,
                    Key=manifest_key,
                    Body=manifest_body.encode("utf-8")
                )
                print(f"Uploaded manifest: s3://{args.bucket}/{manifest_key}")


if __name__ == "__main__":
    main()
