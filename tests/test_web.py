import struct
import wave

from fastapi.testclient import TestClient

from sokhan.contracts import SpeechSegment, TranslationResult
from sokhan.web import create_app


class FakeTranslator:
    def translate(self, request):
        return TranslationResult(text="سلام ؟", model="test")


class FakeASR:
    def transcribe(self, _path):
        return [SpeechSegment(0, 1_000, "Hello")]


class FakeSynthesizer:
    def synthesize(self, _text, output_path):
        with wave.open(str(output_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(8_000)
            output.writeframes(struct.pack("<h", 1000) * 800)


def make_client():
    app = create_app(
        translator_factory=FakeTranslator,
        synthesizer_factory=FakeSynthesizer,
        asr_factory=lambda _model, _device: FakeASR(),
    )
    return TestClient(app)


LOCAL_HEADERS = {"host": "127.0.0.1", "origin": "http://127.0.0.1"}


def test_web_home_and_health_are_available_only_on_local_host():
    client = make_client()
    assert client.get("/", headers={"host": "127.0.0.1"}).status_code == 200
    assert client.get("/api/health", headers={"host": "localhost"}).json() == {
        "status": "ok", "local_only": True,
    }
    assert client.get("/", headers={"host": "attacker.example"}).status_code == 421


def test_web_rejects_cross_origin_mutations():
    client = make_client()
    response = client.post(
        "/api/translate",
        json={"text": "Hello"},
        headers={"host": "127.0.0.1", "origin": "https://attacker.example"},
    )
    assert response.status_code == 403


def test_web_text_translation_uses_injected_local_adapter():
    client = make_client()
    response = client.post(
        "/api/translate", json={"text": "Hello", "register": "formal"},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["translation"] == "سلام؟"


def test_web_rejects_oversized_text():
    client = make_client()
    response = client.post(
        "/api/translate", json={"text": "x" * 100_001}, headers=LOCAL_HEADERS,
    )
    assert response.status_code == 422


def test_web_translates_srt_without_changing_timestamps():
    client = make_client()
    source = b"1\n00:00:00,000 --> 00:00:01,000\nHello\n"
    response = client.post(
        "/api/srt/translate", files={"file": ("captions.srt", source, "text/plain")},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200
    assert "00:00:00,000 --> 00:00:01,000" in response.text
    assert "سلام؟" in response.text
    assert "attachment;" in response.headers["content-disposition"]


def test_web_translates_vtt_and_preserves_header():
    client = make_client()
    source = b"WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n"
    response = client.post(
        "/api/vtt/translate", files={"file": ("captions.vtt", source, "text/vtt")},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200
    assert response.text.startswith("WEBVTT")
    assert "سلام؟" in response.text


def test_web_rejects_non_pdf_upload():
    client = make_client()
    response = client.post(
        "/api/pdf/extract", files={"file": ("notes.txt", b"not a PDF", "text/plain")},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 415


def test_web_audio_to_srt_uses_injected_asr():
    client = make_client()
    response = client.post(
        "/api/audio/srt",
        files={"file": ("speech.wav", b"fake audio", "audio/wav")},
        data={"asr_model": "small.en", "device": "cpu"},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200
    assert "سلام؟" in response.text
    assert "00:00:00,000 --> 00:00:01,000" in response.text


def test_web_tts_returns_wav_from_injected_local_adapter():
    client = make_client()
    response = client.post(
        "/api/tts", json={"text": "سلام"},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 200
    assert response.content.startswith(b"RIFF")
    assert response.headers["content-type"].startswith("audio/wav")


def test_web_rejects_oversized_subtitle_upload():
    client = make_client()
    response = client.post(
        "/api/srt/translate",
        files={"file": ("large.srt", b"x" * (5 * 1024 * 1024 + 1), "text/plain")},
        headers=LOCAL_HEADERS,
    )
    assert response.status_code == 413
