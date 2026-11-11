"""Optional English ASR adapter using faster-whisper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import SpeechSegment, WordTiming


class ASRConfigurationError(RuntimeError):
    """Raised when the optional ASR runtime is unavailable or misconfigured."""


class FasterWhisperASR:
    """CPU-friendly English transcription adapter with segment timestamps."""

    def __init__(
        self,
        model_name: str = "small.en",
        device: str = "cpu",
        compute_type: str = "int8",
        *,
        model: Any | None = None,
        beam_size: int = 5,
    ) -> None:
        if beam_size < 1 or beam_size > 10:
            raise ValueError("beam_size must be between 1 and 10")
        self.beam_size = beam_size
        if model is not None:
            self._model = model
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASRConfigurationError(
                "install the optional audio extra: pip install 'sokhan[audio]'"
            ) from exc
        try:
            self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
        except Exception as exc:
            raise ASRConfigurationError("could not initialize the configured ASR model") from exc

    def transcribe(self, audio_path: str | Path) -> list[SpeechSegment]:
        path = Path(audio_path)
        if not path.is_file():
            raise FileNotFoundError(f"audio file does not exist: {path}")
        try:
            segments, _info = self._model.transcribe(
                str(path),
                language="en",
                task="transcribe",
                beam_size=self.beam_size,
                word_timestamps=True,
                vad_filter=True,
            )
            output = []
            for segment in segments:
                text = str(segment.text).strip()
                start_ms = max(0, round(float(segment.start) * 1000))
                end_ms = round(float(segment.end) * 1000)
                if text and end_ms > start_ms:
                    words = []
                    for word in getattr(segment, "words", None) or ():
                        try:
                            word_text = str(word.word).strip()
                            word_start = round(float(word.start) * 1000)
                            word_end = round(float(word.end) * 1000)
                            probability = getattr(word, "probability", None)
                            if (word_text and start_ms <= word_start < word_end <= end_ms):
                                words.append(WordTiming(
                                    word_start, word_end, word_text,
                                    float(probability) if probability is not None else None,
                                ))
                        except (AttributeError, TypeError, ValueError):
                            continue
                    output.append(SpeechSegment(
                        start_ms, end_ms, text, words=tuple(words)
                    ))
            return output
        except Exception as exc:
            raise ASRConfigurationError("English audio transcription failed") from exc
