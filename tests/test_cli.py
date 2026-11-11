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

def test_benchmark_tts_cli_writes_aggregate_json_without_source_text(tmp_path, monkeypatch):
    import json
    import wave

    from sokhan import cli

    samples = tmp_path / "samples.txt"
    report = tmp_path / "report.json"
    samples.write_text("private phrase one\n\nprivate phrase two\n", encoding="utf-8")

    class FakeSynthesizer:
        model = "test-local-tts"

        def synthesize(self, text, output_path):
            with wave.open(str(output_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(8_000)
                output.writeframes(b"\x00\x00" * 800)
            return output_path

    monkeypatch.setattr(cli, "synthesizer_from_env", lambda: FakeSynthesizer())
    monkeypatch.setattr(
        "sys.argv",
        ["sokhan", "benchmark-tts", str(samples), str(report)],
    )

    assert cli.main() == 0
    result = json.loads(report.read_text(encoding="utf-8"))
    assert result["sample_count"] == 2
    assert result["model"] == "test-local-tts"
    assert "private phrase" not in report.read_text(encoding="utf-8")
