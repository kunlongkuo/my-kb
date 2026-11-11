"""整片串接與混音。
- 各鏡在金色光帶下 xfade 溶接；最後一鏡 1 秒溶入片尾名單（若有 credits）。
- 旁白依時間軸擺放（每鏡起點＋delay）。
- 背景音樂延長到片長：前段 [0,a_end] 接上從 Y 秒到結尾的後段，交叉淡化，使音樂自然結尾落在片尾；
  旁白出現時 sidechain 自動壓低，最後 loudnorm。
用法：python assemble.py --config project.json [--dry-run]
"""
import argparse, json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projcfg  # noqa: E402


def dur_of(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


ap = argparse.ArgumentParser()
ap.add_argument("--config", required=True)
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
c = projcfg.load(a.config)
SC, XF, TAIL, CXF = c["scenes"], c["xfade"], c["tail"], c["credits_xfade"]
PARTS = c.path("parts_dir")
cred = PARTS / "credits.mp4"
has_cred = "credits" in c and (cred.exists() or a.dry_run)
CRED = float(c["credits"]["dur"]) if has_cred else 0

lens = [s["dur"] - TAIL if i < len(SC) - 1 else s["dur"] for i, s in enumerate(SC)]
starts, t = [], 0.0
for i, L in enumerate(lens):
    starts.append(t)
    t += L - (XF if i < len(SC) - 1 else 0)
total = (t - CXF + CRED) if has_cred else t
gaps = []
for k in range(1, len(SC)):
    prev_end = starts[k - 1] + SC[k - 1]["delay"] + dur_of(c.path("voice_dir") / f"{SC[k-1]['voice']}.mp3")
    gaps.append(round(starts[k] + SC[k]["delay"] - prev_end, 2))
print(json.dumps({"starts": [round(x, 2) for x in starts], "credits_at": round(t - CXF, 2) if has_cred else None,
                  "total": round(total, 2), "voice_gaps": gaps}, ensure_ascii=False))
if any(g < 0 for g in gaps):
    print("[警告] 有旁白重疊（gap<0），請加長前一鏡 dur")
if a.dry_run:
    sys.exit(0)

inp, fc = [], []
for i, s in enumerate(SC):
    inp += ["-i", str(PARTS / f"{s['id']}.mp4")]
    fc.append(f"[{i}:v]trim=0:{lens[i]},setpts=PTS-STARTPTS,fps=30,settb=AVTB[v{i}]")
prev, acc = "v0", lens[0]
for i in range(1, len(SC)):
    off = acc - XF
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
    prev, acc = f"x{i}", off + lens[i]
n_in = len(SC)
if has_cred:
    inp += ["-i", str(cred)]
    fc.append(f"[{n_in}:v]fps=30,settb=AVTB[vc]")
    fc.append(f"[{prev}][vc]xfade=transition=fade:duration={CXF}:offset={acc - CXF:.3f}[vout]")
    n_in += 1
else:
    fc.append(f"[{prev}]null[vout]")

labels = []
for k, s in enumerate(SC):
    inp += ["-i", str(c.path("voice_dir") / f"{s['voice']}.mp3")]
    ms = int(round((starts[k] + s["delay"]) * 1000))
    fc.append(f"[{n_in + k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{k}]")
    labels.append(f"[n{k}]")
fc.append(f"{''.join(labels)}amix=inputs={len(SC)}:normalize=0,apad,atrim=0:{total:.3f},asplit=2[vo][sc]")

bi = n_in + len(SC)
bgm = c.path("bgm")
BL = dur_of(bgm)
A_END, CF = c["bgm_join"]["a_end"], c["bgm_join"]["crossfade"]
if BL >= total:
    fc.append(f"[{bi}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000[bj]")
    inp += ["-i", str(bgm)]
else:
    Y = max(15.0, min(A_END + BL - CF - total, A_END - 10))
    inp += ["-i", str(bgm), "-i", str(bgm)]
    fc.append(f"[{bi}:a]atrim=0:{A_END},asetpts=PTS-STARTPTS,aresample=48000[ba]")
    fc.append(f"[{bi + 1}:a]atrim={Y:.3f},asetpts=PTS-STARTPTS,aresample=48000[bb]")
    fc.append(f"[ba][bb]acrossfade=d={CF}:c1=tri:c2=tri[bj]")
    print(f"音樂延長：0–{A_END}s 接 {Y:.1f}s–結尾，重複段 {Y:.1f}–{A_END}s")
fc.append(f"[bj]atrim=0:{total:.3f},volume={c['bgm_volume']},afade=t=in:d=0.8,afade=t=out:st={total - 3:.3f}:d=3[bgm]")
fc.append("[bgm][sc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=450[duck]")
fc.append(f"[duck][vo]amix=inputs=2:normalize=0,loudnorm=I={c['loudness']}:TP=-1.5:LRA=11[aout]")

out = c.path("output")
out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", *inp, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
                "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", str(out)], check=True)
print("written", out)
