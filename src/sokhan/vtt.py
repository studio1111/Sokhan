"""WebVTT parser and serializer using the shared timed-cue contract."""

from __future__ import annotations

import re

from .subtitles import Cue

_TIMESTAMP = re.compile(r"^(?:(?P<h>\d{2,}):)?(?P<m>[0-5]\d):(?P<s>[0-5]\d)\.(?P<ms>\d{3})$")


def _parse_timestamp(value: str) -> int:
    match = _TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid WebVTT timestamp: {value!r}")
    parts = match.groupdict()
    hours = int(parts["h"] or 0)
    minutes = int(parts["m"])
    seconds = int(parts["s"])
    milliseconds = int(parts["ms"])
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def _format_timestamp(value: int) -> str:
    if value < 0:
        raise ValueError("timestamp cannot be negative")
    hours, rem = divmod(value, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, milliseconds = divmod(rem, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def parse_vtt(content: str) -> list[Cue]:
    if not isinstance(content, str):
        raise TypeError("WebVTT content must be a string")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    if not normalized.startswith("WEBVTT"):
        raise ValueError("WebVTT header is missing")
    blocks = re.split(r"\n\s*\n", normalized)
    cues: list[Cue] = []
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines or lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        timing_index = 0 if "-->" in lines[0] else 1
        if len(lines) <= timing_index:
            raise ValueError("malformed WebVTT cue block")
        timing = lines[timing_index].split("-->")
        if len(timing) != 2:
            raise ValueError("malformed WebVTT timing line")
        start = _parse_timestamp(timing[0])
        end = _parse_timestamp(timing[1].strip().split()[0])
        text = "\n".join(lines[timing_index + 1:]).strip()
        cues.append(Cue(len(cues) + 1, start, end, text))
    return cues


def dump_vtt(cues: list[Cue]) -> str:
    blocks = [
        f"{cue.index}\n{_format_timestamp(cue.start_ms)} --> "
        f"{_format_timestamp(cue.end_ms)}\n{cue.text.strip()}"
        for cue in cues
    ]
    return "WEBVTT\n\n" + "\n\n".join(blocks) + ("\n" if blocks else "")
