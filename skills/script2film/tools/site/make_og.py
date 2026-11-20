"""Makes the share-preview images (1200×630): docs/site/og-zh.jpg for the Chinese pages, docs/site/og.jpg for the
English ones (og_tags.py writes each page's og:image from site_config.OG_IMAGE).

  python3 tools/site/make_og.py [--font path/to/NotoSansTC-Variable.ttf]

Run it only when the images should change; it is not part of the regular site build (build_en.py).
Layout: "Script2Film" on the left (the "2" in the site's gold, as in the page header), the home page's subtitle in two
lines below it, and frames from films on the right, each with rounded corners and a soft shadow.
  zh: the cream of the daily devotional films, two portrait frames from them (December's opening, a January background).
     The Chinese audience is mostly churches and friends who know that series.
  en: the site's dark background, a frame from the opening of Dino park above the host with English subtitles
     (docs/site/host-full.jpg). The English audience is mostly people who work in tech and AI.
The frames are kept in tools/site/og_src/ (devotional-*.png were cut from the blog post's month-by-month figure,
dino-park.jpg is a full-resolution screenshot of the opening of Dino park, cropped to 16:9; a frame cut from
docs/site/studio-hero.mp4 is too soft).
The font is Noto Sans TC from assets/fonts/ (see docs/INSTALL.md); it is read, not copied. Same input, same output.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()

import argparse, pathlib, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from site_config import OG_IMAGE, OG_IMAGE_SIZE  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "site" / "og_src"
GOLD = (216, 185, 94)    # site.css dark --gold #d8b95e
LOOK = {
    "zh": {"bg": (242, 238, 224), "fg": (31, 74, 66), "sub": (90, 96, 92),          # the devotional films' cream
           "lines": ("給 AI agent 用的", "影片與解說片工具組"),                       # docs/index.html hero subtitle
           "frames": [SRC / "devotional-december.png", SRC / "devotional-january.png"], "side": "row", "h": 470},
    "en": {"bg": (20, 24, 31), "fg": (236, 231, 216), "sub": (200, 204, 212),       # site.css dark --bg, --fg
           "lines": ("A video and explainer", "toolkit for AI agents"),             # docs/en/index.html hero subtitle
           "frames": [SRC / "dino-park.jpg", ROOT / "docs" / "site" / "host-full.jpg"], "side": "column", "w": 500},
}
RIGHT, GAP, RADIUS = 56, 24, 13


def font(path, size, weight):
    f = ImageFont.truetype(str(path), size)
    f.set_variation_by_axes([weight])
    return f


def place(im, frame, x, y):
    """Paste a frame with rounded corners over a soft drop shadow."""
    w, h = frame.size
    shadow = Image.new("L", (w + 40, h + 40))
    ImageDraw.Draw(shadow).rounded_rectangle((20, 26, w + 19, h + 25), RADIUS, fill=115)
    im.paste((0, 0, 0), (x - 20, y - 20), shadow.filter(ImageFilter.GaussianBlur(10)))
    mask = Image.new("L", (w, h))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), RADIUS, fill=255)
    im.paste(frame, (x, y), mask)


def make(font_path, lang):
    W, H = OG_IMAGE_SIZE
    L = LOOK[lang]
    im = Image.new("RGB", (W, H), L["bg"])
    frames = [Image.open(f).convert("RGB") for f in L["frames"]]
    if L["side"] == "row":       # portrait frames side by side, all the same height
        fh = L["h"]
        frames = [f.resize((round(f.width * fh / f.height), fh), Image.LANCZOS) for f in frames]
        x = W - RIGHT - sum(f.width for f in frames) - GAP * (len(frames) - 1)
        left_edge, y = x, (H - fh) // 2
        for f in frames:
            place(im, f, x, y)
            x += f.width + GAP
        top, bottom = y, y + fh
    else:                        # landscape frames stacked, all the same width
        fw = L["w"]
        frames = [f.resize((fw, round(f.height * fw / f.width)), Image.LANCZOS) for f in frames]
        left_edge = x = W - RIGHT - fw
        top = y = (H - sum(f.height for f in frames) - GAP * (len(frames) - 1)) // 2
        for f in frames:
            place(im, f, x, y)
            y += f.height + GAP
        bottom = y - GAP
    assert top >= 0 and bottom <= H and left_edge > 0, "frames run off the image"
    d = ImageDraw.Draw(im)
    big, sub = font(font_path, 80, 800), font(font_path, 34, 500)
    left, base = 64, 290
    cx = left
    for text, col in (("Script", L["fg"]), ("2", GOLD), ("Film", L["fg"])):
        d.text((cx, base), text, font=big, fill=col, anchor="ls")
        cx += d.textlength(text, font=big)
    d.rectangle((left, base + 28, left + 100, base + 33), fill=GOLD)
    for k, line in enumerate(L["lines"]):
        d.text((left, base + 92 + 50 * k), line, font=sub, fill=L["sub"], anchor="ls")
    widest = max([cx] + [left + d.textlength(t, font=sub) for t in L["lines"]])
    assert widest < left_edge - 20, "the words run into the frames"
    dst = ROOT / "docs" / OG_IMAGE[lang]
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=85, optimize=True)
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", default=str(ROOT / "assets" / "fonts" / "NotoSansTC-Variable.ttf"))
    a = ap.parse_args()
    for lang in ("zh", "en"):
        out = make(a.font, lang)
        print(f"{out.relative_to(ROOT)}: {Image.open(out).size}, {out.stat().st_size // 1024} KB")
