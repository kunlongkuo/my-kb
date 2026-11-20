"""讓配音的腳本用系統的 python3 也能跑：找不到 qwen_tts 時，改用配音環境的 Python 重新執行自己。

用法（設定檔那四句之後、任何第三方 import 之前）：
  import qwen_python; qwen_python.ensure()

找得到 qwen_tts → 什麼都不做。找不到 → 用 <S2F_QWEN_TTS_DIR>/.venv/bin/python 重新執行（os.execv，參數照舊），
並在環境裡留記號 S2F_QWEN_REEXEC=1：轉交過還找不到就停，不會一直轉交。舊名 QWEN_TTS_DIR 也認。
只用標準庫。
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import importlib.util
import os
import sys
from pathlib import Path

MARK = "S2F_QWEN_REEXEC"


def venv_python(environ):
    """<配音資料夾>/.venv/bin/python；資料夾沒設回 None。"""
    d = environ.get("S2F_QWEN_TTS_DIR") or environ.get("QWEN_TTS_DIR")
    return Path(d).expanduser() / ".venv/bin/python" if d else None


def ensure():
    if importlib.util.find_spec("qwen_tts") is not None:
        return
    py = venv_python(os.environ)
    if os.environ.get(MARK) == "1":
        sys.exit(f"✗ the voice environment's Python ({sys.executable}) has no qwen_tts either: install Qwen3-TTS there, "
                 "or run python3 tools/doctor/doctor.py to see what is missing")
    if py is None or not py.is_file():
        sys.exit("✗ this Python has no qwen_tts, and the voice environment's Python was not found"
                 f" ({py if py else 'S2F_QWEN_TTS_DIR not set'}): set S2F_QWEN_TTS_DIR to the qwen3-tts folder"
                 " (the one with .venv in it), or run python3 tools/doctor/doctor.py")
    os.environ[MARK] = "1"
    print(f"switching to the voice environment's Python: {py}", file=sys.stderr, flush=True)
    os.execv(str(py), [str(py), *sys.argv])
