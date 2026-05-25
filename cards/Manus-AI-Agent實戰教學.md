---
title: Manus 實戰教學：從研究、簡報到個人網站
tags: [AI, Agent, Manus, 簡報生成, 網站建立, Skill-Creator, 實戰教學]
sources: [raw/obsidian/【Manus 實戰教學】從研究、簡報到個人網站，帶你掌握普通人也能上手的 AI Agent.md]
status: verified
updated: 2026-05-19
---

# Manus 實戰教學：從研究、簡報到個人網站

## 核心觀點
傳統 Chatbot（如 ChatGPT、Claude）屬於**「對話型 AI」**，討論出結果後仍需人類動手執行；而 **Manus** 則是**「任務型 AI (AI Agent)」**，它能夠啟動虛擬機、操作瀏覽器、搜尋資料、使用 API，全自動完成高階且複雜的任務（如生成簡報、建立前端網頁、部署至 GitHub）。

---

## 核心功能與模式對比

| 模式/功能 | 運作機制 | 積分消耗與特點 |
| :--- | :--- | :--- |
| **Chat 模式** | 傳統對話與腦力激盪，不啟動虛擬機或網頁爬取。 | **0 積分**。適合初始需求釐清、提示詞優化、大綱規劃。 |
| **Agent 模式** | 啟動虛擬機與瀏覽器，自主進行深度網路研究與工具操作。 | 消耗較多積分。適合資料整合研究、複雜簡報與網站生成。 |
| **Skill（技能）** | 透過 `/skill-creator` 將多輪對話與工作流打包成重複使用的 SOP。 | 教會 AI 一次，日後提供新主題即可一鍵自動化執行。 |

---

## 核心實戰工作流 (SOP)

### 1. 簡報生成工作流：如何讓 AI 把簡報「做好」而非僅「做完」
> [!IMPORTANT]
> **不要一開始就叫 AI 做簡報！** 直接生成除了掌控度低外，方向錯誤會耗費大量時間與積分。

*   **STEP 1：優化提示詞**：先在 Chat 模式提供模糊需求，使用指令 `「請幫我把需求優化成更完整、更適合交給 AI 研究的 Prompt，用 Markdown 顯示」` 讓 AI 補充背景、階層與細節。
*   **STEP 2：反向檢查缺口**：讓 AI 從市場顧問角度反問自己，需要補充哪些背景資訊（如受眾、特定販售項目），補齊商業決策所需深度。
*   **STEP 3：設計簡報大綱**：在大綱階段確認結構、頁數、圖表類型與內容方向無誤後再行生成。
*   **STEP 4：生成簡報**：
    *   **專業模式 (HTML)**：文字與圖表高度可編輯，風格偏向傳統簡報，適合需要時常微調數據、涵蓋大量圖表的場景。
    *   **視覺化模式 (Nano Banana / GPT)**：圖片視覺張力極高，但修改需重新生成圖片較花時間，適合傳達故事與概念。
*   **STEP 5：生成逐字稿與下載**：利用 Manus 產出有起承轉合的演講逐字稿，並支援下載為 PPT、PDF 或匯入 Google Slides 編輯。

### 2. 個人品牌網站建立與 GitHub 自動部署
*   **多格式解析**：上傳不同格式的素材（Word、PPT、PDF），讓 Manus 自動提取並彙整個人成就與擅長領域。
*   **前端網頁生成**：利用 Manus 連接器（Connectors）授權 GitHub 帳號，AI 會自動在 GitHub 建立 Repository，並透過 GitHub Actions 完成部署（產出 `deanlin.net/repo-name/` 網址）。
*   **對話式優化**：可直接透過對話請 AI 進行圖片 WebP 壓縮以加快網頁載入速度，或修復行動裝置/手機破版問題。

---

## 雙向連結與延伸閱讀
*   **AI Agent 桌面伴侶與安裝**：[[Hermes-Desktop-GUI安裝與功能摘要|Hermes Desktop GUI 安裝與功能摘要]] / [Hermes Desktop GUI 安裝與功能摘要](file:///i:/Mark/my-kb/cards/Hermes-Desktop-GUI安裝與功能摘要.md) ——記錄了 Windows 一鍵安裝 Hermes Agent 的操作，比較了地端運維與 Manus 雲端虛擬機操作的生態系差異。
*   **開源 Agent 工具學習**：[[OpenCode基本功 EP01：免費 AI Agent 啟手式_免費仔必看！三師爸手把手教你用開源OpenCode打造專屬AI Agent！|OpenCode 免費 AI Agent 啟手式]] / [OpenCode EP01 筆記](file:///i:/Mark/my-kb/Clippings/OpenCode%E5%9F%BA%E6%9C%AC%E5%8A%9F%20EP01%EF%BC%9A%E5%85%8D%E8%B2%BB%20AI%20Agent%20%E5%95%9F%E6%89%8B%E5%BC%8F_%E5%85%8D%E8%B2%BB%E4%BB%94%E5%BF%85%E7%9C%8B%EF%BC%81%E4%B8%89%E5%B8%AB%E7%88%B8%E6%89%8B%E6%8A%8A%E6%89%8B%E6%95%99%E4%BD%A0%E7%94%A8%E9%96%8B%E6%BA%90OpenCode%E6%89%93%E9%80%A0%E5%B0%88%E5%B1%ACAI%20Agent%EF%BC%81.md) ——深入探討本機開源 OpenCode 框架與雲端全託管 Manus Agent 在隱私、權限及自訂 Skills 上的優缺點。
*   **運維哲學與 Agent 發展**：[[用Agent養Agent|用 Agent 養 Agent]] / [用 Agent 養 Agent](file:///i:/Mark/my-kb/cards/用Agent養Agent.md) ——探討外圍強 LLM/遠端修復控制與地端/雲端 Agent 共存關係的哲學思辯。
*   **個人知識庫母筆記**：[[LLM-Wiki-筆記術|LLM Wiki 個人知識庫筆記術]] / [LLM Wiki 個人知識庫筆記術](file:///i:/Mark/my-kb/wiki/AI%E5%B7%A5%E5%85%B7/LLM-Wiki-%E7%AD%86%E8%A8%98%E8%A1%93.md) ——本卡片將作為「AI Agent 實踐案例」，回填更新至永久 Wiki 母筆記中。
