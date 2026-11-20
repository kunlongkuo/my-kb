"""line_chart: parameter checks and what the page draws."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_code import line_params  # noqa: E402

BEAT = {"id": "B7", "duration": 4.0, "tokens": [["甲", 0.2]]}
DOC = {"lang": "zh"}
LABELS = ["2019", "2020", "2021", "2022", "2023", "2024"]
VALUES = [10, 14, 9, 20, 26, 22]
GOOD = {"labels": LABELS, "series": [{"name": "營收", "values": VALUES}],
        "reveal": [{"upto": 2, "at": 0.5}, {"upto": 5, "at": 2.0}], "unit": "億"}


def page(tmp_path, params, js, theme="lecture-light"):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "line_chart", "params": params}, theme)
    return doc_code.page_value(out, js)


def test_good_params_pass(tmp_path):
    """① good params pass the check and build a page."""
    line_params(tmp_path, BEAT, GOOD)
    full = {**GOOD, "series": [{"name": "a", "values": VALUES, "color": "accent"}, {"name": "b", "values": VALUES[::-1], "color": "down"}],
            "marks": [{"i": 4, "text": "高點", "at": 2.2}], "band": {"from": 1, "to": 3, "label": "疫情"}, "hot": 4, "title": "營收"}
    line_params(tmp_path, BEAT, full)
    assert page(tmp_path, full, "document.querySelectorAll('#ink path.series').length") == 2


def bad_cases():
    s = GOOD["series"][0]
    return [
        ({"labels": ["a"], "series": [{"values": [1]}]}, "labels"),
        ({"labels": [str(i) for i in range(25)], "series": [{"values": list(range(25))}]}, "labels"),
        ({"series": []}, "series"),
        ({"series": [s, s, s, s]}, "series"),
        ({"series": [{"values": VALUES[:5]}]}, "values"),
        ({"series": [{**s, "color": "pink"}]}, "color"),
        ({"reveal": [{"upto": 3, "at": 0.5}, {"upto": 2, "at": 1}]}, "reveal"),
        ({"reveal": [{"upto": 6, "at": 0.5}]}, "reveal"),
        ({"marks": [{"i": k, "text": "x"} for k in range(5)]}, "marks"),
        ({"band": {"from": 3, "to": 3}}, "band"),
        ({"band": {"from": 4, "to": 2}}, "band"),
        ({"marks": [{"i": 6, "text": "x"}]}, "marks"),
        ({"marks": [{"i": 1, "series": 1, "text": "x"}]}, "marks"),
        ({"hot": 6}, "hot"),
        ({"min": 30, "max": 10}, "min"),
    ]


@pytest.mark.parametrize("change,msg", bad_cases())
def test_bad_params_stop(tmp_path, change, msg):
    """② each bad parameter stops with a message naming it."""
    with pytest.raises(SystemExit, match=rf"✗ B7: line_chart .*{msg}"):
        line_params(tmp_path, BEAT, {**GOOD, **change})


def expected_points(values):
    lo, hi = min(values), max(values)
    lo, hi = lo - (hi - lo) * .08, hi + (hi - lo) * .08
    n = len(values)
    return [(280 + i * 1280 / (n - 1), 770 - (v - lo) / (hi - lo) * 520) for i, v in enumerate(values)]


def test_reveal_draws_to_the_named_point(tmp_path):
    """③ at 1.2 s (first reveal 0.5 + 0.6 done, second not started) the dash offset / total = 1 − len(points 0..2) / total."""
    pts = expected_points(VALUES)
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    want = 1 - sum(seg[:2]) / sum(seg)
    got = page(tmp_path, GOOD, """(() => { tl.seek(1.2); const p = document.querySelector('#ink path.series');
      return parseFloat(getComputedStyle(p).strokeDashoffset) / p.getTotalLength(); })()""")
    assert got == pytest.approx(want, abs=0.01)


def test_line_is_whole_at_the_end(tmp_path):
    """④ at D the dash offset is 0."""
    got = page(tmp_path, GOOD, "(tl.seek(D), parseFloat(getComputedStyle(document.querySelector('#ink path.series')).strokeDashoffset))")
    assert got == pytest.approx(0, abs=0.01)


def test_twelve_labels_show_at_most_eight(tmp_path):
    """⑤ 12 labels: 8 or fewer on screen, the first and the last among them."""
    labels = [f"{m}月" for m in range(1, 13)]
    shown = page(tmp_path, {"labels": labels, "series": [{"values": list(range(12))}]},
                 "[...document.querySelectorAll('#content .blk.xlab')].map(b => b.textContent)")
    assert len(shown) <= 8 and shown[0] == "1月" and shown[-1] == "12月"


def test_each_line_prints_its_last_value_in_its_colour(tmp_path):
    """⑥ two lines: one end value each, coloured like its line."""
    params = {**GOOD, "series": [{"name": "a", "values": VALUES}, {"name": "b", "values": [5, 6, 7, 8, 9, 30]}]}
    got = page(tmp_path, params, """(() => { tl.seek(D);
      const lines = [...document.querySelectorAll('#ink path.series')].map(p => getComputedStyle(p).stroke);
      const tails = [...document.querySelectorAll('#content .blk.tail')].map(b => [b.textContent, getComputedStyle(b.querySelector('.num')).color]);
      return { lines, tails }; })()""")
    assert len(got["tails"]) == 2
    assert [t[0] for t in got["tails"]] == ["22億", "30億"]
    assert [t[1] for t in got["tails"]] == got["lines"] and got["lines"][0] != got["lines"][1]
