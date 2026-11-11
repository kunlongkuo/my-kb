"""片尾名單捲動：背景＝模糊暗化的結尾畫面＋金色粒子，最後淡出到黑。
用法：python credits.py --config project.json
project.json 的 credits: {"dur": 16, "bg": "<圖>", "rows": [["h1","標題"],["h2","獎項"],["s","學校｜姓名"],["p","《教案》"],["gap",""]]}
"""
import argparse, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fxlib as fx  # noqa: E402
import projcfg  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

W, H, FPS = fx.W, fx.H, fx.FPS
STY = {"h1": (fx.SERIF, 64, 900, (255, 222, 140), 96), "h2": (fx.SERIF, 54, 900, (255, 200, 90), 92),
       "s": (fx.SANS, 32, 700, (255, 226, 160), 50), "p": (fx.SERIF, 36, 700, (255, 250, 236), 64),
       "gap": (fx.SANS, 10, 400, (0, 0, 0), 60)}


def sheet(rows):
    hs = sum(STY[k][4] for k, _ in rows) + 80
    img = Image.new("RGBA", (W, hs), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 40
    for k, text in rows:
        path, size, wt, col, lh = STY[k]
        f = fx.fit_font(path, text, size, wt, W - 220)
        if k == "h2":
            tw = f.getlength(text)
            d.rounded_rectangle([W / 2 - tw / 2 - 40, y + 6, W / 2 + tw / 2 + 40, y + lh - 14], radius=30,
                                fill=fx.RED + (235,), outline=(240, 200, 110), width=3)
            d.text((W / 2, y + lh / 2 - 4), text, font=f, fill=(255, 246, 220), anchor="mm")
        elif text:
            d.text((W / 2, y + lh / 2), text, font=f, fill=col, anchor="mm", stroke_width=2, stroke_fill=(10, 20, 50))
        y += lh
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    cfg = projcfg.load(a.config)
    cr = cfg["credits"]
    dur = float(cr.get("dur", 16))
    bgp = Path(cr["bg"]) if Path(cr["bg"]).is_absolute() else Path(cfg["root"]) / cr["bg"]
    bg = Image.open(bgp).convert("RGB").resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", (W, H), fx.NAVY), 0.62).convert("RGBA")
    sh, parts = sheet(cr["rows"]), fx.Particles(70, 11)
    out = cfg.path("parts_dir") / "credits.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)],
                          stdin=subprocess.PIPE)
    travel = sh.height + H * 0.15
    for i in range(int(dur * FPS)):
        t = i / FPS
        fr = bg.copy()
        parts.draw(fr, t, 0.7)
        y = int(H * 0.9 - travel * t / dur)
        if y > -sh.height:
            fr.alpha_composite(sh, (0, y))
        a = min(1, (dur - t) / 1.2)
        if a < 1:
            fr = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), fr, max(0, a))
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print("credits", out, dur)
