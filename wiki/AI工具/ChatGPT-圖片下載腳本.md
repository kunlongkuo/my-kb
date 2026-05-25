---
title: "ChatGPT & Gemini 圖片一鍵批次下載腳本"
category: WORKFLOW
tags: [AI工具, 自動化, ChatGPT, Gemini, Tampermonkey]
sources: [raw/obsidian/想把 ChatGPT 生的圖一次下載？我把步驟拆成七步，連小孩都會裝.md, cards/ChatGPT-圖片下載腳本.md]
status: verified
updated: 2026-05-03
---

# ChatGPT & Gemini 圖片一鍵批次下載腳本

這是一個基於 Tampermonkey 的自動化工作流，用於從 ChatGPT 與 Gemini 網頁介面中快速提取並命名 AI 生成的圖片。

## 功能特點
- **一鍵下載**：在頁面右下角顯示懸浮按鈕，偵測並下載所有圖片。
- **智能命名**：檔名格式為 `YYYYMMDD_主題名稱_001.png`，主題名稱自動抓取對話標題（上限 7 字）。
- **過濾機制**：自動過濾頭像 (Avatar)、圖標 (Icon) 等非生成圖片。
- **跨平台**：支援 `chatgpt.com` 與 `gemini.google.com`。

## 安裝步驟 (一次性設定)
1. **安裝擴充功能**：在 Chrome 安裝 [Tampermonkey](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)。
2. **開啟開發人員模式**：前往 `chrome://extensions/` 並開啟右上角的「開發人員模式」。
3. **允許指令碼**：在 Tampermonkey 的詳細資料頁面中，開啟「允許使用者指令碼」。
4. **建立指令碼**：點擊 Tampermonkey 圖示 -> 「建立新指令碼」，清空編輯器。
5. **貼上代碼**：將腳本代碼貼入編輯器並儲存 (Ctrl+S)。

## 使用方法
- 回到 ChatGPT 或 Gemini 頁面重新整理 (F5)。
- 點擊右下角出現的藍色圓鈕即可開始下載。
- **Debug 模式**：對按鈕點擊右鍵，可於瀏覽器 Console (F12) 查看目前偵測到的主題與圖片清單。

## 代碼片段 (v1.2 核心邏輯)
```javascript
// ==UserScript==
// @name AI 生成圖片一鍵批次下載（ChatGPT + Gemini）v1.2
// @match https://chatgpt.com/*
// @match https://chat.openai.com/*
// @match https://gemini.google.com/*
// ==/UserScript==
// (完整代碼請參考 [Ref 1])
```

[Ref 1]: file:///i:/Mark/my-kb/raw/obsidian/%E6%83%B3%E6%8A%8A%20ChatGPT%20%E7%94%9F%E7%9A%84%E5%9C%96%E4%B8%80%E6%AC%A1%E4%B8%8B%E8%BC%89%EF%BC%9F%E6%88%91%E6%8A%8A%E6%AD%A5%E9%A9%9F%E6%8B%86%E6%88%90%E4%B8%83%E6%AD%A5%EF%BC%8C%E9%80%A3%E5%B0%8F%E5%AD%A9%E9%83%BD%E6%9C%83%E8%A3%9D.md
