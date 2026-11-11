import pytest

from sokhan.subtitles import (\n    Cue, dump_srt, parse_srt, retime_cues, retime_cues_for_readability,\n)

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



def test_readability_retiming_extends_cue_without_overlapping_next():
    from sokhan.subtitles import retime_cues_for_readability

    cues = [Cue(1, 0, 500, "A short translated line"), Cue(2, 3000, 3500, "Next")]
    result = retime_cues_for_readability(
        cues, media_end_ms=5000, max_chars_per_second=100, min_duration_ms=1200
    )
    assert result[0].end_ms == 1200
    assert result[1].end_ms >= 3500


def test_readability_retiming_rejects_impossible_timeline():
    from sokhan.subtitles import retime_cues_for_readability

    cues = [Cue(1, 0, 500, "A very long line that needs more display time")]
    with pytest.raises(ValueError, match="only"):
        retime_cues_for_readability(cues, media_end_ms=1000, max_chars_per_second=5)
