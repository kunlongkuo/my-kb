import os

os.environ["S2F_CONFIG"] = "none"   # 測試不讀這台機器的設定檔（tools/config/s2f_config.py）
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
