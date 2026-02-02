"""
Lightweight RAG pipeline for AWS Lambda using Pinecone + Groq + OpenAI embeddings.
"""
import os
from typing import List, Dict, Any

from groq import Groq
from pinecone import Pinecone

from src.config import (
    DEFAULT_LANGUAGE,
    GROQ_MAX_TOKENS,
    GROQ_MODEL,
    PINECONE_INDEX,
    RAG_HISTORY_LIMIT,
    RAG_RETRIEVAL_MULTIPLIER,
    RAG_QUERY_REWRITING,
    RAG_RERANKING,
    RAG_SIMILARITY_THRESHOLD,
    RAG_TEMPERATURE,
    RAG_TOP_K,
)
from src.embedding_service import embed_query
from src.rag.prompts import get_active_prompt, get_language_name


class PineconeRAG:
    def __init__(
        self,
        index_name: str = PINECONE_INDEX,
        groq_api_key: str | None = None,
        pinecone_api_key: str | None = None,
        model: str = GROQ_MODEL,
    ) -> None:
        self.groq_client = Groq(api_key=groq_api_key or os.environ["GROQ_API_KEY"])
        pc = Pinecone(api_key=pinecone_api_key or os.environ["PINECONE_API_KEY"])
        self.index = pc.Index(index_name)
        self.model = model

    def query(
        self,
        question: str,
        history: List[Dict[str, str]] | None = None,
        top_k: int = RAG_TOP_K,
        return_debug: bool = False,
    ) -> Dict[str, Any]:
        rewritten_queries = self._rewrite_queries(question) if RAG_QUERY_REWRITING else [question]

        retrieval_k = max(1, top_k) * max(1, RAG_RETRIEVAL_MULTIPLIER)
        aggregated_matches: dict[str, Dict[str, Any]] = {}
        for query in rewritten_queries:
            query_embedding = embed_query(query)
            results = self.index.query(
                vector=query_embedding,
                top_k=retrieval_k,
                include_metadata=True
            )
            for match in results.get("matches", []):
                match_id = match.get("id")
                if not match_id:
                    continue
                existing = aggregated_matches.get(match_id)
                if not existing or match.get("score", 0) > existing.get("score", 0):
                    aggregated_matches[match_id] = match

        if not aggregated_matches:
            return {"answer": "No relevant information found.", "sources": []}

        raw_matches = list(aggregated_matches.values())
        matches = sorted(
            raw_matches,
            key=lambda match: match.get("score", 0),
            reverse=True,
        )
        filtered_matches = [
            match
            for match in matches
            if match.get("score", 0) >= RAG_SIMILARITY_THRESHOLD
        ][:top_k]

        if filtered_matches:
            matches = filtered_matches
        else:
            matches = matches[:top_k]

        if RAG_RERANKING and matches:
            matches = self._rerank_matches(question, matches)

        context_text = "\n\n".join([
            match["metadata"]["text"] for match in matches
        ])

        prompt = get_active_prompt()
        system_template = prompt["system"]
        system_kwargs = {"context": context_text}
        if "{language}" in system_template:
            system_kwargs["language"] = get_language_name(DEFAULT_LANGUAGE)

        messages = [{
            "role": "system",
            "content": system_template.format(**system_kwargs)
        }]

        if isinstance(history, list):
            for item in history[-RAG_HISTORY_LIMIT:]:
                role = item.get("role")
                content = item.get("content")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})

        messages.append({
            "role": "user",
            "content": prompt["human"].format(question=question)
        })

        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=RAG_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS
        )
        payload = {
            "answer": response.choices[0].message.content,
            "sources": [
                {
                    "episode_name": (
                        match["metadata"].get("episode_name")
                        or match["metadata"].get("title")
                    ),
                    "title": (
                        match["metadata"].get("title")
                        or match["metadata"].get("episode_name")
                    ),
                    "video_id": match["metadata"].get("video_id"),
                    "score": match.get("score"),
                    "content": match["metadata"].get("text"),
                }
                for match in matches
            ]
        }

        if return_debug:
            payload["debug"] = {
                "question": question,
                "rewrite_queries": rewritten_queries,
                "similarity_chunks": [self._serialize_match(match) for match in raw_matches],
                "reranked_chunks": [self._serialize_match(match) for match in matches],
                "prompt": messages,
            }

        return payload

    @staticmethod
    def _serialize_match(match: Dict[str, Any]) -> Dict[str, Any]:
        metadata = match.get("metadata") or {}
        text = metadata.get("text") or ""
        return {
            "score": match.get("score"),
            "id": match.get("id"),
            "episode_name": metadata.get("episode_name") or metadata.get("title"),
            "video_id": metadata.get("video_id"),
            "text_preview": text[:300],
        }

    def _rerank_matches(self, question: str, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        id_to_match = {match.get("id"): match for match in matches if match.get("id")}
        if not id_to_match:
            return matches

        passages = []
        for match in matches:
            match_id = match.get("id")
            text = (match.get("metadata") or {}).get("text") or ""
            if match_id and text:
                passages.append({"id": match_id, "text": text[:800]})

        if not passages:
            return matches

        prompt = (
            "You are reranking transcript passages by relevance to the user question. "
            "Return a JSON array of passage ids ordered from most to least relevant. "
            "Only return JSON, no extra text.\n\n"
            f"Question: {question}\n\n"
            "Passages:\n"
            + "\n".join([f"- id: {p['id']}\n  text: {p['text']}" for p in passages])
        )

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256,
            )
            content = response.choices[0].message.content.strip()
            ordered_ids = []
            if content.startswith("[") and content.endswith("]"):
                import json
                ordered_ids = json.loads(content)
            if ordered_ids:
                reranked = [id_to_match[mid] for mid in ordered_ids if mid in id_to_match]
                remaining = [m for m in matches if m.get("id") not in ordered_ids]
                return reranked + remaining
        except Exception:
            return matches

        return matches

    def _rewrite_queries(self, question: str) -> List[str]:
        try:
            from langchain_groq import ChatGroq
            from src.rag.query_rewriter import QueryRewriter

            llm = ChatGroq(model_name=self.model, groq_api_key=os.environ.get("GROQ_API_KEY"))
            rewriter = QueryRewriter(llm=llm, enabled=True)
            rewritten = rewriter.rewrite(question)
            queries = rewritten.get("queries") or [question]
            if question not in queries:
                queries.insert(0, question)
            return queries[:3]
        except Exception as exc:
            print(f"Query rewriting unavailable: {exc}")
            return [question]
