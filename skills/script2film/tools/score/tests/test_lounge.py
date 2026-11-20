import random

from planner import make_plan
from score import CHANNEL, DRUM, SWING, build_events
from styles import SHAKER, STYLES, degree_chord, parse_chord

EV = {"name": "lounge-sample", "duration": 40, "style": "lounge", "under_voice": True,
      "sections": [{"t": 0, "role": "intro"}, {"t": 6, "role": "verse"}, {"t": 20, "role": "reflect"},
                   {"t": 26, "role": "warm"}, {"t": 34, "role": "outro"}]}


def ons(plan):
    return [e for e in build_events(plan, random.Random(0)) if e[1] == 1]


def test_seventh_chords_parse():
    assert parse_chord("Fmaj7") == [5, 9, 0, 4]
    assert parse_chord("Gm7") == [7, 10, 2, 5]
    assert parse_chord("C7") == [0, 4, 7, 10]
    assert parse_chord("Em") == [4, 7, 11]  # 既有三和弦不受影響


def test_major_degrees():
    assert degree_chord(5, "I", "major") == "Fmaj7"
    assert degree_chord(5, "ii", "major") == "Gm7"
    assert degree_chord(5, "V", "major") == "C7"
    assert degree_chord(4, "i") == "Em"  # 預設仍是小調


def test_lounge_plan_is_major_and_ends_on_tonic():
    p = make_plan(EV)
    assert p["key"] == "F major"
    assert p["sections"][-1]["chords"][-1][0] == "Fmaj7"
    lo, hi = STYLES["lounge"]["bpm"]
    for s in p["sections"]:
        assert lo <= 60 * s["beats"] / (s["end"] - s["start"]) <= hi, s
        assert sum(nb for _, nb in s["chords"]) == s["beats"]


def test_walking_bass_one_note_per_beat():
    p = make_plan(EV)
    verse = next(s for s in p["sections"] if s["role"] == "verse")
    bass = [e for e in ons(p) if e[2] == CHANNEL["bass"] and verse["start"] - .02 <= e[0] < verse["end"] - .02]
    assert len(bass) == verse["beats"]


def test_swing_ride_skip_lands_on_triplet():
    p = make_plan(EV)
    verse = next(s for s in p["sections"] if s["role"] == "verse")
    spb = (verse["end"] - verse["start"]) / verse["beats"]
    rides = sorted(round((e[0] - verse["start"]) / spb, 3) for e in ons(p)
                   if e[2] == SHAKER["channel"] and e[3] == DRUM["ride"] and verse["start"] <= e[0] < verse["end"])
    assert round(SWING, 3) in rides  # 第一個切音在第 1 拍的三連音第三格（2/3 拍）


def test_reflect_has_no_drums_except_bell():
    p = make_plan(EV)
    r = next(s for s in p["sections"] if s["role"] == "reflect")
    keys = {e[3] for e in ons(p) if e[2] == SHAKER["channel"] and r["start"] <= e[0] < r["end"]}
    assert keys == {DRUM["bell"]}


def test_every_section_start_has_bell():
    p = make_plan(EV)
    bells = [e[0] for e in ons(p) if e[2] == SHAKER["channel"] and e[3] == DRUM["bell"]]
    assert bells == [s["start"] for s in p["sections"]]


def test_other_styles_have_no_lounge_layers():
    for st in ("devotion", "story", "scifi"):
        p = make_plan({**EV, "style": st, "name": f"{st}-x"})
        assert not any({"comp", "walk", "swing"} & set(s["layers"]) for s in p["sections"])
