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
