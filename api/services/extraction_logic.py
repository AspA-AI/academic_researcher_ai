import io
import re
import asyncio
import aiohttp
from typing import Dict, Any
import pdfplumber
from PIL import Image


# =========================
# Text Validation
# =========================

def _is_valid_text(text: str) -> bool:
    if not text or len(text) < 800:
        return False

    # Detect hex / glyph garbage
    if text.count("/x") > 3:
        return False

    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return alpha_ratio > 0.6


# =========================
# Extraction Strategies
# =========================

def _extract_pymupdf(pdf_bytes: bytes) -> str:
    # Optional dependency path: PyMuPDF provides best-in-class text extraction for many PDFs.
    try:
        import fitz  # type: ignore  # PyMuPDF
    except Exception as e:
        raise RuntimeError("PyMuPDF is not installed. Install `PyMuPDF` to enable pymupdf extraction.") from e

    text = ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        text += page.get_text()
    return text


def _extract_pdfplumber(pdf_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def _extract_ocr(pdf_bytes: bytes) -> str:
    # Optional dependency path: OCR requires `pdf2image` + Poppler and `pytesseract` + Tesseract.
    try:
        from pdf2image import convert_from_bytes  # type: ignore
        import pytesseract  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "OCR extraction requires optional dependencies: `pdf2image` and `pytesseract` "
            "(and system tools Poppler + Tesseract)."
        ) from e

    images = convert_from_bytes(pdf_bytes, dpi=300)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="eng")
    return text


EXTRACTION_PIPELINE = [
    ("pymupdf", _extract_pymupdf),
    ("pdfplumber", _extract_pdfplumber),
    ("ocr", _extract_ocr),
]


# =========================
# Unified Public Function
# =========================

async def extract_paper_content(
    pdf_url: str,
    paper_id: str
) -> Dict[str, Any]:
    """
    Robust PDF extractor for ALL sources:
    arXiv, CORE, OpenAlex, EuropePMC, Semantic Scholar, Crossref, Unpaywall
    """

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url, timeout=60) as response:
                if response.status != 200:
                    return {
                        "paper_id": paper_id,
                        "status": "failed",
                        "error": f"HTTP {response.status}"
                    }

                pdf_bytes = await response.read()

        if not pdf_bytes.startswith(b"%PDF"):
            return {
                "paper_id": paper_id,
                "status": "failed",
                "error": "Not a valid PDF"
            }

        for method_name, extractor in EXTRACTION_PIPELINE:
            try:
                text = extractor(pdf_bytes)

                if _is_valid_text(text):
                    return {
                        "paper_id": paper_id,
                        "status": "success",
                        "method": method_name,
                        "word_count": len(text.split()),
                        "content": text.strip()
                    }

            except Exception:
                continue

        return {
            "paper_id": paper_id,
            "status": "failed",
            "error": "All extraction strategies failed"
        }

    except Exception as e:
        return {
            "paper_id": paper_id,
            "status": "failed",
            "error": str(e)
        }
