"""Local OpenAI-compatible text-to-speech adapter.

This boundary intentionally supports speech synthesis only. It does not perform
speaker cloning, diarization, emotion inference, or cloud fallback.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .translation import _validate_endpoint


class SpeechSynthesisError(RuntimeError):
    """Raised when the configured local speech engine cannot synthesize audio."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalSpeechSynthesizer:
    """Call a local OpenAI-compatible /v1/audio/speech endpoint."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:1234",
        model: str = "local-tts",
        voice: str = "alloy",
        *,
        timeout_seconds: float = 120,
        max_text_chars: int = 20_000,
        max_audio_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        if timeout_seconds <= 0 or max_text_chars < 1 or max_audio_bytes < 1:
            raise ValueError("timeouts and size limits must be positive")
        self.endpoint = _validate_endpoint(endpoint, allow_external=False)
        self.model = model
        self.voice = voice
        self.timeout_seconds = timeout_seconds
        self.max_text_chars = max_text_chars
        self.max_audio_bytes = max_audio_bytes
        self._opener = build_opener(_NoRedirect())

    def synthesize(self, text: str, output_path: str | Path) -> Path:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("speech text must not be empty")
        if len(text) > self.max_text_chars:
            raise ValueError(f"text exceeds configured limit of {self.max_text_chars} characters")

        import json

        payload = json.dumps({
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
        }, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.endpoint}/v1/audio/speech",
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "audio/wav"},
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"audio/wav", "audio/x-wav", "application/octet-stream"}:
                    raise SpeechSynthesisError("speech engine returned a non-audio response")
                audio = response.read(self.max_audio_bytes + 1)
            if len(audio) > self.max_audio_bytes:
                raise SpeechSynthesisError("speech response exceeded configured size limit")
            if not audio.startswith(b"RIFF") or audio[8:12] != b"WAVE":
                raise SpeechSynthesisError("speech engine did not return a valid WAV stream")
            destination = Path(output_path)
            with destination.open("xb") as output:
                output.write(audio)
            return destination
        except SpeechSynthesisError:
            raise
        except FileExistsError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise SpeechSynthesisError(
                "local speech request failed; redirects and cloud fallback are disabled"
            ) from exc


def synthesizer_from_env() -> LocalSpeechSynthesizer:
    return LocalSpeechSynthesizer(
        endpoint=os.getenv("SOKHAN_TTS_BASE_URL", "http://127.0.0.1:1234"),
        model=os.getenv("SOKHAN_TTS_MODEL", "local-tts"),
        voice=os.getenv("SOKHAN_TTS_VOICE", "alloy"),
    )
