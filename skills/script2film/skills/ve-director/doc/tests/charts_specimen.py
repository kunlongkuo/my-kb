"""Specimen sheets for the four chart scenes and the lecture palettes.

  python3 tests/charts_specimen.py --out <folder>     (fonts from the asset layers, doc_common.asset)
      charts.jpg    8 rows (lecture palettes) x 6 columns (line_chart, pie, formula, breakdown, bars, stat_count), last frame
      palettes.jpg  the three sampled palettes next to the picture each was sampled from
The numbers are made up for the sheet (示意), not facts.
"""
import argparse, io, json, sys, tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
sys.path.insert(0, str(DOC / "tests"))
import doc_code  # noqa: E402
import doc_common  # noqa: E402
from lecture_palette_check import PALETTES, find_source  # noqa: E402

W, H = 480, 270
BEAT = {"duration": 5.0, "tokens": [["甲", 0.2]]}
SCENES = [
    ("line_chart", {"labels": [str(y) for y in range(2017, 2025)], "unit": "億", "title": "營收走勢（示意）",
                    "series": [{"name": "甲公司", "values": [12, 15, 14, 21, 19, 27, 33, 31]},
                               {"name": "乙公司", "values": [10, 11, 13, 12, 16, 18, 17, 22]}],
                    "marks": [{"i": 6, "series": 0, "text": "高點", "at": 2.5}], "band": {"from": 3, "to": 4, "label": "疫情"}}),
    ("pie", {"items": [{"label": "房租", "value": 38, "at": .4}, {"label": "伙食", "value": 27, "at": .9},
                       {"label": "交通", "value": 14, "at": 1.4}, {"label": "娛樂", "value": 12, "at": 1.9},
                       {"label": "其他", "value": 9, "at": 2.4}],
             "title": "每月支出（示意）", "center": {"text": "3.2 萬", "sub": "月支出", "at": 2.6}, "focus": [{"i": 0, "at": 3.2}]}),
    ("formula", {"terms": [{"text": "利潤", "at": .3}, {"text": "收入", "sub": "賣了多少", "at": .9},
                           {"text": "成本", "sub": "花了多少", "at": 1.5}], "ops": ["=", "−"], "focus": [{"i": 2, "at": 3.0}],
                 "title": "一條式子"}),
    ("breakdown", {"root": {"text": "利潤", "value": 30, "at": .3}, "unit": "萬", "title": "拆開來看（示意）",
                   "parts": [{"text": "收入", "value": 100, "at": .9},
                             {"text": "成本", "op": "−", "value": 60, "at": 1.5,
                              "parts": [{"text": "人事", "value": 40, "at": 2.2}, {"text": "房租", "op": "+", "value": 20, "at": 2.6}]},
                             {"text": "稅", "op": "−", "value": 10, "at": 3.0}],
                   "focus": [{"id": "1.0", "at": 3.6}]}),
    ("bars", {"items": [{"label": "甲", "value": 42, "at": .4}, {"label": "乙", "value": 67, "at": 1.0, "dir": "up"},
                        {"label": "丙", "value": 25, "at": 1.6, "dir": "down"}], "unit": "%", "title": "三家比一比（示意）"}),
    ("stat_count", {"value": 88, "suffix": "%", "caption": "一個數字（示意）", "at": .4, "dur": 1.2}),
]


def font(size):
    return ImageFont.truetype(str(doc_common.asset("fonts", "NotoSansTC-Variable.ttf")), size)


def shot(pg, url, js=""):
    pg.goto(url, wait_until="load")
    pg.evaluate("window.__built && window.__built.catch(() => {})")   # the template builds the scene once its fonts are in
    pg.evaluate("document.fonts.ready.then(() => new Promise(r => setTimeout(r, 80)))")
    if js:
        pg.evaluate(js)
    return Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")


def charts(out, tmp, pg):
    sheet = Image.new("RGB", (W * len(SCENES), H * len(PALETTES)), "#000")
    for r, mode in enumerate(PALETTES):
        for c, (scene, params) in enumerate(SCENES):
            o, _ = doc_code.build(tmp, {"lang": "zh"}, {**BEAT, "id": f"S{c}"}, {"scene": scene, "params": params}, f"lecture-{mode}")
            im = shot(pg, (o / "index.html").resolve().as_uri(), f"void tl.seek({BEAT['duration']}, false)")
            sheet.paste(im.resize((W, H), Image.LANCZOS), (c * W, r * H))
        ImageDraw.Draw(sheet).text((8, r * H + 6), f"lecture-{mode}", font=font(15), fill="#ff2d6f")
    sheet.save(out / "charts.jpg", quality=92)
    return sheet.size


def palettes(out, pg):
    t = json.loads((DOC / "themes/lecture.json").read_text(encoding="utf-8"))
    rows = [m for m in PALETTES if "_from" in t[m]]
    RH, SW = 360, 640
    sheet = Image.new("RGB", (SW + 9 * 130 + 40, RH * len(rows)), "#ffffff")
    d = ImageDraw.Draw(sheet)
    for r, mode in enumerate(rows):
        state, where = find_source(t[mode]["_from"])
        if state == "ok":
            src = shot(pg, Path(where).as_uri()) if where.endswith(".html") else Image.open(where).convert("RGB")
            src.thumbnail((SW, RH - 20))
            sheet.paste(src, ((SW - src.width) // 2, r * RH + 10))
        else:
            d.text((20, r * RH + 150), f"來源不在這台機器：{t[mode]['_from']}", font=font(18), fill="#000")
        for k, key in enumerate(["bg", "panel", "fg", "muted", "accent", "accent2", "hi", "ring", "dim"]):
            x = SW + 20 + k * 130
            d.rectangle([x, r * RH + 70, x + 118, r * RH + 250], fill=t[mode][key], outline="#888888")
            d.text((x, r * RH + 258), key, font=font(18), fill="#000")
            d.text((x, r * RH + 284), t[mode][key], font=font(16), fill="#555")
        d.text((SW + 20, r * RH + 22), f"lecture-{mode}   {'亮' if t[mode]['light'] else '暗'}   取樣自 {t[mode]['_from']}", font=font(20), fill="#000")
    sheet.save(out / "palettes.jpg", quality=92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        size = charts(a.out, Path(tmp), pg)
        palettes(a.out, pg)
        br.close()
    print(f"charts.jpg {size[0]}x{size[1]} ({len(PALETTES)} palettes x {len(SCENES)} scenes), palettes.jpg → {a.out}")


if __name__ == "__main__":
    main()
