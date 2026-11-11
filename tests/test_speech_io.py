import json

from sokhan.contracts import SpeechSegment, WordTiming
from sokhan.speech_io import dump_speech_json


def test_speech_json_preserves_segment_word_and_speaker_metadata():
    segments = [
        SpeechSegment(
            125,
            1_750,
            "Hello world",
            speaker_id="speaker_1",
            emotion=None,
            confidence=0.87,
            words=(
                WordTiming(125, 700, "Hello", 0.98),
                WordTiming(750, 1_750, "world", 0.95),
            ),
        )
    ]

    payload = json.loads(dump_speech_json(segments))

    assert payload["schema_version"] == 1
    assert payload["language"] == "en"
    assert payload["segments"] == [
        {
            "start_ms": 125,
            "end_ms": 1750,
            "text": "Hello world",
            "speaker_id": "speaker_1",
            "emotion": None,
            "confidence": 0.87,
            "words": [
                {"start_ms": 125, "end_ms": 700, "text": "Hello", "probability": 0.98},
                {"start_ms": 750, "end_ms": 1750, "text": "world", "probability": 0.95},
            ],
        }
    ]


def test_speech_json_is_deterministic_and_unicode_friendly():
    segments = [SpeechSegment(0, 500, "سلام")]
    output = dump_speech_json(segments)

    assert "سلام" in output
    assert output.endswith("\n")
    assert output == dump_speech_json(segments)


def test_speech_json_supports_empty_transcript():
    payload = json.loads(dump_speech_json([]))
    assert payload["segments"] == []
