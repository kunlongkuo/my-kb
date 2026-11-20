"""timeline window / from / pan_at: a long line shown a few items at a time, sliding from one stretch to the next."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_code import timeline_params  # noqa: E402

ERAS = ["原初", "族長", "出埃及", "士師", "聯合王國", "分裂王國", "被擄", "歸回", "彌賽亞", "教會初期", "末世"]
BEAT = {"id": "B5", "duration": 6.0, "tokens": [["甲", 0.2]]}
DOC = {"lang": "zh"}
LONG = {"items": [{"date": e} for e in ERAS], "window": [4, 7], "from": [0, 3], "pan_at": 1.5, "hot": 5}
# each date box: its centre with the slide (gsap x) applied, and whether it is shown
X4 = [260, 727, 1193, 1660]   # a 4-item stretch: 260 + k × 1400 / 3


def near(xs):   # box centres are whole pixels: within 2 px of X4
    return all(abs(x - w) <= 2 for x, w in zip(xs, X4)) and len(xs) == 4


READ = """(t => { tl.seek(t); return [...document.querySelectorAll('#content .blk')].map(b =>
  [b.textContent, b.offsetLeft + gsap.getProperty(b, 'x') + b.offsetWidth / 2, +getComputedStyle(b).opacity]); })"""


def page(tmp_path, params, t):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "timeline", "params": params}, "collage")
    return {d: (round(x), op) for d, x, op in doc_code.page_value(out, f"{READ}({t})")}


def test_slides_from_one_stretch_to_the_next(tmp_path):
    """before the slide the from-stretch stands at 260 / 727 / 1193 / 1660; after it the window does; eras outside both
    are not drawn."""
    before, after = page(tmp_path, LONG, 1.4), page(tmp_path, LONG, 4.0)
    assert set(before) == set(ERAS[:8])
    assert near([before[e][0] for e in ERAS[:4]]) and all(before[e][1] == 1 for e in ERAS[:4])
    assert near([after[e][0] for e in ERAS[4:8]]) and all(after[e][1] == 1 for e in ERAS[4:8])
    assert all(after[e][0] < 0 for e in ERAS[:4])


def test_window_without_from_stays(tmp_path):
    """a window alone: only its items, standing where a 4-item line stands."""
    got = page(tmp_path, {"items": [{"date": e} for e in ERAS], "window": [7, 10], "hot": 8}, 5.0)
    assert set(got) == set(ERAS[7:]) and near([got[e][0] for e in ERAS[7:]])


def test_good_params_pass():
    timeline_params(None, BEAT, LONG)
    timeline_params(None, BEAT, {"items": [{"date": "1950"}, {"date": "1960"}], "hot": 1})


@pytest.mark.parametrize("params,msg", [
    ({"items": [{"date": e} for e in ERAS[:7]]}, "2-6 items"),
    ({"items": [{"date": e} for e in ERAS + ["新天新地", "x"]], "window": [0, 3]}, "2-6 items"),
    ({**LONG, "window": [4, 11]}, "window must be"),
    ({**LONG, "window": [2, 9]}, "window must be"),
    ({**LONG, "window": [4, 4]}, "window must be"),
    ({**LONG, "from": [0, 2]}, "from must be"),
    ({"items": LONG["items"][:4], "from": [0, 3]}, "from needs a window"),
    ({"items": LONG["items"], "window": [0, 3], "pan_at": 1}, "pan_at needs from"),
    ({**LONG, "hot": 11}, "hot must be"),
    ({"items": [{"date": ""}, {"date": "1960"}]}, "needs a date"),
])
def test_bad_params_stop(params, msg):
    with pytest.raises(SystemExit, match=rf"✗ B5: timeline .*{msg}"):
        timeline_params(None, BEAT, params)
