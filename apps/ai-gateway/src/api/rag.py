"""RAG API – simple vector search for demo purposes.

Provides two endpoints:
* ``POST /rag/ingest`` – accepts a document ID and raw text, chunks the text,
  computes embeddings, and stores them in the in‑memory vector store.
* ``GET /rag/search`` – accepts a query string, computes its embedding, and
  returns the top‑k most similar chunks.

In production these endpoints would interact with Milvus or another vector DB
and support metadata filters. Here we keep the implementation lightweight for
testing and demonstration.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..rag.chunker import chunk_text
from ..rag.embedding import embed_text
from ..rag.store import InMemoryVectorStore

router = APIRouter(prefix="/rag", tags=["rag"])

# Import the RAG request metric from main
from ..main import RAG_REQUESTS

# Global in‑memory store – in a real app this would be a proper service class
_vector_store = InMemoryVectorStore()


class IngestRequest(BaseModel):
    doc_id: str = Field(..., description="Unique identifier for the document")
    text: str = Field(..., description="Raw document text to ingest")
    chunk_size: int = Field(4000, ge=1, description="Maximum characters per chunk")
    overlap: int = Field(200, ge=0, description="Overlap characters between chunks")


@router.post("/ingest")
async def ingest_document(req: IngestRequest):
    """Chunk a document, embed each chunk, and store it in the vector store."""
    if not req.text:
        raise HTTPException(status_code=400, detail="Empty document text")
    chunks = chunk_text(req.text, max_chunk=req.chunk_size, overlap=req.overlap)
    for i, chunk in enumerate(chunks):
        emb = embed_text(chunk)
        # Use a composite ID to keep chunks distinct
        chunk_id = f"{req.doc_id}#c{i}"
        _vector_store.add(chunk_id, chunk, emb)
    return {"doc_id": req.doc_id, "chunks": len(chunks)}


class SearchResponse(BaseModel):
    query: str
    results: list[dict]


@router.get("/search", response_model=SearchResponse)
async def search(query: str, top_k: int = 5, filters: dict | None = None):
    """Return the top‑k most similar chunks for ``query``.

    ``filters`` allows optional metadata filtering (key/value exact match) before
    similarity ranking, implementing the hybrid‑search concept.
    The response contains a list of dictionaries with ``doc_id``, ``chunk`` and
    ``score`` (cosine similarity).
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query string required")
    query_emb = embed_text(query)
    hits = _vector_store.search(query_emb, top_k=top_k, filters=filters)
    results = [{"doc_id": doc_id, "chunk": chunk, "score": score} for doc_id, chunk, score in hits]
    return SearchResponse(query=query, results=results)
