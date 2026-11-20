"""Text placed by measuring it lands where the scene says, in every scene, with Chinese and English words.

2026-11-17: every box(..., {cx}) title sat right of centre, up to 90 px on English (onion B4 "How to stop the tears"): the
scene measured offsetWidth while the page still drew a fallback font, and the real font came in after (CJK glyphs are 1 em in
both, so Chinese moved 0-4 px). The template now builds a scene only once both font files are loaded; a few scenes also set
a heavier weight after box() measured (list_reveal's title 30 px off), now followed by recentre().
For each scene (all of scenes/*.js, zh and en; a scene with optional centred parts has a second set of params) the page is
built and read once its build is done:
  - the scene was built with every font face loaded (catches a template that builds before its fonts again; it also covers
    the scenes that place text by measuring it without box({cx}): map_route's left labels, screen_step's step labels ...);
  - every box({cx}) / quote(cx) block's centre (offsetLeft + offsetWidth / 2) is within TOL px of cx;
  - every box() call with a cx in a scene's source ran in at least one case (a new centred part needs params here);
  - text a scene lines up by itself: the formula row is centred on 960, a map_route stop's left label ends 30 px left of it.
TOL 1: after the fix the largest miss over all cases is 0.5 px (offsetLeft and offsetWidth are whole pixels); before it the
misses were 1-90 px, Chinese 1-4 px."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

DOC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC_DIR / "scripts"))
import doc_code  # noqa: E402

TOL = 1.0
S7 = {lang: {b["id"]: b.get("params") for b in json.loads((DOC_DIR / f"examples/seventy-times-seven.{lang}.json").read_text())["beats"]}
      for lang in ("zh", "en")}


def s7(lang, beat):   # an example beat with its pictures swapped for the test still
    def swap(x, key=None):
        if isinstance(x, dict):
            return {k: swap(v, k) for k, v in x.items()}
        if isinstance(x, list):
            return [swap(v) for v in x]
        return "stills/a.jpg" if key in ("src", "fg") else x
    return swap(S7[lang][beat])


def flow(lang, look, extra=False):
    zh = lang == "zh"
    names = [("切開洋蔥", "釋出氣體"), ("氣體上升", "含硫化合物"), ("你的眼睛", "角膜神經")] if zh else \
        [("Cut Onion", "Releases gas"), ("Rising Vapor", "Sulfur compound"), ("Your Eyes", "Cornea nerves")]
    nodes = [{"id": f"n{k}", "x": 360 + 600 * k, "y": 460, "label": a, "sub": b, "icon": i, "at": .3 + k * .8}
             for k, ((a, b), i) in enumerate(zip(names, ("container", "target", "shield")))]
    nodes[2]["hot"] = True
    p = {"look": look, "nodes": nodes, "links": [{"from": "n0", "to": "n1", "at": .6}, {"from": "n1", "to": "n2", "at": 1.4}]}
    if extra:   # every optional centred part: a time card, a link label, the shutter's label, the note
        nodes[0]["time"] = "0:00"
        p["links"][1]["label"] = "上升" if zh else "rises"
        p.update(block={"link": 0, "at": 2.5, "label": "擋下" if zh else "Blocked"}, note="示意" if zh else "Sketch")
    return p


def relation(lang):
    zh = lang == "zh"
    n = [("亞伯拉罕", "父親"), ("以撒", "兒子"), ("以實瑪利", "兒子")] if zh else [("Abraham", "Father"), ("Isaac", "Son"), ("Ishmael", "Son")]
    xy = [(960, 300), (600, 620), (1320, 620)]
    return {"nodes": [{"id": f"r{k}", "label": a, "sub": b, "x": x, "y": y, "at": .3 + k * .5, "hot": k == 2}
                      for k, ((a, b), (x, y)) in enumerate(zip(n, xy))],
            "links": [{"from": "r0", "to": "r1", "label": "應許" if zh else "promise", "at": 1.8},
                      {"from": "r0", "to": "r2", "label": "長子" if zh else "firstborn", "at": 2.2}]}


def W(zh, en):
    return lambda lang: zh if lang == "zh" else en


T = {   # scene → lang → params, or a list of params when one set cannot reach every centred part
    "bars": lambda L: {"items": [{"label": a, "value": v, "at": t} for a, v, t in
                                 zip(W(["甲", "乙", "丙"], ["Alpha", "Beta", "Gamma"])(L), (42, 67, 25), (.4, 1, 1.6))],
                       "unit": "%", "title": W("三家比一比（示意）", "Three shops side by side")(L)},
    "breakdown": lambda L: {"root": {"text": W("利潤", "Profit")(L), "value": 30, "at": .3}, "unit": W("萬", "k")(L),
                            "title": W("拆開看", "Where it goes")(L),
                            "parts": [{"text": W("收入", "Revenue")(L), "value": 100, "at": .9},
                                      {"text": W("成本", "Costs")(L), "op": "−", "value": 60, "at": 1.5,
                                       "parts": [{"text": W("人事", "Staff")(L), "value": 40, "at": 2},
                                                 {"text": W("房租", "Rent")(L), "op": "+", "value": 20, "at": 2.4}]},
                                      {"text": W("稅", "Tax")(L), "op": "−", "value": 10, "at": 2.9}]},
    "burst_title": lambda L: s7(L, "B6"),
    "compare": lambda L: [{"left": {"title": W("在眼睛上", "On the eye")(L), "text": W("氣體碰到角膜上的水", "Gas meets moisture on the cornea")(L), "at": .3},
                          "right": {"title": W("觸發", "The trigger")(L), "text": W("弱酸刺激神經", "Mild acid stings the nerves")(L), "at": 1},
                          "verdict": {"side": "right", "text": W("淚腺把它沖掉", "Tear glands flush it out")(L), "at": 2}},
                         {"left": {"title": W("發行公司｜凍結", "Issuer: freeze")(L), "items": [{"text": W("開始凍結", "Freezing starts")(L), "at": .5},
                                   {"text": W("約 8.2 億", "About 820 million")(L), "at": 1.2, "hot": True}]},
                          "right": {"title": W("攻擊者｜換幣", "Attacker: swap")(L), "items": [{"text": W("穩定幣換成以太幣", "Stablecoins to ETH")(L), "at": .9}]}}],
    "countdown": lambda L: {"value": 204, "label": W("授權生效（分:秒）", "Time to drain (min:s)")(L), "at": .3, "dur": 3,
                            "caption": W("錢包被掃空", "Wallet emptied")(L)},
    "cover": lambda L: {"series": W("編年讀經", "Through the Bible")(L), "title": W("出埃及記", "Exodus")(L),
                        "sub": W("第 13–21 章", "Chapters 13-21")(L), "badge": W("第 12 天", "Day 12")(L), "at": .15, "sub_at": .8},
    "credits": lambda L: {"title": W("資料來源", "Sources")(L), "groups": [{"head": W("照片", "Photos")(L), "lines": ["Wikimedia Commons CC BY-SA", "Pexels"]}]},
    "exchange": lambda L: s7(L, "B7"),
    "flow": lambda L: [flow(L, "pipe"), flow(L, "lanes", extra=True)],
    "formula": lambda L: {"title": W("切開的洋蔥", "Inside a sliced onion")(L), "ops": ["+", "+"], "focus": [{"i": 1, "at": 3}],
                          "terms": [{"text": W("細胞壁", "Cell Wall")(L), "sub": W("被刀切破", "Broken by knife")(L), "at": .3},
                                    {"text": W("酵素", "Enzyme")(L), "sub": W("蒜胺酸酶", "Alliinase")(L), "at": 1},
                                    {"text": W("硫", "Sulfur")(L), "sub": W("胺基酸", "Amino acids")(L), "at": 1.7}]},
    "grid_hot": lambda L: {"count": 50, "title": W("一筆交易，50 張授權", "One trade, fifty approvals")(L), "at": .3, "hot": 17,
                           "hot_at": 2.5, "caption": W("生效的是第 17 張", "Number 17 fired")(L)},
    "line_chart": lambda L: {"title": W("示意：每月銷售", "Sample: monthly sales")(L), "labels": W(["3月", "4月", "5月", "6月", "7月", "8月"],
                             ["Mar", "Apr", "May", "Jun", "Jul", "Aug"])(L), "series": [{"name": W("銷售", "Sales")(L), "values": [20, 21, 20, 28, 35, 42]}],
                             "unit": "k", "reveal": [{"upto": 2, "at": .5}, {"upto": 5, "at": 1.5}],
                             "band": {"from": 1, "to": 3, "label": W("淡季", "Slow season")(L)}, "marks": [{"i": 4, "text": W("新品上市", "New blend")(L), "at": 2}]},
    "list_reveal": lambda L: {"title": W("怎樣不流淚", "How to stop the tears")(L), "big": True, "hot": 2,
                              "items": [{"text": t, "at": .5 + k} for k, t in enumerate(W(["先冰洋蔥", "用利刀", "在風扇旁切"],
                                        ["Chill the onion first", "Use a sharp knife", "Cut near a fan"])(L))]},
    "map_route": lambda L: {"land": ["M 200 300 Q 700 200 1200 350 T 1700 300"], "hot": 2, "title": W("出埃及路線", "The Exodus route")(L),
                            "note": W("路線示意（傳統說法）", "Route sketch (traditional)")(L),
                            "stops": [{"name": n, "x": x, "y": y, "at": t, "side": side} for n, x, y, t, side in
                                      zip(W(["蘭塞", "疏割", "西乃山"], ["Rameses", "Succoth", "Mount Sinai"])(L), (500, 900, 1300), (500, 420, 600),
                                          (.3, .9, 1.5), ("right", "left", "right"))]},
    "merge_bubble": lambda L: {"a": {"name": W("大公司", "Microsoft")(L), "sub": W("買方", "Buyer")(L)}, "b": {"name": W("小公司", "Activision")(L), "sub": W("遊戲", "Games")(L)},
                               "a_at": .3, "b_at": 1, "merge_at": 2, "value": {"text": W("690 億美元", "$69 billion")(L), "at": 3}},
    "object_draw": lambda L: s7(L, "B15"),
    "photo": lambda L: s7(L, "B5"),
    "pie": lambda L: {"title": W("每月支出", "Monthly spending")(L), "hot": 0, "center": {"text": W("3.2 萬", "$3.2k")(L), "sub": W("每月", "a month")(L), "at": 2.8},
                      "items": [{"label": a, "value": v, "at": t} for a, v, t in
                                zip(W(["房租", "伙食", "交通"], ["Rent", "Food", "Transport"])(L), (45, 35, 20), (.4, 1, 1.6))]},
    "quote_card": lambda L: {"text": W("不要懼怕，只管站住", "Do not be afraid. Stand firm")(L), "by": W("出埃及記 14:13", "Exodus 14:13")(L), "at": .3},
    "relation": relation,
    "screen_step": lambda L: {"src": "stills/screen.png", "frame": "browser", "url_text": "example.com",
                              "steps": [{"n": 1, "label": W("按這裡登入", "Click sign in")(L), "at": .5, "box": [800, 400, 300, 80]}]},
    "seed_dot": lambda L: s7(L, "B1"),
    "split_duel": lambda L: s7(L, "B4"),
    "stat_count": lambda L: {"value": 88, "suffix": "%", "caption": W("一個數字（示意）", "One number that matters")(L), "at": .4, "dur": 1.2},
    "timeline": lambda L: [{"hot": 1, "items": [{"date": d, "text": t, "at": .2 + k * .4} for k, (d, t) in enumerate(
        W([("原初", "創 1–11"), ("族長", "創 12–50"), ("出埃及", "出 1–40")], [("1950", "First shop opens"), ("1971", "Seattle store"), ("2008", "Global crash")])(L))]},
        {"hot": 4, "window": [2, 5], "items": [{"date": d, "text": t} for d, t in   # a long line shown a stretch at a time
         W([("原初", ""), ("族長", ""), ("出埃及", "出 1–40"), ("士師", "士 1–21"), ("聯合王國", "撒上–王上 11"), ("分裂王國", "王上 12–")],
           [("1900", ""), ("1930", ""), ("1950", "First shop"), ("1971", "Seattle"), ("1987", "Bought out"), ("2008", "Crash")])(L)]}],
    "ve_annotate": lambda L: {"src": "stills/clip.mp4", "freeze": 1.0, "hold": 1.5, "rings": [{"x": 960, "y": 500, "r": 80}],
                              "note": {"text": W("注意這裡", "Look here")(L), "x": 1200, "y": 300}},
    "web_evidence": lambda L: {"src": "stills/screen.png", "source": W("官方網站｜2026-11-01", "Official site, 2026-11-01")(L),
                               "marks": [{"box": [100, 100, 400, 60], "at": .8}]},
}
THEME = {"exchange": "collage", "seed_dot": "collage", "split_duel": "collage", "burst_title": "collage", "object_draw": "collage",
         "photo": "collage", "map_route": "collage"}
PARAMS = {(s, lang, k): p for s in sorted(T) for lang in ("zh", "en")
          for k, p in enumerate(T[s](lang) if isinstance(T[s](lang), list) else [T[s](lang)])}
CASES = list(PARAMS)
# box() and quote() keep a list of what they centred, with the cx they were given; the scene records whether the fonts were in
HOOK = """window.__cxs = []; window.__fontsAtBuild = null;
{ const line = () => +new Error().stack.split("\\n")[3].match(/:(\\d+):\\d+\\)?$/)[1];   // the line that called box() / quote()
  const _b = box; box = function (h, o = {}) { const b = _b(h, o); if (o && o.cx != null) window.__cxs.push([b, o.cx, line()]); return b; };
  const _q = quote; quote = function (t, cx, top) { const q = _q(t, cx, top); window.__cxs.push([q, cx, line()]); return q; };
  const _s = SCENES[__S__]; SCENES[__S__] = p => { window.__fontsAtBuild = [...document.fonts].map(f => f.family + " " + f.status); return _s(p); }; }
"""
TL = "const tl = gsap.timeline({ paused: true });\n"
READ = """async () => { await window.__built; tl.seek(D, false);
  const box = e => [e.offsetLeft, e.offsetLeft + e.offsetWidth];
  return { fonts: window.__fontsAtBuild, cx: window.__cxs.map(([b, cx, ln]) => [b.textContent.trim().slice(0, 30), cx,
           b.offsetLeft + b.offsetWidth / 2 - cx, ln]),
           row: [...document.querySelectorAll('.term, .op')].map(box),
           cards: [...document.querySelectorAll('.blk.card')].map(e => [e.textContent.trim(), ...box(e)]) }; }"""


def test_every_scene_is_covered():
    assert set(T) == {f.stem for f in (DOC_DIR / "scenes").glob("*.js")}


def cx_sites(src):
    """Line numbers (1-based, in src) of the box() calls whose options carry a cx."""
    out, i = [], src.find("box(")
    while i >= 0:
        depth, j = 0, i + 3
        for j in range(i + 3, len(src)):
            depth += {"(": 1, ")": -1}.get(src[j], 0)
            if depth == 0:
                break
        if re.search(r"[{,]\s*cx\s*[:,}]", src[i:j]):
            out.append(src.count("\n", 0, i) + 1)
        i = src.find("box(", j)
    return out


@pytest.fixture(scope="module")
def pages(tmp_path_factory):
    """Every case built first (screen_step's build opens its own browser), then read in one browser."""
    P = tmp_path_factory.mktemp("centring")
    (P / "stills").mkdir()
    for args in (["-f", "lavfi", "-i", "color=gray:s=1280x720", "-frames:v", "1", "stills/a.jpg"],
                 ["-f", "lavfi", "-i", "color=white:s=1920x1080", "-frames:v", "1", "stills/screen.png"],
                 ["-f", "lavfi", "-i", "testsrc=s=1920x1080:d=6:r=30", "-pix_fmt", "yuv420p", "stills/clip.mp4"]):
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args], cwd=P, check=True)
    outs, starts = {}, {}
    for k, case in enumerate(CASES):
        scene, lang, _ = case
        out, _ = doc_code.build(P, {"lang": lang}, {"id": f"B{k}", "duration": 5.0, "tokens": []},
                                {"scene": scene, "params": PARAMS[case]}, THEME.get(scene, "lecture-light"))
        html = (out / "index.html").read_text(encoding="utf-8")
        assert TL in html
        html = html.replace(TL, HOOK.replace("__S__", json.dumps(scene)) + TL, 1)
        (out / "index.html").write_text(html, encoding="utf-8")
        src = (DOC_DIR / "scenes" / f"{scene}.js").read_text(encoding="utf-8")
        starts[case] = html[:html.index(src)].count("\n")   # page line = start + line in the scene file
        outs[case] = out
    from playwright.sync_api import sync_playwright
    got = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        for key, out in outs.items():
            pg.goto((out / "index.html").resolve().as_uri(), wait_until="load")
            got[key] = pg.evaluate(READ)
            got[key]["lines"] = {ln - starts[key] for *_, ln in got[key]["cx"]}
        br.close()
    return got


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c[0]}-{c[1]}-{c[2]}")
def test_built_after_fonts(pages, case):
    fonts = pages[case]["fonts"]
    assert fonts and all(f.endswith(" loaded") for f in fonts), fonts


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c[0]}-{c[1]}-{c[2]}")
def test_centred_text_is_on_cx(pages, case):
    off = [(text, cx, round(d, 1)) for text, cx, d, _ in pages[case]["cx"] if abs(d) > TOL]
    assert not off, off


@pytest.mark.parametrize("scene", sorted(T))
def test_every_centred_part_ran(pages, scene):
    want = set(cx_sites((DOC_DIR / "scenes" / f"{scene}.js").read_text(encoding="utf-8")))
    ran = set().union(*(pages[c]["lines"] for c in CASES if c[0] == scene))
    assert want <= ran, f"box({{cx}}) on scenes/{scene}.js lines {sorted(want - ran)} never ran: add params that reach them"


def test_a_quote_is_centred(pages):   # quote(cx) lives in lib.js: the photo cases carry one
    assert any(t.startswith(("「", "“")) for c in CASES if c[0] == "photo" for t, *_ in pages[c]["cx"])


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_formula_row_is_centred(pages, lang):
    row = pages[("formula", lang, 0)]["row"]
    assert len(row) == 5 and abs((min(l for l, _ in row) + max(r for _, r in row)) / 2 - 960) <= TOL, row


@pytest.mark.parametrize("lang", ["zh", "en"])
def test_map_route_left_label_ends_by_its_stop(pages, lang):
    stop = next(s for s in PARAMS[("map_route", lang, 0)]["stops"] if s.get("side") == "left")
    right = next(r for t, _, r in pages[("map_route", lang, 0)]["cards"] if t == stop["name"])
    assert abs(right - (stop["x"] - 30)) <= TOL, (right, stop)
