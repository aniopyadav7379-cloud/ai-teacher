from backend.services.rag.parser import ExtractedDocument, ExtractedPage
from backend.services.rag.chunker import chunk_document


def test_chunk_document_respects_token_budget():
    long_text = "The mitochondria is the powerhouse of the cell. " * 200
    doc = ExtractedDocument(pages=[ExtractedPage(page_number=1, text=long_text, heading="Cell Biology")])
    chunks = chunk_document(doc, chunk_tokens=100, overlap_tokens=20)

    assert len(chunks) > 1
    for c in chunks:
        assert c.page_number == 1
        assert c.heading == "Cell Biology"
        assert c.text.strip()


def test_chunk_document_preserves_metadata_across_pages():
    doc = ExtractedDocument(
        pages=[
            ExtractedPage(page_number=1, text="Newton's first law states that an object at rest stays at rest.", heading="Ch1"),
            ExtractedPage(page_number=2, text="Newton's second law relates force, mass, and acceleration.", heading="Ch2"),
        ]
    )
    chunks = chunk_document(doc)
    pages_seen = {c.page_number for c in chunks}
    assert pages_seen == {1, 2}
    ch2_chunks = [c for c in chunks if c.page_number == 2]
    assert all(c.heading == "Ch2" for c in ch2_chunks)


def test_empty_page_produces_no_chunks():
    doc = ExtractedDocument(pages=[ExtractedPage(page_number=1, text="   ")])
    assert chunk_document(doc) == []
