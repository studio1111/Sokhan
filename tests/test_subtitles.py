import pytest

from sokhan.subtitles import Cue, dump_srt, parse_srt, retime_cues

SAMPLE = """1
00:00:01,000 --> 00:00:02,500
Hello world.

2
00:00:03,000 --> 00:00:04,000
Goodbye.
"""


def test_srt_round_trip():
    assert dump_srt(parse_srt(SAMPLE)) == SAMPLE


def test_retime_clamps_to_media_duration():
    cues = retime_cues(parse_srt(SAMPLE), max_end_ms=3500)
    assert cues[0].end_ms == 2500
    assert cues[1].end_ms == 3500


def test_rejects_invalid_ranges():
    with pytest.raises(ValueError):
        Cue(1, 2000, 1000, "invalid")


def test_rejects_malformed_srt():
    with pytest.raises(ValueError):
        parse_srt("not an srt")
