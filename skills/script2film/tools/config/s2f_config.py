"""設定檔：~/.config/script2film/config.json（一台機器一份，和 secrets.json 同一個資料夾；金鑰不放這裡）。

寫一次路徑與偏好，之後不用每個 shell 都 export。鍵名和環境變數相同（KEYS）。優先順序：
環境變數 → 設定檔 → 各程式原本的預設值。沒有設定檔時什麼都不做。

讀設定的程式在檔案最前面呼叫 load()：把設定檔裡「環境沒設」的鍵填進 os.environ，之後的程式照舊讀環境變數。
環境裡設的是舊名（OLD_NAMES，例如 QWEN_TTS_DIR）時也算有設，不會被設定檔蓋掉。

  python3 tools/config/s2f_config.py --show     每個鍵現在的值與來源（環境／設定檔／未設）
  python3 tools/config/s2f_config.py --export   印出 export 那幾行，給 shell 用：eval "$(python3 …/s2f_config.py --export)"

S2F_CONFIG 可以指到另一個設定檔；設成 none 表示不讀設定檔（測試用）。只用標準庫：配音的 venv 與 tools/score
的 uv 專案都要匯入得到。
"""
import json
import os
import shlex
import sys
from pathlib import Path

# 種類：dir＝要已經存在的資料夾；file＝要已經存在的檔（或資料夾）；newdir＝程式自己會建的資料夾（不查存在）；value＝不是路徑
KEYS = {
    "S2F_DIR": ("dir", "where this repository is (used by the command lines in the workflow docs)"),
    "S2F_ASSETS": ("dir", "bundled assets layer (fonts/, sfx/); unset: the repository's assets/"),
    "S2F_ASSETS_LOCAL": ("dir", "user assets layer: your own sounds, CUV Bible data, SoundFont"),
    "S2F_QWEN_TTS_DIR": ("dir", "qwen3-tts folder (with a .venv inside)"),
    "S2F_QWEN_TTS_MODELS": ("dir", "Qwen3-TTS model folder; unset: <S2F_QWEN_TTS_DIR>/../_models"),
    "S2F_WHISPER_CPP_MODEL": ("file", "whisper.cpp model file for transcription and word timing (ggml-large-v3-turbo.bin)"),
    "S2F_WHISPER_CLI": ("file", "whisper-cli program; unset: whisper-cli on PATH"),
    "S2F_MLX_WHISPER_DIR": ("value", "retired 2026-11-20 (mlx-whisper): only read to say S2F_WHISPER_CPP_MODEL replaces it"),
    "S2F_HF_BIN": ("file", "HyperFrames package folder or entry point; unset: the repository's node_modules/hyperframes"),
    "S2F_CONCAT_BIN": ("file", "Concat executable; unset: the one in /Applications/Concat.app"),
    "S2F_SOUNDFONT": ("file", "SoundFont file for the score; unset: <S2F_ASSETS_LOCAL>/soundfonts/GeneralUser-GS.sf2"),
    "S2F_SCORE_WORK": ("newdir", "working folder for the score"),
    "S2F_YT_DIR": ("newdir", "YouTube credentials folder"),
    "S2F_YT_PYTHON": ("file", "interpreter that runs yt_upload.py (a venv with the Google packages)"),
    "S2F_TP_PROFILE": ("newdir", "browser profile folder for TalkingPhotos"),
    "S2F_H3_SKILL_DIR": ("dir", "h3-multimodal-colab folder of github.com/dseditor/h3-colab-skill (MiniMax H3 on Colab)"),
    "S2F_TP_IDLE_MIN": ("value", "minutes of idle before the TP browser closes itself (0 = never)"),
    "S2F_SPEECHBRAIN_CACHE": ("newdir", "cache folder for the speaker-embedding model"),
    "S2F_SCRIBE_MODEL": ("value", "ElevenLabs model for cloud word timing"),
    "S2F_EXPORT_CRF": ("value", "compression of the finished film (16–32, default 24)"),
    "S2F_VE_HEADED": ("value", "1 = VE opens a window (for logging in again)"),
    "TP_HEADLESS": ("value", "whether the TP browser runs headless"),
    "TP_ASPECT": ("value", "aspect ratio of TP videos"),
    "TP_GENDER": ("value", "gender option for the TP character"),
    "TP_ORIGINAL": ("value", "name of the original character in TP when no look is given"),
    "TP_AUDIO_DIR": ("value", "name of the audio folder in the TP media library (not a local path)"),
}
# 環境變數的舊名：程式先讀新名、再讀舊名；舊名在環境裡有值時，設定檔不填新名（否則設定檔會蓋過使用者 export 的舊名）
OLD_NAMES = {
    "S2F_QWEN_TTS_DIR": "QWEN_TTS_DIR", "S2F_QWEN_TTS_MODELS": "QWEN_TTS_MODELS", "S2F_MLX_WHISPER_DIR": "MLX_WHISPER_DIR",
    "S2F_CONCAT_BIN": "CONCAT_BIN", "S2F_VE_HEADED": "VE_HEADED", "S2F_TP_PROFILE": "TP_PROFILE",
    "S2F_DIR": "PROMPTSTUDIO_DIR",
}
PATH_KINDS = ("dir", "file", "newdir")
_LOADED = False


class ConfigError(Exception):
    pass


def config_path(environ, home):
    """設定檔的位置：S2F_CONFIG 有值就用它（none＝不讀），否則 <home>/.config/script2film/config.json。不讀時回 None。"""
    v = environ.get("S2F_CONFIG")
    if v:
        return None if v == "none" else Path(v).expanduser()
    return Path(home) / ".config/script2film/config.json"


def read(path):
    """設定檔的內容（dict）；path 是 None、檔不存在或是空檔回 {}；JSON 壞掉或最外層不是物件 → ConfigError。"""
    if path is None or not Path(path).exists():
        return {}
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else {}   # 空檔當成沒有任何鍵
    except (ValueError, OSError) as e:
        raise ConfigError(f"cannot read config file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"config file {path} must hold an object at the top level ({{\"key\": \"value\"}})")
    return data


def value_of(key, raw):
    """設定檔裡一個值 → 要填進環境的字串；型別不對（巢狀物件、陣列、布林、null）或空字串回 None。路徑類展開 ~。"""
    if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
        return None
    s = str(raw)
    if not s:
        return None
    return str(Path(s).expanduser()) if KEYS[key][0] in PATH_KINDS else s


def has_env(environ, key):
    """環境裡這個鍵（或它的舊名）有沒有值；空字串算沒有。"""
    return bool(environ.get(key) or (key in OLD_NAMES and environ.get(OLD_NAMES[key])))


def fill(environ, cfg):
    """把 cfg 裡認得的鍵（KEYS）、環境沒設的，寫進 environ；回傳寫進去的鍵名。不認得的鍵與型別不對的值跳過
    （由 tools/doctor 報告）。"""
    done = []
    for key, raw in cfg.items():
        if key not in KEYS or has_env(environ, key):
            continue
        v = value_of(key, raw)
        if v is not None:
            environ[key] = v
            done.append(key)
    return done


REPO = Path(__file__).resolve().parents[2]


def repo_python(prefix, base_prefix, main_file, repo, environ):
    """要不要改用倉庫自己的 Python 環境重跑：回 <repo>/.venv/bin/python，或 None（照現在的直譯器跑）。
    只在三件事都成立時才換：現在不在任何虛擬環境裡（prefix == base_prefix；已經在 .venv、配音的 venv、uv 的環境裡
    就不動）、被執行的是倉庫裡的程式檔（python3 -m pytest、python3 -c 這些不算）、而且 <repo>/.venv/bin/python 存在。
    S2F_NO_VENV 有值時一律不換。"""
    if environ.get("S2F_NO_VENV") or prefix != base_prefix or not main_file:
        return None
    repo = Path(repo).resolve()
    try:
        rel = Path(main_file).resolve().relative_to(repo)
    except ValueError:
        return None
    if rel.parts and rel.parts[0] in (".venv", "node_modules"):
        return None
    py = repo / ".venv/bin/python"
    return py if py.exists() else None


def use_repo_python():
    """倉庫有 .venv 而現在用的是系統的 python3 時，用 .venv 的直譯器重新執行同一條命令（參數與旗標照舊）。
    Homebrew 的 Python 不讓人直接 pip install，套件裝在 .venv 裡；有這一步，文件裡的 `python3 tools/…` 不用改。"""
    main = sys.modules.get("__main__")
    py = repo_python(sys.prefix, sys.base_prefix, getattr(main, "__file__", None), REPO, os.environ)
    if py:
        orig = getattr(sys, "orig_argv", None)   # 3.10 以上：連 -u 這類旗標一起帶過去
        os.execv(str(py), [str(py), *(orig[1:] if orig else sys.argv)])


def load():
    """讀設定檔、填進 os.environ；同一個行程只做一次。設定檔壞掉 → 印原因、exit 2（不帶著半套設定往下跑）。
    開頭先看要不要改用倉庫的 .venv 重跑（use_repo_python）。"""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    use_repo_python()
    try:
        fill(os.environ, read(config_path(os.environ, Path.home())))
    except ConfigError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args not in (["--export"], ["--show"]):
        sys.exit("usage: s2f_config.py --show | --export")
    try:
        path = config_path(os.environ, Path.home())
        cfg = read(path)
    except ConfigError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)
    if args == ["--export"]:
        for key in KEYS:
            if key in cfg and not has_env(os.environ, key):
                v = value_of(key, cfg[key])
                if v is not None:
                    print(f"export {key}={shlex.quote(v)}")
        return
    print(f"config file: {path if path else 'not read (S2F_CONFIG=none)'}" + ("" if path is None or path.exists() else " (does not exist)"))
    for key, (_, desc) in KEYS.items():
        old = OLD_NAMES.get(key)
        if os.environ.get(key):
            v, src = os.environ[key], "env"
        elif old and os.environ.get(old):
            v, src = os.environ[old], f"env (old name {old})"
        elif key in cfg and value_of(key, cfg[key]) is not None:
            v, src = value_of(key, cfg[key]), "config"
        else:
            v, src = "", "unset"
        print(f"  {key:<24}{src:<8}{v}    # {desc}")


if __name__ == "__main__":
    main()
