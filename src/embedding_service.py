"""
Shared embedding helpers using OpenAI.
All embedding calls should use this module to avoid duplication.
"""
import os
from typing import List

from openai import OpenAI

_DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def embed_documents(
    texts: List[str],
    model_name: str | None = None,
    batch_size: int = 100,
) -> List[List[float]]:
    model = model_name or _DEFAULT_MODEL
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        client = _get_openai_client()
        response = client.embeddings.create(
            model=model,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def embed_query(text: str, model_name: str | None = None) -> List[float]:
    model = model_name or _DEFAULT_MODEL
    client = _get_openai_client()
    response = client.embeddings.create(
        model=model,
        input=[text],
    )
    return response.data[0].embedding
