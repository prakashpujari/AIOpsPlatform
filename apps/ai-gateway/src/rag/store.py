"""In‑memory vector store for RAG demonstration.

This module provides a very small, deterministic store useful for unit and
integration tests. In production the store would be backed by Milvus, PGVector,
or another vector database.
"""

from __future__ import annotations

import math
from typing import List, Tuple

# Simple deterministic pseudo‑embedding generator – see ``embed_text`` below


class InMemoryVectorStore:
    """Store embeddings and associated metadata in memory.

    The store holds tuples of ``(doc_id, text, embedding, metadata)``. ``add``
    inserts new entries; ``search`` can optionally filter by metadata before
    computing similarity.
    """

    def __init__(self) -> None:
        # Each entry: (doc_id, text, embedding, metadata dict)
        self._entries: List[Tuple[str, str, List[float], dict]] = []

    def add(self, doc_id: str, text: str, embedding: List[float], metadata: dict | None = None) -> None:
        self._entries.append((doc_id, text, embedding, metadata or {}))

    def search(self, query_emb: List[float], top_k: int = 5, filters: dict | None = None) -> List[Tuple[str, str, float]]:
        """Return top‑k most similar documents, optionally applying ``filters``.

        ``filters`` is a dict of key/value pairs that must match the entry's
        metadata exactly. Entries that do not satisfy the filter are excluded
        before similarity ranking.
        """
        results: List[Tuple[str, str, float]] = []
        for doc_id, text, emb, meta in self._entries:
            if filters:
                # All filter keys must exist and match exactly
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue
            score = _cosine_similarity(query_emb, emb)
            results.append((doc_id, text, score))
        # Sort by descending similarity
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
