---
title: Hermes Desktop 讓 Windows 直接就能安裝使用 Hermes Agent！初學者也能自己搞定
tags: [AI, Agent, Hermes-Agent, Hermes-Desktop, Windows, GUI, 系統安裝]
sources: [raw/obsidian/Hermes Desktop 讓 Windows 直接就能安裝使用 Hermes Agent！初學者也能自己搞定.md]
status: verified
updated: 2026-05-17
---

# Hermes Desktop 讓 Windows 直接就能安裝使用 Hermes Agent！初學者也能自己搞定

## 核心觀點
**Hermes Desktop** (開發者 Fathah 打造的 v0.4.3，於 2026 年 5 月中旬推出) 是開源 AI 代理生態系中的關鍵補完拼圖。它將功能強大但「CLI-only」的 **Hermes Agent** 封裝成直覺、跨平台的 Electron 桌面應用程式（GUI），徹底消除了初學者面對命令列與手動修改配置的心理障礙，使 AI 代理的安裝、對話、排程與閘道設定實現全圖形化管理。

## 核心功能亮點

| 類別 | 功能細節 | 備註 / 說明 |
| :--- | :--- | :--- |
| **一鍵安裝** | 自動檢查 Git、uv、Python 3.11+ 依賴，並自動執行官方安裝腳本。 | 無痛解決 CLI 版最容易遇到的環境問題。 |
| **強大 GUI 交互** | SSE 串流對話 UI、22 個斜線指令（如 `/fast`、`/web` 等）、Markdown 與代碼高亮。 | 幾乎將 CLI 的所有指令搬進 GUI 介面。 |
| **整合工具集** | 網頁搜尋、瀏覽器控制、終端機執行、檔案操作、委派任務等 14 組工具。 | 支援極強的地端執行與瀏覽操作。 |
| **訊息閘道** | 內建 Telegram、Discord、Slack、飛書、微信、Webhooks 等 16 種通訊平台網關。 | 達成遠端發話與通知的橋樑。 |
| **排程任務** | 圖形化 Cron Job 任務建立器，支援自訂時間與 15 種交付目標。 | 用於自動化定期任務，極為便利。 |
| **模型與供應商** | 支援 OpenRouter、Anthropic、OpenAI、Gemini、Ollama 及多種地端 API 伺服器。 | 模型管理較 CLI 模式更加直覺。 |

## 運作模式與環境設定
1. **本地模式 (Local Mode)**：
   * 在本機端（127.0.0.1:8642）直接運行 Hermes 後端。
   * 自動安裝並託管地端執行環境（需保持後台 CMD 視窗開啟，關閉會中斷工作流）。
2. **遠端模式 (Remote Mode)**：
   * 適合已經在 Mac / Linux / 伺服器上部署 CLI 伺服器的使用者。
   * 輸入伺服器 URL 與 API Key，將 Hermes Desktop 當作一個「純前端 UI 介面」來遠端操縱背景運行的代理。

## 系統限制與侷限性
> [!WARNING]
> * **電腦關機即失效**：Hermes Desktop 與 Windows 一起運行，電腦關機後代理即失去作用。若已有 Mac 或 Linux 伺服器 24/7 運行，則無需替換。
> * **打包限制**：目前 v0.4.3 在 Windows 下無代碼簽章（SmartScreen 會警報），Mac 版本未公證（需手動繞過 Gatekeeper）。

## 生態展望：NVIDIA RTX AI PC
NVIDIA 在 2026 年 5 月宣布 **Hermes Agent** 將登陸 **RTX AI PC 平台**。未來 Hermes Desktop 前端介面若與 NVIDIA RTX 本地 AI 硬體加速深度整合，將為開源 AI 代理的地端日常自動化提供極為廣闊的想像空間。

---

## 雙向連結與延伸閱讀
*   **用 Agent 養 Agent 運維哲學**：[[用Agent養Agent|用 Agent 養 Agent：開關啟動與遠端修復]] / [用 Agent 養 Agent](file:///i:/Mark/my-kb/cards/用Agent養Agent.md) ——此卡片所探討的「避免手手改設定、防啟動崩潰」的運維哲學，正是 Hermes Desktop 設計來解決的痛點。
*   **Claude Code 本地 Skills 自動化**：[[CLAUDE CODE 4小時完整教學：學會Skills  AI 自動工作  搜集資料 (2026)_fYuohy6rQ9c|Claude Code 4 小時完整教學]] / [Claude Code](file:///i:/Mark/my-kb/wiki/youtube-notes/CLAUDE%20CODE%204%E5%B0%8F%E6%99%82%E5%AE%8C%E6%95%B4%E6%95%99%E5%AD%B8%EF%BC%9A%E5%AD%B8%E6%9C%83Skills%20%20AI%20%E8%87%AA%E5%8B%95%E5%B7%A5%E4%BD%9C%20%20%E6%90%9C%E9%9B%86%E8%B3%87%E6%96%99%20%282026%29_fYuohy6rQ9c.md) ——對比了 CLI-based Agent 與 GUI-based Agent 在工作流部署中的差異。
*   **全域知識庫母筆記方法論**：[[LLM-Wiki-筆記術|LLM Wiki 個人知識庫筆記術]] / [LLM Wiki 個人知識庫筆記術](file:///i:/Mark/my-kb/wiki/AI%E5%B7%A5%E5%85%B7/LLM-Wiki-%E7%AD%86%E8%A8%98%E8%A1%93.md) ——本卡片已作為開源 Agent 生態與 UI 實踐案例，回填收錄至該 Opinions 永久筆記中。
