"""map-route-basemap: map_route on an old (or modern) base map — stops in map pixels follow the crop, the picture pushes in
on the hot stop, a modern map says so; doc_build.map_route() fills the stops from the series map library; doc_lint map_base."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_build  # noqa: E402
import doc_code  # noqa: E402
import doc_lint  # noqa: E402

DOC = {"lang": "zh"}
BEAT = {"id": "B1", "duration": 4.0, "tokens": [["甲", 0.2], ["乙", 0.6]]}
STOPS = [{"name": "甲地", "x": 300, "y": 400, "at": 0.2}, {"name": "乙地", "x": 550, "y": 453, "at": 0.6}]


@pytest.fixture
def P(tmp_path):
    (tmp_path / "refs/maps").mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=gray:s=1200x900", "-frames:v", "1",
                    str(tmp_path / "refs/maps/m.jpg")], check=True)
    return tmp_path


def base(**k):
    return {"src": "refs/maps/m.jpg", "size": [1200, 900], "crop": [100, 200, 900, 506], "kind": "old", **k}


def page(P, params, js):
    out, _ = doc_code.build(P, DOC, BEAT, {"scene": "map_route", "params": params}, "collage")
    return doc_code.page_value(out, js)


CARDS = "[...document.querySelectorAll('#content .blk')].map(b => [b.textContent, parseFloat(b.style.left), parseFloat(b.style.top)])"


def test_stops_follow_the_crop(P):
    """crop [100, 200, 900, 506] fills the frame (scale 1920/900): map pixel (550, 453) lands on the frame centre."""
    cards = page(P, {"stops": STOPS, "hot": 1, "base": base()}, CARDS)
    name, left, top = [c for c in cards if c[0] == "乙地"][0]
    assert left == pytest.approx(960 + 30, abs=1) and top == pytest.approx(540 - 36, abs=1)


def test_a_tall_crop_is_centred(P):
    """a crop taller than 16:9 fits the height and sits in the middle, paper either side."""
    cards = page(P, {"stops": STOPS, "hot": 1, "base": base(crop=[100, 100, 600, 800])}, CARDS)
    s = 1080 / 800
    _, left, top = [c for c in cards if c[0] == "甲地"][0]
    assert left == pytest.approx((1920 - 600 * s) / 2 + (300 - 100) * s + 30, abs=1)
    assert top == pytest.approx((400 - 100) * s - 36, abs=1)


def test_without_base_nothing_changes(P):
    """no base: stops are frame pixels, no map image, nothing pushes (the scene before this change)."""
    cards = page(P, {"stops": STOPS, "hot": 1}, CARDS)
    assert [c for c in cards if c[0] == "甲地"][0][1:] == [330, 364]
    img, scale = page(P, {"stops": STOPS, "hot": 1}, "(tl.seek(D), [document.querySelectorAll('#ink image').length,"
                                                       " gsap.getProperty('#drift', 'scale')])")
    assert img == 0 and scale == 1


def test_base_sits_under_the_route_and_pushes_on_the_hot_stop(P):
    first, scale, origin = page(P, {"stops": STOPS, "hot": 1, "base": base()},
                                "(tl.seek(D), [[...document.getElementById('ink').children].find(e => e.tagName !== 'defs')"
                                ".querySelector('image') !== null, gsap.getProperty('#drift', 'scale'),"
                                " getComputedStyle(document.getElementById('drift')).transformOrigin])")
    assert first and scale == pytest.approx(1.04, abs=1e-3) and origin == "960px 540px"
    assert page(P, {"stops": STOPS, "hot": 1, "base": base(push=1.0)},
                "(tl.seek(D), gsap.getProperty('#drift', 'scale'))") == 1


def test_a_modern_map_says_it_is_today(P):
    cards = page(P, {"stops": STOPS, "note": "路線示意", "base": base(kind="modern")}, CARDS)
    assert any(c[0] == "路線示意｜今日位置示意" for c in cards)
    cards = page(P, {"stops": STOPS, "note": "路線示意", "base": base()}, CARDS)
    assert any(c[0] == "路線示意" for c in cards)


@pytest.fixture
def lib(tmp_path):
    d = tmp_path / "series/maps"; d.mkdir(parents=True)
    (d / "m.jpg").write_bytes(b"jpg")
    (d / "maps.json").write_text(json.dumps({"m": {"src": "m.jpg", "size": [1200, 900], "kind": "old", "credit": "底圖：測試",
                                                   "crops": {"中部": [100, 200, 900, 506]}, "places": {"耶利哥": [550, 453]}}}))
    ep = tmp_path / "series/026_x"; ep.mkdir()
    return ep


def test_doc_build_takes_places_and_copies_the_map(lib):
    p = doc_build.map_route("m", "中部", [{"place": "耶利哥", "at": 0.2}, {"name": "別處", "x": 300, "y": 400, "at": 0.5}],
                            project=lib, title="約書亞記", hot=0)
    assert p["stops"][0] == {"name": "耶利哥", "x": 550, "y": 453, "at": 0.2}
    assert p["base"] == {"src": "refs/maps/m.jpg", "size": [1200, 900], "crop": [100, 200, 900, 506], "kind": "old",
                         "credit": "底圖：測試"}
    assert (lib / "refs/maps/m.jpg").read_bytes() == b"jpg" and p["title"] == "約書亞記"


def test_doc_build_refuses_a_map_path(lib):
    p = lib.parent / "maps/maps.json"; m = json.loads(p.read_text()); m["m"]["src"] = "../m.jpg"; p.write_text(json.dumps(m))
    with pytest.raises(SystemExit) as e:
        doc_build.map_route("m", "中部", [], project=lib)
    assert "without a path" in str(e.value)


def test_push_and_dim_are_clamped(P):
    assert page(P, {"stops": STOPS, "hot": 1, "base": base(push=3)}, "(tl.seek(D), gsap.getProperty('#drift', 'scale'))") \
        == pytest.approx(1.2, abs=1e-3)
    assert page(P, {"stops": STOPS, "hot": 1, "base": base(push=0.5)}, "(tl.seek(D), gsap.getProperty('#drift', 'scale'))") == 1
    op = page(P, {"stops": STOPS, "base": base(dim=5)}, "[...document.querySelectorAll('#ink rect')].map(r => +r.getAttribute('opacity')).filter(Boolean)")
    assert max(op) == pytest.approx(.6)


@pytest.mark.parametrize("bad", [{"key": "x"}, {"crop": "南部"}, {"place": "艾城"}])
def test_doc_build_stops_on_unknown_names(lib, bad):
    with pytest.raises(SystemExit) as e:
        doc_build.map_route(bad.get("key", "m"), bad.get("crop", "中部"), [{"place": bad.get("place", "耶利哥"), "at": 0}],
                            project=lib)
    assert next(v for v in bad.values()) in str(e.value)


def lint_doc(stops, crop=(100, 200, 900, 506), side=False):
    b = {"id": "B1", "lines": [1], "source": "code", "scene": "map_route",
         "params": {"stops": stops, "base": {"src": "refs/maps/m.jpg", "size": [1200, 900], "crop": list(crop), "kind": "old"}}}
    return {"lines": [{"text": "甲"}], "beats": [b], **({"side": {"beats": ["B1"]}} if side else {})}


def test_lint_map_base(capsys):
    ok = [{"name": "乙地", "x": 550, "y": 453}]
    assert doc_lint.map_base(lint_doc(ok)) == []
    assert "is outside the crop" in doc_lint.map_base(lint_doc([{"name": "外", "x": 50, "y": 453}]))[0]
    assert "150–820" in doc_lint.map_base(lint_doc([{"name": "低", "x": 550, "y": 680}]))[0]     # frame y ≈ 1024
    assert "side layout" in doc_lint.map_base(lint_doc(ok, side=True))[0]
    assert doc_lint.map_base(lint_doc(ok, crop=(100, 200, 800, 450))) == [] and "will blur" in capsys.readouterr().out
    assert doc_lint.map_base(lint_doc(ok)) == [] and "will blur" not in capsys.readouterr().out
