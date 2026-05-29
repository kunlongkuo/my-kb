---
title: Codex-Ollama 本地模型串接與無限量使用
tags: [AI, Agent, Codex, Ollama, 本地模型, 系統維護, 運維哲學]
sources: [raw/obsidian/免費無限使用 Codex 桌面版！一個指令，就能透過 Ollama 輕鬆串接本地 AI 模型.md]
status: verified
updated: 2026-05-29
---

# Codex-Ollama 本地模型串接與無限量使用

## 核心觀點
地端 AI Agent 常因雲端模型 API 呼叫額度與成本受限。透過 2026 年 5 月中旬釋出的 **Ollama v0.24.0**，正式支援 **Codex 桌面版** 本地模型串接。僅需單一指令即可將 Codex 的推理大腦切換為本地開源模型（如 Llama 3、Mistral 等），達成完全免費、無額度限制的本地 AI 開發協作環境。

## 關鍵技術與操作

### 1. 串接核心指令
在 Ollama 與 Codex 桌面版皆已安裝的前提下，在終端機執行以下指令：
```bash
ollama launch
```
此指令會自動在本地啟動 Ollama 的本地服務適配層，並與 Codex 桌面版的 API 端口完成自動偵測與配對，將本地運行的開源模型無縫註冊為 Codex 的後端推理引擎。

### 2. 優勢對比

| 維度 | 雲端 API 模式 (如 Claude / GPT) | 本地 Ollama 模式 (ollama launch) |
| :--- | :--- | :--- |
| **使用成本** | 依 Token 計費，有每日/每月額度限制。 | 完全免費，無任何 Token 限制。 |
| **隱私安全** | 程式碼與文件會傳送至雲端供應商。 | 100% 本地運行，機密程式碼不離外網。 |
| **網路依賴** | 必須連線網際網路。 | 可在完全離線的沙盒環境中工作。 |
| **推論速度** | 受限於網路延遲與雲端佇列。 | 取決於本地 GPU/CPU 硬體效能。 |

## 可應用情境
*   **高隱私開發沙盒**：在內部網路或離線環境中，使用 Codex 本地對程式碼庫進行重構與 Debug，保證代碼不外洩。
*   **無限制實驗與學習**：適合開發者無額度壓力地進行大量程式碼生成測試、Agent 多輪對話調試或 Skill 撰寫實驗。

## 雙向連結與延伸閱讀
*   **地端 AI Agent 部署**：[[OpenCode-AI-Agent地端部署|OpenCode AI Agent 地端部署]] / [OpenCode AI Agent 地端部署](file:///i:/Mark/my-kb/cards/OpenCode-AI-Agent%E5%9C%B0%E7%AB%AF%E9%83%A8%E7%BD%B2.md) ——記錄了 OpenCode 地端 AI Agent 的 Canvas 部署、ReAct 思考除錯與自訂工具的擴充架構，可與本地 Ollama 模型適配配合。
*   **運維哲學與 Agent 共存**：[[用Agent養Agent|用 Agent 養 Agent 運維哲學]] / [用 Agent 養 Agent 運維哲學](file:///i:/Mark/my-kb/cards/%E7%94%A8Agent%E9%A4%8AAgent.md) ——探討了以強 LLM 運維地端系統與多代理架構存廢的思辨，本地模型串接提供了無額度成本運維的可能。
*   **知識庫母筆記方法論**：[[LLM-Wiki-筆記術|LLM Wiki 個人知識庫筆記術]] / [LLM Wiki 個人知識庫筆記術](file:///i:/Mark/my-kb/wiki/AI%E5%B7%A5%E5%85%B7/LLM-Wiki-%E7%AD%86%E8%A8%98%E8%A1%93.md) ——本卡片已作為本地適配實踐案例，回填收錄至該 Opinions 永久筆記中。
