"""Typed boundaries for pluggable translation, ASR, and speech engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    text: str
    source_language: str = "en"
    target_language: str = "fa"
    register: str = "conversational"
    preserve_meaning: bool = True

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("translation text must not be empty")
        if self.source_language != "en" or self.target_language != "fa":
            raise ValueError("the initial release supports English-to-Persian only")
        if self.register not in {"conversational", "formal", "neutral"}:
            raise ValueError("register must be conversational, formal, or neutral")


@dataclass(frozen=True, slots=True)
class TranslationResult:
    text: str
    model: str
    source_language: str = "en"
    target_language: str = "fa"


class Translator(Protocol):
    def translate(self, request: TranslationRequest) -> TranslationResult: ...


@dataclass(frozen=True, slots=True)
class WordTiming:
    start_ms: int
    end_ms: int
    text: str
    probability: float | None = None

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("word timing must have a positive time range")
        if not self.text.strip():
            raise ValueError("word text must not be empty")
        if self.probability is not None and not 0 <= self.probability <= 1:
            raise ValueError("word probability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class SpeechSegment:
    start_ms: int
    end_ms: int
    text: str
    speaker_id: str | None = None
    emotion: str | None = None
    confidence: float | None = None
    words: tuple[WordTiming, ...] = ()

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("speech segment must have a positive time range")
        if not self.text.strip():
            raise ValueError("speech segment text must not be empty")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        previous_start = self.start_ms
        for word in self.words:
            if word.start_ms < self.start_ms or word.end_ms > self.end_ms:
                raise ValueError("word timing must stay within its speech segment")
            if word.start_ms < previous_start:
                raise ValueError("word timings must be ordered")
            previous_start = word.start_ms
