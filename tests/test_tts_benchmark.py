import json
import wave
from dataclasses import asdict

import pytest

from sokhan.tts_benchmark import benchmark_speech


class FakeSynthesizer:
    model = "fixture-model"

    def synthesize(self, text, output_path):
        with wave.open(str(output_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(8_000)
            output.writeframes(b"\x00\\x00" * 4_000)
        return output_path


def test_benchmark_reports_audio_runtime_metrics_without_source_text():
    report = benchmark_speech(["private sample one", "private sample two"], FakeSynthesizer())

    assert report.sample_count == 2
    assert report.total_audio_duration_ms == 1_000
    assert report.sample_rate_hz == 8_000
    assert report.channels == 1
    assert report.output_bytes > 0
    assert report.median_latency_ms >= 0
    assert report.p95_latency_ms >= report.median_latency_ms
    assert report.real_time_factor >= 0
    serialized = json.dumps(asdict(report))
    assert "private sample" not in serialized


def test_benchmark_rejects_empty_or_blank_sample_sets():
    with pytest.raises(ValueError, match="at least one"):
        benchmark_speech([], FakeSynthesizer())
    with pytest.raises(ValueError, match="must not be empty"):
        benchmark_speech(["  "], FakeSynthesizer())


def test_benchmark_rejects_non_pcm16_wav():
    class InvalidSynthesizer:
        def synthesize(self, text, output_path):
            with wave.open(str(output_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(1)
                output.setframerate(8_000)
                output.writeframes(b"\x00" * 100)

    with pytest.raises(ValueError, match="16-bit PCM"):
        benchmark_speech(["hello"], InvalidSynthesizer())


def test_benchmark_rejects_mixed_sample_rates():
    class MixedRateSynthesizer:
        def __init__(self):
            self.count = 0

        def synthesize(self, text, output_path):
            self.count += 1
            with wave.open(str(output_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(8_000 if self.count == 1 else 16_000)
                output.writeframes(b"\x00\\x00" * 100)

    with pytest.raises(ValueError, match="same sample rate"):
        benchmark_speech(["one", "two"], MixedRateSynthesizer())
