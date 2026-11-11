import struct
import wave
from pathlib import Path

import pytest

from sokhan.dubbing import stitch_srt_audio, synthesize_srt
from sokhan.subtitles import Cue


def write_wav(path: Path, *, frames: int, sample_rate: int = 8_000, channels: int = 1):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack("<h", 1000) * frames * channels)
    return path


def read_wav(path: Path):
    with wave.open(str(path), "rb") as source:
        return source.getparams(), source.readframes(source.getnframes())


def test_stitch_srt_audio_places_cues_on_timeline_and_pads_silence(tmp_path: Path):
    cues = [Cue(1, 100, 600, "First"), Cue(2, 700, 900, "Second")]
    first = write_wav(tmp_path / "1.wav", frames=800)
    second = write_wav(tmp_path / "2.wav", frames=400)
    output = tmp_path / "dub.wav"

    stitch_srt_audio(cues, {1: first, 2: second}, output, media_duration_ms=1_000)

    params, raw = read_wav(output)
    samples = struct.unpack("<" + "h" * params.nframes, raw)
    assert params.framerate == 8_000
    assert params.nchannels == 1
    assert params.sampwidth == 2
    assert params.nframes == 8_000
    assert samples[0:800] == (0,) * 800
    assert samples[800:1600] == (1000,) * 800
    assert samples[1600:4800] == (0,) * 3_200
    assert samples[5600:6000] == (1000,) * 400
    assert samples[7200:] == (0,) * 800


def test_stitch_srt_audio_rejects_overlapping_cues(tmp_path: Path):
    cues = [Cue(1, 0, 500, "First"), Cue(2, 400, 800, "Second")]
    clip1 = write_wav(tmp_path / "1.wav", frames=100)
    clip2 = write_wav(tmp_path / "2.wav", frames=100)
    with pytest.raises(ValueError, match="overlap"):
        stitch_srt_audio(cues, {1: clip1, 2: clip2}, tmp_path / "out.wav")


def test_stitch_srt_audio_rejects_clip_longer_than_cue(tmp_path: Path):
    cues = [Cue(1, 0, 100, "Too long")]
    clip = write_wav(tmp_path / "long.wav", frames=801)
    with pytest.raises(ValueError, match="exceeds cue"):
        stitch_srt_audio(cues, {1: clip}, tmp_path / "out.wav")


def test_stitch_srt_audio_rejects_sample_rate_mismatch(tmp_path: Path):
    cues = [Cue(1, 0, 500, "First"), Cue(2, 600, 900, "Second")]
    clips = {
        1: write_wav(tmp_path / "1.wav", frames=100, sample_rate=8_000),
        2: write_wav(tmp_path / "2.wav", frames=100, sample_rate=16_000),
    }
    with pytest.raises(ValueError, match="sample rate"):
        stitch_srt_audio(cues, clips, tmp_path / "out.wav")


def test_stitch_srt_audio_rejects_stereo_wav(tmp_path: Path):
    cues = [Cue(1, 0, 500, "Stereo")]
    clip = write_wav(tmp_path / "stereo.wav", frames=100, channels=2)
    with pytest.raises(ValueError, match="mono"):
        stitch_srt_audio(cues, {1: clip}, tmp_path / "out.wav")


def test_stitch_srt_audio_rejects_missing_audio_and_empty_cues(tmp_path: Path):
    with pytest.raises(ValueError, match="at least one"):
        stitch_srt_audio([], {}, tmp_path / "empty.wav")
    cues = [Cue(1, 0, 500, "Missing")]
    with pytest.raises(FileNotFoundError):
        stitch_srt_audio(cues, {}, tmp_path / "missing.wav")


def test_stitch_srt_audio_preserves_existing_output(tmp_path: Path):
    cues = [Cue(1, 0, 500, "One")]
    clip = write_wav(tmp_path / "clip.wav", frames=100)
    output = tmp_path / "existing.wav"
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        stitch_srt_audio(cues, {1: clip}, output)
    assert output.read_bytes() == b"keep"


def test_stitch_srt_audio_rejects_duration_over_one_hour(tmp_path: Path):
    cues = [Cue(1, 0, 100, "One")]
    clip = write_wav(tmp_path / "clip.wav", frames=100)
    with pytest.raises(ValueError, match="one hour"):
        stitch_srt_audio(cues, {1: clip}, tmp_path / "long.wav", media_duration_ms=3_600_001)


class FakeSynthesizer:
    def __init__(self):
        self.texts = []

    def synthesize(self, text, output_path):
        self.texts.append(text)
        write_wav(Path(output_path), frames=400)


def test_synthesize_srt_creates_timed_dub_track(tmp_path: Path):
    synthesizer = FakeSynthesizer()
    cues = [Cue(1, 100, 500, "سلام"), Cue(2, 600, 900, "دنیا")]
    output = tmp_path / "dub.wav"

    synthesize_srt(cues, synthesizer, output, media_duration_ms=1_000)

    params, _raw = read_wav(output)
    assert params.nframes == 8_000
    assert synthesizer.texts == ["سلام", "دنیا"]

def test_stitch_srt_audio_rejects_oversized_wav_before_reading_payload(tmp_path: Path):
    data_size = 256 * 1024 * 1024 + 2
    header = (
        b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, 48_000, 96_000, 2, 16)
        + b"data" + struct.pack("<I", data_size)
    )
    oversized = tmp_path / "oversized.wav"
    oversized.write_bytes(header)
    output = tmp_path / "dub.wav"
    cues = [Cue(1, 0, 3_600_000, "Long cue")]

    with pytest.raises(ValueError, match="256 MiB"):
        stitch_srt_audio(cues, {1: oversized}, output)

    assert not output.exists()


def test_synthesize_srt_validates_timeline_before_calling_tts(tmp_path: Path):
    class RecordingSynthesizer(FakeSynthesizer):
        def synthesize(self, text, output_path):
            super().synthesize(text, output_path)

    synthesizer = RecordingSynthesizer()
    cues = [Cue(1, 0, 500, "First"), Cue(2, 400, 800, "Overlapping")]
    output = tmp_path / "dub.wav"

    with pytest.raises(ValueError, match="overlapping"):
        synthesize_srt(cues, synthesizer, output)

    assert synthesizer.texts == []
    assert not output.exists()


def test_synthesize_srt_validates_media_duration_before_calling_tts(tmp_path: Path):
    synthesizer = FakeSynthesizer()
    cues = [Cue(1, 0, 500, "One")]

    with pytest.raises(ValueError, match="covering the final cue"):
        synthesize_srt(cues, synthesizer, tmp_path / "dub.wav", media_duration_ms=100)

    assert synthesizer.texts == []


def test_synthesize_srt_rejects_duplicate_cue_indices_before_calling_tts(tmp_path: Path):
    synthesizer = FakeSynthesizer()
    cues = [Cue(1, 0, 300, "First"), Cue(1, 400, 700, "Second")]

    with pytest.raises(ValueError, match="indices must be strictly increasing"):
        synthesize_srt(cues, synthesizer, tmp_path / "dub.wav")

    assert synthesizer.texts == []
