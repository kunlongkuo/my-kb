"""把 plan.json 透過 Concat 的 MCP 伺服器（concat --mcp，stdio）建成 Concat 專案。plan.json 的來源是
tools/assemble/cut2plan.py（doc_cut.py 會呼叫）。

用法：
  python3 tools/concat/plan2concat_mcp.py <plan.json> <專案所在資料夾> <專案名> --font <family>=<ttf>

走 Concat 的 MCP：不用開視窗、不用 token。
大批指令用 edit_apply 的 batch 一次送（素材一批、片段一批、修剪與音量一批），各批全部成功才生效。
目前只支援字幕型文字（統一字級、無漸顯漸隱、不帶個別字級顏色），字卡動畫做不出來。
--layers <layers.json>：PromptStudio doc_cut 產的疊加層（右框主持人 side、關鍵字膠囊 pills），各放一條軌，在 Concat 裡還能拖
（右框和膠囊交給 Concat 做，減少對 CapCut 的倚賴）。軌由上往下：字幕、膠囊、主持人、外框、草稿原有的軌。
layers.json 另外可帶（doc.json 同名欄位，doc_cut 算好時間）：chapters（章節標籤＋四角括號外框，放最上兩條軌）、
punch（主持人推近跳剪）、grain（匯出時疊底片顆粒，Concat 沒有單純的顆粒圖層）、
en（英文字幕放中文字幕下面，中文字幕往上移；同時在 cut 資料夾產 subtitles_en.srt／subtitles_zh.srt 給 YouTube）。
--photo-credits <集資料夾>：照片拍的當頁署名小字（photo_credits.py 從 doc.json、beats.json、assets/CREDITS.md 算），放最上一條軌、
右上角章節標籤下面靠右（使用者：當頁也標、只在 Concat 加，不重渲程式畫面）。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, json, math, os, re, subprocess, sys
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from concat_export import export as concat_export, add_no_check, parse_no_check, export_crf, FilmCheckFailed  # noqa: E402

CONCAT = os.environ.get("S2F_CONCAT_BIN") or os.environ.get("CONCAT_BIN") or "/Applications/Concat.app/Contents/MacOS/concat"
SUB_SIZE = 0.046   # 字幕字級（畫面高比例）


class MCP:
    def __init__(self):
        self.p = subprocess.Popen([CONCAT, "--mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.n = 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "plan2concat", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")

    def rpc(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}, ensure_ascii=False) + "\n")
        while True:
            m = json.loads(self.p.stdout.readline())
            if m.get("id") == self.n:
                if "error" in m:
                    sys.exit(f"✗ {method}: {json.dumps(m['error'], ensure_ascii=False)[:800]}")
                return m["result"]

    def tool(self, _tool, **args):
        r = self.rpc("tools/call", {"name": _tool, "arguments": args})
        text = "".join(c.get("text", "") for c in r.get("content", []))
        if r.get("isError"):
            sys.exit(f"✗ {_tool}: {text[:800]}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text


def probe(p):
    """addMedia 要的素材描述（與 tools/assemble/cut2plan.py 同一套寫法）。"""
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p],
                                  capture_output=True, text=True, check=True).stdout)
    v = next((x for x in j["streams"] if x["codec_type"] == "video"), None)
    a = next((x for x in j["streams"] if x["codec_type"] == "audio"), None)
    m = {"path": p, "name": os.path.basename(p), "kind": "video" if v else "audio", "hasAudio": bool(a), "duration": float(j["format"]["duration"])}
    if v:
        m.update(width=v["width"], height=v["height"], frameRateFraction=v["r_frame_rate"], videoCodec=v["codec_name"])
    if a:
        m.update(audioCodec=a["codec_name"], audioTracks=[{"index": a["index"], "channels": a["channels"],
                                                         "sampleRate": int(a["sample_rate"]), "codec": a["codec_name"]}])
    return m


LAYER_LANES = ("pills", "side", "plate")   # 字幕之下、草稿軌之上，由上往下


def layer_cmds(L, lane):
    """跟字幕同一批放：外框底板、膠囊字（文字片段建立時就有長度）。主持人片另外一段一段放（add_side）。"""
    cmds = []
    for s in L.get("side", []):
        pl = s["plate"]
        cmds.append({"op": "addTextClip", "trackId": lane["plate"], "start": s["start"], "duration": s["dur"], "offsetY": pl["offsetY"],
                     "style": {"content": " ", "background": pl["color"], "maxWidth": pl["maxWidth"], "maxHeight": pl["maxHeight"],
                               "backgroundRadius": pl["radius"], "backgroundPaddingX": 0, "backgroundPaddingY": 0, "shadow": False}})
    for p in L.get("pills", []):
        cmds.append({"op": "addTextClip", "trackId": lane["pills"], "start": p["start"], "duration": p["dur"], "offsetY": p["offsetY"],
                     "style": {"content": p["text"], "fontFamily": L["font"]["family"], "fontWeight": 800, "fontSize": p.get("size", 0.04),
                               "color": p["color"], "background": p["fill"], "backgroundRadius": 0.05, "backgroundPaddingX": 0.04,
                               "backgroundPaddingY": 0.022, "shadow": False}})
    return cmds


def add_side(c, proj, L, lane, mid):
    """主持人片一段一段放：剛放進來的片段是整支 TP 的長度，修剪前同軌放不下下一段。從該段時間起播（整段旁白版 TP，嘴型才對得上）、
    靜音、裁切遮罩定位。"""
    for s in L.get("side", []):
        cid = c.tool("edit_apply", path=proj, command={"op": "addClip", "mediaId": mid[s["clip"]], "trackId": lane["side"],
                                                       "start": s["start"]})["createdId"]
        full = next(x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"] if x["id"] == cid)["duration"]
        c.tool("edit_apply", path=proj, command={"op": "batch", "commands": [
            {"op": "trimClip", "clipId": cid, "edge": "start", "delta": s["src"]},   # 修片頭：片段跟著往後挪 src 秒
            {"op": "moveClips", "moves": [{"clipId": cid, "start": s["start"], "trackId": lane["side"]}]},   # 搬回該段起點
            {"op": "trimClip", "clipId": cid, "edge": "end", "delta": round(s["dur"] - (full - s["src"]), 4)},
            {"op": "updateClip", "clipId": cid, "patch": {"muted": True, "crop": s["crop"], "mask": s["mask"]}},
            {"op": "setClipTransform", "clipId": cid, "scale": s["scale"], "offsetX": s["offsetX"], "offsetY": s["offsetY"]}]})


def layer_fix(L, lane, have):
    """外框與膠囊補 offsetX（addTextClip 只收 offsetY）；膠囊淡入淡出。"""
    cmds = []
    for s in L.get("side", []):
        cmds.append({"op": "setClipTransform", "clipId": have[(lane["plate"], round(s["start"], 3))]["id"], "offsetX": s["plate"]["offsetX"]})
    for p in L.get("pills", []):
        cid = have[(lane["pills"], round(p["start"], 3))]["id"]
        cmds += [{"op": "updateClip", "clipId": cid, "patch": {"fadeIn": p["fade"], "fadeOut": p["fade"]}},
                 {"op": "setClipTransform", "clipId": cid, "offsetX": p.get("offsetX", 0.0)}]
    return cmds


def add_chapters(c, proj, ch, total, fam):
    """整支片最上層的外框圖（透明 PNG，四角括號）＋章節標籤（右上角深色膠囊，換章淡入）。使用者想要
    「加一個邊框在整個影片的上層」，選了四角括號＋章節標籤（畫面不縮，全版照片照樣滿版）。
    ch：{"frame": png 絕對路徑（可省）, "tags": [{"start", "end", "text"}], "fill", "color", "size", "offsetX", "offsetY", "fade"}"""
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": [{"op": "addTrack"}, {"op": "addTrack"}]})
    tl = c.tool("timeline_read", path=proj)
    top, under = [t["id"] for t in sorted(tl["timeline"]["tracks"], key=lambda t: -t["index"])[:2]]   # 標籤一條、外框一條
    cmds = []
    if ch.get("frame"):
        mid = c.tool("media_import", path=proj, file=ch["frame"])["createdId"]   # 靜圖：probe() 量不到長度，交給 Concat 自己匯入
        cid = c.tool("edit_apply", path=proj, command={"op": "addClip", "mediaId": mid, "trackId": under, "start": 0})["createdId"]
        d = next(x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"] if x["id"] == cid)["duration"]
        cmds.append({"op": "trimClip", "clipId": cid, "edge": "end", "delta": round(total - d, 4)})
    cmds += [{"op": "addTextClip", "trackId": top, "start": t["start"], "duration": round(t["end"] - t["start"], 3), "offsetY": ch["offsetY"],
              "style": {"content": t["text"], "fontFamily": fam, "fontWeight": 800, "fontSize": ch["size"], "color": ch["color"],
                        "background": ch["fill"], "backgroundRadius": 0.12, "backgroundPaddingX": 0.03, "backgroundPaddingY": 0.018,
                        "shadow": False}} for t in ch["tags"]]
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": cmds})
    have = {round(x["start"], 3): x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"]
            if x["track"] == top}
    fix = []
    for t in ch["tags"]:
        x = have[round(t["start"], 3)]["id"]
        fix += [{"op": "updateClip", "clipId": x, "patch": {"fadeIn": ch["fade"], "fadeOut": ch["fade"]}},
                {"op": "setClipTransform", "clipId": x, "offsetX": ch["offsetX"]}]
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": fix})


CREDIT = {"size": 0.0135, "offsetY": -0.36, "right": 70, "fill": "#1f3a5f99", "color": "#ffffff", "padX": 0.012, "padY": 0.008}


def credit_offset_x(width_px, right=CREDIT["right"], pad_x=CREDIT["padX"]):
    """靠右對齊：小字（含底色左右留白）的右緣離畫面右邊 right px。offsetX 是中心離畫面中心佔畫面寬的比例。"""
    half = width_px / 2 + pad_x * 1080
    return round((1920 - right - half) / 1920 - 0.5, 4)


def add_photo_credits(c, proj, rows, fam, fpath):
    """照片拍的署名小字（photo_credits.load 的結果）：自己一條最上層的軌，章節標籤（offsetY -0.425）下面、靠右。"""
    if not rows:   # 這集沒有照片拍：不加空軌
        return
    c.tool("edit_apply", path=proj, command={"op": "addTrack"})
    top = max(c.tool("timeline_read", path=proj)["timeline"]["tracks"], key=lambda t: t["index"])["id"]
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": [
        {"op": "addTextClip", "trackId": top, "start": r["start"], "duration": r["dur"], "offsetY": CREDIT["offsetY"],
         "style": {"content": r["text"], "fontFamily": fam, "fontWeight": 400, "fontSize": CREDIT["size"], "color": CREDIT["color"],
                   "background": CREDIT["fill"], "backgroundRadius": 0.2, "backgroundPaddingX": CREDIT["padX"],
                   "backgroundPaddingY": CREDIT["padY"], "shadow": False}} for r in rows]})
    have = {round(x["start"], 3): x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"] if x["track"] == top}
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": [
        {"op": "setClipTransform", "clipId": have[round(r["start"], 3)]["id"],
         "offsetX": credit_offset_x(text_px(r["text"], CREDIT["size"], fpath))} for r in rows]})


def text_px(text, size, fpath):
    """最寬那行在 1080p 畫面上幾 px。Concat 的 fontSize 是大寫字母高（畫面高比例），先用 H 量出這個字型的大寫高佔 em 多少。"""
    from PIL import ImageFont
    f = ImageFont.truetype(fpath, 1000)
    x0, y0, x1, y1 = f.getbbox("H")
    f = ImageFont.truetype(fpath, max(1, round(size * 1080 * 1000 / (y1 - y0))))
    return CONCAT_K * max(f.getlength(l) for l in text.split("\n"))


# Concat 實際排出來的字比照「fontSize＝大寫高」換算的窄：2026-10-31 DevoSerif700 三句（中 0.046 兩句、英 0.023 一句）
# preview_frame 量到的寬÷上面算的寬＝0.737／0.738／0.728
CONCAT_K = 0.735


PITCH = SUB_SIZE * 1.2   # 中文字幕一行的行距（lineHeight 1.2 × 字級）


def en_rows(en, text):
    """英文這句佔中文框幾行空白：英文行距是 1.2 × 英文字級，一行中文空白裝得下 PITCH ÷ 英文行距 行英文。"""
    return max(1, math.ceil(len(text.split("\n")) * en["size"] / SUB_SIZE - 1e-9))


def shared_zh(s, style, en, fpath):
    """en.shared（中英雙語字幕共用一個底框）：中文字幕框往下多撐 k 行空白，英文疊進去，兩種字共用一個底框。
    中文那行固定在 zh_offsetY，框往下長；框寬＝這一屏中文與同時間英文較寬者＋左右留白（maxWidth 讓框剛好這麼寬、不自己換行）。
    回傳 (style, offsetY)。"""
    cue = next((q for q in en["cues"] if q["start"] - 0.01 <= s["start"] < q["end"]), None)
    k = en_rows(en, cue["text"]) if cue else 0
    w = max(text_px(s["text"], SUB_SIZE, fpath), text_px(cue["text"], en["size"], fpath) if cue else 0)
    return ({**style, "content": s["text"] + "\n\u3000" * k, "maxWidth": round((w * 1.04 + 2 * 0.0315 * 1080) / 1920, 4)},
            round(en["zh_offsetY"] + k * PITCH / 2, 4))


def add_en(c, proj, en, fam, plan):
    """英文字幕（中文旁白、中英字幕）：中文字幕下面一條，一句中文一句英文，同一句的時間；
    底色跟中文字幕一樣。en：{"cues": [{"start", "end", "text"}], "size", "offsetY"}（doc_cut en_subs 算好）。"""
    seg = next((s for t in plan["tracks"] if t["type"] == "text" for s in t["segs"] if s.get("bg")), None)
    c.tool("edit_apply", path=proj, command={"op": "addTrack"})
    top = max(c.tool("timeline_read", path=proj)["timeline"]["tracks"], key=lambda t: t["index"])["id"]
    style = {"fontFamily": fam, "fontWeight": 400, "fontSize": en["size"], "color": en.get("color", "#ffffff"), "shadow": False,
             "align": "center", "lineHeight": 1.2}
    if seg and not en.get("shared"):
        style["background"] = seg["bg"] + f"{round(max(0, min(seg['bga'], 1)) * 255):02x}"
    # shared：英文放在中文那行下面 k 行空白的正中間
    y = lambda q: round(en["zh_offsetY"] + PITCH / 2 + en_rows(en, q["text"]) * PITCH / 2, 4) if en.get("shared") else en["offsetY"]
    c.tool("edit_apply", path=proj, command={"op": "batch", "commands": [
        {"op": "addTextClip", "trackId": top, "start": q["start"], "duration": round(q["end"] - q["start"], 3), "offsetY": y(q),
         "style": {**style, "content": q["text"]}} for q in en["cues"]]})


def add_punch(c, proj, lane, punches):
    """主持人推近跳剪（Gemini 看片建議「腳本驅動的跳剪」）：主畫面軌在 start、end 各切一刀，中間那段放大到 scale，
    像換了一個近一點的機位。punches：[{"start", "end", "scale"}]，時間是時間軸秒數，只該放在全版主持人那幾拍的轉折句。"""
    for pu in punches:
        for t in (pu["start"], pu["end"]):
            clips = [x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"]
                     if x["track"] == lane and x["start"] + 0.02 < t < x["start"] + x["duration"] - 0.02]
            if clips:
                c.tool("clips_split", path=proj, clipIds=[clips[0]["id"]], time=t)
        mid = [x for x in c.tool("timeline_read", path=proj)["timeline"]["clips"] if x["track"] == lane and abs(x["start"] - pu["start"]) < 0.02]
        if not mid:
            sys.exit(f"✗ punch {pu['start']}: the main video track has no clip at this time")
        c.tool("clip_transform", path=proj, clipId=mid[0]["id"], scale=pu["scale"])


def loudnorm(path, target="I=-14:TP=-2.5:LRA=11", grain=0):
    """兩段式 loudnorm（畫面 stream copy；grain > 0 時畫面重編碼並疊 ffmpeg 底片顆粒）。Enhance Voice 會讓人聲小約 0.7 dB，
    Concat 沒有母帶段，交付前在這裡補。TP：AAC 重編碼會讓峰值往上衝（2026-10-21：TP=-1 出來 -0.8；另一集
    TP=-1.5 出來 -0.9，過不了夜跑 S8 的 -1.0），-2.5 出來 -2.2／-1.8。"""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    tmp = path + ".tmp.mp4"
    af = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    # 每格隨機的顆粒壓不下來：只用 crf 17 時影像 25 Mbps、4 分鐘 840 MB（檔案比之前大十倍）；
    # 上限 8 Mbps＝YouTube 1080p 30fps 建議碼率，上片後本來就會再壓一次
    video = (["-vf", f"noise=c0s={grain}:c0f=t+u", "-c:v", "libx264", "-crf", str(export_crf()), "-maxrate", "8M", "-bufsize", "16M",
              "-preset", "medium", "-pix_fmt", "yuv420p"]
             if grain else ["-c:v", "copy"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, *video, "-af", af, "-c:a", "aac", "-b:a", "192k", tmp], check=True)
    os.replace(tmp, path)


def stream_dur(path, kind):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", kind, "-show_entries", "stream=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.split()
    return float(out[0]) if out else 0.0


def trim_silent_tail(path, max_db=-45.0):
    """音軌比畫面長、多出來那段又是靜音，就剪到畫面長度（stream copy）。2026-10-22 第 2 集：音軌多 0.1 秒（-64 dB），
    夜跑 S8 長度檢查（≤0.05s）因此 FAIL。多出的那段有聲音就不剪，留給 S8 擋。回傳 (剪掉秒數, 尾段最大音量)。"""
    v, a = stream_dur(path, "v:0"), stream_dur(path, "a:0")
    if a - v <= 0.02:
        return 0.0, None
    err = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{v:.3f}", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"max_volume: (-?[\d.]+|-inf) dB", err)
    peak = float(m[-1]) if m and m[-1] != "-inf" else -999.0
    if peak > max_db:
        return 0.0, peak
    tmp = path + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-t", f"{v:.3f}", "-c", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, path)
    return round(a - v, 3), peak


def main():
    ap = argparse.ArgumentParser(description="Build a Concat project from plan.json (from tools/assemble/cut2plan.py) "
                                             "through Concat's MCP server (concat --mcp, stdio): no window, no token.")
    ap.add_argument("plan"); ap.add_argument("location"); ap.add_argument("name")
    ap.add_argument("--font", required=True, help="family=path")
    ap.add_argument("--voice-enhance", type=float, default=0, help="add Enhance Voice to narration clips (0–100, 0 = off)")
    ap.add_argument("--voice-match", default=r"^\d+_", help="which audio clips count as narration (file name regex)")
    ap.add_argument("--bgm-gain-db", type=float, default=0, help="extra gain in dB for music clips")
    ap.add_argument("--bgm-match", default=r"^bgm", help="which audio clips count as music (file name regex)")
    ap.add_argument("--credit", default="", help="small credit line under the last shot (e.g. the CC BY credit for the music)")
    ap.add_argument("--layers", default="", help="layers.json from PromptStudio doc_cut (side-frame host, keyword pills)")
    ap.add_argument("--photo-credits", default="", help="episode folder: small on-screen credits for photo beats (photo_credits.py)")
    ap.add_argument("--export", default="", help="after saving, export to this mp4 and run two-pass loudnorm to -14 LUFS / -2.5 dBTP")
    ap.add_argument("--ep", default="", help="episode folder for the film check (fingerprint base, skip log, series thresholds); "
                    "default: the folder above plan.json when it holds doc.json, else the folder of plan.json")
    add_no_check(ap)
    a = ap.parse_args()
    no_check = parse_no_check(ap, a.no_check)
    plan = json.load(open(a.plan, encoding="utf-8"))
    L = json.load(open(a.layers, encoding="utf-8")) if a.layers else {}
    n_layer = len(LAYER_LANES) if (L.get("side") or L.get("pills")) else 0
    layer_media = [probe(c) for c in sorted({s["clip"] for s in L.get("side", [])}) if c not in {m["path"] for m in plan["media"]}]
    fam, fpath = a.font.split("=", 1)
    proj = os.path.join(os.path.abspath(a.location), a.name)
    if os.path.exists(proj):
        sys.exit(f"a project with this name already exists; pick another name: {proj}")

    c = MCP()
    c.tool("project_create", location=os.path.abspath(a.location), name=a.name,
           video={"width": plan["width"], "height": plan["height"], "rateNum": plan["fps"], "rateDen": 1})
    batch = lambda cmds: c.tool("edit_apply", path=proj, command={"op": "batch", "commands": cmds})

    # 1 字型＋素材（一批）
    batch([{"op": "addFont", "family": fam, "path": os.path.abspath(fpath)}] +
          ([{"op": "addFont", "family": L["font"]["family"], "path": L["font"]["path"]}] if L.get("font") else []) +
          [{"op": "addMedia", "item": m} for m in plan["media"] + layer_media] +
          [{"op": "addTrack", "bottom": True} for _ in range(max(0, len(plan["tracks"]) + n_layer - 4))])
    tl = c.tool("timeline_read", path=proj)
    mid = {m["path"]: m["id"] for m in tl["media"]}
    # index 0 是最下面那條（加 bottom 軌會拿到 0；2026-10-21 實測字幕被影片蓋住）→ 由大到小＝由上往下
    lanes = [t["id"] for t in sorted(tl["timeline"]["tracks"], key=lambda t: -t["index"])]
    # 字幕軌放最上面，其次是疊加層（--layers），其餘照草稿順序往下排
    order = sorted(range(len(plan["tracks"])), key=lambda i: plan["tracks"][i]["type"] != "text")
    n_text = sum(plan["tracks"][i]["type"] == "text" for i in order)
    lane = {name: lanes[n_text + k] for k, name in enumerate(LAYER_LANES[:n_layer])}
    rest = lanes[:n_text] + lanes[n_text + n_layer:]
    lane_of = {i: rest[k] for k, i in enumerate(order)}

    # 2 片段與字幕（一批）
    cmds = []
    for i, t in enumerate(plan["tracks"]):
        for s in t["segs"]:
            if "text" in s:
                style = {"content": s["text"], "fontFamily": fam, "fontWeight": 400, "fontSize": SUB_SIZE, "color": "#ffffff",
                         "shadow": False, "align": "center", "lineHeight": 1.2}
                if s.get("bg"):
                    style["background"] = s["bg"] + f"{round(max(0, min(s['bga'], 1)) * 255):02x}"
                oy = L["en"]["zh_offsetY"] if L.get("en") else -s["y"] / 2
                if L.get("en", {}).get("shared"):
                    style, oy = shared_zh(s, style, L["en"], fpath)
                end = plan["total"] if plan["total"] - s["end"] < 0.5 else s["end"]   # 片尾字卡撐到最後一格
                cmds.append({"op": "addTextClip", "trackId": lane_of[i], "start": s["start"], "duration": round(end - s["start"], 3),
                             "style": style, "offsetY": oy})
            else:
                cmds.append({"op": "addClip", "mediaId": mid[s["path"]], "trackId": lane_of[i], "start": s["start"]})
    batch(cmds + (layer_cmds(L, lane) if n_layer else []))
    if n_layer:
        add_side(c, proj, L, lane, mid)

    # 3 修剪尾端、音量（一批）：以 (軌, 起點) 對回剛放的片段
    tl = c.tool("timeline_read", path=proj)
    have = {(x["track"], round(x["start"], 3)): x for x in tl["timeline"]["clips"]}
    fix, gaps = [], []
    for i, t in enumerate(plan["tracks"]):
        for s in t["segs"]:
            if "text" in s:
                continue
            x = have[(lane_of[i], s["start"])]
            d = x["duration"]
            if s["src"] > 0:                                # 素材不從頭用：先修片頭（畫面不滑動，長度跟著少）
                fix.append({"op": "trimClip", "clipId": x["id"], "edge": "start", "delta": s["src"]})
                d -= s["src"]
            if d > s["dur"] + 0.005:
                fix.append({"op": "trimClip", "clipId": x["id"], "edge": "end", "delta": round(s["dur"] - d, 4)})
            elif d < s["dur"] - 0.02:
                gaps.append(f"{s['name']} plan {s['dur']:.3f}s > media {d:.3f}s")
            vol = s["vol"] * (10 ** (a.bgm_gain_db / 20) if re.search(a.bgm_match, s["name"]) else 1.0)
            patch = {"volume": round(vol, 4)} if abs(vol - 1.0) > 1e-4 else {}
            if a.voice_enhance > 0 and re.search(a.voice_match, s["name"]):
                patch["filters"] = [{"id": "concat.enhance-voice", "params": {"amount": a.voice_enhance}}]
            if patch:
                fix.append({"op": "updateClip", "clipId": x["id"], "patch": patch})
    if a.credit:   # 片尾最後一個畫面片段的下方、字幕再下面一點；淺灰小字
        last = max((s for t in plan["tracks"] if t["type"] == "video" for s in t["segs"]), key=lambda s: s["start"])
        fix.append({"op": "addTextClip", "start": last["start"], "duration": round(plan["total"] - last["start"], 3), "above": True,
                    "offsetY": 0.475, "style": {"content": a.credit, "fontFamily": fam, "fontWeight": 400, "fontSize": 0.016,
                                                "color": "#9a9184", "shadow": False, "align": "center"}})
    if n_layer:
        fix += layer_fix(L, lane, have)
    if fix:
        batch(fix)
    if L.get("punch"):
        main_video = lane_of[next(i for i, t in enumerate(plan["tracks"]) if t["type"] == "video")]
        add_punch(c, proj, main_video, L["punch"])
    if L.get("chapters", {}).get("tags"):
        add_chapters(c, proj, L["chapters"], plan["total"], L["font"]["family"] if L.get("font") else fam)
    if L.get("en"):
        add_en(c, proj, L["en"], fam, plan)
    if a.photo_credits:
        from photo_credits import load as photo_rows
        cf = (L["font"]["family"], L["font"]["path"]) if L.get("font") else (fam, fpath)
        add_photo_credits(c, proj, photo_rows(a.photo_credits), *cf)
    c.tool("project_save", path=proj)
    tl = c.tool("timeline_read", path=proj)
    if a.export:
        out = os.path.abspath(a.export)
        grain = int(L.get("grain", 0))

        def post(path):
            loudnorm(path, grain=grain)
            cut, peak = trim_silent_tail(path)
            if cut:
                print(f"trimmed {cut}s of silent audio tail (tail peak {peak} dB)", file=sys.stderr)
            elif peak is not None:
                print(f"audio is longer than the video, but the tail is not silent (peak {peak} dB); not trimmed", file=sys.stderr)
            return path
        plan_dir = os.path.dirname(os.path.abspath(a.plan))
        ep = a.ep or (os.path.dirname(plan_dir) if os.path.exists(os.path.join(os.path.dirname(plan_dir), "doc.json")) else plan_dir)
        inputs = [a.plan, *(m["path"] for m in plan["media"]), *(m["path"] for m in layer_media)] + \
                 [os.path.join(ep, f) for f in ("beats.json", "tts/voice.wav", "sfx/sfx_bed.wav", "score_bgm.wav")] + \
                 ([a.layers] if a.layers else []) + [os.path.abspath(fpath)]
        try:   # 有顆粒的片在 loudnorm 那一步才重編碼（那裡帶 crf），Concat 這一步照預設匯出，免得壓兩次
            concat_export(c, proj, out, crf=None if grain else "default", post=post, ep=ep, inputs=inputs, no_check=no_check)
        except FilmCheckFailed:
            c.p.stdin.close(); c.p.wait(timeout=30)
            sys.exit(1)
    c.p.stdin.close(); c.p.wait(timeout=30)
    print(json.dumps({"project": proj, "clips": len(tl["timeline"]["clips"]), "duration": tl["timeline"]["duration"], "fixes": len(fix), "short": gaps},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
