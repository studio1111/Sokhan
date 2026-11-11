"""Local WAV synthesis and timestamp-aligned subtitle dubbing."""
from __future__ import annotations

import tempfile
import wave
from collections.abc import Mapping, Sequence
from pathlib import Path

from .subtitles import Cue

_MAX_OUTPUT_DURATION_MS = 3_600_000
_MAX_TOTAL_AUDIO_BYTES = 256 * 1024 * 1024
_SILENCE_CHUNK_FRAMES = 8_192


class DubbingError(RuntimeError):
    """Raised when local dubbing audio cannot be assembled safely."""


def _read_pcm16_mono(path: Path, *, max_bytes: int) -> tuple[int, int, bytes]:
    try:
        with wave.open(str(path), "rb") as source:
            if source.getcomptype() != "NONE":
                raise ValueError(f"cue audio must be uncompressed PCM: {path.name}")
            if source.getnchannels() != 1:
                raise ValueError(f"cue audio must be mono: {path.name}")
            if source.getsampwidth() != 2:
                raise ValueError(f"cue audio must use 16-bit PCM: {path.name}")
            sample_rate = source.getframerate()
            if not 8_000 <= sample_rate <= 48_000:
                raise ValueError("cue audio sample rate must be between 8000 and 48000 Hz")
            frame_count = source.getnframes()
            if frame_count < 1:
                raise ValueError(f"cue audio is empty: {path.name}")
            if frame_count * 2 > max_bytes:
                raise ValueError("total synthesized cue audio exceeds 256 MiB")
            payload = source.readframes(frame_count)
            if len(payload) != frame_count * 2:
                raise ValueError(f"cue audio is truncated: {path.name}")
            return sample_rate, frame_count, payload
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"invalid WAV file: {path.name}") from exc


def _write_silence(output: wave.Wave_write, frame_count: int) -> None:
    silence = b"\0" * (_SILENCE_CHUNK_FRAMES * 2)
    remaining = frame_count
    while remaining:
        chunk_frames = min(remaining, _SILENCE_CHUNK_FRAMES)
        output.writeframesraw(silence[:chunk_frames * 2])
        remaining -= chunk_frames


def _validate_timeline(
    cues: Sequence[Cue], media_duration_ms: int | None = None
) -> int:
    """Validate cue ordering and output bounds before any expensive synthesis work."""
    if not cues:
        raise ValueError("at least one subtitle cue is required")
    previous_index = 0
    previous_end_ms = 0
    for cue in cues:
        if cue.index <= previous_index:
            raise ValueError("subtitle cue indices must be strictly increasing")
        if cue.start_ms < previous_end_ms:
            raise ValueError("overlapping subtitle cues cannot be stitched")
        previous_index = cue.index
        previous_end_ms = cue.end_ms

    if media_duration_ms is not None:
        if (
            not isinstance(media_duration_ms, int)
            or isinstance(media_duration_ms, bool)
            or media_duration_ms < previous_end_ms
        ):
            raise ValueError("media duration must be an integer covering the final cue")
        duration_ms = media_duration_ms
    else:
        duration_ms = previous_end_ms
    if duration_ms > _MAX_OUTPUT_DURATION_MS:
        raise ValueError("dubbed output is limited to one hour")
    return duration_ms


def stitch_srt_audio(
    cues: Sequence[Cue],
    audio_paths: Mapping[int, str | Path],
    output_path: str | Path,
    *,
    media_duration_ms: int | None = None,
) -> Path:
    """Place mono PCM16 cue clips on the SRT timeline, padding all gaps with silence.

    Clips are never truncated or time-stretched. A clip longer than its cue window,
    overlapping cues, or incompatible WAV formats are rejected.
    """
    duration_ms = _validate_timeline(cues, media_duration_ms)
    expected_indices = {cue.index for cue in cues}
    if set(audio_paths) != expected_indices:
        missing = sorted(expected_indices - set(audio_paths))
        if missing:
            raise FileNotFoundError(f"missing synthesized audio for cue {missing[0]}")
        raise ValueError("audio path mapping contains unknown cue indices")

    destination = Path(output_path)
    if not destination.parent.is_dir():
        raise DubbingError("output directory does not exist")

    loaded: dict[int, bytes] = {}
    sample_rate: int | None = None
    total_audio_bytes = 0
    for cue in cues:
        source = Path(audio_paths[cue.index])
        if not source.is_file():
            raise FileNotFoundError(f"synthesized audio does not exist for cue {cue.index}")
        if source.resolve() == destination.resolve():
            raise DubbingError("output path cannot overwrite a cue audio input")
        rate, frame_count, payload = _read_pcm16_mono(
            source, max_bytes=_MAX_TOTAL_AUDIO_BYTES - total_audio_bytes
        )
        if sample_rate is None:
            sample_rate = rate
        elif rate != sample_rate:
            raise ValueError("all cue audio must use the same sample rate")
        start_frame = (cue.start_ms * rate + 500) // 1_000
        end_frame = (cue.end_ms * rate + 500) // 1_000
        if frame_count > end_frame - start_frame:
            raise ValueError(f"audio for cue {cue.index} exceeds cue duration; refusing to truncate")
        total_audio_bytes += len(payload)
        if total_audio_bytes > _MAX_TOTAL_AUDIO_BYTES:
            raise ValueError("total synthesized cue audio exceeds 256 MiB")
        loaded[cue.index] = payload

    assert sample_rate is not None
    total_frames = (duration_ms * sample_rate + 500) // 1_000
    if total_frames * 2 > 512 * 1024 * 1024:
        raise ValueError("dubbed output exceeds the 512 MiB output limit")

    stream = destination.open("xb")
    try:
        with stream, wave.open(stream, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            cursor = 0
            for cue in cues:
                start_frame = (cue.start_ms * sample_rate + 500) // 1_000
                end_frame = (cue.end_ms * sample_rate + 500) // 1_000
                if start_frame < cursor:
                    raise ValueError("subtitle cues collide at the output sample rate")
                _write_silence(output, start_frame - cursor)
                payload = loaded[cue.index]
                output.writeframesraw(payload)
                cursor = start_frame + len(payload) // 2
                _write_silence(output, end_frame - cursor)
                cursor = end_frame
            _write_silence(output, total_frames - cursor)
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def synthesize_srt(
    cues: Sequence[Cue],
    synthesizer,
    output_path: str | Path,
    *,
    media_duration_ms: int | None = None,
) -> Path:
    """Synthesize every Persian cue through a local adapter, then stitch the WAV track."""
    _validate_timeline(cues, media_duration_ms)
    destination = Path(output_path)
    if destination.exists():
        raise FileExistsError(destination)
    if not destination.parent.is_dir():
        raise DubbingError("output directory does not exist")
    with tempfile.TemporaryDirectory(prefix="sokhan-dub-") as temporary:
        directory = Path(temporary)
        audio_paths: dict[int, Path] = {}
        for cue in cues:
            clip = directory / f"{cue.index:06d}.wav"
            synthesizer.synthesize(cue.text, clip)
            if not clip.is_file():
                raise DubbingError(f"TTS engine did not create audio for cue {cue.index}")
            audio_paths[cue.index] = clip
        return stitch_srt_audio(
            cues, audio_paths, output_path, media_duration_ms=media_duration_ms
        )
