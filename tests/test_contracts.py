import pytest

from sokhan.contracts import SpeechSegment, TranslationRequest


def test_translation_contract_is_english_to_persian_only():
    assert TranslationRequest("Hello").target_language == "fa"
    with pytest.raises(ValueError):
        TranslationRequest("Hello", source_language="de")


def test_speech_segment_validates_confidence():
    with pytest.raises(ValueError):
        SpeechSegment(0, 1000, "hello", confidence=1.1)
