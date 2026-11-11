"""Versioned JSON serialization for ASR transcripts with word-level timing."""

from __future__ import annotations

import json
from collections.abc import Sequence

from .contracts import SpeechSegment


def dump_speech_json(segments: Sequence[SpeechSegment]) -> str:
    """Serialize speech segments without dropping word, speaker, or confidence fields."""
    if any(not isinstance(segment, SpeechSegment) for segment in segments):
        raise TypeError("segments must contain only SpeechSegment values")

    payload = {
        "schema_version": 1,
        "language": "en",
        "segments": [
            {
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "text": segment.text,
                "speaker_id": segment.speaker_id,
                "emotion": segment.emotion,
                "confidence": segment.confidence,
                "words": [
                    {
                        "start_ms": word.start_ms,
                        "end_ms": word.end_ms,
                        "text": word.text,
                        "probability": word.probability,
                    }
                    for word in segment.words
                ],
            }
            for segment in segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
