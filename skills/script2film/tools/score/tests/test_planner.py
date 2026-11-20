import json
import subprocess
import sys
from pathlib import Path

import pytest

from planner import PlanError, make_plan
from styles import STYLES

SC = Path(__file__).resolve().parent.parent
T1221 = [0, 6.53, 12.17, 15.88, 21.73, 46.65, 55.79, 67.9, 72.72]
R1221 = ["intro", "title", "verse", "verse", "body", "warm", "reflect", "pause", "outro"]


def ev1221(**kw):
    return {"name": "t1221", "duration": 80.3, "style": "devotion",
            "sections": [{"t": t, "role": r} for t, r in zip(T1221, R1221)], **kw}


def story(seed, hits=True):
    return {"name": f"s{seed}", "duration": 30, "style": "story", "under_voice": False, "seed": seed,
            "sections": [{"t": t, "role": r} for t, r in
                         zip([0, 4, 9, 15, 21, 26], ["intro", "title", "body", "warm", "pause", "outro"])],
            "hits": [{"t": 10.3}, {"t": 17.77}] if hits else []}


def test_unknown_role():
    with pytest.raises(PlanError, match="climax") as e:
        make_plan({"name": "x", "duration": 20, "sections": [{"t": 0, "role": "intro"}, {"t": 5, "role": "climax"}]})
    assert "intro" in str(e.value)  # 附允許清單


def test_non_increasing_t():
    with pytest.raises(PlanError, match=r"sections\[2\]\.t"):
        make_plan({"name": "x", "duration": 20, "sections": [{"t": t, "role": "body"} for t in (0, 10, 8)]})


def test_story_rejects_emmanuel():
    with pytest.raises(PlanError, match="emmanuel"):
        make_plan({**story(1), "motif": "emmanuel"})


def test_hit_out_of_range():
    with pytest.raises(PlanError, match=r"hits\[0\]\.t"):
        make_plan({**story(1), "hits": [{"t": 99}]})


def test_1221_starts_and_bpm():
    p = make_plan(ev1221())
    assert [s["start"] for s in p["sections"]] == T1221
    for s in p["sections"]:
        assert 64 <= 60 * s["beats"] / (s["end"] - s["start"]) <= 80


def test_short_section_merged():
    e = ev1221()
    e["sections"].insert(3, {"t": 15.0, "role": "verse"})  # 15.0–15.88 = 0.88 秒
    assert len(make_plan(e)["sections"]) == len(T1221)


def test_first_short_section_merged_into_next():
    e = {"name": "x", "duration": 20, "sections": [{"t": 0, "role": "intro"}, {"t": 1, "role": "body"}]}
    s = make_plan(e)["sections"]
    assert len(s) == 1 and s[0]["start"] == 0 and s[0]["role"] == "body"


def test_chord_beats_sum_and_cadence():
    p = make_plan(ev1221())
    for s in p["sections"]:
        assert sum(nb for _, nb in s["chords"]) == s["beats"]
    assert p["sections"][-2]["chords"][-1][0] == "B"
    assert p["sections"][-1]["chords"][-1][0] == "G"


@pytest.mark.parametrize("combo", ["dev-auto", "dev-emm", "story-auto"])
def test_melody_range(combo):
    for seed in range(50):
        if combo == "story-auto":
            e = story(seed)
        else:
            e = {**ev1221(seed=seed, motif="emmanuel" if combo == "dev-emm" else "auto"), "hits": [{"t": 30.0}]}
        for s in make_plan(e)["sections"]:
            for m in s["melody"]:
                assert 60 <= m[1] <= 76, (combo, seed, s["role"], m)
                assert m[2] > 0


def test_hits_absolute_time():
    p = make_plan(story(3))
    hits = [(s, m) for s in p["sections"] for m in s["melody"] if m[4:] == ["hit"]]
    assert len(hits) == 2
    for (s, m), t in zip(hits, [10.3, 17.77]):
        assert abs(s["start"] + m[0] * (s["end"] - s["start"]) / s["beats"] - t) < 1e-3


def test_story_shaker_layers():
    p = make_plan(story(1))
    assert all(("shaker" in s["layers"]) == (s["role"] in STYLES["story"]["shaker_roles"]) for s in p["sections"])


def test_deterministic_across_processes(tmp_path):
    f = tmp_path / "e.json"
    f.write_text(json.dumps(ev1221()), encoding="utf-8")
    outs = [subprocess.run([sys.executable, "score.py", "plan", str(f), "--out", str(tmp_path / f"p{i}.json")],
                           cwd=SC, check=True) and (tmp_path / f"p{i}.json").read_bytes() for i in range(2)]
    assert outs[0] == outs[1]
