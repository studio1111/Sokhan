"""PDF text extraction, translation, and Persian RTL PDF generation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .contracts import Translator


class PDFExtractionError(RuntimeError):
    pass


class PDFOutputError(RuntimeError):
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
) -> Path:
    """Extract, translate in bounded chunks, and render an RTL Persian PDF."""
    destination = Path(output_path)
    if destination.exists():
        raise FileExistsError(destination)
    source = extract_pdf_text(str(input_path))
    chunks = split_text_chunks(source, chunk_size)
    from .workflows import translate_text

    translated = [
        translate_text(chunk, translator, register=register) for chunk in chunks
    ]
    return write_persian_pdf("\n\n".join(translated), destination, font_path)
