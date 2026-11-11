from types import SimpleNamespace

import pytest

from sokhan.asr import ASRConfigurationError, FasterWhisperASR


class FakeModel:
    def transcribe(self, path, **kwargs):
        assert kwargs["language"] == "en"
        assert kwargs["word_timestamps"] is True
        return iter([
            SimpleNamespace(start=0.125, end=1.75, text=" Hello world "),
            SimpleNamespace(start=2.0, end=2.5, text=" Goodbye "),
        ]), SimpleNamespace(language="en")


def test_asr_maps_segments_to_milliseconds(tmp_path):
    audio = tmp_path / "speech.wav"
    audio.write_bytes(b"fake")
    engine = FasterWhisperASR(model=FakeModel())
    segments = engine.transcribe(audio)
    assert [(s.start_ms, s.end_ms, s.text) for s in segments] == [
        (125, 1750, "Hello world"), (2000, 2500, "Goodbye")
    ]


def test_asr_rejects_missing_audio(tmp_path):
    engine = FasterWhisperASR(model=FakeModel())
    with pytest.raises(FileNotFoundError):
        engine.transcribe(tmp_path / "missing.wav")


def test_asr_requires_optional_dependency_when_not_injected(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("blocked for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ASRConfigurationError, match="audio extra"):
        FasterWhisperASR()
