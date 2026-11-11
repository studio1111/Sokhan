import pytest

from sokhan.translation import LocalChatTranslator


def test_external_endpoint_is_opt_in():
    with pytest.raises(ValueError, match="external endpoints are disabled"):
        LocalChatTranslator("http://example.com")


def test_rejects_credentials_in_endpoint():
    with pytest.raises(ValueError):
        LocalChatTranslator("http://user:secret@127.0.0.1")
