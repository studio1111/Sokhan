"""Composable workflows built on the public domain contracts."""

from __future__ import annotations

from pathlib import Path

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


def audio_to_srt(audio_path: str | Path, asr, translator: Translator, *,
                 register: str = "conversational") -> list[Cue]:
    """Transcribe English audio and translate segments while retaining timestamps."""
    segments = asr.transcribe(audio_path)
    cues = [
        Cue(index, segment.start_ms, segment.end_ms,
            translate_text(segment.text, translator, register=register))
        for index, segment in enumerate(segments, start=1)
    ]
    return cues


def audio_to_dub(
    audio_path: str | Path,
    asr,
    translator: Translator,
    synthesizer,
    output_path: str | Path,
    *,
    register: str = "conversational",
    media_duration_ms: int | None = None,
) -> Path:
    """Run local English ASR, Persian translation, cue synthesis, and WAV stitching."""
    from .dubbing import synthesize_srt

    cues = audio_to_srt(audio_path, asr, translator, register=register)
    return synthesize_srt(
        cues, synthesizer, output_path, media_duration_ms=media_duration_ms
    )
