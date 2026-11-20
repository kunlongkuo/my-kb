import random

from planner import make_plan
from score import DRUM, build_events
from styles import SHAKER, STYLES

EV = {"name": "scifi-sample", "duration": 32, "style": "scifi", "under_voice": False,
      "sections": [{"t": 0, "role": "intro"}, {"t": 4.5, "role": "verse"}, {"t": 11.6, "role": "body"},
                   {"t": 17.1, "role": "pause"}, {"t": 19.1, "role": "verse"}, {"t": 29, "role": "outro"}],
      "hits": [{"t": 6.4}, {"t": 15.1}, {"t": 24.3}]}


def drum_notes(plan):
    return [e for e in build_events(plan, random.Random(0)) if e[2] == SHAKER["channel"] and e[1] == 1]


def test_scifi_drum_layers_follow_roles():
    p = make_plan(EV)
    assert all(("drums" in s["layers"]) == (s["role"] in STYLES["scifi"]["drum_roles"]) for s in p["sections"])
    assert not any("shaker" in s["layers"] for s in p["sections"])


def test_scifi_tempo_range():
    lo, hi = STYLES["scifi"]["bpm"]
    for s in make_plan(EV)["sections"]:
        assert lo <= 60 * s["beats"] / (s["end"] - s["start"]) <= hi, s


def test_scifi_hits_get_kick_and_crash():
    notes = drum_notes(make_plan(EV))
    for t in (6.4, 15.1, 24.3):
        keys = {k for at, _, _, k, _ in notes if abs(at - t) < 0.02}
        assert {DRUM["kick"], DRUM["crash"]} <= keys, (t, keys)


def test_pause_section_has_no_drums():
    p = make_plan(EV)
    pause = next(s for s in p["sections"] if s["role"] == "pause")
    hits = {round(h["t"], 2) for h in EV["hits"]}
    inside = [at for at, *_ in drum_notes(p) if pause["start"] <= at < pause["end"] and round(at, 2) not in hits]
    assert inside == []


def test_story_has_no_drum_kit_notes():
    p = make_plan({**EV, "style": "story", "name": "story-x"})
    assert {k for *_, k, _ in drum_notes(p)} <= {SHAKER["key"]}
