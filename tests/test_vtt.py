import pytest

from sokhan.vtt import dump_vtt, parse_vtt


SAMPLE = """WEBVTT

intro
00:00:01.000 --> 00:00:02.500 align:start
Hello world.

00:02.500 --> 00:03.000
Goodbye.
"""


def test_vtt_round_trip():
    cues = parse_vtt(SAMPLE)
    assert len(cues) == 2
    assert cues[0].start_ms == 1000
    assert cues[1].start_ms == 2500
    result = parse_vtt(dump_vtt(cues))
    assert result == cues


def test_vtt_ignores_note_blocks():
    cues = parse_vtt("WEBVTT\n\nNOTE metadata\nignored\n\n00:01.000 --> 00:02.000\nHi")
    assert len(cues) == 1
    assert cues[0].text == "Hi"


def test_vtt_rejects_invalid_timestamp():
    with pytest.raises(ValueError):
        parse_vtt("WEBVTT\n\n00:99.000 --> 00:02.000\nHi")
