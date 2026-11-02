# Database schema

原始設計建議以兩張表保存來源文件及其 chunks。隨附的 `templates/sql-schema.sql` 是 MySQL 建表範本；執行前先確認資料庫名稱、連線目標及既有資料，不要未經同意直接匯入或刪除資料。

## `rag_sources`

保存來源檔案的基本資料：

- `id`：來源識別碼
- `source_path`、`source_name`：來源位置與檔名
- `doc_type`、`title`：文件類型與標題
- `source_hash`：判斷來源內容是否變更
- `status`、`last_scanned_at`：索引狀態與掃描時間
- `created_at`、`updated_at`：建立／更新時間

## `rag_chunks`

保存切段後的內容及檢索資料：

- `source_id`、`chunk_index`、`chunk_title`：來源關聯、順序與標題
- `content`：可用於回答的原文或完整文字
- `chunk_content`：檢索用的 chunk 文字
- `summary`、`keywords`、`tags`：摘要、關鍵字與主題標籤
- `rag_model`、`embedding_model`、`score`：模型標記及檢索分數欄位
- `status`、`created_at`、`updated_at`：狀態與時間

索引可考慮 `source_hash`、`source_path`、`source_id`、`chunk_index`、`status`、`updated_at`；MySQL 版本支援時，可評估對標題、摘要、關鍵字、標籤及內容欄位建立 FULLTEXT 索引。

## 查詢建議

先由來源資訊定位文件，再取得相關 chunk，使用 `content`／`chunk_content` 組成回答；必要時回原始來源確認上下文。schema 的設計能力不代表隨附腳本已實作資料庫連線或查詢；目前腳本只輸出 SQL 草稿及本機 JSON。
