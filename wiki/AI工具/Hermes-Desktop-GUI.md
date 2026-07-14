---
title: Hermes Desktop GUI — Windows 一鍵安裝 AI Agent
category: WORKFLOW
tags: [AI, Agent, Hermes-Agent, Hermes-Desktop, Windows, GUI, 系統安裝]
sources: [cards/Hermes-Desktop-GUI安裝與功能摘要.md]
status: verified
updated: 2026-07-14
---

# Hermes Desktop GUI — Windows 一鍵安裝 AI Agent

**Hermes Desktop**（開發者 Fathah，v0.4.3，2026 年 5 月推出）將 CLI-only 的 Hermes Agent 封裝為跨平台 Electron 桌面應用程式，實現 AI 代理的全圖形化管理。

## 核心功能

| 類別 | 功能細節 |
| :--- | :--- |
| **一鍵安裝** | 自動檢查 Git、uv、Python 3.11+ 並執行官方安裝腳本 |
| **GUI 交互** | SSE 串流對話、22 個斜線指令、Markdown 與代碼高亮 |
| **整合工具集** | 網頁搜尋、瀏覽器控制、終端機執行、檔案操作等 14 組工具 |
| **訊息閘道** | Telegram、Discord、Slack、飛書、微信等 16 種通訊平台 |
| **排程任務** | 圖形化 Cron Job 建立器，支援 15 種交付目標 |
| **模型支援** | OpenRouter、Anthropic、OpenAI、Gemini、Ollama |

## 運作模式

- **本地模式**：在 127.0.0.1:8642 直接運行後端（需保持 CMD 視窗開啟）
- **遠端模式**：連接已在 Mac/Linux/伺服器部署的 CLI 後端，作為純前端 UI

> [!WARNING]
> - 電腦關機後代理即失效（無 24/7 背景運行）
> - Windows 版本無代碼簽章，首次啟動會觸發 SmartScreen 警報

## NVIDIA RTX 展望

2026 年 5 月 NVIDIA 宣布 Hermes Agent 將登陸 RTX AI PC 平台，未來將與本地 AI 硬體加速深度整合。

## 相關筆記

- [用Agent養Agent](file:///i:/Mark/my-kb/wiki/AI工具/用Agent養Agent.md) — 運維哲學：避免手動改設定導致系統崩潰
- [OpenCode AI Agent 地端部署](file:///i:/Mark/my-kb/wiki/AI工具/OpenCode-AI-Agent地端部署.md)
- [Codex-Ollama 本地模型串接](file:///i:/Mark/my-kb/wiki/AI工具/Codex-Ollama-本地模型串接.md)
