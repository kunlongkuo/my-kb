"""pytest for doc_lint's two reports: read_time (on-screen text held long enough) and vs_prev (not the last episode again)."""
import copy
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from doc_lint import at_texts, late_reveal, prev_episode, read_time, vs_prev  # noqa: E402

DOC = {"lang": "zh", "lines": [{"text": "封面"}, {"text": "鉤子"}, {"text": "引句"}, {"text": "主持"}],
       "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "cover", "params": {}},
                 {"id": "B2", "lines": [2], "source": "ve", "shot": "s"},
                 {"id": "B3", "lines": [3], "source": "code", "scene": "quote_card", "params": {"text": "x"}},
                 {"id": "B4", "lines": [4], "source": "clip"}]}


def beat(text, duration, at=0.15):
    return {"id": "B3", "source": "code", "scene": "quote_card", "params": {"text": text, "at": at},
            "tokens": [["引", 0.2]], "duration": duration}


def test_read_time_flags_text_shown_too_briefly():
    text = "一二三四五六七八九十"                        # 10 characters: 10 / 4.5 + 1.5 = 3.72 s
    assert read_time(DOC, [beat(text, 3.9)]) == []    # 3.9 - 0.15 = 3.75 s on screen
    slow = read_time(DOC, [beat(text, 3.8)])           # 3.65 s on screen
    assert len(slow) == 1 and "B3" in slow[0]


def test_read_time_counts_from_the_phrase_that_brings_the_text_in():
    assert read_time(DOC, [beat("一二三", 2.4, at="引")]) == []         # 3 / 4.5 + 1.5 = 2.17 s, shown at 0.2 s
    assert read_time(DOC, [beat("一二三", 2.3, at="引")]) != []


def test_vs_prev_identical_episode_differs_in_nothing():
    same, differ = vs_prev(DOC, copy.deepcopy(DOC))
    assert differ == 0 and len(same) == 6


def test_vs_prev_counts_changed_items():
    other = copy.deepcopy(DOC)
    other["beats"][1] = {"id": "B2", "lines": [2], "source": "code", "scene": "stat_count", "params": {}}   # hook + structure + mix
    same, differ = vs_prev(DOC, other)
    assert differ == 3, same


def test_prev_episode_finds_sibling_numbered_one_less(tmp_path):
    for name in ("011_a", "012_b"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "doc.json").write_text(json.dumps(DOC))
    assert prev_episode(tmp_path / "012_b" / "doc.json") == tmp_path / "011_a" / "doc.json"
    assert prev_episode(tmp_path / "011_a") is None


LATE_DOC = {"lang": "zh", "beats": [{"id": "B1", "source": "code", "scene": "compare", "params": {
    "left": {"title": "甲", "at": "一", "items": [{"text": "早", "at": "一"}]},
    "right": {"title": "乙", "items": [{"text": "中"}, {"text": "晚項", "at": "三"}]},
    "verdict": {"side": "right", "text": "結論", "at": "三"}}}]}


def late_beat(duration, tokens=(("一", 0.2), ("二", 1.0), ("三", 2.0))):
    return {"id": "B1", "source": "code", "tokens": [list(t) for t in tokens], "duration": duration}


def test_at_texts_walks_nested_params_and_the_quote_card():
    assert [(p, t) for p, t, _ in at_texts(LATE_DOC["beats"][0]["params"])] == [
        ("left.items[0]", "早"), ("right.items[1]", "晚項"), ("verdict", "結論")]   # a title has no "text"; "中" has no "at"
    assert list(at_texts({"text": "引言", "at": "保羅"})) == [("text", "引言", "保羅")]
    assert list(at_texts({"text": "", "at": 1})) == []


def test_late_reveal_uses_the_half_second_floor():
    assert late_reveal(LATE_DOC, [late_beat(2.5)]) == []                       # 0.50 s left: not reported
    late = late_reveal(LATE_DOC, [late_beat(2.49)])                            # 0.49 s left
    assert len(late) == 2 and "right.items[1]" in late[0] and "verdict 「結論」" in late[1] and "0.49s" in late[1]


def test_late_reveal_skips_a_phrase_that_is_not_spoken_and_other_sources():
    doc = copy.deepcopy(LATE_DOC)
    doc["beats"][0]["params"]["verdict"]["at"] = "沒有這個詞"
    assert [x for x in late_reveal(doc, [late_beat(2.1)]) if "verdict" in x] == []
    doc["beats"][0]["params"]["verdict"]["at"] = 2.0                           # a number is a time from the beat's start
    assert any("verdict" in x for x in late_reveal(doc, [late_beat(2.1)]))
    assert late_reveal(LATE_DOC, [{**late_beat(2.1), "id": "B9"}]) == []        # a beat the doc does not draw by code


def test_late_reveal_reports_a_countdown_whose_clock_outruns_the_beat():
    doc = {"lang": "zh", "beats": [{"id": "B1", "source": "code", "scene": "countdown", "params": {"value": 204, "at": "二"}}]}
    assert late_reveal(doc, [late_beat(4.5)]) == []                       # 1.0 + 3 = 4.0 s: 0.50 s of the final value
    late = late_reveal(doc, [late_beat(4.49)])
    assert len(late) == 1 and "B1 countdown" in late[0] and "dur at most 2.9" in late[0] and "4.00s" in late[0]
    doc["beats"][0]["params"] = {"value": 204, "dur": 5}                  # no at: the clock starts at 0.3 s and runs to 5.3 s
    assert "dur at most 2.9" in late_reveal(doc, [late_beat(3.7)])[0]
    doc["beats"][0]["params"]["at"] = "沒有這個詞"                         # not spoken: doc_code.py reports that
    assert late_reveal(doc, [late_beat(3.7)]) == []
