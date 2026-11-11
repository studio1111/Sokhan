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


def test_vtt_readability_fit_extends_cue_without_overlapping_next():
    from sokhan.vtt import retime_vtt_for_readability

    cues = parse_vtt(
        "WEBVTT\n\n00:00:00.000 --> 00:00:00.400\nA short Persian translation\n\n"
        "00:00:03.000 --> 00:00:03.500\nNext"
    )
    fitted = retime_vtt_for_readability(
        cues, media_end_ms=5_000, max_chars_per_second=100, min_duration_ms=1_200
    )
    assert fitted[0].end_ms == 1_200
    assert fitted[1].start_ms == 3_000
    assert parse_vtt(dump_vtt(fitted)) == fitted


def test_vtt_readability_fit_rejects_impossible_timeline():
    from sokhan.vtt import retime_vtt_for_readability

    cues = parse_vtt("WEBVTT\n\n00:00:00.000 --> 00:00:00.300\nA very long subtitle line")
    with pytest.raises(ValueError, match="only"):
        retime_vtt_for_readability(
            cues, media_end_ms=500, max_chars_per_second=5
        )
