import pytest

from sokhan.contracts import SpeechSegment, WordTiming
from sokhan.evaluation import (
    character_error_rate,
    summarize_speech,
    word_error_rate,
)


def test_word_error_rate_normalizes_persian_variants():
    assert word_error_rate("سلام عليکم", "سلام علیکم") == 0.0


def test_word_error_rate_counts_substitutions_insertions_and_deletions():
    assert word_error_rate("one two three", "one four three extra") == pytest.approx(2 / 3)


def test_character_error_rate_uses_normalized_unicode_characters():
    assert character_error_rate("كِتاب", "کتاب") == 0.0


def test_error_rates_handle_two_empty_strings_and_reject_empty_reference():
    assert word_error_rate("", "") == 0.0
    assert character_error_rate("", "") == 0.0
    with pytest.raises(ValueError, match="reference"):
        word_error_rate("", "hypothesis")
    with pytest.raises(ValueError, match="reference"):
        character_error_rate("", "hypothesis")


def test_speech_summary_reports_union_coverage_gaps_overlap_and_word_confidence():
    segments = [
        SpeechSegment(
            0, 1_000, "first",
            words=(WordTiming(100, 400, "first", 0.9),),
        ),
        SpeechSegment(
            800, 1_500, "second",
            words=(WordTiming(900, 1_200, "second", 0.3),),
        ),
        SpeechSegment(2_000, 2_500, "third"),
    ]

    summary = summarize_speech(segments, media_duration_ms=3_000)

    assert summary.segment_count == 3
    assert summary.speech_duration_ms == 2_000
    assert summary.coverage_ratio == pytest.approx(2 / 3)
    assert summary.gap_count == 1
    assert summary.overlap_count == 1
    assert summary.segments_without_word_timestamps == 1
    assert summary.word_count == 2
    assert summary.mean_word_confidence == pytest.approx(0.6)
    assert summary.low_confidence_word_count == 1


def test_speech_summary_validates_media_duration_and_confidence_threshold():
    with pytest.raises(ValueError, match="media_duration_ms"):
        summarize_speech([], media_duration_ms=0)
    with pytest.raises(ValueError, match="threshold"):
        summarize_speech([], media_duration_ms=1, low_confidence_threshold=1.5)


def test_speech_summary_empty_transcript_has_zero_coverage():
    summary = summarize_speech([], media_duration_ms=5_000)
    assert summary.segment_count == 0
    assert summary.speech_duration_ms == 0
    assert summary.coverage_ratio == 0.0
    assert summary.gap_count == 0
    assert summary.mean_word_confidence is None
