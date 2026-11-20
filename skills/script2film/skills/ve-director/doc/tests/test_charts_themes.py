"""The four chart scenes under every theme: the page builds and runs with no
script error (collected here from playwright's pageerror events: doc_code.page_value does not report them), and in the side
layout (host frame on the right) no text block reaches past the content layer."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402
from doc_themes import CODE_THEMES  # noqa: E402

THEMES = list(CODE_THEMES)   # every theme, the styles.json ones included
BEAT = {"id": "B1", "duration": 5.0, "tokens": [["甲", 0.2]]}
SCENES = {
    "line_chart": {"labels": [f"{m}月" for m in range(1, 13)], "title": "月營收",
                   "series": [{"name": "今年", "values": [3, 4, 6, 5, 8, 9, 7, 10, 12, 11, 13, 15]},
                              {"name": "去年", "values": [2, 3, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9], "color": "accent2"}],
                   "reveal": [{"upto": 5, "at": 0.5}, {"upto": 11, "at": 1.8}], "marks": [{"i": 8, "text": "新品上市", "at": 2.6}],
                   "band": {"from": 2, "to": 4, "label": "淡季"}, "hot": 11, "unit": "億"},
    "pie": {"items": [{"label": "房租", "value": 45, "at": 0.4}, {"label": "伙食", "value": 30, "at": 1.0},
                      {"label": "交通", "value": 15, "at": 1.6}, {"label": "其他", "value": 10, "at": 2.2}],
            "hot": 0, "focus": [{"i": 0, "at": 3.0}, {"i": 1, "at": 3.8}], "center": {"text": "3.2 萬", "sub": "每月", "at": 2.8},
            "title": "每月支出"},
    "formula": {"terms": [{"text": "營收", "sub": "賣出多少", "at": 0.3}, {"text": "成本", "sub": "花掉多少", "at": 1.0},
                          {"text": "利潤", "at": 1.7, "hot": True}],
                "ops": ["−", "="], "focus": [{"i": 2, "at": 3.0}], "strike": [{"i": 1, "at": 3.6}], "title": "公式", "note": "示意"},
    "breakdown": {"root": {"text": "利潤", "value": 30, "at": 0.3}, "unit": "萬", "title": "拆開看",
                  "parts": [{"text": "收入", "value": 100, "at": 0.9},
                            {"text": "成本", "op": "−", "value": 60, "at": 1.5,
                             "parts": [{"text": "人事", "value": 40, "at": 2.0}, {"text": "房租", "op": "+", "value": 20, "at": 2.4}]},
                            {"text": "稅", "op": "−", "value": 10, "at": 2.9}],
                  "focus": [{"id": "1.0", "at": 3.8}]},
}
SEEK = "(() => { for (const t of [0, D / 4, D / 2, 3 * D / 4, D]) tl.seek(t, false); return true; })()"
SIDE = """(() => { tl.seek(D, false); const right = CONTENT.getBoundingClientRect().right;
  return [right, Math.max(...[...document.querySelectorAll('#content .blk')].map(b => b.getBoundingClientRect().right))]; })()"""


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        yield br
        br.close()


def run(browser, out, expr):
    """Open out/index.html, evaluate expr; returns (value, the page's script errors)."""
    pg = browser.new_page(viewport={"width": 1920, "height": 1080})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto((out / "index.html").resolve().as_uri(), wait_until="load")
    pg.evaluate("window.__built && window.__built.catch(() => {})")   # the template builds the scene once its fonts are in
    try:
        v = pg.evaluate(expr)
    finally:
        pg.close()
    return v, errors


def test_theme_list_is_complete():
    assert {"collage", "live"} <= set(THEMES) and len([t for t in THEMES if t.startswith("lecture-")]) >= 5


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("scene", SCENES)
def test_builds_without_page_errors(tmp_path, browser, scene, theme):
    out, _ = doc_code.build(tmp_path, {"lang": "zh"}, BEAT, {"scene": scene, "params": SCENES[scene]}, theme)
    ok, errors = run(browser, out, SEEK)
    assert ok is True and errors == []


@pytest.mark.parametrize("scene", SCENES)
def test_side_layout_stays_inside_the_content_layer(tmp_path, browser, scene):
    doc = {"lang": "zh", "side": {"beats": [BEAT["id"]]}}
    out, _ = doc_code.build(tmp_path, doc, BEAT, {"scene": scene, "params": SCENES[scene]}, "lecture-light")
    (right, widest), errors = run(browser, out, SIDE)
    assert errors == []
    assert right == pytest.approx(1220, abs=2)          # the side layout shrinks the content layer into x 40-1220
    assert widest <= right + 0.5
