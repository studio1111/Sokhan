from pathlib import Path

import pytest

from sokhan.speech import LocalSpeechSynthesizer, SpeechSynthesisError


class _Headers:
    def get_content_type(self):
        return "audio/wav"


class _Response:
    headers = _Headers()

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.payload[:limit]


class _Opener:
    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def open(self, request, timeout):
        self.request = request
        return _Response(self.payload)


def _wav():
    return b"RIFF" + (b"\x00" * 4) + b"WAVE" + b"data"


def test_synthesizer_writes_wav_without_overwriting(tmp_path: Path):
    engine = LocalSpeechSynthesizer()
    opener = _Opener(_wav())
    engine._opener = opener
    target = tmp_path / "speech.wav"
    assert engine.synthesize("سلام", target) == target
    assert target.read_bytes() == _wav()
    with pytest.raises(FileExistsError):
        engine.synthesize("سلام", target)


def test_synthesizer_rejects_non_wav_response(tmp_path: Path):
    engine = LocalSpeechSynthesizer()
    engine._opener = _Opener(b"not audio")
    with pytest.raises(SpeechSynthesisError, match="valid WAV"):
        engine.synthesize("سلام", tmp_path / "bad.wav")


def test_synthesizer_rejects_empty_and_oversized_text(tmp_path: Path):
    with pytest.raises(ValueError, match="must not be empty"):
        LocalSpeechSynthesizer().synthesize(" ", tmp_path / "empty.wav")
    engine = LocalSpeechSynthesizer(max_text_chars=2)
    with pytest.raises(ValueError, match="exceeds"):
        engine.synthesize("سلام", tmp_path / "large.wav")
