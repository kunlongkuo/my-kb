# Indexing

## 目的與來源

將多檔案內容整理成可檢索的 chunk，保留來源路徑與內容 hash，讓索引可以追蹤、重建與更新。腳本預設掃描知識庫根目錄下的 `sources/`、`references/`、`knowledge/`、`docs/`，並可用重複的 `--source-dir` 指定額外目錄。

目前腳本讀取 `.md`、`.markdown`、`.txt`、`.json`、`.yaml`、`.yml`、`.sql`、`.docx`、`.pdf`、`.srt`、`.vtt`，以及常見圖片（PNG、JPEG、GIF、WebP、BMP、TIFF、SVG）和影片（MP4、MOV、MKV、AVI、WebM、M4V、MPEG、MPG、WMV、FLV、3GP）格式。DOCX 擷取本文段落與表格；PDF 需安裝 `requirements.txt` 中的 `pypdf`，僅能擷取可選取文字。

圖片／影片索引以檔名為基礎，並讀取同名 `.md`／`.txt` 描述；影片亦讀取同名 `.srt`／`.vtt` 字幕。Markdown 圖片／影片連結、HTML 媒體元素及常見影片平台網址會在查詢結果中輸出為 Markdown 連結，本機檔案連結使用 `file://` URL。媒體檔不會被視覺分析，影片不會自動轉錄；影像型 PDF 需先 OCR。

## 建議切分原則

- 優先以標題和段落切分；過長段落再切成較小區塊。
- 每個 chunk 保留可讀內容、標題、順序及來源資訊。
- 建議 chunk 約 800–1200 字元、重疊 100–200 字元；實際值依內容調整。
- 索引中可保留 `content`、`chunk_content`、`summary`、`keywords`、`tags`、`source_hash` 等欄位。

## 使用隨附腳本

腳本的預設值為 `chunk_size=1200`、`chunk_overlap=150`。先確認來源根目錄、設定檔和輸出路徑，再於知識庫根目錄執行：

```bash
python <skill-dir>/scripts/skill_rag.py --setup <private-setup.json> scan --root <knowledge-root> --output <output-dir>/index.json --sql-output <output-dir>/index.sql
```

腳本會寫出本機 JSON 索引與 SQL 匯出稿。它不會自動連線 MySQL，也不會實作增量掃描／embedding；每次 scan 會重建指定的 JSON 輸出。若目標檔已存在，先確認是否可覆寫，必要時請使用者指定新輸出路徑。

## 更新與重建注意事項

- 來源內容變更後重新掃描，並檢查輸出是否符合預期。
- 設定、模型或 schema 變更時，先說明可能需要重建索引。
- 資料庫 schema 變更前先備份；資料庫資料清理或覆寫需使用者明確同意。
- SQL 匯出不是資料庫匯入；匯入需由使用者另行授權並確認資料庫目標。
