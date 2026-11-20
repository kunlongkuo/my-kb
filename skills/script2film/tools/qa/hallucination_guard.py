#!/usr/bin/env python3
"""轉錄幻覺守衛：靜音上冒出來的字。

Whisper 系的轉錄在靜音段會「補字」：片尾靜音冒出「謝謝觀看」「字幕由…提供」這類套語。檢查吞字的防線抓不到
這種多出來的字。靜音的量法（ffmpeg silencedetect，-35 dB、0.6 秒）取自 HyperFrames 的 embedded-captions skill
（Apache-2.0，見 NOTICE.md）。

判定（只用 ffmpeg 量到的靜音段，不另設比例門檻）：
  - 整句落在某段靜音裡               → 疑似幻覺，列出來讓人判（不自動刪：可能是極小聲的真話）
  - 句子開始於「延伸到檔尾的靜音」之後 → 片尾幻覺，--apply 時直接刪
silencedetect 看峰值，底噪高的錄音可能整片量不到靜音；那時這支等於沒跑，會印出來。

兩種用法：
  獨立工具（字幕是轉錄出來的）：
    python3 tools/qa/hallucination_guard.py --audio audio.m4a --srt final.srt [--apply] [--out final.srt]
  doc 模式（字幕來自稿子，轉錄只用來對時）：doc_align.py 呼叫 tail_words()，只用「檔尾」那一條、只列不刪。
    「整個字落在靜音裡」不用在逐字時間上：句尾的字常被拉進停頓，實測兩集共 55 個全是誤報。
"""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path

NOISE_DB = -35
MIN_SILENCE_S = 0.6
EPS = 0.05   # 時間戳取整誤差


def parse_silencedetect(log: str, duration: float):
    """ffmpeg silencedetect 的 stderr → [(start, end)]；最後一段沒有 silence_end＝延伸到檔尾。"""
    spans, start = [], None
    for line in log.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and start is not None:
            spans.append((start, float(m.group(1))))
            start = None
    if start is not None:
        spans.append((start, duration))
    return spans


def classify(segs, silences, duration: float):
    """segs: [{idx,start,end,text}] → (suspect, trailing)；一句只會落在其中一邊。"""
    tail_start = next((s for s, e in silences if e >= duration - EPS), None)
    suspect, trailing = [], []
    for seg in segs:
        if tail_start is not None and seg["start"] >= tail_start - EPS:
            trailing.append(seg)
        elif any(s - EPS <= seg["start"] and seg["end"] <= e + EPS for s, e in silences):
            suspect.append(seg)
    return suspect, trailing


def tail_words(words, silences, duration: float):
    """words: [{start, end, text}] → 開始在「延伸到檔尾的靜音」之後的那些字；沒有這樣的靜音就是空串列。"""
    return classify(words, silences, duration)[1]


def parse_srt(text: str):
    segs = []
    for b in re.split(r"\n\s*\n", text.strip()):
        lines = b.strip().split("\n")
        if len(lines) < 2:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1])
        if not m:
            continue
        t = [int(x) for x in m.groups()]
        segs.append({"idx": int(lines[0]) if lines[0].strip().isdigit() else None,
                     "start": t[0] * 3600 + t[1] * 60 + t[2] + t[3] / 1000,
                     "end": t[4] * 3600 + t[5] * 60 + t[6] + t[7] / 1000,
                     "text": "\n".join(lines[2:]).strip(), "time": lines[1].strip()})
    return segs


def render_srt(segs) -> str:
    return "".join(f"{i}\n{s['time']}\n{s['text']}\n\n" for i, s in enumerate(segs, 1))


def detect(audio: Path):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)],
                               capture_output=True, text=True, check=True).stdout.strip())
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio), "-af",
                          f"silencedetect=noise={NOISE_DB}dB:d={MIN_SILENCE_S}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return parse_silencedetect(log, dur), dur


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Transcription hallucination guard: subtitles that sit on silence (ffmpeg silencedetect, -35 dB, 0.6 s). A line wholly inside a silence is listed; a line that starts after the silence running to the end of the file is removed with --apply.")
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--srt", type=Path, required=True)
    ap.add_argument("--apply", action="store_true", help="remove the subtitles on the closing silence (suspect lines are only listed)")
    ap.add_argument("--out", type=Path, help="default: overwrite --srt")
    a = ap.parse_args(argv)
    segs = parse_srt(a.srt.read_text(encoding="utf-8"))
    silences, dur = detect(a.audio)
    if not silences:
        print(f"hallucination guard: no silence found at {NOISE_DB}dB / {MIN_SILENCE_S}s (high noise floor?), so it did nothing this time; check the ending by eye")
        return 0
    suspect, trailing = classify(segs, silences, dur)
    for s in suspect:
        print(f"  ⚠ suspected hallucination (the whole line is inside a silence) #{s['idx']} {s['time']} \"{s['text']}\": listen, and delete it if it is not real")
    for s in trailing:
        print(f"  ✗ subtitle on the closing silence #{s['idx']} {s['time']} \"{s['text']}\" " + ("→ removed" if a.apply else "→ add --apply to remove it"))
    if a.apply and trailing:
        keep = [s for s in segs if s not in trailing]
        (a.out or a.srt).write_text(render_srt(keep), encoding="utf-8")
    if not suspect and not trailing:
        print(f"hallucination guard: {len(silences)} silences, no subtitles on them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
