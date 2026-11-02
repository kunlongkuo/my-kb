---
name: skill-rag
description: Use for RAG, multi-file knowledge-base search, image/video source indexing, chunking, retrieval, clickable media links, citations, or the skill_rag.py workflow.
license: MIT
compatibility: OpenCode skills; Python 3.10+
metadata:
  source: Hermes skill-rag
  version: "0.1.0"
---

# Skill RAG

協助使用者管理多檔案知識庫：辨識問題主題、查找相關資料、整理索引與 chunk，並根據可查證的來源內容回答。回答時優先提供直接答案、來源檔名與 chunk 編號；命中圖片／影片或文件內媒體連結時，提供 Markdown 可點擊連結。資料不足時明確指出缺口，不臆測。

## 何時使用

- 使用者要從分散於多個檔案的知識內容查詢答案。
- 使用者要索引圖片／影片，或查詢可點擊的本機媒體路徑與網路網址。
- 使用者要建立、重掃描、重建或更新多檔案索引。
- 使用者詢問 chunk、top-k、檢索、來源引用、索引資料表或本 Skill 的 `skill_rag.py` 腳本。
- 使用者要將索引匯出為 JSON 或 SQL，或討論 MySQL RAG schema。

## 工作流程

1. 確認知識庫根目錄與使用者要完成的工作（查詢、索引或設定）。不要假定目前工作目錄就是知識庫。
2. 依問題類型先讀取相關參照文件：
   - 索引／重掃描：`references/indexing.md`、`references/database-schema.md`
   - 查詢／回答／來源引用：`references/querying.md`、`references/source-map.md`
   - 設定／MySQL／API key：`references/config.md`
3. 查詢時先使用現有索引或最相關來源檔，回答僅根據實際讀到的內容。引用來源檔名；若索引可辨識 chunk，亦提供 chunk 編號。
4. 若需要產生索引，先確認來源目錄與設定檔路徑，再執行下方腳本；不要覆寫使用者資料或把索引輸出到來源資料夾。
5. 完成後說明使用的索引方式、命中來源、限制及產生的輸出路徑。

## 隨附腳本

腳本位置：`scripts/skill_rag.py`。請從知識庫根目錄執行，並明確傳入 `--root`、`--setup` 及輸出路徑。若使用者未提供有效的私有設定檔，不要建立或猜測真實憑證；先說明需要設定檔。

```bash
python <skill-dir>/scripts/skill_rag.py --setup <private-setup.json> validate-config
python <skill-dir>/scripts/skill_rag.py --setup <private-setup.json> scan --root <knowledge-root> --output <output-dir>/index.json --sql-output <output-dir>/index.sql
python <skill-dir>/scripts/skill_rag.py query --index <output-dir>/index.json --question "<question>" --top-k 5
```

Windows PowerShell 中，含空格的路徑需加引號。設定範本位於 `templates/setup.example.json`，SQL schema 範本位於 `templates/sql-schema.sql`。只有在使用者確認後才匯入或修改資料庫；產生 SQL 不等於已連線或已寫入 MySQL。

## 實作能力與限制

- 腳本掃描 `.md`、`.markdown`、`.txt`、`.json`、`.yaml`、`.yml`、`.sql`、`.docx`、`.pdf`、`.srt`、`.vtt`、常見圖片與影片格式，來源目錄預設為 `sources/`、`references/`、`knowledge/`、`docs/`。媒體以檔名及同名描述／字幕建立索引；Markdown／HTML 中的媒體網址會列為可點擊連結。圖片像素和影片畫面不會被辨識，影片不會自動轉錄；要搜尋內容請提供同名描述或字幕。
- `scan` 目前產生本機 JSON 索引與 SQL 匯出稿；它不會自行連線 MySQL，也不會呼叫 OpenAI API 或產生 embedding。
- `query` 使用詞彙重疊與標題加權排序，不是語意向量檢索。`setup.json` 中的 `score_threshold`、`rebuild_mode`、模型欄位不是此腳本目前已實作的功能保證。
- 腳本要求設定檔包含 MySQL 欄位與 OpenAI API key，即使目前索引／查詢流程不會使用 OpenAI API。不得把金鑰貼入對話、寫進 `SKILL.md`、索引或輸出日誌。
- 此 Skill 的 `references/` 文件是操作規範，不應當作使用者知識庫來源；不要為了索引 Skill 本身而掃描整個專案。

## 安全與資料處理

- 不讀出、不回覆、不複製設定檔中的密碼或 API key。設定檔範本僅供使用者自行複製並填入；實際設定應留在私有檔案並排除於版本控制。
- 重建索引前檢查輸出目的地，避免覆寫既有索引或其他使用者檔案。資料庫操作、刪除舊資料或匯入 SQL 前先取得使用者明確同意。
- 若結果不足或候選來源彼此矛盾，說明不確定性並指出來源，不要把猜測包裝成檢索結果。
