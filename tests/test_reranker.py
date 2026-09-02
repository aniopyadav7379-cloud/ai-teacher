import pytest

from backend.services.rag.vector_store import RetrievedChunk
from backend.services.rag.reranker import LexicalOverlapReranker


def _chunk(text, score, page=1):
    return RetrievedChunk(text=text, score=score, metadata={"page_number": page})


@pytest.mark.asyncio
async def test_reranker_promotes_exact_term_match_over_higher_vector_score():
    """
    A classic embedding failure mode: a chunk that's topically adjacent but
    doesn't actually contain the queried term can out-score the chunk that
    does, on pure cosine similarity. The lexical signal should be able to
    correct for that when it's blended in.
    """
    query = "Ohm's law resistance current"
    off_topic_but_high_vector = _chunk(
        "Electrical circuits are used throughout modern engineering and power systems design.", score=0.91
    )
    on_topic_lower_vector = _chunk(
        "Ohm's law states that current equals voltage divided by resistance in a circuit.", score=0.60
    )

    reranker = LexicalOverlapReranker(lexical_weight=0.7, vector_weight=0.3)
    result = await reranker.rerank(query, [off_topic_but_high_vector, on_topic_lower_vector], top_k=2)

    assert result[0].text.startswith("Ohm's law")


@pytest.mark.asyncio
async def test_reranker_respects_top_k():
    chunks = [_chunk(f"chunk {i} about resistance", 0.5) for i in range(5)]
    reranker = LexicalOverlapReranker()
    result = await reranker.rerank("resistance", chunks, top_k=2)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_reranker_handles_empty_input():
    reranker = LexicalOverlapReranker()
    assert await reranker.rerank("anything", [], top_k=5) == []


@pytest.mark.asyncio
async def test_reranker_handles_query_with_no_overlap_gracefully():
    chunks = [_chunk("completely unrelated content about baking bread", 0.7)]
    reranker = LexicalOverlapReranker()
    result = await reranker.rerank("quantum entanglement", chunks, top_k=1)
    assert len(result) == 1  # doesn't crash or drop everything, just low-scores it
