"""Composable workflows built on the public domain contracts."""

from __future__ import annotations

from .contracts import TranslationRequest, Translator
from .subtitles import Cue
from .text import normalize_persian


def translate_text(text: str, translator: Translator, *, register: str = "conversational") -> str:
    """Translate one English text block and normalize Persian output."""
    result = translator.translate(TranslationRequest(text=text, register=register))
    return normalize_persian(result.text)


def translate_srt(cues: list[Cue], translator: Translator, *,
                  register: str = "conversational") -> list[Cue]:
    """Translate cue text independently while preserving source timing and cue IDs."""
    translated: list[Cue] = []
    for cue in cues:
        result = translator.translate(TranslationRequest(text=cue.text, register=register))
        translated.append(Cue(cue.index, cue.start_ms, cue.end_ms, normalize_persian(result.text)))
    return translated
