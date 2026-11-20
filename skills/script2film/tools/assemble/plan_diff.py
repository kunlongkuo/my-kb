"""比對兩份 plan.json（plan2concat_mcp.py 的輸入）是否等價。

  python3 tools/assemble/plan_diff.py <舊 plan.json> <新 plan.json>

規則（s2f-1b design.md D6）：
- 必須完全相同：width、height、fps；軌道數與各軌 type 順序；每軌片段數；
  影音片段的檔名（只比檔名，資料夾本來就不同）、src、vol；文字片段的 text、y、bg、bga；
  media[] 的檔名集合與各自的 kind、hasAudio、width、height。
- 時間（start、dur、end、total）先各自換成整數毫秒（round(秒×1000)），相差超過 1 毫秒就失敗。
輸出每軌一行（片段數、最大時間差），再逐條列出差異與差異數；全部相同 exit 0，否則 exit 1。
"""
from __future__ import annotations

import json
import os
import sys

USAGE = """Check whether two plan.json files (plan2concat_mcp.py input) are equivalent.

  python3 tools/assemble/plan_diff.py <old plan.json> <new plan.json>

Must match exactly: width, height, fps; track count and type order; segment count per track;
audio/video file names (names only), src, vol; text, y, bg, bga of text segments;
the set of media file names and their kind, hasAudio, width, height.
Times (start, dur, end, total) are rounded to whole milliseconds; more than 1 ms apart fails.
Prints one line per track (segment count, max time difference), then each difference and the count;
exit 0 when equivalent, otherwise exit 1.
"""
TOL_MS = 1
TIME_KEYS = ("start", "dur", "end")
AV_KEYS = ("src", "vol")
TEXT_KEYS = ("text", "y", "bg", "bga")
MEDIA_KEYS = ("kind", "hasAudio", "width", "height")


def ms(x: float) -> int:
    return round(x * 1000)


def fmt(d_ms: int) -> str:
    return f"{d_ms / 1000:.3f}"


def compare(old: dict, new: dict) -> tuple[list[str], list[str]]:
    """回傳 (摘要行, 差異行)。差異行是空的就代表等價。"""
    summary, diffs = [], []
    for k in ("width", "height", "fps"):
        if old.get(k) != new.get(k):
            diffs.append(f"{k}: {old.get(k)!r} != {new.get(k)!r}")
    d_total = abs(ms(old["total"]) - ms(new["total"]))
    summary.append(f"total: {old['total']} / {new['total']}, off by {fmt(d_total)}")
    if d_total > TOL_MS:
        diffs.append(f"total: {old['total']} != {new['total']} (off by {fmt(d_total)})")

    ot, nt = old["tracks"], new["tracks"]
    if len(ot) != len(nt):
        diffs.append(f"track count: {len(ot)} != {len(nt)}")
    if [t["type"] for t in ot] != [t["type"] for t in nt]:
        diffs.append(f"track type order: {[t['type'] for t in ot]} != {[t['type'] for t in nt]}")
    for i, (a, b) in enumerate(zip(ot, nt)):
        sa, sb = a["segs"], b["segs"]
        if len(sa) != len(sb):
            diffs.append(f"track {i} ({a['type']}) segment count: {len(sa)} != {len(sb)}")
        worst = 0
        for j, (x, y) in enumerate(zip(sa, sb)):
            where = f"track {i} ({a['type']}) segment {j}"
            if ("text" in x) != ("text" in y):
                diffs.append(f"{where}: one side is a text segment, the other an audio/video segment")
                continue
            if "text" in x:
                keys = TEXT_KEYS
            else:
                keys = AV_KEYS
                if os.path.basename(x["path"]) != os.path.basename(y["path"]):
                    diffs.append(f"{where} file name: {os.path.basename(x['path'])!r} != {os.path.basename(y['path'])!r}")
            for k in keys:
                if x.get(k) != y.get(k):
                    diffs.append(f"{where} {k}: {x.get(k)!r} != {y.get(k)!r}")
            for k in TIME_KEYS:
                if (k in x) != (k in y):
                    diffs.append(f"{where} {k}: only on one side")
                elif k in x:
                    d = abs(ms(x[k]) - ms(y[k]))
                    worst = max(worst, d)
                    if d > TOL_MS:
                        diffs.append(f"{where} {k}: {x[k]} != {y[k]} (off by {fmt(d)})")
        summary.append(f"track {i} {a['type']}: segments {len(sa)} / {len(sb)}, max time difference {fmt(worst)}")

    om = {os.path.basename(m["path"]): m for m in old["media"]}
    nm = {os.path.basename(m["path"]): m for m in new["media"]}
    if set(om) != set(nm):
        diffs.append(f"media file names: only in old {sorted(set(om) - set(nm))}, only in new {sorted(set(nm) - set(om))}")
    for name in sorted(set(om) & set(nm)):
        for k in MEDIA_KEYS:
            if om[name].get(k) != nm[name].get(k):
                diffs.append(f"media {name} {k}: {om[name].get(k)!r} != {nm[name].get(k)!r}")
    summary.append(f"media: {len(om)} / {len(nm)}")
    return summary, diffs


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write(USAGE)
        return 2
    old, new = (json.loads(open(p, encoding="utf-8").read()) for p in argv)
    summary, diffs = compare(old, new)
    for line in summary + diffs:
        print(line)
    print(f"differences: {len(diffs)}")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
