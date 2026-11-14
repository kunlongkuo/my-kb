#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Vlog HEIC 與 HDR 色彩校正轉檔工具
功能：
1. 批次將 iPhone HEIC 照片轉換為 sRGB JPG。
2. 偵測 iPhone HDR (Dolby Vision / HLG / BT.2020) 影片，使用 FFmpeg 進行色域映射 (tonemap) 轉為 BT.709 SDR，防止畫面變灰。
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path

def convert_heic_to_jpg(file_path: Path, output_dir: Path):
    """將 HEIC 照片轉為 JPG"""
    out_file = output_dir / f"{file_path.stem}.jpg"
    if out_file.exists():
        print(f"⏩ 已存在，略過: {out_file.name}")
        return out_file

    # 優先嘗試使用 pillow-heif
    try:
        from PIL import Image
        import pillow_heif
        pillow_heif.register_heif_opener()
        with Image.open(file_path) as img:
            img.convert("RGB").save(out_file, "JPEG", quality=95)
        print(f"✅ HEIC 轉 JPG 成功: {file_path.name} -> {out_file.name}")
        return out_file
    except Exception:
        pass

    # 次選使用 FFmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        cmd = [ffmpeg, "-y", "-i", str(file_path), "-q:v", "2", str(out_file)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0:
            print(f"✅ FFmpeg HEIC 轉檔成功: {file_path.name} -> {out_file.name}")
            return out_file

    print(f"❌ 無法轉換 HEIC: {file_path.name} (請安裝 pillow-heif: pip install pillow-heif)")
    return None

def is_hdr_video(file_path: Path) -> bool:
    """使用 ffprobe 偵測影片是否為 HDR"""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return False
    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=color_space,color_primaries,color_transfer",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        out = res.stdout.lower()
        # 常見 HDR 標識
        if any(hdr_tag in out for hdr_tag in ["bt2020", "arib-std-b67", "smpte2084", "hlg", "pq"]):
            return True
    except Exception:
        pass
    return False

def convert_hdr_to_sdr(file_path: Path, output_dir: Path):
    """使用 FFmpeg 將 HDR 影片 tonemap 映射為 BT.709 SDR"""
    out_file = output_dir / f"{file_path.stem}_sdr.mp4"
    if out_file.exists():
        print(f"⏩ 已存在，略過: {out_file.name}")
        return out_file

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("❌ 缺少 FFmpeg，無法執行 HDR 轉換。")
        return None

    print(f"⏳ 正在將 HDR 影片轉換為 SDR BT.709: {file_path.name} ...")
    # 高相容性 tonemap 濾鏡串流
    vf = "zscale=t=linear:npl=100,tonemap=tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p"
    cmd = [
        ffmpeg, "-y", "-i", str(file_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac",
        str(out_file)
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0:
        print(f"✅ HDR 轉 SDR 成功: {file_path.name} -> {out_file.name}")
        return out_file
    else:
        # 後備方案：簡易 colorspace
        fallback_vf = "format=yuv420p,colorspace=all=bt709:trc=bt709:space=bt709:primaries=bt709"
        cmd_fb = [
            ffmpeg, "-y", "-i", str(file_path),
            "-vf", fallback_vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac",
            str(out_file)
        ]
        res_fb = subprocess.run(cmd_fb, capture_output=True)
        if res_fb.returncode == 0:
            print(f"✅ HDR 轉 SDR (Fallback) 成功: {file_path.name} -> {out_file.name}")
            return out_file
        print(f"❌ HDR 轉檔失敗: {file_path.name}")
        return None

def process_folder(input_dir: str):
    p = Path(input_dir)
    if not p.is_dir():
        print(f"❌ 找不到目錄: {input_dir}")
        return

    processed_dir = p / "_converted"
    processed_dir.mkdir(exist_ok=True)

    print(f"📂 開始掃描素材目錄: {p}")
    heic_files = list(p.glob("*.heic")) + list(p.glob("*.HEIC"))
    video_files = list(p.glob("*.mp4")) + list(p.glob("*.mov")) + list(p.glob("*.MOV"))

    print(f"找到 {len(heic_files)} 個 HEIC 照片、{len(video_files)} 個影片。")

    for hf in heic_files:
        convert_heic_to_jpg(hf, processed_dir)

    for vf in video_files:
        if is_hdr_video(vf):
            print(f"🔍 偵測到 HDR 影片: {vf.name}")
            convert_hdr_to_sdr(vf, processed_dir)

    print("✨ 素材轉檔校正處理完畢！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Vlog HEIC 與 HDR 色彩校正轉檔工具")
    parser.add_argument("folder", help="素材資料夾路徑")
    args = parser.parse_args()
    process_folder(args.folder)
