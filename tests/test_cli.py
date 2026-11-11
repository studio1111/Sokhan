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

def test_audio_to_json_cli_preserves_word_timestamps(tmp_path, monkeypatch):
    import json

    from sokhan import cli
    from sokhan.contracts import SpeechSegment, WordTiming

    audio = tmp_path / "input.wav"
    audio.write_bytes(b"fixture")
    output = tmp_path / "transcript.json"

    class FakeASR:
        def __init__(self, **kwargs):
            assert kwargs == {"model_name": "small.en", "device": "cpu"}

        def transcribe(self, path):
            assert path == str(audio)
            return [
                SpeechSegment(
                    100, 900, "Hello",
                    words=(WordTiming(100, 900, "Hello", 0.91),),
                )
            ]

    monkeypatch.setattr(cli, "FasterWhisperASR", FakeASR)
    monkeypatch.setattr(
        "sys.argv",
        ["sokhan", "audio-to-json", str(audio), str(output)],
    )

    assert cli.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["segments"][0]["words"][0]["probability"] == 0.91
