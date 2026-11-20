"""素材盤點：六拍的小稿子，三個數用手算的值對。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inventory  # noqa: E402

DOC = {
    "lines": [{"text": "一" * 10}] * 6,
    "side": {"beats": ["B6"]},
    "beats": [
        {"id": "B1", "lines": [1], "source": "code", "scene": "bullet_list", "bg_video": {"src": "ve_live/shot1.mp4", "tone": "light"}},
        {"id": "B2", "lines": [2], "source": "code", "scene": "stat_count", "bg_video": {"src": "ve_live/shot1.mp4", "tone": "dark"}},
        {"id": "B3", "lines": [3], "source": "clip", "clip": "ve_live/shot2.mp4"},
        {"id": "B4", "lines": [4], "source": "code", "scene": "photo", "params": {"photos": [{"src": "assets/a.jpg"}]}},
        {"id": "B5", "lines": [5], "source": "clip", "clip": "host/tp_host.mp4"},
        {"id": "B6", "lines": [6], "source": "code", "scene": "relation"},
    ],
}
REAL = {"B1": 4.0, "B2": 6.0, "B3": 5.0, "B4": 5.0, "B5": 10.0, "B6": 10.0}


def test_measured_numbers():
    inv = inventory.inventory(DOC, REAL)
    assert inv["measured"] and inv["total"] == 40.0
    assert inv["card_run_max"] == {"sec": 10.0, "from": "B1", "to": "B2"}      # B1+B2 相連，VE 斷開
    assert inv["bg_video"] == {"ve_live/shot1.mp4": 10.0}
    assert inv["share"] == {"photo": round(5 / 30, 4), "ve": round(5 / 30, 4), "card": round(10 / 30, 4),
                            "card_host": round(10 / 30, 4), "host": 0.25}      # 主持人 10 秒不佔前四欄的分母


def test_estimate_without_beats_json():
    inv = inventory.inventory(DOC, None, k=0.2)
    assert not inv["measured"] and inv["total"] == 12.0 and inv["card_run_max"]["sec"] == 4.0


def test_full_tone_video_counts_as_ve():
    doc = {"lines": [{"text": "一" * 10}], "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "photo",
                                                      "params": {"label": "x"}, "bg_video": {"src": "ve_live/s.mp4", "tone": "full"}}]}
    assert inventory.inventory(doc, {"B1": 3.0})["share"]["ve"] == 1.0


def test_no_side_or_pip_key():
    doc = {"lines": [{"text": "一"}], "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "relation"}]}
    assert inventory.inventory(doc, {"B1": 2.0})["share"]["card"] == 1.0


def test_split_line_estimate_follows_from():
    doc = {"lines": [{"text": "前半句後半句後半句"}], "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "relation"},
                                                             {"id": "B1b", "lines": [1], "source": "code", "scene": "relation", "from": "後半句"}]}
    d = inventory.durations(doc, {}, 1.0)
    assert round(d["B1"], 6) == 3.0 and round(d["B1b"], 6) == 6.0


def test_split_line_without_a_findable_cut_is_shared_evenly():
    doc = {"lines": [{"text": "一" * 10}], "beats": [{"id": "B1", "lines": [1], "source": "code", "scene": "relation"},
                                                     {"id": "B1b", "lines": [1], "source": "code", "scene": "relation", "from": "zzz"}]}
    assert inventory.inventory(doc, None, k=0.2)["total"] == 2.0


def test_targets_are_only_flags():
    inv = inventory.inventory(DOC, REAL)
    assert inventory.over_targets(inv, {}) == []
    over = inventory.over_targets(inv, {"photo": [0.2, 0.3], "ve": [0.1, 0.5], "card_max": 0.3})
    assert len(over) == 2 and "photo" in over[0] and "card" in over[1]
