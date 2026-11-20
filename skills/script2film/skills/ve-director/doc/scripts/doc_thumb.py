"""One YouTube thumbnail per episode (1280×720 JPG, under 2 MB): a darkened background photo, a cut-out (person, object) on the
right, big words on the left, the channel mark top left; set automatically
when the episode is uploaded.

  python3 doc_thumb.py <doc.json>            reads doc["thumb"], writes <episode>/thumbnail.jpg
doc["thumb"]: {"bg": photo (default: the "pic"), "cut": RGBA cut-out (doc_cutout.py *_fg.png) | "pic": a framed picture (VE still) when there
               is no real person, "title": big words, "title2": second line, "sub": one small line, "logo": RGBA mark,
               "accent": "#rrggbb" (title colour), "credit": text}. Paths are relative to the episode.
Credit line: small grey text along the bottom; "credit" when given,
otherwise the 署名 of every picture used, looked up in <episode>/assets/CREDITS.md (a cut-out foo_fg.png counts as foo.jpg).
Font: Noto Sans TC (variable, Black/Bold) from the asset layers (doc_common.asset("fonts", ...)).
"""
import re, sys
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from doc_common import asset, read_json

W, H = 1280, 720
MAX_BYTES = 2 * 1024 * 1024   # YouTube custom thumbnail limit


def font(weight, size):
    f = ImageFont.truetype(str(asset("fonts", "NotoSansTC-Variable.ttf")), size)
    f.set_variation_by_name(weight)
    return f


def cover(im, w, h):
    """Scale and centre-crop to fill w×h."""
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def fit_text(text, weight, size, max_w):
    """Largest size ≤ size whose text fits max_w."""
    while size > 20:
        f = font(weight, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 4
    return font(weight, size)


def credits_for(spec, base):
    """署名 of the pictures this thumbnail uses, from assets/CREDITS.md (table: 檔案｜原檔｜授權｜作者｜署名｜用在)."""
    if spec.get("credit"):
        return spec["credit"]
    table = base / "assets/CREDITS.md"
    if not table.exists():
        return ""
    names = {re.sub(r"_fg\.png$", ".jpg", Path(spec[k]).name) for k in ("bg", "cut", "pic") if spec.get(k)}
    out = []
    for row in table.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in row.strip().strip("|").split("|")]
        if len(c) >= 5 and c[0] in names and c[4] not in out:
            out.append(c[4])
    return "；".join(out)


def make(spec, base):
    # no bg: the picture itself, blurred and darkened behind its framed copy
    bg = cover(Image.open(base / (spec.get("bg") or spec["pic"])).convert("RGB"), W, H).filter(ImageFilter.GaussianBlur(3))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    # left-to-right shade so the words read on any photo
    shade = Image.linear_gradient("L").rotate(90, expand=True).resize((W, H))   # white on the left → black on the right
    im = Image.composite(Image.new("RGB", (W, H), (8, 10, 18)), bg, shade.point(lambda v: int(v * 0.75)))

    if spec.get("cut"):
        cut = Image.open(base / spec["cut"]).convert("RGBA")
        cut = cut.crop(cut.getchannel("A").getbbox())
        k = H * 0.94 / cut.height   # head clear of the top edge
        cut = cut.resize((round(cut.width * k), round(cut.height * k)), Image.LANCZOS)
        x = W - cut.width + round(cut.width * 0.08)
        glow = Image.new("RGBA", cut.size, (0, 0, 0, 0))
        glow.putalpha(cut.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.6))
        im.paste((0, 0, 0), (x - 10, H - cut.height + 6), glow)
        im.paste(cut, (x, H - cut.height), cut)

    room = 690   # width the words may use
    if spec.get("pic"):
        pic = cover(Image.open(base / spec["pic"]).convert("RGB"), 576, 324)
        frame = Image.new("RGB", (pic.width + 24, pic.height + 24), (245, 240, 228))
        frame.paste(pic, (12, 12))
        frame = frame.convert("RGBA").rotate(-3, expand=True, resample=Image.BICUBIC)
        x, y = W - frame.width - 30, (H - frame.height) // 2 + 20
        shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        shadow.putalpha(frame.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: v * 0.7))
        im.paste((0, 0, 0), (x + 12, y + 16), shadow)
        im.paste(frame, (x, y), frame)
        room = x - 64 - 24   # the words stop short of the picture

    d = ImageDraw.Draw(im)
    accent, left = spec.get("accent", "#FFC52F"), 64
    y = 128 if spec.get("logo") else 70   # the mark sits above the words
    f1 = fit_text(spec["title"], b"Black", 230, room)
    d.text((left, y), spec["title"], font=f1, fill=accent, stroke_width=6, stroke_fill=(0, 0, 0))
    y += f1.size + 24
    if spec.get("title2"):
        f2 = fit_text(spec["title2"], b"Black", 120, room)
        d.text((left, y), spec["title2"], font=f2, fill="white", stroke_width=5, stroke_fill=(0, 0, 0))
        y += f2.size + 40
    if spec.get("sub"):
        f3 = fit_text(spec["sub"], b"Bold", 52, room - 40)
        tw = f3.getlength(spec["sub"])
        d.rectangle((left - 14, y - 8, left + tw + 20, y + f3.size + 20), fill=accent)
        d.text((left + 3, y), spec["sub"], font=f3, fill=(10, 10, 10))

    if spec.get("logo"):
        logo = Image.open(base / spec["logo"]).convert("RGBA")
        logo = logo.crop(logo.getchannel("A").getbbox()).resize((92, 92), Image.LANCZOS)
        im.paste(logo, (left, 28), logo)   # top left: the cut-out owns the right side

    credit = credits_for(spec, base)
    if credit:
        fc = font(b"Regular", 17)
        while fc.getlength(credit) > W - 2 * left and fc.size > 11:
            fc = font(b"Regular", fc.size - 1)
        d.text((left - 30, H - 30), credit, font=fc, fill=(190, 190, 190), stroke_width=2, stroke_fill=(0, 0, 0))
    return im


def main():
    doc_path = Path(sys.argv[1]).resolve()
    doc = read_json(doc_path)
    if "thumb" not in doc:
        sys.exit("✗ doc.json has no thumb field")
    base = doc_path.parent
    out = base / "thumbnail.jpg"
    im = make(doc["thumb"], base)
    for q in (92, 85, 78, 70):
        im.save(out, quality=q, optimize=True)
        if out.stat().st_size <= MAX_BYTES:
            break
    print(f"{out}: {W}x{H}, {out.stat().st_size // 1024} KB")
    if out.stat().st_size > MAX_BYTES:
        sys.exit("✗ over 2 MB, YouTube will not take it: use a background with less detail")


if __name__ == "__main__":
    main()
