"""夜跑 S8 出片檢查（解說片）：先跑 film_check.py 的基本層（響度、峰值、音畫長度、最後一格、黑格、音效到位、過期），
再加字幕時間軸長度＋逐拍截圖表。任一項 FAIL 就不上稿。結果同時寫 <集>/nightly/check.json 與片旁 <片名>.check.json。

  python3 tools/nightly/check.py projects/<集>/doc.json <成片.mp4>

門檻（-14 LUFS、容差 0.8 LU、峰值 -1 dBTP 在 film_check.py；長度差 0.05 秒）的意思與出處：tools/nightly/README.md「門檻」一節。
長度比的是 beats.json 的 total（字幕時間軸終點）。
截圖取每拍第一個字後 0.15 秒（ve-director doc 流程第 8 步）：畫面要已經對上那句話。
程式畫的拍（source 是 code）多一格尾格（截圖表上標 tail），取拍尾前 0.4 秒（TAIL_BACK）：圖表跟著旁白一步步出現，第一格常常只有標題，
  這一格才是畫完的樣子。0.4 的依據（2026-11-15 量三支交付的成片共 76 個程式畫的拍，每 0.1 秒一格、只看字幕區以上）：
  和拍尾前 0.4 秒那一格比，到拍尾前 0.3 秒已經變了的 1 拍、0.2 秒 11 拍、0.1 秒 36 拍（最後 0.2 秒常是下一拍的畫面）；
  空卡檢查在 75% 處那一格多半還不是畫完的樣子（三支裡和拍尾前 0.4 秒相同的 2/26、4/18、26/28），所以不共用。
停住段（只列不擋）：切掉下方 1/4 字幕區後，畫面完全沒變 ≥4 秒的段落。門檻的依據：量過的六集
  每集 17–29 段 ≥1 秒、最長 6.2–7.9 秒，其中一集 ≥3 秒的 11 段都是程式畫面動畫播完後定住。
空卡（只列不擋）：程式畫面拍尾（75% 處）字幕區以上，有內容的 48px 格子佔比 < 0.20。有內容＝格內有紋理（標準差 > 6）
  或顏色離該列底色 > 12。量法與門檻：一支片裡看起來偏空的左右排比較卡、清單卡
  量到 0.10–0.19，看起來不空的數字卡、長條圖、時間軸、截圖卡 0.25–0.88；改大字後同一批 0.21–0.32，看起來不空。
  右框主持人那幾拍只量左邊 1240px，左下圓框那幾拍扣掉圓框那一角。
開頭空白（只列不擋，印在最後、帶修法）：程式畫面拍頭的 OPEN_S 秒（從拍頭後 0.1 秒起每 0.25 秒一格，共四格）有內容的格子佔比
  全都 < BLANK。四格是因為拍頭第一格常常還沒淡入（一支片的封面拍頭 0.15 秒量到 0、0.3 秒就出來了），只看一格會誤報。
  OPEN_S 沿用 doc_code.py 的 LEAD_MAX（開場空白超過 1 秒就擋渲染，只管 quote_card／stat_count，這裡補其他場景）。
  BLANK 的依據（2026-11-17 量五支成片 130 個程式畫的拍）：整格空白是 0；開頭只有一行小標題、圖表講到才出現的拍（兩個附帶範例
  都是這樣，這是設計）最低 0.028；拍頭一秒四格全低於 0.05 的只有這種標題拍三個，全低於 0.01 的零個。
  起因：2026-11-17 一個 DeepSeek 試跑，第一拍開頭整格空白，check 照樣 exit 0，只在截圖表上看得出來。
節奏（doc.json 有 "pace": {"script": "<稿.md>"} 才量，五項都擋）：量法與門檻在 tools/nightly/pace.py 檔頭、FORMAT.md §4e。
  沒開的系列不量：2026-11-14 拿三支其他系列的成片量過，四項都不過（前 30 秒 6.0–17.1 秒、最長靜止 10.0–15.5 秒、
  音效每分鐘 7.1–11.9 個），那些片是照另一套寫法做的。
字幕太短（擋）：doc_cut.py 把燒在畫面上的字幕裡短於 0.5 秒的寫在 voice.cleaned/short_subs.json，有任何一條就不過；
  沒有那個檔（這項檢查之前剪的片）就不列這一項。十五集量過：五集共六條，每集一兩條，把那一句和前後併成一屏就過。
結果：<集>/nightly/check.json、nightly/sheet.jpg；退出碼 0＝全過。
"""
import json, re, subprocess, sys
from pathlib import Path

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MAX_DRIFT = 0.05   # 響度、峰值的門檻在 film_check.py（系列可用 film_check.json 改）
COLS, W, H = 4, 480, 270
FREEZE_S, SUB_CROP = 4.0, 0.75
HEAD_AFTER, TAIL_BACK = 0.15, 0.4   # 首格：第一個字之後；尾格：拍尾之前（依據見檔頭）
SPARSE, TILE, SIDE_X, PIP_CORNER = 0.20, 48, 1240, (700, 380)   # 空卡門檻與量法（見上）；圓框角：y ≥ 700、x < 380
BLANK, OPEN_S = 0.01, 1.0   # 開頭空白（見上）


def content_share(img, side=False, pip=False):
    """Share of 48 px tiles above the subtitle band that hold something: texture, or a colour away from that row's ground."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)[:int(1080 * SUB_CROP)]
    if side:
        a = a[:, :SIDE_X]
    h, w = a.shape[0] // TILE * TILE, a.shape[1] // TILE * TILE
    t = a[:h, :w].reshape(h // TILE, TILE, w // TILE, TILE, 3).swapaxes(1, 2)
    std, mean = t.std(axis=(2, 3)).mean(-1), t.mean(axis=(2, 3))
    full = np.zeros(std.shape, bool)
    for r in range(std.shape[0]):
        flat = std[r] < 3
        ground = np.median(mean[r][flat] if flat.sum() >= 3 else mean[r], axis=0)
        full[r] = (std[r] > 6) | (np.abs(mean[r] - ground).max(-1) > 12)
    keep = np.ones_like(full)
    if pip:
        keep[PIP_CORNER[0] // TILE:, :PIP_CORNER[1] // TILE] = False
    return float(full[keep].mean())


def sparse_cards(mp4, beats, doc, tmp):
    """Code beats whose settled frame is mostly empty ground → [{beat, share}] (report only)."""
    side, pip = set(doc.get("side", {}).get("beats", [])), set(doc.get("pip", {}).get("beats", []))
    out = []
    for b in beats:
        if b["source"] != "code":
            continue
        f = tmp / f"{b['id']}_fill.png"
        subprocess.run(["ffmpeg", "-v", "fatal", "-y", "-ss", f"{b['start'] + b['duration'] * 0.75:.2f}", "-i", mp4,
                        "-frames:v", "1", f], check=True)
        s = content_share(Image.open(f), b["id"] in side, b["id"] in pip)
        if s < SPARSE:
            out.append({"beat": b["id"], "share": round(s, 3)})
    return out


def blank_openings(mp4, beats, doc, tmp):
    """Code beats whose first OPEN_S s show nothing above the subtitle band → [{beat, shares}] (report only; see the header)."""
    side, pip = set(doc.get("side", {}).get("beats", [])), set(doc.get("pip", {}).get("beats", []))
    out = []
    for b in beats:
        if b["source"] != "code":
            continue
        for f in tmp.glob(f"{b['id']}_open_*.png"):
            f.unlink()
        subprocess.run(["ffmpeg", "-v", "fatal", "-y", "-ss", f"{b['start'] + 0.1:.2f}", "-i", mp4, "-t", f"{OPEN_S:g}",
                        "-vf", "fps=4", str(tmp / f"{b['id']}_open_%d.png")], check=True)
        shares = [content_share(Image.open(f), b["id"] in side, b["id"] in pip)
                  for f in sorted(tmp.glob(f"{b['id']}_open_*.png"), key=lambda f: int(f.stem.rsplit("_", 1)[1]))]
        if shares and max(shares) < BLANK:
            out.append({"beat": b["id"], "shares": [round(x, 3) for x in shares]})
    return out


def duration(mp4):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                capture_output=True, text=True, check=True).stdout)


def freezes(mp4, beats, total):
    """Segments where the picture above the subtitle band stays identical for FREEZE_S s or more → [{beat, at, seconds}]."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4, "-an", "-vf",
                          f"crop=iw:ih*{SUB_CROP}:0:0,freezedetect=n=-60dB:d={FREEZE_S}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)]
    out = []
    for k, s in enumerate(starts):
        e = ends[k] if k < len(ends) else total      # a freeze running to the last frame has no end line
        b = [x for x in beats if x["start"] <= s + 0.01]
        out.append({"beat": b[-1]["id"] if b else None, "at": round(s, 2), "seconds": round(e - s, 2)})
    return out


def sheet_cells(beats):
    """The frames of the sheet → [(beat, seconds, "head" | "tail")]: every beat at its first word + HEAD_AFTER; a code beat
    also TAIL_BACK before its end (the finished drawing), unless that is not later than its first frame."""
    cells = []
    for b in beats:
        head = max(b.get("first_word", 0), b["start"]) + HEAD_AFTER   # 用 from 從句中開的拍，first_word 是整句第一個字
        cells.append((b, head, "head"))
        tail = b["start"] + b["duration"] - TAIL_BACK
        if b["source"] == "code" and tail > head:
            cells.append((b, tail, "tail"))
    return cells


def sheet_size(n):
    """Canvas (width, height) for n cells: COLS across, as many rows as the cells need."""
    return COLS * W, -(-n // COLS) * (H + 60)


def sheet(mp4, beats, out, tmp):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills/ve-director/doc/scripts"))
    import doc_common   # 截圖表標籤用倉庫附的字型；在這裡才取：字型檔不在 git 裡，找不到時 asset() 會停
    font = ImageFont.truetype(str(doc_common.asset("fonts", "NotoSansTC-Variable.ttf")), 22)
    cells = sheet_cells(beats)
    img = Image.new("RGB", sheet_size(len(cells)), "white")
    d = ImageDraw.Draw(img)
    for k, (b, t, kind) in enumerate(cells):
        f = tmp / (f"{b['id']}.jpg" if kind == "head" else f"{b['id']}_tail.jpg")
        subprocess.run(["ffmpeg", "-v", "fatal", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", f"scale={W}:{H}", f],
                       check=True)
        x, y = (k % COLS) * W, (k // COLS) * (H + 60)
        img.paste(Image.open(f), (x, y))
        d.text((x + 6, y + H + 4), f"{b['id']} {t:.1f}s {b['source']}" + (" tail" if kind == "tail" else ""), fill="#c0392b", font=font)
        d.text((x + 6, y + H + 30), b["text"][:20], fill="black", font=font)
    img.save(out, quality=82)


def short_subtitles(P):
    """(<集>/voice.cleaned/short_subs.json as written by doc_cut.py from the subtitles it burns, the check item);
    (None, None) when the file is not there (a cut made before the file existed). Any subtitle under 0.5 s fails."""
    ss = P / "voice.cleaned/short_subs.json"
    if not ss.exists():
        return None, None
    data = json.loads(ss.read_text(encoding="utf-8"))
    return data, {"item": "no subtitles under 0.5s", "ok": not data["fail"], "value": f"{len(data['fail'])} found",
                  "notes": [f"{c['start']:.1f}s held {c['dur']:.2f}s: {c['text']}" for c in data["fail"]]
                           + (["Fix: in the script, merge that line with the one before or after into one screen (remove the period or "
                               "comma between them), then run doc_align.py and doc_cut.py again"] if data["fail"] else [])}


def main():
    doc_path, mp4 = Path(sys.argv[1]).resolve(), sys.argv[2]
    P = doc_path.parent
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    bj = json.loads((P / "beats.json").read_text())
    out = P / "nightly"
    (out / "frames").mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import film_check   # 基本層（響度、峰值、音畫長度、最後一格、黑格、音效到位、過期）：任何成片都跑的那一份
    try:
        std = film_check.load_standard(P)
    except film_check.ConfigError as e:
        print(f"✗ film_check settings: {e}")
        sys.exit(2)
    base = film_check.basic(mp4, standard=std, sfx_bed=P / "sfx/sfx_bed.wav", ep=P)
    dur = duration(mp4)
    items = base["items"] + [{"code": "timeline_len", "item": f"length vs subtitle timeline ≤ {MAX_DRIFT}s",
                              "ok": abs(dur - bj["total"]) <= MAX_DRIFT, "value": f"{dur:.2f} vs {bj['total']:.2f}"}]
    paced = "pace" in doc
    if paced:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import pace
        items += pace.pace(P, doc, mp4, (doc["pace"] or {}).get("script"), dur)
    sheet(mp4, bj["beats"], out / "sheet.jpg", out / "frames")
    frozen = freezes(mp4, bj["beats"], dur)
    sparse = sparse_cards(mp4, bj["beats"], doc, out / "frames")
    blank = blank_openings(mp4, bj["beats"], doc, out / "frames")
    short_subs, short_item = short_subtitles(P)
    if short_item:
        items.append(short_item)
    ok = all(x["ok"] for x in items)
    rec = {"ok": ok, "video": str(mp4), "items": items, "listed": base["listed"], "skipped": base["skipped"],
           "size": base["size"], "sha256": base["sha256"], "sheet": "sheet.jpg",
           "frozen": frozen, "sparse": sparse, "blank_open": blank, "short_subs": short_subs}
    (out / "check.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    film_check.write_record(mp4, {k: v for k, v in rec.items() if k != "video"})   # 片旁那份（D3）：上傳前確認先找它
    for x in items:
        print("✓" if x["ok"] else "✗", x["item"], x["value"])
        for n in x.get("notes", []):
            print("   ", n)
    for x in base["listed"]:
        print("·", x["item"], x["value"])
    if not paced:
        print("· pace check off (no pace in doc.json; turn it on for episodes made per FORMAT §4e)")
    print(f"· frozen picture ≥{FREEZE_S:g}s (nothing above the subtitle band changes; listed, not blocking): "
          + (", ".join(f"{f['beat']} from {f['at']}s for {f['seconds']}s" for f in frozen) or "none"))
    print(f"· sparse cards (content share < {SPARSE:g}; listed, not blocking): " + (", ".join(f"{x['beat']} {x['share']:.2f}" for x in sparse) or "none"))
    for x in blank:
        print(f"! {x['beat']} opens on a blank frame for {OPEN_S:g}s or more (listed, not blocking, but look at it in sheet.jpg):"
              " bring its first element in at the beat's first words or a number like 0.3")
    print("film check passed" if ok else "film check failed: do not upload")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
