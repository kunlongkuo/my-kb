"""從下載資料夾找出 Veo／Flow 影片，以首格比對分鏡構圖圖，搬到 veo_dir/<scene>_veo.mp4。
用法：python identify_clips.py --config project.json --refs <構圖圖資料夾> [--downloads <下載資料夾>] [--apply]
構圖圖檔名需含場景 ID（例如 s05.jpg、20261105-s05v2.png）；同一場景有多支時取最新的。
未加 --apply 只列出比對結果。舊檔會改名為 *_veo_old<n>.mp4，不刪除。
"""
import argparse, os, re, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projcfg  # noqa: E402
from PIL import Image, ImageChops, ImageStat  # noqa: E402


def thumb(img):
    w, h = img.size
    if w / h < 16 / 9:
        nh = int(w * 9 / 16)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.convert("L").resize((64, 36))


ap = argparse.ArgumentParser()
ap.add_argument("--config", required=True)
ap.add_argument("--refs", required=True)
ap.add_argument("--downloads", default=str(Path.home() / "Downloads"))
ap.add_argument("--apply", action="store_true")
ap.add_argument("--max-diff", type=float, default=12.0)
a = ap.parse_args()
cfg = projcfg.load(a.config)
ids = [s["id"] for s in cfg["scenes"]]
refs = {}
for f in sorted(Path(a.refs).iterdir()):
    m = re.search(r"(s\d{2})", f.name)
    if m and m.group(1) in ids and f.suffix.lower() in (".png", ".jpg", ".jpeg"):
        refs[m.group(1)] = thumb(Image.open(f))       # 後面的（v2）覆蓋前面
vids = sorted(Path(a.downloads).glob("*.mp4"), key=lambda p: p.stat().st_mtime)
tmp = Path(tempfile.gettempdir()) / "idclip.png"
best = {}
for v in vids:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(v), "-frames:v", "1", str(tmp)])
    if not tmp.exists():
        continue
    t = thumb(Image.open(tmp))
    sc = {k: ImageStat.Stat(ImageChops.difference(t, r)).mean[0] for k, r in refs.items()}
    k = min(sc, key=sc.get)
    ok = sc[k] <= a.max_diff
    print(f"{v.name[:50]:50s} -> {k if ok else '??'}  diff={sc[k]:.1f}")
    if ok:
        best[k] = v                                    # 依修改時間排序，最新的勝出
dst = cfg.path("veo_dir")
dst.mkdir(parents=True, exist_ok=True)
for k, v in sorted(best.items()):
    target = dst / f"{k}_veo.mp4"
    print(f"{k}: {v.name}")
    if a.apply:
        if target.exists():
            n = 1
            while (dst / f"{k}_veo_old{n}.mp4").exists():
                n += 1
            target.rename(dst / f"{k}_veo_old{n}.mp4")
        os.replace(v, target)
if not a.apply:
    print("（預覽；加 --apply 才會搬移）")
