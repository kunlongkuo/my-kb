# FFmpeg 影片處理指令配方（FFmpeg Recipes）

本文件提供全自動 Vlog 剪輯時常用的 FFmpeg 精準參數與色彩校正指南。

---

## 1. 滿版裁切至直式 9:16（1080×1920）

無論輸入照片或影片是橫式（16:9）、直式（4:5、3:4）或正方形（1:1），皆從中心向外裁切成滿版 1080×1920，不留黑邊：

```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -c:v libx264 -preset fast -crf 20 -c:a aac -r 30 output_916.mp4
```

---

## 2. iPhone HEIC 照片轉換為 sRGB JPG

使用 ImageMagick 或 Python Pillow / pillow-heif：

```bash
# Python
python -c "from PIL import Image; from pillow_heif import register_heif_opener; register_heif_opener(); img = Image.open('input.heic'); img.convert('RGB').save('output.jpg', quality=95)"
```

---

## 3. iPhone HDR（Dolby Vision / HLG）轉 SDR BT.709（防止畫面泛白變灰）

iPhone 拍攝的 HDR 影片若未經色彩空間轉換，在標準播放器或剪輯軟體中會呈現灰白褪色。
使用 `zscale` 或 `tonemap` 濾鏡校正回 BT.709 色域：

```bash
ffmpeg -i input_hdr.mov -vf "zscale=t=linear:npl=100,tonemap=tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p" -c:v libx264 -preset medium -crf 19 output_sdr.mp4
```

簡易兼顧相容性方案（使用 `lut3d` 或 `color_matrix`）：
```bash
ffmpeg -i input_hdr.mov -vf "format=yuv420p,colorspace=all=bt709:trc=bt709:space=bt709:primaries=bt709" -c:v libx264 -crf 20 output_sdr.mp4
```

---

## 4. 細緻文字與黑色陰影燒錄（Drawtext Filter）

依規範：細字（不加粗）、字高約 72px、黑色陰影約 60% 不透明、稍微模糊、置於畫面乾淨處。

```bash
ffmpeg -i input.mp4 -vf "drawtext=fontfile='NotoSansTC-Regular.ttf':text='慢慢走、慢慢看，就是最美好的回憶':fontsize=72:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-text_w)/2:y=h*0.75" -c:a copy output_subtitled.mp4
```

---

## 5. 多素材拼接（Concat Filter）與淡入淡出（Crossfade）

使用 xfade 濾鏡製作平滑轉場（例如 0.5 秒交叉淡化）：

```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=3.5[v]" -map "[v]" -c:v libx264 -crf 20 output_faded.mp4
```

---

## 6. 背景音樂混音與淡出

將背景音樂調整音量（0.3）並在最後 2 秒淡出：

```bash
ffmpeg -i video.mp4 -i bgm.mp3 -filter_complex "[1:a]volume=0.3,afade=t=out:st=28:d=2[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -shortest 我的Vlog.mp4
```

