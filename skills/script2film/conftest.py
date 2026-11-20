"""Root test settings. tools/score is its own uv project (tinysoundfont, librosa): its tests run inside it with
`cd tools/score && uv run python -m pytest -q`, not from here."""
import os

os.environ["S2F_CONFIG"] = "none"   # 測試不讀這台機器的設定檔（tools/config/s2f_config.py）
collect_ignore_glob = ["tools/score/*"]
