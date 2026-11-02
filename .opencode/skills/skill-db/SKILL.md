---
name: skill-db
description: 使用者詢問 MySQL、SQL、database、資料表、schema、customers、orders、products、rag_chunks、rag_sources，或要求查詢、檢視、摘要及明確修改本機 MySQL 資料庫時使用；透過隨附 helper 執行查詢並依實際結果回答。
license: MIT
---

# Skill DB — MySQL 資料庫

使用者要求檢視或操作已設定的本機 MySQL 資料庫時，使用此技能。所有資料庫內容相關回答都必須根據即時查詢結果，不可依賴記憶或臆測。

## 檔案與設定

- `setup.json` 是本機 MySQL 連線設定檔；此檔不會隨技能提供。請以 `setup.example.json` 為範本，在技能目錄中建立 `setup.json` 並填入有效的連線資訊。不要在對話、記錄檔或提交到版本庫的檔案中放入憑證。
- `tables.json` 說明已知資料表與欄位，可用於判斷查詢方向，但不代表實際 schema；必要時須確認資料庫目前的 schema。
- `scripts/mysql_skill.py` 是查詢 helper。預設設定檔與資料表對照檔的路徑會以腳本所在位置為基準，因此可從知識庫根目錄呼叫。
- helper 需要 Python 及 `requirements.txt` 所列的套件（`python -m pip install -r .opencode/skills/skill-db/requirements.txt`）。

在 PowerShell 中從範本建立已設為忽略的本機設定檔，再填入 MySQL 連線資訊：

```powershell
Copy-Item .opencode/skills/skill-db/setup.example.json .opencode/skills/skill-db/setup.json
```

以下範例指令從知識庫根目錄執行：

```powershell
python .opencode/skills/skill-db/scripts/mysql_skill.py verify
python .opencode/skills/skill-db/scripts/mysql_skill.py schema
python .opencode/skills/skill-db/scripts/mysql_skill.py run --sql "SELECT 1 AS one"
```

若要使用其他設定檔或資料表對照檔，請在子命令之前指定 `--setup PATH` 或 `--tables PATH`。例如：

```powershell
python .opencode/skills/skill-db/scripts/mysql_skill.py --setup .opencode/skills/skill-db/setup.json schema
```

## 操作流程

1. 閱讀 `tables.json`，找出可能相關的資料表與欄位意義。
2. 若需求可能涉及多張資料表，列出可能的資料表並詢問使用者要查哪一張；不可自行猜測。
3. 若 schema 不明確或不熟悉，先執行 `schema` 檢視即時資料庫結構，再撰寫查詢。
4. 使用足以回答問題的最精簡查詢。讀取資料時，使用 helper 的 `run --sql` 指令，並且只根據回傳的資料列或筆數回答。
5. 只有在使用者明確要求寫入時，才執行 INSERT、UPDATE 或 DELETE。使用者詢問某個值，不代表授權寫入。先確認目標資料列與操作範圍；若影響範圍不明或異常廣泛，先停止並詢問使用者。
6. 多筆相關寫入使用 `batch` 與交易處理（`BEGIN`、執行各項語句，最後 `COMMIT`；若操作失敗則使用 `ROLLBACK`）。回報實際影響筆數。
7. 簡潔說明結果，並清楚區分實際查得的資料與分析解讀。

## 安全規範與限制

- 絕不可執行 `DROP DATABASE`、`DROP TABLE`、`TRUNCATE TABLE` 或變更 schema 的 DDL（`ALTER TABLE`、`CREATE TABLE`、`RENAME TABLE`）。helper 會封鎖這些語句模式。
- 不可刪除資料表或資料庫。`DELETE` 會刪除資料列，必須由使用者明確要求且限定操作範圍；執行前先查閱將受影響的資料列。
- 不可宣稱 helper 的 SQL 篩選器是完整的 SQL 安全解析器。它只會進行基本的語句開頭與禁用模式檢查；即使語句通過 helper 檢查，也必須遵守上述需求範圍規則。
- 成功連線不代表指定的資料表或欄位必然存在。請檢查即時 schema 或實際查詢結果。
- 資料庫可能含有敏感資料。只回傳回答問題所需的欄位，不要揭露連線憑證或無關個人資料。

## Helper 子命令

```text
verify                 載入設定、連線，並回傳即時 schema。
schema                 回傳即時資料表與欄位，並合併 tables.json 中的說明。
tables                 輸出已設定的 tables.json 對照內容。
run --sql SQL          執行一條允許的 SQL 語句。
batch --sql SQL ...    在同一連線上執行多條語句。
```
