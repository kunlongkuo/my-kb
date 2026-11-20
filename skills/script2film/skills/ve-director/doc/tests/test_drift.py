"""scene-hold-drift: the five scenes that used to hold still push #drift over the beat (1.10; timeline 1.03); drift: false,
a pushing photo and every other scene leave it alone."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

DOC = {"lang": "zh"}
BEAT = {"id": "B1", "duration": 4.0, "tokens": [["甲", 0.2], ["乙", 0.6]]}
PARAMS = {
    "quote_card": {"text": "不要懼怕", "by": "出埃及記 14:13", "at": 0.3},
    "cover": {"title": "出埃及記", "sub": "第 13–21 章", "badge": "第 12 天", "at": 0.15, "sub_at": 0.8},
    "stat_count": {"value": 40, "at": 0.5, "dur": 1.2},
    "compare": {"left": {"title": "先", "text": "背出埃及", "at": 0.3}, "right": {"title": "後", "text": "立約", "at": 1.0}},
    "timeline": {"items": [{"date": "原初", "text": "創 1–11", "at": 0.2}, {"date": "族長", "text": "創 12–50", "at": 0.6}]},
}


def scale_at_end(P, scene, params):
    out, _ = doc_code.build(P, DOC, BEAT, {"scene": scene, "params": params}, "collage")
    return doc_code.page_value(out, "(tl.seek(D), gsap.getProperty('#drift', 'scale'))")


@pytest.fixture
def P(tmp_path):
    (tmp_path / "stills").mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=gray:s=320x180", "-frames:v", "1",
                    str(tmp_path / "stills/a.jpg")], check=True)
    return tmp_path


@pytest.mark.parametrize("scene", PARAMS)
def test_holding_scenes_drift(P, scene):
    assert scale_at_end(P, scene, PARAMS[scene]) == pytest.approx(1.03 if scene == "timeline" else 1.10, abs=1e-3)


def test_drift_value_and_off(P):
    assert scale_at_end(P, "cover", {**PARAMS["cover"], "drift": 1.05}) == pytest.approx(1.05, abs=1e-3)
    assert scale_at_end(P, "timeline", {**PARAMS["timeline"], "drift": 1.05}) == pytest.approx(1.05, abs=1e-3)
    assert scale_at_end(P, "cover", {**PARAMS["cover"], "drift": False}) == 1


def test_a_pushing_photo_skips_drift(P):
    assert scale_at_end(P, "quote_card", {**PARAMS["quote_card"], "photo": {"src": "stills/a.jpg"}}) == 1
    # a photo with its own rect and no push does not move: drift still applies
    assert scale_at_end(P, "quote_card", {**PARAMS["quote_card"], "photo": {"src": "stills/a.jpg", "rect": [90, 150, 780, 439]}}) \
        == pytest.approx(1.10, abs=1e-3)
    assert scale_at_end(P, "stat_count", {**PARAMS["stat_count"], "photos": [{"src": "stills/a.jpg", "rect": [0, 0, 400, 300],
                                                                             "push": 1.05}]}) == 1


def test_other_scenes_do_not_drift(P):
    assert scale_at_end(P, "list_reveal", {"title": "怨言", "items": [{"text": "沒水", "at": 0.3}]}) == 1


def test_drift_keeps_the_side_layout(P):
    """side.beats moves #content left and scales it (doc_code stage_left); drift pushes the wrapper, so both stay."""
    out, _ = doc_code.build(P, {**DOC, "side": {"beats": ["B1"]}}, BEAT, {"scene": "cover", "params": PARAMS["cover"]}, "collage")
    content, scale = doc_code.page_value(out, "(tl.seek(D), [getComputedStyle(document.getElementById('content')).transform,"
                                              " gsap.getProperty('#drift', 'scale')])")
    assert content != "none" and scale == pytest.approx(1.10, abs=1e-3)
