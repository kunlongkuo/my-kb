"""把 Veo 片段放大到 1080p30、依片長變速，疊上疊加層，輸出純畫面片段（供 assemble 串接）。
用法：python render_clip.py --config project.json --scene s01 | --all
變速：K = 片長 / Veo 長度。interp（project.json 每鏡可設）：
  auto  K<=1.15 用 fps 複製畫格；K>1.15 用 framerate 混合（柔順但快速動作會殘影）
  dup   一律複製畫格（快速動作的鏡頭用這個，避免殘影）
  blend 一律混合
不要用 minterpolate（mci）：插畫人物會糊成色塊。
"""
import argparse, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projcfg  # noqa: E402

BLEND = "framerate=fps=30:interp_start=0:interp_end=255:scene=100"


def dur_of(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


def clip(cfg, sid):
    sc = cfg.scene(sid)
    src = cfg.path("veo_dir") / f"{sid}_veo.mp4"
    D = sc["dur"]
    K = max(1.0, D / (dur_of(src) - 0.05))
    mode = sc.get("interp", "auto")
    interp = "fps=30" if mode == "dup" or (mode == "auto" and K <= 1.15) else BLEND
    ov = cfg.path("work_dir") / f"ov_{sid}" / "%04d.png"
    out = cfg.path("parts_dir") / f"{sid}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    fc = (f"[0:v]setpts={K}*PTS,{interp},trim=0:{D},setpts=PTS-STARTPTS,scale=1920:1080:flags=lanczos,eq=saturation=1.05[bg];"
          f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-framerate", "30", "-i", str(ov), "-filter_complex", fc,
                    "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-r", "30", "-t", str(D), str(out)],
                   check=True)
    warn = "  [注意] 放慢超過 1.5 倍，動作可能偏慢" if K > 1.5 else ""
    return f"{sid} K={K:.2f} {interp.split('=')[0]}{warn}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--scene", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    cfg = projcfg.load(a.config)
    ids = [s["id"] for s in cfg["scenes"]] if a.all else a.scene
    with ThreadPoolExecutor(a.jobs) as ex:
        for r in ex.map(lambda s: clip(cfg, s), ids):
            print(r)
