"""YouTube 憑證資料夾的位置（只用標準庫；yt_upload.py 一匯入就要 Google 的套件，抽出來才測得到）。

S2F_YT_DIR 有設（非空）就用它，沒設用 ~/.config/script2film/youtube。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
from pathlib import Path

SECRET_NAME = "youtube_client_secret.json"


def creds_dir(environ, home):
    if environ.get("S2F_YT_DIR"):
        return Path(environ["S2F_YT_DIR"])
    return Path(home) / ".config/script2film/youtube"
