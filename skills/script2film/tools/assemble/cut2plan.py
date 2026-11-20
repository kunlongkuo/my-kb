"""組裝輸出（cut_<theme>.json 與它的輸出資料夾）→ plan.json，給 plan2concat_mcp.py 用，不經剪映草稿。

  python3 tools/assemble/cut2plan.py <cut_<theme>.json> [<plan.json>]     # 預設寫到 <out>/plan.json

對應草稿那一層的做法（s2f-1b design.md D1、D2）：
- 影片軌：設定檔 shots 的順序，一鏡一段 <out>/.segments/<鏡>.mp4；每段 dur＝ffprobe format.duration 向上取整到毫秒，
  起點＝前面各段 dur 的累加。
- 旁白：cut_voice() 切成一句一個 wav，一位講者一軌，依第一次出現的順序。
  旁白與額外音軌的 dur 取最接近的毫秒（剛好一半取偶數），和影片的向上取整不同，見 dur_ms()。
- 額外音軌：timeline.extra_audios，依 track 欄第一次出現的順序各一軌。
- 字幕：<out>/voice.cleaned/final.srt，y 固定 -0.8；有 timeline.sub_bg 時 bg、bga 取自它，沒有時是 null、1.0。
- 音量：單聲道素材 ×√2（取 4 位小數），其餘 1.0。
- 路徑：一律 normpath 後的絕對路徑，指到檔案原本的位置。
- total：影片軌與所有音訊片段結束時間的最大值。
段落模式（設定檔有 sequence）不支援：那種設定檔用 assemble.py 組裝。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import ROUND_CEILING, ROUND_HALF_EVEN, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from velib import clamp, duration, line_cuts, load_config, parse_srt, shot_windows, timeline_cfg  # noqa: E402

USAGE = """Assembly output (cut_<theme>.json and its output folder) -> plan.json for plan2concat_mcp.py, no CapCut draft.

  python3 tools/assemble/cut2plan.py <cut_<theme>.json> [<plan.json>]     # default: <out>/plan.json

Same approach as the draft layer (s2f-1b design.md D1, D2):
- Video track: the order of shots in the config, one segment per shot <out>/.segments/<shot>.mp4; each dur = ffprobe
  format.duration rounded up to the millisecond, start = the sum of the earlier durs.
- Narration: cut_voice() cuts one wav per line, one track per speaker, in order of first appearance.
  Narration and extra audio dur is rounded to the nearest millisecond (half to even), unlike the video's round-up; see dur_ms().
- Extra audio: timeline.extra_audios, one track per track field value, in order of first appearance.
- Subtitles: <out>/voice.cleaned/final.srt, y fixed at -0.8; bg and bga from timeline.sub_bg if present, else null and 1.0.
- Volume: mono media x√2 (4 decimals), everything else 1.0.
- Paths: always normpath'd absolute paths to where the files are.
- total: the latest end time of the video track and all audio segments.
Block mode (a config with sequence) is not supported: assemble such configs with assemble.py.
"""

SUB_Y = -0.8


def cut_voice(cc: dict, base: Path, out: Path, blocks: list[dict] | None = None) -> list[dict]:
    """配音依句切段、依講者分軌。blocks（段落模式的旁白段）給定時，只留落在旁白段裡的部分，並換算成成片時間；
    被對白段取代的句子就不會出現。"""
    src = out / cc["audio"]
    lines = json.loads((base / cc["lines"]).read_text(encoding="utf-8"))
    vdir = out / "voice_lines"
    vdir.mkdir(exist_ok=True)
    spans = [(0.0, float("inf"), 0.0)] if blocks is None else \
        [(round(b["src_start"] * 24) / 24, round(b["src_end"] * 24) / 24, b["offset"]) for b in blocks]
    segs = []
    for line, a, b in line_cuts(lines, duration(src), float(cc.get("lead_s", 0))):
        for k, (lo, hi, offset) in enumerate(spans):
            part = clamp(a, b, lo, hi)
            if not part or part[1] - part[0] < 0.05:  # 段落邊界對齊到格時留下的句間碎片（靜音）不放
                continue
            x, y = part
            f = vdir / (f"{line['n']:02d}_{line['speaker']}.wav" if blocks is None else f"{line['n']:02d}_{line['speaker']}_b{k}.wav")
            # 以取樣點切；尾端少 1ms（48 個取樣）：相鄰段首尾相接時，秒→微秒的四捨五入會讓兩段重疊不到 1µs，CapCut 草稿會拒收
            sa, sb = round(x * 48000), round(y * 48000) - 48
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                            f"atrim=start_sample={sa}:end_sample={sb},asetpts=PTS-STARTPTS",
                            "-c:a", "pcm_s16le", "-ar", "48000", str(f)], check=True)
            segs.append({"path": str(f), "start_us": round((offset + x - lo) * 1e6), "track": f"配音-{line['speaker']}"})
    return segs


def probe(p):
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True).stdout)
    v = next((s for s in j['streams'] if s['codec_type'] == 'video'), None); a = next((s for s in j['streams'] if s['codec_type'] == 'audio'), None)
    m = {'path': p, 'name': os.path.basename(p), 'kind': 'video' if v else 'audio', 'hasAudio': bool(a), 'duration': float(j['format']['duration'])}
    if v: m.update(width=v['width'], height=v['height'], frameRateFraction=v['r_frame_rate'], videoCodec=v['codec_name'])
    if a: m.update(audioCodec=a['codec_name'], audioTracks=[{'index': a['index'], 'channels': a['channels'], 'sampleRate': int(a['sample_rate']), 'codec': a['codec_name']}])
    return m


def dur_ms(path: str, up: bool = True) -> int:
    """ffprobe 印出的 format.duration 用 Decimal 取整到整數毫秒（浮點數 16.1*1000 會多出尾數）。

    影片向上取整、聲音取最接近的毫秒（剛好一半時取偶數）：照剪映草稿那條路的實際結果定的（它的長度來自
    MediaInfo 的軌道長度）。四集 139 段影片都等於向上取整；長度不是整數毫秒的聲音片段共 5 段，向上取整對 2 段、
    向下取整對 3 段，取最接近且一半取偶數 5 段全對。"""
    s = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True).stdout.strip()
    return int((Decimal(s) * 1000).to_integral_value(rounding=ROUND_CEILING if up else ROUND_HALF_EVEN))


def norm(p: Path | str) -> str:
    return os.path.normpath(os.path.abspath(str(p)))


def build(cfg_path: str) -> tuple[dict, Path]:
    """回傳 (plan, 輸出資料夾)。"""
    cfg, base = load_config(cfg_path)
    if "sequence" in cfg:
        sys.exit("✗ cut2plan.py does not support block mode (a config with sequence) and cannot write plan.json; assemble such configs with tools/assemble/assemble.py")
    cc, out = timeline_cfg(cfg), base / cfg["out"]
    if not cc:
        sys.exit(f"✗ {cfg_path} has no timeline block (or its old name, capcut)")
    windows = shot_windows(parse_srt((base / cfg["srt"]).read_text(encoding="utf-8")), cfg["shots"])
    videos = [norm(out / ".segments" / f"{n}.mp4") for n, _, _ in windows]
    srt = out / "voice.cleaned" / "final.srt"
    extras = [(norm(out / x["path"]), float(x["start_s"]), x.get("track", "音效")) for x in cc.get("extra_audios", [])]
    missing = [p for p in videos + [str(srt)] + [e[0] for e in extras] if not os.path.exists(p)]
    if missing:
        sys.exit("✗ missing media (run the assembly first): " + "; ".join(missing))

    media: dict[str, dict] = {}
    ends_ms: list[int] = []

    def av_seg(path: str, start_s: float, dur: int) -> dict:
        if path not in media:
            media[path] = probe(path)
        mono = media[path].get('audioTracks', [{}])[0].get('channels') == 1
        start = round(start_s, 3)
        ends_ms.append(round(start * 1000) + dur)
        return {"path": path, "name": os.path.basename(path), "start": start, "dur": dur / 1000, "src": 0.0,
                "vol": round(1.0 * (2 ** 0.5 if mono else 1.0), 4)}

    # ①影片軌：起點用整數毫秒累加，避免浮點數累積誤差
    vsegs, acc = [], 0
    for p in videos:
        d = dur_ms(p)
        vsegs.append(av_seg(p, acc / 1000, d))
        acc += d

    # ④字幕
    sb = cc.get("sub_bg")
    tsegs = [{"text": text, "start": round(a, 3), "end": round(b, 3), "y": SUB_Y,
              "bg": sb.get("color") if sb else None, "bga": sb.get("alpha", 1.0) if sb else 1.0}
             for _, a, b, text in parse_srt(srt.read_text(encoding="utf-8"))]

    # ②旁白與額外音軌：依 track 第一次出現的順序分軌
    audios = [(norm(s["path"]), s["start_us"], s["track"]) for s in cut_voice(cc, base, out)]
    audios += [(p, round(st * 1e6), track) for p, st, track in extras]
    groups: dict[str, list[dict]] = {}
    for p, start_us, track in audios:
        groups.setdefault(track, []).append(av_seg(p, start_us / 1_000_000, dur_ms(p, up=False)))

    tracks = [{"type": "video", "segs": vsegs}, {"type": "text", "segs": tsegs}]
    tracks += [{"type": "audio", "segs": segs} for segs in groups.values()]
    plan = {"total": max(ends_ms) / 1000, "width": cc.get("width", 1920), "height": cc.get("height", 1080),
            "fps": round(cc.get("fps", 30)), "media": list(media.values()), "tracks": tracks}
    return plan, out


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 2):
        sys.stderr.write(USAGE)
        return 2
    plan, out = build(argv[0])
    dst = Path(argv[1]) if len(argv) == 2 else out / "plan.json"
    dst.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    print(dst, len(plan["media"]), "media;", [(t["type"], len(t["segs"])) for t in plan["tracks"]], "total", plan["total"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
