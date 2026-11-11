"""Veo 宣傳動畫的疊加層元件庫（PIL 逐格繪製 RGBA）。

元件：Title（逐字彈入金字＋掃光）、Ribbon（紅緞帶副標）、Panel（米白標題卡）、
Caption／voice_caption（對齊旁白停頓的字幕）、Tag（學校／教案資訊標籤）、
AwardBadge（獎項光環＋數字跳動）、Particles（金色光點）、GoldSweep（金色光帶轉場）。
配色常數可在 scenes.py 內覆寫（例如 fx.NAVY = (...)）。
"""
import json, math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS = 1920, 1080, 30
FONT_DIR = Path("C:/Windows/Fonts")
SERIF = str(FONT_DIR / "NotoSerifTC-VF.ttf")
SANS = str(FONT_DIR / "NotoSansTC-VF.ttf")

GOLD_TOP, GOLD_BOT = (255, 236, 170), (214, 150, 40)
NAVY, RED, CREAM = (22, 40, 92), (178, 30, 40), (255, 250, 235)


def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    t = max(0.0, min(1.0, t))
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def gradient_text(ch, f, stroke=6):
    """單字：金色漸層＋藏青描邊＋外光暈，回傳 RGBA。"""
    bbox = f.getbbox(ch, stroke_width=stroke)
    w, h = bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40
    off = (20 - bbox[0], 20 - bbox[1])
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text(off, ch, font=f, fill=255)
    smask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(smask).text(off, ch, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    grad = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        k = y / max(1, h - 1)
        c = tuple(int(GOLD_TOP[i] * (1 - k) + GOLD_BOT[i] * k) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = Image.new("RGBA", (w, h), (255, 214, 120, 0))
    glow.putalpha(smask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.85)))
    out = Image.alpha_composite(out, glow)
    stroke_layer = Image.new("RGBA", (w, h), NAVY + (255,))
    stroke_layer.putalpha(smask)
    out = Image.alpha_composite(out, stroke_layer)
    grad.putalpha(mask)
    out = Image.alpha_composite(out, grad)
    return out, mask, off


class Title:
    """逐字彈入的大標題，含掃光。"""

    def __init__(self, text, size, center, t_in, t_out, stagger=0.09, sweep_at=None, weight=900):
        self.f = font(SERIF, size, weight)
        self.glyphs = [gradient_text(c, self.f) for c in text]
        self.adv = [self.f.getlength(c) for c in text]
        total = sum(self.adv)
        x = center[0] - total / 2
        self.pos = []
        for a in self.adv:
            self.pos.append((x + a / 2, center[1]))
            x += a
        self.t_in, self.t_out, self.stagger = t_in, t_out, stagger
        self.sweep_at = sweep_at

    def draw(self, frame, t):
        for i, (g, mask, off) in enumerate(self.glyphs):
            ti = (t - self.t_in - i * self.stagger) / 0.55
            if ti <= 0:
                continue
            to = (t - self.t_out - i * self.stagger * 0.5) / 0.4
            if to >= 1:
                continue
            s = 0.4 + 0.6 * ease_out_back(ti)
            a = min(1.0, ti * 1.8) * (1 - ease_in_out(to))
            dy = (1 - ease_in_out(ti)) * 40 - ease_in_out(to) * 30
            img = g
            if self.sweep_at is not None:
                img = self.sweep(g, mask, t - self.sweep_at - i * 0.05)
            if s != 1:
                img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
            if a < 1:
                img = img.copy()
                img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
            cx, cy = self.pos[i]
            frame.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2 + dy)))

    @staticmethod
    def sweep(g, mask, dt):
        if not (0 <= dt <= 0.6):
            return g
        w, h = g.size
        band = Image.new("L", (w, h), 0)
        x = -w * 0.5 + (dt / 0.6) * w * 2
        ImageDraw.Draw(band).polygon([(x, 0), (x + w * 0.25, 0), (x + w * 0.05, h), (x - w * 0.2, h)], fill=230)
        band = ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(6)), mask)
        white = Image.new("RGBA", (w, h), (255, 255, 245, 0))
        white.putalpha(band)
        return Image.alpha_composite(g, white)


class Ribbon:
    """紅色緞帶副標：由中央向兩側展開。"""

    def __init__(self, text, center, t_in, t_out, size=46):
        self.f = font(SANS, size, 700)
        self.text, self.center, self.t_in, self.t_out = text, center, t_in, t_out
        tw = self.f.getlength(text)
        self.w, self.h = int(tw + 120), int(size * 1.9)
        base = Image.new("RGBA", (self.w + 40, self.h + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(base)
        d.rounded_rectangle([20, 20, 20 + self.w, 20 + self.h], radius=self.h // 2, fill=RED + (235,),
                            outline=(240, 200, 110, 255), width=4)
        d.text((20 + self.w / 2, 20 + self.h / 2), text, font=self.f, fill=CREAM, anchor="mm")
        self.img = base

    def draw(self, frame, t):
        p = ease_in_out((t - self.t_in) / 0.6)
        q = ease_in_out((t - self.t_out) / 0.4)
        if p <= 0 or q >= 1:
            return
        w = max(2, int(self.img.width * p))
        left = (self.img.width - w) // 2
        crop = self.img.crop((left, 0, left + w, self.img.height))
        if q > 0:
            crop.putalpha(crop.getchannel("A").point(lambda v: int(v * (1 - q))))
        frame.alpha_composite(crop, (int(self.center[0] - w / 2), int(self.center[1] - self.img.height / 2)))


class Panel:
    """標題背板：米白圓角卡＋金邊，彈性放大進場、上移淡出。"""

    def __init__(self, box, t_in, t_out):
        box = tuple(int(v) for v in box)
        self.box, self.t_in, self.t_out = box, t_in, t_out
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        img = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + h], radius=36, fill=(20, 30, 60, 90))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([40, 40, 40 + w, 40 + h], radius=36, fill=CREAM + (232,), outline=(214, 160, 60, 255), width=5)
        d.rounded_rectangle([52, 52, 28 + w, 28 + h], radius=28, outline=(240, 205, 120, 200), width=2)
        self.img = img

    def draw(self, frame, t):
        p = (t - self.t_in) / 0.5
        q = ease_in_out((t - self.t_out) / 0.45)
        if p <= 0 or q >= 1:
            return
        s = 0.6 + 0.4 * ease_out_back(p)
        img = self.img.resize((int(self.img.width * s), int(self.img.height * s)), Image.LANCZOS)
        a = min(1, p * 2) * (1 - q)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        cx = (self.box[0] + self.box[2]) / 2
        cy = (self.box[1] + self.box[3]) / 2 - q * 40
        frame.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


class Caption:
    """旁白字幕：依逗號分段、按字數分配時間，淡入淡出。"""

    def __init__(self, text, t0, dur, y=H - 92, size=44, segs=None):
        self.f = font(SANS, size, 600)
        self.y = y
        if segs:
            self.segs = [(t0 + a, t0 + b, x) for a, b, x in segs]
            return
        parts = [p for p in text.replace("。", "，").split("，") if p.strip()]
        n = sum(len(p) for p in parts)
        self.segs, t = [], t0
        for p in parts:
            d = dur * len(p) / n
            self.segs.append((t, t + d, p.strip()))
            t += d
        self.y = y

    def draw(self, frame, t):
        for a, b, s in self.segs:
            if a - 0.05 <= t <= b + 0.05:
                k = min(1, (t - a + 0.05) / 0.15, (b + 0.05 - t) / 0.15)
                tw = self.f.getlength(s)
                layer = Image.new("RGBA", (int(tw + 80), 80), (0, 0, 0, 0))
                d = ImageDraw.Draw(layer)
                d.rounded_rectangle([0, 0, layer.width - 1, 79], radius=40, fill=NAVY + (int(170 * k),))
                d.text((layer.width / 2, 40), s, font=self.f, fill=(255, 255, 255, int(255 * k)), anchor="mm",
                       stroke_width=1, stroke_fill=(10, 20, 50, int(255 * k)))
                frame.alpha_composite(layer, (int(W / 2 - layer.width / 2), int(self.y - 40)))


class AwardBadge:
    """獎項標籤：光環爆開＋藏青膠囊（金字獎名＋大數字跳動）。"""

    def __init__(self, name, num, unit, center, t, label_pos=None):
        self.name, self.num, self.unit, self.c, self.t = name, num, unit, center, t
        self.lp = label_pos or (center[0], center[1] + 70)
        self.fn = font(SERIF, 40, 900)
        self.fnum = font(SERIF, 84, 900)
        self.fu = font(SANS, 34, 700)

    def draw(self, frame, t):
        dt = t - self.t
        if dt < 0:
            return
        cx, cy = self.c
        # 光環
        if dt < 0.9:
            k = dt / 0.9
            r = 60 + 140 * ease_in_out(k)
            ring = Image.new("RGBA", (440, 440), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([220 - r, 220 - r, 220 + r, 220 + r], outline=(255, 226, 140, int(255 * (1 - k))), width=10)
            ring = ring.filter(ImageFilter.GaussianBlur(3))
            frame.alpha_composite(ring, (int(cx - 220), int(cy - 220)))
        # 標籤
        k = ease_out_back(dt / 0.5)
        a = min(1, dt / 0.25)
        val = self.num if dt > 0.45 else max(0, int(round(self.num * dt / 0.45)))
        w, h = 300, 200
        img = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([15, 15, 15 + w, 15 + h], radius=28, fill=NAVY + (225,), outline=(232, 184, 80, 255), width=4)
        d.text((15 + w / 2, 52), self.name, font=self.fn, fill=(255, 222, 140), anchor="mm")
        tw = self.fnum.getlength(str(val)); uw = self.fu.getlength(self.unit)
        x0 = 15 + w / 2 - (tw + 8 + uw) / 2
        d.text((x0, 140), str(val), font=self.fnum, fill=(255, 244, 210), anchor="lm", stroke_width=2, stroke_fill=(150, 100, 20))
        d.text((x0 + tw + 8, 152), self.unit, font=self.fu, fill=CREAM, anchor="lm")
        s = 0.5 + 0.5 * k
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
        if a < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        lx, ly = self.lp
        frame.alpha_composite(img, (int(lx - img.width / 2), int(ly + (1 - k) * 30)))


class Particles:
    """金色光點緩緩上升、閃爍。"""

    def __init__(self, n=70, seed=1, region=(0, 0, W, H)):
        rnd = random.Random(seed)
        self.p = [dict(x=rnd.uniform(region[0], region[2]), y=rnd.uniform(region[1], region[3]),
                       r=rnd.uniform(2, 6), v=rnd.uniform(18, 55), ph=rnd.uniform(0, 6.28),
                       sw=rnd.uniform(10, 30)) for _ in range(n)]
        dot = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(dot).ellipse([24, 24, 40, 40], fill=(255, 230, 150, 255))
        self.dot = dot.filter(ImageFilter.GaussianBlur(5))
        core = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(core).ellipse([29, 29, 35, 35], fill=(255, 255, 235, 255))
        self.dot = Image.alpha_composite(self.dot, core)

    def draw(self, frame, t, alpha=1.0):
        for q in self.p:
            y = (q["y"] - q["v"] * t) % (H + 80) - 40
            x = q["x"] + math.sin(t * 0.8 + q["ph"]) * q["sw"]
            tw = 0.5 + 0.5 * math.sin(t * 3 + q["ph"] * 2)
            s = q["r"] / 5 * (0.7 + 0.5 * tw)
            d = self.dot.resize((max(4, int(64 * s)), max(4, int(64 * s))))
            a = alpha * (0.35 + 0.65 * tw)
            d.putalpha(d.getchannel("A").point(lambda v: int(v * a)))
            frame.alpha_composite(d, (int(x - d.width / 2), int(y - d.height / 2)))


class GoldSweep:
    """轉場用金色光帶：從左下斜掃到右上，中段幾乎覆蓋全畫面（可與下一鏡銜接）。"""

    def __init__(self, t0, dur=1.0, reverse=False):
        self.t0, self.dur, self.reverse = t0, dur, reverse

    def draw(self, frame, t):
        k = (t - self.t0) / self.dur
        if not (0 <= k <= 1):
            return
        k = ease_in_out(k)
        if self.reverse:
            k = 1 - k
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        cx = -900 + k * (W + 1800)
        for width, col in [(1500, (255, 214, 120, 120)), (900, (255, 226, 150, 200)), (380, (255, 246, 210, 255))]:
            d.polygon([(cx - width / 2 - 500, H), (cx + width / 2 - 500, H), (cx + width / 2 + 500, 0),
                       (cx - width / 2 + 500, 0)], fill=col)
        layer = layer.filter(ImageFilter.GaussianBlur(40))
        frame.alpha_composite(layer)

VOICE = {}


def load_voice_timing(path):
    """讀 voice_timing.py 產生的 JSON（每句旁白的語音段落）。"""
    global VOICE
    VOICE.clear()
    VOICE.update(json.load(open(path, encoding="utf-8")))
    return VOICE


def voice_caption(nid, delay, display=None, **kw):
    """依旁白實際語音段落切字幕：display 以「，」分段，各段起點貼齊最接近的語音段起點。
    display 可與旁白用字不同（例如旁白念「一百一十五年」、字幕顯示「115 年」）。"""
    v = VOICE[nid]
    segs = v["segs"]
    parts = [p.strip() for p in (display or "，".join(v["parts"])).replace("。", "，").split("，") if p.strip()]
    starts = [a for a, b in segs]
    t0, t1 = segs[0][0], segs[-1][1]
    n = sum(len(p) for p in parts)
    out, acc, bounds = [], 0, []
    for p in parts:
        est = t0 + (t1 - t0) * acc / n
        bounds.append(min(starts, key=lambda s: abs(s - est)))
        acc += len(p)
    bounds[0] = t0
    for i in range(1, len(bounds)):
        if bounds[i] <= bounds[i - 1]:
            bounds[i] = bounds[i - 1] + 0.3
    for i, p in enumerate(parts):
        b = bounds[i + 1] - 0.05 if i + 1 < len(parts) else t1 + 0.25
        out.append((bounds[i], b, p))
    return Caption("", delay, 0, segs=out, **kw)


def fit_font(path, text, size, weight, maxw):
    f = font(path, size, weight)
    while f.getlength(text) > maxw and size > 18:
        size -= 2
        f = font(path, size, weight)
    return f


class Tag:
    """資訊標籤：藏青半透明圓角卡＋金邊，多行文字，由左側滑入。"""

    def __init__(self, lines, pos, t_in, t_out=99, maxw=860, anchor="lt"):
        fonts, ws, hs = [], [], []
        for text, size, weight, col, fam in lines:
            f = fit_font(SERIF if fam == "serif" else SANS, text, size, weight, maxw)
            fonts.append(f)
            ws.append(f.getlength(text))
            hs.append(int(f.size * 1.32))
        w, h = int(max(ws) + 56), int(sum(hs) + 30)
        img = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([15, 21, 15 + w, 21 + h], radius=22, fill=(10, 18, 45, 110))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([15, 15, 15 + w, 15 + h], radius=22, fill=NAVY + (226,), outline=(226, 178, 78, 255), width=3)
        y = 15 + 15
        for (text, size, weight, col, fam), f, hh in zip(lines, fonts, hs):
            d.text((15 + 28, y + hh / 2), text, font=f, fill=col, anchor="lm")
            y += hh
        self.img, self.pos, self.t_in, self.t_out, self.anchor = img, pos, t_in, t_out, anchor

    def draw(self, frame, t):
        p = ease_in_out((t - self.t_in) / 0.45)
        q = ease_in_out((t - self.t_out) / 0.4)
        if p <= 0 or q >= 1:
            return
        img = self.img
        a = p * (1 - q)
        if a < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        x, y = self.pos
        if self.anchor == "ct":
            x -= img.width / 2
        elif self.anchor == "rt":
            x -= img.width
        x += (1 - p) * -60 + q * 40
        frame.alpha_composite(img, (int(x), int(y)))


GOLD_TXT, CREAM_TXT = (255, 216, 120), (255, 248, 230)
