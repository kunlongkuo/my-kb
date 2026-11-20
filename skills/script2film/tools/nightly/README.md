# tools/nightly — 夜跑檢查

vox-host 系列（`skills/ve-director/doc/formats/vox-host/FORMAT.md`）一集做完前後的機器檢查與上稿資料。每支都從倉庫根目錄用 `python3` 跑；`<集>` 是集資料夾（裡面有 `doc.json`），它的上一層是系列資料夾（放 `series.json`）。

| 腳本 | 用途 | 用法 |
|---|---|---|
| `preflight.py` | 舊入口：已改到 `tools/checklist/checklist.py`（三層、兩段的開工清單，見 `tools/checklist/README.md`），這裡照跑開工段。結果寫到 `<集>/nightly/checklist_start.json` | `python3 tools/nightly/preflight.py <集>/doc.json` |
| `film_check.py` | 成片基本體檢，任何 mp4 都能跑、不需要 `doc.json`：音畫長度、最後一格、片中黑格、響度、峰值、音效到位（有 `sfx/sfx_bed.wav` 才量）、成片過期（比對出片時記的剪接用檔指紋）；只列不擋的有片尾黑、句間安靜度（`quiet`：最安靜 5% 高於 -28 dB 表示配樂可能蓋過人聲）、前 30 秒最長不換畫面（`first30`，封面拍不算）。所有 Concat 出片都經 `tools/concat/concat_export.py` 自動跑它，結果寫在片旁 `<片名>.check.json`（含成片 SHA-256），上傳前的清單（`film-check`，所有片型）看這份。系列門檻放系列資料夾的 `film_check.json`。項目代號、量法、門檻依據在檔頭 | `python3 tools/nightly/film_check.py <片.mp4> [--ep <集>]` |
| `check.py` | 解說片的完整出片檢查：先跑 `film_check.py` 的基本層，再加字幕時間軸長度，加逐拍截圖表（`nightly/sheet.jpg`：每拍第一個字後 0.15 秒一格；程式畫的拍多一格「tail」，取拍尾前 0.4 秒，是畫完的樣子）；停住段與空卡只列不擋；燒在畫面上的字幕有任何一條短於 0.5 秒就不過（讀 `doc_cut.py` 寫的 `voice.cleaned/short_subs.json`，沒有那個檔就不列這一項）。`doc.json` 有 `"pace"` 時再加節奏五項（都擋）。結果寫到 `<集>/nightly/check.json` | `python3 tools/nightly/check.py <集>/doc.json <成片.mp4>` |
| `pace.py` | 節奏五項（FORMAT §4e）：前 30 秒換畫面間隔、最長靜止、畫面字、音效密度、旁白引用出處。`check.py` 會呼叫它；也可以單獨跑，不管有沒有開都照量。換畫面點的偵測（`scene_cuts`）也給 `film_check.py` 的 `first30` 與 `tools/sample/` 共用 | `python3 tools/nightly/pace.py <集>/doc.json <成片.mp4> [<稿.md>]` |
| `series.py` | 印 `series.json` 的單一欄位，或主清單加該集所屬分部清單（`playlists`） | `python3 tools/nightly/series.py <集> <欄位>`、`python3 tools/nightly/series.py <集> playlists` |
| `state.py` | 夜跑進度紀錄（每步開始、結束），中斷後照它接續 | `python3 tools/nightly/state.py <集> start S1`、`… done\|warn\|fail S1 "說明"`、`… set <鍵> <值>`、`… show` |
| `yt_meta.py` | 從 `doc.json` 與 `series.json` 產 YouTube 標題、說明欄、公開時間 | `python3 tools/nightly/yt_meta.py <集>/doc.json --next "<下一集預告>"` |
| `report.py` | 早上的一頁報告：彙整 `state.json`、`checklist_start.json`（沒有就讀舊的 `preflight.json`）、`check.json` 成 `nightly/report.html` | `python3 tools/nightly/report.py <集>` |

`check.py` 要 `numpy`、`Pillow`、`ffmpeg`；截圖表的標籤字型取自倉庫的字型資產層（`doc_common.asset("fonts", "NotoSansTC-Variable.ttf")`），只在畫截圖表時才取。

## 門檻

響度、峰值的預設在 `film_check.py` 的 `DEFAULT`（系列可用 `film_check.json` 改），長度差是 `check.py` 的 `MAX_DRIFT`，加上字幕最短顯示。任何一項不過就不上稿。基本層其他項目（音畫長度、最後一格、黑格、音效到位、過期）的門檻與實測依據寫在 `film_check.py` 檔頭。

| 數值 | 意思 | 出處 |
|---|---|---|
| −14 LUFS | 整支成片的整體響度目標 | Spotify 的官方說明寫明播放時把音量調到 −14 dB LUFS，並建議母帶以 −14 dB integrated LUFS 為目標：<https://support.spotify.com/artists/article/loudness-normalization/>（2026-11-13 讀）。YouTube 常被說也是 −14，但我們找不到 YouTube 自己的說明頁，只有第三方文章，所以不列為出處 |
| ±0.8 LU | 量到的整體響度離目標多遠算過 | 自己定的，沒有公開出處。我們的實測：同一套流程出的五支成片落在 −14.2 到 −14.6 LUFS |
| −1.0 dBTP | 峰值上限（true peak） | 同一頁 Spotify 說明：True Peak 保持在 −1 dB 以下，對有損格式（Ogg/Vorbis、AAC）最好。我們的實測：三次量到的 true peak 都是 −2.3 dBTP |
| 0.5 秒 | 燒在畫面上的每一條字幕至少停多久（`doc_common.MIN_SUB_FAIL_S`；0.5–0.8 秒只在 `doc_cut.py` 列出） | 數字取自 HyperFrames 的 embedded-captions skill（`NOTICE.md`）。我們的實測：十五集裡五集共六條短於 0.5 秒，最短 0.18 秒。改法：在稿子裡把那一句和前後併成同一屏 |
| 0.05 秒 | 成片長度和字幕時間軸終點（`beats.json` 的 `total`）差多少算過 | 自己定的，沒有公開出處。我們的實測：一支 23 秒的成片和時間軸差 0.030 秒 |

停住段（4 秒）與空卡（0.20）只列不擋，量法與由來寫在 `check.py` 檔頭。

## 節奏檢查（選用）

`doc.json` 寫 `"pace": {"script": "<稿.md>"}`（路徑相對於集資料夾）才量，五項都是擋片項目；沒寫就只印一行「· pace check off」。稿子要是五欄表（`| # | 旁白 | 字幕 | 出處 | 畫面字 |`），第 5 項數「出處」欄含「引用」的句數。開了但找不到稿子或 `sfx_plan.json` 會直接停下。

| 項目 | 上限 | 常數（`pace.py`） |
|---|---|---|
| 前 30 秒相鄰兩次換畫面的最長間隔 | 5 秒 | `GAP_S` |
| 最長靜止 | 6 秒 | `STATIC_S` |
| 每拍標籤／出處小字 | 5／4 個字（只數英文與數字） | `LABEL_W`、`SOURCE_W` |
| 音效 | 每分鐘 3 個 | `SFX_PER_MIN` |
| 旁白引用出處 | 每分鐘 1.2 次 | `CITE_PER_MIN` |

數字的由來在 `skills/ve-director/doc/formats/vox-host/FORMAT.md` §4c、§4e；量法在 `pace.py` 檔頭。三件要知道的事：

- **不是每個系列都適用**。2026-11-14 拿三支沒照 §4e 寫的成片量過，四項都不過（前 30 秒 6.0–17.1 秒、最長靜止 10.0–15.5 秒、音效每分鐘 7.1–11.9 個），所以預設不開。
- **中文標籤不數**。5 個字、4 個字是對英文畫面字定的，中文沒有定過上限。
- 「最長靜止」和上面的「停住段」是兩種量法（縮圖平均差 < 2 對 `freezedetect` 完全沒變），門檻各自對自己的量法定的，沒有統一。

## `series.json` 的 `font` 欄位（選用）

值是 Concat `--font` 參數的寫法 `<family>=<路徑>`，例如 `"font": "MyFont=fonts/MyFont.ttf"`。這裡的**路徑相對於系列資料夾**（也可以寫絕對路徑）；Concat `--font` 參數本身的相對路徑是相對於執行時所在的資料夾，兩者不能直接互換。

有這個欄位時，開工清單多一列「字型 <family>」，檢查檔案在不在；沒有這個欄位就不出這一列。

## 環境變數

| 名稱 | 用途 | 沒設時 |
|---|---|---|
| `S2F_YT_PYTHON` | 清單（出片段）跑 `tools/youtube/yt_upload.py scopes` 用的直譯器（要裝了 YouTube 套件的那個） | `tools/youtube/.venv/bin/python` |

清單另外檢查 `S2F_QWEN_TTS_DIR` 資料夾（新名沒設才看舊名 `QWEN_TTS_DIR`）與 `S2F_WHISPER_CPP_MODEL` 轉錄模型檔、選用的 `S2F_ASSETS_LOCAL`（沒設照樣通過，有設就要資料夾在），以及 `S2F_CONCAT_BIN`（舊名 `CONCAT_BIN`）。

## 測試

```
python3 -m pytest tools/nightly -q
```
