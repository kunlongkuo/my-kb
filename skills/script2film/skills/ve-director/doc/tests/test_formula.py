"""formula: parameter checks and the one-row layout."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_code import formula_params  # noqa: E402

BEAT = {"id": "B9", "duration": 4.0, "tokens": [["甲", 0.2]]}
DOC = {"lang": "zh"}
TWO = {"terms": [{"text": "收入", "at": 0.3}, {"text": "成本", "at": 0.9}], "ops": ["−"]}
FOUR = {"terms": [{"text": t, "at": 0.3 + k * 0.5, "sub": "說明"} for k, t in enumerate(["營業收入", "營業成本", "管理費用", "稅後淨利"])],
        "ops": ["−", "−", "="]}
ROW = """(() => { tl.seek(D);
  const blk = s => [...document.querySelectorAll('#content .blk.' + s)];
  const r = b => [b.offsetLeft, b.offsetTop, b.offsetWidth, parseFloat(getComputedStyle(b).fontSize)];
  return { terms: blk('term').map(r), ops: blk('op').map(r),
           strikes: [...document.querySelectorAll('#content .strike')].map(s => [+s.dataset.i, s.offsetWidth]),
           dims: blk('term').map(b => +getComputedStyle(b.firstChild).opacity) }; })()"""


def page(tmp_path, params, theme="lecture-light"):
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "formula", "params": params}, theme)
    return doc_code.page_value(out, ROW)


def test_good_params_pass(tmp_path):
    """① good params pass and the page has every term and operator."""
    formula_params(tmp_path, BEAT, TWO)
    full = {**FOUR, "focus": [{"i": 3, "at": 3}], "strike": [{"i": 1, "at": 2.8}], "title": "淨利", "note": "示意"}
    formula_params(tmp_path, BEAT, full)
    got = page(tmp_path, full)
    assert len(got["terms"]) == 4 and len(got["ops"]) == 3


@pytest.mark.parametrize("change,msg", [
    ({"terms": TWO["terms"][:1], "ops": []}, "2-5 terms"),
    ({"terms": TWO["terms"][:1], "ops": [], "strike": [{"i": 0, "at": 1}]}, "2-5 terms"),   # one term needs a strike with to
    ({"strike": [{"i": 0, "at": 1, "to": " "}]}, "strike to"),
    ({"strike": [{"i": 0, "at": 1, "to": "一" * 23}]}, "strike to"),
    ({"terms": TWO["terms"] * 3, "ops": ["+"] * 5}, "2-5 terms"),
    ({"ops": ["−", "+"]}, "ops"),
    ({"ops": []}, "ops"),
    ({"ops": ["-"]}, "operator"),
    ({"focus": [{"i": 2, "at": 1}]}, "focus"),
    ({"strike": [{"i": -1, "at": 1}]}, "strike"),
    ({"terms": [{"text": ""}, TWO["terms"][1]]}, "needs text"),
    ({"terms": [{"text": "一二三四五"}] * 5, "ops": ["+"] * 4}, "too long: shorten the terms or split it into two beats"),
])
def test_bad_params_stop(tmp_path, change, msg):
    """② each bad parameter stops with a message naming it."""
    with pytest.raises(SystemExit, match=rf"✗ B9: formula .*{msg}"):
        formula_params(tmp_path, BEAT, {**TWO, **change})


def test_font_size_from_character_count(tmp_path):
    """③ 2 + 2 characters and one operator: 1500 / 5.2 = 288, capped at 190; 4 × 4 characters and three: 1500 / 19.6 → 76."""
    assert {t[3] for t in page(tmp_path, TWO)["terms"]} == {190}
    got = page(tmp_path, FOUR)
    assert {t[3] for t in got["terms"]} == {76} and {o[3] for o in got["ops"]} == {76}


def test_one_row_centred(tmp_path):
    """④ every term's top edge is the same; the margins left and right of the row are equal (±2 px)."""
    got = page(tmp_path, FOUR)
    items = sorted(got["terms"] + got["ops"])
    assert len({t[1] for t in got["terms"] + got["ops"]}) == 1
    left, right = items[0][0], 1920 - (items[-1][0] + items[-1][2])
    assert abs(left - right) <= 2 and left > 0


def test_strike_spans_the_term(tmp_path):
    """⑤ strike on term 1: a line as wide as that term; focus on term 3 dims the others to .25."""
    got = page(tmp_path, {**FOUR, "strike": [{"i": 1, "at": 2.5}], "focus": [{"i": 3, "at": 3.0}]})
    assert got["strikes"] == [[1, got["terms"][1][2]]]
    assert got["dims"] == [pytest.approx(.25)] * 3 + [pytest.approx(1)]


def test_latin_and_digits_do_not_overlap_once_fonts_are_in(tmp_path):
    """Digits and Latin letters change width when the web font loads: the row is laid out with the loaded font (the
    template builds the scene after its fonts), and what hangs on a term (strike) keeps the term's width."""
    params = {"terms": [{"text": "ROE", "at": 0.3}, {"text": "100", "at": 0.9, "hot": True}, {"text": "淨利", "at": 1.5}],
              "ops": ["=", "×"], "strike": [{"i": 1, "at": 2.5}]}
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "formula", "params": params}, "lecture-light")
    got = doc_code.page_value(out, "document.fonts.ready.then(() => new Promise(r => setTimeout(r, 50))).then(() => " + ROW + ")")
    row = sorted(got["terms"] + got["ops"])
    for a, b in zip(row, row[1:]):
        assert a[0] + a[2] <= b[0] + 0.5, (a, b)
    assert abs(row[0][0] - (1920 - row[-1][0] - row[-1][2])) <= 2
    assert abs(dict(map(tuple, got["strikes"]))[1] - got["terms"][1][2]) <= 1


ONE = {"terms": [{"text": "努力", "at": 0.3}], "ops": [], "strike": [{"i": 0, "at": 1.0, "to": "恩典", "to_at": 1.6}]}
REWRITE = """(() => { tl.seek(D);
  const n = document.querySelector('#content .rewrite'), t = document.querySelector('#content .blk.term');
  const nr = n.getBoundingClientRect(), tr = t.getBoundingClientRect();
  return { text: n.textContent, chars: [...n.children].map(c => +getComputedStyle(c).opacity),
           dim: +getComputedStyle(t.firstChild).opacity, above: nr.bottom <= tr.top + 2,
           centre: [(nr.left + nr.right) / 2, (tr.left + tr.right) / 2], size: parseFloat(getComputedStyle(n).fontSize),
           row: parseFloat(getComputedStyle(t).fontSize) }; })()"""


def test_one_term_rewrite(tmp_path):
    """⑥ 「不是 A，而是 B」: one term with a strike that has to passes; at the end the new words stand above the struck term,
    centred on it, every character shown, the term dimmed to .4, the words at 0.8 of the row size."""
    formula_params(tmp_path, BEAT, ONE)
    out, _ = doc_code.build(tmp_path, DOC, BEAT, {"scene": "formula", "params": ONE}, "lecture-light")
    got = doc_code.page_value(out, REWRITE)
    assert got["text"] == "恩典" and got["chars"] == [1, 1] and got["dim"] == pytest.approx(.4) and got["above"]
    assert abs(got["centre"][0] - got["centre"][1]) <= 40   # tilted 3°: the box's centre moves a little
    assert got["size"] == round(got["row"] * .8)
