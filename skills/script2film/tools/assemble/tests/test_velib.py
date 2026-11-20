import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from velib import line_cuts, parse_srt, segment_frames, shot_windows, timeline_cfg  # noqa: E402

SRT = """1
00:00:01,780 --> 00:00:05,300
早飯的時候

2
00:00:05,300 --> 00:00:09,720
喝茶

3
00:00:09,720 --> 00:00:15,060
筷子停住

4
00:00:15,060 --> 00:00:19,260
初五，她把粥推過去
"""


def test_parse_srt():
    cues = parse_srt(SRT)
    assert [c[0] for c in cues] == [1, 2, 3, 4]
    assert cues[0][1:3] == (1.78, 5.3)
    assert cues[3][3] == "初五，她把粥推過去"


def test_windows_first_shot_starts_at_zero_and_last_ends_at_last_cue():
    w = shot_windows(parse_srt(SRT), {"shot1": 1, "shot2": 2, "shot3": 3})
    assert w == [("shot1", 0.0, 5.3), ("shot2", 5.3, 9.72), ("shot3", 9.72, 19.26)]


def test_windows_split_inside_a_cue_by_seconds():
    w = shot_windows(parse_srt(SRT), {"shot1": 1, "shot2": 4, "shot3": "16.84s"})
    assert w[1] == ("shot2", 15.06, 16.84) and w[2] == ("shot3", 16.84, 19.26)


@pytest.mark.parametrize("shots, msg", [
    ({"shot1": 1, "shot2": 9}, "have no line 9"),
    ({"shot1": 1, "shot2": 3, "shot3": 2}, "is not before the next shot"),
    ({"shot1": 1, "shot2": "abc"}, "must be a subtitle line number"),
    ({"shot1": 1, "shot2": True}, "is not a subtitle line number"),
    ({}, "is empty"),
])
def test_windows_reject_bad_tables(shots, msg):
    with pytest.raises(ValueError, match=msg):
        shot_windows(parse_srt(SRT), shots)


def test_segment_frames_do_not_drift():
    bounds = [0.0, 5.3, 9.72, 13.5, 16.84, 19.26]
    total = sum(segment_frames(a, b) for a, b in zip(bounds, bounds[1:]))
    assert total == round(19.26 * 24)


def test_line_cuts_are_seamless():
    lines = [{"n": 1, "start": 0.0, "end": 3.0}, {"n": 2, "start": 3.4, "end": 6.0}, {"n": 3, "start": 6.6, "end": 9.0}]
    cuts = line_cuts(lines, total=10.0, lead=0.45)
    assert cuts[0][1] == 0.0 and cuts[-1][2] == 10.0
    assert all(abs(p[2] - q[1]) < 1e-9 for p, q in zip(cuts, cuts[1:]))
    assert cuts[1][1] == pytest.approx(0.45 + 3.2)


# ---- sequence mode
from velib import block_bounds, clamp, shift_cues, speech_span  # noqa: E402


def test_block_bounds_use_the_line_boundary_before_each_retimed_start():
    cues = [(1, 0.9, 3.83, "a"), (2, 4.76, 8.19, "b"), (3, 8.94, 11.61, "c"), (4, 13.25, 13.95, "d")]
    cuts = [4.07, 8.35, 12.015, 14.19]  # 14.19 is nearer to 13.25 but after it
    assert block_bounds(cues, 1, 4, cuts, 14.0) == (0.0, 14.0)    # whole track
    assert block_bounds(cues, 1, 1, cuts, 14.0) == (0.0, 4.07)
    assert block_bounds(cues, 3, 3, cuts, 14.0) == (8.35, 12.015)  # next start 13.25: the cut before it, not the nearest
    with pytest.raises(ValueError):
        block_bounds(cues, 1, 9, cuts, 14.0)


def test_block_windows_inside_a_block():
    cues = parse_srt(SRT)
    w = shot_windows(cues, {"shot3": 3, "shot4": "16.84s"}, start=9.72, end=19.26)
    assert w == [("shot3", 9.72, 16.84), ("shot4", 16.84, 19.26)]


def test_shift_cues():
    cues = parse_srt(SRT)
    assert shift_cues(cues, 9.72, 19.26, 10.0) == [(10.0, 15.34, "筷子停住"), (15.34, 19.54, "初五，她把粥推過去")]
    assert shift_cues(cues, 0.0, 5.3, 0.0) == [(1.78, 5.3, "早飯的時候")]


def test_speech_span():
    log = "silence_start: 0\nsilence_end: 0.766\nsilence_start: 4.697\nsilence_end: 6.037\n"
    assert speech_span(log, 6.04) == (0.766, 4.697)
    talk_to_end = "silence_start: 1.4\nsilence_end: 1.77\nsilence_start: 4.43\nsilence_end: 4.9\n"
    assert speech_span(talk_to_end, 6.04) == (0.0, 6.04)
    assert speech_span("", 5.0) == (0.0, 5.0)


def test_clamp():
    assert clamp(3.0, 6.0, 5.3, 9.0) == (5.3, 6.0)
    assert clamp(1.0, 2.0, 5.3, 9.0) is None


# ---- 字幕對齊配音表

from velib import retime_cues, silences, speech_bounds  # noqa: E402

LINES = [{"n": 1, "start": 0.0, "end": 3.46}, {"n": 2, "start": 3.78, "end": 7.74},
         {"n": 3, "start": 8.06, "end": 9.0}, {"n": 4, "start": 9.32, "end": 12.0}]


def test_silences_keep_dangling_tail():
    log = "silence_start: 0\nsilence_end: 0.9\nsilence_start: 3.83\nsilence_end: 4.76\nsilence_start: 12.1\n"
    assert silences(log, 13.0) == [(0.0, 0.9), (3.83, 4.76), (12.1, 13.0)]


def test_speech_bounds_trim_lead_silence_and_fall_back():
    sil = [(0.0, 0.9), (3.83, 4.76), (8.19, 8.94)]
    b = speech_bounds(LINES, 0.45, sil, 13.0)
    assert b[0] == (0.9, 3.83)     # start 0.45 在靜音裡 → 0.9；end 3.91 在靜音裡 → 3.83
    assert b[1] == (4.76, 8.19)    # end 8.19 剛好是靜音起點
    assert b[3] == (9.77, 12.45)   # 沒落在靜音裡 → 照配音表
    assert speech_bounds(LINES, 0.45, [], 12.0)[3] == (9.77, 12.0)  # end 夾到檔長以內


def test_retime_fixes_group_edges_keeps_interior_and_spans_lines():
    bounds = [(0.9, 3.83), (4.76, 8.19), (8.94, 9.3), (9.9, 11.8)]
    cues = [(1, 1.78, 5.3, "一"), (2, 5.3, 6.4, "二a"), (3, 6.4, 9.72, "二b"),
            (4, 9.5, 12.5, "跨三四")]  # 第 4 句字幕從配音第 3 句開始、蓋到第 4 句
    got = retime_cues(cues, LINES, 0.45, bounds)
    assert got == [(1, 0.9, 3.83, "一"), (2, 4.76, 6.4, "二a"), (3, 6.4, 8.19, "二b"), (4, 8.94, 11.8, "跨三四")]


def test_retime_rejects_first_line_without_cue():
    with pytest.raises(ValueError, match="voice line 1"):
        retime_cues([(1, 5.0, 6.0, "x")], LINES, 0.45, [(0, 1)] * 4)


from velib import speech_spans, splice_cuts  # noqa: E402


def test_speech_spans_and_splice_cuts():
    sil = [(0.0, 0.36), (0.996, 2.141), (2.619, 4.032)]
    spans = speech_spans(sil, 4.042)
    assert spans == [(0.36, 0.996), (2.141, 2.619)]   # 片尾 0.01 秒不算一段
    assert splice_cuts(spans, 4.042) == [(0.0, 1.569), (1.569, 4.042)]
    assert speech_spans([], 3.0) == [(0.0, 3.0)]


def test_stretch_factor():
    from velib import stretch_factor
    assert stretch_factor(6.0, 5.0, 1.5) == 1.0          # 片夠長不放慢
    assert stretch_factor(4.0, 5.0, 1.5) == 1.25         # 放慢到剛好填滿
    assert stretch_factor(4.0, 7.1, 1.5) == 1.5          # 最多放慢到上限，其餘仍凍結
    assert stretch_factor(4.0, 7.1, 1.0) == 1.0          # 上限 1＝不放慢（預設）
    with pytest.raises(ValueError):
        stretch_factor(4.0, 5.0, 0.8)


def test_timeline_cfg_new_key_only():
    assert timeline_cfg({"timeline": {"name": "a"}}) == {"name": "a"}


def test_timeline_cfg_old_key_only():
    assert timeline_cfg({"capcut": {"name": "b"}}) == {"name": "b"}


def test_timeline_cfg_both_prefers_timeline():
    assert timeline_cfg({"capcut": {"name": "b"}, "timeline": {"name": "a"}}) == {"name": "a"}
    assert timeline_cfg({}) == {}
