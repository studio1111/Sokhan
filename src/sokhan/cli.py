"""Command-line interface for text, subtitles, PDF, and audio workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .asr import FasterWhisperASR
from .media import extract_audio
from .pdf import extract_pdf_text, translate_pdf
from .speech import synthesizer_from_env
from .subtitles import dump_srt, parse_srt, retime_cues, retime_cues_for_readability
from .text import normalize_persian
from .translation import translator_from_env
from .vtt import dump_vtt, parse_vtt
from .workflows import audio_to_srt, translate_srt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sokhan", description="English-to-Persian language toolkit")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="start the secure local browser interface")
    serve.add_argument("--host", choices=("127.0.0.1", "localhost", "::1"), default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    normalize = commands.add_parser("normalize-fa", help="normalize Persian typography")
    normalize.add_argument("input", nargs="?", help="text file; stdin if omitted")
    translate = commands.add_parser("translate", help="translate using a local model endpoint")
    translate.add_argument("input", nargs="?", help="text file; stdin if omitted")
    translate.add_argument("--register", choices=("conversational", "formal", "neutral"),
                           default="conversational")
    pdf = commands.add_parser("extract-pdf", help="extract text from a PDF")
    pdf.add_argument("input")
    pdf_translate = commands.add_parser("pdf-to-fa", help="translate a text PDF into Persian RTL PDF")
    pdf_translate.add_argument("input")
    pdf_translate.add_argument("output")
    pdf_translate.add_argument("--font", required=True, help="path to a Persian-capable TrueType font")
    pdf_translate.add_argument("--register", choices=("conversational", "formal", "neutral"),
                               default="conversational")
    srt = commands.add_parser("srt-check", help="validate and optionally clamp SRT timings")
    srt.add_argument("input")
    srt.add_argument("--max-duration-ms", type=int)
    fit = commands.add_parser("srt-fit", help="extend subtitle display time to a readable rate")
    fit.add_argument("input")
    fit.add_argument("output")
    fit.add_argument("--media-duration-ms", type=int, required=True)
    fit.add_argument("--max-cps", type=float, default=17.0)
    fit.add_argument("--min-duration-ms", type=int, default=1_000)
    vtt = commands.add_parser("vtt-check", help="validate and normalize WebVTT timings")
    vtt.add_argument("input")
    audio = commands.add_parser("extract-audio", help="extract mono WAV audio from a media file")
    audio.add_argument("input")
    audio.add_argument("output")
    tts = commands.add_parser("text-to-speech", help="synthesize WAV through a local TTS endpoint")
    tts.add_argument("input", nargs="?", help="text file; stdin if omitted")
    tts.add_argument("output")
    dubbing = commands.add_parser("audio-to-srt", help="transcribe English audio and translate to Persian SRT")
    dubbing.add_argument("input")
    dubbing.add_argument("output")
    dubbing.add_argument("--asr-model", default="small.en")
    dubbing.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    dubbing.add_argument("--register", choices=("conversational", "formal", "neutral"),
                         default="conversational")
    for name, help_text in (
        ("translate-srt", "translate SRT cue text to Persian"),
        ("translate-vtt", "translate WebVTT cue text to Persian"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("input")
        command.add_argument("output")
        command.add_argument("--register", choices=("conversational", "formal", "neutral"),
                             default="conversational")
    return parser


def _read_input(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()


def _write_new_file(path: str, content: str) -> None:
    """Write a new output without silently overwriting user data."""
    with Path(path).open("x", encoding="utf-8", newline="") as output:
        output.write(content)


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "serve":
            try:
                from .web import serve_local_web
            except ImportError as exc:
                raise RuntimeError("install the web extra: pip install 'sokhan[web]'") from exc
            serve_local_web(host=args.host, port=args.port)
        elif args.command == "normalize-fa":
            print(normalize_persian(_read_input(args.input)))
        elif args.command == "translate":
            from .contracts import TranslationRequest
            result = translator_from_env().translate(
                TranslationRequest(_read_input(args.input), register=args.register))
            print(result.text)
        elif args.command == "extract-pdf":
            print(extract_pdf_text(args.input))
        elif args.command == "pdf-to-fa":
            translate_pdf(args.input, args.output, translator_from_env(),
                          font_path=args.font, register=args.register)
        elif args.command == "srt-check":
            cues = parse_srt(Path(args.input).read_text(encoding="utf-8"))
            print(dump_srt(retime_cues(cues, max_end_ms=args.max_duration_ms)), end="")
        elif args.command == "srt-fit":
            cues = retime_cues_for_readability(
                parse_srt(Path(args.input).read_text(encoding="utf-8")),
                media_end_ms=args.media_duration_ms,
                max_chars_per_second=args.max_cps,
                min_duration_ms=args.min_duration_ms,
            )
            _write_new_file(args.output, dump_srt(cues))
        elif args.command == "vtt-check":
            print(dump_vtt(parse_vtt(Path(args.input).read_text(encoding="utf-8"))), end="")
        elif args.command == "extract-audio":
            extract_audio(args.input, args.output)
        elif args.command == "text-to-speech":
            synthesizer_from_env().synthesize(_read_input(args.input), args.output)
        elif args.command == "audio-to-srt":
            asr = FasterWhisperASR(model_name=args.asr_model, device=args.device)
            cues = audio_to_srt(args.input, asr, translator_from_env(), register=args.register)
            _write_new_file(args.output, dump_srt(cues))
        elif args.command == "translate-srt":
            cues = translate_srt(
                parse_srt(Path(args.input).read_text(encoding="utf-8")),
                translator_from_env(), register=args.register)
            _write_new_file(args.output, dump_srt(cues))
        elif args.command == "translate-vtt":
            cues = translate_srt(
                parse_vtt(Path(args.input).read_text(encoding="utf-8")),
                translator_from_env(), register=args.register)
            _write_new_file(args.output, dump_vtt(cues))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"sokhan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
