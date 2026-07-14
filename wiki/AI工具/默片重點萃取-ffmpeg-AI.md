---
title: ffmpeg + AI 默片重點萃取工作流
category: WORKFLOW
tags: [ffmpeg, AI, 影片處理, 知識萃取, OCR]
sources: [cards/默片撈重點-ffmpeg-AI.md]
status: verified
updated: 2026-07-14
---

# ffmpeg + AI 默片重點萃取工作流

利用 `ffmpeg` 擷取影片關鍵影格，結合 AI 進行 OCR 與結構化整理，將無聲字卡快閃短影音快速轉化為可讀筆記的「5 分鐘高效工作流」。

## 三步驟標準流程

1. **下載**：以 `yt-dlp` 或其他工具下載目標影片為 `.mp4`
2. **抽影格**：估算字卡數 $N$，計算時間間隔，用 `ffmpeg` 擷取關鍵影格
3. **AI 辨識**：批次丟給 AI 模型（ChatGPT、Claude、Gemini），整理成結構化筆記

## 關鍵指令

```bash
# 定點高畫質抽圖（-ss 時間點、-frames:v 1 限制張數、-q:v 2 高品質）
ffmpeg -ss 1.0 -i 影片.mp4 -frames:v 1 -q:v 2 keyframe_01.jpg

# 自動偵測場景切換（畫面變化 > 30% 時抓圖）
ffmpeg -i 影片.mp4 -vf "select='gt(scene,0.3)'" -vsync vfr scene_%03d.jpg
```

## AI Prompt 範例

```
請將以下圖片中的文字逐行讀出，並依照出現順序整理成一個條列清單。
若有段落分隔，請使用二級標題區分。最後請以簡潔摘要說明此段文字的主旨。
```

## 常見問題排解

| 問題 | 解決方案 |
|------|----------|
| 影格畫質太低 | 將 `-q:v` 調整為 2~3，或微調 `-ss` 時間 |
| OCR 識別不到文字 | 加上 `-vf "eq=brightness=0.06:contrast=1.5"` 調整亮度/對比 |
| AI 回答格式錯亂 | 提示詞中明確要求 Markdown 格式 |
| 大量影格觸發速率限制 | 腳本中加入 `time.sleep(1)` 排程 |

## 教育應用情境

引導學生拍攝 1 分鐘默片採訪校園人事物，再用本方法整理並核對訊息，培養「先看清楚，再說話」的習慣（呼應柯維第五個習慣）。

## 相關筆記

- [Edits 影片編輯軟體](file:///i:/Mark/my-kb/wiki/AI工具/Edits-影片編輯軟體.md)
- [一篇文章到80秒說話卡通片](file:///i:/Mark/my-kb/wiki/AI工具/一篇文章到80秒說話卡通片.md)
