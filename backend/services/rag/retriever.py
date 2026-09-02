"""
Student Request -> Query Understanding -> Query Rewriting -> Vector Search ->
Relevant Chunks -> Reranking -> Context Assembly (spec section 7).
Prioritizes uploaded material over general LLM knowledge and preserves
page/heading info for citations.
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.services.rag.vector_store import retrieve, RetrievedChunk
from backend.services.rag.reranker import Reranker, get_default_reranker
from backend.services.llm.base import LLMProvider

# Retrieve this many candidates from the vector store before reranking down
# to the caller's requested top_k — reranking only helps if it has more than
# top_k candidates to actually choose between.
CANDIDATE_POOL_MULTIPLIER = 3


@dataclass
class GroundedContext:
    chunks: list[RetrievedChunk]
    context_text: str
    citations: list[str]
    grounded: bool  # True if any material was actually retrieved


async def rewrite_query(llm: LLMProvider, concept: str, learner_goal: str) -> str:
    """Turns a teaching concept into a focused retrieval query."""
    if not concept.strip():
        return learner_goal
    # Cheap deterministic rewrite (avoids an LLM round-trip on the hot path);
    # an LLM-based rewrite is used only for ambiguous/short concepts.
    if len(concept.split()) >= 3:
        return concept
    prompt = (
        f"Rewrite this short teaching concept into a focused search query "
        f"(under 12 words) for retrieving relevant textbook passages. "
        f"Concept: '{concept}'. Learning goal: '{learner_goal}'. "
        f"Respond with ONLY the rewritten query, nothing else."
    )
    try:
        result = await llm.complete("You rewrite search queries.", prompt, max_tokens=50, temperature=0.0)
        return result.strip().strip('"')
    except Exception:
        return concept


async def get_grounded_context(
    material_ids: list[str],
    query: str,
    *,
    top_k: int = 5,
    reranker: Reranker | None = None,
) -> GroundedContext:
    if not material_ids:
        return GroundedContext(chunks=[], context_text="", citations=[], grounded=False)

    candidate_pool = await retrieve(material_ids, query, top_k=top_k * CANDIDATE_POOL_MULTIPLIER)
    if not candidate_pool:
        return GroundedContext(chunks=[], context_text="", citations=[], grounded=False)

    reranker = reranker or get_default_reranker()
    chunks = await reranker.rerank(query, candidate_pool, top_k=top_k)
    if not chunks:
        return GroundedContext(chunks=[], context_text="", citations=[], grounded=False)

    parts, citations = [], []
    for c in chunks:
        page = c.metadata.get("page_number") or "?"
        heading = c.metadata.get("heading") or ""
        label = f"[Page {page}{f' — {heading}' if heading else ''}]"
        parts.append(f"{label}\n{c.text}")
        citations.append(f"Page {page}" + (f", {heading}" if heading else ""))

    return GroundedContext(
        chunks=chunks,
        context_text="\n\n---\n\n".join(parts),
        citations=citations,
        grounded=True,
    )
