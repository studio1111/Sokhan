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


def test_srt_to_dub_cli_accepts_optional_media_duration():
    args = build_parser().parse_args([
        "srt-to-dub", "captions.fa.srt", "dub.wav", "--media-duration-ms", "90000",
    ])
    assert args.command == "srt-to-dub"
    assert args.media_duration_ms == 90000


def test_audio_to_dub_cli_accepts_local_asr_options():
    args = build_parser().parse_args([
        "audio-to-dub", "source.wav", "dub.wav", "--asr-model", "small.en",
        "--device", "cpu", "--register", "formal",
    ])
    assert args.command == "audio-to-dub"
    assert args.asr_model == "small.en"
    assert args.device == "cpu"
    assert args.register == "formal"
