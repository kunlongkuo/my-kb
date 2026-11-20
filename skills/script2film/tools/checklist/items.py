"""清單的項目：每一項屬於一層（base 通則／format 格式／series 系列）
與一段（start 開工前／release 出片前），函式回傳幾列 (名稱, 通過, 說明)；回傳空的表示這一集沒有這一項。

ctx：{"ep": 集資料夾, "format": "doc"|"book", "doc": doc.json 或 day.json 的內容, "series": series.json 的內容或 None,
      "series_dir": 系列資料夾, "environ": 環境變數}
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC_SCRIPTS = REPO / "skills/ve-director/doc/scripts"


def yt_python(environ):
    """跑 yt_upload.py 用的直譯器：S2F_YT_PYTHON 有設就用它，否則倉庫內 tools/youtube/.venv 的 python。"""
    return Path(environ["S2F_YT_PYTHON"]) if environ.get("S2F_YT_PYTHON") else REPO / "tools/youtube/.venv/bin/python"


def concat_bin(environ):
    """Concat 執行檔：S2F_CONCAT_BIN 有設就只用它，否則舊名 CONCAT_BIN，都沒設用預設路徑。"""
    return Path(environ.get("S2F_CONCAT_BIN") or environ.get("CONCAT_BIN") or "/Applications/Concat.app/Contents/MacOS/concat")


CONCAT = concat_bin(os.environ)
NODE_MIN = 22      # doc_common.NODE_MIN：HyperFrames 要 Node 22 以上
MIN_FREE_GB = 5    # 一集做完約 1.1 GB（實測，含 VE 重抽與三版成片），留 4 倍以上


def check_triggers(doc, P):
    """只用稿面文字驗觸發字（真正逐字時間要配音後才有，S3 後 doc_code 會再驗一次）：抓錯字與 burst_title 不在句首。"""
    sys.path.insert(0, str(DOC_SCRIPTS))
    from doc_code import missing_triggers
    from doc_common import tokens
    lines, bad = doc["lines"], []
    for b in doc["beats"]:
        if b.get("source") != "code":
            continue
        text = "".join(lines[i - 1]["text"] for i in b["lines"])
        if b.get("from"):
            k = text.find(b["from"])
            if k < 0:
                bad.append(f"{b['id']}: from={b['from']!r} is not in the line")
                continue
            text = text[k:]
        fake = {"tokens": [[c, 0] for c in tokens(text, doc["lang"])]}
        if (m := missing_triggers(b.get("params", {}), fake, doc["lang"])):
            bad.append(f"{b['id']}: {', '.join(m)}")
        if b.get("scene") == "burst_title":
            w = tokens(b["params"].get("word", ""), doc["lang"])
            if [t[0] for t in fake["tokens"][:len(w)]] != w:
                bad.append(f"{b['id']}: burst_title word={b['params'].get('word')!r} does not open the line")
    return bad


def facts_problems(doc, P):
    """doc.json "facts" (doc_facts, FORMAT §9): what does not match facts.md; [] when the doc has no list."""
    sys.path.insert(0, str(DOC_SCRIPTS))
    import doc_facts
    return doc_facts.check(doc, P)


REQUIRED_ENV = ("S2F_QWEN_TTS_DIR", "S2F_WHISPER_CPP_MODEL")
OPTIONAL_ENV = ("S2F_ASSETS_LOCAL",)   # 使用者素材層：音效已隨倉庫附帶（assets/sfx），這層只是選用的覆蓋層
OLD_ENV = {"S2F_QWEN_TTS_DIR": "QWEN_TTS_DIR"}   # 舊名，相容讀法
SECRET_FILES = ("~/.config/script2film/secrets.json",)


def env_items(environ):
    """環境變數那幾列 (名稱, 通過, 說明)。必要的兩個要設且路徑存在（配音是資料夾、轉錄模型是檔）；和執行期同一條規則：新名有設就只驗新名的路徑，
    新名沒設才看去掉 S2F_ 的舊名；列名一律顯示新名。選用的 S2F_ASSETS_LOCAL（沒有舊名）沒設照樣通過，
    只用內附素材；有設就要資料夾存在，設錯路徑要擋。"""
    out = []
    for env in REQUIRED_ENV:
        v, old = environ.get(env), OLD_ENV.get(env)
        used = env if v else None
        if not v and old and environ.get(old):
            v, used = environ[old], old
        detail = "not set" if not v else v if used == env else f"{v} (old name {used})"
        out.append((f"env {env}", bool(v and Path(v).expanduser().exists()), detail))
    for env in OPTIONAL_ENV:
        v = environ.get(env)
        if not v:
            out.append((f"env {env}", True, "not set: bundled assets only"))
        else:
            ok = Path(v).expanduser().is_dir()
            out.append((f"env {env}", ok, v if ok else f"{v} does not exist (optional: remove the setting if you do not use it)"))
    return out


def has_secret(name):
    """金鑰檔（SECRET_FILES）裡有沒有這個鍵；檔不在算沒有。只回 True／False，不讀出值。"""
    for f in SECRET_FILES:
        p = Path(f).expanduser()
        if p.exists() and name in json.loads(p.read_text()):
            return True
    return False


def yt_item(py, script):
    """「YouTube 權杖與範圍」那一列的 (通過與否, 說明)。直譯器不在就回不過並說怎麼補，不讓整支檢查當掉。"""
    if not Path(py).exists():
        return False, f"{py} not found: set S2F_YT_PYTHON, or create the venv as tools/youtube/README.md says"
    r = subprocess.run([py, script, "scopes"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout or r.stderr).strip()[-200:]


def font_item(series, series_dir):
    """series.json 選用欄位 "font"（Concat --font 的寫法 <family>=<路徑>，路徑相對於系列資料夾）那一列
    (名稱, 檔案存在, 解析後的路徑)；沒有這個欄位回 None，不出這一列。"""
    if "font" not in series:
        return None
    family, path = series["font"].split("=", 1)
    p = Path(path)
    if not p.is_absolute():
        p = Path(series_dir) / p
    return (f"font {family}", p.exists(), str(p))


UPLOAD_FIELDS = ("backup", "desc_head", "desc_body", "hook_lines")   # yt_meta.py 產標題與說明欄要的欄位


def series_cfg(ep_dir):
    """(series.json 的內容, 系列資料夾)；上一層沒有 series.json 回 (None, 系列資料夾)：單集專案，系列層不跑。
    有檔但沒有 "name" 就停：那是寫壞的設定，不是單集。"""
    d = Path(ep_dir).resolve().parent
    p = d / "series.json"
    if not p.exists():
        return None, d
    s = json.loads(p.read_text(encoding="utf-8"))   # 檔壞了丟 ValueError，checklist 轉成設定錯誤（退出碼 2）
    if not isinstance(s, dict) or not s.get("name"):
        raise ValueError(f"{p} has no name")
    return s, d


def release_check(ep):
    """出片檢查（tools/nightly/check.py）的結果：nightly/check.json 的 ok 是 true，而且不比它檢查的那支成片舊。"""
    p = Path(ep) / "nightly/check.json"
    if not p.exists():
        return False, "no nightly/check.json: run tools/nightly/check.py first"
    c = json.loads(p.read_text(encoding="utf-8"))
    if not c.get("ok"):
        return False, "ok in check.json is not true"
    v = Path(c.get("video", ""))
    video = next((x for x in (v, Path(ep) / v.name) if v.name and x.exists()), None)
    if video is None:
        return False, f"film not found: {c.get('video')}"
    if p.stat().st_mtime < video.stat().st_mtime:
        return False, f"check.json is older than the film {video.name}: the film changed, run the film check again"
    return True, video.name


def film_record(video):
    """成片體檢紀錄（tools/nightly/film_check.py 寫在片旁的 <片名>.check.json）：ok 是 true、紀錄裡的 SHA-256 等於現在這支片、
    出片時記的剪接用檔指紋（<片名>.inputs.json）沒有變。沒有指紋檔的片（這項檢查之前出的）不因此擋。"""
    sys.path.insert(0, str(REPO / "tools/nightly"))
    import film_check
    video = Path(video)
    if not video.is_file():
        return False, f"film not found: {video}"
    rec_f, inputs_f = film_check.record_paths(video)
    if not rec_f.exists():
        return False, f"no film check record {rec_f.name}: run tools/nightly/film_check.py {video.name} (Concat exports write it)"
    rec = json.loads(rec_f.read_text(encoding="utf-8"))
    if not rec.get("ok"):
        return False, f"ok in {rec_f.name} is not true"
    if rec.get("size") != video.stat().st_size or rec.get("sha256") != film_check.sha256(video):
        return False, f"{video.name} changed after it was checked: run the film check again"
    fresh, value, notes = film_check.stale(inputs_f)
    if fresh is False:
        return False, f"{video.name} is older than its inputs ({'; '.join(notes[:3])}): export it again"
    return True, video.name + ("" if fresh else " (no inputs fingerprint)")


def film_record_for(ep, video=None):
    """要上傳的那支（video）；沒給就用 nightly/check.json 記的片，再沒有就用集資料夾裡最新一份片旁紀錄的片。
    舊集數（片旁紀錄出現前）只有 nightly/check.json：照舊用 release_check 判。"""
    ep = Path(ep)
    if video is None:
        chk = ep / "nightly/check.json"
        if chk.exists():
            v = Path(json.loads(chk.read_text(encoding="utf-8")).get("video", ""))
            video = next((x for x in (v, ep / v.name) if v.name and x.exists()), None)
        if video is None:
            recs = sorted(ep.glob("*.check.json"), key=lambda f: f.stat().st_mtime)
            if not recs:
                return False, "no film check record in this folder: export through Concat (it checks the film) or run tools/nightly/film_check.py"
            video = recs[-1].with_name(recs[-1].name[:-len(".check.json")] + ".mp4")
    video = Path(video)
    if not (video.with_name(video.stem + ".check.json")).exists() and (ep / "nightly/check.json").exists():
        return release_check(ep)
    return film_record(video)


# ---- 每一項：ctx -> [(名稱, 通過, 說明)] ----

def _lexicon(c):
    lexicon = load_module("s2f_lexicon", REPO / "tools/tts/lexicon.py")
    try:
        rules = lexicon.load()
    except (OSError, ValueError, KeyError) as e:
        return [("pronunciation table", False, f"cannot load: {e}")]
    bad = lexicon.problems(rules)
    return [("pronunciation table", not bad, "; ".join(bad) if bad else f"{len(rules)} rules")]


def _inventory(c):
    """素材盤點（FORMAT §6 第 7 點）：量得出來就過，三個數印出來；系列有目標時並排標出超出的，只印不擋。"""
    inventory = load_module("s2f_inventory", REPO / "tools/qa/inventory.py")
    inv = inventory.run(c["ep"], write=c.get("write", True))
    targets = ((c["series"] or {}).get("checklist") or {}).get("targets") or {}
    over = inventory.over_targets(inv, targets)
    return [("inventory (report only)", True, inventory.summary(inv) + ("; over target: " + ", ".join(over) if over else ""))]


RETIME = "time it again"   # _blank_lead says this when beats.json is stale; _lead_estimate then falls back to the estimate
SEC_PER_CHAR = 0.21   # 和 tools/qa/inventory.py 的預設一樣：中文每字秒數，含句間停頓


def _lead_estimate(c):
    """開工段：還沒配音就用稿面字數估引言卡、數字卡幾秒才出現（每字 SEC_PER_CHAR 秒），超過 doc_code.LEAD_MAX 就擋。
    改法不花錢（改 at），所以擋在配音與送 VE 之前。只估中文稿；已經對時過就用實測（_blank_lead）。"""
    if (c["ep"] / "beats.json").exists():
        rows = _blank_lead(c)
        if RETIME not in rows[0][2]:   # 對時結果是新的：用實測
            return rows
    doc = c["doc"]
    if doc.get("lang", "zh") != "zh":
        return [("blank card lead (script estimate)", True, "not a Chinese script: measured after timing")]
    sys.path.insert(0, str(DOC_SCRIPTS))
    import doc_code
    from doc_common import tokens
    bad = []
    for b in doc["beats"]:
        if b.get("source") != "code" or b.get("scene") not in doc_code.EMPTY_UNTIL_AT:
            continue
        text = "".join(doc["lines"][i - 1]["text"] for i in b["lines"])
        if b.get("from") and b["from"] in text:
            text = text[text.find(b["from"]):]
        fake = {"id": b["id"], "lines": b["lines"], "tokens": [[t, round(i * SEC_PER_CHAR, 2)] for i, t in enumerate(tokens(text, "zh"))]}
        m = doc_code.empty_first_line(doc, fake, b) or doc_code.late_first_element(doc, fake, b)
        if m:
            bad.append(m)
    return [("blank card lead (script estimate)", not bad, ("; ".join(bad) + " (estimate; set at to a word that opens this beat or a number like 0.3, or add bg_video/photos underneath)") if bad else "")]


def _blank_lead(c):
    """引言卡、數字卡開頭空白（用對時後的 beats.json 實測）：觸發字落在第二句以後（doc_code.empty_first_line），或落在
    第一句裡但晚於 1.0 秒、畫面上又沒有別的東西（doc_code.late_first_element），都擋。"""
    bj = c["ep"] / "beats.json"
    if not bj.exists():
        return [("blank card lead", False, "not timed yet (no beats.json)")]
    sys.path.insert(0, str(DOC_SCRIPTS))
    import doc_code
    spec = {b["id"]: b for b in c["doc"]["beats"]}
    timed = {b["id"]: b for b in json.loads(bj.read_text(encoding="utf-8"))["beats"]}
    stale = [i for i, b in spec.items() if b.get("scene") in doc_code.EMPTY_UNTIL_AT and (b.get("params") or {}).get("at")
             and not (timed.get(i) or {}).get("tokens")]
    if stale:   # 稿子有這一拍、對時結果裡沒有：beats.json 是舊的，量不了
        return [("blank card lead", False, f"beats.json has no word timing for these beats, {RETIME}: " + ", ".join(stale))]
    beats = [b for b in timed.values() if b["id"] in spec and b.get("tokens")]
    bad = [m for b in beats if (m := doc_code.empty_first_line(c["doc"], b, spec[b["id"]])
                                or doc_code.late_first_element(c["doc"], b, spec[b["id"]]))]
    return [("blank card lead", not bad, "; ".join(bad))]


def caption_files(ep):
    """這一集要上傳的字幕檔 [(語言, 路徑)]：最新的 cut_<色版>/ 資料夾裡旁白語言的那一份，加上有翻譯的那一份
    （doc_cut.write_caption_files 寫的；路徑不管檔在不在都回）。沒剪過（沒有 cut_* 資料夾）回空的。"""
    ep = Path(ep)
    doc = json.loads((ep / "doc.json").read_text(encoding="utf-8"))
    def newest(p):   # 資料夾與裡面字幕檔的修改時間取最新的：--captions-only 只覆寫字幕檔，資料夾的時間不會變
        return max([p.stat().st_mtime] + [f.stat().st_mtime for f in p.glob("subtitles_*.srt")])
    cuts = sorted((p for p in ep.glob("cut_*") if p.is_dir()), key=newest)
    if not cuts:
        return []
    lang = "en" if str(doc.get("lang", "zh")).lower().startswith("en") else "zh"
    langs = [lang] + [k for k in ("en", "zh") if doc.get(k) and k != lang]
    return [(k, cuts[-1] / f"subtitles_{k}.srt") for k in langs]


def caption_hint(ep):
    """上傳成功後印給人看的那一段：要手動傳哪幾個字幕檔、在 YouTube Studio 哪裡傳。沒有檔回空字串。"""
    have = [(k, p) for k, p in caption_files(ep) if p.exists()]
    if not have:
        return ""
    return "\n".join(["Upload the subtitles by hand (YouTube Studio → Subtitles → this video → Add language → Add → Upload file → With timing):"]
                     + [f"  {k}  {p}" for k, p in have])


def _subs_files(c):
    """字幕檔（FORMAT §4d 第 4 點）：集或系列有設 subs.burn 才查；每個該有的檔都在，而且不比對時結果舊。"""
    burn = next((s["burn"] for s in (c["doc"].get("subs"), (c["series"] or {}).get("subs"))
                 if isinstance(s, dict) and s.get("burn")), None)
    if not burn:
        return [("subtitle files", True, "subs.burn not set: not checked")]
    files = caption_files(c["ep"])
    if not files:
        return [("subtitle files", False, "not cut yet (no cut_<theme>/): run doc_cut.py first")]
    bj = c["ep"] / "beats.json"
    bad = []
    for _, p in files:
        if not p.exists():
            bad.append(f"no {p.parent.name}/{p.name}: run doc_cut.py --captions-only")
        elif bj.exists() and p.stat().st_mtime < bj.stat().st_mtime:
            bad.append(f"{p.parent.name}/{p.name} is older than beats.json: run doc_cut.py again")
    return [("subtitle files", not bad, "; ".join(bad) if bad else "upload by hand after the video: " + ", ".join(f"{p.parent.name}/{p.name}" for _, p in files))]


MEDIA_EXT = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"}


def load_module(name, path):
    """照路徑載入工具裡的模組，取一個不會撞名的名字（各集資料夾裡可能有同名的 lexicon.py、inventory.py）。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        del sys.modules[name]   # 載到一半失敗的不留著，下次重新載
        raise
    return mod


def unlisted_assets(ep):
    """<集>/assets/ 底下的圖檔與影片檔（不含 src/ 子資料夾）裡，檔名沒出現在 assets/CREDITS.md 的
    （工具自己去背產生的 <名>_fg.png 跟著原圖算）。沒有 assets/ 回空的。"""
    d = Path(ep) / "assets"
    if not d.is_dir():
        return []
    credits = (d / "CREDITS.md").read_text(encoding="utf-8") if (d / "CREDITS.md").exists() else ""
    files = [p for p in sorted(d.rglob("*")) if p.is_file() and p.suffix.lower() in MEDIA_EXT and "src" not in p.relative_to(d).parts]
    # <名>_fg.png 是 doc_cutout 從 <名>.* 去背產生的，原圖有登記就算數
    def listed(name):   # 整個檔名，不是別的檔名的一部分（a.png 不能被 banana.png 蓋過）
        return re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])", credits) is not None
    def source_listed(name):
        stem = name[:-len("_fg.png")]
        return re.search(r"(?<![\w.-])" + re.escape(stem) + r"\.\w+(?![\w-])", credits) is not None
    return [str(p.relative_to(d)) for p in files
            if not listed(p.name) and not (p.name.endswith("_fg.png") and source_listed(p.name))]


def _credits(c):
    miss = unlisted_assets(c["ep"])
    return [("outside media log assets/CREDITS.md", not miss, "not listed: " + ", ".join(miss) if miss else "")]


def _disk(c):
    free = shutil.disk_usage(c["ep"]).free / 1e9
    return [(f"free disk ≥ {MIN_FREE_GB} GB", free >= MIN_FREE_GB, f"{free:.0f} GB")]


def _node(c):
    node = shutil.which("node")   # 渲染入口直接用 PATH 上的 node
    ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
    head = ver.lstrip("v").split(".")[0]
    major = int(head) if head.isdigit() else 0
    return [(f"node ≥ {NODE_MIN} (on PATH)", major >= NODE_MIN, f"{ver or 'not found'} ({node or 'no node on PATH'})")]


def _power(c):
    if not shutil.which("pmset"):   # 只有 macOS 有；別的系統查不了，不擋
        return [("on AC power (reminder only)", True, "no pmset on this machine: not checked")]
    r = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    first = r.stdout.splitlines()[0] if r.stdout else ""
    return [("on AC power (reminder only)", True, first if "AC Power" in r.stdout else f"not on AC power: long renders will slow down. {first}")]


def _concat(c):
    p = concat_bin(c["environ"])
    return [("Concat executable", p.exists(), str(p))]


def _env_dirs(c):
    return env_items(c["environ"])


def _yt_token(c):
    return [("YouTube token and scopes", *yt_item(yt_python(c["environ"]), REPO / "tools/youtube/yt_upload.py"))]


def _voice_ref(c):
    ref = c["doc"]["voice"]["ref_wav"]
    return [("host reference voice", (c["ep"] / ref).exists(), ref)]


def _triggers(c):
    bad = check_triggers(c["doc"], c["ep"])
    return [("trigger words (script)", not bad, "; ".join(bad))]


def _facts(c):
    if not c["doc"].get("facts"):
        return []
    fb = facts_problems(c["doc"], c["ep"])
    return [("fact list facts.md", not fb, "; ".join(fb)[:300])]


def _no_dash(c):
    dash = [i + 1 for i, l in enumerate(c["doc"]["lines"]) if "—" in l["text"]]
    return [("no em dash in narration", not dash, f"lines {dash}" if dash else "")]


def _asr_keys(c):
    """只提示不擋：沒有金鑰時 doc_align 退回本機轉錄。"""
    env = c["environ"]
    out = [("Groq key (needed only when the script says \"asr\": \"cloud\"; not blocking)", True,
            "present" if env.get("GROQ_API_KEY") or has_secret("GROQ_API_KEY") else "none → local whisper.cpp")]
    if c["doc"].get("asr") == "cloud":
        has = any(env.get(k) or has_secret(k) for k in ("ELEVENLABS_API_KEY", "ELEVEN_API_KEY"))
        out.append(("ElevenLabs Scribe key (the script says \"asr\": \"cloud\"; not blocking)", True, "present" if has else "none → local whisper.cpp"))
    return out


def _bgm_file(c):
    bgm = (c["ep"] / c["doc"]["bgm"]["src"]) if c["doc"].get("bgm") else None
    return [("music file", bool(bgm and bgm.exists()), str(bgm))]


def _bgm_credit(c):
    return [("music credit", bool(c["doc"].get("bgm", {}).get("credit")), "")]


def _thumb(c):
    th, P = c["doc"].get("thumb") or {}, c["ep"]   # stills/ 的圖收片後才抽，這裡只驗其他檔
    miss = [th[k] for k in ("bg", "cut", "pic", "logo") if th.get(k) and not th[k].startswith("stills/") and not (P / th[k]).exists()]
    ok = bool(th.get("title") and (th.get("bg") or th.get("pic")) and not miss)
    detail = ("no thumb field" if not th else "missing files " + ", ".join(miss) if miss else "no title" if not th.get("title")
              else "no bg or pic" if not (th.get("bg") or th.get("pic")) else th["title"])
    return [("thumbnail settings thumb", ok, detail)]


def _release_check(c):
    return [("film check check.json", *release_check(c["ep"]))]


def _film_record(c):
    return [("film check record", *film_record_for(c["ep"], c.get("video")))]


def _series(c):
    return [("series settings series.json", True, c["series"]["name"])]


def _font(c):
    f = font_item(c["series"], c["series_dir"])
    return [f] if f else []


def _upload_fields(c):
    miss = [k for k in UPLOAD_FIELDS if k not in c["series"]]
    return [("upload fields", not miss, "missing " + ", ".join(miss) if miss else "")]


def _item(id, layer, stage, fn, format=None, na_ok=False, label=None):
    return {"id": id, "layer": layer, "format": format, "stage": stage, "na_ok": na_ok, "fn": fn, "label": label or id}


ITEMS = [
    _item("disk", "base", "start", _disk),
    _item("node", "base", "start", _node),
    _item("power", "base", "start", _power),
    _item("concat", "base", "start", _concat),
    _item("env-dirs", "base", "start", _env_dirs),
    _item("lexicon", "base", "start", _lexicon),
    _item("voice-ref", "format", "start", _voice_ref, "doc"),
    _item("triggers", "format", "start", _triggers, "doc"),
    _item("facts", "format", "start", _facts, "doc"),
    _item("no-dash", "format", "start", _no_dash, "doc"),
    _item("asr-keys", "format", "start", _asr_keys, "doc"),
    _item("inventory", "format", "start", _inventory, "doc"),
    _item("lead-est", "format", "start", _lead_estimate, "doc"),
    _item("series", "series", "start", _series),
    _item("font", "series", "start", _font),
    _item("yt-token", "base", "release", _yt_token),
    _item("credits", "base", "release", _credits),
    _item("film-check", "base", "release", _film_record),
    _item("bgm-file", "format", "release", _bgm_file, "doc"),
    _item("bgm-credit", "format", "release", _bgm_credit, "doc"),
    _item("thumb", "format", "release", _thumb, "doc"),
    _item("release-check", "format", "release", _release_check, "doc"),
    _item("blank-lead", "format", "release", _blank_lead, "doc"),
    _item("subs-files", "format", "release", _subs_files, "doc", label="subtitle files"),
    _item("upload-fields", "series", "release", _upload_fields, na_ok=True, label="upload fields"),
]
