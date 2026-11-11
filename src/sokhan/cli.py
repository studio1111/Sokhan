"""Command-line interface for deterministic text and subtitle utilities."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .pdf import extract_pdf_text
from .subtitles import dump_srt, parse_srt, retime_cues
from .text import normalize_persian
from .translation import translator_from_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sokhan", description="English-to-Persian language toolkit")
    commands = parser.add_subparsers(dest="command", required=True)
    normalize = commands.add_parser("normalize-fa", help="normalize Persian typography")
    normalize.add_argument("input", nargs="?", help="text file; stdin if omitted")
    translate = commands.add_parser("translate", help="translate using a local model endpoint")
    translate.add_argument("input", nargs="?", help="text file; stdin if omitted")
    translate.add_argument("--register", choices=("conversational", "formal", "neutral"),
                           default="conversational")
    pdf = commands.add_parser("extract-pdf", help="extract text from a PDF")
    pdf.add_argument("input")
    srt = commands.add_parser("srt-check", help="validate and optionally clamp SRT timings")
    srt.add_argument("input")
    srt.add_argument("--max-duration-ms", type=int)
    return parser


def _read_input(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "normalize-fa":
            print(normalize_persian(_read_input(args.input)))
        elif args.command == "translate":
            from .contracts import TranslationRequest
            result = translator_from_env().translate(
                TranslationRequest(_read_input(args.input), register=args.register))
            print(result.text)
        elif args.command == "extract-pdf":
            print(extract_pdf_text(args.input))
        elif args.command == "srt-check":
            cues = parse_srt(Path(args.input).read_text(encoding="utf-8"))
            print(dump_srt(retime_cues(cues, max_end_ms=args.max_duration_ms)), end="")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"sokhan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
