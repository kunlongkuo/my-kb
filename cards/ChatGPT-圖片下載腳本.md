---
title: "ChatGPT 生成圖片一鍵批次下載腳本"
category: WORKFLOW
tags: [ChatGPT, Gemini, Tampermonkey, 圖片下載, 自動化]
sources: [raw/obsidian/想把 ChatGPT 生的圖一次下載？我把步驟拆成七步，連小孩都會裝.md]
status: draft
updated: 2026-05-03
---

## 核心摘要
這篇文章介紹了一個基於 Tampermonkey 的使用者指令碼 (UserScript)，能夠在 ChatGPT 或 Gemini 的對話頁面中一鍵下載所有生成的圖片。

## 關鍵觀點
1. **解決痛點**：解決了在 ChatGPT 網頁版需要手動一張張下載圖片的繁瑣過程。
2. **自動命名**：下載的圖片會自動依照 `YYYYMMDD_對話標題_序號` 格式命名，方便整理。
3. **低門檻安裝**：教學將安裝過程拆解為 7 個簡單步驟，即使不具備程式背景也能按圖索驥完成設定。
4. **跨平台支持**：腳本同時支援 ChatGPT 與 Gemini。

## 下一步行動 / 應用情境
- 適用於需要大量生成並收集 AI 圖片的教學、簡報製作等場景。
- 可以作為「AI 輔助工作流」的一個組件，減少手動操作。

## 原始資源參考
- 腳本核心代碼見原文內容。
- 安裝步驟包含：Tampermonkey 擴充功能安裝、開發人員模式開啟、指令碼貼上與儲存。
