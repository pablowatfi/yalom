"""
AWS Lambda handler for RAG queries.
Handles user queries via API Gateway.
Uses OpenAI embeddings and Groq for generation.
"""
import json
import logging
from typing import Any

from src.config import RAG_DEBUG_LOGS, RAG_DEBUG_MAX_CHUNKS, RAG_DEBUG_MAX_PROMPT_CHARS, RAG_TOP_K
from src.rag.aws_pipeline import PineconeRAG
from src.rag.safety import is_prompt_injection, is_prompt_injection_in_history

logger = logging.getLogger(__name__)
rag = PineconeRAG()


def _normalize_top_k(value: Any) -> int:
    if isinstance(value, int):
        return max(1, value)
    if isinstance(value, str) and value.strip().isdigit():
        return max(1, int(value.strip()))
    return RAG_TOP_K


def lambda_handler(event: dict[str, Any] | None, context: Any) -> dict[str, Any]:
    """
    Handle RAG queries.
    Called via API Gateway.
    """
    try:
        payload = event or {}
        body = json.loads(payload.get("body", "{}"))
        query = body.get("query", "")
        top_k = _normalize_top_k(body.get("top_k", RAG_TOP_K))
        history = body.get("history", [])
        if not isinstance(history, list):
            history = []

        if not query:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({"error": "Query is required"}),
            }

        if is_prompt_injection(query) or is_prompt_injection_in_history(history):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps({
                    "error": "Request rejected: prompt-injection attempt detected."
                }),
            }

        response_body = rag.query(query, history=history, top_k=top_k, return_debug=RAG_DEBUG_LOGS)

        debug_payload = response_body.pop("debug", None)

        if debug_payload:
            debug_payload["similarity_chunks"] = debug_payload.get("similarity_chunks", [])[:RAG_DEBUG_MAX_CHUNKS]
            debug_payload["reranked_chunks"] = debug_payload.get("reranked_chunks", [])[:RAG_DEBUG_MAX_CHUNKS]
            prompt_messages = debug_payload.get("prompt", [])
            trimmed_prompt = []
            for message in prompt_messages:
                content = message.get("content", "")
                trimmed_prompt.append({
                    **message,
                    "content": content[:RAG_DEBUG_MAX_PROMPT_CHARS],
                })
            debug_payload["prompt"] = trimmed_prompt
            logger.info("query_debug", extra=debug_payload)

        log_payload = {
            "event": "query_completed",
            "query_preview": query[:120],
            "answer_length": len(response_body["answer"]),
            "sources_count": len(response_body["sources"]),
        }

        if debug_payload:
            log_payload["rewrite_queries"] = debug_payload.get("rewrite_queries", [])
            log_payload["similarity_chunks"] = debug_payload.get("similarity_chunks", [])
            log_payload["reranked_chunks"] = debug_payload.get("reranked_chunks", [])

        logger.info("query_completed", extra=log_payload)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(response_body),
        }

    except Exception:
        logger.exception("Unhandled query lambda error")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": "Internal server error"}),
        }
