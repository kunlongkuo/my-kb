import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import drama_sheet as ds  # noqa: E402

D = {"style": "Photorealistic live-action, real people, shot on a cinema camera, 35mm lens, 16:9.",
     "location": "Indoors in a dim bedroom.", "accent": "Taiwanese Mandarin",
     "actors": {"1": "CHEN master", "3": "room A master"},
     "characters": {"CHEN": {"actor": 1, "bible": "CHEN — a man of forty, one single braid"}},
     "sets": {"roomA": 3},
     "shots": [
         {"id": "D1", "dur": 5, "slug": "he wakes", "framing": "Wide shot from the doorway.", "image": "{CHEN} sits up in bed.",
          "cast": ["CHEN"], "set": "roomA", "motion": "CHEN sits up.", "sound": "room tone"},
         {"id": "D2", "dur": 5, "slug": "the ceiling", "framing": "Architectural photograph, camera pointing straight up.",
          "image": "Only the dark red beams, no person.", "location": False, "motion": "Camera locked. The basket sways.",
          "sound": "room tone"},
         {"id": "D3", "dur": 6, "slug": "he answers", "framing": "Close-up, eye level.", "image": "{CHEN}, blank face.",
          "cast": ["CHEN"], "line": {"who": "CHEN", "tone": "slow, uncertain", "text": "我再想一想。"}, "sound": "his voice"},
     ]}


def shot_md(md, n):
    return md.split(f"## Shot {n}\n")[1].split("\n## Shot")[0]


def test_render_rules():
    md = ds.render(D)
    s1, s2, s3 = shot_md(md, 1), shot_md(md, 2), shot_md(md, 3)
    assert "- **Cast:** Actor 1, Actor 3" in s1
    assert "CHEN — a man of forty, one single braid sits up in bed. Indoors in a dim bedroom." in s1  # bible + location verbatim
    t2i_2 = [l for l in s2.splitlines() if l.startswith("- **Text-To-Image")][0]
    assert "cinema camera" not in t2i_2 and "Indoors" not in t2i_2  # no person: no camera phrase; location off
    assert "Keep the framing identical to the start image; no person appears." in s2
    assert "Camera locked. Camera locked." not in s2
    v3 = [l for l in s3.splitlines() if l.startswith("- **Image-To-Video")][0]
    assert 'Right from the first second, CHEN says in a slow, uncertain Taiwanese Mandarin accent: "我再想一想。"' in v3
    assert "No dialogue" not in v3 and "No dialogue; nobody speaks." in s1
    assert t2i_2.endswith("Dynamic composition, subject fills the frame.")


def test_set_master_refused_on_close_up():
    d = copy.deepcopy(D)
    d["shots"][2]["set"] = "roomA"
    with pytest.raises(ds.SheetError, match="non-wide"):
        ds.render(d)
    d["shots"][2]["force_set"] = True
    assert "Actor 1, Actor 3" in shot_md(ds.render(d), 3)


def test_line_length_cap():
    d = copy.deepcopy(D)
    d["shots"][2]["dur"] = 5
    d["shots"][2]["line"]["text"] = "郭家說初五要回話，你到底想好了沒有啊？"  # 17 字 > 15 for 5 s
    with pytest.raises(ds.SheetError, match="ceiling"):
        ds.render(d)


def test_unknown_character_and_duplicate_id():
    d = copy.deepcopy(D)
    d["shots"][0]["image"] = "{SUQIN} at the door."
    with pytest.raises(ds.SheetError, match="unknown character"):
        ds.render(d)
    d = copy.deepcopy(D)
    d["shots"][1]["id"] = "D1"
    with pytest.raises(ds.SheetError, match="duplicate"):
        ds.render(d)


def test_two_speakers_refused():
    d = copy.deepcopy(D)
    d["shots"][0]["motion"] = 'CHEN says in a calm accent: "好。" and SUQIN says in a calm accent: "嗯。"'
    with pytest.raises(ds.SheetError, match="one speaker"):
        ds.render(d)
