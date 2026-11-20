"""節奏檢查（FORMAT.md §4e）：五項都量，回傳和 check.py 同格式的項目；check.py 在 doc.json 有 "pace" 時把它們當成擋片項目。

  doc.json  "pace": {"script": "<稿.md>"}      稿子路徑相對於集資料夾；第 5 項要讀它

也可以單獨跑（不管 doc.json 有沒有開，照量照印，任一項不過 exit 1）：
  python3 tools/nightly/pace.py <集>/doc.json <成片.mp4> [<稿.md>]

門檻與量法（出處：FORMAT.md §4c 與 §4e；量法沒有和 check.py 的停住段統一，兩邊的門檻各自是用自己的量法定的）：
  1 前 30 秒相鄰兩次換畫面最長間隔 ≤ 5 秒      ffmpeg scene 0.15，去掉下方 22% 字幕帶
  2 最長靜止 ≤ 6 秒                            每秒 2 格、縮到 160x90、去掉下方 22%，相鄰兩格平均差 < 2 算靜止
  3 每拍畫面字：標籤 ≤ 5 字、出處小字 ≤ 4 字    doc.json 各拍 params 的文字欄；只數英文與數字（數字算一個字），
                                               中文標籤沒有定過上限，不數；引言卡與截圖的內文只列不擋
  4 音效 ≤ 每分鐘 3 個                         sfx_plan.json 的 kept
  5 旁白引用出處 ≤ 每分鐘 1.2 次               稿子五欄表「出處」欄含「引用」的句數；當事人自己的發言（念…）另列，不計
"""
import json, re, subprocess, sys
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import numpy as np

GAP_S, STATIC_S, LABEL_W, SOURCE_W, SFX_PER_MIN, CITE_PER_MIN = 5.0, 6.0, 5, 4, 3.0, 1.2
W, H, FPS, KEEP, SCENE, STILL = 160, 90, 2, 0.78, 0.15, 2.0
LABEL_KEYS = {"text", "caption", "title", "sub", "big", "head", "left", "right", "value", "unit"}
SOURCE_KEYS = {"source", "by", "cap"}
QUOTE_SCENES = {"quote_card", "web_evidence"}


def scene_cuts(mp4, seconds=None):
    """[cut times]: picture changes (scene > SCENE, subtitle band left out). seconds=None: the whole film."""
    lim = ["-t", str(seconds)] if seconds is not None else []
    err = subprocess.run(["ffmpeg", "-hide_banner", *lim, "-i", mp4, "-vf",
                          f"crop=iw:ih*{KEEP}:0:0,select='gt(scene,{SCENE})',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, check=True).stderr.decode(errors="replace")
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", err)]


def first30_gap(mp4):
    """(longest stretch without a picture change in the first 30 s, [cut times])."""
    cuts = scene_cuts(mp4, 30)
    edges = [0.0] + cuts + [30.0]
    return max(b - a for a, b in zip(edges, edges[1:])), cuts


def longest_static(mp4):
    """(longest still stretch in seconds, where it starts, share of the film that is still)."""
    hh = int(H * KEEP)
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-vf", f"fps={FPS},scale={W}:{H},crop={W}:{hh}:0:0,format=gray",
                          "-an", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = W * hh
    f = np.frombuffer(raw[:len(raw) // n * n], dtype=np.uint8).reshape(-1, n).astype(np.int16)
    still = np.abs(f[1:] - f[:-1]).mean(axis=1) < STILL
    best = cur = 0
    at = 0.0
    for i, s in enumerate(still):
        cur = cur + 1 if s else 0
        if cur > best:
            best, at = cur, (i + 1 - cur) / FPS
    return best / FPS, at, float(still.mean()) if len(still) else 0.0


def words(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9%.,'’+\-]*", s))


def _walk(x, key, out):
    if isinstance(x, dict):
        for k, v in x.items():
            _walk(v, k, out)
    elif isinstance(x, list):
        for v in x:
            _walk(v, key, out)
    elif isinstance(x, str) and (key in LABEL_KEYS or key in SOURCE_KEYS):
        out.append((key in SOURCE_KEYS, x))


def text_over(doc):
    """(over-limit entries, listed-only entries) from the beats' params and the pills."""
    over, listed = [], []
    for b in doc.get("beats", []):
        got = []
        _walk(b.get("params", {}), None, got)
        for is_src, s in got:
            w = words(s)
            if b.get("scene") in QUOTE_SCENES and not is_src:
                listed.append(f"{b['id']} {b['scene']} {w} words")
            elif w > (SOURCE_W if is_src else LABEL_W):
                over.append(f"{b['id']} {'source' if is_src else 'label'} {w} words: {s}")
    for pl in doc.get("pills", []) or []:
        s = pl.get("text", "") if isinstance(pl, dict) else str(pl)
        if words(s) > LABEL_W:
            over.append(f"pill {words(s)} words: {s}")
    return over, listed


def citations(md_text):
    """(row numbers whose 出處 cell says 引用, row numbers the party itself speaks) from the five-column script table."""
    rows = [[c.strip() for c in r.split("|")[1:-1]] for r in md_text.splitlines() if re.match(r"^\| \d+ \|", r)]
    rows = [r for r in rows if len(r) == 5]
    return [r[0] for r in rows if "引用" in r[3]], [r[0] for r in rows if r[3].startswith("念") and "引用" not in r[3]]


def pace(P, doc, mp4, script, dur):
    """Five items [{item, ok, value, notes?}]; stops when a file the gate needs is missing."""
    plan, md = P / "sfx_plan.json", Path(script) if script else None
    if md and not md.is_absolute():
        md = P / md
    if not md or not md.exists():
        sys.exit(f"✗ the pace check needs the script (five-column table): {md or 'pace.script in doc.json is empty'}")
    if not plan.exists():
        sys.exit(f"✗ the pace check needs {plan} (run doc_sfx.py first)")
    mins = dur / 60
    gap, cuts = first30_gap(mp4)
    still, at, share = longest_static(mp4)
    over, listed = text_over(doc)
    kept = len(json.loads(plan.read_text(encoding="utf-8"))["kept"])
    cite, actor = citations(md.read_text(encoding="utf-8"))
    return [
        {"item": f"longest stretch without a picture change in the first 30 s ≤ {GAP_S:g}s", "ok": gap <= GAP_S,
         "value": f"{gap:.1f}s, {len(cuts)} changes, the first at {cuts[0] if cuts else 'none'}s"},
        {"item": f"longest still stretch ≤ {STATIC_S:g}s", "ok": still <= STATIC_S, "value": f"{still:.1f}s (from {at:.1f}s), still for {share:.0%} of the film"},
        {"item": f"on-screen text over the limit (label {LABEL_W}, source {SOURCE_W}): 0", "ok": not over, "value": f"{len(over)} found",
         "notes": over + (["listed, not blocking (quote cards, screenshots): " + "; ".join(listed)] if listed else [])},
        {"item": f"sound effects ≤ {SFX_PER_MIN:g} a minute", "ok": kept / mins <= SFX_PER_MIN, "value": f"{kept}, {kept / mins:.1f} a minute"},
        {"item": f"citations in the narration ≤ {CITE_PER_MIN:g} a minute", "ok": len(cite) / mins <= CITE_PER_MIN,
         "value": f"{len(cite)} lines (lines {', '.join(cite)}), {len(cite) / mins:.1f} a minute; {len(actor)} lines in the party's own words not counted"},
    ]


def show(items):
    for x in items:
        print("✓" if x["ok"] else "✗", x["item"], x["value"])
        for n in x.get("notes", []):
            print("   ", n)


USAGE = """Pace check (FORMAT.md §4e): five items, any failing item exits 1.

  python3 tools/nightly/pace.py <episode>/doc.json <film.mp4> [<script.md>]

Runs whether or not doc.json turns pace on. Without <script.md>, reads pace.script in doc.json (relative to the episode folder)."""


def main():
    if len(sys.argv) not in (3, 4) or sys.argv[1] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    doc_path, mp4 = Path(sys.argv[1]).resolve(), sys.argv[2]
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    script = sys.argv[3] if len(sys.argv) > 3 else (doc.get("pace") or {}).get("script")
    if script and len(sys.argv) > 3:
        script = str(Path(script).resolve())
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True, check=True).stdout)
    items = pace(doc_path.parent, doc, mp4, script, dur)
    show(items)
    ok = all(x["ok"] for x in items)
    print("pace check passed" if ok else "pace check failed: do not release the film")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
