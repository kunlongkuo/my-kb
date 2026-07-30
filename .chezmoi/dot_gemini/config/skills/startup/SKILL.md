---
name: startup
description: 開工 — 確認 Git 狀態、讀取 handoff.md + Obsidian 今日筆記、給出第一步建議。說「開工」「我來了」「上次做到哪」時觸發。
---

# 🟢 開工

執行以下步驟，完成後給出結構化摘要與今日第一步行動建議：

## 步驟一：確認工作環境

1. 確認當前目錄是否在 Git 倉庫（`git status`）
2. 執行 `git fetch origin`，確認本地與遠端分支同步狀況
   - 若有落後（behind commits），**提示**使用者手動執行 `git pull`，不主動執行以免覆蓋本地修改

## 步驟二：讀取 handoff.md

- 優先檢查並讀取根目錄的 `handoff.md`（包含：上次做到哪、目前狀態、下一步與注意事項）
- 比對 `handoff.md` 中的**最後更新電腦/更新者**與當前系統環境（PowerShell：`$env:COMPUTERNAME`）
  - 若更新電腦與當前電腦**不同**，顯示警告：
    > ⚠️ 上次在另一台電腦 [電腦名稱] 收工，請確認 Google Drive / Git 已完成同步後再繼續工作

## 步驟三：讀取 Obsidian 每日筆記

- 讀取 Obsidian `每日筆記/YYYY-MM-DD.md` 中的「上次做到哪」與「下一步計畫」作為輔助背景脈絡
- Obsidian Vault 路徑：`C:\Users\Mark\Documents\Obsidian Vault`

## 步驟四：輸出結構化摘要

以下格式回報：

```
## 🟢 開工摘要

**當前分支**：[branch]
**同步狀態**：[超前/落後/同步]
**上次更新電腦**：[電腦名稱]

### 上次做到哪
[handoff.md 的「目前做到哪」內容]

### 目前狀態
[handoff.md 的「目前狀態」]

### 下一步（優先）
[handoff.md 的「下一步」前 1-3 項]

### 今日第一步建議
[根據以上資訊，給出具體的第一步行動]
```

最後詢問使用者：「要從哪個任務開始？」
