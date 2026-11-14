#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Vlog 環境檢查工具
檢查系統是否已安裝 FFmpeg、可用中文字型與必要 Python 函式庫。
"""

import sys
import shutil
import subprocess
import os
from pathlib import Path

def check_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            res = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
            first_line = res.stdout.splitlines()[0] if res.stdout else ""
            print(f"✅ FFmpeg 已就緒: {first_line} ({ffmpeg_path})")
            return True
        except Exception as e:
            print(f"⚠️ FFmpeg 執行異常: {e}")
            return False
    else:
        print("❌ 找不到 FFmpeg。請先安裝 FFmpeg (例如 winget install Gyan.FFmpeg 或 brew install ffmpeg)。")
        return False

def check_python_libs():
    libs = [
        ("PIL", "Pillow (用於影像裁切與預覽圖產生)"),
    ]
    all_ok = True
    for mod, desc in libs:
        try:
            __import__(mod)
            print(f"✅ Python 套件 [{mod}] 已就緒: {desc}")
        except ImportError:
            print(f"❌ 缺少 Python 套件 [{mod}]: {desc}。請執行: pip install Pillow")
            all_ok = False
            
    # 選用套件
    try:
        __import__("pillow_heif")
        print("✅ Python 套件 [pillow_heif] 已就緒 (支援直接讀取 iPhone HEIC 照片)")
    except ImportError:
        print("ℹ️ 未安裝 [pillow_heif] (若有大量 HEIC 原始照片建議執行: pip install pillow-heif)")

    return all_ok

def check_fonts():
    # 尋找 Windows / Mac 常見繁體中文字體
    common_fonts = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        font_dir = Path(windir) / "Fonts"
        candidates = ["msjh.ttc", "msjhl.ttc", "kaiu.ttf", "mingliu.ttc", "NotoSansTC-Regular.ttf", "NotoSansTC-Light.ttf"]
        for c in candidates:
            p = font_dir / c
            if p.exists():
                common_fonts.append(str(p))
    elif sys.platform == "darwin":
        font_dirs = [Path("/System/Library/Fonts"), Path("/Library/Fonts")]
        for fd in font_dirs:
            for p in fd.glob("*TC*"):
                common_fonts.append(str(p))
                
    if common_fonts:
        print(f"✅ 偵測到繁體中文字型: {common_fonts[0]}")
    else:
        print("ℹ️ 未在預設路徑偵測到繁中字型，可於素材資料夾中放置 .ttf 字體檔。")

def main():
    print("=" * 50)
    print("🎬 AI-Vlog 剪輯環境檢查")
    print("=" * 50)
    f_ok = check_ffmpeg()
    p_ok = check_python_libs()
    check_fonts()
    print("=" * 50)
    if f_ok and p_ok:
        print("🎉 恭喜！剪輯環境已全部就緒，隨時可以開始剪片！")
    else:
        print("⚠️ 還有部分工具尚未齊備，請依照上方提示補齊。")

if __name__ == "__main__":
    main()
