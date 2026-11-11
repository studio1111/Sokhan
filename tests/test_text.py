import pytest

from sokhan.text import normalize_persian, prepare_translation_text


def test_normalizes_arabic_characters_and_spacing():
    assert normalize_persian("  كِتاب  ي   خوب  است ؟ ") == "کتاب ی خوب است؟"


def test_preserves_paragraph_boundaries():
    assert prepare_translation_text(" First  line \n\n Second\tline ") == "First line\nSecond line"


def test_rejects_non_string():
    with pytest.raises(TypeError):
        normalize_persian(None)
