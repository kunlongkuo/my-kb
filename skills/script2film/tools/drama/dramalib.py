"""drama_cut.py 的純邏輯（不碰 ffmpeg／檔案系統，pytest 直接測）。

時間軸設定檔（cut.json，路徑相對於設定檔所在資料夾；絕對路徑照用）：
{
  "name": "my_drama",                   # 成片檔名／Concat 專案名
  "fps": 30,                            # 字卡與每鏡畫面的格率（預設 30）
  "lang": "zh",                         # check 做語音辨識的語言："zh"（預設）或 "en"
  "font": "fonts/NotoSerifTC-Variable.ttf",   # 字幕與字卡的字型；省略＝<內附素材層（設定檔的素材層路徑，沒設用倉庫 assets/）>/fonts/NotoSerifTC-Variable.ttf
  "sfx_dir": "sfx",                     # 音效檔 <sfx_dir>/<name>.mp3 或 .wav
  "roomtone": {"name": "roomtone", "db": -26},   # 整片循環的底噪（可省略；音效資料夾裡的檔名）
  "grade": "old_photo",                 # 另出一版調色（可省略，只有 concat --export 用）；原色版一定出
  "dialogue": {"stem": "vocals", "db": -18},     # 對白取原片聲音（"original"，預設）或 demucs 拆出的人聲（"vocals"）；db＝整支來源的對白 RMS 拉到多少
  "sep_dir": "work/sep",                # demucs 結果的快取（可省略＝工作資料夾裡的 sep/）：<sep_dir>/htdemucs/<來源路徑 / 換 _、去掉 .mp4>/vocals.wav
  "scenes": {"cafe": {"bed": "auto", "db": -33}, "street": {"bed": "sfx/street.wav", "db": -30, "fade_out": 2.0}},
  "music": {"file": "music/theme.wav", "db": -31, "stop_at": "D5"},
  "shots": [
    {"id": "D0", "card": "第一天　早上", "dur": 3.0, "sfx": [{"name": "rooster", "at": 0.6, "db": -10}]},
    {"id": "D5", "src": "clips/shot5.mp4", "in": 0, "dur": 2.6, "zoom": 1.2, "speaker": "小美", "scene": "cafe",
     "sub": {"text": "阿明，下來。", "from": 0.27, "to": 1.67}}
  ]
}
每鏡：
- 一鏡一個 id；card＝程式字卡，src＝影片（in／dur 秒，zoom＝中心裁切放大，speed＝播放倍速：從 in 取 dur×speed 秒的素材加速成 dur 秒，
  聲音同步 atempo，限 0.5–2）。card 可以是字串（置中一行），或 {"lines": [{"text","size","y", 可選 "font"}], "bg": "#000000"}
  （白字、各行水平置中，y＝字的上緣像素）。
- speaker：這鏡的聲音是對白（換過聲的對嘴片），Concat 裡放「對白-<speaker>」軌；沒有 speaker 的鏡不帶原聲。每段對白頭尾各淡入淡出 20 毫秒。
- sub＝一張字幕 {"text","from","to"}；subs＝多張 [{"text","from","to"}, …]。from／to 是鏡內秒數（to 超過鏡長會截在鏡尾前 0.02 秒）；
  sfx 的 at 也是鏡內秒數。
- hflip: true＝左右翻轉；crop: [w, h, x, y]＝先裁這塊再縮回 1920×1080（在 zoom 之前）。
- pics：插入鏡 [{"src","in","dur", 可選 "hflip","crop","zoom"}, …]。聲音仍取自這鏡的 src（整段不斷），畫面依序換成各段；
  各段 dur 加總要等於這鏡的 dur（差 0.001 內），有 pics 的鏡不能設 speed≠1。每鏡仍只產出一支畫面檔。
- title：疊在畫面上的字 {"lines": [{"text","size","y", 可選 "font"}], "from": 0.8, "to": 5.4}（白字加陰影），
  from 起淡入 0.8 秒、到 to 時淡出完（淡出從 to−0.8 開始）。
- scene：場名。頂層 scenes 每場一條連續的底噪，從這場第一鏡鋪到最後一鏡（同一場的鏡要連續）。bed："auto"＝從這場有 speaker 的鏡的
  來源片取沒有人聲的空檔接起來，不夠長就循環、交叉淡化 0.5 秒；或給檔案路徑。db＝素材 RMS 拉到的值，fade_out＝場尾淡出秒數（預設 0.03）。
- music：配樂從 0 秒開始，到 stop_at 那一鏡的起點硬停（頭 0.05 秒淡入、尾 0.03 秒淡出）；沒有 stop_at 就到片尾。
- punch：限時放大，[{"zoom": 1.3, "cx": 0.5, "cy": 0.4, "from": 2, "to": 4}]，cx／cy 是放大中心（畫面寬高比例），用來在某幾秒把燒字推出畫面或補特寫。
- delogo：限時糊掉一塊，[{"box": [x, y, w, h], "from": 1, "to": 3}]，box 是成片 1920×1080 的像素（在 zoom／punch 之後）。
  兩者的 from／to 都是鏡內秒數，省略就是整鏡。
"""
from __future__ import annotations

import copy
import math
import re

CJK = re.compile(r"[一-鿿]")
WORD = re.compile(r"[A-Za-z0-9']+")
W, H = 1920, 1080


def units(text: str) -> int:
    """台詞長度：有中日韓字就數那些字，否則數英文詞。"""
    cjk = CJK.findall(text)
    return len(cjk) if cjk else len(WORD.findall(text))


def subs_of(shot: dict) -> list[dict]:
    """一鏡的字幕清單：新寫法 subs、舊寫法 sub 都統一成清單。"""
    if shot.get("subs"):
        return list(shot["subs"])
    return [shot["sub"]] if shot.get("sub") else []


def pics_of(shot: dict) -> list[dict]:
    """一鏡的插入鏡畫面段（補上預設值）；沒有 pics 回空清單。"""
    out = []
    for p in shot.get("pics") or []:
        q = {"src": p["src"], "in": float(p.get("in", 0)), "dur": float(p["dur"]), "zoom": float(p.get("zoom", 1.0))}
        if p.get("hflip"):
            q["hflip"] = True
        if p.get("crop"):
            q["crop"] = list(p["crop"])
        out.append(q)
    return out


def offsets(shots: list[dict], durs: list[float] | None = None) -> list[float]:
    """每鏡在成片的起點；durs 給實際片長（編碼後可能和設定差一兩格）時照實際排。"""
    out, t = [], 0.0
    for i, s in enumerate(shots):
        out.append(t)
        t += durs[i] if durs else float(s["dur"])
    return out


def total(shots: list[dict], durs: list[float] | None = None) -> float:
    return sum(durs) if durs else sum(float(s["dur"]) for s in shots)


def frame_counts(lengths: list[float], fps: int, start: float = 0.0) -> list[int]:
    """一串依序相接的長度 → 各段的格數：照累計的起訖點取整，誤差不累積（每段各自四捨五入會一路多出幾格）。"""
    out, t = [], start
    for ln in lengths:
        out.append(round((t + ln) * fps) - round(t * fps))
        t += ln
    return out


def scene_spans(shots: list[dict], durs: list[float] | None = None) -> dict[str, tuple[float, float]]:
    """每場在成片的（起點, 終點）；同一場的鏡要連續，否則 ValueError。沒有 scene 的鏡不屬於任何場。"""
    spans: dict[str, tuple[float, float]] = {}
    last = None
    real = durs or [float(s["dur"]) for s in shots]
    for t, s, d in zip(offsets(shots, durs), shots, real):
        sc = s.get("scene")
        if sc is not None and sc in spans and last != sc:
            raise ValueError(f"{s['id']}: the shots of scene \"{sc}\" are not consecutive (a shot of another scene, or of no scene, is in between)")
        if sc is not None:
            spans[sc] = (spans[sc][0] if sc in spans else t, t + d)
        last = sc
    return spans


def _lines_ok(lines, where: str):
    if not isinstance(lines, list) or not lines:
        raise ValueError(f"{where}: lines must be a non-empty list")
    for k, ln in enumerate(lines):
        if not ln.get("text") or float(ln.get("size", 0)) <= 0 or "y" not in ln:
            raise ValueError(f"{where}: lines[{k}] needs text, size (>0) and y")


def check_cfg(cfg: dict) -> None:
    """cut.json 的限制；違反就丟 ValueError，訊息帶鏡號。"""
    fps = cfg.get("fps", 30)
    if not isinstance(fps, int) or fps <= 0:
        raise ValueError(f"fps must be a positive integer: {fps}")
    if cfg.get("lang", "zh") not in ("zh", "en"):
        raise ValueError(f"lang must be zh or en: {cfg.get('lang')}")
    dia = cfg.get("dialogue") or {}
    if dia.get("stem", "original") not in ("original", "vocals"):
        raise ValueError(f"dialogue.stem must be original or vocals: {dia.get('stem')}")
    shots = cfg["shots"]
    ids = [s["id"] for s in shots]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError("duplicate shot ids: " + ", ".join(dup))
    scenes = cfg.get("scenes") or {}
    for s in shots:
        sid, dur = s["id"], float(s["dur"])
        if ("card" in s) == ("src" in s):
            raise ValueError(f"{sid}: needs exactly one of card and src")
        if dur <= 0:
            raise ValueError(f"{sid}: dur must be greater than 0")
        speed = float(s.get("speed", 1.0))
        if not 0.5 <= speed <= 2:
            raise ValueError(f"{sid}: speed must be within 0.5–2: {speed}")
        if isinstance(s.get("card"), dict):
            _lines_ok(s["card"].get("lines"), f"{sid} card")
        if s.get("crop") is not None and (len(s["crop"]) != 4 or min(s["crop"][:2]) <= 0 or min(s["crop"][2:]) < 0):
            raise ValueError(f"{sid}: crop must be [w, h, x, y], w/h > 0, x/y ≥ 0")
        pics = s.get("pics")
        if pics:
            if "src" not in s:
                raise ValueError(f"{sid}: pics needs src (the sound comes from src)")
            if abs(speed - 1.0) > 1e-9:
                raise ValueError(f"{sid}: a shot with pics cannot set speed")
            got = sum(float(p["dur"]) for p in pics)
            if abs(got - dur) > 0.001:
                raise ValueError(f"{sid}: the pics' dur adds up to {got:g}; it must equal this shot's dur {dur:g}")
            for k, p in enumerate(pics):
                if not p.get("src") or float(p["dur"]) <= 0:
                    raise ValueError(f"{sid} pics {k}: needs src and dur > 0")
                if p.get("crop") is not None and len(p["crop"]) != 4:
                    raise ValueError(f"{sid} pics {k}: crop must be [w, h, x, y]")
        for k, c in enumerate(subs_of(s)):
            a, b = float(c["from"]), float(c["to"])
            if not (0 <= a < b and a < dur) or not c.get("text"):
                raise ValueError(f"{sid} subtitle {k}: needs text, with 0 ≤ from < to and from inside the shot: {a}–{b}")
        t = s.get("title")
        if t:
            _lines_ok(t.get("lines"), f"{sid} title")
            a, b = float(t.get("from", 0)), float(t.get("to", dur))
            if not 0 <= a < b <= dur + 1e-6:
                raise ValueError(f"{sid} title: from/to must be within 0–{dur:g}s with from < to: {a}–{b}")
        sc = s.get("scene")
        if sc is not None and sc not in scenes:
            raise ValueError(f"{sid}: scene \"{sc}\" is not in the top-level scenes")
    for name, sc in scenes.items():
        if not isinstance(sc.get("bed"), str) or not sc["bed"]:
            raise ValueError(f"scene \"{name}\": bed must be \"auto\" or a file path")
    scene_spans(shots)
    mus = cfg.get("music")
    if mus:
        if not mus.get("file"):
            raise ValueError("music: needs file")
        if mus.get("stop_at") is not None and mus["stop_at"] not in ids:
            raise ValueError(f"music.stop_at: no such shot {mus['stop_at']}")


def lanes(items: list[tuple[float, float]]) -> list[int]:
    """(起點, 長度) 依序分配到第一條空著的軌，回傳每項的軌號（0 起）。剪輯軟體同軌不能重疊。"""
    ends: list[float] = []
    out = []
    for at, ln in items:
        k = next((j for j, e in enumerate(ends) if e <= at + 1e-6), len(ends))
        if k == len(ends):
            ends.append(0.0)
        ends[k] = at + ln
        out.append(k)
    return out


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def subtitles(shots: list[dict], durs: list[float] | None = None) -> list[tuple[float, float, str]]:
    """成片時間的字幕；結尾截在該鏡實際片長前 0.02 秒，才不會壓到下一鏡的字幕（剪輯軟體會拒收重疊）。"""
    out = []
    real = durs or [float(s["dur"]) for s in shots]
    for t, s, d in zip(offsets(shots, durs), shots, real):
        for sub in subs_of(s):
            out.append((t + float(sub["from"]), t + min(float(sub["to"]), d - 0.02), sub["text"]))
    return out


def srt(subs: list[tuple[float, float, str]]) -> str:
    return "".join(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n" for n, (a, b, txt) in enumerate(subs, 1))


def sfx_cues(shots: list[dict], durs: list[float] | None = None) -> list[dict]:
    """全片音效清單（成片秒數），k＝全片序號，素材檔名用它（sfx_<k>_<name>.wav），pull 時靠它找回原設定。"""
    out = []
    for t, s in zip(offsets(shots, durs), shots):
        for c in s.get("sfx", []):
            out.append({"k": len(out), "shot": s["id"], "name": c["name"], "at": t + float(c["at"]), "rel": float(c["at"]),
                        "db": c.get("db", 0)})
    return out


def _window(c: dict, dur: float, where: str) -> str:
    a, b = float(c.get("from", 0)), float(c.get("to", dur))
    if not 0 <= a < b <= dur + 1e-6:
        raise ValueError(f"{where}: from/to must be within 0–{dur}s with from < to: {a}–{b}")
    return f"between(t,{a:g},{b:g})"


def shot_filter(s: dict, fps: int = 30, inp: str = "0:v", out: str = "v", tag: str = "") -> str:
    """一鏡（或一段插入鏡）畫面的 filter_complex 片段（輸入 [inp]、輸出 [out]）：翻轉、裁切、倍速、中心放大，
    再疊限時 punch，最後限時 delogo。tag＝內部標籤的前綴（同一張濾鏡圖放好幾段時避免撞名）。"""
    dur, zoom, speed = float(s["dur"]), float(s.get("zoom", 1.0)), float(s.get("speed", 1.0))
    punch, logo = s.get("punch", []), s.get("delogo", [])
    pre = ("hflip," if s.get("hflip") else "") + ("crop={}:{}:{}:{},".format(*(int(v) for v in s["crop"])) if s.get("crop") else "")
    b, p, z = f"{tag}b", f"{tag}p", f"{tag}z"
    g = [f"[{inp}]{pre}setpts=PTS/{speed},scale={round(W * zoom)}:{round(H * zoom)},crop={W}:{H},fps={fps},setsar=1"
         + (f",split={len(punch) + 1}[{b}0]" + "".join(f"[{p}{k}]" for k in range(len(punch))) if punch else f"[{b}0]")]
    for k, c in enumerate(punch):
        zz, cx, cy = float(c["zoom"]), float(c.get("cx", 0.5)), float(c.get("cy", 0.5))
        if not 1 < zz <= 3 or not (0 <= cx <= 1 and 0 <= cy <= 1):
            raise ValueError(f"{s['id']} punch {k}: zoom must be within 1–3 and cx/cy within 0–1")
        zw, zh = round(W * zz), round(H * zz)
        x, y = min(max(round(cx * zw - W / 2), 0), zw - W), min(max(round(cy * zh - H / 2), 0), zh - H)
        en = _window(c, dur, f"{s['id']} punch {k}")
        g.append(f"[{p}{k}]scale={zw}:{zh},crop={W}:{H}:{x}:{y}[{z}{k}];[{b}{k}][{z}{k}]overlay=0:0:enable='{en}'[{b}{k + 1}]")
    last = f"{b}{len(punch)}"
    chain = []
    for k, c in enumerate(logo):
        x, y, w, h = (int(v) for v in c["box"])
        if not (x >= 1 and y >= 1 and w > 0 and h > 0 and x + w <= W - 1 and y + h <= H - 1):
            raise ValueError(f"{s['id']} delogo {k}: box must be inside the picture, at least 1 pixel from each edge (an ffmpeg delogo limit): {c['box']}")
        en = _window(c, dur, f"{s['id']} delogo {k}")
        chain.append(f"delogo=x={x}:y={y}:w={w}:h={h}:enable='{en}'")
    g.append(f"[{last}]" + (",".join(chain) if chain else "null") + f"[{out}]")
    return ";".join(g)


# ---- 檢查：對白有沒有被截 ----
def line_status(expected: str, words: list[dict], clip_end: float) -> dict:
    """比對語音辨識與台詞。words＝[{"word","start","end"}]（鏡內秒數）。
    截斷＝辨識到的字數（英文數詞，見 units）少於台詞，且最後一個字貼著片尾（0.15 秒內）：片子裡就沒有那幾個字，剪接補不回來。
    頭尾空白只是建議修剪量，剪接就能處理。同音字不算錯（只比字數）。"""
    want = units(expected)
    cjk = bool(CJK.search(expected))
    got = sum(len(CJK.findall(w["word"])) if cjk else len(WORD.findall(w["word"])) for w in words)
    if not words:
        return {"ok": False, "reason": "no speech recognized", "want": want, "got": 0}
    first, last = float(words[0]["start"]), float(words[-1]["end"])
    truncated = got < want and last >= clip_end - 0.15
    # 字數少但句尾沒貼片尾：多半是辨識漏字（同音、連音），不判失敗，只提醒聽一下
    return {"ok": not truncated, "truncated": truncated, "want": want, "got": got,
            "speech": (round(first, 2), round(last, 2)), "lead": round(first, 2), "tail": round(clip_end - last, 2),
            "reason": "the end of the line is cut off (not in the clip: reshoot, or cut to a reaction shot over a separately recorded line)" if truncated
            else (f"recognition is {want - got} short of the line (the speech does not reach the clip's end, so most likely missed by recognition; listen)" if got < want else "")}


# ---- pull：把使用者在 Concat 調過的時間軸讀回 cut.json ----
SHOT_FILE = re.compile(r"^\d+_(.+?)\.mp4$")
SFX_FILE = re.compile(r"^sfx_(\d+)_(.+?)\.wav$")
LINE_FILE = re.compile(r"^\d+_(.+?)_(.+?)\.wav$")


def text_of(content: str) -> str:
    """文字素材的內容：JSON {"text": …}，或標籤格式 <font …>…[文字]…</font>（取方括號裡的字）。"""
    import json
    try:
        return json.loads(content)["text"]
    except (ValueError, KeyError, TypeError):
        pass
    m = re.search(r"\[(.*)\]", re.sub(r"<[^>]+>", "", content), re.S)
    return m.group(1) if m else re.sub(r"<[^>]+>", "", content)


def concat_as_draft(tl: dict) -> tuple[dict, dict[str, str], dict[str, float]]:
    """Concat 的 timeline_read 結果 → pull 吃的格式（tracks／segments／微秒時間）與名稱對照。"""
    tracks: dict[str, list] = {}
    names, full = {}, {}
    media_len = {m["id"]: m.get("duration", 0) for m in tl.get("media", [])}
    for x in tl["timeline"]["clips"]:
        kind = x.get("kind")
        if kind not in ("video", "audio", "text"):
            continue
        names[x["id"]] = x.get("text", "") if kind == "text" else x.get("name", "")
        if x.get("media") in media_len:
            full[x["id"]] = media_len[x["media"]]
        seg = {"material_id": x["id"],
               "target_timerange": {"start": round(x["start"] * 1e6), "duration": round(x["duration"] * 1e6)},
               "source_timerange": {"start": round(x.get("sourceStart", 0) * 1e6), "duration": round(x["duration"] * 1e6)}}
        if "volume" in x:
            seg["volume"] = x["volume"]
        tracks.setdefault((kind, x.get("track")), []).append(seg)
    return {"tracks": [{"type": k[0], "segments": v} for k, v in tracks.items()]}, names, full


def _segs(draft: dict, kind: str) -> list[list[dict]]:
    return [t["segments"] for t in draft["tracks"] if t["type"] == kind]


def pull(cut: dict, draft: dict, names: dict[str, str], full: dict[str, float] | None = None) -> tuple[dict, list[str]]:
    """draft＝時間軸（concat_as_draft 的格式）；names＝素材 id → 檔名（影片、音訊）或文字內容。
    回傳（新的 cut、改動報告）。畫面段依檔名對回鏡號，入點加上素材內的偏移、長度用時間軸上的長度；
    音效依檔名序號對回原設定（保留音量）、掛到起點所在的那一鏡；字幕依文字內容對回（sub／subs 照原本的寫法寫回）；
    對白聲音跟著畫面走（成片從同一支片取聲），只報告時間軸裡聲畫的偏差。
    full＝素材 id → 素材全長：整段照用（沒修頭尾）時保留原設定長度，不把「來源本來就短一點」誤報成修剪。"""
    by_id = {s["id"]: s for s in cut["shots"]}
    old_order = [s["id"] for s in cut["shots"]]
    cues = sfx_cues(cut["shots"])
    report: list[str] = []
    vsegs = sorted((s for tr in _segs(draft, "video") for s in tr), key=lambda s: s["target_timerange"]["start"])
    shots, starts = [], []
    for seg in vsegs:
        m = SHOT_FILE.match(names.get(seg["material_id"], ""))
        if not m or m.group(1) not in by_id:
            report.append(f"⚠ unrecognized picture segment: {names.get(seg['material_id'], seg['material_id'])} (skipped)")
            continue
        old = by_id[m.group(1)]
        s = copy.deepcopy(old)
        s["sfx"] = []
        src_off = (seg.get("source_timerange") or {}).get("start", 0) / 1e6
        s["dur"] = round(seg["target_timerange"]["duration"] / 1e6, 3)
        whole = full and seg["material_id"] in full and src_off < 0.01 and abs(full[seg["material_id"]] - s["dur"]) < 0.02
        if whole:
            s["dur"] = float(old["dur"])
        if "src" in s:
            s["in"] = round(float(s.get("in", 0)) + src_off, 3)
        if abs(s["dur"] - float(old["dur"])) > 0.04 or src_off > 0.04:
            report.append(f"trimmed {s['id']}: {float(old['dur']):.2f} → {s['dur']:.2f}s" + (f" (in point moved {src_off:.2f} later)" if src_off > 0.04 else ""))
            if s.get("pics"):
                report.append(f"⚠ {s['id']} has inserts (pics) whose lengths were not changed with it: adjust them by hand to add up to {s['dur']:.2f}s")
        st = seg["target_timerange"]["start"] / 1e6
        if shots and st - (starts[-1] + shots[-1]["dur"]) > 0.05:
            report.append(f"gap of {st - (starts[-1] + shots[-1]['dur']):.2f}s between {shots[-1]['id']} and {s['id']} (the film joins them directly)")
        shots.append(s)
        starts.append(st)
    new_order = [s["id"] for s in shots]
    removed = [i for i in old_order if i not in new_order]
    if removed:
        report.append("removed: " + ", ".join(removed))
    kept_old = [i for i in old_order if i in new_order]
    if kept_old != new_order:
        report.append("reordered: " + " → ".join(new_order))

    def shot_at(t: float) -> int:
        k = 0
        for j, st in enumerate(starts):
            if st <= t + 1e-3:
                k = j
        return k

    seen = set()
    for tr in _segs(draft, "audio"):
        for seg in tr:
            name = names.get(seg["material_id"], "")
            at = seg["target_timerange"]["start"] / 1e6
            m = SFX_FILE.match(name)
            if m:
                k = int(m.group(1))
                c = cues[k] if k < len(cues) else {"name": m.group(2), "db": 0, "shot": "?", "at": at}
                j = shot_at(at)
                db = c["db"]
                vol = seg.get("volume", 1.0)  # 使用者在剪輯軟體裡調的片段音量，疊加到原設定
                if vol and abs(vol - 1.0) > 1e-3:
                    db = round(db + 20 * math.log10(vol), 1)
                    report.append(f"sound effect {c['name']}: volume {c['db']} → {db} dB")
                shots[j]["sfx"].append({"name": c["name"], "at": round(at - starts[j], 3), "db": db})
                seen.add(k)
                if c["shot"] != shots[j]["id"] or abs((at - starts[j]) - c.get("rel", 0)) > 0.1:  # 3 格內算格點誤差（重存會對齊格點）
                    report.append(f"sound effect {c['name']}: moved to {shots[j]['id']} +{at - starts[j]:.2f}s")
                continue
            m = LINE_FILE.match(name)
            if m and m.group(1) in new_order:
                j = new_order.index(m.group(1))
                a_src = (seg.get("source_timerange") or {}).get("start", 0) / 1e6
                drift = (at - a_src) - (starts[j] - 0)  # 聲音的 0 秒落點 vs 畫面的 0 秒落點（畫面段入點已併進 in）
                v_off = shots[j].get("in", 0) - by_id[m.group(1)].get("in", 0)
                drift += v_off
                if abs(drift) > 0.1:
                    report.append(f"dialogue {m.group(1)}: on the timeline the sound is {abs(drift):.2f}s {'behind' if drift > 0 else 'ahead of'} the picture (the film aligns to the picture)")
    for c in cues:
        if c["k"] not in seen:
            report.append(f"removed sound effect: {c['name']} (was in {c['shot']})")

    texts = [(s["target_timerange"]["start"] / 1e6, s["target_timerange"]["duration"] / 1e6, names.get(s["material_id"], ""))
             for tr in _segs(draft, "text") for s in tr]
    for j, s in enumerate(shots):
        olds = subs_of(s)
        if not olds:
            continue
        used, news = set(), []
        for sub in olds:
            hit = [(k, x) for k, x in enumerate(texts)
                   if k not in used and x[2] == sub["text"] and starts[j] - 0.05 <= x[0] < starts[j] + s["dur"]]
            if not hit:
                report.append(f"subtitle {s['id']} \"{sub['text']}\" is not within this shot's time (kept as it was; please check)")
                news.append(sub)
                continue
            k, (a, ln, _) = hit[0]
            used.add(k)
            news.append({"text": sub["text"], "from": round(a - starts[j], 3), "to": round(a - starts[j] + ln, 3)})
        if s.get("subs"):
            s["subs"] = news
        else:
            s["sub"] = news[0]
    new = copy.deepcopy(cut)
    new["shots"] = shots
    return new, report
