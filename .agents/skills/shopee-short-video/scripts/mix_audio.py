#!/usr/bin/env python3
"""
蝦皮短影音自動音訊混音工具 (Shopee Short Video Audio Mixer)
將口播語音 (Voiceover) 與背景音樂 (BGM) 自動混音，
支援側鏈閃避 (Sidechain Ducking) 或固定音量衰減，並進行 EBU R128 (-14 LUFS) 響度正規化。
"""

import argparse
import subprocess
import sys
import os

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False

def mix_audio(voice_path, bgm_path, output_path, bgm_volume=0.12, ducking=False):
    if not os.path.exists(voice_path):
        print(f"錯誤：找不到口播語音檔案: {voice_path}", file=sys.stderr)
        return False
    if not os.path.exists(bgm_path):
        print(f"錯誤：找不到背景音樂檔案: {bgm_path}", file=sys.stderr)
        return False

    if not check_ffmpeg():
        print("錯誤：系統中未找到 ffmpeg，請確認已安裝並加入 PATH 環境變數。", file=sys.stderr)
        return False

    print(f"開始混音: 口播={voice_path}, BGM={bgm_path}, 輸出={output_path}")

    if ducking:
        # 動態側鏈閃避：人聲說話時自動壓低 BGM，停頓時微幅浮現
        filter_complex = (
            f"[1:a]volume=0.35[bgm_base];"
            f"[bgm_base][0:a]sidechaincompress=threshold=0.08:ratio=6:attack=50:release=300[ducked_bgm];"
            f"[0:a][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
            f"[mixed]loudnorm=I=-14:TP=-1.5:LRA=7[aout]"
        )
    else:
        # 固定音量衰減 (預設 0.12 約 -18dB)
        filter_complex = (
            f"[1:a]volume={bgm_volume},afade=t=in:ss=0:d=0.5[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
            f"[mixed]loudnorm=I=-14:TP=-1.5:LRA=7[aout]"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-i", bgm_path,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print(f"混音成功！輸出已儲存至: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 混音失敗: {e.stderr}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="蝦皮短影音自動混音工具")
    parser.add_argument("--voice", required=True, help="口播人聲音檔路徑 (例如 voice.mp3)")
    parser.add_argument("--bgm", required=True, help="背景音樂音檔路徑 (例如 bgm.mp3)")
    parser.add_argument("--output", default="mixed_audio.mp3", help="輸出混音音檔路徑 (預設: mixed_audio.mp3)")
    parser.add_argument("--bgm-volume", type=float, default=0.12, help="BGM 基礎音量比例 (預設 0.12，約 -18dB)")
    parser.add_argument("--ducking", action="store_true", help="啟用側鏈自動閃避 (Sidechain Ducking)")

    args = parser.parse_args()
    success = mix_audio(args.voice, args.bgm, args.output, args.bgm_volume, args.ducking)
    sys.exit(0 if success else 1)
