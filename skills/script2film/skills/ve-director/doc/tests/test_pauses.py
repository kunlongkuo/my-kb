"""doc_pauses: lengthen only pauses the voice already made, never cut into a syllable; slow fast lines by at most 5%
(2026-11-06 samples D–G)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_pauses as dp  # noqa: E402

SR = 48000


def tone(sec, db=-20):
    t = np.arange(int(sec * SR)) / SR
    return (10 ** (db / 20) * np.sqrt(2) * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def quiet(sec, db=-70):
    return tone(sec, db)


def test_marks_merge_and_skip_line_end():
    text = "再問他：「你想，這樣。」"
    words = [("再", 0, .2), ("問", .2, .4), ("他", .4, .6), ("你", .6, .8), ("想", .8, 1.0),
             ("這", 1.0, 1.2), ("樣", 1.2, 1.4)]
    st, en = dp.char_times(words)
    m = dp.marks(text, st, en)
    assert m == [(0.6, 0.4), (1.0, 0.4)]   # ：「 merged into one; 。」 at the end skipped
    st, en = dp.char_times([("呢", 0, .2), ("祂", .2, .4)])
    assert dp.marks("呢，」祂", st, en) == [(0.2, 0.65)]   # ，」 merged with the larger target


def test_char_times_split_words_evenly():
    st, en = dp.char_times([("第二", 0.0, 0.4), ("AI", 0.4, 0.6)])
    assert np.allclose(st, [0, .2, .4, .5]) and np.allclose(en, [.2, .4, .5, .6])


def test_quiet_runs_ignore_edges_and_short_dips():
    x = np.concatenate([quiet(.3), tone(.5), quiet(.04), tone(.3), quiet(.12), tone(.3), quiet(.3)])
    runs = dp.quiet_runs(x, SR)
    assert len(runs) == 1   # the 0.04 s dip (a stop consonant) and the leading/trailing silence are not pauses
    a, b, d = runs[0]
    assert abs(a - 1.14) < 0.02 and abs(b - 1.26) < 0.02 and d < -60


def test_pick_deepest_near():
    runs = [(0.97, 1.04, -46.0), (1.12, 1.19, -56.0), (2.0, 2.5, -70.0)]
    assert dp.pick_run(runs, 1.06) == (1.12, 1.19, -56.0)   # 清楚。: the deep pause, not the dip inside 楚
    assert dp.pick_run(runs, 1.5) is None


def test_no_real_pause_means_no_insert():
    """「第三，」 with no gap: D inserted silence between 第 and 三; now nothing is added."""
    x = np.concatenate([quiet(.1), tone(.9), quiet(.1)])
    cuts, hits = dp.plan(x, SR, "第三，重要", [("第三", .1, .4), ("重要", .4, 1.0)])
    assert cuts == [] and hits == 0
    assert len(dp.apply(x, SR, cuts)) == len(x)


def test_consonant_gap_is_not_a_pause():
    """「不吃不喝、」: the quiet onset of 喝 (0.09 s) sat next to the mark; the pause went inside the word (2026-11-10)."""
    x = np.concatenate([quiet(.1), tone(.4), quiet(.09), tone(.4), quiet(.1)])
    cuts, hits = dp.plan(x, SR, "不喝、全年", [("不", .1, .5), ("喝", .59, .99), ("全年", .99, 1.0)])
    assert cuts == [] and hits == 0


def test_lengthen_from_middle_of_real_pause():
    x = np.concatenate([quiet(.1), tone(.4), quiet(.15), tone(.4), quiet(.1)])
    # ASR puts the comma 0.15 s early, as it often does
    cuts, hits = dp.plan(x, SR, "第二，它引", [("第二", .1, .4), ("它引", .4, 1.0)])
    assert hits == 1 and len(cuts) == 1
    at, add = cuts[0]
    assert abs(at - 0.575) < 0.02 and abs(add - 0.25) < 0.02
    y = dp.apply(x, SR, cuts)
    assert abs(len(y) / SR - (len(x) / SR + add)) < 0.001
    k = int(round(at * SR))
    assert np.allclose(y[:k], x[:k]) and np.allclose(y[-(len(x) - k):], x[k:])


def test_strong_mark_target():
    x = np.concatenate([quiet(.1), tone(.4), quiet(.15), tone(.4), quiet(.1)])
    cuts, _ = dp.plan(x, SR, "清楚。跟", [("清楚", .1, .5), ("跟", .65, 1.05)])
    assert abs(cuts[0][1] - 0.5) < 0.02


def test_tempo_caps_at_5_percent():
    assert dp.tempo("一二三四五六七八九十", 2.0) is None   # 5.0 chars/s
    assert dp.tempo("一二三四五六七八九十一二", 2.0) == 0.95   # 6.0 → 5.6/6.0 = 0.933, capped at 0.95
    assert dp.tempo("一二三四五六七八九十一", 1.92) == round(5.6 / (11 / 1.92), 4)   # 5.73 → 0.977
    assert dp.tempo("一二", 0) is None


def test_pace_gap_prefers_near_target_not_slowest():
    text = "一二三四五六七八九十"
    gaps = {sec: dp.pace_gap(text, sec) for sec in (1.6, 2.0, 2.4)}   # 6.25, 5.0, 4.17 a second
    assert min(gaps, key=gaps.get) == 2.0
