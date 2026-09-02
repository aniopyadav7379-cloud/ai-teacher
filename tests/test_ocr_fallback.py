"""
Validates the OCR fallback path (spec limitation #1: OCR for scanned PDFs).
Builds a synthetic image-only PDF (no embedded text layer) at test time so
this doesn't depend on a fixture binary, then confirms pypdf alone extracts
nothing but the parser's OCR fallback recovers the text.

Skips gracefully if tesseract/poppler aren't installed in the environment
running the tests (OCR is a best-effort enhancement, not a hard dependency).
"""
import shutil
import pytest
from pathlib import Path

from backend.services.rag.parser import parse_document, _ocr_available

pytestmark = pytest.mark.skipif(not _ocr_available(), reason="tesseract/poppler not installed in this environment")


def _make_scanned_pdf(tmp_path: Path) -> Path:
    from PIL import Image, ImageDraw
    from reportlab.pdfgen import canvas

    img_path = tmp_path / "page.png"
    img = Image.new("RGB", (900, 300), "white")
    ImageDraw.Draw(img).text((30, 100), "Photosynthesis converts light energy into chemical energy", fill="black")
    img.save(img_path)

    pdf_path = tmp_path / "scanned.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(900, 300))
    c.drawImage(str(img_path), 0, 0, width=900, height=300)
    c.save()
    return pdf_path


def test_pypdf_alone_extracts_nothing_from_image_only_pdf(tmp_path):
    import pypdf

    pdf_path = _make_scanned_pdf(tmp_path)
    reader = pypdf.PdfReader(str(pdf_path))
    assert (reader.pages[0].extract_text() or "").strip() == ""


def test_ocr_fallback_recovers_text(tmp_path):
    pdf_path = _make_scanned_pdf(tmp_path)
    doc = parse_document(pdf_path)

    assert doc.ocr_used is True
    recovered = doc.pages[0].text.lower()
    assert "photosynthesis" in recovered
    assert "energy" in recovered
