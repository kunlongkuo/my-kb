# Skill RAG 使用說明

這個 Skill 可將多種文件、圖片與影片來源建立本機 JSON 索引及 MySQL SQL 匯出檔，再查詢相關內容並回傳可點擊的媒體連結。設定檔位於本目錄的 `setup.json`，已由本目錄 `.gitignore` 排除；不要將其加入版本控制或分享。

## 1. 需要的環境

- Python 3.10 以上。
- DOCX 可由標準函式庫直接擷取文字；PDF 需安裝 `pypdf`：

  ```powershell
  python -m pip install -r .opencode\skills\skill-rag\requirements.txt
  ```

- 若要將 SQL 匯入資料庫，需安裝並啟動 MySQL Server，另需 MySQL 命令列工具 `mysql`，或使用 MySQL Workbench。
- 私有設定檔：`setup.json`。請自行填入有效的 MySQL 連線資料及已輪替的 OpenAI API key。腳本目前要求 API key 欄位存在，但不會呼叫 OpenAI API。

## 2. 要查詢的來源檔放在哪裡？

建議為每個知識庫準備一個專用根目錄，例如專案根目錄下的 `rag-data/`，再把要查詢的文字檔放在 `rag-data/sources/`：

```text
rag-data/
└── sources/
    ├── 操作手冊.md
    ├── 商品資料.json
    ├── 商品正面.jpg
    ├── 商品正面.md       # 同名描述，讓圖片可用內容關鍵字搜尋
    ├── 安裝示範.mp4
    └── 安裝示範.vtt      # 同名字幕，可依對白搜尋影片
```

腳本也會掃描知識庫根目錄下的 `references/`、`knowledge/`、`docs/`。支援 `.md`、`.markdown`、`.txt`、`.json`、`.yaml`、`.yml`、`.sql`、`.docx`、`.pdf`、`.srt`、`.vtt`，以及 `.png`、`.jpg`、`.jpeg`、`.gif`、`.webp`、`.bmp`、`.tif`、`.tiff`、`.svg`、`.mp4`、`.mov`、`.mkv`、`.avi`、`.webm`、`.m4v`、`.mpeg`、`.mpg`、`.wmv`、`.flv`、`.3gp`。

DOCX 會擷取本文段落與表格文字；PDF 擷取可選取的文字。圖片與影片會依檔名及同名 `.md`／`.txt` 描述檔建立可搜尋記錄；影片也會讀取同名 `.srt`／`.vtt` 字幕。圖片或影片本身不會做 OCR、視覺辨識或自動轉錄。掃描影像型 PDF 仍需先 OCR。

Markdown 可用 `![圖片說明](https://example.com/photo.jpg)`、`[影片](https://youtu.be/...)` 等語法連結遠端媒體；HTML `<img>`、`<video>`、`<source>` 與常見影片 iframe 連結也會列出。搜尋命中後，結果會以 Markdown 連結列出本機 `file://` 路徑或網路網址。

使用專用根目錄可避免把專案中其他文件意外編入索引。索引與 SQL 輸出可能含有來源文字，請當作私有資料保存。

## 在 OpenCode 中使用此 Skill

首次使用或剛安裝 Skill 後，重新啟動 OpenCode。把來源檔放好後，可以直接用自然語言提出需求，例如：

- 「請用 skill-rag 從 `rag-data/sources/` 查出退貨期限，附上來源檔名。」
- 「請掃描 `rag-data/` 建立索引，並用問題『如何重設設備？』測試查詢。」
- 「找出安裝示範影片，列出可以點開的影片連結。」
- 「請說明這份 RAG 索引使用的 MySQL 資料表。」

若要自行執行索引、查詢或匯入 MySQL，請使用下方命令列流程。

## 3. 驗證設定

以下命令請在知識庫專案根目錄的 PowerShell 執行：

```powershell
$skill = ".opencode\skills\skill-rag"
python "$skill\scripts\skill_rag.py" --setup "$skill\setup.json" validate-config
```

這只會檢查必要設定欄位，不會測試 MySQL 是否可連線，也不會確認 API key 是否有效。驗證輸出不包含密碼或 API key。

## 4. 建立本機索引

確認 `rag-data/sources/` 已放入文字檔後，在專案根目錄執行：

```powershell
$skill = ".opencode\skills\skill-rag"
$knowledgeRoot = ".\rag-data"
python "$skill\scripts\skill_rag.py" --setup "$skill\setup.json" scan --root "$knowledgeRoot" --output "$skill\build\index.json" --sql-output "$skill\build\index.sql"
```

成功後會產生：

- `.opencode/skills/skill-rag/build/index.json`：本機查詢使用的索引。
- `.opencode/skills/skill-rag/build/index.sql`：可匯入 MySQL 的 SQL 資料稿。

`build/` 已列入此 Skill 的 `.gitignore`。重新掃描會重寫指定輸出檔；若要保留舊版，請先另選輸出路徑或自行備份。腳本目前每次全量重建，沒有增量更新或 embedding 檢索。

## 5. 查詢索引

索引建立後，在專案根目錄執行：

```powershell
$skill = ".opencode\skills\skill-rag"
python "$skill\scripts\skill_rag.py" query --index "$skill\build\index.json" --question "你的問題" --top-k 5
```

結果會列出命中的來源檔、chunk 編號與摘要；命中圖片、影片或含媒體網址的說明文件時，也會輸出可點擊的 Markdown 連結。本機路徑會轉成 `file://` URL；OpenCode 或作業系統是否直接開啟該 URL，仍取決於用戶端對本機連結的支援。查詢使用本機 JSON 索引，以詞彙重疊和標題加權排序；它不是語意向量搜尋，也不會連到 MySQL。若沒有命中，請檢查來源是否已掃描、問題是否包含文件中的關鍵詞，或回到來源文件查證。

## 6. 建立 MySQL 資料庫與匯入索引

`scan` 只會產生 SQL 檔，不會自行連線或寫入 MySQL。若要匯入資料庫，先確認 MySQL Server 已啟動，且 `setup.json` 中的帳號有建立資料庫及資料表的權限。

### 使用 MySQL 命令列工具

在 **命令提示字元（cmd.exe）** 開啟專案根目錄，先建立資料庫與資料表：

```cmd
mysql -h 127.0.0.1 -P 3306 -u user1 -p < .opencode\skills\skill-rag\templates\sql-schema.sql
```

輸入 MySQL 密碼後，再匯入剛才產生的索引資料：

```cmd
mysql -h 127.0.0.1 -P 3306 -u user1 -p mydb < .opencode\skills\skill-rag\build\index.sql
```

`-p` 會在終端提示輸入密碼；不要把密碼直接寫在命令列。也可以在 MySQL Workbench 先執行 `templates/sql-schema.sql`，再執行 `build/index.sql`。

SQL schema 範本會建立 `mydb`、`rag_sources` 與 `rag_chunks`，並在 chunk 文字欄位建立 FULLTEXT 索引。若資料庫中已有資料，匯入前先確認目標及備份；本工具不會替你檢查或備份既有資料。

## 7. 日常更新流程

1. 將新檔案或修改後的檔案放入 `rag-data/sources/`。
2. 再次執行「建立本機索引」命令。
3. 用代表性問題執行查詢並檢查來源及內容。
4. 若使用 MySQL，重新匯入新產生的 `index.sql`；確認資料庫目標後再執行。

## 功能限制

- 支援圖片／影片檔名、同名描述／字幕及文件中的媒體 URL 搜尋；不會分析像素、執行 OCR 或自動轉錄影片。
- 支援 DOCX 本文段落／表格及 PDF 可選取文字；掃描型 PDF 需先 OCR。
- 索引為本機 JSON；SQL 是匯出稿，匯入 MySQL 需另外執行。
- 查詢是關鍵詞重疊排序，沒有 OpenAI 呼叫、embedding 或語意檢索。
- `setup.json` 仍須包含 OpenAI API key 欄位才能通過目前腳本的設定檢查，但腳本不會使用該金鑰。
- `score_threshold`、`rebuild_mode` 等範例設定目前不是已實作的執行選項。

## 執行測試

在專案根目錄執行：

```powershell
python -m unittest discover -s .opencode\skills\skill-rag\tests -v
```
