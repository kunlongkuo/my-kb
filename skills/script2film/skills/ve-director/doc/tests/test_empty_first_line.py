"""doc_code.empty_first_line: a quote card whose phrase is in the beat's second line leaves the first line on bare paper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_code import empty_first_line  # noqa: E402

DOC = {"lang": "zh", "lines": [{"text": "很多年以後"}, {"text": "我就是糧"}]}
BEAT = {"id": "B19", "lines": [1, 2],
        "tokens": [["很", 0.2], ["多", 0.4], ["年", 0.6], ["以", 0.8], ["後", 1.0], ["我", 4.3], ["就", 4.5], ["是", 4.7], ["糧", 4.9]]}


def spec(scene="quote_card", at="我就是"):
    return {"scene": scene, "params": {"text": "x", "at": at}}


def test_phrase_in_second_line_is_flagged():
    m = empty_first_line(DOC, BEAT, spec())
    assert m and "B19" in m and "line 2" in m


def test_phrase_in_first_line_or_number_passes():
    assert empty_first_line(DOC, BEAT, spec(at="以後")) is None
    assert empty_first_line(DOC, BEAT, spec(at=0.3)) is None


def test_other_scenes_and_one_line_beats_pass():
    assert empty_first_line(DOC, BEAT, spec(scene="list_reveal")) is None
    assert empty_first_line(DOC, {**BEAT, "lines": [1]}, spec()) is None


# ---- late_first_element: the phrase is inside the first line but late (stops the render since 2026-11-15) ----
from doc_code import late_first_element  # noqa: E402

ONE = {"id": "B48", "lines": [1], "tokens": [["他", 0.2], ["到", 0.4], ["撒", 2.5], ["該", 2.7], ["說", 2.9]]}
DOC1 = {"lang": "zh", "lines": [{"text": "他到撒該說"}]}


def test_late_phrase_in_a_one_line_beat_is_listed():
    m = late_first_element(DOC1, ONE, spec(at="撒該"))
    assert m and "B48" in m and "2.5 s into the beat" in m
    assert empty_first_line(DOC1, ONE, spec(at="撒該")) is None      # the stop keeps its old scope


def test_early_phrase_or_small_number_is_not_listed():
    assert late_first_element(DOC1, ONE, spec(at="他到")) is None
    assert late_first_element(DOC1, ONE, spec(at=0.4)) is None


def test_late_number_is_listed_too():
    assert "3.0 s" in late_first_element(DOC1, ONE, spec(at=3.0))


def test_something_else_on_screen_is_not_listed():
    assert late_first_element(DOC1, ONE, {**spec(at="撒該"), "bg_video": {"src": "ve_live/s.mp4", "tone": "light"}}) is None
    assert late_first_element({**DOC1, "side": {"beats": ["B48"]}}, ONE, spec(at="撒該")) is None
    assert late_first_element({**DOC1, "pip": {"beats": ["B48"]}}, ONE, spec(at="撒該")) is None
    s = spec(at="撒該")
    s["params"]["photos"] = [{"src": "stills/a.jpg", "at": 0.05}]
    assert late_first_element(DOC1, ONE, s) is None


def test_late_still_or_the_card_s_own_photo_does_not_count():
    s = spec(at="撒該")
    s["params"]["photos"] = [{"src": "stills/a.jpg", "at": "撒該"}]
    assert late_first_element(DOC1, ONE, s)
    s = spec(at="撒該")
    s["params"]["photo"] = {"src": "stills/c.jpg"}
    assert late_first_element(DOC1, ONE, s)


def test_phrase_missing_or_already_stopped_is_not_repeated():
    assert late_first_element(DOC1, ONE, spec(at="不存在")) is None
    assert empty_first_line(DOC, BEAT, spec()) and late_first_element(DOC, BEAT, spec()) is None
