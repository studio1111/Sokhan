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

    monkeypatch.setattr(pdf, "extract_pdf_text", lambda _: "A" * 20 + "\n\n" + "B" * 20)
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
