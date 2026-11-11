from sokhan.contracts import TranslationResult
from sokhan.subtitles import Cue
from sokhan.workflows import translate_srt, translate_text


class FakeTranslator:
    def translate(self, request):
        return TranslationResult(text="  سلام ؟ ", model="test")


def test_translate_text_normalizes_persian():
    assert translate_text("Hello", FakeTranslator()) == "سلام؟"


def test_translate_srt_preserves_timing_and_indices():
    source = [Cue(7, 1000, 2500, "Hello")]
    result = translate_srt(source, FakeTranslator())
    assert result == [Cue(7, 1000, 2500, "سلام؟")]
