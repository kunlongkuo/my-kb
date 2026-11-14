#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Vlog 成片建造與預覽引擎 (vlog_builder.py)
功能：
1. 依據分鏡與字幕設定檔 (scenes.json)，對每段素材執行 9:16 (1080x1920) 滿版中心裁切。
2. 疊加上高質感細字字幕（字高約 72px、行距 1.4 倍、60% 黑色陰影、避開 Reels 遮蔽區）。
3. 產生每個場景預覽圖、拼合 Contact Sheet 總覽圖，並輸出 400px 手機尺寸自檢圖。
4. 調用 FFmpeg 組合成 30fps 直式影片，支援背景音樂混合與淡入淡出，輸出「我的Vlog.mp4」。
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

def get_font(font_path=None, size=72):
    """尋找可用繁體中文字體"""
    candidates = []
    if font_path and Path(font_path).exists():
        candidates.append(font_path)
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fdir = Path(windir) / "Fonts"
        candidates.extend([
            str(fdir / "msjhl.ttc"), # 微軟正黑體 Light
            str(fdir / "msjh.ttc"),  # 微軟正黑體 Regular
            str(fdir / "kaiu.ttf"),
            str(fdir / "mingliu.ttc")
        ])
    elif sys.platform == "darwin":
        candidates.extend([
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf"
        ])
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

def crop_center_to_916(img: Image.Image) -> Image.Image:
    """中心滿版裁切至 9:16 (1080x1920)"""
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT # 9 / 16 = 0.5625
    w, h = img.size
    img_ratio = w / h

    if img_ratio > target_ratio:
        # 圖片較寬，裁切左右兩側
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        top = 0
        right = left + new_w
        bottom = h
    else:
        # 圖片較長，裁切上下兩側
        new_h = int(w / target_ratio)
        left = 0
        top = (h - new_h) // 2
        right = w
        bottom = top + new_h

    cropped = img.crop((left, top, right, bottom))
    return cropped.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

def draw_subtitle_on_image(img: Image.Image, text: str, font, font_color=(255, 255, 255), y_ratio=0.75):
    """
    在畫面上繪製細字排版字幕
    - 黑色陰影約 60% 不透明、稍微模糊
    - 避開 Reels 安全區 (y_ratio 預設 0.75，距底部約 480px)
    """
    if not text.strip():
        return img

    canvas = img.convert("RGBA")
    w, h = canvas.size

    # 計算文字寬高
    draw_dummy = ImageDraw.Draw(canvas)
    lines = text.split("\n")
    line_height = int(font.size * 1.4)
    total_text_h = len(lines) * line_height

    # 基準 Y 軸 (受 Reels 安全限制，避免過於靠底)
    start_y = int(h * y_ratio) - (total_text_h // 2)

    # 製作陰影層 (60% 不透明黑色，微模糊)
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_color = (0, 0, 0, 153) # 60% alpha = 255 * 0.6 = 153

    for i, line in enumerate(lines):
        bbox = draw_dummy.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = start_y + i * line_height
        # 繪製陰影 (微偏移)
        shadow_draw.text((x + 3, y + 3), line, font=font, fill=shadow_color)

    # 陰影高斯模糊
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=2))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    # 繪製本體文字 (細字、不描邊)
    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    fill_rgba = (*font_color[:3], 255)

    for i, line in enumerate(lines):
        bbox = draw_dummy.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = start_y + i * line_height
        text_draw.text((x, y), line, font=font, fill=fill_rgba)

    canvas = Image.alpha_composite(canvas, text_layer)
    return canvas.convert("RGB")

def build_previews(scenes, output_dir: Path, font_path=None):
    """產生每個場景的預覽圖，並組裝 Contact Sheet 與 400px 手機自檢圖"""
    preview_dir = output_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    font = get_font(font_path, size=72)

    rendered_images = []

    print("🖼️ 正在產生各場景帶字預覽圖...")
    for idx, scene in enumerate(scenes):
        media_path = Path(scene["path"])
        caption = scene.get("caption", "")
        
        # 若素材為影片，截取第 1 秒作為底圖
        if media_path.suffix.lower() in [".mp4", ".mov"]:
            frame_path = preview_dir / f"frame_{idx:02d}.jpg"
            ffmpeg = shutil.which("ffmpeg")
            cmd = [ffmpeg, "-y", "-ss", "00:00:01", "-i", str(media_path), "-vframes", "1", "-q:v", "2", str(frame_path)]
            subprocess.run(cmd, capture_output=True)
            if frame_path.exists():
                src_img = Image.open(frame_path)
            else:
                src_img = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), (40, 40, 40))
        else:
            src_img = Image.open(media_path)

        cropped = crop_center_to_916(src_img)
        subbed = draw_subtitle_on_image(cropped, caption, font)
        
        out_single = preview_dir / f"scene_{idx+1:02d}.jpg"
        subbed.save(out_single, "JPEG", quality=90)
        rendered_images.append(subbed)
        print(f"  - 場景 {idx+1}: {caption} -> {out_single.name}")

    # 拼合 Contact Sheet (橫向或宮格排列)
    if rendered_images:
        cols = min(4, len(rendered_images))
        rows = (len(rendered_images) + cols - 1) // cols
        thumb_w = 270
        thumb_h = 480
        contact_sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (20, 20, 20))
        for i, img in enumerate(rendered_images):
            c = i % cols
            r = i // cols
            thumb = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            contact_sheet.paste(thumb, (c * thumb_w, r * thumb_h))
        
        contact_path = preview_dir / "contact_sheet.jpg"
        contact_sheet.save(contact_path, "JPEG", quality=92)
        print(f"✅ Contact Sheet 預覽總覽圖已生成: {contact_path}")

        # 手機寬度 400px 自檢圖 (檢驗第 1 鏡)
        mobile_check = rendered_images[0].resize((400, int(400 * 16 / 9)), Image.Resampling.LANCZOS)
        mobile_path = preview_dir / "mobile_check_400px.jpg"
        mobile_check.save(mobile_path, "JPEG", quality=85)
        print(f"📱 400px 手機尺寸字體清晰度自檢圖: {mobile_path}")

    return preview_dir

def render_vlog(scenes, output_dir: Path, bgm_path=None, font_path=None):
    """調用 FFmpeg 將場景與字幕組合成我的Vlog.mp4"""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("❌ 找不到 FFmpeg，無法渲染影片。")
        return None

    temp_clips_dir = output_dir / "_temp_clips"
    temp_clips_dir.mkdir(parents=True, exist_ok=True)
    font = get_font(font_path, size=72)

    clip_paths = []
    print("🎬 正在逐段渲染 9:16 片段與字幕...")

    for idx, scene in enumerate(scenes):
        media_path = Path(scene["path"])
        caption = scene.get("caption", "")
        duration = float(scene.get("duration", 3.0))
        clip_out = temp_clips_dir / f"clip_{idx:02d}.mp4"

        # 若為圖片，先加上字幕並轉為持續時間的 mp4
        if media_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            src_img = Image.open(media_path)
            cropped = crop_center_to_916(src_img)
            subbed = draw_subtitle_on_image(cropped, caption, font)
            subbed_img_path = temp_clips_dir / f"subbed_{idx:02d}.png"
            subbed.save(subbed_img_path, "PNG")

            cmd = [
                ffmpeg, "-y", "-loop", "1", "-i", str(subbed_img_path),
                "-t", str(duration),
                "-r", "30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_out)
            ]
            subprocess.run(cmd, capture_output=True)
            clip_paths.append(clip_out)
        else:
            # 影片片段：裁切 1080x1920，擷取所需時長
            # 先將字幕輸出為透明 PNG
            sub_png = temp_clips_dir / f"text_overlay_{idx:02d}.png"
            empty_img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
            subbed_trans = draw_subtitle_on_image(empty_img, caption, font)
            subbed_trans.save(sub_png, "PNG")

            vf = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"movie='{sub_png.as_posix()}'[txt];[in][txt]overlay=0:0[out]"
            )
            cmd = [
                ffmpeg, "-y", "-ss", "00:00:00", "-i", str(media_path),
                "-t", str(duration),
                "-vf", vf,
                "-r", "30",
                "-an",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_out)
            ]
            subprocess.run(cmd, capture_output=True)
            clip_paths.append(clip_out)

    # 建立 concat 清單
    concat_list = temp_clips_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    final_out = output_dir / "我的Vlog.mp4"

    # 若有背景音樂
    if bgm_path and Path(bgm_path).exists():
        total_duration = sum(float(s.get("duration", 3.0)) for s in scenes)
        fade_out_start = max(0, total_duration - 2)
        print(f"🎵 正在混音背景音樂 (淡出點 {fade_out_start:.1f}s)...")
        cmd_concat = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(bgm_path),
            "-filter_complex", f"[1:a]volume=0.35,afade=t=out:st={fade_out_start}:d=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-crf", "19", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_out)
        ]
    else:
        cmd_concat = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c:v", "libx264", "-crf", "19", "-preset", "fast",
            str(final_out)
        ]

    res = subprocess.run(cmd_concat, capture_output=True)
    if res.returncode == 0:
        print(f"🎉 成片剪輯完成: {final_out}")
        return final_out
    else:
        print(f"❌ 剪輯合成失敗: {res.stderr.decode('utf-8', errors='ignore')}")
        return None

def main():
    parser = argparse.ArgumentParser(description="AI-Vlog 成片建造與預覽引擎")
    parser.add_argument("--scenes", required=True, help="場景分鏡 JSON 檔案路徑")
    parser.add_argument("--out", required=True, help="輸出目錄路徑")
    parser.add_argument("--preview-only", action="store_true", help="僅生成預覽圖與 Contact Sheet")
    parser.add_argument("--bgm", help="背景音樂 MP3 檔案路徑")
    parser.add_argument("--font", help="指定字型檔案 (.ttf / .ttc) 路徑")
    args = parser.parse_args()

    scenes_file = Path(args.scenes)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(scenes_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data.get("scenes", data)
    print(f"載入 {len(scenes)} 個場景...")

    build_previews(scenes, out_dir, font_path=args.font)

    if not args.preview_only:
        render_vlog(scenes, out_dir, bgm_path=args.bgm, font_path=args.font)

if __name__ == "__main__":
    main()

