---
title: Manus 實戰教學 — 從研究、簡報到個人網站
category: WORKFLOW
tags: [AI, Agent, Manus, 簡報生成, 網站建立, 實戰教學]
sources: [cards/Manus-AI-Agent實戰教學.md]
status: verified
updated: 2026-07-14
---

# Manus 實戰教學 — 從研究、簡報到個人網站

**Manus** 是「任務型 AI Agent」，可自動啟動虛擬機、操作瀏覽器、搜尋資料並使用 API，完成高階複雜任務（簡報生成、前端網頁、GitHub 部署）。相較於傳統「對話型 AI」（ChatGPT、Claude）仍需人類動手執行，Manus 可全自動端對端完成。

## 模式對比

| 模式 | 運作機制 | 積分消耗 |
| :--- | :--- | :--- |
| **Chat 模式** | 傳統對話，不啟動虛擬機 | 0 積分 |
| **Agent 模式** | 啟動虛擬機與瀏覽器，深度網路研究 | 較多積分 |
| **Skill（技能）** | 透過 `/skill-creator` 打包重複 SOP | 教一次，日後一鍵執行 |

## 簡報生成 SOP（5 步驟）

> [!IMPORTANT]
> **不要一開始就叫 AI 做簡報！** 先在 Chat 模式優化需求，確認方向後再生成。

1. **優化提示詞**：Chat 模式下請 AI「優化需求成適合 AI 研究的 Prompt」
2. **反向補缺口**：讓 AI 從顧問角度補充背景（受眾、販售項目等）
3. **設計大綱**：確認頁數、圖表類型與結構後再生成
4. **選擇格式**：
   - **HTML 模式**：可編輯文字與圖表，適合數據密集
   - **視覺化模式**（Nano Banana）：視覺張力高，適合傳遞概念
5. **生成逐字稿**：下載為 PPT/PDF 或匯入 Google Slides

## 個人網站建立與 GitHub 部署

- 上傳 Word/PPT/PDF 素材，Manus 自動提取個人成就
- 透過 GitHub Connectors 授權，AI 自動建立 Repo 並使用 GitHub Actions 部署
- 可對話式優化（WebP 壓縮、手機版修復等）

## 相關筆記

- [用Agent養Agent](file:///i:/Mark/my-kb/wiki/AI工具/用Agent養Agent.md)
- [OpenCode AI Agent 地端部署](file:///i:/Mark/my-kb/wiki/AI工具/OpenCode-AI-Agent地端部署.md)
- [Image Extraction 抓圖神器](file:///i:/Mark/my-kb/wiki/AI工具/Image-Extraction-抓圖神器.md)
