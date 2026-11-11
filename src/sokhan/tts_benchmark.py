"""Resource and latency benchmark for a configured local TTS adapter.

This measures runtime and WAV output characteristics only. It does not assess
speech intelligibility, pronunciation, naturalness, prosody, or speaker similarity.
"""

from __future__ import annotations

import math
import statistics
import tempfile
import time
import wave
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class SpeechSynthesizer(Protocol):
    model: str

    def synthesize(self, text: str, output_path: str | Path) -> Path: ...


@dataclass(frozen=True, slots=True)
class TTSBenchmarkReport:
    """Aggregate runtime metrics; deliberately excludes input text and generated audio."""

    model: str
    sample_count: int
    total_audio_duration_ms: int
    total_synthesis_duration_ms: int
    median_latency_ms: float
    p95_latency_ms: float
    real_time_factor: float
    output_bytes: int
    sample_rate_hz: int
    channels: int


def _inspect_wav(path: Path) -> tuple[int, int, int, int]:
    try:
        with wave.open(str(path), "rb") as audio:
            channels = audio.getnchannels()
            sample_width = audio.getsampwidth()
            sample_rate = audio.getframerate()
            frames = audio.getnframes()
            compression = audio.getcomptype()
    except (OSError, EOFError, wave.Error) as exc:
        raise ValueError("TTS benchmark requires a valid PCM WAV output") from exc
    if compression != "NONE" or sample_width != 2:
        raise ValueError("TTS benchmark requires uncompressed 16-bit PCM WAV")
    if channels not in {1, 2} or not 8_000 <= sample_rate <= 96_000:
        raise ValueError("TTS WAV must be mono/stereo with a sample rate from 8 to 96 kHz")
    if frames < 1:
        raise ValueError("TTS WAV output must contain at least one audio frame")
    return channels, sample_rate, frames, path.stat().st_size


def benchmark_speech(
    texts: Sequence[str],
    synthesizer: SpeechSynthesizer,
) -> TTSBenchmarkReport:
    """Run local synthesis samples and report reproducible runtime/audio metrics.

    Temporary WAV files are deleted on success or failure. No source text or
    synthesized audio is included in the returned report.
    """
    if not texts:
        raise ValueError("provide at least one benchmark sample")
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("benchmark sample text must not be empty")

    latencies: list[float] = []
    total_duration_ms = 0
    total_bytes = 0
    common_format: tuple[int, int] | None = None

    with tempfile.TemporaryDirectory(prefix="sokhan-tts-benchmark-") as temporary:
        for index, text in enumerate(texts):
            output = Path(temporary) / f"sample-{index:04d}.wav"
            started = time.perf_counter()
            synthesizer.synthesize(text, output)
            latency_ms = (time.perf_counter() - started) * 1_000
            if not output.is_file():
                raise ValueError("TTS engine did not create its requested WAV output")
            channels, sample_rate, frames, output_size = _inspect_wav(output)
            current_format = (channels, sample_rate)
            if common_format is None:
                common_format = current_format
            elif current_format != common_format:
                raise ValueError("all benchmark samples must use the same sample rate and channels")
            duration_ms = round(frames * 1_000 / sample_rate)
            if duration_ms < 1:
                raise ValueError("TTS WAV duration is below one millisecond")
            latencies.append(latency_ms)
            total_duration_ms += duration_ms
            total_bytes += output_size

    ordered_latencies = sorted(latencies)
    p95_index = max(0, math.ceil(0.95 * len(ordered_latencies)) - 1)
    total_latency_ms = sum(latencies)
    channels, sample_rate = common_format or (0, 0)
    return TTSBenchmarkReport(
        model=str(getattr(synthesizer, "model", "unspecified")),
        sample_count=len(latencies),
        total_audio_duration_ms=total_duration_ms,
        total_synthesis_duration_ms=round(total_latency_ms),
        median_latency_ms=round(statistics.median(latencies), 3),
        p95_latency_ms=round(ordered_latencies[p95_index], 3),
        real_time_factor=round(total_latency_ms / total_duration_ms, 4),
        output_bytes=total_bytes,
        sample_rate_hz=sample_rate,
        channels=channels,
    )
