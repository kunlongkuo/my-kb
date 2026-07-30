---
name: shutdown
description: 收工 — 安全掃描 + handoff.md + README + PROGRESS + Obsidian + Git commit/push。說「收工」「下班了」「結束」時觸發。
---

# 🔴 收工

執行以下步驟，完成後回報 checklist：

## 步驟一：敏感檔案安全掃描

掃描是否有 API Key 或密碼外洩風險（防止提交至 Git）：
- 搜尋 `.env*`、`config.json`、`secrets.*` 等檔案中是否含明文金鑰
- 確認 `.gitignore` 已排除敏感檔案
- 若發現風險，**先警告使用者，暫停後續 Git 操作**

## 步驟二：彙整今日進度，更新 handoff.md

全新寫入（覆蓋）根目錄的 `handoff.md`，格式如下：

```markdown
# Handoff

## 目前做到哪
[本次完成的具體進度]

## 目前狀態
- 是否可運行：[是/否]
- 做一半的功能：[列出]
- 卡關項目：[列出或「無」]

## 下一步（優先順序）
1. [最優先的下一步]
2. [第二優先]
3. [第三優先]

## 最後更新
- 日期時間：[YYYY-MM-DD HH:MM]
- 更新者：Antigravity @ [電腦名稱]
- Git push 狀態：[已推送/未推送]
```

## 步驟三：更新 README.md

確保 README.md 涵蓋：
- 專案用途與功能描述
- 目前功能列表
- 啟動方式
- 部署方式（如有）
- 環境變數說明
- 已知問題
- 下一步計畫

## 步驟四：更新 docs/PROGRESS.md

以日期追加記錄（格式）：

```markdown
## YYYY-MM-DD

### 完成項目
- [今天完成了什麼]

### 重要改動檔案
- [改了哪些重要檔案]

### 決策紀錄
- [做了哪些技術決策]

### 卡關 / 待解
- [目前卡在哪裡]

### 下次接手先看
- [下次最重要的事]
```

## 步驟五：更新 Obsidian 每日筆記

更新 `C:\Users\Mark\Documents\Obsidian Vault\每日筆記\YYYY-MM-DD.md`：
- 在「已完成工作」區塊追加今日完成事項
- 在「待辦事項」區塊更新未完成項目

## 步驟六：Git 提交與推送

```bash
git add -A
git commit -m "[類型]: [簡短描述]

[詳細說明本次改動]
[handoff 摘要：做到哪、下一步]"
git push
```

Commit message 規則：
- **禁止**使用無意義的 "update"、"fix" 等模糊訊息
- 必須說明本次改動的核心內容

## 收工 Checklist 回報格式

```
## 🔴 收工完成

- [x] 安全掃描通過
- [x] handoff.md 已更新
- [x] README.md 已更新
- [x] docs/PROGRESS.md 已更新
- [x] Obsidian 每日筆記已更新
- [x] Git commit & push 完成

**Commit**：[commit hash 前 7 碼] - [commit message]
```
