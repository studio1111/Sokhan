"""Deterministic, privacy-safe metrics for speech transcripts and ASR output.

These metrics measure transcription agreement and timing integrity. They do not
measure translation adequacy, speaker identity, emotion, or perceived naturalness.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from .contracts import SpeechSegment
from .text import normalize_persian


@dataclass(frozen=True, slots=True)
class SpeechQualitySummary:
    """Aggregate speech timing and word-confidence metrics; contains no transcript text."""

    segment_count: int
    speech_duration_ms: int
    coverage_ratio: float
    gap_count: int
    overlap_count: int
    segments_without_word_timestamps: int
    word_count: int
    mean_word_confidence: float | None
    low_confidence_word_count: int


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    """Compute Levenshtein distance with O(min(n, m)) memory."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for row, ref_item in enumerate(reference, start=1):
        current = [row]
        for column, hyp_item in enumerate(hypothesis, start=1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (ref_item != hyp_item),
            ))
        previous = current
    return previous[-1]


def _normalized_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("transcript text must be a string")
    return normalize_persian(value).casefold()


def _error_rate(reference: list[str], hypothesis: list[str], *, unit: str) -> float:
    if not reference:
        if not hypothesis:
            return 0.0
        raise ValueError(f"{unit} reference must not be empty when hypothesis is non-empty")
    return _edit_distance(reference, hypothesis) / len(reference)


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Return WER after Persian Unicode normalization and whitespace tokenization.

    WER is a reference-relative edit-rate metric; it is not a semantic translation score.
    """
    ref = _normalized_text(reference).split()
    hyp = _normalized_text(hypothesis).split()
    return _error_rate(ref, hyp, unit="word")


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Return code-point CER after Persian normalization and whitespace removal."""
    ref = list("".join(_normalized_text(reference).split()))
    hyp = list("".join(_normalized_text(hypothesis).split()))
    return _error_rate(ref, hyp, unit="character")


def summarize_speech(
    segments: list[SpeechSegment],
    *,
    media_duration_ms: int,
    low_confidence_threshold: float = 0.5,
) -> SpeechQualitySummary:
    """Summarize timeline coverage, gaps, overlaps, and available word confidence.

    Speech duration is the union of segment intervals, so overlapping segments
    never inflate coverage. Leading and trailing silence are not counted as gaps.
    """
    if not isinstance(media_duration_ms, int) or isinstance(media_duration_ms, bool) or media_duration_ms < 1:
        raise ValueError("media_duration_ms must be a positive integer")
    if (
        not math.isfinite(low_confidence_threshold)
        or not 0 <= low_confidence_threshold <= 1
    ):
        raise ValueError("low-confidence threshold must be between 0 and 1")

    ordered = sorted(segments, key=lambda item: (item.start_ms, item.end_ms))
    if any(segment.end_ms > media_duration_ms for segment in ordered):
        raise ValueError("speech segment exceeds media_duration_ms")

    intervals: list[tuple[int, int]] = []
    overlap_count = 0
    for segment in ordered:
        if intervals and segment.start_ms < intervals[-1][1]:
            overlap_count += 1
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], segment.end_ms))
        else:
            intervals.append((segment.start_ms, segment.end_ms))

    speech_duration = sum(end - start for start, end in intervals)
    gap_count = sum(
        1 for previous, current in zip(intervals, intervals[1:])
        if current[0] > previous[1]
    )
    words = [word for segment in ordered for word in segment.words]
    confidences = [
        word.probability for word in words if word.probability is not None
    ]

    return SpeechQualitySummary(
        segment_count=len(ordered),
        speech_duration_ms=speech_duration,
        coverage_ratio=speech_duration / media_duration_ms,
        gap_count=gap_count,
        overlap_count=overlap_count,
        segments_without_word_timestamps=sum(not segment.words for segment in ordered),
        word_count=len(words),
        mean_word_confidence=(
            sum(confidences) / len(confidences) if confidences else None
        ),
        low_confidence_word_count=sum(
            confidence < low_confidence_threshold for confidence in confidences
        ),
    )
