"""pie: parameter checks and what the page draws."""
import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_code import pie_params  # noqa: E402

BEAT = {"id": "B8", "duration": 4.0, "tokens": [["甲", 0.2]]}
DOC = {"lang": "zh"}
ITEMS = [{"label": "房租", "value": 45, "at": 0.4}, {"label": "伙食", "value": 30, "at": 1.0}, {"label": "其他", "value": 25, "at": 2.5}]
GOOD = {"items": ITEMS, "title": "每月支出"}
CX, CY = 640, 490
NUM = r"-?\d+(?:\.\d+)?"
SLICES = "[...document.querySelectorAll('#ink path.slice')].map(p => p.getAttribute('d'))"


def page(tmp_path, params, js, theme="lecture-light"):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "pie", "params": params}, theme)
    return doc_code.page_value(out, js)


def ends(d):
    """(first point, outer arc end) of a sectorPath d."""
    m = re.match(rf"\s*M\s*({NUM})\s+({NUM})\s*A\s*(?:{NUM}\s+){{5}}({NUM})\s+({NUM})", d)
    assert m, d
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x0, y0), (x1, y1)


def angle(pt):
    """0 at 12 o'clock, clockwise, 0-2π."""
    return math.atan2(pt[0] - CX, -(pt[1] - CY)) % (2 * math.pi)


def test_good_params_pass(tmp_path):
    """① good params pass and the page has one slice per item."""
    pie_params(tmp_path, BEAT, GOOD)
    pie_params(tmp_path, BEAT, {**GOOD, "donut": 0, "show": "value", "unit": "元", "hot": 2, "focus": [{"i": 0, "at": 3}]})
    pie_params(tmp_path, BEAT, {**GOOD, "center": {"text": "3 萬", "sub": "每月", "at": 3}})
    assert len(page(tmp_path, {**GOOD, "center": {"text": "3 萬", "at": 3}}, SLICES)) == 3


@pytest.mark.parametrize("change,msg", [
    ({"items": ITEMS[:1]}, "2-6 items"),
    ({"items": ITEMS * 2 + ITEMS[:1]}, "2-6 items"),
    ({"items": [ITEMS[0], {**ITEMS[1], "value": 0}]}, "value"),
    ({"items": [ITEMS[0], {**ITEMS[1], "value": -3}]}, "value"),
    ({"donut": 0.8}, "donut"),
    ({"focus": [{"i": 3, "at": 2}]}, "focus"),
    ({"donut": 0, "center": {"text": "x"}}, "center"),
    ({"items": [ITEMS[0], {"value": 3}]}, "label"),
    ({"show": "share"}, "show"),
    ({"hot": 3}, "hot"),
])
def test_bad_params_stop(tmp_path, change, msg):
    """② each bad parameter stops with a message naming it."""
    with pytest.raises(SystemExit, match=rf"✗ B8: pie .*{msg}"):
        pie_params(tmp_path, BEAT, {**GOOD, **change})


def test_slices_close_the_circle(tmp_path):
    """③ at D the slices' angles (from each path's end points) add up to 2π."""
    ds = page(tmp_path, GOOD, f"(tl.seek(D, false), {SLICES})")
    spans = [(angle(b) - angle(a)) % (2 * math.pi) for a, b in map(ends, ds)]
    assert sum(spans) == pytest.approx(2 * math.pi, abs=0.01)
    assert spans[0] == pytest.approx(2 * math.pi * .45, abs=0.01)


def test_percent_adds_to_100_and_six_colours(tmp_path):
    """④ six equal items: four 17s and two 16s (largest remainder), 100 in all; six slices, no hot: six different fills."""
    six = [{"label": f"項{k}", "value": 1, "at": 0.3 + k * 0.3} for k in range(6)]
    got = page(tmp_path, {"items": six}, """[[...document.querySelectorAll('#content .pval')].map(s => s.textContent),
      [...document.querySelectorAll('#ink path.slice')].map(p => p.getAttribute('fill') + '@' + p.getAttribute('fill-opacity'))]""")
    nums = [int(s.rstrip("%")) for s in got[0]]
    assert sorted(nums) == [16, 16, 17, 17, 17, 17] and sum(nums) == 100
    assert all(s.endswith("%") for s in got[0])
    assert len(got[1]) == 6 and len(set(got[1])) == 6


def test_focus_pulls_one_slice_and_dims_the_rest(tmp_path):
    """⑤ focus on slice 1: it moves out 26 px, the other slices drop to opacity 0.25."""
    got = page(tmp_path, {**GOOD, "focus": [{"i": 1, "at": 3.0}]}, """(() => { tl.seek(D, false);
      return [...document.querySelectorAll('#ink g.sector')].map(g => [gsap.getProperty(g, 'x'), gsap.getProperty(g, 'y'),
        +getComputedStyle(g).opacity]); })()""")
    assert math.hypot(got[1][0], got[1][1]) == pytest.approx(26, abs=0.1)
    assert got[1][2] == pytest.approx(1)
    assert [g[2] for g in (got[0], got[2])] == [pytest.approx(.25), pytest.approx(.25)]
    assert all(math.hypot(g[0], g[1]) == pytest.approx(0, abs=0.1) for g in (got[0], got[2]))


def test_slice_has_no_area_before_its_at(tmp_path):
    """⑥ before slice 2's at (2.5 s) its path starts and ends at the same point; slice 0 is already open."""
    ds = page(tmp_path, GOOD, f"(tl.seek(2.0, false), {SLICES})")
    a, b = ends(ds[2])
    assert a == pytest.approx(b, abs=0.01)
    a0, b0 = ends(ds[0])
    assert math.dist(a0, b0) > 100
