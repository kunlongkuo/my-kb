---
title: Codex-Ollama 本地模型串接與無限量使用
category: WORKFLOW
tags: [AI, Agent, Codex, Ollama, 本地模型, 地端部署]
sources: [cards/Codex-Ollama-本地模型串接.md]
status: verified
updated: 2026-07-14
---

# Codex-Ollama 本地模型串接與無限量使用

透過 **Ollama v0.24.0**（2026 年 5 月）正式支援 Codex 桌面版本地模型串接。僅需單一指令即可將 Codex 的推理大腦切換為本地開源模型（Llama 3、Mistral 等），達成完全免費、無額度限制的地端 AI 開發環境。

## 串接核心指令

```bash
# 在 Ollama 與 Codex 桌面版皆已安裝的前提下執行
ollama launch
```

此指令自動啟動本地服務適配層，與 Codex 桌面版 API 端口完成自動配對，將開源模型無縫註冊為 Codex 後端。

## 雲端 vs 本地 Ollama 模式對比

| 維度 | 雲端 API（Claude / GPT） | 本地 Ollama（ollama launch）|
| :--- | :--- | :--- |
| **使用成本** | 依 Token 計費，有額度限制 | 完全免費，無任何 Token 限制 |
| **隱私安全** | 程式碼傳送至雲端供應商 | 100% 本地運行，機密不外洩 |
| **網路依賴** | 必須連線網際網路 | 可在完全離線的沙盒環境運作 |
| **推論速度** | 受限於網路延遲與雲端佇列 | 取決於本地 GPU/CPU 硬體效能 |

## 可應用情境

- **高隱私開發沙盒**：內部網路或離線環境下的程式碼重構與 Debug
- **無限制實驗**：無額度壓力地進行大量程式碼生成測試、Agent 多輪對話調試

## 相關筆記

- [OpenCode AI Agent 地端部署](file:///i:/Mark/my-kb/wiki/AI工具/OpenCode-AI-Agent地端部署.md)
- [用Agent養Agent](file:///i:/Mark/my-kb/wiki/AI工具/用Agent養Agent.md)
