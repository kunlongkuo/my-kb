"""跟著畫面走的配樂：events → 分段計畫 → GeneralUser GS 離線渲染。

用法：
  uv run python score.py plan   events/<x>.json [--out plans/<x>.json]   # 自動編曲，產出可手改的計畫
  uv run python score.py render plans/<x>.json [--lufs -20] [--voice V.wav --video IN.mp4]
  uv run python score.py make   events/<x>.json [--lufs -20] [--voice V.wav --video IN.mp4]   # plan＋render
  uv run python score.py mux    IN.mp4 outputs/<x>.wav [--lufs -20] [--out OUT.mp4]   # 疊進影片，保留原音軌
  （四種都可以在子命令前加 --work <資料夾>；plans/、outputs/ 建在工作資料夾底下，順序見 paths.py）

--voice/--video：另出 outputs/<name>-preview.mp4，配樂壓到 -40 LUFS（旁白底下不搶話的音量）、
淡入淡出後和旁白混音，再對齊原片響度（只供試聽比較）。

計畫 JSON：style（devotion|story|scifi|lounge|bazaar，缺省 devotion）；sections[]：name、start、end（秒）、beats（整數）、
chords [[和弦, 拍數], ...]（拍數總和須等於 beats）、layers [聲部...]、gain_db、
melody [[拍位, MIDI, 拍數, 聲部(, "hit")], ...]（拍位相對段首）
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import tinysoundfont

from paths import soundfont, work_dir
from planner import PlanError, make_plan
from styles import SHAKER, STYLES, parse_chord

WORK = work_dir()   # main() replaces it when --work is given


def out_dir():
    d = WORK / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d

SR = 44100
BGM_LUFS = -40.0  # 試聽混音用：旁白底下的配樂音量
REVERB = "aecho=0.8:0.5:70|140|230:0.22|0.14|0.08"  # 輕殘響（tinysoundfont 沒有）

CHANNEL = {"motif": 0, "lead": 1, "harp": 2, "arp": 3, "pad": 4, "bass": 5}
ACCENT = 14
VEL = {"motif": 62, "lead": 64, "harp": 52, "arp": 46, "pad": 42, "bass": 58, "hit": 50}
# GM 鼓組（channel 9）；drums 聲部：verse 每拍大鼓＋反拍鈸，body 再加 2、4 拍小鼓；hits 打大鼓＋小鼓＋碎音鈸
DRUM = {"kick": 36, "snare": 38, "hat": 42, "crash": 49, "pedal": 44, "ride": 51, "bell": 53}
SWING = 2 / 3  # 搖擺八分音符：後半拍落在三連音第三個位置


def voicing(pcs, lo, hi):
    return [n for n in range(lo, hi + 1) if n % 12 in pcs]


def build_events(plan, rnd):
    ev = []
    sec_start = None

    def note(ch, key, t0, dur, vel):
        if abs(t0 - sec_start) < 1e-6 and ch not in (CHANNEL["pad"], CHANNEL["bass"]):
            vel += ACCENT  # 段首重音：讓換段聽得出來（pad、bass 起音慢，加了也聽不出）
        t0 += rnd.uniform(0, 0.012)
        vel = max(1, min(127, int(vel + rnd.randint(-5, 5))))
        ev.append((t0, 1, ch, key, vel))
        ev.append((t0 + dur * 0.96, 0, ch, key, 0))

    for s in plan["sections"]:
        sec_start = s["start"]
        spb = (s["end"] - s["start"]) / s["beats"]
        assert sum(b for _, b in s["chords"]) == s["beats"], f"{s['name']}: the chords' beats do not add up to beats"
        L = s["layers"]
        beat = 0
        for ci, (name, nb) in enumerate(s["chords"]):
            pcs, t, dur = parse_chord(name), s["start"] + beat * spb, nb * spb
            if "comp" in L:  # Rhodes 切分：每兩拍一組，正拍長音＋第二拍的搖擺後半拍短音
                v = voicing(pcs, 53, 67)[:4]
                for b in range(0, nb, 2):
                    for k in v:
                        note(CHANNEL["pad"], k, t + b * spb, 0.9 * spb, VEL["pad"] + 6)
                    if b + 1 < nb:
                        for k in v:
                            note(CHANNEL["pad"], k, t + (b + 1 + SWING) * spb, 0.5 * spb, VEL["pad"])
            if "walk" in L:  # 走路貝斯：每拍一音，第一拍根音、中間走和弦音、最後一拍半音接到下一個和弦根音
                nxt = parse_chord(s["chords"][ci + 1][0] if ci + 1 < len(s["chords"]) else name)[0]
                lo = [n for n in range(36, 56) if n % 12 in pcs]
                root = next(n for n in range(36, 48) if n % 12 == pcs[0])
                cur = root
                for b in range(nb):
                    if b == 0:
                        cur = root
                    elif b == nb - 1:
                        tgt = next(n for n in range(36, 48) if n % 12 == nxt)
                        cur = tgt + (1 if cur > tgt else -1)
                    else:
                        cur = min((n for n in lo if n != cur), key=lambda n: (abs(n - (root + 4 * b)), n))
                    note(CHANNEL["bass"], cur, t + b * spb, 0.85 * spb, VEL["bass"] - (0 if b == 0 else 6))
            if "pad" in L:
                for k in voicing(pcs, 55, 67):
                    note(CHANNEL["pad"], k, t, dur, VEL["pad"])
            if "bass" in L:
                note(CHANNEL["bass"], next(n for n in range(36, 48) if n % 12 == pcs[0]), t, dur, VEL["bass"])
            if "arp" in L:
                v = voicing(pcs, 52, 71)[:4]
                for e in range(nb * 2):
                    idx = [0, 1, 2, 3, 2, 1, 2, 1][e % 8]
                    note(CHANNEL["arp"], v[idx % len(v)], t + e * spb / 2, spb / 2, VEL["arp"] - (6 if e % 2 else 0))
            if "harp" in L:
                for e, k in enumerate(voicing(pcs, 59, 74)[:5]):
                    note(CHANNEL["harp"], k, t + e * spb / 4, nb * spb - e * spb / 4, VEL["harp"])
            beat += nb
        if "drums" in L:
            for b in range(s["beats"]):
                t = s["start"] + b * spb
                ev.append((t, 1, SHAKER["channel"], DRUM["kick"], 96))
                ev.append((t + spb / 2, 1, SHAKER["channel"], DRUM["hat"], 54))
                if s["role"] == "body" and b % 2:
                    ev.append((t, 1, SHAKER["channel"], DRUM["snare"], 84))
        if "swing" in L:  # 鼓刷：ride 每拍＋第 2、4 拍前的搖擺切音，踏鈸在 2、4 拍
            for b in range(s["beats"]):
                t = s["start"] + b * spb
                ev.append((t, 1, SHAKER["channel"], DRUM["ride"], 46 if b % 2 else 40))
                if b % 2:
                    ev.append((t - (1 - SWING) * spb, 1, SHAKER["channel"], DRUM["ride"], 30))
                    ev.append((t, 1, SHAKER["channel"], DRUM["pedal"], 44))
        if {"comp", "walk", "swing"} & set(L):  # 換段：ride 鈴一聲，讓段首起音清楚
            ev.append((s["start"], 1, SHAKER["channel"], DRUM["bell"], 64))
        if "shaker" in L:
            for e in range(s["beats"] * 2):
                vel = SHAKER["vel_off"] if e % 2 else SHAKER["vel_on"]
                ev.append((s["start"] + e * spb / 2, 1, SHAKER["channel"], SHAKER["key"], vel))
        for m in s.get("melody", []):
            b, key, nb, layer = m[:4]
            vel = VEL["hit"] if m[4:] == ["hit"] else VEL[layer]
            note(CHANNEL[layer], key, s["start"] + b * spb, nb * spb, vel)
            if m[4:] == ["hit"] and "drum_roles" in STYLES[plan.get("style", "devotion")]:
                for k, v in (("kick", 124), ("snare", 110), ("crash", 104)):
                    ev.append((s["start"] + b * spb, 1, SHAKER["channel"], DRUM[k], v))
    ev.sort(key=lambda e: (e[0], e[1]))
    return ev


def gain_curve(plan, n, ramp=0.6):
    """依各段 gain_db 做音量包絡，段與段之間 ramp 秒線性過渡。"""
    t = np.arange(n) / SR
    xs, ys = [], []
    for s in plan["sections"]:
        xs += [s["start"], s["end"] - ramp]
        ys += [s["gain_db"]] * 2
    db = np.interp(t, xs, ys)
    return (10 ** (db / 20)).astype(np.float32)


def total_of(plan):
    return plan["sections"][-1]["end"] + plan.get("tail", 0)


def synth(plan, seed=7):
    programs = STYLES[plan.get("style", "devotion")]["programs"]
    syn = tinysoundfont.Synth(samplerate=SR, gain=-6)
    sfid = syn.sfload(str(soundfont()))
    for layer, ch in CHANNEL.items():
        syn.program_select(ch, sfid, 0, programs[layer])
    kit = STYLES[plan.get("style", "devotion")].get("drum_kit", 0)
    syn.program_select(SHAKER["channel"], sfid, SHAKER["bank"], kit, is_drums=True)
    total = total_of(plan)
    chunks, now = [], 0.0
    for t, on, ch, key, vel in build_events(plan, random.Random(seed)) + [(total, -1, 0, 0, 0)]:
        n = int((t - now) * SR)
        if n > 0:
            chunks.append(np.frombuffer(syn.generate(n), dtype=np.float32).reshape(-1, 2).copy())
            now += n / SR
        if on == 1:
            syn.noteon(ch, key, vel)
        elif on == 0 and ch != SHAKER["channel"]:
            syn.noteoff(ch, key)
    y = np.concatenate(chunks)[: int(total * SR)]
    y *= gain_curve(plan, len(y))[:, None]
    return y / (np.abs(y).max() + 1e-9) * 0.7


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout)


def has_audio(path):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip())


def loudness(path):
    """整體響度（LUFS），用 ffmpeg loudnorm 量測。"""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "loudnorm=print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.JSONDecoder().raw_decode(err[err.rindex("{"):])[0]["input_i"])


def render(plan, lufs=None):
    """dry → 殘響 → 截到計畫長度 →（可選）線性調到目標響度。回傳 wav 路徑。"""
    wav = out_dir() / f"{plan['name']}.wav"
    dry = out_dir() / f"{plan['name']}-dry.wav"
    sf.write(dry, synth(plan), SR)
    ff("-i", dry, "-af", f"{REVERB},atrim=0:{total_of(plan):.4f}", wav)
    dry.unlink()
    if lufs is not None:
        tmp = out_dir() / f"{plan['name']}-pre.wav"
        wav.rename(tmp)
        ff("-i", tmp, "-af", f"volume={lufs - loudness(tmp):.2f}dB", wav)
        tmp.unlink()
    print(f"{wav.name}  {duration(wav):.2f}s")
    return wav


def preview(wav, voice, video, out):
    """試聽混音：配樂壓到 -40 LUFS、1.5s 淡入、3s 淡出，和旁白 amix（normalize=0），再對齊原片響度換掉影片音軌。"""
    total = duration(video)
    gain = BGM_LUFS - loudness(wav)
    af = (f"[0:a]volume={gain:.1f}dB,"
          f"atrim=0:{total:.3f},afade=t=in:d=1.5,afade=t=out:st={total - 3:.3f}:d=3[b];"
          f"[1:a][b]amix=inputs=2:duration=longest:normalize=0[a]")
    raw = out.with_name(out.stem + "-raw.wav")
    ff("-i", wav, "-i", voice, "-filter_complex", af, "-map", "[a]", "-t", f"{total:.3f}", raw)
    # 成片經剪輯軟體匯出後整體響度被拉高；對齊原片響度才能公平比較
    lift = loudness(video) - loudness(raw)
    ff("-i", video, "-i", raw, "-map", "0:v", "-map", "1:a", "-af", f"volume={lift:.1f}dB,alimiter=limit=0.95:level=false",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out)
    raw.unlink()
    print(out.name)


def mux(video, wav, out, lufs=None):
    """配樂疊進影片：原本有音軌就 amix（normalize=0）保留，沒有就直接放；畫面 stream copy。"""
    total = duration(video)
    gain = f"volume={lufs - loudness(wav):.2f}dB," if lufs is not None else ""
    bgm = f"[1:a]{gain}atrim=0:{total:.3f},afade=t=in:d=0.3,afade=t=out:st={max(total - 1.5, 0):.3f}:d=1.5"
    if has_audio(video):
        fc = f"{bgm}[b];[0:a][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]"  # 兩軌相加會過 0 dBFS；留 1 dB 給 AAC 編碼過衝
    else:
        fc = f"{bgm},apad=whole_dur={total:.3f}[a]"
    ff("-i", video, "-i", wav, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", out)
    print(f"{Path(out).name}  {duration(out):.2f}s")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_plan(plan, out):
    out = Path(out) if out else WORK / "plans" / f"{plan['name']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", help="work folder for plans/ and outputs/ (default: $S2F_SCORE_WORK, else ./score_out)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("events")
    p.add_argument("--out")
    for name in ("render", "make"):
        r = sub.add_parser(name)
        r.add_argument("src")
        r.add_argument("--lufs", type=float)
        r.add_argument("--voice")
        r.add_argument("--video")
        if name == "make":
            r.add_argument("--plan-out")
    m = sub.add_parser("mux")
    m.add_argument("video")
    m.add_argument("wav")
    m.add_argument("--lufs", type=float)
    m.add_argument("--out")
    a = ap.parse_args()
    global WORK
    WORK = work_dir(a.work)

    try:
        if a.cmd == "plan":
            write_plan(make_plan(load(a.events)), a.out)
            return
        if a.cmd == "mux":
            out = Path(a.out) if a.out else out_dir() / f"{Path(a.video).stem}-score.mp4"
            mux(a.video, a.wav, out, a.lufs)
            return
        if a.cmd == "make":
            plan = make_plan(load(a.src))
            write_plan(plan, a.plan_out)
        else:
            plan = load(a.src)
        wav = render(plan, a.lufs)
        if a.voice and a.video:
            preview(wav, a.voice, a.video, out_dir() / f"{plan['name']}-preview.mp4")
    except PlanError as e:
        sys.exit(f"events error: {e}")


if __name__ == "__main__":
    main()
