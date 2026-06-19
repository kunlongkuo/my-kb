---
name: antigravity-skill-creator
description: 協助使用者在專案中建立、修改與最佳化自訂技能（Skills）。當使用者說「建立技能」「新增技能」「製作技能」「設計技能」「skill-creator」時載入。
---

# 技能製造機（Skill-Creator）

本技能旨在引導使用者與 AI 代理（Antigravity）協同合作，快速設計、建立、修改與最佳化專案自訂技能（Custom Skills），將繁瑣的多步驟 SOP 自動打包成隨插即用的技能模組。

## 技能開發流程 (SOP)

當載入此技能時，請依照以下步驟引導使用者：

### STEP 1：需求收集與釐清
透過簡短的問答，向使用者確認以下基本資訊：
1. **技能名稱 (Skill Name)**：英文短標籤（例如 `auto-report`）與中文名稱。
2. **主要功能與用途**：該技能要解決什麼重覆性工作？期望的「完成定義 (Definition of Done)」為何？
3. **觸發詞與情境**：在什麼情境下，使用者會下達什麼指令來觸發此技能？
4. **所需依賴與工具**：是否需要連接外部 API、本機指令、MCP 伺服器或特定 Python/Bash 腳本？

### STEP 2：架構與目錄設計
自訂技能將儲存在 `skills/` 目錄下，標準結構如下：
- `skills/<number>-<skill-name>/` (例如 `skills/08-auto-report/`)
  - `SKILL.md` (必要，包含 YAML Frontmatter 與指令)
  - `scripts/` (選填，存放該技能專屬的自動化程式碼)
  - `references/` (選填，存放參考文獻、API 格式或規範檔)
  - `assets/` (選填，存放模板、圖表等靜態資源)

### STEP 3：自動生成 SKILL.md
為使用者生成並寫入 `SKILL.md`，內容必須包含：
1. **YAML Frontmatter**：
   ```yaml
   ---
   name: antigravity-<skill-name>
   description: <第三人稱描述，明確寫出在什麼語意或關鍵字下會自動載入該技能>
   ---
   ```
2. **結構化指令 (Imperative Instructions)**：
   - 使用祈使句（如「讀取...」、「執行...」、「回報...」）。
   - 將步驟模組化（STEP 1、STEP 2...）。
3. **輸出格式規範**：明確定義完成後的成果回報格式。
4. **安全守則與避坑指南**：
   - 嚴禁寫入任何個人 Token、API Key、密碼等敏感資料。
   - 保留既有檔案，非經明確許可不做破壞性覆蓋。

### STEP 4：驗證、註冊與優化
1. **本機註冊**：
   - 更新全域安裝技能清單 `skills/00-install-all/SKILL.md`，將新技能加入列表。
   - 更新 `09-AntiGravity專屬懶人包.md`，在適當章節或更新紀錄中說明。
2. **測試優化**：
   - 模擬一次該技能的執行過程，檢視引導語句與 Trigger 是否自然，確認無誤後寫入日誌 `log.md`。
