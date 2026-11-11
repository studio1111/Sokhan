from sokhan.contracts import SpeechSegment, TranslationResult
from sokhan.subtitles import Cue
from sokhan.workflows import audio_to_srt, translate_srt, translate_text


class FakeTranslator:
    def translate(self, request):
        return TranslationResult(text="  سلام ؟ ", model="test")


class FakeASR:
    def transcribe(self, audio_path):
        return [SpeechSegment(125, 1750, "Hello world")]


def test_translate_text_normalizes_persian():
    assert translate_text("Hello", FakeTranslator()) == "سلام؟"


def test_translate_srt_preserves_timing_and_indices():
    source = [Cue(7, 1000, 2500, "Hello")]
    result = translate_srt(source, FakeTranslator())
    assert result == [Cue(7, 1000, 2500, "سلام؟")]


def test_audio_to_srt_preserves_asr_timestamps():
    cues = audio_to_srt("speech.wav", FakeASR(), FakeTranslator())
    assert cues == [Cue(1, 125, 1750, "سلام؟")]


def test_audio_to_dub_runs_asr_translation_and_local_synthesis(tmp_path):
    import struct
    import wave

    from sokhan.workflows import audio_to_dub

    class FakeSynthesizer:
        def synthesize(self, text, output_path):
            with wave.open(str(output_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(8_000)
                output.writeframes(struct.pack("<h", 1000) * 400)

    output = tmp_path / "dub.wav"
    result = audio_to_dub(
        "speech.wav", FakeASR(), FakeTranslator(), FakeSynthesizer(), output,
        media_duration_ms=2_000,
    )
    assert result == output
    assert output.read_bytes().startswith(b"RIFF")
