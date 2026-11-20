"""VE 片段 → 組裝輸出（assemble.py：畫面軌換進 HTML 殼）與 Concat 用的 plan.json（cut2plan.py）的共用邏輯。

專案設定檔（ve-project.json）的路徑一律相對於設定檔所在資料夾：

{
  "clips": "ve-runs/<run>/picks",            # shotN.mp4
  "srt": "../<配音專案>/voice.cleaned/final.srt",
  "out": "<輸出資料夾>",
  "stepped_fps": 8,                          # 抽格頓挫；0 = 不抽格（停格動畫素材本身就是一頓一頓的）
  "shots": {"shot1": 1, "shot2": 2, "shot5": "16.84s", ...},
      # 每鏡從第幾句字幕開始（整數＝字幕句號）；要在句中換鏡就寫秒數字串 "16.84s"。
      # 第一鏡一律從 0 秒起，每鏡到下一鏡開始為止，最後一鏡到最後一句字幕結束。
  "shell": {"dir": "...", "copy": ["index.html", ...], "video_src": "shadow_visual.mp4"},
  "timeline": {"name": "...", "lines": ".../tts/lines.json", "audio": "voice.cleaned/audio.m4a",
               "lead_s": 0.45, "width": 1920, "height": 1080, "fps": 30,
               "extra_audios": [{"path": "sfx/impact.wav", "start_s": 28.02, "track": "音效"}]}   # 選用：音效等額外音軌
}

段落模式：把 "shots" 換成 "sequence"，照順序列段落（旁白段和對白段可以交錯）：
  "sequence": [
    {"voice": [1, 1], "shots": {"shot1": 1}},            # 旁白段：Qwen 配音第 1～1 句字幕的區間，段內各鏡同上切法
    {"clip": "ve-runs/.../D1.mp4", "speaker": "小美", "text": "「下午的茶葉……」"},   # 對白段：整支片，畫面和聲音都用它的
    {"clip": "...", "speaker": "阿明、小美", "text": ["「喝茶。」", "「初五。」"]},       # 兩人同鏡：每段講話一句字幕
    {"voice": [4, 6], "shots": {"shot3": 4, "shot4": 5, "shot5": "16.84s"}},
    ...
  ]
  字幕時間是辨識出來的、句首可能晚近一秒，所以先把字幕對齊配音表（timeline.lines／lead_s）每句實際出聲的區間（retime_cues），
  旁白段的切點與字幕都用對齊後的時間；段內各鏡的換鏡點仍照原字幕。
  對白段的字幕放在片子裡實際講話的區間（靜音偵測）；text 是清單時，講話段數要剛好等於句數，依序各放一句；句中有停頓時用 "cut" 指定換人的秒數。可選："ambience_gain"（各鏡自帶環境音的音量，預設 1.0）、
  段落層的 "stepped_fps"、"max_stretch"（旁白段裡片子比鏡窗短時最多放慢幾倍，預設 1＝不放慢、直接凍結末格；對白段不放慢）。輸出多了 mix.m4a（混好的聲音）、subtitles.srt、sequence.json，殼裡的字幕時間表與長度會改寫。
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def _sec(stamp: str) -> float:
    h, m, s, ms = TIME.fullmatch(stamp.strip()).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 10 ** len(ms)


def parse_srt(text: str) -> list[tuple[int, float, float, str]]:
    """[(句號, 起秒, 迄秒, 文字)]，依句號排序。"""
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [s for s in block.strip().splitlines() if s.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        a, b = lines[1].split("-->")
        cues.append((int(lines[0]), _sec(a), _sec(b), "\n".join(lines[2:])))
    return sorted(cues)


def shot_windows(cues: list[tuple[int, float, float, str]], shots: dict[str, int | str],
                 start: float = 0.0, end: float | None = None) -> list[tuple[str, float, float]]:
    """每鏡的 (名稱, 起秒, 迄秒)。shots 依鏡頭順序；值是字幕句號或 "<秒>s"。
    第一鏡從 start 起（預設 0），最後一鏡到 end（預設最後一句字幕結束）。"""
    if not shots:
        raise ValueError("shots is empty")
    by_n = {c[0]: c for c in cues}
    starts = []
    for name, v in shots.items():
        if isinstance(v, bool):
            raise ValueError(f"{name}: {v!r} is not a subtitle line number or seconds")
        if isinstance(v, int):
            if v not in by_n:
                raise ValueError(f"{name}: the subtitles have no line {v}")
            starts.append(by_n[v][1])
        elif isinstance(v, str) and re.fullmatch(r"\d+(\.\d+)?s", v):
            starts.append(float(v[:-1]))
        else:
            raise ValueError(f"{name}: {v!r} must be a subtitle line number (integer) or a seconds string (such as \"16.84s\")")
    starts[0] = start
    end = cues[-1][2] if end is None else end
    for (name, _), a, b in zip(shots.items(), starts, starts[1:] + [end]):
        if not a < b:
            raise ValueError(f"{name}: start {a:.2f}s is not before the next shot's start {b:.2f}s (wrong shot order or line number?)")
    return [(name, a, b) for (name, _), a, b in zip(shots.items(), starts, starts[1:] + [end])]


def segment_frames(a: float, b: float, fps: int = 24) -> int:
    """以累計格數切段：每段終點對齊句界，多段串接不漂移。"""
    return round(b * fps) - round(a * fps)


def line_cuts(lines: list[dict], total: float, lead: float) -> list[tuple[dict, float, float]]:
    """把一條配音切成每句一段：切在兩句間空白的中點，首段從 0、末段到 total，整條無縫。
    lines 是 TTS 的 lines.json（start/end 以配音本身計時）；lead 是配音檔前面多墊的靜音秒數。"""
    out = []
    for i, line in enumerate(lines):
        a = 0.0 if i == 0 else lead + (lines[i - 1]["end"] + line["start"]) / 2
        b = total if i == len(lines) - 1 else lead + (line["end"] + lines[i + 1]["start"]) / 2
        if not a < b:
            raise ValueError(f"line {line.get('n', i + 1)}: cut points out of order: {a:.3f}–{b:.3f}")
        out.append((line, a, b))
    return out


def load_config(path: str | Path) -> tuple[dict, Path]:
    p = Path(path).resolve()
    return json.loads(p.read_text(encoding="utf-8")), p.parent


def timeline_cfg(cfg: dict) -> dict:
    """設定檔的時間軸區塊：有 "timeline" 用它，沒有才用舊名 "capcut"（相容讀法），兩個都沒有回 {}。"""
    if "timeline" in cfg:
        return cfg["timeline"]
    return cfg.get("capcut", {})


def duration(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(path)], capture_output=True, text=True, check=True).stdout)


# ---- sequence mode: 旁白段（Qwen 配音的一段）與對白段（自帶聲音的片子）依序排

def block_bounds(cues: list[tuple[int, float, float, str]], first: int, last: int, cuts: list[float],
                 end: float) -> tuple[float, float]:
    """旁白段 [first, last] 句在配音裡的區間。cues 要用對齊過配音表的字幕（retime_cues），cuts 是配音表的句界（line_boundaries）。
    起點：first 句開頭之前最近的句界（若是第一句則從 0）；迄點：下一句字幕開頭之前最近的句界（若 last 是最後一句則到 end）。
    字幕開頭已對齊到實際出聲，所以「之前最近的句界」就是前一句配音與這一句之間空白的中點。"""
    by_n = {c[0]: c for c in cues}
    for n in (first, last):
        if n not in by_n:
            raise ValueError(f"the subtitles have no line {n}")
    if first > last:
        raise ValueError(f"narration block first line {first} is after its last line {last}")

    def before(t):
        return max([0.0] + [c for c in cuts if c <= t])
    start = 0.0 if first == cues[0][0] else before(by_n[first][1])
    nxt = [c for c in cues if c[0] > last]
    stop = before(nxt[0][1]) if nxt else end
    if not start < stop:
        raise ValueError(f"narration block {first}-{last}: span out of order: {start:.3f}–{stop:.3f}")
    return start, stop


def shift_cues(cues: list[tuple[int, float, float, str]], start: float, end: float, offset: float) -> list[tuple[float, float, str]]:
    """把落在 [start, end) 的字幕平移到成片時間 offset 起；結束時間不超過段尾。"""
    out = []
    for _, a, b, text in cues:
        if start <= a < end:
            out.append((round(a - start + offset, 3), round(min(b, end) - start + offset, 3), text))
    return out


SIL = re.compile(r"silence_(start|end): ([0-9.]+)")


def speech_span(silencedetect_log: str, duration: float) -> tuple[float, float]:
    """ffmpeg silencedetect 的輸出 → 片子裡講話的 (起, 迄)。開頭的靜音結束處是起點；延續到片尾的靜音開始處是迄點。
    沒有偵測到靜音就整支都算。"""
    ev = [(k, float(v)) for k, v in SIL.findall(silencedetect_log)]
    s, e = 0.0, duration
    if ev and ev[0] == ("start", ev[0][1]) and ev[0][1] < 0.05 and len(ev) > 1 and ev[1][0] == "end":
        s = ev[1][1]
    starts = [v for k, v in ev if k == "start"]
    if starts:
        last = starts[-1]
        ended = [v for k, v in ev if k == "end" and v > last]
        if last > s and (not ended or ended[0] >= duration - 0.05):
            e = last
    return round(s, 3), round(e, 3)


def stretch_factor(have: float, need: float, cap: float) -> float:
    """片段比鏡窗短時要放慢幾倍：剛好填滿，但不超過 cap（cap=1 不放慢）；放到上限仍不夠的部分由凍結末格補。"""
    if cap < 1:
        raise ValueError(f"max_stretch cannot be less than 1: {cap}")
    return 1.0 if need <= have else min(cap, round(need / have, 4))


def clamp(a: float, b: float, lo: float, hi: float) -> tuple[float, float] | None:
    """(a, b) 與 [lo, hi] 的交集；沒有交集回 None。"""
    x, y = max(a, lo), min(b, hi)
    return (x, y) if y > x else None


def line_boundaries(lines: list[dict], lead: float) -> list[float]:
    """配音表裡相鄰兩句之間的切點（前一句結束與下一句開始的中點，加上配音檔前面墊的靜音），和 line_cuts 一致。"""
    return [round(lead + (a["end"] + b["start"]) / 2, 3) for a, b in zip(lines, lines[1:])]


def silences(silencedetect_log: str, duration: float) -> list[tuple[float, float]]:
    """ffmpeg silencedetect 的輸出 → [(靜音起, 靜音迄)]；最後一段沒有結束（延續到檔尾）就以 duration 收。"""
    out, start = [], None
    for k, v in SIL.findall(silencedetect_log):
        if k == "start":
            start = float(v)
        elif start is not None:
            out.append((start, float(v)))
            start = None
    if start is not None:
        out.append((start, duration))
    return out


def speech_bounds(lines: list[dict], lead: float, sil: list[tuple[float, float]], duration: float,
                  tol: float = 0.05) -> list[tuple[float, float]]:
    """配音表每句實際出聲的 (起, 迄)。TTS 每句前面常帶 0.3-1 秒靜音，所以 start 落在某段靜音裡時，改用那段靜音的結束；
    end 落在靜音裡時，改用那段靜音的開始。沒落在靜音裡就用配音表的值。"""
    def inside(t):
        return next(((a, b) for a, b in sil if a - tol <= t <= b + tol), None)
    out = []
    for line in lines:
        a, b = lead + line["start"], min(lead + line["end"], duration)
        s, e = inside(a), inside(b)
        a2, b2 = (s[1] if s else a), (e[0] if e else b)
        out.append((round(a2, 3), round(b2, 3)) if b2 > a2 else (round(a, 3), round(b, 3)))
    return out


def retime_cues(cues: list[tuple[int, float, float, str]], lines: list[dict], lead: float,
                bounds: list[tuple[float, float]]) -> list[tuple[int, float, float, str]]:
    """字幕時間改對齊配音表。語音辨識的錯在句首（一支短劇實測晚 0.3-0.9 秒）與句尾（延伸到下一句開頭）；
    句中換行的時間點和實際停頓幾乎相同（實測差 0.01-0.08 秒），所以不動。
    做法：每句字幕依「開始時間」歸到配音表的某一句（以 line_boundaries 為界）；配音表裡沒有字幕開頭的句子併入前一組
    （一句字幕跨兩句配音的情形）。每組第一句字幕的開始改成該組配音實際出聲的起點、最後一句的結束改成出聲的迄點，
    中間的時間點沿用辨識結果，只夾在這個區間內。"""
    import bisect
    cuts = line_boundaries(lines, lead)
    owner = [bisect.bisect_right(cuts, c[1]) for c in cues]
    if owner[0] != 0:
        raise ValueError(f"voice line 1 matches no subtitle (the first subtitle line starts only at {cues[0][1]:.2f}s)")
    heads = sorted(set(owner))
    out = []
    for g, head in enumerate(heads):
        tail = (heads[g + 1] if g + 1 < len(heads) else len(lines)) - 1
        group = [c for c, o in zip(cues, owner) if o == head]
        y0, y1 = bounds[head][0], bounds[tail][1]
        for j, (n, a, b, text) in enumerate(group):
            a2 = y0 if j == 0 else min(max(a, y0), y1)
            b2 = y1 if j == len(group) - 1 else min(max(b, y0), y1)
            if not a2 < b2:
                raise ValueError(f"subtitle line {n} has a non-positive length after alignment: {a2:.3f}–{b2:.3f}")
            out.append((n, round(a2, 3), round(b2, 3), text))
    return out


def speech_spans(sil: list[tuple[float, float]], duration: float, min_len: float = 0.15) -> list[tuple[float, float]]:
    """靜音區間 → 講話區間（兩段靜音之間、長度至少 min_len 秒）。"""
    out, t = [], 0.0
    for a, b in sil:
        if a - t >= min_len:
            out.append((round(t, 3), round(a, 3)))
        t = max(t, b)
    if duration - t >= min_len:
        out.append((round(t, 3), round(duration, 3)))
    return out


def splice_cuts(spans: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    """每段講話分到的聲音區間：切在兩段講話之間空白的中點，首段從 0、末段到片尾，整條無縫。"""
    mids = [round((a[1] + b[0]) / 2, 3) for a, b in zip(spans, spans[1:])]
    return list(zip([0.0] + mids, mids + [round(duration, 3)]))
