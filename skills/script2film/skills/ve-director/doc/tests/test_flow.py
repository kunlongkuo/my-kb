"""doc_code.flow_params: the flow scene's nodes, links and shutter must hang together before anything renders."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_code import flow_params  # noqa: E402

BEAT = {"id": "B30"}
GOOD = {"look": "pipe", "nodes": [{"id": "a", "x": 300, "y": 470, "icon": "laptop"}, {"id": "b", "x": 900, "y": 470, "icon": "stamp"}],
        "links": [{"from": "a", "to": "b", "at": "x"}]}


def test_good_params_pass(tmp_path):
    flow_params(tmp_path, BEAT, GOOD)
    flow_params(tmp_path, BEAT, {**GOOD, "look": "lanes", "block": {"link": 0, "at": "x"}})


def test_picture_node_must_exist(tmp_path):
    (tmp_path / "stills").mkdir()
    (tmp_path / "stills/a.jpg").write_bytes(b"x")
    nodes = [{"id": "a", "x": 300, "y": 470, "src": "stills/a.jpg"}, GOOD["nodes"][1]]
    flow_params(tmp_path, BEAT, {**GOOD, "nodes": nodes})
    with pytest.raises(SystemExit, match="src not found"):
        flow_params(tmp_path, BEAT, {**GOOD, "nodes": [{**nodes[0], "src": "stills/none.jpg"}, nodes[1]]})


@pytest.mark.parametrize("change,msg", [
    ({"look": "maze"}, "look must be"),
    ({"nodes": GOOD["nodes"][:1]}, "at least 2 nodes"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "id": "a"}]}, "unique"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "y": 950}]}, "y 80-860"),
    ({"nodes": [GOOD["nodes"][0], {**GOOD["nodes"][1], "icon": "rocket"}]}, "icon must be"),
    ({"links": []}, "at least 1 link"),
    ({"links": [{"from": "a", "to": "z"}]}, "join two different nodes"),
    ({"links": [{"from": "a", "to": "a"}]}, "join two different nodes"),
    ({"block": {"link": 3}}, "block.link"),
])
def test_bad_params_stop(tmp_path, change, msg):
    with pytest.raises(SystemExit, match=msg):
        flow_params(tmp_path, BEAT, {**GOOD, **change})


# Text on the page around the dark looks' tiles follows the page (2026-11-17 trial: pipe on lecture-food left white labels on
# a cream ground). Contrast is the WCAG 2 ratio; 3:1 is its floor for large text (these labels are 42 px bold).
import doc_code  # noqa: E402

PIPE = {"look": "pipe", "nodes": [{"id": "a", "x": 360, "y": 460, "label": "Cut Onion", "sub": "Releases gas", "icon": "container", "time": "0 s"},
                                  {"id": "b", "x": 960, "y": 460, "label": "Your Eyes", "icon": "shield", "hot": True, "time": "2 s"}],
        "links": [{"from": "a", "to": "b", "at": 1.0}], "note": "made-up"}
TEXT = """document.fonts.ready.then(() => [...document.querySelectorAll('.blk')].map(b => getComputedStyle(b).color))"""


def _lum(rgb):
    c = [v / 255 for v in rgb]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def _ratio(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + .05) / (y + .05)


def _colors(tmp_path, theme, params=PIPE):
    o, _ = doc_code.build(tmp_path, {"lang": "en"}, {"id": "B1", "duration": 4.0, "tokens": [["a", 0.1]]},
                          {"scene": "flow", "params": params}, theme)
    return [tuple(int(v) for v in c[c.index("(") + 1:-1].split(",")[:3]) for c in doc_code.page_value(o, TEXT)]


from doc_themes import CODE_THEMES  # noqa: E402

LIGHT = [t for t, th in CODE_THEMES.items() if th["light"]]
# streams: two sources pour into a sink that has the label under it, one ribbon carries a counter
STREAMS = {"look": "streams", "nodes": [{"id": "a", "x": 360, "y": 300, "label": "Cut Onion", "icon": "container"},
                                        {"id": "b", "x": 360, "y": 620, "label": "Vapor", "icon": "target"},
                                        {"id": "s", "x": 1500, "y": 460, "label": "Your Eyes", "sub": "Cornea", "icon": "shield", "sink": True,
                                         "hot": True}],
           "links": [{"from": "a", "to": "s", "at": 0.8, "count": {"value": 40, "suffix": "%"}}, {"from": "b", "to": "s", "at": 1.4}],
           "note": "made-up"}


def _bg(theme):
    v = dict(re.findall(r"--([\w-]+):\s*([^;]+);", CODE_THEMES[theme]["vars"]))
    h = (v.get("bg-solid") or v["bg"]).strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


@pytest.mark.parametrize("theme", LIGHT)
@pytest.mark.parametrize("params", [PIPE, STREAMS], ids=["pipe", "streams"])
def test_dark_look_text_reads_on_a_light_palette(tmp_path, theme, params):
    assert "lecture-food" in LIGHT and "collage" in LIGHT
    cols = _colors(tmp_path, theme, params)
    assert len(cols) >= 3                                     # labels, time cards or the counter, the note
    assert min(_ratio(c, _bg(theme)) for c in cols) >= 3, cols


def test_dark_look_text_unchanged_on_a_dark_palette(tmp_path):
    cols = _colors(tmp_path, "lecture-dark")
    assert (255, 255, 255) in cols                            # the plain label stays white on the dark page
