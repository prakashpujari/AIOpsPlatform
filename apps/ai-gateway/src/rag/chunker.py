"""Simple text chunker for RAG.

The chunker splits a string into overlapping windows of a given size (in characters).
It is used by the ingestion pipeline to break large documents into manageable
chunks before embedding.
"""

from __future__ import annotations

from typing import List


def chunk_text(text: str, max_chunk: int = 4000, overlap: int = 200) -> List[str]:
    """Split ``text`` into overlapping chunks.

    Args:
        text: The original document.
        max_chunk: Maximum characters per chunk.
        overlap: Number of characters each chunk should overlap with the previous.

    Returns:
        A list of chunk strings.
    """
    if len(text) <= max_chunk:
        return [text]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chunk, len(text))
        chunks.append(text[start:end])
        # Move start forward by (max_chunk - overlap) to create overlap
        start += max_chunk - overlap
    return chunks
