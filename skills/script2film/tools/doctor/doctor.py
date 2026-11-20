"""安裝檢查：這台機器缺什麼。只檢查、印修法，不安裝、不下載、不連線。

  python3 tools/doctor/doctor.py                       零付費路徑的項目缺了才算失敗
  python3 tools/doctor/doctor.py --need concat,ve,tp,youtube   把這幾組也當必要
  python3 tools/doctor/doctor.py --json                給其他腳本讀
  python3 tools/doctor/doctor.py --skip voice          配音與轉錄兩項缺了不算失敗，印 skipped（CI 不裝 6 GB 的模型）

每一項一行：✓ 通過、✗ 要處理（下一行 → 修法）、－ 選用功能沒裝（下一行 → 要用時怎麼裝）。
退出碼：0 可以開始；1 必要的項目有 ✗；2 設定檔讀不進來；64 用法錯誤。
三組：必要（零付費路徑：手寫稿、本機配音與轉錄、doc_cut.py --render）、concat／ve／tp／youtube（選用，--need 可升成必要）、
另有兩項提醒不影響退出碼。項目與查法在 README.md。
"""
import importlib.util
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/config"))
import s2f_config  # noqa: E402

GROUPS = ("concat", "ve", "tp", "youtube")
SKIPS = {"voice": ("voice (TTS)", "transcription")}   # --skip 的名字 → 跳過的項目
PACKAGES = {"pytest": "pytest", "opencc": "opencc-python-reimplemented", "PIL": "pillow", "numpy": "numpy",
            "fontTools": "fonttools", "playwright": "playwright", "soundfile": "soundfile"}   # 匯入名 → pip 套件名；和 requirements.txt 同一份
QWEN_MODEL = "Qwen3-TTS-12Hz-1.7B-Base"
WHISPER_MODEL = "ggml-large-v3-turbo.bin"
CONFIG_HINT = "~/.config/script2film/config.json"


def row(name, group, ok, detail="", fix=""):
    return {"name": name, "group": group, "status": "ok" if ok else "fail", "detail": detail, "fix": "" if ok else fix}


def check_system(system, machine):
    ok = (system == "Darwin" and machine == "arm64") or (system in ("Windows", "Linux"))
    return row("system", "required", ok, f"{system} {machine}", "macOS (Apple Silicon), Windows and Linux are supported")


def check_packages(missing, has_venv=False):
    """missing：匯入不到的匯入名。has_venv：倉庫根目錄有沒有 .venv。
    套件裝在倉庫自己的 .venv 裡（Homebrew 的 Python 不讓人直接 pip install）；之後照常用 python3 跑，程式會自己改用它。"""
    fix = (".venv/bin/python -m pip install -r requirements.txt (in the repository root)" if has_venv else
           "In the repository root, run python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
           " (keep running scripts with python3: they switch to .venv on their own)")
    return row("python packages", "required", not missing, "missing " + ", ".join(missing) if missing else ", ".join(PACKAGES), fix)


def check_ffmpeg(ffmpeg, ffprobe, encoders):
    """ffmpeg／ffprobe：找到的路徑或 None；encoders：`ffmpeg -encoders` 的輸出。"""
    if not ffmpeg or not ffprobe:
        return row("ffmpeg", "required", False, "not found: " + ", ".join(n for n, p in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if not p),
                   "brew install ffmpeg")
    return row("ffmpeg", "required", "libx264" in encoders, ffmpeg if "libx264" in encoders else "this ffmpeg has no libx264",
               "brew install ffmpeg")


def check_node(version, minimum):
    """version：`node --version` 的輸出（例 v22.3.0）或 None。"""
    try:
        major = int(version.strip().lstrip("v").split(".")[0])
    except (AttributeError, ValueError):
        return row("node", "required", False, "node not found", "brew install node")
    return row("node", "required", major >= minimum, f"{version.strip()} (needs {minimum} or later)", "brew install node")


def check_hyperframes(package_dir, why=""):
    """package_dir：找到的 HyperFrames 套件資料夾，或 None（why：找不到的原因）。"""
    return row("HyperFrames", "required", bool(package_dir), str(package_dir or why or "node_modules/hyperframes not found"),
               "In the repository root, run npm ci (or point S2F_HF_BIN at the package folder)")


def check_gsap(repo):
    f = Path(repo) / "node_modules/gsap/dist/gsap.min.js"
    return row("GSAP", "required", f.is_file(), str(f) if f.is_file() else f"{f} does not exist",
               "In the repository root, run npm ci (the animation library for the scenes; copied next to the page at render time, no CDN)")


def check_render_browser(environ, home):
    hint = environ.get("HYPERFRAMES_BROWSER_PATH")
    if hint:
        return row("render browser", "required", Path(hint).exists(), hint,
                   f"HYPERFRAMES_BROWSER_PATH={hint} does not exist: fix the path, or unset it")
    root = Path(home) / ".cache/hyperframes/chrome"
    found = next((p for p in root.rglob("chrome-headless-shell*") if p.is_file()), None) if root.is_dir() else None
    return row("render browser", "required", bool(found), str(found or f"no chrome-headless-shell under {root}"),
               "In the repository root, run npx hyperframes browser ensure")


PW_INSTALL = ("--only-shell", "chromium")   # 和 docs/INSTALL.md 第 3 步、CI 同一條
PW_FIX = ".venv/bin/python -m playwright install " + " ".join(PW_INSTALL) + " (in the repository root; about 97 MB)"


def check_playwright_browser(locations, why=""):
    """locations：`playwright install --dry-run` 列的安裝位置（無頭殼與錄影用的 ffmpeg；尊重 PLAYWRIGHT_BROWSERS_PATH），
    None 表示問不到（why：原因）。每個位置都要有 Playwright 裝完才寫的 INSTALLATION_COMPLETE。測試讀場景頁、doc_code.py 的
    sfx_on 與螢幕錄製拍都用這個瀏覽器；送 VE、TP 用的是系統的 Chrome，不在這一項。"""
    if not locations:
        return row("playwright browser", "required", False, why or "cannot ask playwright where its browser goes", PW_FIX)
    miss = [str(p) for p in locations if not (Path(p) / "INSTALLATION_COMPLETE").exists()]
    return row("playwright browser", "required", not miss,
               "missing " + ", ".join(miss) if miss else ", ".join(str(p) for p in locations), PW_FIX)


def _pw_locations():
    """(安裝位置的清單或 None, 問不到的原因)：問 Playwright 自己（--dry-run 只印位置，不下載、不連線、不開瀏覽器）。"""
    if importlib.util.find_spec("playwright") is None:
        return None, "the playwright package is not installed (see python packages)"
    out = _run(sys.executable, "-m", "playwright", "install", "--dry-run", *PW_INSTALL)
    found = [Path(l.split(":", 1)[1].strip()) for l in (out or "").splitlines() if l.strip().startswith("Install location:")]
    return (found, "") if found else (None, "playwright install --dry-run listed no install location")


def _tool_dir(environ, key, label):
    """(資料夾或 None, 失敗時的那一列或 None)：key 沒設、資料夾不存在、沒有 .venv/bin/python 各有各的修法。"""
    v = environ.get(key) or environ.get(s2f_config.OLD_NAMES.get(key, ""), "")
    if not v:
        return None, row(label, "required", False, f"{key} is not set",
                         f"Not installed yet: run bash tools/doctor/setup_voice.sh (sets up the voice and transcription environments, "
                         f"downloads the voice model and writes the config file; about 20 minutes, 6 GB, see docs/INSTALL.md). "
                         f"Already installed: add \"{key}\": \"<folder>\" to {CONFIG_HINT}")
    d = Path(v).expanduser()
    if not d.is_dir():
        return None, row(label, "required", False, f"{key}={d} does not exist", f"Set {key} to the correct path (now {d})")
    if not (d / ".venv/bin/python").exists():
        return None, row(label, "required", False, f"no .venv/bin/python in {d}", f"Create the Python environment (.venv) in {d}")
    return d, None


def check_tts(environ):
    d, bad = _tool_dir(environ, "S2F_QWEN_TTS_DIR", "voice (TTS)")
    if bad:
        return bad
    m = environ.get("S2F_QWEN_TTS_MODELS") or environ.get("QWEN_TTS_MODELS")
    models = Path(m).expanduser() if m else d.parent / "_models"
    ok = (models / QWEN_MODEL).is_dir()
    return row("voice (TTS)", "required", ok, str(d) if ok else f"no {QWEN_MODEL} in {models}",
               f"Download Qwen/{QWEN_MODEL} from Hugging Face (about 4.2 GB, Apache-2.0) to {models}/{QWEN_MODEL}")


def check_asr(environ, which=shutil.which):
    """轉錄（whisper.cpp）：模型檔要在、whisper-cli 要找得到（S2F_WHISPER_CLI 或 PATH）。只設了舊的 mlx 資料夾就說換掉了。"""
    setup = (f"Not installed yet: run bash tools/doctor/setup_voice.sh (installs whisper.cpp and downloads {WHISPER_MODEL}, "
             f"about 1.6 GB). Already have it: add \"S2F_WHISPER_CPP_MODEL\": \"<the .bin file>\" to {CONFIG_HINT}")
    v = environ.get("S2F_WHISPER_CPP_MODEL")
    if not v:
        old = environ.get("S2F_MLX_WHISPER_DIR") or environ.get("MLX_WHISPER_DIR")
        why = "S2F_WHISPER_CPP_MODEL is not set" + (" (S2F_MLX_WHISPER_DIR is no longer used: mlx-whisper was replaced by whisper.cpp)" if old else "")
        return row("transcription", "required", False, why, setup)
    m = Path(v).expanduser()
    if not m.is_file():
        return row("transcription", "required", False, f"S2F_WHISPER_CPP_MODEL={m} does not exist", setup)
    cli = environ.get("S2F_WHISPER_CLI") or which("whisper-cli")
    if not cli or not Path(cli).expanduser().is_file():
        return row("transcription", "required", False, f"whisper-cli not found ({cli or 'not on PATH'})",
                   "macOS: brew install whisper.cpp; other systems: build github.com/ggml-org/whisper.cpp and set S2F_WHISPER_CLI")
    return row("transcription", "required", True, f"{m} ({cli})")


FONT_URL = "https://github.com/google/fonts/raw/main/ofl"
FONT_FIX = ("The fonts are not in git (OFL 1.1). In the repository root, run these two downloads (about 29 MB in all): "
            f"curl -L -o assets/fonts/NotoSansTC-Variable.ttf '{FONT_URL}/notosanstc/NotoSansTC%5Bwght%5D.ttf' && "
            f"curl -L -o assets/fonts/NotoSerifTC-Variable.ttf '{FONT_URL}/notoseriftc/NotoSerifTC%5Bwght%5D.ttf'")


SFX_FIX = ("The sound effects ship with the repository (assets/sfx is in git): in the repository root, run git checkout -- assets/sfx "
           "to restore them, or point S2F_ASSETS at the correct folder")


def check_assets(environ, repo):
    """內附素材層：兩份 manifest 都在，而且列的每個檔都在。音效隨倉庫附帶；字型檔不在 git 裡，要另外下載（assets/README.md）。"""
    a = Path(environ["S2F_ASSETS"]).expanduser() if environ.get("S2F_ASSETS") else Path(repo) / "assets"
    miss = [p for p in ("fonts/manifest.json", "sfx/manifest.json") if not (a / p).exists()]
    n = {}
    if not miss:
        for kind in ("fonts", "sfx"):
            try:
                files = [f"{kind}/{x['file']}" for x in json.loads((a / kind / "manifest.json").read_text(encoding="utf-8"))
                         if not x.get("optional")]   # 選用字型（optional）不擋：assets/README.md「Optional fonts」
            except (ValueError, OSError, KeyError, TypeError, AttributeError):
                return row("bundled assets", "required", False, f"cannot read {a}/{kind}/manifest.json",
                           f"The manifest must be [{{\"file\": \"<file name>\"}}, …]; restore it with git (git checkout -- assets/{kind}/manifest.json)")
            n[kind] = len(files)
            miss += [p for p in files if not (a / p).is_file()]
    detail = f"{a} (fonts: {n.get('fonts', 0)}, sounds: {n.get('sfx', 0)})" if not miss else f"{a} is missing " + ", ".join(miss[:5]) + (
        f" and more ({len(miss)} in all)" if len(miss) > 5 else "")
    fix = (FONT_FIX if any(p.startswith("fonts/") and p.endswith(".ttf") for p in miss)
           else SFX_FIX if any(p.startswith("sfx/") for p in miss)
           else "Clone the repository again, or point S2F_ASSETS at the correct folder")
    return row("bundled assets", "required", not miss, detail, fix)


def check_disk(free_gb, minimum):
    return row("disk", "required", free_gb >= minimum, f"{free_gb:.0f} GB free (needs {minimum} GB or more)", "Free up space")


def check_config(path, cfg):
    """設定檔本身：不存在算通過；存在時每個鍵都要認得、值的型別對、dir／file 類的路徑要存在（newdir 類不查）。"""
    if path is None:
        return row("config file", "required", True, "not reading a config file (S2F_CONFIG=none)")
    if not Path(path).exists():
        return row("config file", "required", True, f"no {path}; reading environment variables only")
    bad = []
    for key, raw in cfg.items():
        if key not in s2f_config.KEYS:
            bad.append(f"{key}: unknown key" + (" (keys go in secrets.json, not here)" if "KEY" in key else ""))
            continue
        v = s2f_config.value_of(key, raw)
        if v is None:
            bad.append(f"{key}: the value must be a non-empty string or number")
        elif s2f_config.KEYS[key][0] in ("dir", "file") and not Path(v).exists():
            bad.append(f"{key}: {v} does not exist")
    return row("config file", "required", not bad, f"{path} ({len(cfg)} keys)" if not bad else "; ".join(bad),
               f"Edit {path}: " + "; ".join(bad))


def check_concat(binary):
    return row("Concat", "concat", Path(binary).exists(), str(binary), "Install Concat, or point S2F_CONCAT_BIN at its executable")


def check_chrome(app):
    return row("Google Chrome", "ve", Path(app).exists(), str(app), "Install Google Chrome (VE and TP both use the system Chrome)")


def check_ve(profile):
    """VideoExpress 的登入存在倉庫裡的 tools/ve-runner/.profile（不進版控）：新複本裡沒有，要開視窗登入一次。"""
    ok = (Path(profile) / "Default" / "Cookies").exists()
    return row("VE login", "ve", ok, str(profile) if ok else f"{profile} has never been logged in",
               "First use: run S2F_VE_HEADED=1 python3 tools/ve-runner/ve_runner.py --login and log in yourself in the window it opens")


def check_tp(profile):
    return row("TP profile folder", "tp", Path(profile).is_dir(), str(profile),
               "Run python3 tools/tp/tp_browser.py serve once and log in yourself in the window it opens")


def check_youtube(python, creds, secret_name):
    miss = []
    if not Path(python).exists():
        miss.append(f"no {python}")
    if not (Path(creds) / secret_name).exists():
        miss.append(f"no {secret_name} in {creds}")
    return row("YouTube", "youtube", not miss, str(python) if not miss else "; ".join(miss),
               "Follow tools/youtube/README.md: set up the environment, add the client credentials, run auth once")


def check_assets_local(environ):
    v = environ.get("S2F_ASSETS_LOCAL")
    if not v:
        return row("user assets layer", "note", False, "S2F_ASSETS_LOCAL is not set",
                   f"Sound effects ship with the repository. To use your own sounds (they win on the same id), CUV Bible data or a SoundFont, add \"S2F_ASSETS_LOCAL\" to {CONFIG_HINT}")
    d = Path(v).expanduser()
    return row("user assets layer", "note", d.is_dir(), str(d) if d.is_dir() else f"S2F_ASSETS_LOCAL={d} does not exist",
               f"Set S2F_ASSETS_LOCAL to the correct path (now {d})")


def check_secrets(path):
    """金鑰檔的權限（只看權限，不開檔）；沒有金鑰檔算通過。"""
    p = Path(path)
    if not p.exists():
        return row("secrets file permissions", "note", True, "no secrets file (the zero-cost path needs none)")
    mode = stat.S_IMODE(p.stat().st_mode)
    return row("secrets file permissions", "note", mode == 0o600, f"{p} mode {mode:o}", f"chmod 600 {p}")


def _run(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def _hf_dir():
    """(套件資料夾或 None, 找不到的原因)：用程式實際的找法 doc_common.hf_package（S2F_HF_BIN，否則倉庫的
    node_modules/hyperframes；package.json 與它的進入點都要在）。那個函式找不到時會結束行程，這裡接住。"""
    sys.path.insert(0, str(REPO / "skills/ve-director/doc/scripts"))
    import doc_common
    try:
        return doc_common.hf_package()[1], ""
    except SystemExit as e:
        return None, str(e.code).lstrip("✗ ")


def collect(environ, home):
    """這台機器的每一列。規則引用原模組的（items 的門檻與 Concat、YouTube 的預設；tp、youtube 的路徑），不抄第二份。"""
    sys.path[:0] = [str(REPO / "tools/checklist"), str(REPO / "tools/tp"), str(REPO / "tools/youtube")]
    import items
    import tp_paths
    import yt_paths
    ffmpeg = shutil.which("ffmpeg")
    try:
        path = s2f_config.config_path(environ, home)
        cfg = s2f_config.read(path)
    except s2f_config.ConfigError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)
    return [
        check_system(platform.system(), platform.machine()),
        check_packages([m for m in PACKAGES if importlib.util.find_spec(m) is None], (REPO / ".venv/bin/python").exists()),
        check_ffmpeg(ffmpeg, shutil.which("ffprobe"), (_run(ffmpeg, "-hide_banner", "-encoders") or "") if ffmpeg else ""),
        check_node(_run("node", "--version"), items.NODE_MIN),
        check_hyperframes(*_hf_dir()),
        check_gsap(REPO),
        check_render_browser(environ, home),
        check_playwright_browser(*_pw_locations()),
        check_tts(environ),
        check_asr(environ),
        check_assets(environ, REPO),
        check_disk(_free_gb(home), items.MIN_FREE_GB),
        check_config(path, cfg),
        check_concat(items.concat_bin(environ)),
        check_chrome("/Applications/Google Chrome.app"),
        check_ve(REPO / "tools/ve-runner/.profile"),
        check_tp(tp_paths.profile_dir(environ, home)),
        check_youtube(items.yt_python(environ), yt_paths.creds_dir(environ, home), yt_paths.SECRET_NAME),
        check_assets_local(environ),
        check_secrets(Path(home) / ".config/script2film/secrets.json"),
    ]


def _free_gb(home):
    """家目錄所在磁碟的剩餘空間（GB）；家目錄不存在就往上找到存在的那一層。"""
    p = Path(home)
    while not p.exists() and p != p.parent:
        p = p.parent
    return shutil.disk_usage(p).free / 1e9


def apply_skip(rows, skip):
    """--skip 指名的項目缺了改成 skipped（不算失敗，不印修法）；通過的照舊是 ✓。"""
    names = {n for k in skip for n in SKIPS[k]}
    return [{**r, "status": "skipped", "detail": f"skipped (--skip {','.join(skip)}): {r['detail']}", "fix": ""}
            if r["name"] in names and r["status"] == "fail" else r for r in rows]


def exit_code(rows, need):
    """必要組（required 加上 --need 指名的組）有 fail → 1，否則 0。"""
    must = {"required", *need}
    return 1 if any(r["status"] == "fail" and r["group"] in must for r in rows) else 0


def render(rows, need):
    must, out = {"required", *need}, []
    for r in rows:
        mark = "✓" if r["status"] == "ok" else "－" if r["status"] == "skipped" or r["group"] not in must else "✗"
        out.append(f"{mark} {r['name']}  {r['detail']}")
        if r["fix"]:
            out.append(f"   → {r['fix']}")
    n = sum(1 for r in rows if r["status"] == "fail" and r["group"] in must)
    skipped = [r["name"] for r in rows if r["status"] == "skipped"]
    out.append(f"✗ {n} to fix" if n else "✓ ready to go" + (f" (skipped: {', '.join(skipped)})" if skipped else ""))
    return "\n".join(out)


def usage(msg):
    """用法錯誤：退出碼 64（和「必要的項目有 ✗」的 1 分開，其他腳本才分得出來）。"""
    print(msg, file=sys.stderr)
    sys.exit(64)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    need = []
    if "--need" in args:
        k = args.index("--need")
        need = [g for g in (args[k + 1] if k + 1 < len(args) else "").split(",") if g]
        del args[k:k + 2]
        bad = [g for g in need if g not in GROUPS]
        if bad or not need:
            usage(f"--need takes one or more of {','.join(GROUPS)}, comma-separated: got {','.join(bad) or 'nothing'}")
    skip = []
    if "--skip" in args:
        k = args.index("--skip")
        skip = [g for g in (args[k + 1] if k + 1 < len(args) else "").split(",") if g]
        del args[k:k + 2]
        bad = [g for g in skip if g not in SKIPS]
        if bad or not skip:
            usage(f"--skip takes {','.join(SKIPS)}: got {','.join(bad) or 'nothing'}")
    as_json = "--json" in args
    if [a for a in args if a != "--json"]:
        usage("usage: doctor.py [--need concat,ve,tp,youtube] [--skip voice] [--json]")
    s2f_config.load()   # 檢查的是程式實際會讀到的值：設定檔先填進環境
    rows = apply_skip(collect(os.environ, Path.home()), skip)
    print(json.dumps(rows, ensure_ascii=False, indent=1) if as_json else render(rows, need))
    sys.exit(exit_code(rows, need))


if __name__ == "__main__":
    main()
