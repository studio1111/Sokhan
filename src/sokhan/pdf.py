"""PDF text extraction, optional local OCR, translation, and Persian RTL output."""
from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .contracts import Translator

_OCR_LANGUAGE = re.compile(r"^[A-Za-z0-9_+-]{2,32}$")


class PDFExtractionError(RuntimeError):
    """Raised when PDF text cannot be extracted safely."""


class PDFOutputError(RuntimeError):
    """Raised when Persian PDF output cannot be generated."""


def _extract_pdf_text_native(path: str | Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFExtractionError("install the PDF extra: pip install 'sokhan[pdf]'") from exc
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise PDFExtractionError("encrypted PDFs are not supported")
        return "\n\n".join(
            value for page in reader.pages if (value := (page.extract_text() or "").strip())
        )
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError("could not extract PDF text") from exc


def ocr_pdf_text(
    path: str | Path,
    *,
    language: str = "eng",
    dpi: int = 300,
    max_pages: int = 200,
) -> str:
    """OCR every page locally using PyMuPDF's Tesseract integration.

    PyMuPDF, the Tesseract executable, and the requested language data must be
    installed by the user. Sokhan never downloads OCR engines or language packs.
    """
    if not _OCR_LANGUAGE.fullmatch(language):
        raise ValueError("OCR language must be a simple Tesseract language code")
    if not isinstance(dpi, int) or isinstance(dpi, bool) or not 72 <= dpi <= 600:
        raise ValueError("OCR DPI must be an integer between 72 and 600")
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 2_000:
        raise ValueError("OCR page limit must be an integer between 1 and 2000")

    try:
        import pymupdf
    except ImportError as exc:
        raise PDFExtractionError("install the OCR extra: pip install 'sokhan[ocr]'") from exc

    try:
        with pymupdf.open(path) as document:
            if document.is_encrypted:
                raise PDFExtractionError("encrypted PDFs are not supported")
            page_count = len(document)
            if page_count > max_pages:
                raise PDFExtractionError(
                    f"PDF has {page_count} pages; configured OCR page limit is {max_pages}"
                )
            extracted = []
            for page in document:
                text_page = page.get_textpage_ocr(language=language, dpi=dpi, full=True)
                text = page.get_text(textpage=text_page).strip()
                if text:
                    extracted.append(text)
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(
            "local OCR failed; verify the Tesseract executable and requested language data"
        ) from exc

    if not extracted:
        raise PDFExtractionError("OCR found no readable text in the PDF")
    return "\n\n".join(extracted)


def extract_pdf_text(
    path: str | Path,
    *,
    ocr: bool = False,
    ocr_language: str = "eng",
    ocr_dpi: int = 300,
    ocr_max_pages: int = 200,
) -> str:
    """Extract native PDF text, optionally using OCR when no text layer exists."""
    text = _extract_pdf_text_native(path)
    if text.strip():
        return text
    if ocr:
        return ocr_pdf_text(
            path, language=ocr_language, dpi=ocr_dpi, max_pages=ocr_max_pages
        )
    raise PDFExtractionError("no extractable text found; scanned PDFs need explicit OCR")


def split_text_chunks(text: str, max_chars: int = 6_000) -> list[str]:
    """Pack paragraphs into bounded chunks without dropping source characters."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if not text.strip():
        raise ValueError("PDF text must not be empty")
    chunks: list[str] = []
    current = ""
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in text.split("\n\n")]
    for paragraph in (part for part in paragraphs if part):
        pieces: Iterable[str]
        if len(paragraph) <= max_chars:
            pieces = (paragraph,)
        else:
            words = paragraph.split()
            split: list[str] = []
            piece = ""
            for word in words:
                if len(word) > max_chars:
                    if piece:
                        split.append(piece)
                        piece = ""
                    split.extend(word[i:i + max_chars] for i in range(0, len(word), max_chars))
                elif not piece:
                    piece = word
                elif len(piece) + 1 + len(word) <= max_chars:
                    piece += " " + word
                else:
                    split.append(piece)
                    piece = word
            if piece:
                split.append(piece)
            pieces = split
        for piece in pieces:
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) > max_chars:
                chunks.append(current)
                current = piece
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def write_persian_pdf(text: str, output_path: str | Path, font_path: str | Path) -> Path:
    """Write a searchable Persian PDF using HarfBuzz shaping and RTL BiDi layout.

    A user-provided Unicode TTF font is required; no font is bundled or downloaded.
    """
    font = Path(font_path)
    if not font.is_file() or font.suffix.lower() != ".ttf":
        raise PDFOutputError("font file must be an existing TrueType .ttf file")
    if not text.strip():
        raise PDFOutputError("PDF content must not be empty")
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise PDFOutputError("install the PDF extra: pip install 'sokhan[pdf]'") from exc

    try:
        document = FPDF()
        document.set_auto_page_break(auto=True, margin=15)
        document.set_margins(16, 16, 16)
        document.add_page()
        document.add_font("Persian", fname=str(font.resolve()))
        document.set_font("Persian", size=12)
        document.set_text_shaping(
            use_shaping_engine=True, direction="rtl", script="arab", language="fas"
        )
        for paragraph in text.split("\n"):
            if paragraph.strip():
                document.multi_cell(w=document.epw, h=8, text=paragraph, align="R")
            else:
                document.ln(3)
        payload = bytes(document.output())
    except Exception as exc:
        raise PDFOutputError(
            "could not render Persian RTL text; verify the font and install fpdf2 with uharfbuzz"
        ) from exc

    if not payload.startswith(b"%PDF"):
        raise PDFOutputError("PDF renderer returned an invalid document")
    destination = Path(output_path)
    try:
        with destination.open("xb") as output:
            output.write(payload)
    except FileExistsError:
        raise
    except OSError as exc:
        raise PDFOutputError("could not create PDF output") from exc
    return destination


def translate_pdf(
    input_path: str | Path,
    output_path: str | Path,
    translator: Translator,
    *,
    font_path: str | Path,
    register: str = "conversational",
    chunk_size: int = 6_000,
    ocr: bool = False,
    ocr_language: str = "eng",
    ocr_dpi: int = 300,
    ocr_max_pages: int = 200,
) -> Path:
    """Extract, optionally OCR, translate bounded chunks, and render an RTL PDF."""
    destination = Path(output_path)
    if destination.exists():
        raise FileExistsError(destination)
    source = extract_pdf_text(
        input_path,
        ocr=ocr,
        ocr_language=ocr_language,
        ocr_dpi=ocr_dpi,
        ocr_max_pages=ocr_max_pages,
    )
    chunks = split_text_chunks(source, chunk_size)
    from .workflows import translate_text

    translated = [
        translate_text(chunk, translator, register=register) for chunk in chunks
    ]
    return write_persian_pdf("\n\n".join(translated), destination, font_path)
