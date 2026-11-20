"""拆片量測：外部樣本和自己的片用同一把尺量，只量、不下判斷（openspec/changes/sample-breakdown）。

量法都沿用體檢的函式，數字才和成片檢查對得上：
  換畫面點、前 30 秒最長不換畫面   tools/nightly/pace.py（scene > 0.15、去掉下方 22% 字幕帶）
  響度、最安靜 5%                  tools/nightly/film_check.py
  逐字稿與字的時間                  doc_common.local_asr（本機 whisper.cpp）
鏡頭：相隔 ≤ MERGE_S 秒的連續換點併成一次（取第一個）。門檻 0.15 下快轉、快速移動會每格都觸發（第一支樣本
一段快轉 4.3 秒觸發 36 次，全片 188 個換點、中位數 0.12 秒）；間隔 ≤ 0.3 秒的有 131 個，放寬到 0.5 秒只多 8 個，0.3 在轉折處。
前 30 秒最長不換畫面用沒合併的換點（和 pace.first30_gap 一致；合併只會把間隔拉長，不會縮短）。
說話時間＝相鄰兩字的開始時間差 ≤ 門檻的那些差加總；門檻報 0.35、0.5、0.65 三個，因為語速會隨門檻變
（2026-11-20 四支片：門檻 0.3 時樣本比我方慢一成，0.65 時幾乎一樣；說話時間佔比的高低順序則每個門檻都一樣）。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / 'tools/config'))
import s2f_config; s2f_config.load()  # noqa: E402,E702
import math, re, subprocess, sys, tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
for _p in ("tools/nightly", "skills/ve-director/doc/scripts"):
    sys.path.insert(0, str(ROOT / _p))
import numpy as np  # noqa: E402
import film_check, pace  # noqa: E402,E401

GAPS = (0.35, 0.5, 0.65)
MERGE_S = 0.3
QUIET_FLOOR = -120.0     # quiet_level 對全零的音量會給約 -180 dB（log 前加了 1e-9）：低於這個寫 null
HAN = re.compile(r"[\u4e00-\u9fff]")
TILE_W, COLS, ROWS, CAP_H, FONT_PX = 320, 6, 5, 64, 17
EVERY_MIN, EVERY_MAX = 0.5, 60.0    # 聯絡表間隔：0 會除以零；太大一張只剩幾格
FONT = ROOT / "assets/fonts/NotoSansTC-Variable.ttf"


def streams(mp4):
    """片裡有哪些種類的流（"video"、"audio"）。用 codec_type 判斷，不靠 duration 欄位。"""
    out = film_check._ffprobe(["-show_entries", "stream=codec_type", "-of", "csv=p=0", str(mp4)])
    return {x.strip() for x in out.splitlines() if x.strip()}


def speech(words, duration):
    """words：local_asr 單支的結果 {"segments": [{"words": [{"word", "start", "end"}]}]}。只數漢字。"""
    ws = [w for s in words.get("segments", []) for w in s.get("words", []) if HAN.search(w["word"])]
    chars = sum(len(HAN.findall(w["word"])) for w in ws)
    if not chars:
        return None
    steps = [b["start"] - a["start"] for a, b in zip(ws, ws[1:])]
    by_gap = {}
    for g in GAPS:
        t = sum(d for d in steps if 0 < d <= g)
        by_gap[str(g)] = {"per_min": round(chars / t * 60, 1) if t else None, "share": round(t / duration, 3)}
    return {"chars": chars, "chars_per_min_film": round(chars / duration * 60, 1), "by_gap": by_gap}


def merge(cuts):
    """相隔 ≤ MERGE_S 的連續換點只留第一個（一段快轉、一次閃白算一次換畫面）。"""
    return [c for k, c in enumerate(cuts) if k == 0 or c - cuts[k - 1] > MERGE_S]


def shots(cuts, duration):
    """鏡頭長度分布；cuts 是合併後的換點。"""
    edges = [0.0] + [c for c in cuts if 0 < c < duration] + [duration]
    lens = np.diff(edges)
    return {"count": len(lens), "per_min": round((len(edges) - 2) / duration * 60, 1),
            "median": round(float(np.median(lens)), 2), "p10": round(float(np.percentile(lens, 10)), 2),
            "p90": round(float(np.percentile(lens, 90)), 2)}


def measure(mp4, words=None):
    """一支片的量測（measure.json 的一筆）。words 是 local_asr 單支的結果；None 時 speech 為 null。"""
    mp4 = str(mp4)
    kinds = streams(mp4)
    dur = film_check.probe(mp4)["fmt"]
    cuts = pace.scene_cuts(mp4)
    sh = shots(merge(cuts), dur)
    sh["raw_cuts"] = len(cuts)
    sh["first30_gap"] = round(pace.first30_gap(mp4)[0], 2) if dur >= 30 else None   # first30_gap 把 30 秒當尾端
    lufs = quiet = None
    if "audio" in kinds:
        lufs = film_check.black_and_loudness(mp4)[1]
        q = film_check.quiet_level(mp4)
        quiet = round(q, 1) if q is not None and q > QUIET_FLOOR else None
    return {"name": Path(mp4).stem, "path": mp4, "duration": round(dur, 2), "lufs": lufs, "quiet_db": quiet,
            "cuts": [round(c, 2) for c in cuts], "shots": sh,
            "speech": speech(words, dur) if words and "audio" in kinds else None}


def _wrap(draw, text, font, width, lines):
    """依實際字寬斷行，最多 lines 行，放不下的最後補「…」。"""
    out, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > width:
            out.append(cur)
            cur = ch
            if len(out) == lines:
                out[-1] = out[-1][:-1] + "…"
                return out
        else:
            cur += ch
    return out + [cur] if cur else out


def sheet(mp4, words, out_prefix, every=3.0):
    """聯絡表：每 every 秒一格（寬 320），格下寫開始時間與開始時間落在這一格內的字；6×5 一張，超過分張。
    回傳圖檔路徑。ffmpeg 8 沒有 drawtext，字用 PIL 寫。"""
    from PIL import Image, ImageDraw, ImageFont
    dur = film_check.probe(str(mp4))["fmt"]
    n = math.ceil(dur / every)
    ws = [w for s in (words or {}).get("segments", []) for w in s.get("words", [])]
    font = ImageFont.truetype(str(FONT), FONT_PX)
    with tempfile.TemporaryDirectory() as tmp:
        # 取每格開始那一格：fps=1/every 取的是格內最後一秒（round=down）或中間（預設），畫面會比標的時間晚（2026-11-20 實測）
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vf",
                        f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{every})',scale={TILE_W}:-2",
                        "-fps_mode", "passthrough", "-frames:v", str(n), f"{tmp}/%05d.png"], check=True)
        frames = sorted(Path(tmp).glob("*.png"))[:n]
        tile_h = Image.open(frames[0]).height + CAP_H
        paths = []
        per = COLS * ROWS
        for k in range(0, len(frames), per):
            chunk = frames[k:k + per]
            img = Image.new("RGB", (COLS * TILE_W, math.ceil(len(chunk) / COLS) * tile_h), "white")
            d = ImageDraw.Draw(img)
            for j, f in enumerate(chunk):
                i = k + j
                t0 = i * every
                x, y = (j % COLS) * TILE_W, (j // COLS) * tile_h
                img.paste(Image.open(f), (x, y))
                said = "".join(w["word"] for w in ws if t0 <= w["start"] < t0 + every).strip()
                cap = f"{int(t0 // 60)}:{t0 % 60:04.1f}  " + said
                for m, line in enumerate(_wrap(d, cap, font, TILE_W - 8, 3)):
                    d.text((x + 4, y + tile_h - CAP_H + 2 + m * (FONT_PX + 3)), line, fill="black", font=font)
            p = Path(f"{out_prefix}_{k // per + 1:02d}.jpg")
            img.save(p, quality=85)
            paths.append(p)
    return paths


def transcribe(paths):
    """{path: words}：一次載模型跑完。沒設 S2F_WHISPER_CPP_MODEL 時回 None。沒聲音流的片呼叫端先濾掉（local_asr 轉檔遇到會整批中止）。"""
    import doc_common
    if not paths:
        return {}
    res = doc_common.local_asr(paths, "zh", words=True)
    return None if res is None else {p: res[Path(p)] for p in paths}


def names(paths):
    """檔名（去副檔名）；重名加 -2、-3。"""
    out, seen = [], {}
    for p in paths:
        n = Path(p).stem
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n}-{seen[n]}")
    return out


def table(films, asr_missing):
    def v(x, fmt="{}"):
        return "—" if x is None else fmt.format(x)

    def gap(f, g, k, fmt):
        return v(((f["speech"] or {}).get("by_gap") or {}).get(g, {}).get(k), fmt)
    rows = [("片長", lambda f: v(f["duration"], "{:.0f} s")),
            ("鏡頭數（相隔 ≤ 0.3 秒的換點併成一次）", lambda f: str(f["shots"]["count"])),
            ("每分鐘換鏡", lambda f: str(f["shots"]["per_min"])),
            ("鏡頭長度 中位數／第 10、90 百分位", lambda f: f'{f["shots"]["median"]}／{f["shots"]["p10"]}、{f["shots"]["p90"]} s'),
            ("前 30 秒最長不換畫面", lambda f: v(f["shots"]["first30_gap"], "{} s")),
            ("整體響度", lambda f: v(f["lufs"], "{} LUFS")),
            ("最安靜 5%", lambda f: v(f["quiet_db"], "{} dB")),
            ("全片字數 ÷ 片長（含停頓）", lambda f: v((f["speech"] or {}).get("chars_per_min_film"), "{} 字／分"))]
    for g in GAPS:
        rows.append((f"開口語速／說話佔比（停頓門檻 {g} 秒）",
                     lambda f, g=g: gap(f, str(g), "per_min", "{:.0f}") + "／" + gap(f, str(g), "share", "{:.0%}")))
    head = ["| 項目 | " + " | ".join(f["name"] for f in films) + " |", "|---|" + "---|" * len(films)]
    import doc_common
    lines = (["沒設 S2F_WHISPER_CPP_MODEL，說話量測沒做：" + doc_common.LOCAL_SETUP, ""] if asr_missing else []) + head
    lines += [f"| {label} | " + " | ".join(fn(f) for f in films) + " |" for label, fn in rows]
    return "\n".join(lines) + "\n"


def main(argv=None):
    import argparse, json
    ap = argparse.ArgumentParser(description="Measure a sample film and our own films the same way (measure only, no verdicts).")
    ap.add_argument("sample")
    ap.add_argument("--vs", nargs="*", default=[], help="our films to measure side by side")
    ap.add_argument("--out", required=True, help="output folder (nothing is written next to the films)")
    ap.add_argument("--every", type=float, default=3.0, help="contact sheet: one tile every N seconds")
    a = ap.parse_args(argv)
    if not EVERY_MIN <= a.every <= EVERY_MAX:
        print(f"✗ --every must be {EVERY_MIN}–{EVERY_MAX} seconds")
        return 2
    paths = [a.sample] + a.vs
    kinds = {}
    for p in paths:                                   # 先全部檢查，有一支不行就不產半套結果
        if not Path(p).is_file():
            print(f"✗ not found: {p}")
            return 2
        kinds[p] = streams(p)
        if "video" not in kinds[p]:
            print(f"✗ no video stream: {p}")
            return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tr = transcribe([p for p in paths if "audio" in kinds[p]])
    films = []
    for p, n in zip(paths, names(paths)):
        w = (tr or {}).get(p)
        if w is not None:
            (out / f"words_{n}.json").write_text(json.dumps(w, ensure_ascii=False), encoding="utf-8")
        m = measure(p, w)
        m["name"] = n
        m["sheets"] = [x.name for x in sheet(p, w, out / f"sheet_{n}", a.every)]
        films.append(m)
        print(f"  {n}: {m['shots']['count']} shots, {m['duration']:.0f}s")
    (out / "measure.json").write_text(json.dumps({"films": films}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "measure.md").write_text(table(films, tr is None), encoding="utf-8")
    print(f"→ {out / 'measure.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
