import pytest

from sokhan.translation import LocalChatTranslator


def test_remote_https_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="external endpoints are disabled"):
        LocalChatTranslator("https://example.org")


def test_remote_http_is_rejected_even_with_opt_in():
    with pytest.raises(ValueError, match="HTTPS"):
        LocalChatTranslator("http://example.org", allow_external=True)


def test_remote_https_is_allowed_only_after_opt_in():
    translator = LocalChatTranslator("https://example.org", allow_external=True)
    assert translator.endpoint == "https://example.org"

def test_translation_input_size_is_bounded():
    from sokhan.contracts import TranslationRequest

    translator = LocalChatTranslator(max_input_chars=32)
    with pytest.raises(ValueError, match="input exceeds"):
        translator.translate(TranslationRequest("x" * 33))


def test_translation_input_limit_must_be_positive():
    with pytest.raises(ValueError, match="max_input_chars"):
        LocalChatTranslator(max_input_chars=0)
