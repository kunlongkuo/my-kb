"""依專案的 scenes.py 逐格產生疊加層 PNG（透明背景）。
用法：python render_overlay.py --config project.json --scene s01 [--scene s02 ...] | --all
scenes.py 需定義 build(scene_id, fx) -> (dur, items)；fx 即 fxlib 模組。
"""
import argparse, importlib.util, json, shutil, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fxlib as fx  # noqa: E402
import projcfg  # noqa: E402


def load_scenes(cfg):
    spec = importlib.util.spec_from_file_location("scenes", cfg.path("scenes_py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render(cfg_path, sid):
    from PIL import Image
    cfg = projcfg.load(cfg_path)
    if cfg.path("voice_timing").exists():
        fx.load_voice_timing(cfg.path("voice_timing"))
    dur, items = load_scenes(cfg).build(sid, fx)
    want = cfg.scene(sid)["dur"]
    if abs(dur - want) > 0.01:
        print(f"[警告] {sid} scenes.py 片長 {dur} 與 project.json {want} 不同，以 project.json 為準")
        dur = want
    out = cfg.path("work_dir") / f"ov_{sid}"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    n = int(round(dur * fx.FPS))
    for i in range(n):
        t = i / fx.FPS
        frame = Image.new("RGBA", (fx.W, fx.H), (0, 0, 0, 0))
        for it in items:
            it.draw(frame, t)
        frame.save(out / f"{i:04d}.png", compress_level=1)
    return json.dumps({"scene": sid, "frames": n, "dur": dur})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--scene", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    cfg = projcfg.load(a.config)
    ids = [s["id"] for s in cfg["scenes"]] if a.all else a.scene
    with ProcessPoolExecutor(a.jobs) as ex:
        for r in ex.map(render, [a.config] * len(ids), ids):
            print(r)
