"""成片基本體檢：任何一支 mp4 都能跑，不需要 doc.json。出片腳本經由 tools/concat/export.py 自動呼叫；也可以單獨跑。

  python3 tools/nightly/film_check.py <片.mp4> [--ep <集資料夾>]

結果寫在片旁的 <片名>.check.json（含成片大小與 SHA-256，上傳前用來確認檢查的就是這支）。退出碼 0＝過、1＝不過、2＝設定錯誤。
<片名>.inputs.json 是出片當下剪接用檔的指紋，只有 tools/concat/export.py 會寫；本程式只讀、不寫也不刪，
所以過期的片重跑檢查照樣不過，不會「檢查時順手記下現況」替自己蓋章。

項目（代號：擋／列）。門檻依據：openspec/changes/film-check-all/evidence/（2026-11-19 量 67 支已交付成片）。
  av_len     擋  影像流與聲音流長度差 ≤ 3 格。67 支最大 0.067 秒（兩個短片系列共 12 支音軌多兩格，封裝的量化誤差）；
                 半截檔差的是秒級。
  last_frame 擋  最後一個影像封包的結束時間比檔頭長度少 ≤ 3 格。67 支最大 0.067 秒。
  black_mid  擋  畫面全黑的段落（blackdetect d=0 pic_th=0.98 pix_th=0.10；長度 0 的偵測殘影不算），片尾黑以外一段都不許有。
                 一個解說系列的交付檔抽 10 集全有、每集 2–8 段（換鏡第一格前全黑只剩字幕），是 Concat 0.2.8–0.2.10 匯出時在部分
                 接縫產生的；2026-11-20 同一個專案用 0.2.11 重匯，帶 crf 24 與不帶 crf 都是 0 段，原本黑的位置都有畫面。
                 再出現就是 Concat 又壞了或版本退回。
  black_tail 列  黑段結束點離檔尾 < 0.1 秒、長度 ≤ 2 秒：片尾硬切黑（剪接計畫的畫面比總長短，Concat 補黑）。量到的：解說片 4 支、
                 短劇 1 支 0.13–0.73 秒，一支教學短片 1.37 秒。2026-11-20 定只提醒、上限放寬到 2 秒，不回頭修舊片的剪接。
  loudness   擋  整體響度，預設 -14±0.8 LUFS。
  peak       擋  真峰值，預設 ≤ -1.0 dBTP。
  sfx        擋  只在給了音效床（集資料夾的 sfx/sfx_bed.wav）時量：整條音效床和成片做互相關（8 kHz 單聲道、只取音效床有聲的
                 20 ms 區塊、位移搜尋 ±1 秒），分數 ≥ SFX_MIN 且位移 ≤ SFX_LAG 秒才算音效真的混進去、而且沒對歪。
                 門檻依據（2026-11-20，evidence/sfx.txt）：17 集成片 0.136–0.208、位移都 0.000；同集合成反例：音效床比實際再小
                 12 dB 0.031–0.056（位移 0）、拿掉音效床 0.009–0.013、換別集音效床 0.009–0.024（位移亂跳，0.024 那組位移 -0.95 秒）。
                 SFX_MIN 取 0.031 與 0.022 的中點（D5 規則；0.024 是之後重量多出的一組，仍在門檻下，且位移條件另外擋得住）。
  stale      擋  <片名>.inputs.json 記的剪接用檔，SHA-256 有任何一個對不上。檔不見只列在說明裡、不擋（交片後清中間檔是常態，
                 例：疊加層的外框 PNG；缺檔證明不了片子過期）。沒有 .inputs.json 的舊片列「無紀錄」、不擋。
  quiet      列  成片最安靜 5% 的音量（16 kHz 單聲道、每 0.1 秒算 RMS dBFS，取第 5 百分位）高於 quiet_max（預設 -28）就提醒：句子之間
                 配樂沒讓開，可能蓋過人聲。依據（2026-11-20 量 57 支已上架片）：唯一被聽出配樂蓋人聲的一集（-20、沒 duck）
                 -26.4；刻意熱鬧的時事解說 11 支（-20＋duck 6）-29.8～-31.7；其他系列 -34～-46。正例只有一支、和時事只差
                 3.4 dB，所以只列不擋，門檻取兩者中點。
  first30    列  前 30 秒最長不換畫面（量法與上限 5 秒照 pace.py 的 first30_gap，FORMAT §4c／§4e）。集資料夾有 doc.json＋beats.json 時，
                 封面拍（scene "cover"）那段不算（2026-11-20 定：系列固定開場的封面可以停久一點）。§4c 寫所有長片都適用，但擋片
                 只在開了 pace 的片；2026-11-20 量 22 支（封面扣掉）：開了 pace 的 4.5 秒，其他 5.7–16.4 秒，使用者都收了，所以這裡先列。
系列門檻：系列資料夾（集資料夾的上一層）放 film_check.json，例
  {"lufs": -14, "lufs_tol": 0.8, "max_tp": -1.0, "skip": [{"item": "black_mid", "why": "刻意用黑場轉場"}]}
  缺鍵用預設；skip 的 item 不在代號表或 why 空白：設定錯誤（exit 2）。
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

DEFAULT = {"lufs": -14.0, "lufs_tol": 0.8, "max_tp": -1.0, "quiet_max": -28.0, "skip": []}
ITEMS = ("av_len", "last_frame", "black_mid", "loudness", "peak", "sfx", "stale", "quiet", "first30")
SLACK_FRAMES = 3       # 音畫差、最後一格的容許格數
TAIL_GAP, TAIL_MAX = 0.1, 2.0   # 片尾黑：結束點離檔尾 < 0.1 秒，長度 ≤ 2 秒
SFX_SR, SFX_MAXLAG, SFX_MIN, SFX_LAG = 8000, 1.0, 0.026, 0.02


class ConfigError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_paths(mp4):
    p = Path(mp4)
    return p.with_name(p.stem + ".check.json"), p.with_name(p.stem + ".inputs.json")


def load_standard(ep_dir):
    """系列資料夾的 film_check.json 合併預設。ep_dir 是 None（不在集裡的片）就看片所在資料夾的上一層。"""
    std = dict(DEFAULT)
    if ep_dir is None:
        return std
    f = Path(ep_dir).resolve().parent / "film_check.json"
    if not f.exists():
        return std
    try:
        cfg = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ConfigError(f"{f}: not JSON ({e})")
    if not isinstance(cfg, dict):
        raise ConfigError(f"{f}: not a JSON object")
    unknown = set(cfg) - set(DEFAULT)
    if unknown:
        raise ConfigError(f"{f}: unknown keys {sorted(unknown)}; allowed {sorted(DEFAULT)}")
    for s in cfg.get("skip", []):
        if not isinstance(s, dict) or s.get("item") not in ITEMS or not str(s.get("why", "")).strip():
            raise ConfigError(f"{f}: each skip needs an item from {ITEMS} and a non-blank why; got {s}")
    std.update(cfg)
    return std


def _ffprobe(args):
    return subprocess.run(["ffprobe", "-v", "error", *args], capture_output=True, text=True, check=True).stdout


def probe(mp4):
    """{"fmt", "v", "a", "last", "fps"}：檔頭長度、影像流與聲音流長度、最後一個影像封包的結束時間、影格率。"""
    fmt = float(_ffprobe(["-show_entries", "format=duration", "-of", "csv=p=0", mp4]))
    s = json.loads(_ffprobe(["-show_entries", "stream=codec_type,duration,r_frame_rate", "-of", "json", mp4]))["streams"]
    v = next((x for x in s if x["codec_type"] == "video"), None)
    a = next((x for x in s if x["codec_type"] == "audio"), None)
    num, den = (v or {}).get("r_frame_rate", "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    ends = []
    for line in _ffprobe(["-select_streams", "v:0", "-show_entries", "packet=pts_time,duration_time", "-of", "csv=p=0", mp4]).splitlines():
        parts = line.split(",")
        if len(parts) >= 2 and parts[0] not in ("", "N/A"):
            ends.append(float(parts[0]) + (float(parts[1]) if parts[1] not in ("", "N/A") else 0.0))
    last = max(ends) if ends else None

    def dur(x):
        return float(x["duration"]) if x and x.get("duration") not in (None, "N/A") else None
    return {"fmt": fmt, "v": dur(v) if v else None, "a": dur(a) if a else None, "last": last, "fps": fps}


def black_and_loudness(mp4):
    """([(開始, 結束, 長度)], 整體響度 LUFS, 真峰值 dBTP)，一次解碼量完。沒有聲音流時響度與峰值是 None。"""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4, "-vf", "blackdetect=d=0:pic_th=0.98:pix_th=0.10",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    blacks = [(float(s), float(e), float(d)) for s, e, d in
              re.findall(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", err)]
    if "Summary:" not in err:
        return blacks, None, None
    summ = err[err.rindex("Summary:"):]
    i, pk = re.search(r"I:\s+(-?[\d.]+) LUFS", summ), re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ)
    return blacks, float(i[1]) if i else None, float(pk[1]) if pk else None   # 全靜音的音軌：ebur128 峰值印 -inf（響度印下限 -70.0），印不出數字的當作量不到


def split_blacks(blacks, fmt):
    """(片中黑段, 片尾黑段)；長度 0 的偵測殘影丟掉。"""
    mid, tail = [], []
    for s, e, d in blacks:
        if d <= 0:
            continue
        (tail if fmt - e < TAIL_GAP and d <= TAIL_MAX else mid).append({"at": round(s, 3), "seconds": round(d, 3)})
    return mid, tail


def _mono8k(path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SFX_SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def sfx_match(bed_wav, mp4):
    """(分數, 位移秒)：音效床有聲的 20 ms 區塊（> 最大能量 -40 dB）才算，成片只留這些區塊（左右放寬 SFX_MAXLAG）；
    FFT 互相關，在 ±SFX_MAXLAG 內找絕對值最大的正規化相關。任一邊沒有聲音：(0.0, None)。"""
    import numpy as np
    bed, film = _mono8k(bed_wav), _mono8k(mp4)
    n = min(len(bed), len(film))
    if n == 0:
        return 0.0, None
    bed, film = bed[:n], film[:n]
    blk = 160
    k = n // blk
    e = (bed[:k * blk].reshape(k, blk) ** 2).mean(1)
    if e.max() <= 0:
        return 0.0, None
    on = e > e.max() * 1e-4
    w = int(SFX_MAXLAG * SFX_SR / blk)
    onw = np.convolve(on.astype(float), np.ones(2 * w + 1), "same") > 0
    b = bed[:k * blk] * np.repeat(on, blk)
    f = film[:k * blk] * np.repeat(onw, blk)
    size = 1 << (2 * len(b) - 1).bit_length()
    c = np.fft.irfft(np.fft.rfft(f, size) * np.conj(np.fft.rfft(b, size)), size)
    L = int(SFX_MAXLAG * SFX_SR)
    lags = np.r_[c[:L + 1], c[-L:]]
    idx = np.r_[np.arange(L + 1), np.arange(-L, 0)]
    j = int(np.abs(lags).argmax())
    denom = float(np.sqrt((b * b).sum() * (f * f).sum())) + 1e-9
    return float(abs(lags[j]) / denom), float(idx[j] / SFX_SR)


def quiet_level(mp4):
    """成片最安靜 5% 的音量（dBFS）：每 0.1 秒一塊算 RMS，取第 5 百分位。沒有聲音：None。"""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float) / 32768    # 16 kHz：門檻是用這個取樣率量的，8 kHz 會高約 2.5 dB
    blk = 1600
    k = len(a) // blk
    if k == 0:
        return None
    rms = np.sqrt((a[:k * blk].reshape(k, blk) ** 2).mean(1))
    return float(np.percentile(20 * np.log10(rms + 1e-9), 5))


def cover_spans(ep):
    """封面拍在成片裡的 (起, 訖) 秒：doc.json 裡 scene 是 cover 的拍，時間從 beats.json 拿。缺檔或讀不了：[]。"""
    try:
        doc = json.loads((Path(ep) / "doc.json").read_text())
        beats = json.loads((Path(ep) / "beats.json").read_text())["beats"]
    except (OSError, ValueError, KeyError, TypeError):
        return []
    covers = {b["id"] for b in doc.get("beats", []) if b.get("scene") == "cover"}
    return [(float(b["start"]), float(b["end"])) for b in beats if b.get("id") in covers]


def first30(mp4, covers=()):
    """前 30 秒最長不換畫面的秒數，封面那段扣掉。換畫面點照 pace.first30_gap 的量法。"""
    from pace import first30_gap
    _, cuts = first30_gap(str(mp4))
    edges = [0.0] + cuts + [30.0]
    return max((b - a) - sum(max(0.0, min(b, ce) - max(a, cs)) for cs, ce in covers) for a, b in zip(edges, edges[1:]))


def stale(inputs_file):
    """(ok, value, notes)。沒有指紋檔：(None, "no record", [])。"""
    if not inputs_file.exists():
        return None, "no record", []
    rec = json.loads(inputs_file.read_text(encoding="utf-8"))
    base = Path(rec.get("base", inputs_file.parent))
    bad, gone = [], []
    for rel, h in rec.get("files", {}).items():
        f = base / rel
        if not f.exists():
            gone.append(f"{rel}: missing (cleaned up after export? cannot compare)")   # 缺檔證明不了過期：列、不擋
        elif sha256(f) != h:
            bad.append(f"{rel}: changed since the film was made")
    value = f"{len(bad)} of {len(rec.get('files', {}))} inputs differ" + (f", {len(gone)} missing" if gone else "")
    return not bad, value, bad + gone


def basic(mp4, *, standard=None, skip=(), sfx_bed=None, ep=None):
    """跑基本層。skip：這一次不跑的代號（--no-check 給的）；系列 film_check.json 的 skip 另外合併。
    ep：集資料夾（有的話，first30 從它的 doc.json＋beats.json 找封面拍）。
    回傳 {"ok", "items", "listed", "size", "sha256", "skipped"}。"""
    std = standard or dict(DEFAULT)
    skipped = set(skip) | {s["item"] for s in std.get("skip", [])}
    p = probe(mp4)
    blacks, lufs, tp = black_and_loudness(mp4)
    slack = SLACK_FRAMES / p["fps"]
    items, listed = [], []

    def add(code, label, ok, value, notes=()):
        if code in skipped:
            return
        items.append({"code": code, "item": label, "ok": bool(ok), "value": value, "notes": list(notes)})

    if p["v"] is not None and p["a"] is not None:
        add("av_len", f"video and audio lengths within {SLACK_FRAMES} frames ({slack:.3f}s)",
            abs(p["a"] - p["v"]) <= slack, f"video {p['v']:.3f}s, audio {p['a']:.3f}s")
    else:
        add("av_len", "film has both video and audio", False, f"video {p['v']}, audio {p['a']}")
    add("last_frame", f"last video frame within {SLACK_FRAMES} frames of the file length",
        p["last"] is not None and p["fmt"] - p["last"] <= slack,
        f"last frame ends {p['last']:.3f}s, file {p['fmt']:.3f}s" if p["last"] is not None else "no video packets")
    mid, tail = split_blacks(blacks, p["fmt"])
    add("black_mid", "no black frames inside the film", not mid, f"{len(mid)} found",
        [f"{b['at']}s for {b['seconds']}s" for b in mid])
    if tail:
        listed.append({"code": "black_tail", "item": "black at the very end (listed, not blocking)", "value": tail})
    add("loudness", f"loudness {std['lufs']}±{std['lufs_tol']} LUFS", lufs is not None and abs(lufs - std["lufs"]) <= std["lufs_tol"], lufs)
    add("peak", f"peak ≤ {std['max_tp']} dBTP", tp is not None and tp <= std["max_tp"], tp)
    if sfx_bed and Path(sfx_bed).is_file() and "sfx" not in skipped:
        score, lag = sfx_match(sfx_bed, mp4)
        add("sfx", f"sound effects are in the mix (match ≥ {SFX_MIN}, offset ≤ {SFX_LAG}s)",
            score >= SFX_MIN and lag is not None and abs(lag) <= SFX_LAG, f"match {score:.3f}, offset {lag}s",
            [] if score >= SFX_MIN else ["the sfx bed is missing or far too quiet in the film: check the mix step"])
    if "stale" not in skipped:
        ok, value, notes = stale(record_paths(mp4)[1])
        if ok is None:
            listed.append({"code": "stale", "item": "inputs fingerprint (listed, not blocking)", "value": value})
        else:
            add("stale", "film made from the current inputs", ok, value, notes)
    if "quiet" not in skipped and p["a"] is not None:
        q, qmax = quiet_level(mp4), std.get("quiet_max", DEFAULT["quiet_max"])
        if q is not None:
            listed.append({"code": "quiet", "item": "quietest 5% of the sound (listed, not blocking)",
                           "value": f"{q:.1f} dB" + (f"; louder than {qmax}: music may be covering the voice between lines"
                                                      if q > qmax else "")})
    if "first30" not in skipped and p["v"] is not None:
        from pace import GAP_S
        g = first30(mp4, cover_spans(ep) if ep else [])
        listed.append({"code": "first30", "item": "longest stretch without a new picture in the first 30 s, cover left out "
                       "(listed, not blocking)", "value": f"{g:.1f}s" + (f"; over {GAP_S:.0f}s (FORMAT §4c)" if g > GAP_S else "")})
    return {"ok": all(x["ok"] for x in items), "items": items, "listed": listed,
            "size": Path(mp4).stat().st_size, "sha256": sha256(mp4), "skipped": sorted(skipped)}


def write_record(mp4, result):
    out = record_paths(mp4)[0]
    out.write_text(json.dumps({"video": str(Path(mp4).resolve()), **result}, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def show(result):
    for x in result["items"]:
        print("✓" if x["ok"] else "✗", x["item"], x["value"])
        for n in x["notes"]:
            print("   ", n)
    for x in result["listed"]:
        print("·", x["item"], x["value"])
    if result["skipped"]:
        print("· skipped:", ", ".join(result["skipped"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Basic film check for any mp4 (see the file header for items and thresholds).")
    ap.add_argument("mp4")
    ap.add_argument("--ep", help="episode folder (its parent may hold film_check.json; its sfx/sfx_bed.wav turns on the sfx item); "
                                 "default: the film's folder")
    a = ap.parse_args(argv)
    if not Path(a.mp4).exists():
        print(f"✗ film not found: {a.mp4}")
        return 2
    try:
        std = load_standard(a.ep or Path(a.mp4).resolve().parent)
    except ConfigError as e:
        print(f"✗ film_check settings: {e}")
        return 2
    ep = Path(a.ep or Path(a.mp4).resolve().parent)
    r = basic(a.mp4, standard=std, sfx_bed=ep / "sfx/sfx_bed.wav", ep=ep)
    write_record(a.mp4, r)
    show(r)
    print("film check passed" if r["ok"] else "film check failed: do not upload")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
