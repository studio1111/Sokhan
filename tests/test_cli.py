from sokhan.cli import build_parser


def test_pdf_translation_cli_requires_a_font():
    args = build_parser().parse_args([
        "pdf-to-fa", "source.pdf", "translated.pdf", "--font", "/fonts/persian.ttf"
    ])
    assert args.command == "pdf-to-fa"
    assert args.font == "/fonts/persian.ttf"


def test_text_to_speech_cli_accepts_stdin_and_output():
    args = build_parser().parse_args(["text-to-speech", "speech.txt", "speech.wav"])
    assert args.command == "text-to-speech"
    assert args.input == "speech.txt"
    assert args.output == "speech.wav"


def test_srt_fit_cli_requires_media_duration():
    args = build_parser().parse_args([
        "srt-fit", "source.srt", "fitted.srt", "--media-duration-ms", "120000"
    ])
    assert args.command == "srt-fit"
    assert args.media_duration_ms == 120000


def test_pdf_extraction_cli_requires_explicit_ocr_opt_in():
    args = build_parser().parse_args([
        "extract-pdf", "scan.pdf", "--ocr", "--ocr-language", "eng",
        "--ocr-dpi", "240", "--ocr-max-pages", "12",
    ])
    assert args.ocr is True
    assert args.ocr_language == "eng"
    assert args.ocr_dpi == 240
    assert args.ocr_max_pages == 12


def test_pdf_translation_cli_can_enable_ocr_explicitly():
    args = build_parser().parse_args([
        "pdf-to-fa", "scan.pdf", "translated.pdf", "--font", "fa.ttf", "--ocr",
    ])
    assert args.ocr is True
