"""偵測每句旁白的語音段落（silencedetect），供字幕對齊與標籤出場時間使用。
用法：python voice_timing.py --manifest 配音清單.json --audio-dir <mp3資料夾> --out voice_timing.json
清單格式：{"clips": [{"id": "n01", "text": "旁白文字"}, ...]}；音檔檔名為 <id>.mp3。
"""
import argparse, json, re, subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--manifest", required=True)
ap.add_argument("--audio-dir", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--noise", default="-35dB")
ap.add_argument("--min-sil", default="0.15")
a = ap.parse_args()

m = json.load(open(a.manifest, encoding="utf-8"))
out = {}
for c in m["clips"]:
    f = Path(a.audio_dir) / f"{c['id']}.mp3"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", f"silencedetect=noise={a.noise}:d={a.min_sil}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                               capture_output=True, text=True).stdout)
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    segs, cur = [], 0.0
    for s0, s1 in sorted(zip(ss, se + [dur] * (len(ss) - len(se)))):
        if s0 - cur > 0.05:
            segs.append((round(cur, 2), round(s0, 2)))
        cur = s1
    if dur - cur > 0.05:
        segs.append((round(cur, 2), round(dur, 2)))
    parts = [p for p in re.split("[，。：、！？]", c["text"]) if p.strip()]
    out[c["id"]] = dict(dur=round(dur, 3), segs=segs, parts=parts)
    print(c["id"], round(dur, 2), "segs", len(segs), "parts", len(parts))
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", a.out)
