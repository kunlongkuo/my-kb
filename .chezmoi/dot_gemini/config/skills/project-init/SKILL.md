---
name: project-init
description: 初始化新專案 — 建立標準檔案結構 + Git init + GitHub repo + Obsidian 專案筆記。說「初始化專案」「開新專案」時觸發。
---

# 🔵 初始化專案

執行以下步驟，建立完整的專案標準結構：

## 步驟一：確認資訊

在開始之前，確認以下資訊（若使用者未提供，請詢問）：
- **專案名稱**（英文，用於 Git repo 和資料夾名稱）
- **專案描述**（一句話說明用途）
- **技術棧**（語言/框架）
- **是否建立 GitHub 遠端倉庫**（預設：是）

## 步驟二：建立標準檔案

### AGENTS.md（AI Agent 工作規範）

```markdown
# [專案名稱] — AI Agent 工作規範

## 專案概述
[專案描述]

## 技術棧
[語言、框架、主要套件]

## 目錄結構
[說明重要目錄的用途]

## 開發規範
- 語言：繁體中文回覆
- 不可刪除已建立的檔案（除非明確指示）
- 完成任務前確認不破壞現有功能
```

### handoff.md（交接文件範本）

```markdown
# Handoff

## 目前做到哪
專案初始化完成

## 目前狀態
- 是否可運行：初始狀態
- 做一半的功能：無
- 卡關項目：無

## 下一步（優先順序）
1. 實作核心功能
2. 撰寫測試
3. 部署設定

## 最後更新
- 日期時間：[YYYY-MM-DD HH:MM]
- 更新者：Antigravity @ [電腦名稱]
- Git push 狀態：已推送（初始 commit）
```

### README.md

```markdown
# [專案名稱]

[專案描述]

## 功能
- [ ] 待實作

## 啟動方式
```bash
# 安裝依賴
[安裝指令]

# 啟動
[啟動指令]
```

## 環境變數
| 變數名 | 說明 | 必填 |
|--------|------|------|
| `ENV_VAR` | 說明 | ✅ |

## 已知問題
無

## 下一步
- [ ] 待定
```

### docs/PROGRESS.md

```markdown
# 開發進度記錄

## [YYYY-MM-DD] — 專案初始化

### 完成項目
- 建立專案標準結構
- 初始化 Git 倉庫
- 建立 GitHub repo

### 技術決策
- [記錄重要的技術選擇]
```

### .gitignore

根據技術棧生成適當的 `.gitignore`，必須包含：
- 敏感檔案：`.env`, `.env.local`, `secrets.*`
- 編譯產物和暫存檔
- IDE 設定：`.vscode/`, `.idea/`
- OS 產物：`.DS_Store`, `Thumbs.db`

## 步驟三：Git 初始化

```bash
git init
git add -A
git commit -m "init: 專案初始化

- 建立標準目錄結構
- 新增 AGENTS.md、handoff.md、README.md
- 新增 docs/PROGRESS.md
- 設定 .gitignore"
```

## 步驟四：建立 GitHub 遠端倉庫

```bash
gh repo create [專案名稱] --private --source=. --remote=origin --push
```

- 預設建立**私有倉庫**（`--private`），若使用者指定公開則改用 `--public`

## 步驟五：建立 Obsidian 專案筆記

在 `C:\Users\Mark\Documents\Obsidian Vault\Projects\[專案名稱]\` 建立：
- `00-概述.md`：記錄專案目標、技術棧、GitHub 連結
- `01-進度.md`：追蹤開發進度

## 完成回報格式

```
## 🔵 專案初始化完成

**專案名稱**：[名稱]
**本地路徑**：[路徑]
**GitHub**：[repo URL]
**Obsidian**：已建立專案筆記

### 建立的檔案
- [x] AGENTS.md
- [x] handoff.md
- [x] README.md
- [x] docs/PROGRESS.md
- [x] .gitignore
- [x] Git 初始化完成
- [x] GitHub repo 建立完成
- [x] Obsidian 專案筆記建立

### 下一步
[根據專案類型給出具體的第一步建議]
```
