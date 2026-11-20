"""TP 瀏覽器設定檔與 serve 紀錄檔的位置（只用標準庫，tp_browser.py 一匯入就開瀏覽器，抽出來才測得到）。

新名 S2F_TP_PROFILE 有設（非空）就只用它，沒設才看舊名 TP_PROFILE；都沒設時用 ~/.config/script2film/tp-profile，
只有一種例外：舊版的預設資料夾已經存在、新位置還不存在，就沿用舊的（已登入的人不用重登）。
紀錄檔跟著設定檔走：<設定檔的上一層>/tp_serve.log。

閒置自動關：tp_browser.py 的每個單步指令都會摸一下 <設定檔的上一層>/tp_last_use；serve 看到它超過
S2F_TP_IDLE_MIN 分鐘（預設 10；設 0 不自動關）沒被摸過，就正常關瀏覽器結束。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
from pathlib import Path


DEFAULT_PROFILE = ".config/script2film/tp-profile"


def profile_dir(environ, home):
    for name in ("S2F_TP_PROFILE", "TP_PROFILE"):
        if environ.get(name):
            return Path(environ[name])
    new = Path(home) / DEFAULT_PROFILE
    old = Path(home) / ".cutline-profiles/tp"   # 舊版的預設位置：只在這裡當後備，已登入的人不用重登
    if old.is_dir() and not new.exists():
        return old
    return new


def serve_log(environ, home):
    return profile_dir(environ, home).parent / "tp_serve.log"


IDLE_MIN_DEFAULT = 10   # 分鐘：TP 視窗沒有任何指令連進來這麼久就自己關


def last_use_file(environ, home):
    return profile_dir(environ, home).parent / "tp_last_use"


def idle_minutes(environ):
    """S2F_TP_IDLE_MIN：幾分鐘沒有指令就關；沒設或寫錯用預設，0 表示不自動關。"""
    try:
        v = float(environ.get("S2F_TP_IDLE_MIN", ""))
    except ValueError:
        return IDLE_MIN_DEFAULT
    return v if v >= 0 else IDLE_MIN_DEFAULT


def idle_expired(now, last_use, minutes):
    """last_use（秒）之後過了 minutes 分鐘沒有？minutes 是 0 永遠回 False。"""
    return minutes > 0 and now - last_use > minutes * 60
