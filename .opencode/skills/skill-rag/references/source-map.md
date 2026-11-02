# Source map

依問題主題先讀最可能直接回答的文件；仍不足時再擴大到相鄰主題，避免無差別掃描整個知識庫。

| 問題類型 | 優先閱讀 | 可補充閱讀 |
| --- | --- | --- |
| 建索引、重掃描、重建 | `indexing.md` | `database-schema.md` |
| 查詢、回答、top-k、來源引用 | `querying.md` | `indexing.md` |
| 資料表、內容欄位、chunk 欄位 | `database-schema.md` | `indexing.md` |
| 設定、API key、MySQL 連線 | `config.md` | 使用者指定的設定範本 |
| 如何選擇主題文件 | 本文件 | `indexing.md` |

## 關鍵字提示

- 索引：index、scan、rebuild、rescan、chunk、summary、keyword、tag
- 查詢：query、retrieve、answer、top-k、relevant、source、citation
- 設定：setup、config、api key、mysql、database、password、openai

## 閱讀順序

- 「怎麼把檔案變成可查詢資料？」：`indexing.md` → `database-schema.md` → `querying.md`
- 「查詢時要怎麼回答？」：`querying.md` → 本文件 → `database-schema.md`
- 「設定怎麼放？」：`config.md` → 使用者提供的範本

跨主題問題先讀最相關的兩份文件；只有答案仍不足時才擴展搜尋或讀取原始知識檔。
