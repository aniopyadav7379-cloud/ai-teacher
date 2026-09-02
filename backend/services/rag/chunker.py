"""
CHUNKING -> METADATA GENERATION (spec section 6).

Uses a lightweight word-based splitter with overlap rather than tiktoken:
tiktoken's BPE files are fetched from a remote blob on first use, which is a
real reliability risk in restricted/offline deployments (this sandbox can't
reach it either). A words-per-token approximation is accurate enough for
chunk-sizing purposes and keeps this pipeline stage fully dependency-free
at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.services.rag.parser import ExtractedDocument

WORDS_PER_TOKEN = 0.75  # ~1 token per 0.75 words (rough English average)


@dataclass
class Chunk:
    index: int
    text: str
    page_number: int | None
    heading: str | None
    chapter: str | None = None
    section: str | None = None


def chunk_document(
    doc: ExtractedDocument,
    *,
    chunk_tokens: int = 350,
    overlap_tokens: int = 60,
) -> list[Chunk]:
    chunk_words = max(int(chunk_tokens * WORDS_PER_TOKEN), 10)
    overlap_words = max(int(overlap_tokens * WORDS_PER_TOKEN), 0)

    chunks: list[Chunk] = []
    idx = 0
    for page in doc.pages:
        words = page.text.split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(start + chunk_words, len(words))
            piece = " ".join(words[start:end])
            if piece.strip():
                chunks.append(
                    Chunk(
                        index=idx,
                        text=piece.strip(),
                        page_number=page.page_number,
                        heading=page.heading,
                    )
                )
                idx += 1
            if end == len(words):
                break
            start = end - overlap_words
    return chunks
