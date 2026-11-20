#!/usr/bin/env python3
"""收片後檢查 VE 片段：每支完整解碼、長度、片中換鏡點，以及首格是不是拿了上一鏡的圖。

  python3 ve_clipcheck.py <ve_collage 資料夾> [--run <ve-runs/時間 資料夾>] [--scd 12] [--strips]

換鏡點用 ffmpeg scdet（門檻 12）：VE 一鏡應該是單一連續鏡頭，
片中有換鏡就印出秒數；開頭 2.5 秒內的換鏡常是先放了參考圖（片段開頭可能先放 1–2 秒的參考圖）。
給 --run 時再比首格：首格比較像上一鏡的候選圖、不像自己的候選圖，就是 VE 拿了上一鏡的圖（實際出過兩次）。
這一項不設門檻，只比兩個距離誰小。有問題的鏡印 ✗、exit 1；寫 <資料夾>/clipcheck.json。
--strips：另存 <資料夾>/strips.jpg，資料夾裡每支 mp4 一列、由左到右五格（片長的 10、30、50、70、90%）。給人看動作方向用：
生成影片會把車倒著開、人倒著走（2026-11-14 一支卡車片上線前沒看出來）。這不是機器檢查：光流量得到畫面往哪邊動，量不到
車頭朝哪邊，所以只出圖，由看的人判斷；方向錯就整支倒放（ffmpeg reverse）或重生。
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
from PIL import Image, ImageChops, ImageStat

EARLY_CUT_S = 2.5   # 實測先放參考圖 1–2.2 秒；多留一點


def shot_no(p):
    m = re.search(r"shot(\d+)", p.stem)
    return int(m[1]) if m else None


def probe(p, scd):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(p)],
                                  capture_output=True, text=True).stdout or "{}")
    r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(p), "-vf", f"scdet=threshold={scd}", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    errs = [ln for ln in r.stderr.splitlines() if re.search(r"error|invalid|corrupt", ln, re.I) and "scd" not in ln]
    cuts = [round(float(x), 2) for x in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", r.stderr)]
    return {"dur": round(float(d.get("format", {}).get("duration", 0)), 2), "cuts": cuts, "ok": r.returncode == 0 and not errs}


def thumb(path):
    return Image.open(path).convert("L").resize((96, 54))


def dist(a, b):
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def first_frame(p, tmp):
    out = Path(tmp) / f"{p.stem}_f0.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-frames:v", "1", str(out)], check=True)
    return thumb(out)


def check(clips_dir, run=None, scd=12):
    clips = sorted((p for p in Path(clips_dir).glob("shot*.mp4") if shot_no(p)), key=shot_no)
    res, bad = {}, 0
    with tempfile.TemporaryDirectory() as tmp:
        for p in clips:
            n, c = shot_no(p), probe(p, scd)
            notes = [] if c["ok"] else ["decode failed"]
            if c["cuts"]:
                notes.append(("reference image shown first?" if c["cuts"][0] <= EARLY_CUT_S else "cut inside the clip") + f" {c['cuts']}")
            if run:
                own, prev = Path(run) / f"shot{n}_cand1.jpg", Path(run) / f"shot{n - 1}_cand1.jpg"
                if own.exists() and prev.exists():
                    f0 = first_frame(p, tmp)
                    d_own, d_prev = dist(f0, thumb(own)), dist(f0, thumb(prev))
                    c.update(d_own=round(d_own, 1), d_prev=round(d_prev, 1))
                    if d_prev < d_own:
                        notes.append(f"first frame looks like the previous shot (distance {d_prev:.1f} < own {d_own:.1f})")
            c["notes"] = notes
            bad += bool(notes)
            res[p.name] = c
            print(f"{'✗' if notes else '✓'} {p.name:12} {c['dur']:5.2f}s  {'; '.join(notes)}")
    (Path(clips_dir) / "clipcheck.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return bad


def strips(clips_dir, n=5, w=384, h=216):
    """One row per mp4 in the folder, n frames left to right in time order → <folder>/strips.jpg; returns its path or None."""
    from PIL import ImageDraw
    clips = sorted(Path(clips_dir).glob("*.mp4"))
    if not clips:
        return None
    sheet = Image.new("RGB", (n * w, len(clips) * (h + 24)), "white")
    d = ImageDraw.Draw(sheet)
    with tempfile.TemporaryDirectory() as tmp:
        for r, p in enumerate(clips):
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                       capture_output=True, text=True).stdout or 0)
            for k in range(n):
                f = Path(tmp) / f"{r}_{k}.jpg"
                t = dur * (2 * k + 1) / (2 * n)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1",
                                "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2", str(f)])
                if f.exists():
                    sheet.paste(Image.open(f), (k * w, r * (h + 24) + 24))
            d.text((4, r * (h + 24) + 6), f"{p.name}  {dur:.1f}s  (left to right = time)", fill="black")
    out = Path(clips_dir) / "strips.jpg"
    sheet.save(out, quality=85)
    return out


def main():
    ap = argparse.ArgumentParser(description="Check VE clips after collecting them: full decode, length, cuts inside a clip, "
                                             "and whether the first frame took the previous shot's image.")
    ap.add_argument("clips")
    ap.add_argument("--run", help="ve-runs/<time> folder (with shotN_cand1.jpg): compare first frames with the candidate images")
    ap.add_argument("--scd", type=float, default=12)
    ap.add_argument("--strips", action="store_true", help="also write strips.jpg: five frames per clip, for a person to check the motion direction (not a machine check)")
    a = ap.parse_args()
    bad = check(a.clips, a.run, a.scd)
    if a.strips:
        out = strips(a.clips)
        print(f"check the motion direction in {out} (each row runs left to right in time)" if out else "strips: no mp4 in the folder")
    print(f"{bad} shot(s) to look at" if bad else "all passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
