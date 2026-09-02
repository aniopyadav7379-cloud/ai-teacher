"""
Vector storage + retrieval, backed by Chroma (embedded, no separate server
needed). Each material gets its own Chroma collection so retrieval can be
scoped to "this session's uploaded document" as required by spec section 7
("prioritize uploaded material").
"""
from __future__ import annotations
from dataclasses import dataclass

import chromadb

from backend.core.config import get_settings
from backend.services.embeddings.factory import get_embedding_provider

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.vector_db_path)
    return _client


@dataclass
class RetrievedChunk:
    text: str
    score: float
    metadata: dict


def collection_name(material_id: str) -> str:
    return f"material_{material_id}".replace("-", "")


async def index_chunks(material_id: str, chunks: list, embeddings: list[list[float]]) -> list[str]:
    """Stores chunk texts + embeddings + metadata. Returns the vector IDs assigned."""
    client = _get_client()
    coll = client.get_or_create_collection(collection_name(material_id))
    ids = [f"{material_id}_{c.index}" for c in chunks]
    coll.add(
        ids=ids,
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "page_number": c.page_number or 0,
                "heading": c.heading or "",
                "chunk_index": c.index,
            }
            for c in chunks
        ],
    )
    return ids


async def retrieve(material_ids: list[str], query: str, *, top_k: int = 5) -> list[RetrievedChunk]:
    if not material_ids:
        return []
    client = _get_client()
    provider = get_embedding_provider()
    query_vec = await provider.embed_query(query)

    results: list[RetrievedChunk] = []
    for material_id in material_ids:
        try:
            coll = client.get_collection(collection_name(material_id))
        except Exception:
            continue
        res = coll.query(query_embeddings=[query_vec], n_results=top_k)
        for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            results.append(RetrievedChunk(text=text, score=1 - dist, metadata=meta))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
