"""
Shared embedding helpers using OpenAI.
All embedding calls should use this module to avoid duplication.
"""
import os
from typing import List

from openai import OpenAI

_DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
_OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_documents(
    texts: List[str],
    model_name: str | None = None,
    batch_size: int = 100,
) -> List[List[float]]:
    model = model_name or _DEFAULT_MODEL
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = _OPENAI_CLIENT.embeddings.create(
            model=model,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def embed_query(text: str, model_name: str | None = None) -> List[float]:
    model = model_name or _DEFAULT_MODEL
    response = _OPENAI_CLIENT.embeddings.create(
        model=model,
        input=[text],
    )
    return response.data[0].embedding
