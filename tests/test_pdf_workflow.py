from pathlib import Path

import pytest

from sokhan.contracts import TranslationResult
from sokhan.pdf import PDFOutputError, split_text_chunks, translate_pdf, write_persian_pdf


class FakeTranslator:
    def __init__(self):
        self.requests = []

    def translate(self, request):
        self.requests.append(request.text)
        return TranslationResult(text=f"ترجمه {len(self.requests)}", model="test")


def test_split_text_chunks_respects_limit_and_preserves_content():
    source = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = split_text_chunks(source, max_chars=24)
    assert all(len(chunk) <= 24 for chunk in chunks)
    assert " ".join(chunks).replace(" ", "") == source.replace("\n", "").replace(" ", "")


def test_translate_pdf_chunks_extracted_text(monkeypatch, tmp_path: Path):
    from sokhan import pdf

    monkeypatch.setattr(pdf, "extract_pdf_text", lambda _path, **_kwargs: "A" * 20 + "\n\n" + "B" * 20)
    captured = {}
    monkeypatch.setattr(
        pdf, "write_persian_pdf",
        lambda text, output, font: captured.update(text=text, output=output, font=font),
    )
    translator = FakeTranslator()
    destination = tmp_path / "translated.pdf"
    translate_pdf("source.pdf", destination, translator, font_path="font.ttf", chunk_size=24)
    assert len(translator.requests) == 2
    assert captured["text"] == "ترجمه 1\n\nترجمه 2"
    assert captured["output"] == destination


def test_split_text_chunks_rejects_invalid_limit():
    with pytest.raises(ValueError):
        split_text_chunks("text", 0)


def test_pdf_writer_requires_existing_ttf_font(tmp_path: Path):
    with pytest.raises(PDFOutputError, match="font file"):
        write_persian_pdf("متن فارسی", tmp_path / "out.pdf", tmp_path / "missing.ttf")


def test_pdf_writer_renders_a_persian_page_when_system_font_is_available(tmp_path: Path):
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
    ]
    font = next((candidate for candidate in candidates if candidate.is_file()), None)
    if font is None:
        pytest.skip("no system TrueType font with Arabic/Persian glyphs is installed")
    output = tmp_path / "persian.pdf"
    assert write_persian_pdf("سلام دنیا\nاین یک آزمون فارسی است.", output, font) == output
    assert output.read_bytes().startswith(b"%PDF")


def test_ocr_pdf_text_uses_bounded_local_tesseract_pages(monkeypatch, tmp_path: Path):
    import sys
    from types import SimpleNamespace

    from sokhan.pdf import ocr_pdf_text

    calls = []

    class Page:
        def __init__(self, number):
            self.number = number

        def get_textpage_ocr(self, *, language, dpi, full):
            calls.append((self.number, language, dpi, full))
            return f"ocr-page-{self.number}"

        def get_text(self, *, textpage):
            return f"Scanned page {self.number}"

    class Document:
        is_encrypted = False

        def __len__(self):
            return 2

        def __iter__(self):
            return iter([Page(1), Page(2)])

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setitem(sys.modules, "pymupdf", SimpleNamespace(open=lambda _path: Document()))
    source = tmp_path / "scanned.pdf"
    source.touch()

    assert ocr_pdf_text(source, language="eng", dpi=240, max_pages=2) == (
        "Scanned page 1\n\nScanned page 2"
    )
    assert calls == [(1, "eng", 240, True), (2, "eng", 240, True)]


def test_ocr_pdf_text_rejects_unsafe_limits_and_language(tmp_path: Path):
    from sokhan.pdf import ocr_pdf_text

    source = tmp_path / "scanned.pdf"
    source.touch()
    with pytest.raises(ValueError, match="DPI"):
        ocr_pdf_text(source, dpi=601)
    with pytest.raises(ValueError, match="language"):
        ocr_pdf_text(source, language="eng; touch /tmp/pwned")


def test_ocr_pdf_text_rejects_encrypted_and_oversized_documents(monkeypatch, tmp_path: Path):
    import sys
    from types import SimpleNamespace

    from sokhan.pdf import PDFExtractionError, ocr_pdf_text

    class Document:
        is_encrypted = True

        def __len__(self):
            return 3

        def __iter__(self):
            return iter(())

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setitem(sys.modules, "pymupdf", SimpleNamespace(open=lambda _path: Document()))
    source = tmp_path / "scanned.pdf"
    source.touch()
    with pytest.raises(PDFExtractionError, match="encrypted"):
        ocr_pdf_text(source)

    Document.is_encrypted = False
    with pytest.raises(PDFExtractionError, match="page limit"):
        ocr_pdf_text(source, max_pages=2)


def test_pdf_extraction_can_explicitly_fallback_to_ocr(monkeypatch, tmp_path: Path):
    from sokhan import pdf

    monkeypatch.setattr(pdf, "ocr_pdf_text", lambda path, **kwargs: "OCR result")
    monkeypatch.setattr(pdf, "_extract_pdf_text_native", lambda path: "")
    assert pdf.extract_pdf_text(tmp_path / "scanned.pdf", ocr=True) == "OCR result"


def test_ocr_pdf_text_reports_missing_optional_runtime(monkeypatch, tmp_path: Path):
    import sys

    from sokhan.pdf import PDFExtractionError, ocr_pdf_text

    monkeypatch.setitem(sys.modules, "pymupdf", None)
    source = tmp_path / "scanned.pdf"
    source.touch()
    with pytest.raises(PDFExtractionError, match="sokhan\\[ocr\\]"):
        ocr_pdf_text(source)


def test_ocr_pdf_text_enforces_hard_page_limit(tmp_path: Path):
    from sokhan.pdf import ocr_pdf_text

    source = tmp_path / "scanned.pdf"
    source.touch()
    with pytest.raises(ValueError, match="2000"):
        ocr_pdf_text(source, max_pages=2001)


def test_translate_pdf_forwards_explicit_ocr_configuration(monkeypatch, tmp_path: Path):
    from sokhan import pdf

    captured = {}
    monkeypatch.setattr(
        pdf, "extract_pdf_text",
        lambda path, **kwargs: captured.update(options=kwargs) or "Hello",
    )
    monkeypatch.setattr(
        pdf, "write_persian_pdf",
        lambda text, output, font: output,
    )
    result = translate_pdf(
        "scan.pdf", tmp_path / "translated.pdf", FakeTranslator(),
        font_path="font.ttf", ocr=True, ocr_language="eng+fas",
        ocr_dpi=240, ocr_max_pages=12,
    )
    assert result == tmp_path / "translated.pdf"
    assert captured["options"] == {
        "ocr": True, "ocr_language": "eng+fas", "ocr_dpi": 240, "ocr_max_pages": 12,
    }
