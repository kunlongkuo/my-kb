# tools/youtube — YouTube 上稿

用 YouTube Data API v3 上傳影片、設縮圖、排定公開、管理播放清單，以及批次改標題與說明。

## 建 venv

兩支都要 Google 的套件，建議放在本資料夾的 `.venv`（已在 `.gitignore`）：

```
python3 -m venv tools/youtube/.venv
tools/youtube/.venv/bin/python -m pip install google-api-python-client google-auth google-auth-oauthlib requests
```

開工清單（`tools/checklist`，出片段）用 `S2F_YT_PYTHON` 指定的直譯器跑 `yt_upload.py scopes`，沒設就用 `tools/youtube/.venv/bin/python`。

## 憑證放哪

放在家目錄、不進版控：

- `youtube_client_secret.json`：Google Cloud 的 OAuth「電腦版」用戶端（自己建）。
- `youtube_token.json`：跑 `auth` 授權後產生；`YT_ACCOUNT=<名稱>` 時是 `youtube_token_<名稱>.json`（第二個頻道）。

資料夾的找法（`yt_paths.py`）：`S2F_YT_DIR` 有設就用它，沒設用 `~/.config/script2film/youtube`。

## `yt_upload.py` 子命令

以下都是 `tools/youtube/.venv/bin/python tools/youtube/yt_upload.py <子命令> …`：

| 子命令 | 用途 |
|---|---|
| `auth` | 第一次用：開瀏覽器授權，存權杖 |
| `whoami` | 驗證授權：印出頻道名稱與 id（唯讀） |
| `scopes` | 用權杖換一次存取權杖，看 Google 實際給的範圍；缺範圍就 exit 1（不印權杖） |
| `upload <影片.mp4> --title … --desc-file … [--thumb 圖] [--playlist ID] [--publish-at <ISO 時間>] [--language <語言>]` | 上傳；預設「不公開」，給 `--publish-at` 改成私人並排定公開 |
| `thumb <影片 ID> <圖>` | 已上傳的片換縮圖 |
| `private <影片 ID>` | 改成私人並取消排定公開 |
| `plswap <舊 ID> <新 ID> <清單 ID,…>` | 換片：新的移到舊的在清單裡的位置，舊的移出清單（影片不刪） |

`upload` 開頭會先跑出片清單（`tools/checklist/README.md`）：影片所在的集過不了就不上傳，在連線之前退出。硬要傳加 `--skip-checklist "<原因>"`，會記在 `<集>/nightly/checklist_skips.jsonl`。影片不在任何集資料夾內時清單檢查不了，同樣要帶 `--skip-checklist "<原因>"` 才上傳（記在影片旁邊的 `checklist_skips.jsonl`）。

## 字幕

字幕檔不自動上傳（要 `youtube.force-ssl` 範圍，這一版不要求重新授權）。`upload` 成功後，影片在集資料夾內而且那一集有字幕檔（`cut_<色版>/subtitles_<語言>.srt`，`doc_cut.py` 每次都會產；已經剪好的集用 `doc_cut.py <doc.json> --captions-only` 補），會在結果那一行之前印出要手動傳的檔。手動傳的位置：YouTube Studio → 字幕 → 選這支影片 → 新增語言 → 新增 → 上傳檔案 → 含時間碼。檔案是純文字的 `.srt`、UTF-8、沒有樣式標記。

## `yt_retitle.py`

批次替播放清單裡的片在標題後加後綴、說明欄加標籤行。不加 `--apply` 只列出會改什麼；`--must-contain` 必填（標題要含這個字串才改，防止改到清單裡別的片）。

```
tools/youtube/.venv/bin/python tools/youtube/yt_retitle.py <播放清單 ID> --suffix "<後綴>" --tags-line "<#標籤 …>" --must-contain "<字串>" --out <資料夾> [--apply]
```

## 測試

```
python3 -m pytest tools/youtube -q
```
