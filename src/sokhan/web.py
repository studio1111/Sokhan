"""Secure loopback-only browser interface for Sokhan's local workflows."""
from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from .contracts import Translator
from .pdf import extract_pdf_text, translate_pdf
from .subtitles import dump_srt, parse_srt
from .vtt import dump_vtt, parse_vtt
from .workflows import audio_to_srt, translate_srt, translate_text

_ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}
_MAX_REQUEST_BYTES = 100 * 1024 * 1024
_MAX_SUBTITLE_BYTES = 5 * 1024 * 1024
_MAX_PDF_BYTES = 20 * 1024 * 1024
_MAX_AUDIO_BYTES = 100 * 1024 * 1024
_MAX_TTS_BYTES = 50 * 1024 * 1024
_MAX_PDF_OUTPUT_BYTES = 50 * 1024 * 1024
_ALLOWED_ASR_MODELS = {"tiny.en", "base.en", "small.en", "medium.en", "large-v3"}
_ALLOWED_REGISTERS = {"conversational", "formal", "neutral"}
_UPLOAD_REQUIRED = File(...)
_FONT_UPLOAD_REQUIRED = File(...)


class _RequestTooLarge(Exception):
    pass


class RequestLimitMiddleware:
    """Enforce a hard ASGI request-body ceiling, including chunked requests."""

    def __init__(self, app, max_bytes: int = _MAX_REQUEST_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        content_lengths = [
            value for key, value in scope.get("headers", []) if key.lower() == b"content-length"
        ]
        if len(content_lengths) > 1:
            await self._reject(send)
            return
        if content_lengths:
            try:
                declared_text = content_lengths[0].decode("ascii")
                if not declared_text.isdecimal() or int(declared_text) > self.max_bytes:
                    await self._reject(send)
                    return
            except (UnicodeDecodeError, ValueError):
                await self._reject(send)
                return

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _RequestTooLarge
            return message

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestTooLarge:
            if not response_started:
                await self._reject(send)

    @staticmethod
    async def _reject(send):
        body = b'{"detail":"request body exceeds the configured server limit"}'
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        })
        await send({"type": "http.response.body", "body": body})


class TextPayload(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    translation_register: Literal["conversational", "formal", "neutral"] = Field(
        default="conversational", alias="register"
    )


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


UI_HTML = r"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>سخن | ابزار ترجمه محلی</title>
<style>
:root{color-scheme:dark;font-family:Tahoma,Arial,sans-serif;background:#111827;color:#e5e7eb}
*{box-sizing:border-box}body{margin:0}header{padding:26px max(20px,calc((100vw - 1040px)/2));background:#172033;border-bottom:1px solid #334155}
h1{margin:0 0 8px;font-size:28px}header p{margin:0;color:#aab8cb}
main{max-width:1040px;margin:24px auto;padding:0 16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
section{background:#1f2937;border:1px solid #374151;border-radius:14px;padding:18px;min-width:0}
h2{font-size:18px;margin:0 0 14px}label{display:block;font-size:13px;color:#cbd5e1;margin:10px 0 6px}
textarea,input,select{width:100%;border:1px solid #475569;border-radius:8px;padding:10px;background:#0f172a;color:#f8fafc;font:inherit}
textarea{min-height:110px;resize:vertical}button{border:0;border-radius:8px;padding:10px 15px;background:#2563eb;color:white;font:inherit;cursor:pointer;margin-top:12px}
button:disabled{opacity:.55;cursor:wait}.output{white-space:pre-wrap;overflow-wrap:anywhere;background:#0b1220;border-radius:8px;padding:12px;margin-top:12px;min-height:36px;max-height:280px;overflow:auto}
.status{font-size:12px;color:#93c5fd;min-height:18px;margin-top:8px}.muted{color:#9ca3af;font-size:12px;line-height:1.7}
</style>
</head>
<body>
<header><h1>سُخَن | Sokhan</h1><p>ترجمه و پردازش فارسی با اجرای محلی؛ فایل‌ها پس از پایان درخواست از فضای موقت پاک می‌شوند.</p></header>
<main>
<section><h2>ترجمه متن</h2><label for="sourceText">متن انگلیسی</label><textarea id="sourceText" maxlength="100000"></textarea>
<label for="register">سبک ترجمه</label><select id="register"><option value="conversational">محاوره‌ای</option><option value="formal">رسمی</option><option value="neutral">خنثی</option></select>
<button id="translateText">ترجمه</button><div class="status" id="textStatus" aria-live="polite"></div><pre class="output" id="textOutput"></pre></section>
<section><h2>ترجمه زیرنویس</h2><label for="subtitleFile">فایل SRT یا WebVTT</label><input id="subtitleFile" type="file" accept=".srt,.vtt,text/plain,text/vtt">
<button id="translateSubtitle">ترجمه زیرنویس</button><div class="status" id="subtitleStatus" aria-live="polite"></div><pre class="output" id="subtitleOutput"></pre>
<button id="downloadSubtitle" disabled>دریافت فایل ترجمه‌شده</button></section>
<section><h2>استخراج PDF</h2><label for="pdfFile">فایل PDF متنی</label><input id="pdfFile" type="file" accept=".pdf,application/pdf">
<button id="extractPdf">استخراج متن</button><div class="status" id="pdfStatus" aria-live="polite"></div><pre class="output" id="pdfOutput"></pre>
<label for="fontFile">فایل فونت TTF فارسی</label><input id="fontFile" type="file" accept=".ttf,font/ttf">
<button id="translatePdf">ترجمه PDF به فارسی</button></section>
<section><h2>تبدیل صوت به زیرنویس</h2><label for="audioFile">فایل صوتی یا ویدئو</label><input id="audioFile" type="file" accept="audio/*,video/*">
<label for="asrModel">مدل تشخیص گفتار انگلیسی</label><select id="asrModel"><option>tiny.en</option><option>base.en</option><option selected>small.en</option><option>medium.en</option><option>large-v3</option></select>
<button id="audioToSrt">تبدیل به زیرنویس فارسی</button><div class="status" id="audioStatus" aria-live="polite"></div><pre class="output" id="audioOutput"></pre></section>
<section><h2>تولید گفتار فارسی</h2><label for="ttsText">متن فارسی</label><textarea id="ttsText" maxlength="20000"></textarea>
<button id="makeTts">تولید WAV</button><div class="status" id="ttsStatus" aria-live="polite"></div><audio id="ttsPlayer" controls></audio></section>
</main>
<script>
const $=id=>document.getElementById(id);
const show=(id,value)=>{$(id).textContent=value};
async function request(url,options){const response=await fetch(url,options);if(!response.ok){let message='درخواست ناموفق بود';try{const data=await response.json();message=data.detail||message}catch{}throw new Error(message)}return response}
function download(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
let subtitleBlob=null;
$('translateText').onclick=async()=>{show('textStatus','در حال ترجمه…');try{const r=await request('/api/translate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('sourceText').value,register:$('register').value})});show('textOutput',(await r.json()).translation);show('textStatus','تمام شد')}catch(e){show('textStatus',e.message)}};
$('translateSubtitle').onclick=async()=>{const file=$('subtitleFile').files[0];if(!file){show('subtitleStatus','ابتدا فایل زیرنویس را انتخاب کنید');return}show('subtitleStatus','در حال پردازش…');try{const ext=file.name.toLowerCase().split('.').pop();const form=new FormData();form.append('file',file);form.append('register',$('register').value);const r=await request(ext==='vtt'?'/api/vtt/translate':'/api/srt/translate',{method:'POST',body:form});const text=await r.text();subtitleBlob=new Blob([text],{type:'text/plain;charset=utf-8'});show('subtitleOutput',text);$('downloadSubtitle').disabled=false;show('subtitleStatus','تمام شد')}catch(e){show('subtitleStatus',e.message)}};
$('downloadSubtitle').onclick=()=>{if(subtitleBlob)download(subtitleBlob,$('subtitleFile').files[0].name.replace(/\.(srt|vtt)$/i,'.fa.$1'))};
$('extractPdf').onclick=async()=>{const file=$('pdfFile').files[0];if(!file){show('pdfStatus','ابتدا PDF را انتخاب کنید');return}show('pdfStatus','در حال استخراج…');try{const form=new FormData();form.append('file',file);const r=await request('/api/pdf/extract',{method:'POST',body:form});show('pdfOutput',(await r.json()).text);show('pdfStatus','تمام شد')}catch(e){show('pdfStatus',e.message)}};
$('translatePdf').onclick=async()=>{const file=$('pdfFile').files[0];const font=$('fontFile').files[0];if(!file||!font){show('pdfStatus','PDF و فایل فونت TTF لازم است');return}show('pdfStatus','در حال ترجمه و ساخت PDF…');try{const form=new FormData();form.append('file',file);form.append('font_file',font);form.append('register',$('register').value);const r=await request('/api/pdf/translate',{method:'POST',body:form});download(await r.blob(),'sokhan-fa.pdf');show('pdfStatus','PDF آماده شد')}catch(e){show('pdfStatus',e.message)}};
$('audioToSrt').onclick=async()=>{const file=$('audioFile').files[0];if(!file){show('audioStatus','ابتدا فایل صوتی را انتخاب کنید');return}show('audioStatus','مدل ASR در حال اجراست؛ اولین اجرا ممکن است زمان‌بر باشد…');try{const form=new FormData();form.append('file',file);form.append('asr_model',$('asrModel').value);form.append('device','cpu');form.append('register',$('register').value);const r=await request('/api/audio/srt',{method:'POST',body:form});const text=await r.text();show('audioOutput',text);download(new Blob([text],{type:'text/plain;charset=utf-8'}),'captions.fa.srt');show('audioStatus','تمام شد')}catch(e){show('audioStatus',e.message)}};
$('makeTts').onclick=async()=>{show('ttsStatus','در حال تولید صدا…');try{const r=await request('/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:$('ttsText').value})});const url=URL.createObjectURL(await r.blob());$('ttsPlayer').src=url;show('ttsStatus','فایل صوتی آماده است')}catch(e){show('ttsStatus',e.message)}};
</script>
</body></html>"""


def _read_upload(upload: UploadFile, limit: int) -> bytes:
    payload = upload.file.read(limit + 1)
    if len(payload) > limit:
        raise HTTPException(status_code=413, detail="uploaded file exceeds the endpoint size limit")
    return payload


def _decode_text(payload: bytes) -> str:
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=415, detail="text files must use UTF-8 encoding") from exc


def _check_register(register: str) -> None:
    if register not in _ALLOWED_REGISTERS:
        raise HTTPException(status_code=422, detail="unsupported translation register")


def create_app(
    *,
    translator_factory: Callable[[], Translator] | None = None,
    synthesizer_factory: Callable[[], object] | None = None,
    asr_factory: Callable[[str, str], object] | None = None,
) -> FastAPI:
    """Create the local web application; factories are injectable for isolated tests."""
    from .asr import FasterWhisperASR
    from .speech import synthesizer_from_env
    from .translation import translator_from_env

    translator_provider = translator_factory or translator_from_env
    synthesizer_provider = synthesizer_factory or synthesizer_from_env
    asr_provider = asr_factory or (
        lambda model, device: FasterWhisperASR(model_name=model, device=device)
    )

    app = FastAPI(title="Sokhan Local UI", docs_url=None, redoc_url=None)
    app.add_middleware(RequestLimitMiddleware)

    @app.middleware("http")
    async def local_only(request, call_next):
        if request.url.hostname not in _ALLOWED_HOSTS:
            return JSONResponse({"detail": "Sokhan web UI only accepts loopback hosts"}, status_code=421)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin:
                parsed = urlsplit(origin)
                if (
                    parsed.scheme != "http"
                    or parsed.hostname not in _ALLOWED_HOSTS
                    or parsed.port != request.url.port
                    or parsed.path not in {"", "/"}
                    or parsed.query
                    or parsed.fragment
                ):
                    return JSONResponse({"detail": "cross-origin requests are not allowed"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "connect-src 'self'; media-src 'self' blob:; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'"
        )
        return response

    @app.get("/", response_class=HTMLResponse)
    def home():
        return HTMLResponse(UI_HTML)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "local_only": True}

    @app.post("/api/translate")
    def api_translate(payload: TextPayload):
        try:
            result = translate_text(
                payload.text, translator_provider(), register=payload.translation_register
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"translation": result}

    @app.post("/api/srt/translate")
    def srt_translate(
        file: UploadFile = _UPLOAD_REQUIRED,
        translation_register: str = Form("conversational", alias="register"),
    ):
        _check_register(translation_register)
        content = _decode_text(_read_upload(file, _MAX_SUBTITLE_BYTES))
        try:
            cues = parse_srt(content)
            translated = translate_srt(cues, translator_provider(), register=translation_register)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return Response(
            dump_srt(translated), media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="captions.fa.srt"'},
        )

    @app.post("/api/vtt/translate")
    def vtt_translate(
        file: UploadFile = _UPLOAD_REQUIRED,
        translation_register: str = Form("conversational", alias="register"),
    ):
        _check_register(translation_register)

        content = _decode_text(_read_upload(file, _MAX_SUBTITLE_BYTES))
        try:
            cues = parse_vtt(content)
            translated = translate_srt(cues, translator_provider(), register=translation_register)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return Response(
            dump_vtt(translated), media_type="text/vtt; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="captions.fa.vtt"'},
        )

    @app.post("/api/pdf/extract")
    def pdf_extract(file: UploadFile = _UPLOAD_REQUIRED):
        payload = _read_upload(file, _MAX_PDF_BYTES)
        if b"%PDF-" not in payload[:1_024]:
            raise HTTPException(status_code=415, detail="uploaded file is not a PDF")
        with tempfile.TemporaryDirectory(prefix="sokhan-web-pdf-") as temporary:
            source = Path(temporary) / "source.pdf"
            source.write_bytes(payload)
            try:
                text = extract_pdf_text(str(source))
            except (ValueError, RuntimeError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {"text": text}

    @app.post("/api/pdf/translate")
    def pdf_translate(
        file: UploadFile = _UPLOAD_REQUIRED,
        font_file: UploadFile = _FONT_UPLOAD_REQUIRED,
        translation_register: str = Form("conversational", alias="register"),
    ):
        _check_register(translation_register)
        payload = _read_upload(file, _MAX_PDF_BYTES)
        if b"%PDF-" not in payload[:1_024]:
            raise HTTPException(status_code=415, detail="uploaded file is not a PDF")
        font_name = font_file.filename or ""
        if not font_name.lower().endswith(".ttf"):
            raise HTTPException(status_code=415, detail="font upload must be a TrueType .ttf file")
        font_payload = _read_upload(font_file, 20 * 1024 * 1024)
        if (
            len(font_payload) < 12
            or font_payload[:4] not in {b"\x00\x01\x00\x00", b"true", b"typ1"}
        ):
            raise HTTPException(status_code=415, detail="uploaded font has an invalid TrueType signature")
        with tempfile.TemporaryDirectory(prefix="sokhan-web-pdf-") as temporary:
            source = Path(temporary) / "source.pdf"
            font = Path(temporary) / "font.ttf"
            destination = Path(temporary) / "translated.fa.pdf"
            source.write_bytes(payload)
            font.write_bytes(font_payload)
            try:
                translate_pdf(source, destination, translator_provider(), font_path=font, register=translation_register)
            except (ValueError, RuntimeError, OSError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            if destination.stat().st_size > _MAX_PDF_OUTPUT_BYTES:
                raise HTTPException(status_code=413, detail="translated PDF exceeds the 50 MiB output limit")
            output = destination.read_bytes()
        return Response(
            output, media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="sokhan.fa.pdf"'},
        )

    @app.post("/api/audio/srt")
    def audio_srt(
        file: UploadFile = _UPLOAD_REQUIRED,
        asr_model: str = Form("small.en"),
        device: str = Form("cpu"),
        translation_register: str = Form("conversational", alias="register"),
    ):
        _check_register(translation_register)
        if asr_model not in _ALLOWED_ASR_MODELS or device not in {"cpu", "cuda"}:
            raise HTTPException(status_code=422, detail="unsupported ASR model or device")
        payload = _read_upload(file, _MAX_AUDIO_BYTES)
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".wav", ".mp3", ".m4a", ".mp4", ".mkv", ".webm", ".ogg", ".flac"}:
            suffix = ".media"
        with tempfile.TemporaryDirectory(prefix="sokhan-web-audio-") as temporary:
            source = Path(temporary) / f"source{suffix}"
            source.write_bytes(payload)
            try:
                cues = audio_to_srt(
                    source, asr_provider(asr_model, device), translator_provider(), register=translation_register
                )
            except (ValueError, RuntimeError, OSError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        return Response(
            dump_srt(cues), media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="captions.fa.srt"'},
        )

    @app.post("/api/tts")
    def api_tts(payload: TTSRequest):
        with tempfile.TemporaryDirectory(prefix="sokhan-web-tts-") as temporary:
            destination = Path(temporary) / "speech.wav"
            try:
                synthesizer_provider().synthesize(payload.text, destination)
            except (ValueError, RuntimeError, OSError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            if not destination.is_file():
                raise HTTPException(status_code=502, detail="TTS engine did not create a WAV file")
            if destination.stat().st_size > _MAX_TTS_BYTES:
                raise HTTPException(status_code=413, detail="TTS output exceeds the 50 MiB limit")
            output = destination.read_bytes()
        if not output.startswith(b"RIFF") or b"WAVE" not in output[:16]:
            raise HTTPException(status_code=502, detail="TTS engine returned an invalid WAV file")
        return Response(output, media_type="audio/wav", headers={
            "Content-Disposition": 'attachment; filename="sokhan-speech.wav"',
        })

    return app


def serve_local_web(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the optional browser UI on a loopback interface only."""
    if host not in _ALLOWED_HOSTS:
        raise ValueError("Sokhan web UI must bind to 127.0.0.1, localhost, or ::1")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65_535:
        raise ValueError("port must be between 1 and 65535")
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("install the web extra: pip install 'sokhan[web]'") from exc
    uvicorn.run(
        create_app(), host=host, port=port, access_log=False, server_header=False,
    )
