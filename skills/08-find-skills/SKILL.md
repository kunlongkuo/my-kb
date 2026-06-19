---
name: antigravity-find-skills
description: 協助使用者在專案中搜尋已安裝的自訂技能（Skills）。當使用者說「搜尋技能」「有哪些技能」「尋找技能」「find-skills」時載入。
---

# 技能搜尋員（Find-Skills）

本技能旨在協助使用者快速檢索與盤點目前專案知識庫中已安裝的所有自訂技能（Custom Skills），並展示其名稱、觸發條件與功能描述，以利重複使用。

## 執行流程 (SOP)

當使用者觸發此技能時，請執行以下步驟：

### STEP 1：掃描技能目錄
1. 列出專案根目錄下 `skills/` 資料夾內的所有子資料夾。
2. 逐一檢查每個子資料夾中是否存在 `SKILL.md` 檔案。

### STEP 3：讀取與解析技能資訊
1. 對於每個找到的 `SKILL.md` 檔案，讀取其前 10 行以解析 YAML Frontmatter。
2. 提取以下核心屬性：
   - **技能名稱 (name)**
   - **觸發說明 (description)**
   - **目錄路徑**（相對路徑，如 `skills/07-skill-creator/`）

### STEP 3：格式化回報結果
將搜尋結果整理為 Markdown 表格並呈送給使用者。回報格式範例：

```markdown
## 🔍 已安裝技能列表

| 編號與路徑 | 技能名稱 (Name) | 功能與觸發說明 (Description) |
| :--- | :--- | :--- |
| `skills/01-notebooklm` | antigravity-notebooklm | 連接 NotebookLM MCP... |
| `skills/07-skill-creator` | antigravity-skill-creator | 協助設計與建立自訂技能... |
```

### STEP 4：引導下一步
提示使用者如何觸發其中特定的技能，例如：「如果您想建立新技能，可以直接對我說『建立技能』來啟動技能製造機。」
