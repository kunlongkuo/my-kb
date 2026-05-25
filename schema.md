# Knowledge Base Schema

這份文件定義了本知識庫的操作規範與結構。為確保知識管理的延續性與品質，所有處理本知識庫的 AI 代理（包括 LLM 自身）在進行寫入與更新時，皆須嚴格遵守以下流程。

## 目錄與結構
- `raw/`: 存放不可變更 (immutable) 的原始資料。所有來源文件都必須放在這裡。
- `raw/assets/`: 存放所有參考的圖片、圖表與附加檔案。
- `cards/`: 暫時筆記 (Literature/Fleeting Notes)。存放從原始資料萃取出的摘要、個人觀點與下一步行動。一篇文獻對應一張卡片。
- `wiki/`: 永久筆記 (Permanent Notes/Opinions)。整合性的 Markdown 筆記。按主題分類，例如 `wiki/交通法規/`、`wiki/勞工法規/`。**核心原則為「更新既有母筆記為主」，減少發散。**
- `index.md`: 全域索引，這份清單指向 `wiki/` 目錄下的所有節點。
- `log.md`: 操作日誌，每次操作（新增資料、回答複雜問題等）都必須記錄。

## 操作指南 (Operations)

### 1. Ingest (收錄新資料)
當收到新的原始資料並被指示收錄時（通常放入 `raw/` 內）：
1. 閱讀與解析該新資料。
2. 建立 `cards/` 暫時筆記：針對該文獻萃取核心觀點、摘要與可應用情境，並附上原文連結。
3. 檢查並更新 `wiki/` 中的永久筆記：
   - 優先尋找既有相關的實體 (Entity)、概念 (Concept) 或流程筆記，並將新的知識點「回填 / 更新」進去。
   - 若內容與舊資料矛盾，請標註矛盾之處。
   - **重要**：若需建立全新的 `wiki/` 頁面，請先取得使用者同意，避免資料庫發散混亂。
4. 在 `index.md` (與知識架構圖，如有) 中同步註冊有新增或修改的頁面。
5. 在 `log.md` 中附加一筆日誌。

### 2. Query (查詢與問答)
當被詢問問題時：
1. 先尋找並閱讀 `index.md`，鎖定可能相關的 `wiki/` 頁面。
2. 若有必要，讀取 `wiki/` 下的特定頁面。
3. 綜合答案並提供引用連結。
4. (Optional) 如果這是一次具備「洞見或有價值的整理」，請將這個回答或討論結果建立為 `wiki/` 的新頁面。

### 3. Lint (健康檢查)
當被要求進行 Lint 時：
- 檢查孤立頁面 (Orphan pages)，無連入連結的頁面。
- 尋找需要建立新頁面的標題與概念。
- 確認是否有矛盾但未被標記的知識。
- 推薦後續可以探索的研究問題或搜尋。

## 紀錄慣例 (Log Conventions)
在 `log.md` 紀錄時，請遵循以下格式，以利未來分析：
```
## [YYYY-MM-DD] action | Title/Subject
- Description of what was added or changed...
```
(例如: `## [2026-04-10] ingest | Article Title`)

## 頁面結構 (Page Structure)
## 頁面寫入慣例
1. **Frontmatter**: 所有頁面必須包含定義好的 YAML 區塊。
所有 `wiki/` 下的 Markdown 頁面，都必須包含以下結構：

title: 頁面標題
category: PROJECT | WORKFLOW | METHOD | CONCEPT
tags: [標籤1, 標籤2]
sources: [raw/source_v1.pdf, cards/card_name.md]
status: verified | draft | conflicting
updated: YYYY-MM-DD

2. **Atomic Notes**: 鼓勵「原子化」筆記，一個頁面僅討論一個核心概念，利用連結互相勾連。
3. **Citations**: 所有的結論必須在文末列出 `[Ref]` 並連結至 `raw/` 內的檔案。

