import subprocess
from pathlib import Path

import pytest

from sokhan.media import AudioExtractionError, extract_audio


def test_extract_audio_invokes_ffmpeg_without_shell(monkeypatch, tmp_path):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"fixture")
    target = tmp_path / "audio.wav"
    monkeypatch.setattr("sokhan.media.shutil.which", lambda _: "/usr/bin/ffmpeg")

    def fake_run(command, **kwargs):
        assert command[0] == "/usr/bin/ffmpeg"
        assert "-vn" in command
        assert kwargs["shell"] is False
        Path(command[-1]).write_bytes(b"RIFFfixture")
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr("sokhan.media.subprocess.run", fake_run)
    assert extract_audio(source, target) == target
    assert target.read_bytes().startswith(b"RIFF")


def test_extract_audio_rejects_missing_ffmpeg(monkeypatch, tmp_path):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"fixture")
    monkeypatch.setattr("sokhan.media.shutil.which", lambda _: None)
    with pytest.raises(AudioExtractionError, match="FFmpeg"):
        extract_audio(source, tmp_path / "audio.wav")


def test_extract_audio_does_not_overwrite_existing_output(monkeypatch, tmp_path):
    source = tmp_path / "input.mp4"
    source.write_bytes(b"fixture")
    target = tmp_path / "audio.wav"
    target.write_bytes(b"existing")
    monkeypatch.setattr("sokhan.media.shutil.which", lambda _: "/usr/bin/ffmpeg")
    with pytest.raises(AudioExtractionError, match="already exists"):
        extract_audio(source, target)
