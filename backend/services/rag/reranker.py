"""
RAG RERANKING (limitation #4).

Vector search alone (cosine similarity on dense embeddings) sometimes ranks
a chunk that's topically-nearby above one that actually answers the query —
embeddings capture semantic similarity, not exact-term relevance. A rerank
pass over a larger candidate pool fixes this.

Follows the same provider-abstraction pattern as LLM/TTS/Avatar: a default,
free, dependency-free local reranker (lexical overlap — BM25-lite, no
network call, fully unit-testable) and an optional LLM-based reranker for
when relevance judgments need real semantic reasoning the lexical scorer
can't do (e.g. paraphrased or non-English queries).
"""
from __future__ import annotations
import abc
import math
import re
from collections import Counter

from backend.services.rag.vector_store import RetrievedChunk

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


class Reranker(abc.ABC):
    @abc.abstractmethod
    async def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int) -> list[RetrievedChunk]:
        """Reorders `chunks` (already vector-search candidates) and returns the best `top_k`."""


class LexicalOverlapReranker(Reranker):
    """
    BM25-lite: scores each candidate chunk by term-frequency overlap with
    the query (with an IDF-style discount computed across the candidate
    pool itself, so common words across all chunks don't dominate), then
    blends that with the original vector-similarity score. Deterministic,
    free, and needs no network — the default reranker.
    """

    def __init__(self, *, lexical_weight: float = 0.4, vector_weight: float = 0.6):
        self.lexical_weight = lexical_weight
        self.vector_weight = vector_weight

    def _lexical_scores(self, query: str, chunks: list[RetrievedChunk]) -> list[float]:
        query_terms = set(_tokenize(query))
        if not query_terms:
            return [0.0] * len(chunks)

        doc_term_counts = [Counter(_tokenize(c.text)) for c in chunks]
        n_docs = len(chunks)
        # document frequency of each query term across the candidate pool
        df = {t: sum(1 for counts in doc_term_counts if counts.get(t)) for t in query_terms}

        scores = []
        for counts in doc_term_counts:
            doc_len = sum(counts.values()) or 1
            score = 0.0
            for term in query_terms:
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                idf = math.log((n_docs + 1) / (df[term] + 0.5)) + 1
                score += (tf / doc_len) * idf
            scores.append(score)

        max_score = max(scores) if scores and max(scores) > 0 else 1.0
        return [s / max_score for s in scores]

    async def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int) -> list[RetrievedChunk]:
        if not chunks:
            return []
        lexical = self._lexical_scores(query, chunks)
        # Vector scores from Chroma are already in a roughly comparable 0..1 range
        # (1 - cosine distance); normalize defensively in case they aren't.
        vec_scores = [c.score for c in chunks]
        max_vec = max(vec_scores) if vec_scores and max(vec_scores) > 0 else 1.0
        blended = [
            self.vector_weight * (v / max_vec) + self.lexical_weight * l
            for v, l in zip(vec_scores, lexical)
        ]
        ranked = sorted(zip(chunks, blended), key=lambda pair: pair[1], reverse=True)
        return [
            RetrievedChunk(text=c.text, score=score, metadata=c.metadata)
            for c, score in ranked[:top_k]
        ]


class LLMReranker(Reranker):
    """
    Optional: asks the LLM to score each candidate's relevance 0-10 and
    reorders by that. More accurate for paraphrased/non-English queries than
    lexical overlap, at the cost of a network call. Not the default because
    it adds latency + cost to every teaching request; enable by passing this
    reranker explicitly where that tradeoff is worth it.
    """

    def __init__(self, llm=None):
        from backend.services.llm.factory import get_llm_provider
        self._llm = llm or get_llm_provider()

    async def rerank(self, query: str, chunks: list[RetrievedChunk], *, top_k: int) -> list[RetrievedChunk]:
        if not chunks:
            return []
        numbered = "\n\n".join(f"[{i}] {c.text[:500]}" for i, c in enumerate(chunks))
        prompt = (
            f"Query: {query}\n\nCandidate passages:\n{numbered}\n\n"
            f"Return a JSON object {{\"scores\": [list of {len(chunks)} numbers 0-10, "
            f"one per passage in order, higher = more relevant to the query]}}."
        )
        try:
            data = await self._llm.complete_json(
                "You score passage relevance for a retrieval system.", prompt, max_tokens=300, temperature=0.0
            )
            scores = data.get("scores", [])
            if len(scores) != len(chunks):
                raise ValueError("score count mismatch")
        except Exception:
            # Fail open to the original vector ranking rather than breaking retrieval.
            return chunks[:top_k]

        ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]


def get_default_reranker() -> Reranker:
    return LexicalOverlapReranker()
