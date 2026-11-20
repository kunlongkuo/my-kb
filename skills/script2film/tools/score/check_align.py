"""段首對齊檢查：段首後 [0, +90 ms] 內有起音算命中，並與隨機時間點的基線比較。

用法：uv run python check_align.py <wav> <plan.json>    # 命中率 ≥ 0.8 且 ≥ 基線 + 0.3 → exit 0
"""
import json
import random
import sys

import librosa

WINDOW = 0.09


def hit_rate(onsets, times):
    return sum(bool(((onsets >= t) & (onsets <= t + WINDOW)).any()) for t in times) / len(times)


def main(wav, plan_path):
    plan = json.load(open(plan_path, encoding="utf-8"))
    y, sr = librosa.load(wav, sr=22050)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    starts = [s["start"] for s in plan["sections"]]
    for s, t in zip(plan["sections"], starts):
        after = onsets[onsets >= t]
        d = (after[0] - t) * 1000 if len(after) else float("inf")
        bpm = 60 * s["beats"] / (s["end"] - s["start"])
        print(f"{s['name'][:10]:10s} {t:7.2f}  {s['role']:7s} {s['beats']:3d} beats {bpm:5.1f} bpm  first onset after the section start +{d:5.0f} ms")
    rate = hit_rate(onsets, starts)
    rnd = random.Random(0)
    total = len(y) / sr
    base = hit_rate(onsets, [rnd.uniform(0, total - WINDOW) for _ in range(200)])
    ok = rate >= 0.8 and rate >= base + 0.3
    print(f"aligned {round(rate * len(starts))}/{len(starts)} (hit rate {rate:.2f}, baseline {base:.2f}) {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
