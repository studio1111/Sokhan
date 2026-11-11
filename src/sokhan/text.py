"""Persian text normalization utilities; deliberately model-independent."""

from __future__ import annotations

import re
import unicodedata

_ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
_SPACES = re.compile(r"[ \t\u00a0]+")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([،؛؟.!:])")
_REPEATED_PUNCTUATION = re.compile(r"([،؛؟.!])\1+")


def normalize_persian(text: str, *, remove_diacritics: bool = True) -> str:
    """Normalize common Arabic/Persian variants without rewriting meaning."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    value = unicodedata.normalize("NFC", text).translate(_ARABIC_TO_PERSIAN).replace("\u0640", "")
    if remove_diacritics:
        value = _DIACRITICS.sub("", value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in value.split("\n"):
        line = _SPACES.sub(" ", line).strip()
        line = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", line)
        line = _REPEATED_PUNCTUATION.sub(r"\1", line)
        lines.append(line)
    return "\n".join(lines).strip()


def prepare_translation_text(text: str) -> str:
    """Normalize source whitespace while preserving paragraph boundaries."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    paragraphs = [re.sub(r"\s+", " ", part).strip() for part in text.splitlines()]
    return "\n".join(part for part in paragraphs if part)
