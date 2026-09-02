"""
Full pipeline: UPLOAD -> VALIDATION -> EXTRACTION -> CLEANING -> STRUCTURE
DETECTION -> CHUNKING -> METADATA -> EMBEDDINGS -> VECTOR STORAGE, and
persists DocumentChunk rows so the DB and vector store stay in sync.
"""
from __future__ import annotations
import re
from pathlib import Path

from sqlalchemy.orm import Session

from backend import models
from backend.services.rag.parser import parse_document, ParsingError
from backend.services.rag.chunker import chunk_document
from backend.services.rag.vector_store import index_chunks
from backend.services.embeddings.factory import get_embedding_provider


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class IngestionError(Exception):
    pass


async def ingest_material(db: Session, material: "models.UploadedMaterial") -> None:
    """
    Runs the full pipeline for one uploaded material and updates its status.
    Designed to be called from a background task (see backend/api/routes/materials.py).
    """
    material.status = "processing"
    db.commit()

    try:
        path = Path(material.file_path)
        doc = parse_document(path)
        for page in doc.pages:
            page.text = clean_text(page.text)

        chunks = chunk_document(doc)
        if not chunks:
            raise IngestionError("Document produced no usable chunks after cleaning.")

        embedding_provider = get_embedding_provider()
        texts = [c.text for c in chunks]
        # Batch to stay well under typical provider request-size limits.
        batch_size = 100
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            vectors.extend(await embedding_provider.embed(texts[i : i + batch_size]))

        vector_ids = await index_chunks(material.id, chunks, vectors)

        for chunk, vec_id in zip(chunks, vector_ids):
            db.add(
                models.DocumentChunk(
                    material_id=material.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    heading=chunk.heading,
                    vector_id=vec_id,
                )
            )

        material.status = "ready"
        material.page_count = doc.page_count
        db.commit()

    except (ParsingError, IngestionError) as e:
        material.status = "failed"
        material.error_message = str(e)
        db.commit()
    except RuntimeError as e:
        # Providers (embeddings, etc.) raise RuntimeError specifically for
        # missing configuration (e.g. no OPENAI_API_KEY) — a known, actionable
        # setup issue, not a genuine crash. Surface it as such rather than
        # under the generic "unexpected error" label below.
        material.status = "failed"
        material.error_message = f"Configuration error: {e}"
        db.commit()
    except Exception as e:  # noqa: BLE001 — pipeline stage must never crash the request
        material.status = "failed"
        material.error_message = f"Unexpected processing error: {e}"
        db.commit()
