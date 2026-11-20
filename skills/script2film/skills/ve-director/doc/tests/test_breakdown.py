"""breakdown: parameter checks and the tree's layout."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_code import breakdown_params  # noqa: E402

BEAT = {"id": "B10", "duration": 5.0, "tokens": [["甲", 0.2]]}
DOC = {"lang": "zh"}
ONE = {"root": {"text": "利潤", "value": 30, "at": 0.3},
       "parts": [{"text": "收入", "value": 100, "at": 0.9}, {"text": "成本", "op": "−", "value": 60, "at": 1.5},
                 {"text": "稅", "op": "−", "at": 2.1}],
       "unit": "萬"}
KIDS = [{"text": "人事", "value": 40, "at": 2.6}, {"text": "房租", "op": "+", "value": 20, "at": 3.0}]
TWO = {**ONE, "parts": [ONE["parts"][0], {**ONE["parts"][1], "parts": KIDS}, ONE["parts"][2]]}
NODES = """(() => { tl.seek(D);
  return [...document.querySelectorAll('#content .blk.node')].map(b => ({ id: b.dataset.id, x: b.offsetLeft + b.offsetWidth / 2,
    bottom: b.offsetTop + b.offsetHeight, num: b.querySelector('.num') ? b.querySelector('.num').textContent : null,
    op: +getComputedStyle(b.firstChild).opacity })); })()"""


def page(tmp_path, params, theme="lecture-light"):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "breakdown", "params": params}, theme)
    return {n["id"]: n for n in doc_code.page_value(out, NODES)}


def test_good_params_pass(tmp_path):
    """① one level and two levels pass and build."""
    breakdown_params(tmp_path, BEAT, ONE)
    breakdown_params(tmp_path, BEAT, TWO)
    assert set(page(tmp_path, ONE)) == {"root", "0", "1", "2"}
    assert set(page(tmp_path, TWO)) == {"root", "0", "1", "2", "1.0", "1.1"}


def part(k, **kw):
    return {"text": f"項{k}", **({"op": "+"} if k else {}), **kw}


def kids(m):
    return [{"text": f"子{j}", **({"op": "+"} if j else {})} for j in range(m)]


@pytest.mark.parametrize("change,msg", [
    ({"parts": [part(0)]}, "2-5 parts"),
    ({"parts": [part(k) for k in range(6)]}, "2-5 parts"),
    ({"parts": [part(0), {"text": "乙"}]}, "op"),
    ({"parts": [part(0), part(1, op="=")]}, "op"),
    ({"parts": [part(0), part(1, parts=kids(1))]}, "2-3"),
    ({"parts": [part(0), part(1, parts=kids(4))]}, "2-3"),
    ({"parts": [part(0), part(1, parts=[kids(2)[0], {"text": "子1"}])]}, "op"),
    ({"parts": [part(0, parts=kids(3)), part(1, parts=kids(2)), part(2, parts=kids(2))]}, "at most 6"),
    ({"parts": [part(0), part(1, parts=[kids(2)[0], {**kids(2)[1], "parts": kids(2)}])]}, "third level"),
    ({"parts": [part(k, **({"parts": kids(3)} if k == 2 else {})) for k in range(5)]}, "second level too crowded: use fewer items"),
    ({"focus": [{"id": "1.0", "at": 3}]}, "focus"),
    ({"parts": [part(0, op="+"), part(1)]}, "first: no op"),
    ({"parts": [part(0), {"op": "+"}]}, "needs text"),
    ({"root": {}}, "root needs text"),
])
def test_bad_params_stop(tmp_path, change, msg):
    """② each bad parameter stops with a message naming it."""
    with pytest.raises(SystemExit, match=rf"✗ B10: breakdown .*{msg}"):
        breakdown_params(tmp_path, BEAT, {**ONE, **change})


def test_positions(tmp_path):
    """③ three parts at x 440 / 960 / 1480 (relation's spread); part 1's two children at 845 and 1075 (c = min(230, 520 / 2));
    an item without value prints no number."""
    n = page(tmp_path, TWO)
    s = min(520, 1500 / 2)
    assert [n[k]["x"] for k in "012"] == [pytest.approx(960 + (k - 1) * s, abs=1) for k in range(3)] == [440, 960, 1480]
    c = min(230, s / 2)
    assert [n["1.0"]["x"], n["1.1"]["x"]] == [pytest.approx(960 - c / 2, abs=1), pytest.approx(960 + c / 2, abs=1)]
    assert n["1.0"]["x"] == pytest.approx(845, abs=1) and n["1.1"]["x"] == pytest.approx(1075, abs=1)
    assert n["2"]["num"] is None and n["1"]["num"] == "−60萬" and n["root"]["num"] == "30萬"


def test_cards_stay_above_the_subtitles(tmp_path):
    """④ every card's bottom edge is at y 820 or above (two levels, all with values)."""
    full = {**TWO, "parts": [{**p, "value": 1} for p in TWO["parts"]]}
    n = page(tmp_path, full)
    assert n and max(v["bottom"] for v in n.values()) <= 820


def test_focus_lights_the_path_to_the_root(tmp_path):
    """⑤ focus "1.0": the root, part 1 and its first child stay at 1, everything else drops to .25."""
    n = page(tmp_path, {**TWO, "focus": [{"id": "1.0", "at": 4.0}]})
    lit = {"root", "1", "1.0"}
    assert {k for k, v in n.items() if v["op"] == pytest.approx(1)} == lit
    assert all(v["op"] == pytest.approx(.25) for k, v in n.items() if k not in lit)
