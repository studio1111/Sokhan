"""Strict SRT parsing and serialization with safe timestamp handling."""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass

_TIMESTAMP = re.compile(r"^(?P<h>\d{2,}):(?P<m>[0-5]\d):(?P<s>[0-5]\d),(?P<ms>\d{3})$")


@dataclass(frozen=True, slots=True)
class Cue:
    index: int
    start_ms: int
    end_ms: int
    text: str

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("cue index must be >= 1")
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("cue timestamps must satisfy 0 <= start < end")
        if not self.text.strip():
            raise ValueError("cue text must not be empty")


def _parse_timestamp(value: str) -> int:
    match = _TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    p = {key: int(val) for key, val in match.groupdict().items()}
    return ((p["h"] * 60 + p["m"]) * 60 + p["s"]) * 1000 + p["ms"]


def _format_timestamp(value: int) -> str:
    if value < 0:
        raise ValueError("timestamp cannot be negative")
    hours, rem = divmod(value, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, milliseconds = divmod(rem, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def parse_srt(content: str) -> list[Cue]:
    if not isinstance(content, str):
        raise TypeError("SRT content must be a string")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    blocks = re.split(r"\n\s*\n", normalized)
    cues: list[Cue] = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError("malformed SRT cue block")
        timing = lines[1].split("-->")
        if len(timing) != 2:
            raise ValueError("malformed SRT timing line")
        cues.append(Cue(int(lines[0].strip()), _parse_timestamp(timing[0]),
                        _parse_timestamp(timing[1]), "\n".join(lines[2:]).strip()))
    for previous, current in itertools.pairwise(cues):
        if current.index <= previous.index:
            raise ValueError("cue indices must be strictly increasing")
        if current.start_ms < previous.start_ms:
            raise ValueError("cue start times must be non-decreasing")
    return cues


def dump_srt(cues: list[Cue]) -> str:
    blocks = [f"{c.index}\n{_format_timestamp(c.start_ms)} --> "
              f"{_format_timestamp(c.end_ms)}\n{c.text.strip()}" for c in cues]
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def retime_cues(cues: list[Cue], *, max_end_ms: int | None = None) -> list[Cue]:
    """Clamp cue ends to the next cue and media duration without invalidating cues."""
    if max_end_ms is not None and max_end_ms < 1:
        raise ValueError("max_end_ms must be positive")
    result = []
    for position, cue in enumerate(cues):
        next_start = cues[position + 1].start_ms if position + 1 < len(cues) else None
        end = min(cue.end_ms, next_start) if next_start is not None else cue.end_ms
        if max_end_ms is not None:
            end = min(end, max_end_ms)
        if end <= cue.start_ms:
            raise ValueError(f"cue {cue.index} has no duration after retiming")
        result.append(Cue(cue.index, cue.start_ms, end, cue.text))
    return result
