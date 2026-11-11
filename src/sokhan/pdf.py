"""Optional PDF text extraction. Scanned PDFs require a separately configured OCR engine."""

from __future__ import annotations


class PDFExtractionError(RuntimeError):
    pass


def extract_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFExtractionError("install the PDF extra: pip install 'sokhan[pdf]'") from exc
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PDFExtractionError("encrypted PDFs are not supported")
        text = "\n\n".join(value for page in reader.pages
                            if (value := (page.extract_text() or "").strip()))
        if not text:
            raise PDFExtractionError("no extractable text found; scanned PDFs need OCR")
        return text
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError("could not extract PDF text") from exc
